from pathlib import Path
import json,hashlib,time,socket
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;P=B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
d=read(P)
assert d['direct_numerical_criterion_satisfied'] and not d['launch34'] and not d['overall_goal_complete']
refs=dict(d['evidence']);refs['checkpoint33']=d['latest_complete_checkpoint']
for r in refs.values():assert sha(r['path'])==r['sha256']
assert d['original_reward_window']==[27,28,29] and d['task_success']==d['strict_success']==0 and d['frozen_evidence_cycle']==29 and d['latest_complete_training_cycle']==33
assert read(B/'runs/serl_take_cycle33_review_20261027_v1/FINISHED.json')['completed']
r=dict(time=time.time(),host=socket.gethostname(),passed=True,decision=dict(path=str(P),sha256=sha(P)),bound_evidence_and_checkpoint_hashes=refs,scope='Current-container read-only persistence check of the existing Direct33 empirical numerical decision and exact checkpoint. No new convergence gate, bootstrap, forward, training or frozen evaluation. Historical GPU snapshot in evidence remains historical.',direct34=False,task_strict=[0,0],frozen_evidence_cycle=29,latest_complete_cycle=33,overall_goal_complete=False,remaining_goal_scope='Parameter reward stability and healthy loss remain unproved. Original frozen-policy/final comparison and specified-ESN requirements are not established by current77/78 preparation; no historical ESN substitution.',new_physics=0,optimizer_updates=0,source_sha256=sha(Path(__file__)))
(D/'DIRECT33_PERSISTENCE_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print('Existing Direct33 decision evidence and exact checkpoint preserved; not overall completion')
