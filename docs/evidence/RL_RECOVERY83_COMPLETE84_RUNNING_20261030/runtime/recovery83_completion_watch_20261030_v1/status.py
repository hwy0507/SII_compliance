from pathlib import Path
import json,time
D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(p.read_text())
plan=read(D/'PLAN.json');states={}
for j in plan['identities']:
 p=Path(f'/proc/{j["pid"]}/stat');live=False
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split();live=s[19]==j['proc_start_ticks'] and s[0]!='Z'
 if live:states[j['name']]='live'
 else:
  assert j['terminal_requirements'],j['name']
  for r in j['terminal_requirements']:assert read(Path(r['path']))[r['key']]==r['value']
  states[j['name']]='verified_terminal'
 for p in j['failure_paths']:assert not Path(p).exists(),p
progress={m:read(Path(plan['run'])/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
g=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
for rel in ['parameter_partial75_recovery_cycle83_review_20261029_v1','parameter_recovery83_loss_20261029_v1','vmc_recovery83_terminal_followup_20261029_v1','admittance_recovery83_terminal_followup_20261029_v1']:
 p=B/'runs'/rel
 if (p/'REVIEW.json').exists():print('REVIEW ready:',rel)
print(json.dumps(dict(time=time.time(),steps={m:v['steps'] for m,v in progress.items()},completed={m:v['completed_conditions'] for m,v in progress.items()},terminal=[n for n,s in states.items() if s=='verified_terminal'],gpu=[v['utilization'] for v in g['gpus']],gpu_age=time.time()-g['time'])))
