"""Read-only CUDA replay on CPU-probe observations after restoring the frozen runtime.

Numerical differences are reported, never used to certify identical closed-loop
physics or include the CPU probe in the registered CUDA development matrix.
"""
import argparse
from pathlib import Path
import sys
import numpy as np

from office_v7_uniform24_20261008 import read, write, sha, now
from research72_checkpoint_20261003 import checkpoint_hashes
from complete_rl_node_20261012 import check_runtime


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('root','probe','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();probe=read(a.probe.resolve())
    assert not a.output.exists()
    check_runtime(root)
    import jax
    assert any(d.platform=='gpu' for d in jax.devices()), 'Requires actual local CUDA runtime'
    cp=probe['checkpoint'];path=Path(cp['path'])
    assert checkpoint_hashes(path)==cp['hashes']
    config=read(path/'official_agent_state.json');cfg=config['config'];utd=config['utd']
    sys.path.insert(0,str(root/'parameter_fullrange'))
    from official_parameter_agent import OfficialParameterAgent
    agent=OfficialParameterAgent(seed=cfg['seed'],total_steps=int(cfg['learning_rate_decay_step'])//utd,utd=utd,
        gamma=cfg['gamma'],entropy_coef=cfg['temp_target_entropy_coef'],
        initial_temperature=cfg['temp_initial_value'],action_dimension=cfg['action_dimension'])
    agent.load(path);before=agent.diagnostics()
    from research72_adapted_rl_worker_20261003 import normalization_hash
    norm=normalization_hash(agent);rows=[]
    for row in probe['rows']:
        run=Path(row['run'])
        assert read(run/'execution.json')['runtime_provenance']['normalization_sha256']==norm
        with np.load(run/'baseline_policy.npz') as data:
            obs=data['observation'];expected=data['raw_action']
        actual=np.asarray([agent.sample_action(o,training=False) for o in obs])
        assert actual.shape==expected.shape and np.isfinite(actual).all()
        diff=np.abs(actual-expected)
        rows.append(dict(condition=row['condition'],samples=len(obs),max_abs=float(diff.max()),
            rms=float(np.sqrt(np.mean(diff**2))),exact=bool(np.array_equal(actual,expected)),
            baseline_policy_sha256=sha(run/'baseline_policy.npz')))
    assert before==agent.diagnostics() and norm==normalization_hash(agent)
    assert checkpoint_hashes(path)==cp['hashes']
    write(a.output,dict(status='complete',created_utc=now(),source_sha256=sha(__file__),
        rows=rows,normalization_hash_identical=True,checkpoint_unchanged=True,
        actual_device=[str(d) for d in jax.devices()],gradient_updates=0,new_physics_steps=0,
        limitation='Same stored observations; nonzero errors and possible feedback amplification remain explicit. Not proof of identical CPU/CUDA closed-loop trajectories.'))
    print('cross-device replay max abs',max(r['max_abs'] for r in rows),flush=True)


if __name__=='__main__':main()
