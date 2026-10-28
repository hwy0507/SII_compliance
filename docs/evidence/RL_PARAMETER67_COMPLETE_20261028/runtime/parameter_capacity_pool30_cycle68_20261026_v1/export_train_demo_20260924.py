"""Export the preselected, audited train zero-parameter VMC proof for action7 replay.

Data preparation only: no simulator, policy training, selection by success,
normalizer fitting, or reward replacement.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

FIXED_PROOF_MANIFEST_SHA256='a1a9c25c037928e3792ae20aaa960e4f4468922d44341f85bb7b77b5b7cf00bd'


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(Path(path).read_text())


def convert_transitions(data):
    """Keep all 600 fixed-fixture transitions regardless of task outcome."""
    count=600
    shapes={'observation':(count,48),'next_observation':(count,48),'execution_action':(count,7),
        'policy_action':(count,6),'parameter_request':(count,6),'log_scale':(count,6),
        'reward':(count,),'terminated':(count,),'truncated':(count,),'next_observation_valid':(count,)}
    for key,shape in shapes.items():
        require(np.asarray(data[key]).shape==shape,'Wrong shape: '+key)
        require(np.isfinite(data[key]).all(),'Nonfinite: '+key)
    for key in ('policy_action','parameter_request','log_scale'):
        require(not np.any(data[key]),'Expected predeclared zero6 nominal VMC behavior')
    done=np.asarray(data['terminated'],dtype=bool);valid=np.asarray(data['next_observation_valid'],dtype=bool)
    require(done[-1] and not done[:-1].any(),'Require one complete600 transition episode')
    require(not np.asarray(data['truncated']).any(),'Terminal placeholder cannot be treated as timeout')
    require(np.array_equal(valid,~done),'Invalid terminal/next observation mask')
    require(np.array_equal(data['next_observation'][:-1],data['observation'][1:]),'Next observation chain mismatch')
    require(np.array_equal(data['next_observation'][-1],data['observation'][-1]),'Unmarked terminal observation semantics')
    original_action=np.asarray(data['execution_action'])
    low=np.array([0.,-1.,-1.,-1.,-1.,-1.,-1.]);high=np.ones(7)
    require(np.all(original_action>=low) and np.all(original_action<=high),'Actual action7 outside execution bounds')
    execution=original_action.astype(np.float32)
    # Preserve SB3's exact float32 operation sequence on ALL axes. Although
    # yield bounds are [-1,1], simplifying their affine expression to identity
    # changes rounding for small values and is not bitwise scale_action parity.
    policy_low=low.astype(np.float32);policy_high=high.astype(np.float32)
    scaled=2.*((execution-policy_low)/(policy_high-policy_low))-1.
    output=dict(observations=np.asarray(data['observation'],dtype=np.float32),
        next_observations=np.asarray(data['next_observation'],dtype=np.float32),
        actions_execution=execution,actions_sac=scaled,
        rewards=np.asarray(data['reward'],dtype=np.float32).reshape(count,1),
        dones=done.astype(np.float32).reshape(count,1),timeouts=np.zeros((count,1),dtype=np.float32),
        next_observation_valid=valid.reshape(count,1))
    require(all(np.isfinite(array).all() for array in output.values()),'Float32 conversion overflow')
    require(np.all(scaled>=-1.) and np.all(scaled<=1.),'SAC action scaling bounds')
    roundtrip=policy_low+(.5*(scaled+1.)*(policy_high-policy_low))
    errors=dict(observation=float(np.max(np.abs(output['observations'].astype(float)-data['observation']))),
        next_observation=float(np.max(np.abs(output['next_observations'].astype(float)-data['next_observation']))),
        execution_action=float(np.max(np.abs(execution.astype(float)-original_action))),
        reward=float(np.max(np.abs(output['rewards'][:,0].astype(float)-data['reward']))),
        float32_action_scale_roundtrip=float(np.max(np.abs(roundtrip-execution))))
    return output,errors


def export(proof,audit_report,snapshot,output):
    proof=Path(proof).resolve();snapshot=Path(snapshot).resolve();output=Path(output).resolve()
    require(not output.exists(),'Fresh output directory required')
    manifest=read(proof/'manifest.json');reported=read(audit_report)
    require(sha(proof/'manifest.json')==FIXED_PROOF_MANIFEST_SHA256,'Only the preselected fixed train proof is in scope')
    require(manifest['mode']=='parameter6','Demonstration must be nominal parameter6 proof')
    require(read(proof/'COMPLETE.json')['status']=='proof_passed' and not (proof/'FAILED.json').exists(),'Proof incomplete/failed')
    require(reported['passed'] and reported['manifest_sha256']==FIXED_PROOF_MANIFEST_SHA256,'Independent audit does not cover fixed proof')
    require(Path(reported['run']).resolve()==proof and Path(reported['snapshot']).resolve()==snapshot,'Independent audit provenance paths differ')
    auditor=snapshot/'tools/audit_paired_transitions_20260924.py'
    require(sha(auditor)==manifest['source_hashes']['tools/audit_paired_transitions_20260924.py']==reported['audit_tool_sha256'],
        'Frozen auditor hash mismatch')
    spec=importlib.util.spec_from_file_location('frozen_demo_transition_audit',auditor)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    fresh=module.audit_run(proof,snapshot)
    require(fresh['passed'] and len(fresh['episodes'])==len(reported['episodes'])==1,'Expected one audited demonstration episode')
    current,previous=fresh['episodes'][0],reported['episodes'][0]
    for key in ('hashes','transitions','complete','split','mode','task_success','development_gate'):
        require(current[key]==previous[key],'Independent audit evidence drift: '+key)
    require(current['split']=='train' and current['complete'] and current['transitions']==600,'Not complete train-only data')
    # Inclusion is determined solely by the predeclared fixture/proof identity;
    # task_success and development_gate are metadata, never acceptance filters.
    episode=proof/'gym/episode_00000'
    with np.load(episode/'transitions.npz',allow_pickle=False) as data:
        arrays,conversion=convert_transitions(data)
        reward_audit={key:data[key].copy() for key in data.files if key.startswith('reward_term_') or key in ('stage','next_stage')}
    output.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(output/'demonstration.npz',**arrays)
    np.savez_compressed(output/'reward_audit_only.npz',**reward_audit)
    metadata=dict(schema='canonical48_action7_train_demo_v2',dataset_role='train_only_demonstration',
        selected_by='Fixed first training fixture and its predeclared zero6 Gym proof; never success/validation selection',
        demonstration_transitions=600,demonstration_episodes=1,online_rl_training_performed=False,
        behavior='Analytic nominal VMC driven by raw48 wrench; zero parameter6 requests, generally nonzero execution_action7',
        actor_observation_dim=48,execution_action_dim=7,policy_parameter6_not_used_as_replay_action=True,
        actor_privileged_fields=[],critic_privileged_fields=[],
        reward=dict(protocol=manifest['reward'],source='Every actual audited Gym reward cast float64 to float32; no relabeling',normalization=False),
        observation=dict(source='Raw canonical48 SI values cast float64 to float32',normalized=False,
            vecnormalize='Store raw; SB3 ReplayBuffer sampling normalizes with train-only VecNormalize. Never normalize twice or update from validation/test.',
            initialization='Future training must predeclare whether train-demo initializes obs_rms; this exporter does not fit a normalizer'),
        actions=dict(environment_field='actions_execution',sb3_sac_replay_field='actions_sac',
            mapping='Exact SB3 float32 expression on all axes: 2*((action-low)/(high-low))-1; float32 action/low/high',
            mathematical_mapping='slowdown maps to2*a0-1; yield is mathematically identity, but the uniform float32 operation sequence is retained',
            warning='Never put six-dimensional zero policy_action or unscaled slowdown directly into SAC replay'),
        terminal=dict(dones_last=1,timeouts_all=0,next_valid_last=False,
            next_observation='Final next is explicitly last-observation placeholder, legal only because done=1/timeout=0 disables bootstrap',
            sb3='Use handle_timeout_termination correctly: TimeLimit.truncated=False; do not convert the finite task termination to truncation'),
        reward_only_metadata='reward_audit_only.npz contains stage and potential terms, never actor/critic inputs',
        extra_data_budget=dict(additional_train_demonstrations=600,
            example='8192 future online interactions +600 demonstrations =8792 unique available transitions, unlike8192 online-only',
            replay_reuse='Repeated gradient sampling must be reported separately from unique transition count'),
        observed_outcome=dict(task_success=current['task_success'],development_gate=current['development_gate'],used_as_selection_filter=False),
        limitation='One preselected successful teacher trajectory does not establish coverage, robustness, RL learning, or RLPD paper reproduction',
        conversion_max_abs_errors=conversion,
        arrays={key:dict(shape=list(value.shape),dtype=str(value.dtype)) for key,value in arrays.items()},
        provenance=dict(proof=str(proof),snapshot=str(snapshot),independent_audit=str(Path(audit_report).resolve()),
            proof_manifest_sha256=sha(proof/'manifest.json'),proof_complete_sha256=sha(proof/'COMPLETE.json'),
            independent_audit_sha256=sha(audit_report),frozen_auditor_sha256=sha(auditor),exporter_sha256=sha(__file__),
            source_files_verified=fresh['verified_source_files'],source_hashes=manifest['source_hashes'],
            fixture=manifest['fixture_specs']['train'],episode_hashes=current['hashes']),
        artifact_sha256={name:sha(output/name) for name in ('demonstration.npz','reward_audit_only.npz')})
    (output/'manifest.json').write_text(json.dumps(metadata,indent=2,allow_nan=False)+'\n')
    return dict(output=str(output),transitions=600,manifest_sha256=sha(output/'manifest.json'),conversion_max_abs_errors=conversion)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('proof','audit','snapshot','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();print(json.dumps(export(args.proof,args.audit,args.snapshot,args.output)))


if __name__=='__main__':main()
