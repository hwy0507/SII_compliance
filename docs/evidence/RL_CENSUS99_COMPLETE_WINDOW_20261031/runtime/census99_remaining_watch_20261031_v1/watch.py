from pathlib import Path
import json,time,os,hashlib,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle99_20261031_v1';F=B/'runs/census99_fixed98_terminal_20261031_v1';C=B/'runtime/census99_prefix_comparison_20261031_v1';N=B/'runs/census99_new_terminal_diagnosis_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 try:s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();return s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
 except FileNotFoundError:return False
def last_guard(path):
 with path.open('rb') as f:
  f.seek(0,2);end=f.tell();f.seek(max(0,end-65536));b=f.read()
 lines=b.split(b'\n');return json.loads(lines[-2])
def main():
 os.sched_setaffinity(0,{54});p=rd(D/'PLAN.json');assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==p['source_sha256'];guard=p['guard'];start=time.monotonic();rows=[];last_print=-60
 for j in p['jobs']:assert live(j['identity'])
 for j in guard['identities']:assert live(j)
 with (D/'OBSERVATIONS.jsonl').open('x') as log:
  while True:
   for j in guard['identities']:assert live(j)
   assert not Path(guard['root'],'STOP').exists()
   failures=list(R.rglob('*FAILURE*.json'))+list(F.glob('*FAILURE*.json'))+list(C.glob('COMPARISON_FAILURE*'))+list(N.glob('*FAILURE*.json'))+list((B/'runtime/census99_completion_20261031_v1').glob('WAIT_FAILURE*'));assert not failures,failures
   statuses={}
   for j in p['jobs']:
    finished=Path(j['finished']);done=False
    if finished.exists():
     value=rd(finished);assert value[j['finished_key']]==j['finished_value'];done=True
    running=live(j['identity']);assert running or done,(j['name'],'original identity missing without successful terminal receipt')
    statuses[j['name']]=dict(live=running,finished=done)
   progress={}
   for m in ['impedance','admittance','vmc']:
    q=rd(R/m/'train/PROGRESS.json');finish=R/m/'train/FINISHED.json'
    if finish.exists():q=dict(q,steps=rd(finish)['steps'],completed_conditions=30)
    progress[m]=q
   sample=last_guard(Path(guard['root'],'samples.jsonl'));assert time.time()-sample['time']<30
   util=[x['utilization'] for x in sample['gpus']];assert len(util)==4 and min(util)>=50,util
   elapsed=time.monotonic()-start;row=dict(time=time.time(),elapsed_s=elapsed,status=statuses,progress=progress,gpu=util);rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
   ready=all(x['finished'] for x in statuses.values())
   if elapsed-last_print>=30 or ready:
    print(json.dumps(dict(elapsed_s=round(elapsed,1),steps={m:x['steps'] for m,x in progress.items()},complete_conditions={m:x['completed_conditions'] for m,x in progress.items()},finished=[n for n,x in statuses.items() if x['finished']],gpu=util)),flush=True);last_print=elapsed
   if ready or elapsed>=p['maximum_wait_seconds'] or time.time()>=p['deadline_unix']:break
   time.sleep(p['interval_seconds'])
 put(D/'WATCH_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,samples=len(rows),ready_for_full_scientific_review=ready,outcome='all_registered_results_ready' if ready else 'bounded_wait_elapsed_jobs_not_restarted',first=rows[0],last=rows[-1],minimum_gpu=[min(x['gpu'][i] for x in rows) for i in range(4)],automatic100=False,convergence_claim=False))
 print('WATCH_FINISHED ready='+str(ready),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException:put(D/'WATCH_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc(),science_and_guard_not_stopped=True));raise
