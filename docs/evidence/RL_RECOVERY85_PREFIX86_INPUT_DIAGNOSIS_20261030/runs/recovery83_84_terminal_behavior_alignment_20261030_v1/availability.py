from pathlib import Path
import json,hashlib,time,os
D=Path(__file__).parent;B=D.parents[1];os.sched_setaffinity(0,{54})
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
report=read(D/'REVIEW.json');results={};inputs=[]
for m in ['impedance','admittance','vmc']:
 root=B/f'runs/parameter_partial75_recovery_cycle84_20261029_v1/{m}';source=root/'trainer_registered.py';s=source.read_text();seam="replay.add(observations=previous['observation']";start=s.index(seam);stop=s.index('                    if done:',start);body=s[start:stop];assert body.index('replay.add(')<body.index('steps += 1')<body.index('learner.update(replay.sample(batch_size))')<body.index('optimizer_log.write')
 reg=read(root/'REGISTRATION.json');assert reg['learner_batch_size']==65536 and reg['learner_updates_per_transition']==1
 p=root/'train/optimizer.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];steps=[r['step'] for r in rows];assert len(steps)==41250 and steps==list(range(steps[0],steps[0]+41250)) and all(r['update_index']==0 for r in rows)
 cases=[]
 for pair in report['methods'][m]['pairs']:
  e=pair['cases']['84'];terminal_step=e['terminal_replay_index']+1;eligible=sum(x>=terminal_step for x in steps);assert eligible==steps[-1]-terminal_step+1
  cases.append(dict(condition=pair['condition'],terminal_transition_step=terminal_step,final_step=steps[-1],optimizer_updates_after_append_including_same_step=eligible,maximum_accepted_minibatches_that_could_include_row=eligible,actual_sampled_count_unknown=True,task=e['task'],strict=e['strict'],terminal_prediction=e.get('terminal_prediction')))
 results[m]=sorted(cases,key=lambda r:r['terminal_transition_step']);inputs.extend([ref(source),ref(p),ref(root/'REGISTRATION.json')])
out=dict(passed=True,time=time.time(),methods=results,inputs=inputs,new_physics=0,optimizer_updates=0,new_network_forward=0,limitation='Exact logged update opportunities after each complete84 terminal append. Batch samples were not saved; opportunity is not actual row inclusion and one accepted batch may repeat a row. Rejected draw attempts are not optimizer updates. No independent RNG reconstruction, causal claim, health threshold or reward/horizon change.')
with (D/'UPDATE_AVAILABILITY_REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
for m,rows in results.items():print(m,[(r['condition'],r['optimizer_updates_after_append_including_same_step']) for r in rows[-3:]])
