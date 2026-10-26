from pathlib import Path
import json,hashlib,time,collections,os
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
out=B/'runs/parameter19_to20_paired_review_20261026_v1';out.mkdir()
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
methods={};sources=[]
for m in ['impedance','admittance','vmc']:
 cycles={}
 for cycle in [19,20]:
  review=B/f'runs/parameter_pool30_cycle{cycle}_review_20261026_v1';assert json.loads((review/'FINISHED.json').read_text())['completed'];assert json.loads((review/'REVIEW.json').read_text())['passed'];sources.append(ref(review/'REVIEW.json'))
  file=B/f'runs/parameter_pool30_cycle{cycle}_20261026_v1/{m}/train/episodes.jsonl';sources.append(ref(file))
  rows=[e for e in map(json.loads,file.read_text().splitlines()) if e['cycle']==cycle];assert len(rows)==30
  records={}
  for e in rows:
   path=Path(e['episode_path'])/'TERMINAL.json';t=json.loads(path.read_text());sources.append(ref(path))
   for k in ['task_success','strict_success','abort_reason','full_task_horizon_completed']:assert e[k]==t['result'][k]
   records[e['condition']]=dict(condition=e['condition'],task=e['task_success'],strict=e['strict_success'],physical_valid=t['result']['physical_valid'],stage=t['result']['final_task_stage'],reward=e['reward'],terminal=ref(path))
  assert len(records)==30;cycles[cycle]=records
 assert set(cycles[19])==set(cycles[20])
 changed=[dict(condition=c,before=cycles[19][c],after=cycles[20][c]) for c in sorted(cycles[20]) if any(cycles[19][c][k]!=cycles[20][c][k] for k in ['task','strict','physical_valid','stage'])]
 methods[m]=dict(changed=changed,all_conditions=cycles)
result=dict(time=time.time(),passed=True,methods=methods,sources=sources,source=ref(Path(__file__)),new_physics=0,optimizer_updates=0,limitation='Descriptive condition-matched comparison of changing online training policies. Terminal physical_valid labels are checked against original receipts, not a new substep audit or proof of a causal policy effect. All30 conditions retained, no selected-seed training or changes to gates.')
(out/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
print({m:[dict(condition=e['condition'],before=[e['before']['task'],e['before']['strict']],after=[e['after']['task'],e['after']['strict']]) for e in v['changed']] for m,v in methods.items()})
