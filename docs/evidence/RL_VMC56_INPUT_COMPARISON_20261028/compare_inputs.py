"""Posthoc input comparison of specified VMC49/55/56 short0600 terminals."""
from pathlib import Path
import ast, hashlib, itertools, json, math, os, time
os.sched_setaffinity(0, {53})
import numpy as np
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT = Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return dict(path=str(p), sha256=sha(p))
inputs = {}
anchor = B/'runs/vmc56_preterminal_followup_20261028_v1/values.npz'
inputs['anchor'] = ref(anchor)
assert sha(anchor) == '0385dae82df125e48e37c14cfe71e8fc40e9c80876c79bcf97c95f104168525d'
learner = B/'runtime/parameter_capacity_pool30_cycle57_20261026_v1/published_compliance_learner_20261025.py'
schema = B/'runtime/source_train17_clock/source/scripts/validate_office_apparatus_v5_20260917.py'
inputs['learner'] = ref(learner); inputs['observation_schema'] = ref(schema)
scale_node = next(n for n in ast.parse(learner.read_text()).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'OBSERVATION_SCALE' for t in n.targets))
scale = eval(compile(ast.Expression(scale_node.value), str(learner), 'eval'), {'np':np})
assert scale.shape == (48,)
with np.load(anchor, allow_pickle=False) as saved:
    indices = saved['indices'].copy(); all_features = saved['features'].copy()
    rewards = saved['rewards'].copy(); q = saved['q_after'].copy(); masks = saved['masks'].copy()
records = []; features = []
for cycle in [49,55,56]:
    root = B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1/vmc/train'
    episodes = root/'episodes.jsonl'; inputs[f'episodes{cycle}'] = ref(episodes)
    matches = [json.loads(s) for s in episodes.read_text().splitlines() if json.loads(s)['condition'] == 'active_short_train_0600']
    assert len(matches) == 1
    ep = matches[0]; index = ep['total_steps']-1; k = int(np.flatnonzero(indices == index)[0])
    path = Path(ep['episode_path']); terminal = read(path/'TERMINAL.json')
    inputs[f'terminal{cycle}'] = ref(path/'TERMINAL.json')
    journal = path/'actor_intervals.jsonl'; inputs[f'journal{cycle}'] = ref(journal)
    rows = journal.read_text().splitlines(); assert len(rows) == ep['steps'] == 1375
    last = json.loads(rows[-1]); scaled = np.asarray(last['observation'], np.float32)/scale
    np.testing.assert_array_equal(scaled, all_features[k,:48])
    assert ep['model_sha256'] == terminal['model_sha256']
    features.append(all_features[k].copy())
    records.append(dict(cycle=cycle, replay_index=index, task=ep['task_success'], strict=ep['strict_success'],
        model_sha256=ep['model_sha256'], episode_reward=ep['reward'], terminal_reward=float(rewards[k]),
        external_penetration_peak_mm=1000*terminal['interval']['external_penetration_peak_m'],
        q=q[:,k].tolist(), masks=masks[:,k].tolist(), canonical48_exactly_reproduced=True))
assert [r['replay_index'] for r in records[:2]] == [2050526,2299142]
assert len({r['model_sha256'] for r in records}) == 1
features = np.asarray(features); assert features.shape == (3,57)
groups = {'canonical48':(0,48), 'mixing_context':(48,49), 'critic_clock':(49,50), 'raw_action7':(50,57), 'critic_input57':(0,57)}
pairs = []
for a,b in itertools.combinations(range(3),2):
    delta = features[b].astype(float)-features[a].astype(float)
    metrics = {}
    for name,(lo,hi) in groups.items():
        d=delta[lo:hi]
        metrics[name] = dict(exactly_equal=bool(np.array_equal(features[a,lo:hi],features[b,lo:hi])),
            differing_dimensions=int(np.count_nonzero(d)), l2=float(np.linalg.norm(d)), max_abs=float(np.abs(d).max()))
        assert math.isclose(metrics[name]['l2'],math.sqrt(math.fsum(float(x)**2 for x in d)),rel_tol=1e-12,abs_tol=1e-12)
    pairs.append(dict(cycles=[records[a]['cycle'],records[b]['cycle']], metrics=metrics,
        terminal_reward_delta=records[b]['terminal_reward']-records[a]['terminal_reward']))
np.savez_compressed(OUT/'features.npz',features=features,cycles=np.array([49,55,56]),scale=scale,
    replay_indices=np.array([r['replay_index'] for r in records]))
for v in inputs.values(): assert sha(Path(v['path'])) == v['sha256']
report = dict(passed=True,time=time.time(),records=records,pairs=pairs,inputs=inputs,
    source_sha256=sha(Path(__file__)),features_sha256=sha(OUT/'features.npz'),
    independent_scalar_norm_checks=True,all_source_hashes_unchanged=True,
    selection='Posthoc specified49/55 historical high-error failures and56 same-condition success; all1704 anchor rows retained in source.',
    limitation='Distances use existing learner-scaled canonical48 plus actual context/clock/raw action; no new fitted normalization or closeness threshold. Exact differences do not establish or rule out partial observability, learnability, or causal gradient interference. No convergence claim, no network forward, optimization, physics, replay mutation or configuration change.')
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(records=records,pairs=pairs),indent=2))
