"""Consolidate complete100 evidence after actual inspection of all required plots."""
from pathlib import Path
import json, hashlib, time

D = Path(__file__).resolve().parent
B = D.parents[1]
R = B / 'runs/parameter_census_cycle100_review_20261031_v1'
T = B / 'runs/census100_fixed99_terminal_20261031_v1'
C = B / 'runtime/census100_prefix_comparison_20261031_v1'
N = B / 'runs/census100_new_terminal_diagnosis_20261031_v1'
read = lambda p: json.loads(p.read_text())

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

checks = [R / 'REVIEW.json', D / 'FULL_LOSS_SAVED_REVIEW.json', D / 'FULL_CONTEXT_REVIEW.json',
          C / 'CACHE_POPULATION_FULL_REVIEW.json', C / 'INTERPRETATION.json',
          C / 'INTERPRETATION_SAVED_REVIEW.json', C / 'CHANGED_CASES_REVIEW.json',
          T / 'REVIEW.json', N / 'reference100/REVIEW.json', N / 'DIAGNOSIS.json',
          N / 'SAVED_ARITHMETIC_REVIEW.json']
for p in checks:
    assert read(p)['passed'], str(p)
assert read(R / 'FINISHED.json')['completed']
for p in [T / 'FINISHED.json', C / 'COMPARISON_FINISHED.json', N / 'FINISHED.json']:
    assert read(p)['passed']
for root, names in [(R, ['loss/loss100.png', 'health/training_diagnostics.png']),
                    (T, ['fixed99_terminal_99_100.png']),
                    (C, ['training99_100_all90.png']), (N, ['new100_terminal_residuals.png'])]:
    p = root / ('FULL100_PLOT_INSPECTION.json' if root == C else 'PLOT_INSPECTION.json')
    record = read(p)
    assert record['actual_visual_inspection'] and len(record['plots']) == len(names)
    assert {v['path']:v['sha256'] for v in record['plots']} == {str(root/n):sha(root/n) for n in names}
    assert all(v['inspected'] for v in record['plots'])
    checks.append(p)
full = read(R / 'REVIEW.json')
health = read(R / 'health/DIAGNOSIS.json')
loss = read(D / 'FULL_LOSS_SAVED_REVIEW.json')
pop = read(C / 'CACHE_POPULATION_FULL_REVIEW.json')
context = read(D / 'FULL_CONTEXT_REVIEW.json')
comp = read(C / 'INTERPRETATION.json')
reference = read(N / 'reference100/REVIEW.json')
diagnosis = read(N / 'DIAGNOSIS.json')
methods = {}
for m, r in full['methods'].items():
    assert 0 < r['new_transitions'] <= 41250 and r['conditions'] == 30
    assert r['max_reward_reconstruction_error'] == 0 and r['current_replay_capacity'] == 6000000
    for k in ['retained_replay_all_old_fields_exact', 'retained_history_features_exact',
              'retained_violation_features_exact', 'new_current_next52_and_raw_mixed_action_exact',
              'optimizer_and_network_finite']:
        assert r[k]
    h = health['methods'][m]
    assert h['full_learner_optimizer_RNG_unchanged'] and h['network_state_unchanged']
    assert h['checkpoint_sha256'] == r['checkpoint_sha256']
    l = loss['methods'][m]
    assert l['rows'] == r['new_transitions'] and l['all_saved_arrays_exact_to_original_log'] and l['all_saved_scalar_stats_exact']
    p = pop['methods'][m]
    assert p['rows'] == r['new_transitions'] and p['new_terminal_rows'] == 30
    assert p['checkpoint_sha256'] == r['checkpoint_sha256'] and p['online_total_count_checked'] and p['online_new_terminal_growth_observed']
    x = context['methods'][m]
    assert x['new_rows'] == r['new_transitions'] and x['checkpoint_sha256'] == r['checkpoint_sha256']
    assert x['every_new_row_covered'] and x['all_current_contexts_match_journal'] and x['all_terminal_next_contexts_match_registered_terminal_rule']
    t = read(T / (m + '_REVIEW.json'))
    assert t['checkpoint_sha256'] == r['checkpoint_sha256'] and t['full_learner_optimizer_replay_rng_unchanged']
    assert t['saved_scalar_arithmetic_verified'] and sha(T / (m + '_values.npz')) == t['values_sha256']
    n = reference['methods'][m]
    assert n['checkpoint_sha256'] == r['checkpoint_sha256'] and n['terminal_rows'] == p['final_population']
    assert n['full_learner_optimizer_replay_rng_unchanged'] and n['saved_scalar_arithmetic_verified']
    assert sha(Path(n['values']['path'])) == n['values']['sha256']
    groups = {}
    for name, g in t['groups'].items():
        a, b = g['complete99'], g['complete100']
        assert a['rows'] == b['rows'] and a['mask_counts'] == b['mask_counts']
        groups[name] = dict(rows=a['rows'], masked_sse99=a['total_masked_sse'],
            masked_sse100=b['total_masked_sse'], relative_change=b['total_masked_sse']/a['total_masked_sse']-1,
            masked_per_critic_delta=[y-x for x,y in zip(a['masked_sse'],b['masked_sse'])],
            all_row_per_critic_delta=[y-x for x,y in zip(a['all_row_sse'],b['all_row_sse'])])
    methods[m] = dict(training=r, loss=l['stats'], terminal_population=p['final_population'],
        fixed99_terminal_groups=groups, fixed99_regression_rows=t['regression_rows'],
        fixed99_improved_rows=t['improved_rows'], known_terminal_rows=t['known_rows'],
        new100_terminal_diagnosis=diagnosis['methods'][m],
        reward_change=comp['methods'][m]['mean_reward_delta'],
        task_gained=comp['methods'][m]['task_gained'], task_lost=comp['methods'][m]['task_lost'],
        strict_gained=comp['methods'][m]['strict_gained'], strict_lost=comp['methods'][m]['strict_lost'])
assert sum(v['terminal_population'] for v in methods.values()) == 8983
assert sum(v['fixed99_terminal_groups']['all']['rows'] for v in methods.values()) == 8893
for p in [B / 'runtime/census100_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',
          B / 'runs/parameter_census97_99_reward_stability_20261031_v1/REVIEW.json',
          B / 'runs/parameter_census94_96_reward_stability_20261031_v1/REVIEW.json']:
    checks.append(p)
result = dict(passed=True, time=time.time(), methods=methods,
    inputs=[dict(path=str(p),sha256=sha(p)) for p in checks], complete100=True,
    convergence_claim=False, health_acceptance_pending=True, physics_steps=0, optimizer_updates=0,
    scope='Complete100 logs/arrays/scalars/all90 labels/all8893 old and90 new terminals/full next-context closure/all plots. Actual online total terminal growth checked; online per-stratum tensor contents not logged. Original94–96 failures retained; original97–99 complete failure retained and prospective100–102 still requires all three finite stages and final bound audit. No convergence or held-out evaluation claim.')
with (D / 'COMPLETE100_SCIENTIFIC_REVIEW.json').open('x') as f:
    json.dump(result, f, indent=2, allow_nan=False)
    f.write('\n')
print(json.dumps({m:dict(task=v['training']['task'], strict=v['training']['strict'],
    reward=v['training']['reward_mean'], original_loss=v['loss']['agent_train/original_sampled_q_loss'],
    old_terminal_relative_change=v['fixed99_terminal_groups']['all']['relative_change'],
    new_terminal_masked_sse=v['new100_terminal_diagnosis']['total_new100_masked_sse']) for m,v in methods.items()}, indent=2))
