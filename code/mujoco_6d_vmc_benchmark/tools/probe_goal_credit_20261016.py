"""Bounded preflight of the registered n25 checkpoint/replay migration."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / 'source/tools'))
    from rl_goal_stage_20261016 import read, write, digest, verify_inputs
    from goal_rl_credit_adapter_20261016 import migrated_replay_metadata
    from baseline_repair_rl_diagnostics_20261008 import flatten_metrics
    reg = read(root / 'REGISTRATION.json')
    verify_inputs(reg)
    out = root / 'CREDIT_PREFLIGHT.json'
    assert not out.exists()
    result = dict(status='running', simulation=False, gradient_updates=1, model_saved=False,
                  registration_sha256=digest(root / 'REGISTRATION.json'))
    write(out, result)
    try:
        cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
        assert int((cg/'memory.max').read_text()) <= 3*1024**3
        assert (cg/'memory.swap.max').read_text().strip() == '0'
        sys.path.insert(0, reg['parameter_source'])
        import numpy as np
        from official_parameter_agent import OfficialParameterAgent
        from multistep_rl_replay_20261009 import MultiStepReplay
        job = reg['jobs'][0]
        cp = Path(job['checkpoint'])
        spec = read(cp.parent / 'PROTOCOL.json')
        cfg = spec['agent_config']
        agent = OfficialParameterAgent(seed=job['seed'], total_steps=reg['optimizer_schedule_steps'],
            utd=1, gamma=cfg['gamma'], entropy_coef=cfg['temp_target_entropy_coef'],
            initial_temperature=cfg['temp_initial_value'], action_dimension=cfg['action_dimension'])
        agent.load(cp)
        assert agent.config['n_step'] == agent.raw_agent._cfg.n_step == 25
        runner = read(cp/'office_runner.json')
        replay = MultiStepReplay(reg['optimizer_schedule_steps'], cfg['action_dimension'],
            job['seed']+53, n_step=25, gamma=cfg['gamma'])
        replay.restore(cp/'office_replay.npz', migrated_replay_metadata(runner['replay'],runner['step'],cfg['gamma']))
        ids = np.arange(runner['step']-25, runner['step'])
        batch = replay.at(ids)
        expected = [sum(cfg['gamma']**j*float(replay.data['reward'][i+j])
                        for j in range(runner['step']-i)) for i in ids]
        np.testing.assert_allclose(batch['reward'], expected, atol=2e-6, rtol=2e-6)
        np.testing.assert_array_equal(batch['terminated'], np.ones(25))
        np.testing.assert_array_equal(batch['next_observation'],
            np.repeat(replay.data['next_observation'][runner['step']-1][None,:],25,axis=0))
        before = agent.updates
        metrics = flatten_metrics(agent.update(replay.sample(256)))
        assert agent.updates == before+1
        assert all(np.isfinite(v) for v in metrics.values())
        assert all(digest(cp/k)==v for k,v in reg['parent_checkpoint_hashes'].items())
        result.update(status='passed', inherited_steps=runner['step'], actual_n_step=25,
            terminal_windows_match=True, no_cross_episode_bootstrap=True,
            restored_raw_replay_count=replay.count, finite_update_metrics=True, metrics=metrics,
            checkpoint_hashes_unchanged=True, peak_memory_bytes=int((cg/'memory.peak').read_text()),
            memory_events=(cg/'memory.events').read_text())
    except BaseException as exc:
        result.update(status='failed_preserved',error=repr(exc))
        raise
    finally:
        write(out,result)


if __name__ == '__main__':
    main()
