from pathlib import Path
import json,hashlib,time,math,os
O=Path(__file__).parent;B=O.parents[1];P=B/'runs/parameter_capacity_pool30_cycle47_review_20261026_v1';os.sched_setaffinity(0,{54});os.nice(15)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
try:
 limit=time.monotonic()+1800
 while not (P/'FINISHED.json').exists():
  assert time.monotonic()<limit,'Original47 review wait expired'
  for m in ['impedance','admittance','vmc']:assert not (B/'runs/parameter_capacity_pool30_cycle47_20261026_v1'/m/'train/FAILURE.json').exists()
  time.sleep(3)
 r=json.loads((P/'REVIEW.json').read_text());h=json.loads((P/'health/DIAGNOSIS.json').read_text());assert r['passed']
 result={};inputs={}
 for m in ['impedance','admittance','vmc']:
  train=B/'runs/parameter_capacity_pool30_cycle47_20261026_v1'/m/'train';ep=train/'episodes.jsonl';op=train/'optimizer.jsonl'
  es=[json.loads(x) for x in ep.read_text().splitlines()];opts=[json.loads(x) for x in op.read_text().splitlines()];row=r['methods'][m];health=h['methods'][m]
  assert len(es)==30 and len({e['condition'] for e in es})==30 and all(e['cycle']==47 for e in es)
  assert len(opts)==row['new_transitions']==sum(e['steps'] for e in es)
  assert [v['step'] for v in opts]==list(range(row['steps']-len(opts)+1,row['steps']+1))
  assert sum(e['task_success'] for e in es)==row['task'] and sum(e['strict_success'] for e in es)==row['strict']
  assert abs(sum(e['reward'] for e in es)/30-row['reward_mean'])<1e-10
  assert health['network_state_unchanged'] and row['checkpoint_sha256']==health['checkpoint_sha256']
  assert row['optimizer_and_network_finite'] and row['retained_replay_all_fields_exact'] and row['max_reward_reconstruction_error']==0
  assert all(math.isfinite(v) for x in opts for v in x.values() if isinstance(v,(int,float)))
  losses=[x['agent_train/q_loss'] for x in opts];assert min(losses)>=0
  result[m]=dict(steps=row['steps'],new_transitions=len(opts),task=row['task'],strict=row['strict'],reward_mean=row['reward_mean'],last_q_loss=losses[-1],first1000_q_loss=sum(losses[:1000])/1000,last1000_q_loss=sum(losses[-1000:])/1000,maximum_q_loss=max(losses),checkpoint_sha256=row['checkpoint_sha256'],aborts=row['aborts'],terminal_inbag_mae=health['terminal_q_in_bag_absolute_error']['mean'])
  for p in [ep,op]:inputs[str(p)]=sha(p)
 for p in [P/'REVIEW.json',P/'health/DIAGNOSIS.json',P/'FINISHED.json']:inputs[str(p)]=sha(p)
 report=dict(passed=True,time=time.time(),methods=result,inputs=inputs,all_saved_optimizer_numbers_finite=True,new_physics=0,optimizer_updates=0,convergence_claim=False)
 (O/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
except BaseException as e:
 (O/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
