"""Audit real resumed replay prefixes and appended executed transitions.

Use only an already saved checkpoint referenced by one atomic live execution
snapshot. No learner import, updates, actions, physics or live-file edits.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import numpy as np
from research72_checkpoint_20261003 import checkpoint_hashes
from research72_rl_resume_audit_20261004 import check_lineage


def read(path):return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def compare_buffers(parent, child, inherited, steps, dimension):
    shapes=dict(observation=(48,),next_observation=(48,),action=(dimension,),
                reward=(),terminated=(),truncated=())
    assert set(parent)==set(child)==set(shapes) and 0<inherited<steps
    for key,shape in shapes.items():
        assert parent[key].shape==(inherited,*shape) and child[key].shape==(steps,*shape)
        assert parent[key].dtype==child[key].dtype==np.float32
        assert np.isfinite(child[key]).all()
        np.testing.assert_array_equal(child[key][:inherited],parent[key])
    assert np.isin(child['terminated'],[0,1]).all() and (child['truncated']==0).all()
    assert child['terminated'][-1]==1 and np.max(np.abs(child['action']))<=1
    return dict(fields=list(shapes),prefix_transitions=inherited,appended_transitions=steps-inherited,
                all_parent_values_exact=True)


def audit(manifest_path,segment):
    manifest=read(manifest_path);parent=Path(manifest['checkpoint'])
    assert checkpoint_hashes(parent)==manifest['hashes']
    parent_protocol=Path(manifest['training_protocol']);parent_execution=parent.parent/'execution.json'
    assert sha(parent_protocol)==manifest['training_protocol_sha256']
    prunner=read(parent/'office_runner.json');pp=read(parent_protocol);pe=read(parent_execution)
    cp=read(segment/'PROTOCOL.json')
    raw=(segment/'execution.json').read_bytes();snapshot=json.loads(raw)
    check_lineage(manifest,pp,pe,prunner,cp,snapshot)
    saved=snapshot['checkpoint_rows'][-1];checkpoint=Path(saved['path'])
    assert checkpoint.parent==segment and checkpoint_hashes(checkpoint)==saved['hashes']
    inherited=snapshot['resumed_from']
    assert inherited['training_protocol_sha256']==sha(parent_protocol)
    assert inherited['parent_execution_sha256']==sha(parent_execution)
    runner=read(checkpoint/'office_runner.json');agent=read(checkpoint/'official_agent_state.json')
    steps=runner['step'];old_steps=prunner['step']
    assert old_steps<steps==saved['step']==runner['replay']['count']<=cp['maximum_new_physics_steps']
    assert runner['episode']==saved['episode'] and runner['episode_boundary'] and runner['pending_transition'] is None
    assert runner['automatic_exact_resume_supported'] and runner['replay']['capacity']==prunner['replay']['capacity']
    assert agent['interactions']==agent['reward_samples']==steps
    assert agent['config']==cp['agent_config'] and agent['updates']==pe['updates']+cp['utd']*(steps-old_steps)
    assert sha(checkpoint/'office_replay.npz')==runner['replay']['sha256']
    assert sha(parent/'office_replay.npz')==prunner['replay']['sha256']
    np.testing.assert_array_equal(runner['condition_order'],prunner['condition_order'])
    dimension=5 if cp['controller']=='impedance' else 7
    with np.load(parent/'office_replay.npz',allow_pickle=False) as z:old={k:z[k].copy() for k in z.files}
    with np.load(checkpoint/'office_replay.npz',allow_pickle=False) as z:new={k:z[k].copy() for k in z.files}
    buffers=compare_buffers(old,new,old_steps,steps,dimension)
    rows=[r for r in snapshot['rows'] if r.get('step_after',steps+1)<=steps]
    assert len(rows)==runner['episode']-prunner['episode']
    cursor=old_steps;evidence=[]
    for row in rows:
        start,end=row['step_before'],row['step_after'];run=Path(row['run'])
        assert start==cursor and end-start==row['steps'] and row.get('ended_utc')
        assert read(run/'execution.json')['status']=='complete'
        assert sha(run/'AUDIT.json')==row['audit_sha256'] and sha(run/'rollout.npz')==row['trace_sha256']
        with np.load(run/'baseline_policy.npz',allow_pickle=False) as policy:
            obs=policy['observation'].astype(np.float32);action=policy['raw_action'].astype(np.float32)
        assert obs.shape==(end-start,48) and action.shape==(end-start,dimension)
        np.testing.assert_array_equal(new['observation'][start:end],obs)
        np.testing.assert_array_equal(new['action'][start:end],action)
        np.testing.assert_array_equal(new['next_observation'][start:end-1],obs[1:])
        np.testing.assert_array_equal(new['terminated'][start:end],np.r_[np.zeros(end-start-1),1.])
        cursor=end;evidence.append(dict(run=str(run),steps=end-start,
            policy_sha256=sha(run/'baseline_policy.npz'),trace_sha256=row['trace_sha256'],audit_sha256=row['audit_sha256']))
    assert cursor==steps and new['terminated'].sum()==runner['episode']
    for state in (runner['replay']['rng_state'],runner['exploration_rng']):
        rng=np.random.default_rng();rng.bit_generator.state=state
        assert rng.bit_generator.state==state
    assert checkpoint_hashes(parent)==manifest['hashes'] and checkpoint_hashes(checkpoint)==saved['hashes']
    return dict(parent_manifest=str(manifest_path),parent_manifest_sha256=sha(manifest_path),
        checkpoint=str(checkpoint),checkpoint_hashes=saved['hashes'],training_protocol_sha256=sha(segment/'PROTOCOL.json'),
        child_execution_snapshot_sha256=hashlib.sha256(raw).hexdigest(),child_execution_snapshot=snapshot,
        steps=steps,episodes=runner['episode'],updates=agent['updates'],controller=cp['controller'],seed=cp['seed'],
        replay=buffers,executed_new_episodes=evidence,nonterminal_next_observations_exact=True,rng_states_loadable=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent-manifest',type=Path,required=True);p.add_argument('--child-segment',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    cgroup=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=int((cgroup/'memory.max').read_text());assert memory<=3*1024**3
    result=dict(status='complete',created_utc=datetime.now(timezone.utc).isoformat(),host=platform.node(),
        python=sys.executable,numpy=np.__version__,memory_max=memory,argv=sys.argv,
        source_sha256={str(p.resolve()):sha(p) for p in (Path(__file__),
            Path(check_lineage.__code__.co_filename),Path(checkpoint_hashes.__code__.co_filename))},
        actor_calls=0,gradient_updates=0,physics_steps=0,sealed_reads=0,
        result=audit(a.parent_manifest.resolve(),a.child_segment.resolve()),
        limits=['Verifies persisted prefix and actual appended observation/action/termination, not gradient-by-gradient optimizer parity.',
            'Nonterminal next observations checked; terminal next observations and reward values not independently recomputed.',
            'Snapshot of one saved episode boundary, not completion of the live segment or final policy evaluation.'])
    with a.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status='complete',sha256=sha(a.output),steps=result['result']['steps'],updates=result['result']['updates'])))


if __name__=='__main__':main()
