from pathlib import Path
import json,time,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).resolve().parent
os.sched_setaffinity(0,{53})
run=B/'runs/parameter_capacity_pool30_cycle69_20261026_v1'
expected={3088968:41426931,3088970:41426931,3088972:41426931,3088977:41426932,3093145:41428217,3389722:41481329,3373363:41478491,3545889:41509360,3545890:41509360,1085142:41039557,3256866:37410686,3256867:37410690,3256868:37410690,3256869:37410691,3256870:37410693}
for index in range(7):
 sample=dict(index=index,time=time.time(),processes={},methods={})
 for pid,start in expected.items():
  p=Path(f'/proc/{pid}/stat')
  if p.exists():
   st=p.read_text().rsplit(')',1)[1].split();sample['processes'][str(pid)]=dict(state=st[0],start_ticks=int(st[19]),identity_live=st[0]!='Z' and int(st[19])==start)
  else:sample['processes'][str(pid)]=dict(identity_live=False,missing=True)
 for method in ['impedance','admittance','vmc']:
  p=run/method/'train';sample['methods'][method]=dict(progress=json.loads((p/'PROGRESS.json').read_text()),finished=(p/'FINISHED.json').exists(),failure=(p/'FAILURE.json').exists())
 with (OUT/'samples.jsonl').open('a') as stream:stream.write(json.dumps(sample)+'\n')
 print(json.dumps(dict(index=index,time=sample['time'],steps={m:v['progress']['steps'] for m,v in sample['methods'].items()},all_identities_live=all(v['identity_live'] for v in sample['processes'].values()),finished={m:v['finished'] for m,v in sample['methods'].items()},failure={m:v['failure'] for m,v in sample['methods'].items()})),flush=True)
 if index<6:time.sleep(30)
(OUT/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),observer_completed=True,samples=7,scientific_completion_claim=False))+'\n')
