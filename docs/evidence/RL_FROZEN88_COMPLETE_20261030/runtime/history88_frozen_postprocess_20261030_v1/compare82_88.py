"""Finite read-only same-seed comparison; all90 cases retained, no policy selection."""
from pathlib import Path
import json,time,hashlib,os,math
B=Path(__file__).resolve().parents[2];O=B/'runs/parameter88_history_frozen_full30_20261030_v1';D=O/'comparison82_88'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
def main():
 os.sched_setaffinity(0,{3});plan=read(D/'PLAN.json');assert sha(__file__)==plan['source']['sha256']
 old=B/'runs/parameter82_frozen_full30_20261030_v1';assert sha(old/'REVIEW.json')==plan['prior_review']['sha256'];assert sha(O/'PLAN.json')==plan['evaluation_plan']['sha256']
 assert read(O/'REVIEW.json')['passed']
 assert not (O/'REVIEW_FAILURE.json').exists()
 before,after=read(old/'REVIEW.json'),read(O/'REVIEW.json');assert before['passed'] and after['passed'] and before['total_episodes']==after['total_episodes']==90
 results={}
 for m in ['impedance','admittance','vmc']:
  a,b=before['methods'][m],after['methods'][m];rp,rq=read(old/m/'REGISTRATION.json'),read(O/m/'REGISTRATION.json')
  assert rp['case_ids']==rq['case_ids'] and rp['action_seed']==rq['action_seed']==2026102638
  pp,pq=read(Path(rp['training_registration'])),read(Path(rq['training_registration']));assert pp['conditions']==pq['conditions']
  for k in ['physics_dt_s','actor_period_s','horizon_s','reference_plan','reference_plan_sha256','torque_thresholds_nm','reward']:assert pp[k]==pq[k],k
  rows=[]
  for case,x,y in zip(rp['case_ids'],a['episodes'],b['episodes']):
   assert x['condition']==y['condition']==case and x['seed']==y['seed']==2026102638
   for root,row in [(old,x),(O,y)]:
    saved=read(root/m/f'{case}_REVIEW.json');assert saved['passed'] and saved['physical']['row']['task_success']==row['task'] and saved['physical']['row']['strict_success']==row['strict']
    assert saved['reward']==row['reward'] and saved['actions']==row['actions']
    assert sha(root/m/case/'rollout.mjb')==next(c['model_sha256'] for c in pp['conditions'] if c['id']==case)
   rows.append(dict(condition=case,before=x,after=y,reward_delta=y['reward']-x['reward'],task_change=int(y['task'])-int(x['task']),strict_change=int(y['strict'])-int(x['strict']),machine_violation_change=int(y['machine_safety_violation'])-int(x['machine_safety_violation'])))
  assert len(rows)==30
  results[m]=dict(rows=rows,mean_reward_delta=math.fsum(r['reward_delta'] for r in rows)/30,task_before=a['task'],task_after=b['task'],strict_before=a['strict'],strict_after=b['strict'],task_gained=[r['condition'] for r in rows if r['task_change']>0],task_lost=[r['condition'] for r in rows if r['task_change']<0],strict_gained=[r['condition'] for r in rows if r['strict_change']>0],strict_lost=[r['condition'] for r in rows if r['strict_change']<0],abort_before=[r['condition'] for r in rows if r['before']['abort_reason']],abort_after=[r['condition'] for r in rows if r['after']['abort_reason']])
 put(D/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,inputs=[ref(old/'REVIEW.json'),ref(O/'REVIEW.json')],all90_pairs_retained=True,new_physics=0,optimizer_updates=0,convergence_claim=False,limitation='Descriptive same external action seed and original30 training conditions, frozen82 vs frozen88 with additional training exposure and the history51 critic amendment. No independent training seeds, unseen evaluation, convergence test, causal claim or specified ESN/final SPT ranking. Actual-contact denominator and no-contact NA preserved from audited per-case metrics; no pooled equal-episode comfort average.'))
 saved=read(D/'REVIEW.json');assert saved['methods']==results
 for m,r in saved['methods'].items():
  assert math.isclose(r['mean_reward_delta'],math.fsum(x['after']['reward'] for x in r['rows'])/30-math.fsum(x['before']['reward'] for x in r['rows'])/30,abs_tol=1e-12)
  for stage in ['before','after']:
   assert sum(x[stage]['task'] for x in r['rows'])==r['task_'+stage] and sum(x[stage]['strict'] for x in r['rows'])==r['strict_'+stage]
 put(D/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),rows=90,all_rows_read_back=True,mean_deltas_recomputed_from_separate_endpoint_sums=True,source=ref(Path(__file__)),review=ref(D/'REVIEW.json')))
if __name__=='__main__':
 try:main()
 except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),automatic_retry=False));raise
