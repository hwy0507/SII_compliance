"""Report every initial public candidate after the whole phase is audited.

Descriptive development evidence only: no ranking, model selection, heldout
access, new fitting, or physical integration. Keep seed/variant denominators.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics

from research72_select_learning_20261003 import load_phase, read, sha


def summarize(rows, contacts=True):
    full = [r for r in rows if r['full_horizon']]
    result = dict(
        episodes=len(rows), task=sum(r['task_success'] for r in rows),
        strict=sum(r['strict_success'] for r in rows), full_horizons=len(full),
        placed_but_not_strict=sum(r['task_success'] and not r['strict_success'] for r in rows),
        failed_task_stages=dict(Counter(r['stage'] for r in rows if not r['task_success'])),
        full_horizon_mean_rmse_mm=statistics.mean(r['rmse_mm'] for r in full) if full else None,
        full_horizon_mean_peak_torque_nm=statistics.mean(r['peak_torque_nm'] for r in full) if full else None,
        full_horizon_mean_peak_speed_mps=statistics.mean(r['peak_speed_mps'] for r in full) if full else None,
        all_observed_max_external_penetration_mm=max(r['penetration_mm'] for r in rows),
        all_observed_max_edge_penetration_mm=max(r['edge_penetration_mm'] for r in rows),
    )
    if contacts:
        result['contacts'] = {}
        for event in ('ball', 'human', 'rod', 'unknown_edge', 'pillar'):
            exposed = [r['contact'][event] for r in full if r['contact'][event]['exposure']]
            result['contacts'][event] = dict(
                full_horizon_exposed=len(exposed),
                short_horizon_exposed=sum(r['contact'][event]['exposure'] for r in rows if not r['full_horizon']),
                mean_over_exposed_full_episodes={field: statistics.mean(e[field] for e in exposed) if exposed else None
                    for field in ('contact_p95_force_n', 'peak_force_n', 'impulse_ns', 'contact_duration_s')})
        result['recovery'] = {}
        for event in ('ball', 'human', 'rod'):
            values = [r['recovery'][event] for r in full if r['recovery'][event]['exposed']]
            result['recovery'][event] = dict(exposed_full_episodes=len(values),
                observed_recovery=sum(r['settled_rejoin_time_s'] is not None for r in values),
                right_censored=sum(r['right_censored'] for r in values))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--phase', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root, phase, output = args.root.resolve(), args.phase.resolve(), args.output.resolve()
    assert not output.exists()
    protocol = read(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']
    conditions = [c['id'] for c in read(root/'CONDITIONS.json')['conditions'] if c['role'] == 'development']
    models, observed, evidence = load_phase(phase, sha(root/'PROTOCOL.json'), conditions)
    assert len(observed) == len(models)*len(conditions)
    metric_sources = set()
    for row in observed.values():
        run = Path(row['run'])
        analysis = phase/(run.parent.name+'_analysis')
        receipt = read(analysis/'execution.json')
        metric_path = analysis/(run.name+'.metrics.json')
        assert sha(metric_path) == receipt['outputs'][metric_path.name]
        metric = read(metric_path)
        assert metric['trace_sha256'] == row['trace_sha256']
        assert metric['model_sha256'] == protocol['formal_model_sha256']
        for field in ('task_success', 'strict_success', 'full_horizon'):
            assert metric[field] == row[field]
        for field in ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps'):
            assert abs(metric[field]-row[field]) <= 1e-8
        row.update(contact=metric['contact'], recovery=metric['recovery'])
        metric_sources.add((metric['metric_version'], metric['metric_source_sha256']))
        evidence.append(dict(path=str(metric_path), sha256=sha(metric_path)))
    groups = defaultdict(list)
    individual = []
    for model in models:
        metadata_path = Path(model['checkpoint']).parent/'TRAINING_COMPLETE.json'
        metadata = read(metadata_path)
        assert sha(Path(model['checkpoint'])) == model['checkpoint_sha256'] == metadata['checkpoint_sha256']
        evidence.append(dict(path=str(metadata_path), sha256=sha(metadata_path)))
        rows = [observed[model['name'], c] for c in conditions]
        groups[model['category'], model['variant']].append((model, rows))
        individual.append(dict(name=model['name'], category=model['category'], variant=model['variant'],
            seed=model['seed'], checkpoint_sha256=model['checkpoint_sha256'],
            gradient_updates=metadata.get('updates'), selected_update=metadata.get('selected_update'),
            parent_checkpoint_sha256=metadata.get('parent_checkpoint_sha256'), **summarize(rows)))
    variants = []
    for (family, variant), members in sorted(groups.items()):
        assert sorted(m['seed'] for m, _ in members) == sorted(protocol['budget_caps']['training_seeds'])
        variants.append(dict(category=family, variant=variant, seeds=[m['seed'] for m, _ in members],
            **summarize([r for _, rows in members for r in rows])))
    per_condition = []
    for condition in conditions:
        for (family, variant), members in sorted(groups.items()):
            per_condition.append(dict(condition=condition, category=family, variant=variant,
                **summarize([observed[m['name'], condition] for m, _ in members], contacts=False)))
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
        selector_source_sha256=sha(Path(__file__).with_name('research72_select_learning_20261003.py')),
        role='public_development_descriptive_only', phase=str(phase),
        protocol_sha256=sha(root/'PROTOCOL.json'), condition_ids=conditions,
        expected_episodes=len(models)*len(conditions), observed_episodes=len(observed),
        independent_evidence=evidence, variants=variants, models=individual, per_condition=per_condition,
        metric_sources=[dict(version=v, sha256=s) for v, s in sorted(metric_sources)],
        overall=summarize(list(observed.values())), new_physics_episodes=0, new_fitted_models=0,
        caveats=['These are all initial candidates, not selected finalists or heldout rates.',
            'Variants and seeds are separate; pooled candidates are not independent trials.',
            'Matched networks inherit fitted parent weights; selected_update=0 retains initialization and is not evidence that gradient training improved the policy.',
            'Full-horizon scalar means exclude short episodes, whose counts and failures remain explicit.',
            'Contact means condition on observed contact, include successes and failures, and do not compare a common exposed subset; no-contact is null, not zero compliance burden.',
            'Force integral is the integral of force magnitude, not net signed impulse; recovery without observation is right-censored.',
            'These are the immutable phase event metrics, not a newly recomputed whole-horizon supplemental audit.',
            'Improved neural learning rates, context-memory candidates and RL adaptation are separate pending cohorts.'])
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(output), sha256=sha(output),
        episodes=len(observed), task=result['overall']['task'], strict=result['overall']['strict'],
        variants=[{k: v[k] for k in ('category', 'variant', 'episodes', 'task', 'strict')} for v in variants])))


if __name__ == '__main__':
    main()
