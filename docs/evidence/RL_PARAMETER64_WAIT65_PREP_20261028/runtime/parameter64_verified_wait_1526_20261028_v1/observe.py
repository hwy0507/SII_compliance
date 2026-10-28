from pathlib import Path
import json,time,subprocess,os
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).parent;RUN=B/'runs/parameter_capacity_pool30_cycle64_20261026_v1'
jobs=json.loads((RUN/'LAUNCH.json').read_text())['jobs']
watchers=[(1505869, '39497113'), (1522440, '39501622'), (1758711, '38725355'), (2178507, '39618553'), (2178510, '39618553'), (2458384, '39669245'), (3256866, '37410686'), (3256867, '37410690'), (3256868, '37410690'), (3256869, '37410691'), (3256870, '37410693')]
def identity(pid,ticks):
    p=Path(f'/proc/{pid}/stat')
    try:f=p.read_text().rsplit(')',1)[1].split()
    except FileNotFoundError:return dict(pid=pid,expected_start=ticks,live=False)
    return dict(pid=pid,expected_start=ticks,actual_start=f[19],state=f[0],live=f[19]==ticks and f[0]!='Z')
deadline=time.monotonic()+600;index=0;reason='finite_observation_elapsed'
with (OUT/'SAMPLES.jsonl').open('x') as output:
    while True:
        learners=[]
        for j in jobs:
            p=RUN/j['controller']/'train';v=identity(j['pid'],j['proc_start_ticks']);v.update(controller=j['controller'],progress=json.loads((p/'PROGRESS.json').read_text()),finished=(p/'FINISHED.json').exists(),failure=(p/'FAILURE.json').exists());learners.append(v)
        sample=dict(index=index,time=time.time(),learners=learners,watchers=[identity(p,t) for p,t in watchers],gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader'],text=True),archive_finished=(RUN/'ARCHIVE_REVIEW_FINISHED.json').exists())
        output.write(json.dumps(sample)+'\n');output.flush()
        print(json.dumps(dict(index=index,time=sample['time'],steps=[x['progress']['steps'] for x in learners],gpu=sample['gpu'],all_identities_live=all(x['live'] for x in learners+sample['watchers']))),flush=True)
        if any(not x['live'] or x['failure'] for x in learners) or any(not x['live'] for x in sample['watchers']):reason='identity_or_scientific_state_change';break
        if time.monotonic()>=deadline:break
        index+=1;time.sleep(30)
(OUT/'OBSERVER_FINISHED.json').write_text(json.dumps(dict(time=time.time(),observer_finished=True,reason=reason,science_restarted=False,science_completion_claim=False),indent=2)+'\n')
