"""Bounded local checkpoint/replay diagnostic. No simulator, no saved trained model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve();out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    result=dict(status='running',simulation=False,updates_per_restored_copy=1,
                purpose='Checkpoint/replay and deterministic update parity only; not acceptance or convergence')
    def save():
        (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    save()
    try:
        cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
        assert int((cg/'memory.max').read_text())<=2*1024**3
        assert (cg/'memory.swap.max').read_text().strip()=='0'
        sys.path.insert(0,str(root/'parameter_fullrange'))
        import numpy as np
        import jax
        from official_parameter_agent import OfficialParameterAgent
        from baseline_repair_rl_diagnostics_20261008 import flatten_metrics
        state=json.loads((root/'direct_task_safety/execution.json').read_text())
        entry=state['checkpoint_rows'][-1];cp=Path(entry['path'])
        assert all(digest(cp/k)==v for k,v in entry['hashes'].items())
        spec=json.loads((cp.parent/'PROTOCOL.json').read_text())
        agent=OfficialParameterAgent(seed=spec['seed'],total_steps=spec['maximum_steps'],utd=1,
            gamma=spec['agent_config']['gamma'],entropy_coef=spec['agent_config']['temp_target_entropy_coef'],
            initial_temperature=spec['agent_config']['temp_initial_value'],action_dimension=7)
        agent.load(cp)
        saved=json.loads((cp/'official_agent_state.json').read_text())
        runner=json.loads((cp/'office_runner.json').read_text())
        assert agent.interactions==agent.reward_samples==runner['step']==entry['step']
        with np.load(cp/'office_replay.npz',allow_pickle=False) as z:
            sample_ids=np.random.default_rng(20261016).integers(runner['step'],size=256)
            batch={k:z[k][sample_ids].copy() for k in z.files}
            result['replay_count']=len(z['reward'])
            result['terminal_samples']=int(np.count_nonzero(z['terminated']))
        assert all(np.isfinite(v).all() for v in batch.values())
        assert np.max(np.abs(batch['action']))<=1.
        obs=batch['observation'][0]
        action1=agent.sample_action(obs,training=False)
        agent.load(cp)
        action2=agent.sample_action(obs,training=False)
        np.testing.assert_array_equal(action1,action2)
        def leaves():
            return [np.asarray(x).copy() for x in jax.tree_util.tree_leaves(agent.raw_agent._actor.params)]
        agent.load(cp);before=leaves();started=time.monotonic()
        metrics1=flatten_metrics(agent.update(batch));after1=leaves()
        assert agent.updates==saved['updates']+1
        assert any(not np.array_equal(a,b) for a,b in zip(before,after1))
        agent.load(cp);metrics2=flatten_metrics(agent.update(batch));after2=leaves()
        for a,b in zip(after1,after2):np.testing.assert_array_equal(a,b)
        for k in metrics1:
            np.testing.assert_array_equal(np.asarray(metrics1[k]),np.asarray(metrics2[k]))
            assert np.isfinite(np.asarray(metrics1[k])).all(),k
        result.update(status='passed',checkpoint=str(cp),checkpoint_step=entry['step'],
            original_updates=saved['updates'],actual_utd_from_historical_counts=2,
            declared_utd=spec['utd'],restored_action_exact=True,repeated_update_exact=True,
            actor_parameters_changed=True,finite_update_metrics=True,
            update_pair_seconds=time.monotonic()-started,
            peak_memory_bytes=int((cg/'memory.peak').read_text()),
            memory_events=(cg/'memory.events').read_text(),
            checkpoint_still_unchanged=all(digest(cp/k)==v for k,v in entry['hashes'].items()))
    except BaseException as exc:
        result.update(status='failed_preserved',error=repr(exc));raise
    finally:
        save()


if __name__=='__main__':main()
