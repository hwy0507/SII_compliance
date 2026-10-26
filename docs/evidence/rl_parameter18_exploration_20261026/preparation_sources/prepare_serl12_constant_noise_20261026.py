from pathlib import Path
import ast, hashlib, json, shutil, subprocess, os, time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'repository/SII_compliance'
old=B/'runs/serl_cycle12_stochastic_representatives_20261026_v1'
out=B/'runs/serl_cycle12_constant_noise_representatives_20261026_v1'
rt=B/'runtime'/out.name
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert read(old/'FINISHED.json')['scientific_review_complete']
assert read(old/'FINAL_SCIENTIFIC_REVIEW.json')['passed']
history=[];seen=set();episodes=[]
for path in sorted((B/'runs').glob('serl*/direct/episodes.jsonl')):
    resolved=path.resolve()
    if resolved in seen:continue
    seen.add(resolved)
    rows=[json.loads(line) for line in resolved.read_text().splitlines()]
    if not rows or any(row['cycle']>12 for row in rows):continue
    history.append(ref(resolved));episodes.extend(rows)
assert len(episodes)==390 and not any(row['task_success'] for row in episodes)
assert sorted({row['cycle'] for row in episodes})==list(range(13))
out.mkdir();shutil.copytree(Path(read(old/'REGISTRATION.json')['audit_runtime']),rt,ignore=shutil.ignore_patterns('__pycache__'))
name='evaluate_serl_seeded_multistep_20261026.py'
shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/name,rt/name)
reg=read(old/'REGISTRATION.json');reg.update(time=time.time(),audit_runtime=str(rt),noise_schedule='episode_constant',baseline_run=str(old),baseline_review=ref(old/'FINAL_SCIENTIFIC_REVIEW.json'),baseline_results=ref(old/'evaluation/RESULTS.json'),history_sources=history,formal_history_episodes=390,formal_history_task_successes=0,
    scope='Finite collection-policy diagnostic: same exact formal12 frozen network and first action seeds as completed independent-noise representatives, but retain one base Gaussian sample per episode. State-dependent public actions continue to change. Zero optimizer/replay writes; no nominal control, demonstrations, corrections, auxiliary weight promotion, or deployment. Three trajectories cannot establish expected success-rate improvement.',
    hypothesis='Per-step independent action noise may cancel temporally coherent exploratory directions; test episode-constant base noise after zero successes in390 formal SERL episodes and near-correct value prediction on failed frozen trajectories.')
reg['source_hashes'][name]=sha(rt/name)
reg.pop('wait_for_profile',None)
s=(old/'coordinator.py').read_text();start=s.index('deadline=time.monotonic()+1800');end=s.index("assert sha(reg['required_review'])",start)
s=s[:start]+"assert sha(reg['baseline_review']['path'])==reg['baseline_review']['sha256'] and json.loads(Path(reg['baseline_review']['path']).read_text())['passed']\nassert sha(reg['baseline_results']['path'])==reg['baseline_results']['sha256']\n"+s[end:]
s=s.replace("'--action-seed',str(reg['action_seed'])","'--action-seed',str(reg['action_seed']),'--noise-schedule',reg['noise_schedule']")
ast.parse(s);(out/'coordinator.py').write_text(s)
s=(old/'review_complete.py').read_text()
s=s.replace("results=read(folder/'RESULTS.json');", "baseline=Path(reg['baseline_run']);assert sha(reg['baseline_review']['path'])==reg['baseline_review']['sha256'];assert sha(reg['baseline_results']['path'])==reg['baseline_results']['sha256'];baseline_report=read(reg['baseline_review']['path']);baseline_episodes={e['condition']:e for e in baseline_report['episodes']};\nresults=read(folder/'RESULTS.json');assert results['evaluation']['noise_schedule']=='episode_constant';")
s=s.replace("key,sample_key=a.jax.random.split(key)", "unused_next_key,sample_key=a.jax.random.split(key)")
s=s.replace("seed=int.from_bytes", "baseline_rows=[json.loads(line) for line in (baseline/'evaluation'/case/'actor_intervals.jsonl').read_text().splitlines()];np.testing.assert_array_equal(rows[0]['observation'],baseline_rows[0]['observation']);np.testing.assert_array_equal(rows[0]['action'],baseline_rows[0]['action'])\n seed=int.from_bytes")
s=s.replace("reports.append(dict(condition=case,", "comparison['baseline_independent_noise']=baseline_episodes[case]['value_comparison'];comparison['baseline_physical_row']=baseline_episodes[case]['physical']['row'];comparison['first_observation_and_action_exact']=True\n reports.append(dict(condition=case,")
s=s.replace("label='realized discounted return'", "label='constant-noise realized discounted return'").replace("label='mean10 critic'", "label='original independent-noise policy mean10 critic'")
s=s.replace("Frozen stochastic SERL12: one realized trajectory per condition, correlated states", "Frozen SERL12 constant-noise behavior: original-policy Q is not this policy value")
s=s.replace("One stochastic trajectory per condition; statewise returns are correlated and do not establish expected-return calibration or confidence intervals.", "One constant-noise trajectory per condition versus original independent-noise trajectories with matched initial samples. Different continuation policy: original-policy critic versus realized returns is not a calibration error. Correlated states, no success-rate confidence intervals, no training deployment.")
ast.parse(s);(out/'review_complete.py').write_text(s)
reg['reviewer_sha256']=sha(out/'review_complete.py');reg['coordinator_sha256']=sha(out/'coordinator.py')
write(out/'REGISTRATION.json',reg)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='0',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'))
with (out/'coordinator.log').open('x') as f:
    p=subprocess.Popen([str(B/'env/bin/python'),str(out/'coordinator.py')],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(out/'LAUNCH.json',dict(pid=p.pid,time=time.time(),automatic_extension=False))
print(json.dumps(dict(pid=p.pid,run=str(out),episodes=3,maximum_physical_substeps=3300000,optimizer_updates=0)))
