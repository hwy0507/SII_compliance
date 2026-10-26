"""Audit saved paired short-prefix physics; do not retrain discarded learners."""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {52})
    import numpy as np
    reg = json.loads((root/'REGISTRATION.json').read_text())
    report = json.loads((root/'REVIEW.json').read_text())
    assert report['passed'] and report['original_checkpoint_and_replay_unchanged']
    assert report['total_critic_updates'] == 3200 and report['total_actor_updates'] == 400
    assert report['total_temperature_updates'] == 400 and not report['weights_saved']
    assert not report['formal_deployment'] and report['physical_prefix_episodes'] == 48
    for key in ['checkpoint', 'training_registration', 'cycle_review', 'health_review', 'implementation_gate', 'gate_decision']:
        assert sha(reg[key]['path']) == reg[key]['sha256']
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    protocol = json.loads(Path(reg['training_registration']['path']).read_text())
    sys.path[:0] = [str(Path(reg['episode_adapter']).parent), reg['adapter_runtime'],
        str(Path(protocol['runtime'])/'source/tools')]
    from summarize_published_episode_audit_20261025 import summarize
    from replay_published_filter_audit_20261025 import audit as filter_audit
    from replay_published_torque_audit_20261025 import audit as torque_audit
    from evaluate_serl_seeded_multistep_20261026 import case_action_seed
    arms = report['results']
    assert [r['arm'] for r in arms] == ['learned_alpha', 'actor_floor01']
    for field in ['initial_learner_digest', 'initial_replay_digest', 'sampled_rows_sha256',
                  'final_sample_rng_digest', 'final_agent_rng_digest']:
        assert arms[0][field] == arms[1][field]
    assert {k:v for k,v in arms[0]['initial'].items() if k != 'effective_actor_temperature'} == {
        k:v for k,v in arms[1]['initial'].items() if k != 'effective_actor_temperature'}
    conditions = {c['id']: c for c in protocol['conditions']}
    records, physical_samples, pairs = [], 0, {}
    for arm in arms:
        name = arm['arm']
        assert arm == json.loads((root/(name+'_RESULT.json')).read_text())
        assert arm['outer_updates'] == arm['actor_updates'] == arm['temperature_updates'] == 200
        assert arm['critic_updates'] == 1600 and len(arm['points']) == 1
        prefix = arm['prefixes']
        assert prefix['learner_optimizer_rng_unchanged'] and prefix['replay_writes'] == 0
        assert prefix['frozen_learner_digest_before'] == prefix['frozen_learner_digest_after'] == arm['final_learner_digest']
        assert len(prefix['episodes']) == 24 and not prefix['weights_saved']
        for episode in prefix['episodes']:
            case, index = episode['case'], episode['seed_index']
            assert case in reg['case_ids'] and 0 <= index < 8 and episode['arm'] == name
            assert episode['seed'] == case_action_seed(reg['action_seed_start']+index, case)
            assert (case, index, name) not in pairs and episode['action_replay_exact']
            folder = Path(episode['folder'])
            assert sha(folder/'rollout.mjb') == conditions[case]['model_sha256']
            assert sha(folder/'actor_intervals.jsonl') == episode['journal_sha256']
            journal = [json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()]
            assert 0 < len(journal) == episode['actions'] <= 64
            actions = np.asarray([r['action'] for r in journal])
            assert actions.shape == (len(journal), 7) and np.isfinite(actions).all()
            np.testing.assert_array_equal(actions, np.asarray([r['executed_action'] for r in journal]))
            physical = summarize(folder, 'direct', f'{case}:{index}:{name}')
            filt, torque = filter_audit(folder), torque_audit(folder)
            assert filt['passed'] and torque['passed']
            row = physical['row']
            assert physical['samples'] <= 51200 and row['elapsed_s'] <= 2.5600001
            assert row['full_horizon'] is False
            assert episode['left_initial_approach'] == (row['final_task_stage'] != 'approach')
            assert row['abort_reason'] == episode['terminal']['result']['abort_reason']
            physical_samples += physical['samples']
            audit = dict(physical=physical, filter=filt, torque=torque,
                action_replay_scope='Original evaluator replayed sampled policy actions exactly while auxiliary weights remained in RAM. This reviewer checks saved actions and physical telemetry; it does not recompute trained neural inference.')
            (folder/'PREFIX_REVIEW.json').write_text(json.dumps(audit, indent=2)+'\n')
            record = dict(arm=name, case=case, seed_index=index, seed=episode['seed'],
                first_observation=journal[0]['observation'], stage=row['final_task_stage'],
                left_initial_approach=episode['left_initial_approach'], abort=row['abort_reason'],
                machine_violation=row['machine_safety_violation'], actions=len(journal),
                samples=physical['samples'], public0_mean=float(actions[:, 0].mean()),
                residual_abs_mean=float(np.abs(actions[:, 1:]).mean()),
                review=dict(path=str(folder/'PREFIX_REVIEW.json'), sha256=sha(folder/'PREFIX_REVIEW.json')))
            pairs[case, index, name] = record
            records.append(record)
    assert physical_samples <= reg['maximum_physical_substeps'] == 2457600
    tables, summaries = {}, {}
    for case in reg['case_ids']:
        table = collections.Counter()
        summaries[case] = {}
        for index in range(8):
            a, b = [pairs[case, index, arm] for arm in reg['arms']]
            np.testing.assert_array_equal(a['first_observation'], b['first_observation'])
            table[str(int(a['left_initial_approach']))+str(int(b['left_initial_approach']))] += 1
        tables[case] = dict(table)
        for arm in reg['arms']:
            rows = [pairs[case, i, arm] for i in range(8)]
            summaries[case][arm] = dict(trials=8,
                exits=sum(r['left_initial_approach'] for r in rows),
                exits_without_machine_violation=sum(r['left_initial_approach'] and not r['machine_violation'] for r in rows),
                aborts=sum(r['abort'] is not None for r in rows),
                machine_violations=sum(r['machine_violation'] for r in rows),
                public0_mean=float(np.mean([r['public0_mean'] for r in rows])),
                residual_abs_mean=float(np.mean([r['residual_abs_mean'] for r in rows])))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), constrained_layout=True)
    for axis, metric in zip(axes, ['exits', 'public0_mean', 'residual_abs_mean']):
        for i, arm in enumerate(reg['arms']):
            axis.bar(np.arange(3)+(i-.5)*.35, [summaries[c][arm][metric] for c in reg['case_ids']], width=.35, label=arm)
        axis.set_xticks(np.arange(3), ['passive0000', 'short0000', 'long0000'])
        axis.set_title(metric)
        axis.grid(axis='y', alpha=.2)
    axes[0].legend()
    fig.suptitle('Eight paired seeds per original condition;2.56s prefixes, not full-task success')
    plot = root/'physical_prefix_comparison.png'
    fig.savefig(plot, dpi=140)
    plt.close(fig)
    result = dict(passed=True, time=time.time(), checkpoint=reg['checkpoint'], summaries=summaries,
        paired_exit_tables=tables, trials=records, physical_substeps=physical_samples,
        report_sha256=sha(root/'REVIEW.json'), plot_sha256=sha(plot), source_sha256=sha(Path(__file__)),
        new_physics_by_review=0, optimizer_updates=0, formal_deployment=False, convergence_claim=False,
        limitation='Saved paired short-prefix telemetry/filter/torque audit, not a dynamics rerun. Original evaluator verified trained actions and frozen learner state before discarding weights. Eight seeds per each of three conditions, correlated initial geometry; no full-task or all30 generalization claim. No seed selection, replay injection, or automatic extension.')
    (root/'INDEPENDENT_REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    (root/'FINISHED.json').write_text(json.dumps(dict(completed=True, convergence_claim=False, time=time.time()))+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.run)
    except BaseException as error:
        (args.run/'INDEPENDENT_REVIEW_FAILURE.json').write_text(json.dumps(dict(time=time.time(), error=repr(error)))+'\n')
        raise
