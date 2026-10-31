from pathlib import Path
import sys,json,time,os,copy
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import torch
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).resolve().parent;O=B/'runs/census93_native_compatibility_20261031_v2'
sys.path[:0]=[str(D),str(B/'runtime/violation93_continuation_20261031_v1'),str(B/'runtime/source_train17_clock/source/tools')]
from violation_pipeline import classes
from census_native import census_class
from validate_published_finite_check_20261025 import digest
p=json.loads((O/'PLAN.json').read_text());e=p['methods']['impedance'];ck=torch.load(e['checkpoint'],map_location='cpu',weights_only=False,mmap=True);reg=json.loads(Path(e['registration']).read_text());base,_=classes(reg)
kwargs=dict(dimension=reg['violation_critic_amendment']['binding']['action_dimension'],direct=False,seed=ck['seed'],device='cuda:0',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
torch.set_num_threads(1);os.sched_setaffinity(0,{10});out={}
for label,cls in [('original_loader',base),('census_owned_copy',census_class(base))]:
 state=copy.deepcopy(ck['learner']);original=digest(state);l=cls(B/'runtime/source_train17_clock',**kwargs)
 if label=='original_loader':l.load_state_dict(state)
 else:l.migrate_parent(state)
 aliases={}
 for attr,key in [('q_optimizer','q_optimizer'),('actor_optimizer','actor_optimizer'),('a_optimizer','alpha_optimizer')]:
  opt=getattr(l.learner,attr);saved=state[key];ids=[i for g in saved['param_groups'] for i in g['params']];params=[v for g in opt.param_groups for v in g['params']];shared=[opt.state[v]['step'].data_ptr()==saved['state'][i]['step'].data_ptr() for i,v in zip(ids,params)];aliases[key]=dict(shared=sum(shared),total=len(shared))
 out[label]=aliases;assert digest(state)==original
 del l
assert all(x['shared']==x['total'] for x in out['original_loader'].values()) and all(x['shared']==0 for x in out['census_owned_copy'].values())
result=dict(passed=True,time=time.time(),cpu_Adam_step_storage=out,no_optimizer_or_physics=True,source_input_unchanged=True,interpretation='Original loader aliases input CPU step counters; independent owned state copy prevents disposable updates from mutating reset reference. V1 metric/RNG equality was insufficient.')
(O/'ADAM_ALIAS_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
