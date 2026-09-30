"""No-physics final-policy replay with a predeclared safety-short fallback.

Policy requests: exact on same device; absolute1e-6 across devices. Same-request
analytic backend: absolute1e-12. Never choose a favorable learned trajectory.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical48_paired_deployment_20260924 import load_policy,sha
from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning


def compare(a,b,tolerance,label):
    a,b = np.asarray(a),np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Invalid arrays: '+label)
    maximum = float(np.max(np.abs(a-b))) if a.size else 0.
    if maximum > tolerance:
        raise AssertionError(f'{label}: {maximum} > predefined {tolerance}')
    return dict(max_abs_difference=maximum,atol=tolerance,rtol=0.,exact=bool(np.array_equal(a,b)),passed=True)


def read_episode(folder,hashes):
    files = ('transitions.npz','actor_trace.npz','transition_contract.json','rollout.json','rollout.mjb')
    for name in files:
        hashes[str(folder/name)] = sha(folder/name)
    with np.load(folder/'transitions.npz',allow_pickle=False) as archive:
        data = {k:archive[k] for k in archive.files}
    with np.load(folder/'actor_trace.npz',allow_pickle=False) as actor:
        compare(data['observation'],actor['observation'],0.,'archived actor input')
        compare(data['execution_action'],actor['action'],0.,'archived execution')
    raw = data['observation']
    count = len(raw)
    if not 1 <= count <= 600 or raw.shape != (count,48) or raw.dtype != np.float64:
        raise ValueError('Invalid original rawfloat64 boundaries')
    if not data['terminated'][-1] or data['terminated'][:-1].any() or data['truncated'].any():
        raise ValueError('Evaluation has execution error/partial logging, not a valid terminal episode')
    if data['next_observation_valid'][-1] or not data['next_observation_valid'][:-1].all():
        raise ValueError('Invalid terminal observation mask')
    compare(data['next_observation'][:-1],raw[1:],0.,'consecutive raw boundary')
    result = json.loads((folder/'rollout.json').read_text())
    if abs(result['duration_s']-.04*count)>1e-6:
        raise ValueError('Episode duration does not match actual actor transitions')
    if count < 600 and not result['invalid_physics']:
        raise ValueError('Short evaluation is not a genuine archived safety termination')
    return data,json.loads((folder/'transition_contract.json').read_text()),result


def independent_training_actor(training,manifest):
    """Use the original evaluate expression with separately loaded model/norm."""
    import gymnasium as gym
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv,VecNormalize
    model = PPO.load(training/'ppo_final.zip',device=manifest['device'])
    class SpacesOnly(gym.Env):
        observation_space = model.observation_space
        action_space = model.action_space
        def reset(self,*args,**kwargs): raise RuntimeError('No physics')
        def step(self,*args,**kwargs): raise RuntimeError('No physics')
    normalizer = VecNormalize.load(training/'vecnormalize_train_only.pkl',DummyVecEnv([SpacesOnly]))
    normalizer.training=False
    normalizer.norm_reward=False
    def predict(raw):
        observation = raw.astype(np.float32)
        action,_ = model.predict(normalizer.normalize_obs(observation[None])[0],deterministic=True)
        return np.clip(np.asarray(action,dtype=np.float64),model.action_space.low,model.action_space.high)
    return predict,normalizer


def replay(policy,predict,raw,metadata,recorded=None):
    policy.reset()
    backend = Canonical48VMCTuning(metadata['nominal_options'])
    actual_request_backend = Canonical48VMCTuning(metadata['nominal_options'])
    recorded_backend = Canonical48VMCTuning(metadata['nominal_options'])
    reference_requests,reference_actions,same_request_actions,recorded_actions,recorded_parameters = [],[],[],[],[]
    same_request_parameters = []
    for index,observation in enumerate(raw):
        request = predict(observation)
        reference_requests.append(request)
        reference_actions.append(backend.act(observation,request) if policy.mode=='parameter6' else request)
        policy.act(observation)
        generated = policy.log['policy_action'][-1]
        same_request_actions.append(actual_request_backend.act(observation,generated) if policy.mode=='parameter6' else generated)
        same_request_parameters.append([actual_request_backend.log_scale.copy(),actual_request_backend.base.k.copy(),actual_request_backend.base.b.copy()])
        if recorded is not None:
            old_request = recorded['policy_action'][index]
            recorded_actions.append(recorded_backend.act(observation,old_request) if policy.mode=='parameter6' else old_request)
            recorded_parameters.append([recorded_backend.log_scale.copy(),recorded_backend.base.k.copy(),recorded_backend.base.b.copy()])
    first = {k:np.asarray(v) for k,v in policy.log.items()}
    tolerance = 0. if metadata['device']==metadata['trained_device'] else 1e-6
    checks = dict(independent_policy_requests=compare(first['policy_action'],reference_requests,tolerance,'independent training path vs loader'),
                  same_request_analytic_backend=compare(first['execution_action'],same_request_actions,1e-12,'same-request backend'))
    if policy.mode=='parameter6':
        parameters = np.asarray(same_request_parameters)
        for i,key in enumerate(('log_scale','stiffness','damping')):
            checks['generated_'+key] = compare(first[key],parameters[:,i],1e-12,'same generated request '+key)
    if recorded is not None:
        checks['training_inference_matches_archived_requests'] = compare(reference_requests,recorded['policy_action'],0.,'original device inference vs actual evaluation')
        checks['archived_request_backend'] = compare(recorded_actions,recorded['execution_action'],1e-12,'archived same-request backend')
        if policy.mode == 'parameter6':
            parameters = np.asarray(recorded_parameters)
            for i,key in enumerate(('log_scale','stiffness','damping')):
                checks['recorded_'+key] = compare(parameters[:,i],recorded[key],1e-12,'recorded '+key)
    if tolerance==0.:
        checks['same_device_end_to_end'] = compare(first['execution_action'],reference_actions,1e-12,'same-device end-to-end backend')
    policy.reset()
    for observation in raw:
        policy.act(observation)
    for key,value in first.items():
        checks['reset_replay_'+key] = compare(policy.log[key],value,0.,'reset replay '+key)
    return dict(samples=len(raw),checks=checks,policy_atol=tolerance,analytic_same_request_atol=1e-12,
        end_to_end_execution_max_abs_difference=float(np.max(np.abs(first['execution_action']-np.asarray(reference_actions)))),
        end_to_end_exact=bool(np.array_equal(first['execution_action'],reference_actions)))


def fixed_proof(manifest,mode,hashes):
    argv = manifest['argv']
    if argv.count('--proof-root') != 1:
        raise ValueError('Training argv does not bind one unique proof root')
    root = Path(argv[argv.index('--proof-root')+1])
    if not root.is_absolute():
        raise ValueError('Proof root must be absolute; cannot infer a different fallback')
    root = root/mode
    if (root/'FAILED.json').exists():
        raise ValueError('Fallback proof has FAILED marker')
    evidence = {}
    for filename in ('manifest.json','COMPLETE.json','PARITY.json'):
        hashes[str(root/filename)] = sha(root/filename)
        evidence[filename] = json.loads((root/filename).read_text())
    complete,proof,parity = (evidence[k] for k in ('COMPLETE.json','manifest.json','PARITY.json'))
    if complete['status']!='proof_passed' or not parity['passed'] or any(x['mode']!=mode for x in (complete,proof,parity)):
        raise ValueError('Fallback is not the fixed successful branch proof')
    if complete['parity_sha256']!=sha(root/'PARITY.json'):
        raise ValueError('Fallback proof parity hash drift')
    for field in ('fixture_specs','asset_hashes','runtime','device','protocol_sha256','source_hashes','nominal_options'):
        if proof[field]!=manifest[field]:
            raise ValueError('Proof/train provenance mismatch: '+field)
    folder = root/'gym/episode_00000'
    if sha(folder/'rollout.mjb')!=parity['model_mjb_sha256']:
        raise ValueError('Fallback model hash drift')
    data,contract,result = read_episode(folder,hashes)
    if len(data['observation'])!=600 or np.any(data['policy_action']) or result['invalid_physics']:
        raise ValueError('Fallback must be the original600-frame zero proof')
    if contract['mode']!=mode or contract['adapter_train_nominal_options']!=manifest['nominal_options']:
        raise ValueError('Fallback contract drift')
    return data['observation'],str(folder)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training-directory',type=Path,required=True)
    p.add_argument('--mode',choices=['parameter6','direct7'],required=True)
    p.add_argument('--device',choices=['cpu','cuda'])
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    args.training_directory = args.training_directory.resolve()
    manifest = json.loads((args.training_directory/'manifest.json').read_text())
    hashes = {}
    folder = args.training_directory/'eval/train/ppo/episode_00000'
    data,contract,result = read_episode(folder,hashes)
    policy,metadata = load_policy(args.training_directory,args.mode,args.device)
    if contract['mode']!=args.mode or contract['adapter_train_nominal_options']!=metadata['nominal_options']:
        policy.close()
        raise ValueError('Evaluation contract differs from frozen branch')
    predict,reference_normalizer = independent_training_actor(args.training_directory,manifest)
    before = policy.actor.statistics()
    reference_before = (reference_normalizer.obs_rms.mean.copy(),reference_normalizer.obs_rms.var.copy(),np.asarray(reference_normalizer.obs_rms.count).copy())
    try:
        actual = replay(policy,predict,data['observation'],metadata,recorded=data)
        fallback = None
        proof_path = None
        if len(data['observation'])<600:
            proof_raw,proof_path = fixed_proof(manifest,args.mode,hashes)
            fallback = replay(policy,predict,proof_raw,metadata)
        after = policy.actor.statistics()
        normalizer_checks = {str(i):compare(a,b,0.,'deployment normalizer') for i,(a,b) in enumerate(zip(before,after))}
        reference_after = (reference_normalizer.obs_rms.mean,reference_normalizer.obs_rms.var,reference_normalizer.obs_rms.count)
        normalizer_checks.update({'reference_'+str(i):compare(a,b,0.,'training reference normalizer') for i,(a,b) in enumerate(zip(reference_before,reference_after))})
        for path in (args.training_directory/'manifest.json',args.training_directory/'COMPLETE.json',
                args.training_directory/'ppo_final.zip',args.training_directory/'vecnormalize_train_only.pkl',Path(__file__),
                ROOT/'scripts/canonical48_paired_deployment_20260924.py',ROOT/'scripts/canonical48_vmc_tuning_20260924.py'):
            hashes[str(path)] = sha(path)
        report = dict(passed=True,mode=args.mode,samples=600,metadata=metadata,actual_evaluation=actual,
            actual_evaluation_safety_terminated=bool(result['invalid_physics']),fallback=fallback,fallback_proof_path=proof_path,
            normalizer_checks=normalizer_checks,end_to_end_exact=actual['end_to_end_exact'] and (fallback is None or fallback['end_to_end_exact']),
            input_sha256=hashes,policy_atol=actual['policy_atol'],analytic_same_request_atol=1e-12,
            limitation='Fallback is offline policy input replay, not invented future physical transitions. Cross-device actor tolerance does not imply identical closed-loop physics.')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(report,stream,indent=2,allow_nan=False)
            stream.write('\n')
        print(json.dumps(dict(passed=True,mode=args.mode,actual_samples=len(data['observation']),fallback_used=fallback is not None)))
    finally:
        policy.close()
        reference_normalizer.close()


if __name__=='__main__':
    main()
