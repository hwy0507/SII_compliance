from pathlib import Path
import os,json,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');root=B/'runs/parameter_capacity_pool30_cycle36_review_20261026_v1';learners=[2805435,2805436,2805437];coordinator=2805441;limit=time.monotonic()+7200
while any(Path(f'/proc/{pid}').exists() for pid in learners):
 assert time.monotonic()<limit
 time.sleep(2)
rows=[]
while not (root/'FINISHED.json').exists():
 assert time.monotonic()<limit
 if not Path(f'/proc/{coordinator}').exists():raise RuntimeError('Original review coordinator exited without FINISHED')
 pending=[coordinator]
 while pending:
  pid=pending.pop()
  try:
   cmd=Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0',b' ').decode()
   assert str(root) in cmd,'Not the registered original parameter36 review process'
   previous=sorted(os.sched_getaffinity(pid))
   if previous!=[13]:
    os.sched_setaffinity(pid,{13});rows.append(dict(pid=pid,time=time.time(),old_cpus=previous,new_cpus=[13],command=cmd))
   childfile=Path(f'/proc/{pid}/task/{pid}/children')
   pending.extend(int(v) for v in childfile.read_text().split())
  except (FileNotFoundError,ProcessLookupError):pass
 (root/'TRANSITION_CPU_ASSIGNMENT.json').write_text(json.dumps(dict(reason='Original parameter36 learner exited; use freed CPU13 for original read-only review before37 launches; no source/state/precision change.',processes=rows),indent=2)+'\n')
 time.sleep(2)
print('Original parameter36 review completed; temporary scheduler adjustment finished.',flush=True)
