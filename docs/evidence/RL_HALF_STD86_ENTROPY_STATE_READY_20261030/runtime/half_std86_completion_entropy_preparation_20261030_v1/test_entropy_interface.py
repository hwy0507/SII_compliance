from pathlib import Path
import os,sys,json,time,copy,io,hashlib
D=Path(__file__).parent;B=D.parents[1];os.sched_setaffinity(0,{12})
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
import torch
torch.set_num_threads(1)
sys.path[:0]=[str(D),str(B/'runtime/parameter86_half_std_paired_20261030_v3'),str(B/'runtime/source_train17_clock/source/tools')]
from persisted_entropy_target import entropy_class,KEY
from published_compliance_learner_20261025 import PublishedLearner
from published_pair_reduction_learner_20261026 import pair_class
from validate_published_finite_check_20261025 import digest
rows=[];negative=0
for dim,reduction in [(5,'minimum'),(7,'mean')]:
 base=pair_class(PublishedLearner,reduction)
 args=dict(dimension=dim,direct=False,seed=20261030,device='cpu',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
 legacy=base(B/'runtime/source_train17_clock',**args);state=legacy.state_dict();parent=digest(state)
 cls=entropy_class(base,target=-dim,dimension=dim,parent_digest=parent,allow_parent=True)
 wrapped=cls(B/'runtime/source_train17_clock',**args);wrapped.load_state_dict(state)
 saved=wrapped.state_dict();plain=dict(saved);plain.pop(KEY);assert digest(plain)==parent
 buf=io.BytesIO();torch.save(saved,buf);buf.seek(0);persisted=torch.load(buf,weights_only=False)
 restored=entropy_class(base,target=-dim,dimension=dim,parent_digest=parent)(B/'runtime/source_train17_clock',**args);restored.load_state_dict(persisted);assert digest(restored.state_dict())==digest(saved)
 for bad in [state,dict(saved,**{KEY:{**saved[KEY],'version':2}}),dict(saved,**{KEY:{**saved[KEY],'target_entropy':-dim-1}}),dict(saved,**{KEY:{**saved[KEY],'action_dimension':dim+1}}),dict(saved,**{KEY:{**saved[KEY],'migration_parent_learner_digest':'0'*64}})]:
  before=digest(restored.state_dict())
  try:restored.load_state_dict(bad)
  except ValueError:negative+=1
  else:raise AssertionError('Invalid restore accepted')
  assert digest(restored.state_dict())==before
 bad=copy.deepcopy(state);bad['num_gradient_steps']+=1
 try:wrapped.load_state_dict(bad)
 except ValueError:negative+=1
 else:raise AssertionError('Wrong legacy parent accepted')
 restored.learner.target_entropy=-dim-2
 try:restored.state_dict()
 except ValueError:negative+=1
 else:raise AssertionError('Unregistered target drift accepted')
 restored.load_state_dict(saved)
 # A small deterministic synthetic batch tests actual native train plumbing.
 # These are random initialized fixtures, never actual87 or scientific replay.
 rng=np.random.default_rng(20261030);n=32
 arrays=dict(observations=rng.normal(size=(n,50)).astype('float32'),next_observations=rng.normal(size=(n,50)).astype('float32'),actions=rng.uniform(-1,1,size=(n,dim)).astype('float32'),rewards=rng.normal(size=(n,1)).astype('float32'),dones=np.ones((n,1),'float32'),masks=np.ones((n,5),'float32'))
 legacy.load_state_dict(state);m0=legacy.update(arrays);after0=legacy.state_dict();grad0=float(legacy.learner.log_alpha.grad)
 wrapped.load_state_dict(state);m1=wrapped.update(arrays);after1=wrapped.state_dict();after1.pop(KEY)
 assert m1.pop('registered_entropy_target/applied')==-dim and m0==m1 and digest(after0)==digest(after1)
 alt=entropy_class(base,target=-dim-1.,dimension=dim,parent_digest=parent,allow_parent=True)(B/'runtime/source_train17_clock',**args);alt.load_state_dict(state)
 m2=alt.update(arrays);grad2=float(alt.learner.log_alpha.grad)
 assert m2['agent_train/target_entropy']==m2['registered_entropy_target/applied']==-dim-1.
 assert abs((grad2-grad0)-1.)<2e-6
 ast=alt.state_dict();buf=io.BytesIO();torch.save(ast,buf);buf.seek(0)
 alt_resume=entropy_class(base,target=-dim-1.,dimension=dim,parent_digest=parent)(B/'runtime/source_train17_clock',**args);alt_resume.load_state_dict(torch.load(buf,weights_only=False));assert digest(alt_resume.state_dict())==digest(ast)
 rows.append(dict(dimension=dim,original_target=-dim,alternate_fixture_target=-dim-1.,same_target_update_exact=True,full_state_roundtrip_exact=True,alternate_target_roundtrip_exact=True,alpha_gradient_delta=grad2-grad0,synthetic_native_update_calls=3))
for bad in [float('nan'),float('inf'),True]:
 try:entropy_class(base,target=bad,dimension=7,parent_digest=parent)
 except ValueError:negative+=1
 else:raise AssertionError('Invalid target accepted')
report=dict(passed=True,time=time.time(),rows=rows,negative_cases=negative,synthetic_random_fixture_native_update_calls=6,actual_checkpoint_optimizer_updates=0,new_physics=0,scientific_target_selected=False,adapter_sha256=hashlib.sha256((D/'persisted_entropy_target.py').read_bytes()).hexdigest())
(D/'ENTROPY_INTERFACE_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
