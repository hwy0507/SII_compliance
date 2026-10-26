from pathlib import Path
import json,hashlib,os,time,statistics
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/admittance26_terminal_loss_20261026_v1';os.sched_setaffinity(0,{52})
reg=json.loads((out/'REGISTRATION.json').read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(__file__)==reg['source_sha256']
for ref in reg['inputs'].values():assert sha(ref['path'])==ref['sha256']
def lines(k):return [json.loads(v) for v in Path(reg['inputs'][k]['path']).read_text().splitlines()]
old={e['condition']:e for e in lines('episodes25')};new={e['condition']:e for e in lines('episodes26')};ts=lines('transitions26');opt=lines('optimizer26')
assert old.keys()==new.keys() and len(old)==30 and len(ts)==len(opt)==41250
assert [t['step'] for t in ts]==[o['step'] for o in opt]
loss=[o['agent_train/q_loss'] for o in opt];terms=[]
for i,t in enumerate(ts):
 if not t['done']:continue
 k=t['condition'];a=old[k];b=new[k]
 before=loss[max(0,i-1000):i];after=loss[i:min(len(loss),i+1000)]
 terms.append(dict(condition=k,step=t['step'],within_cycle_index=i,old_task=a['task_success'],new_task=b['task_success'],old_strict=a['strict_success'],new_strict=b['strict_success'],new_final_stage=b['final_task_stage'],terminal_reward=t['reward'],new_episode_reward=b['reward'],old_episode_reward=a['reward'],mean_loss_previous_up_to1000=statistics.mean(before) if before else None,previous_count=len(before),mean_loss_following_up_to1000=statistics.mean(after),following_count=len(after)))
assert len(terms)==30
blocks=[dict(start_index=i,end_index=min(i+1000,len(loss)),mean_loss=statistics.mean(loss[i:i+1000]),new_terminals=sum(i<=r['within_cycle_index']<i+1000 for r in terms),new_strict_failures=sum(i<=r['within_cycle_index']<i+1000 and not r['new_strict'] for r in terms)) for i in range(0,len(loss),1000)]
result=dict(passed=True,time=time.time(),strict_lost=[r for r in terms if r['old_strict'] and not r['new_strict']],strict_gained=[r for r in terms if not r['old_strict'] and r['new_strict']],terminal_insertions=terms,blocks=blocks,new_physics=0,optimizer_updates=0,convergence_claim=False,limitation='Retrospective temporal association of terminal insertions with optimizer loss under unchanged terminal128 weighting. Nearby windows overlap and policies/states change. Does not establish which replay samples caused loss spikes or justify a weight/LR change.')
(out/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
