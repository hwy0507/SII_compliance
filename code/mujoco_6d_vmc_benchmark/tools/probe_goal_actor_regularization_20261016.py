"""Finite paired, disposable replay experiment with upstream actor regularization.

No simulator, saved model, reward relabeling, or policy deployment. The two arms
load one closed checkpoint and consume the same 256 batches. Diagnostics use
training replay (not held-out acceptance); neither arm establishes task benefit.
"""
import argparse
from dataclasses import replace, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

from rl_goal_stage_20261016 import read, write, digest
from rl_recovery_control_20261016 import verify_checkpoint

UPDATES = 256
SEED = 202610161415


def set_probe_regularization(agent, alpha):
    """Only an in-memory upstream actor-loss coefficient may differ."""
    if type(alpha) not in (int, float) or alpha not in (0., 1.):
        raise ValueError('Only registered paired weights0 and1 are allowed')
    before = asdict(agent.raw_agent._cfg)
    if before['actor_bc_alpha'] != 0. or agent.config['actor_bc_alpha'] != 0.:
        raise ValueError('Probe must start from the untreated saved checkpoint')
    agent.raw_agent._cfg = replace(agent.raw_agent._cfg, actor_bc_alpha=float(alpha))
    agent.config = dict(agent.config, actor_bc_alpha=float(alpha))
    after = asdict(agent.raw_agent._cfg)
    assert {k:v for k,v in before.items() if k != 'actor_bc_alpha'} == {
        k:v for k,v in after.items() if k != 'actor_bc_alpha'}


def prepare(cp, root):
    assert platform.node() == 'airpig' and not root.exists()
    checked = verify_checkpoint(cp)
    spec = read(cp.parent/'PROTOCOL.json')
    assert spec['controller'] is None and spec['agent_config']['actor_bc_alpha'] == 0.
    assert spec['agent_config']['n_step'] == 25 and spec['utd'] == 1
    assert 5000 < checked['step'] <= 100000
    root.mkdir()
    reg = dict(schema='sii-goal-actor-regularization-probe-v1',registered_utc=datetime.now(timezone.utc).isoformat(),
        checkpoint=str(cp),checkpoint_hashes=checked['hashes'],protocol_sha256=digest(cp.parent/'PROTOCOL.json'),
        source_sha256=digest(Path(__file__)),seed=SEED,updates_per_arm=UPDATES,batch_size=256,weights=[0.,1.],
        evaluation_samples=1024,simulation=False,model_saved=False,server_compute=False,
        cpu=6,memory_max=2*1024**3,swap_max=0,backend='cuda',gpu_fraction='0.125',
        hypothesis='Earlier terminal behavior values fit, but current policy has higher Q and larger action deviation. Test whether upstream replay-action regularization reduces that deviation on fixed training data.',
        limitation='Both arms are disposable optimizer experiments. Uniform training batches can overlap diagnostic samples. No true-Q, safety, task success, convergence or generalization claim; no live model or replay edits.')
    write(root/'REGISTRATION.json',reg)
    return reg


