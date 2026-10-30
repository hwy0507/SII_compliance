from pathlib import Path
import json,time,sys
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/history89_violation_pipeline_preflight_20261030_v1';sys.path.insert(0,str(D))
from violation_pipeline import read,sha,ref

def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
review=read(O/'MIGRATION_REVIEW.json');assert review['passed'];commands=[]
for m,r in review['methods'].items():
 reg=read(B/'runs/parameter88_history_frozen_full30_20261030_v1'/m/'REGISTRATION.json');tr=O/m/'REGISTRATION.json';cp=Path(r['checkpoint_path']);journal=B/'runs/parameter_history_cycle89_20261030_v1'/m/'train/cycle_00089/active_short_train_0600/actor_intervals.jsonl'
 reg.update(cpu=12,device='cuda:1',audit_runtime=str(D),training_registration=str(tr),training_registration_sha256=sha(tr),checkpoint=str(cp),checkpoint_sha256=sha(cp),parent_cycle=89,required_review=str(O/'MIGRATION_REVIEW.json'),required_review_sha256=sha(O/'MIGRATION_REVIEW.json'),gate_observations=str(journal),gate_observations_sha256=sha(journal),gate_case_id='active_short_train_0600',source_hashes={p.name:sha(p) for p in D.glob('*.py')})
 put(O/'frozen'/m/'REGISTRATION.json',reg);commands.append(dict(name='frozen_'+m,command=[sys.executable,str(D/'evaluate_violation_preparation.py'),'--registration',str(O/'frozen'/m/'REGISTRATION.json'),'--check-only','--validation-cycle','89']))
commands.append(dict(name='health',command=['taskset','-c','12',sys.executable,str(D/'health_violation_preparation.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--run',str(B/'runs/parameter_history_cycle89_view_20261030_v1'),'--registrations',str(O),'--output',str(O/'health'),'--cycle-archive',str(O/'archive'),'--cycle','89']))
put(O/'CONSUMER_PLAN.json',dict(time=time.time(),commands=commands,scope='Actual evaluator restore/check-only and full readonly health; no new physical evaluation',physics=0,formal_updates=0,budget_seconds=1800,source_plan=ref(D/'PLAN.json')))
print('Consumer commands registered')
