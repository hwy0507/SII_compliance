from pathlib import Path
import json,hashlib,math,statistics,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/vmc49_first5000_followup_20261027_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'REVIEW.json').read_text());assert r['passed'];assert sha(O/'FIRST5000.jsonl')==r['prefix_sha256'];assert sha(O/'PLAN.json')==r['plan_sha256']
rows=[json.loads(x) for x in (O/'FIRST5000.jsonl').read_text().splitlines()];assert [x['step'] for x in rows]==list(range(2018251,2023251));assert all(math.isfinite(v) for x in rows for v in x.values() if isinstance(v,(int,float)))
for part,s in [(rows,r['summary'])]+[(rows[i*1000:(i+1)*1000],r['blocks'][i]) for i in range(5)]:
 loss=[x['agent_train/q_loss'] for x in part];entropy=[x['agent_train/actor_entropy'] for x in part];alpha=[x['agent_train/entropy_coefficient'] for x in part]
 assert len(part)==s['count'] and part[0]['step']==s['first_step'] and part[-1]['step']==s['last_step']
 assert math.isclose(statistics.fmean(loss),s['mean_q_loss'],abs_tol=1e-12) and max(loss)==s['maximum_q_loss'];assert math.isclose(statistics.fmean(entropy),s['actor_entropy_mean'],abs_tol=1e-12);assert [min(alpha),max(alpha)]==s['alpha_range']
for n in [10,50,100]:assert sum(x['agent_train/q_loss']>n for x in rows)==r['loss_counts'][f'over{n}']
out=dict(passed=True,time=time.time(),prefix_sha256=sha(O/'FIRST5000.jsonl'),review_sha256=sha(O/'REVIEW.json'),plan_sha256=sha(O/'PLAN.json'),independent_saved_arithmetic=True,new_physics=0,optimizer_updates=0,convergence_claim=False,scope='Original first5000 only; no expanded prefix or rerun')
(O/'SAVED_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');(O/'saved_audit.py').write_bytes(Path(__file__).read_bytes());print(out)
T=B/'runs/parameter48_serl29_transition_20261027_v1';obs=json.loads((T/'OBSERVATION.json').read_text());launch=json.loads((B/'runs/parameter_capacity_pool30_cycle49_20261026_v1/LAUNCH.json').read_text());bounds={}
for pid,job in zip([359275,359279,359281],launch['jobs']):
 x=obs['parent_observations'][str(pid)];bounds[job['controller']]=dict(old_pid=pid,next_pid=job['pid'],old_last_live=x['last_seen_alive'],old_first_exited=x['first_seen_exited'],next_spawn=job['time'],seconds_lower=job['time']-x['first_seen_exited'],seconds_upper=job['time']-x['last_seen_alive'])
(T/'PARAMETER_PARTIAL_RECEIPT.json').write_text(json.dumps(dict(time=time.time(),bounds=bounds,observer_complete=False,scope='Parameter48 to49 only; process exit-to-spawn bounds, not exact GPU idle; original observer continues Direct29 to30'),indent=2)+'\n');print(bounds)