def run(root, alpha):
    reg=read(root/'REGISTRATION.json')
    assert reg['schema']=='sii-goal-actor-regularization-probe-v1'
    assert reg['source_sha256']==digest(Path(__file__))
    assert reg['updates_per_arm']==UPDATES and reg['seed']==SEED and reg['weights']==[0.,1.]
    assert alpha in reg['weights'] and platform.node()=='airpig'
    assert sorted(os.sched_getaffinity(0))==[6]
    for key,value in dict(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                          JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',
                          CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_MEM_FRACTION='0.125').items():
        assert os.environ.get(key)==value,key
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
    assert int((cg/'memory.max').read_text())==reg['memory_max']
    assert (cg/'memory.swap.max').read_text().strip()=='0'
    out=root/f'alpha_{int(alpha)}.json'
    assert not out.exists()
    cp=Path(reg['checkpoint']);checked=verify_checkpoint(cp)
    assert checked['hashes']==reg['checkpoint_hashes']
    assert digest(cp.parent/'PROTOCOL.json')==reg['protocol_sha256']
    spec=read(cp.parent/'PROTOCOL.json');cfg=spec['agent_config']
    result=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),alpha=alpha,
        registration_sha256=digest(root/'REGISTRATION.json'),checkpoint=str(cp),checkpoint_hashes=checked['hashes'],
        simulation=False,model_saved=False,acceptance=False)
    write(out,result)
    try:
        sys.path.insert(0,spec['parameter_source'])
        import numpy as np
        import jax
        import jax.numpy as jnp
        from official_parameter_agent import OfficialParameterAgent
        from multistep_rl_replay_20261009 import MultiStepReplay
        from baseline_repair_rl_diagnostics_20261008 import flatten_metrics
        assert all(d.platform=='gpu' for d in jax.devices())
        agent=OfficialParameterAgent(seed=spec['seed'],total_steps=spec['maximum_steps'],utd=1,
            gamma=cfg['gamma'],entropy_coef=cfg['temp_target_entropy_coef'],
            initial_temperature=cfg['temp_initial_value'],action_dimension=cfg['action_dimension'])
        agent.load(cp)
        count=checked['step']
        replay=MultiStepReplay(count,cfg['action_dimension'],SEED,n_step=25,gamma=cfg['gamma'])
        with np.load(cp/'office_replay.npz',allow_pickle=False) as raw:
            assert set(raw.files)==set(replay.data)
            for key in raw.files:
                assert raw[key].shape==replay.data[key].shape
                replay.data[key][:]=raw[key]
        replay.count=count
        assert replay.data['terminated'][-1] and not replay.data['truncated'].any()
        replay.last_terminal=count-1
        ids=np.random.default_rng(SEED+1).integers(count,size=1024)
        batches=np.random.default_rng(SEED).integers(count,size=(UPDATES,256))
        result['evaluation_ids_sha256']=hashlib.sha256(ids.astype('<i8').tobytes()).hexdigest()
        result['batch_ids_sha256']=hashlib.sha256(batches.astype('<i8').tobytes()).hexdigest()
        def evaluate():
            values={k:[] for k in ('policy_behavior_mse','policy_action_rms','saturation','actor_q','behavior_q','actor_minus_behavior_q')}
            rng=np.asarray(agent.raw_agent._rng).copy()
            for offset in range(0,len(ids),256):
                batch=replay.at(ids[offset:offset+256])
                obs=jnp.asarray(agent.observation_normalizer._normalize(batch['observation']))
                dist,_=agent.raw_agent._actor(observations=obs)
                action=dist.sample(seed=jax.random.PRNGKey(20261016+offset))
                q,_=agent.raw_agent._critic(observations=obs,actions=action)
                behavior_q,_=agent.raw_agent._critic(observations=obs,actions=jnp.asarray(batch['action']))
                action=np.asarray(action);q=np.asarray(q).min(axis=0);behavior_q=np.asarray(behavior_q).min(axis=0)
                sample=dict(policy_behavior_mse=((action-batch['action'])**2).mean(axis=1),
                    policy_action_rms=np.sqrt((action**2).mean(axis=1)),saturation=(abs(action)>.95).mean(axis=1),
                    actor_q=q,behavior_q=behavior_q,actor_minus_behavior_q=q-behavior_q)
                for key in values:values[key].append(sample[key])
            assert np.array_equal(rng,np.asarray(agent.raw_agent._rng))
            values={k:np.concatenate(v) for k,v in values.items()}
            assert all(np.isfinite(v).all() for v in values.values())
            groups=dict(all=np.ones(len(ids),bool),warmup=ids<5000,learned=ids>=5000)
            return {g:{k:dict(mean=float(v[mask].mean()),p90=float(np.quantile(v[mask],.9)),n=int(mask.sum()))
                for k,v in values.items()} for g,mask in groups.items()}
        before_diag=agent.diagnostics();before_updates=agent.updates
        result['before']=evaluate()
        set_probe_regularization(agent,alpha)
        result['actual_actor_bc_alpha']=agent.raw_agent._cfg.actor_bc_alpha
        metrics=[]
        for indices in batches:
            info=flatten_metrics(agent.update(replay.at(indices)))
            assert all(np.isfinite(v) for v in info.values())
            metrics.append(info)
        result['after']=evaluate()
        after_diag=agent.diagnostics()
        assert agent.updates-before_updates==UPDATES
        assert {k:v for k,v in before_diag.items() if k!='updates'}=={
            k:v for k,v in after_diag.items() if k!='updates'}
        assert all(digest(cp/k)==v for k,v in checked['hashes'].items())
        result.update(status='passed',discarded_updates=UPDATES,diagnostics_before=before_diag,
            diagnostics_after=after_diag,checkpoint_hashes_unchanged=True,first_metrics=metrics[0],last_metrics=metrics[-1],
            devices=[str(d) for d in jax.devices()],interpretation=reg['limitation'])
    except BaseException as exc:
        result.update(status='failed_preserved',error=repr(exc));raise
    finally:
        result.update(ended_utc=datetime.now(timezone.utc).isoformat(),
            memory_peak_bytes=int((cg/'memory.peak').read_text()),memory_events=(cg/'memory.events').read_text())
        write(out,result)
    print(json.dumps(dict(status=result['status'],alpha=alpha,before=result['before']['all'],after=result['after']['all']),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run'))
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--checkpoint',type=Path)
    p.add_argument('--alpha',type=float,choices=(0.,1.))
    a=p.parse_args()
    if a.mode=='prepare':
        assert a.checkpoint is not None
        prepare(a.checkpoint.resolve(),a.root.resolve())
    else:
        assert a.alpha is not None
        run(a.root.resolve(),a.alpha)
