from pathlib import Path
import hashlib,json,subprocess,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
root=Path(__file__).parent
os.sched_setaffinity(0,{52})
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 plan=json.loads((root/'PLAN.json').read_text())
 assert plan['cycles']==[19,20,21,22] and plan['stability_window']==[20,21,22]
 source=root/'audit_serl20_22_reward_stability_20261027.py'
 assert sha(source)==plan['source_sha256']
 deadline=time.monotonic()+plan['wait_deadline_seconds']
 while True:
  complete=True
  for c in plan['cycles']:
   run=B/'runs'/f'serl_multistep_batch65536_cycle{c}_20261026_v1'
   review=B/'runs'/f'serl_multistep_batch65536_cycle{c}_review_20261026_v1'
   assert not (run/'direct/FAILURE.json').exists()
   assert not list(review.rglob('*FAILURE.json'))
   if not (review/'FINISHED.json').exists():complete=False
   else:
    assert json.loads((review/'FINISHED.json').read_text())['completed']
    assert json.loads((review/'REVIEW.json').read_text())['passed']
  if complete:break
  assert time.monotonic()<deadline,'Registered10800-second wait expired; no automatic extension'
  time.sleep(5)
 reg={k:plan[k] for k in ['cycles','stability_window','bootstrap_seed','bootstrap_replicates','relative_change_limit','near_zero_guard','source_sha256','partially_prospective','registration_state']}
 reg['inputs']={};reg['time']=time.time()
 for c in plan['cycles']:
  run=B/'runs'/f'serl_multistep_batch65536_cycle{c}_20261026_v1';review=B/'runs'/f'serl_multistep_batch65536_cycle{c}_review_20261026_v1'
  files=dict(protocol=run/'REGISTRATION.json',review=review/'REVIEW.json',health=review/'DIAGNOSIS.json',finished=review/'FINISHED.json',episodes=run/'direct/episodes.jsonl',optimizer=run/'direct/optimizer.jsonl')
  reg['inputs'][str(c)]={k:dict(path=str(p),sha256=sha(p)) for k,p in files.items()}
  if str(c) in plan['known_complete_inputs']:assert reg['inputs'][str(c)]==plan['known_complete_inputs'][str(c)]
 with (root/'REGISTRATION.json').open('x') as f:f.write(json.dumps(reg,indent=2)+'\n')
 subprocess.run([str(B/'env/bin/python'),str(source),'--registration',str(root/'REGISTRATION.json'),'--output',str(root)],check=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  (root/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
