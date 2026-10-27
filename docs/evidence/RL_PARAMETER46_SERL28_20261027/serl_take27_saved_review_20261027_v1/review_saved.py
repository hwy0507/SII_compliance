from pathlib import Path
import json,time,hashlib,math,os
O=Path(__file__).parent;B=O.parents[1];P=B/'runs/serl_recovery26_take27_review_20261027_v1';run=B/'runs/serl_recovery26_take27_20261027_v1/direct';os.sched_setaffinity(0,{54});os.nice(15)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
try:
 limit=time.monotonic()+1800
 while not (P/'FINISHED.json').exists():
  assert time.monotonic()<limit,'Original27 full review bounded wait expired'
  assert not (run/'FAILURE.json').exists() and not (run.parent/'DRIVER_FAILURE.json').exists()
  time.sleep(3)
 r=json.loads((P/'REVIEW.json').read_text());h=json.loads((P/'DIAGNOSIS.json').read_text());assert r['passed'];row=r['methods']['direct']
 ep=run/'episodes.jsonl';op=run/'optimizer.jsonl';episodes=[json.loads(s) for s in ep.read_text().splitlines()];opts=[json.loads(s) for s in op.read_text().splitlines()]
 assert len(episodes)==30 and len({e['condition'] for e in episodes})==30 and all(e['cycle']==27 for e in episodes)
 assert len(opts)==row['new_transitions']==sum(e['steps'] for e in episodes)
 assert [r['step'] for r in opts]==list(range(row['steps']-len(opts)+1,row['steps']+1))
 assert all(math.isfinite(v) for r in opts for v in r.values() if isinstance(v,(int,float)))
 assert sum(e['task_success'] for e in episodes)==row['task'] and sum(e['strict_success'] for e in episodes)==row['strict']
 assert abs(sum(e['reward'] for e in episodes)/30-row['reward_mean'])<1e-10
 assert row['optimizer_and_network_finite'] and row['retained_replay_all_fields_exact'] and row['max_reward_reconstruction_error']==0
 assert row['multistep_replay']['new_pending_rows']==0 and row['multistep_replay']['quarantined_old_pending_rows']==930
 assert h['network_optimizer_rng_unchanged'] and h['checkpoint_sha256']==row['checkpoint_sha256'] and h['terminal_count']==810
 losses=[r['serl/critic/critic_loss'] for r in opts];alpha=[r['serl/actor/temperature'] for r in opts];assert min(losses)>=0 and min(alpha)>0
 refs=[P/'REVIEW.json',P/'DIAGNOSIS.json',P/'FINISHED.json',ep,op];inputs={str(p):sha(p) for p in refs}
 report=dict(passed=True,time=time.time(),steps=row['steps'],critic_updates=row['updates'],new_transitions=len(opts),task=row['task'],strict=row['strict'],reward_mean=row['reward_mean'],last_critic_loss=losses[-1],first1000_critic_loss=sum(losses[:1000])/1000,last1000_critic_loss=sum(losses[-1000:])/1000,maximum_critic_loss=max(losses),checkpoint_sha256=row['checkpoint_sha256'],aborts=row['aborts'],terminal_mae=h['terminal_q_absolute_error']['mean'],td32_mae=h['sampled_multistep_td_absolute_error']['mean'],quarantined_pending=930,inputs=inputs,new_physics=0,optimizer_updates=0,convergence_claim=False)
 (O/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
except BaseException as e:
 (O/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
