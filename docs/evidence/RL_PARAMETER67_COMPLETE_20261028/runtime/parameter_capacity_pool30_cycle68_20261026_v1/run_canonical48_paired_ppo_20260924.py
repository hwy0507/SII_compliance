"""DGX paired PPO workflow; each invocation owns exactly one simulator worker."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import queue
import sys
import time
import traceback
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import numpy as np
import torch
import mujoco
import stable_baselines3 as sb3
from stable_baselines3.common.vec_env import DummyVecEnv,VecNormalize
from canonical48_rl_env_20260923 import load_fixture_specs,save_json,sha,resource_check
from canonical48_paired_rl_env_20260924 import PairedControlEnv,run_archived_episode
from canonical48_potential_reward_20260924 import protocol as reward_protocol
from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning

spec=importlib.util.spec_from_file_location('original_training_callbacks',ROOT/'tools/run_canonical48_ppo_20260923.py')
workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)


def source_hashes():
    return {str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools','src') for p in (ROOT/folder).rglob('*.py')}


def asset_hashes(menagerie):
    # Both robot trees are the complete133-file asset set used by the original
    # canonical runtime. Other menagerie robots are not part of this model.
    result={}
    for name in ('franka_emika_panda','franka_fr3'):
        folder=menagerie/name
        if not folder.is_dir():raise ValueError('Missing canonical robot assets:'+name)
        result.update({str(f.relative_to(menagerie)):sha(f) for f in folder.rglob('*') if f.is_file()})
    return result


def finite_exact(first,second,name):
    if first.dtype.kind in 'fciu' and not (np.isfinite(first).all() and np.isfinite(second).all()):
        raise ValueError('Nonfinite arrays:'+name)
    if not np.array_equal(first,second):raise AssertionError('Exact array mismatch:'+name)
    return dict(shape=list(first.shape),exact=True)


def compare_episode(reference,current,mode):
    checks={}
    names=('rollout.npz','physics_states.npz','contact_samples.npz')
    if mode=='direct7':names+=('actor_trace.npz',)
    for filename in names:
        with np.load(reference/filename,allow_pickle=False) as first,np.load(current/filename,allow_pickle=False) as second:
            if set(first.files)!=set(second.files):raise AssertionError('Different trace keys')
            for key in first.files:
                if mode=='parameter6' and filename=='rollout.npz' and key=='teacher_action':
                    checks[filename+':teacher_action=A.actual_action']=finite_exact(first[key],second['action'],key)
                    if np.any(second[key]):raise AssertionError('Policy branch teacher labels not zero')
                else:checks[filename+':'+key]=finite_exact(first[key],second[key],filename+':'+key)
    if sha(reference/'rollout.mjb')!=sha(current/'rollout.mjb'):raise AssertionError('MJB mismatch')
    a,b=[json.loads((root/'rollout.json').read_text()) for root in (reference,current)]
    original_diff=[k for k in a if a[k]!=b[k]]
    for result in (a,b):
        for key in ('pairs','robot_geoms','robot_bodies','other_contacts'):
            result['contact'][key]=sorted(result['contact'][key],key=lambda x:json.dumps(x,sort_keys=True))
    if set(a)!=set(b):raise AssertionError('Result keys differ')
    excluded=('controller','teacher_called','arguments') if mode=='parameter6' else ('arguments',)
    for key in a:
        if key not in excluded and a[key]!=b[key]:raise AssertionError('JSON dynamics mismatch:'+key)
    arg_diff={k for k in a['arguments'] if a['arguments'][k]!=b['arguments'][k]}
    if arg_diff!=({'output','model'} if mode=='parameter6' else {'output'}):raise AssertionError('Unexpected argument drift:'+str(arg_diff))
    with np.load(current/'transitions.npz',allow_pickle=False) as transitions,np.load(current/'actor_trace.npz',allow_pickle=False) as actor:
        if transitions['observation'].shape!=(600,48):raise AssertionError('Not full24s')
        for key in transitions.files:
            if not np.isfinite(transitions[key]).all():raise AssertionError('Nonfinite transition log')
        finite_exact(transitions['observation'],actor['observation'],'journal vs actor observations')
        finite_exact(transitions['execution_action'],actor['action'],'journal vs actor actions')
        finite_exact(transitions['next_observation'][:-1],transitions['observation'][1:],'next actor boundary')
        if not np.all(transitions['next_observation_valid'][:-1]) or transitions['next_observation_valid'][-1]:raise AssertionError('Wrong next validity')
        if np.any(transitions['policy_action']) or np.any(transitions['truncated']):raise AssertionError('Not zero policy')
        if not transitions['terminated'][-1] or np.any(transitions['terminated'][:-1]):raise AssertionError('Wrong terminal boundary')
        if mode=='parameter6' and np.any(transitions['log_scale']):raise AssertionError('Nominal gains drift')
    return dict(passed=True,arrays=checks,model_mjb_sha256=sha(current/'rollout.mjb'),
        task_success=b['success'],accepted_panel_demo=b['accepted_panel_demo'],
        original_json_differences=original_diff,argument_differences=sorted(arg_diff),
        source_set_semantics='run_primitive_teacher_v7 clean and four explicit contact set fields')


def proof(args,specs,nominal,menagerie,manifest):
    if args.mode=='parameter6':
        if args.nominal_reference is None:raise ValueError('Archived nominal reference required')
        reference=args.nominal_reference
    else:
        reference=args.output/'direct_reference'
        published=queue.Queue()
        run_archived_episode(specs['train'],menagerie,reference/'rollout',published,queue.Queue(),
            duration=24.,direct_action=lambda _:np.zeros(7))
        event,value,_=published.get(timeout=5.)
        if event!='terminal':raise RuntimeError(value)
    env=PairedControlEnv(specs['train'],menagerie,args.output/'gym',mode=args.mode,nominal_options=nominal,duration=24.)
    try:
        env.reset();done=False
        while not done:_,_,done,_,_=env.step(np.zeros(env.action_space.shape))
    finally:env.close()
    result=compare_episode(reference,args.output/'gym/episode_00000',args.mode)
    result.update(mode=args.mode,duration_s=24.,steps=600,source_hashes=manifest['source_hashes'],
        nominal_options=nominal,base_bridge_unchanged=True,reference=str(reference),
        reference_hashes={p.name:sha(p) for p in reference.iterdir() if p.suffix in ('.npz','.mjb') or p.name=='rollout.json'})
    if source_hashes()!=manifest['source_hashes']:raise RuntimeError('Proof source changed')
    if asset_hashes(menagerie)!=manifest['asset_hashes']:raise RuntimeError('Proof model assets changed')
    save_json(args.output/'PARITY.json',result)
    save_json(args.output/'COMPLETE.json',dict(status='proof_passed',mode=args.mode,parity_sha256=sha(args.output/'PARITY.json')))


class PairedProgress(workflow.Progress):
    def __init__(self,output,start):
        super().__init__(output,start,checkpoint_every=2048)
        self.reward_log=(output/'sb3_received_rewards.jsonl').open('x',buffering=1)
    def _on_step(self):
        info=self.locals['infos'][0];actual=float(self.locals['rewards'][0]);gym_value=info['gym_reward_float64']
        if actual!=float(np.float32(gym_value)):raise AssertionError('SB3 received unexpected reward')
        self.reward_log.write(json.dumps(dict(step=int(self.num_timesteps),gym_float64=gym_value,
            sb3_float32=actual,done=bool(self.locals['dones'][0]),reward_terms=info['reward_terms']))+'\n')
        return super()._on_step()
    def _on_training_end(self):
        super()._on_training_end();self.reward_log.close()


def evaluate(spec,menagerie,output,mode,nominal,model=None,normalizer=None):
    env=PairedControlEnv(spec,menagerie,output,mode=mode,nominal_options=nominal)
    total=0.
    try:
        observation,_=env.reset();done=False
        while not done:
            if model is None:action=np.zeros(env.action_space.shape)
            else:action,_=model.predict(normalizer.normalize_obs(observation[None])[0],deterministic=True)
            observation,reward,done,_,info=env.step(action);total+=reward
        return dict(**info['evaluation'],episode_reward=total,mode=mode)
    finally:env.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=['parameter6','direct7'],required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--menagerie',type=Path,required=True);p.add_argument('--proof-only',action='store_true')
    p.add_argument('--nominal-reference',type=Path);p.add_argument('--proof-root',type=Path)
    p.add_argument('--device',choices=['cpu','cuda'],default='cuda')
    p.add_argument('--cpu-offset',type=int,default=0)
    args=p.parse_args();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    started=time.time();torch.set_num_threads(1);torch.set_num_interop_threads(1)
    allowed=sorted(os.sched_getaffinity(0))
    if not 0<=args.cpu_offset<len(allowed):raise ValueError('Invalid CPU offset')
    os.sched_setaffinity(0,[allowed[args.cpu_offset]])
    specs,intersections=load_fixture_specs(args.assets)
    nominal=json.loads(specs['train']['command']['environment']['CORE_VMC_CONFIG'])
    manifest=dict(mode=args.mode,pid=os.getpid(),started_unix=started,argv=sys.argv,
        source_hashes=source_hashes(),fixture_specs=specs,split_intersections=intersections,
        nominal_options=nominal,nominal_rule='training options for all adapter episodes; runtime specs unchanged',
        reward=reward_protocol(),adapter=Canonical48VMCTuning.protocol(),
        actor_observation_dim=48,critic_observation_dim=48,policy_action_dim=6 if args.mode=='parameter6' else 7,
        execution_action_dim=7,actor_privileged_fields=[],critic_privileged_fields=[],
        training=dict(steps=8192,seed=20260923,n_steps=64,batch_size=64,n_epochs=3,gamma=.995,
            gae_lambda=.95,learning_rate=3e-4,net_arch=[128,128],log_std_init=-2.,selection='fixed final8192'),
        device=args.device,runtime=dict(python=sys.version,mujoco=mujoco.__version__,numpy=np.__version__,
            torch=torch.__version__,sb3=sb3.__version__,cuda_available=torch.cuda.is_available(),
            cuda_runtime=torch.version.cuda,gpu=torch.cuda.get_device_name() if torch.cuda.is_available() else None),
        asset_hashes=asset_hashes(args.menagerie),
        protocol_sha256=sha(ROOT/'docs/RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md'),
        cpu_affinity=sorted(os.sched_getaffinity(0)),threads=1,simulator_environments=1,
        control_class_limitations='Different output dimensions, VMC hidden memory/priors and executable action sets',
        transition_logging='Every actual Gym reward/raw prev+next, partial last next, terminal placeholder valid mask; SB3 received float32 reward independently saved')
    save_json(args.output/'manifest.json',manifest)
    callback=None;normalized=None
    try:
        if args.proof_only:
            proof(args,specs,nominal,args.menagerie,manifest);return
        if args.proof_root is None:raise ValueError('Both completed Gym proofs required before training')
        for mode in ('parameter6','direct7'):
            proof_root=args.proof_root/mode
            completed=json.loads((proof_root/'COMPLETE.json').read_text())
            if completed['status']!='proof_passed':raise ValueError('Proof incomplete')
            parity=json.loads((proof_root/'PARITY.json').read_text())
            proof_manifest=json.loads((proof_root/'manifest.json').read_text())
            if any(value['mode']!=mode for value in (completed,parity,proof_manifest)):
                raise ValueError('Proof mode does not match its directory')
            for field in ('fixture_specs','asset_hashes','runtime','device','protocol_sha256'):
                if proof_manifest[field]!=manifest[field]:raise ValueError('Proof environment drift:'+field)
            if not parity['passed'] or parity['source_hashes']!=manifest['source_hashes'] or parity['nominal_options']!=nominal:
                raise ValueError('Proof does not cover current source and nominal options')
            if sha(proof_root/'PARITY.json')!=completed['parity_sha256']:raise ValueError('Proof artifact drift')
        if args.device=='cuda':
            if not torch.cuda.is_available():raise RuntimeError('CUDA unavailable; no unilateral device fallback')
            torch.cuda.set_per_process_memory_fraction(.15)
        env=PairedControlEnv(specs['train'],args.menagerie,args.output/'train',mode=args.mode,nominal_options=nominal)
        normalized=VecNormalize(DummyVecEnv([lambda:env]),norm_obs=True,norm_reward=False,clip_obs=12.)
        model=sb3.PPO('MlpPolicy',normalized,learning_rate=3e-4,n_steps=64,batch_size=64,n_epochs=3,
            gamma=.995,gae_lambda=.95,seed=20260923,device=args.device,
            policy_kwargs=dict(net_arch=[128,128],log_std_init=-2.),verbose=0)
        callback=PairedProgress(args.output,started)
        save_json(args.output/'model_architecture.json',dict(mode=args.mode,policy_class=type(model.policy).__name__,
            trainable_parameter_count=sum(v.numel() for v in model.policy.parameters() if v.requires_grad),
            parameter_shapes={name:list(value.shape) for name,value in model.policy.named_parameters()},
            observation_dim=48,policy_action_dim=manifest['policy_action_dim'],execution_action_dim=7))
        model.learn(8192,callback=callback)
        model.save(args.output/'ppo_final.zip');normalized.save(args.output/'vecnormalize_train_only.pkl')
        normalized.training=False;normalized.close()
        model=sb3.PPO.load(args.output/'ppo_final.zip',device=args.device)
        if model.num_timesteps!=8192:raise AssertionError('Wrong final budget')
        before=(normalized.obs_rms.mean.copy(),normalized.obs_rms.var.copy(),normalized.obs_rms.count)
        results={}
        for split in ('train','validation'):
            for kind in ('zero','ppo'):
                save_json(args.output/'progress.json',dict(status='evaluation',mode=args.mode,split=split,kind=kind,pid=os.getpid()))
                results[f'{split}/{kind}']=evaluate(specs[split],args.menagerie,args.output/'eval'/split/kind,
                    args.mode,nominal,model if kind=='ppo' else None,normalized)
                save_json(args.output/'evaluation.json',results)
        if not (np.array_equal(before[0],normalized.obs_rms.mean) and np.array_equal(before[1],normalized.obs_rms.var) and before[2]==normalized.obs_rms.count):raise AssertionError('Eval normalization changed')
        if source_hashes()!=manifest['source_hashes']:raise RuntimeError('Frozen source changed')
        if asset_hashes(args.menagerie)!=manifest['asset_hashes']:raise RuntimeError('Model assets changed')
        transitions=0
        for file in (args.output/'train').rglob('transitions.npz'):
            with np.load(file,allow_pickle=False) as data:transitions+=len(data['reward'])
        if transitions!=8192:raise AssertionError('Missing transition logs')
        save_json(args.output/'COMPLETE.json',dict(status='complete',mode=args.mode,training_steps=8192,
            recorded_transitions=transitions,updates=model._n_updates,normalization_frozen=True,results=results,
            checkpoint_sha256=sha(args.output/'ppo_final.zip'),normalizer_sha256=sha(args.output/'vecnormalize_train_only.pkl'),
            elapsed_s=time.time()-started,source_unchanged=True,publication_ready=False))
        save_json(args.output/'progress.json',dict(status='complete',mode=args.mode,pid=os.getpid()))
    except BaseException as error:
        save_json(args.output/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),pid=os.getpid()));raise
    finally:
        if normalized is not None:normalized.close()
        if callback is not None and not callback.reward_log.closed:callback.reward_log.close()


if __name__=='__main__':main()
