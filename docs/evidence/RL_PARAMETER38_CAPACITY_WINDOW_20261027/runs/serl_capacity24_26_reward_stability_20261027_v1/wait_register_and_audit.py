from pathlib import Path
import hashlib,json,subprocess,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
root=Path(__file__).parent
os.sched_setaffinity(0,{52})
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 plan=json.loads((root/'PLAN.json').read_text())
 assert plan['cycles']==[23,24,25,26] and plan['stability_window']==[24,25,26]
 source=root/'audit_serl_capacity24_26_reward_stability_20261027.py'
 assert sha(source)==plan['source_sha256']
 deadline=time.monotonic()+plan['wait_deadline_seconds']
 while True:
  complete=True
  for c in plan['cycles']:
   run=Path(plan['runs'][str(c)]['run']);review=Path(plan['runs'][str(c)]['review'])
   assert not (run/'direct/FAILURE.json').exists()
   assert not list(review.rglob('*FAILURE.json'))
   if not (review/'FINISHED.json').exists():complete=False
   else:
    assert json.loads((review/'FINISHED.json').read_text())['completed']
    assert json.loads((review/'REVIEW.json').read_text())['passed']
  if complete:break
  assert time.monotonic()<deadline,'Registered21600-second wait expired; no automatic extension'
  time.sleep(5)
 reg={k:plan[k] for k in ['cycles','stability_window','bootstrap_seed','bootstrap_replicates','relative_change_limit','near_zero_guard','source_sha256','partially_prospective','registration_state','capacity_marker']}
 reg['inputs']={};reg['time']=time.time()
 assert sha(Path(plan['baseline_protocol']['path']))==plan['baseline_protocol']['sha256']
 for c in plan['cycles']:
  run=Path(plan['runs'][str(c)]['run']);review=Path(plan['runs'][str(c)]['review'])
  files=dict(protocol=run/'REGISTRATION.json',review=review/'REVIEW.json',health=review/'DIAGNOSIS.json',finished=review/'FINISHED.json',episodes=run/'direct/episodes.jsonl',optimizer=run/'direct/optimizer.jsonl')
  reg['inputs'][str(c)]={k:dict(path=str(p),sha256=sha(p)) for k,p in files.items()}
 with (root/'REGISTRATION.json').open('x') as f:f.write(json.dumps(reg,indent=2)+'\n')
 subprocess.run([str(B/'env/bin/python'),str(source),'--registration',str(root/'REGISTRATION.json'),'--output',str(root)],check=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  (root/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
