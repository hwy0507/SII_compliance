"""Bounded readonly follower of the original95 jobs; recognizes recorded natural exits."""
from pathlib import Path
import json,time,hashlib,os,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_census_cycle95_20261031_v1';V=B/'runs/parameter_census_cycle95_review_20261031_v1';F=B/'runs/census95_fixed94_terminal_20261031_v1';C=B/'runtime/census95_comparison_20261031_v1'
rd=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def identity(pid):
 try:
  s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
  return None if s[0]=='Z' else dict(pid=pid,start=s[19])
 except FileNotFoundError:return None
def live(j):return identity(j['pid'])==dict(pid=j['pid'],start=str(j.get('start',j.get('proc_start_ticks'))))
def main():
 os.sched_setaffinity(0,{11});jobs=rd(T/'LAUNCH.json')['jobs'];guards=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')['identities'];samplers={}
 for j in jobs:
  assert live(j);m=j['controller'];children=list(map(int,Path('/proc',str(j['pid']),'task',str(j['pid']),'children').read_text().split()));assert len(children)==30
  entries=[]
  for pid in children:
   ident=identity(pid);assert ident;args=Path('/proc',str(pid),'cmdline').read_bytes().decode().split('\0');out=Path(args[args.index('--output')+1]);assert out.parent==T/m/'train/cycle_00095';entries.append(dict(**ident,condition=out.name,output=str(out)))
  assert len({e['condition'] for e in entries})==30;samplers[m]=entries
 consumers=[dict(name='archive',job=rd(T/'MONITOR_LAUNCH.json'),finished=str(T/'ARCHIVE_REVIEW_FINISHED.json'),key='completed'),dict(name='terminal',job=rd(F/'LAUNCH.json'),finished=str(F/'FINISHED.json'),key='passed'),dict(name='comparison',job=rd(C/'PROCESS.json'),finished=str(C/'COMPARISON_FINISHED.json'),key='passed')]
 for x in consumers:assert live(x['job'])
 for j in guards:assert live(j)
 deadline=min(time.time()+1800,rd(T/'MONITOR_LAUNCH.json')['time']+14400)
 put(D/'FOLLOW_PLAN.json',dict(time=time.time(),deadline=deadline,interval_seconds=10,jobs=jobs,samplers=samplers,consumers=consumers,guards=guards,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),missing_sampler_grace_seconds=60,new_training=False,new_analysis_consumer=False))
 rows=[];first_missing={};start=time.monotonic()
 with (D/'OBSERVATIONS.jsonl').open('x') as log:
  while True:
   assert not list(T.rglob('*FAILURE.json')) and not list(F.glob('*FAILURE*')) and not list(C.glob('*FAILURE*'))
   for j in guards:assert live(j)
   states={}
   for j in jobs:
    m=j['controller'];run=T/m/'train';progress=rd(run/'PROGRESS.json');finished=run/'FINISHED.json'
    if finished.exists():assert rd(finished)['status']=='stopped_at_complete_cycle' and rd(finished)['cycles_completed']==1
    else:assert live(j)
    episodes=[json.loads(l) for l in (run/'episodes.jsonl').read_text().splitlines()];done={e['condition'] for e in episodes};assert len(done)==len(episodes) and len(done)<=30
    active=[];closed=[];pending=[]
    for s in samplers[m]:
     if live(s):active.append(s['condition'])
     elif s['condition'] in done:
      e=next(e for e in episodes if e['condition']==s['condition']);roll=rd(Path(s['output'])/'rollout.json')
      assert e['cycle']==95 and e['task_success']==roll['task_success'] and e['strict_success']==roll['strict_success'] and e['abort_reason']==roll['abort_reason'];closed.append(s['condition'])
     else:
      key=(m,s['pid']);first_missing.setdefault(key,time.monotonic());assert time.monotonic()-first_missing[key]<60;pending.append(s['condition'])
    if live(j):
     current=set(map(int,Path('/proc',str(j['pid']),'task',str(j['pid']),'children').read_text().split()));assert current<={s['pid'] for s in samplers[m]}
    if finished.exists():assert len(done)==30
    states[m]=dict(steps=progress['steps'],learner_live=live(j),train_finished=finished.exists(),completed_conditions=len(done),active_original_samplers=len(active),closed_original_samplers=len(closed),transition_pending=pending)
   cs={}
   for x in consumers:
    p=Path(x['finished']);complete=p.exists()
    if complete:assert rd(p)[x['key']] is True
    else:assert live(x['job'])
    cs[x['name']]=dict(live=live(x['job']),finished=complete)
   row=dict(time=time.time(),elapsed_s=time.monotonic()-start,methods=states,consumers=cs,guard_identities_live=5);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
   all_complete=all(x['train_finished'] for x in states.values()) and all(x['finished'] for x in cs.values())
   if all_complete or time.time()>=deadline:break
   time.sleep(10)
 assert all(rows[-1]['methods'][m]['steps']>rows[0]['methods'][m]['steps'] for m in samplers)
 put(D/'FOLLOW_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),all_complete=all_complete,first=rows[0],last=rows[-1],original_identities=101,natural_sampler_exits_bound_to_original_episode_and_rollout=True,new_training=False,new_analysis_consumer=False,scope='Process lifecycle/progress only; complete scientific and plot review remains separate.'))
 print('Original95 follow finished; all_complete=',all_complete,flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:put(D/'FOLLOW_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
