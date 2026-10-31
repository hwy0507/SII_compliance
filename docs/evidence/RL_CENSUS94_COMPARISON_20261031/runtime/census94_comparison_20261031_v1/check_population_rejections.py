from pathlib import Path
import json,time,copy,hashlib
from check_terminal_population import D,B,R,read,first_lines,audit_rows,sha
p=read(D/'CACHE_POPULATION_PLAN.json');assert sha(D/'check_terminal_population.py')==p['source_sha256'];results={}
for m,e in p['methods'].items():
 reg=read(R/m/'REGISTRATION.json');n=reg['post_interruption_continuation']['parent_steps'];t=[json.loads(x) for x in first_lines(R/m/'train/transitions.jsonl',5000).splitlines()];u=[json.loads(x) for x in first_lines(R/m/'train/optimizer.jsonl',5000).splitlines()];base=audit_rows(t,u,n,e['terminal_rows']);assert base['new_terminal_rows']==0
 rejected=[]
 for case in ['missing_update','wrong_step','wrong_population','missed_terminal_growth','wrong_parent_count']:
  tt=copy.deepcopy(t);uu=copy.deepcopy(u);count=e['terminal_rows']
  if case=='missing_update':uu.pop()
  elif case=='wrong_step':uu[-1]['step']-=1
  elif case=='wrong_population':uu[-1]['agent_train/terminal_population']+=1
  elif case=='missed_terminal_growth':tt[-1]['done']=True
  elif case=='wrong_parent_count':count-=1
  try:audit_rows(tt,uu,n,count)
  except ValueError:rejected.append(case)
  else:raise AssertionError('Accepted '+case)
 results[m]=dict(actual_prefix_rows=5000,negative_cases=rejected,synthetic_negative_mutations_only=True,no_actual_new_terminal_claim=True)
with (D/'CACHE_POPULATION_NEGATIVE_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=results,negative_count=15,optimizer_updates=0,physics_steps=0),f,indent=2);f.write('\n')
print('Actual three prefixes accepted;15 corruptions rejected; no real growth claim')
