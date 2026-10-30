from pathlib import Path
import json,time,hashlib,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;os.sched_setaffinity(0,{0})
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert read(B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1/FINISHED.json')['completed'];results={};inputs=[]
for m in ['impedance','admittance','vmc']:
 root=B/f'runs/parameter_partial75_recovery_cycle85_20261029_v1/{m}';source=root/'trainer_registered.py';s=source.read_text();start=s.index("replay.add(observations=previous['observation']");body=s[start:s.index('                    if done:',start)]
 assert body.index('replay.add(')<body.index('steps += 1')<body.index('learner.update(replay.sample(batch_size))')<body.index('optimizer_log.write')
 reg=read(root/'REGISTRATION.json');assert reg['learner_batch_size']==65536 and reg['learner_updates_per_transition']==1
 p=root/'train/optimizer.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];steps=[r['step'] for r in rows];assert len(steps)==41250 and steps==list(range(steps[0],steps[0]+41250)) and all(r['update_index']==0 for r in rows)
 ep=root/'train/episodes.jsonl';episodes=[json.loads(l) for l in ep.read_text().splitlines()];assert len(episodes)==30;cases=[]
 for e in episodes:
  terminal_step=e['total_steps'];eligible=sum(x>=terminal_step for x in steps);assert eligible==steps[-1]-terminal_step+1
  cases.append(dict(condition=e['condition'],replay_index=terminal_step-1,terminal_step=terminal_step,final_step=steps[-1],optimizer_updates_after_append_including_same_step=eligible,actual_sampled_count_unknown=True,task=e['task_success'],strict=e['strict_success']))
 results[m]=cases;inputs.extend([ref(source),ref(p),ref(ep),ref(root/'REGISTRATION.json')])
with (D/'UPDATE_AVAILABILITY85_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=results,inputs=inputs,new_physics=0,new_network_forward=0,optimizer_updates=0,limitation='Retrospective all90 complete85 terminal update opportunities. No actual minibatch row inclusion reconstruction; one batch can include repeated rows. No new health threshold or historical Adam causality.'),f,indent=2);f.write('\n')
for m in ['vmc','admittance']:print(m,[x for x in results[m] if x['condition'] in ['active_short_train_0000','active_short_train_0600']])
