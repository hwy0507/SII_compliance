from pathlib import Path
import os,sys,json,time,hashlib,gc,io
D=Path(__file__).parent;B=D.parents[1];os.sched_setaffinity(0,{12});os.environ['OMP_NUM_THREADS']='1'
import torch
torch.set_num_threads(1)
sys.path[:0]=[str(D),str(B/'runtime/parameter86_half_std_paired_20261030_v3'),str(B/'runtime/source_train17_clock/source/tools')]
from persisted_entropy_target import entropy_class,KEY
from published_compliance_learner_20261025 import PublishedLearner
from published_pair_reduction_learner_20261026 import pair_class
from validate_published_finite_check_20261025 import digest

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert json.loads((D/'ENTROPY_INTERFACE_REVIEW.json').read_text())['passed']
review=json.loads((B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1/REVIEW.json').read_text());rows=[]
for method in ['impedance','admittance','vmc']:
 p=B/f'runs/parameter_partial75_recovery_cycle87_archive_20261029_v1/{method}/cycle_00087.pt';original_hash=sha(p);assert original_hash==review['methods'][method]['checkpoint_sha256']
 ck=torch.load(p,map_location='cpu',weights_only=False);assert ck['cycle']==87 and ck['boundary']=='complete_condition_cycle'
 dim=ck['replay']['arrays']['actions'].shape[1];replay_digest=digest(ck['replay']);parent=digest(ck['learner']);state=ck['learner'];seed=ck['seed'];del ck['replay'];gc.collect()
 base=pair_class(PublishedLearner,'minimum' if method=='impedance' else 'mean');args=dict(dimension=dim,direct=False,seed=seed,device='cuda:0',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
 cls=entropy_class(base,target=-dim,dimension=dim,parent_digest=parent,allow_parent=True)
 learner=cls(B/'runtime/source_train17_clock',**args);learner.load_state_dict(state);saved=learner.state_dict();plain=dict(saved);plain.pop(KEY);assert digest(plain)==parent and digest(state)==parent
 buffer=io.BytesIO();torch.save(saved,buffer);buffer.seek(0)
 resume=entropy_class(base,target=-dim,dimension=dim,parent_digest=parent)(B/'runtime/source_train17_clock',**args);resume.load_state_dict(torch.load(buffer,weights_only=False));assert digest(resume.state_dict())==digest(saved)
 assert resume.learner.target_entropy==-dim and resume.learner.num_gradient_steps==state['num_gradient_steps']
 assert sha(p)==original_hash
 rows.append(dict(method=method,checkpoint=str(p),checkpoint_sha256=original_hash,parent_learner_digest=parent,replay_digest_read_only=replay_digest,original_target=-dim,marker=saved[KEY],full_learner_weights_optimizers_rng_exact_except_new_marker=True,serialized_roundtrip_exact=True,original_checkpoint_bytes_unchanged=True,checkpoint_update_count_unchanged=True,actual_optimizer_updates=0,physics=0,replay_restoration_not_claimed=True))
 print('PASSED',method,flush=True)
 del learner,resume,saved,plain,state,ck,buffer;gc.collect();torch.cuda.empty_cache()
report=dict(passed=True,time=time.time(),methods=rows,actual_checkpoint_optimizer_updates=0,new_physics=0,scientific_target_selected=False,automatic88=False,adapter_sha256=sha(D/'persisted_entropy_target.py'))
(D/'ENTROPY_ACTUAL87_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
