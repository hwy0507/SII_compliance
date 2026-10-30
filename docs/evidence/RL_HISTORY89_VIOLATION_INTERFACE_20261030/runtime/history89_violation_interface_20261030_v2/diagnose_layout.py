"""Read-only single-row CUDA comparison of old, dense-zero, and split-zero layers."""
from pathlib import Path
import os,sys,json,copy,hashlib,time,gc
D=Path(__file__).resolve().parent;B=D.parents[1];os.sched_setaffinity(0,{13});os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';plan=json.loads((D/'PLAN.json').read_text());sys.path[:0]=[str(D),plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools')]
import torch,numpy as np
from torch import nn
from history_consumers import restore_learner
from persisted_history_critic import history_class
from published_compliance_learner_20261025 import PublishedLearner,OBSERVATION_SCALE
from published_pair_reduction_learner_20261026 import pair_class
from persisted_violation_critic import violation_class
from validate_published_finite_check_20261025 import digest
binding=json.loads((D.parent/'history89_violation_interface_20261030_v1/impedance_BINDING.json').read_text());cp=B/'runs/parameter_history_cycle89_archive_20261030_v1/impedance/cycle_00089.pt';ck=torch.load(cp,map_location='cpu',weights_only=False);state=ck['learner'];raw=ck['replay']['arrays']['observations'][0,:48]*OBSERVATION_SCALE;steps=ck['steps'];del ck;gc.collect();torch.set_num_threads(1)
old=restore_learner(state,binding['history_binding'],B/'runtime/source_train17_clock','cuda:2');old.consume_interval(None);o,a,_,_=old.act(raw,step=steps)
HC=history_class(pair_class(PublishedLearner,'minimum'),binding['history_binding']);split=violation_class(HC,binding)(B/'runtime/source_train17_clock',dimension=5,direct=False,seed=20261025,device='cuda:2',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);split.migrate_parent(state);dense=copy.deepcopy(split.learner.agent.ensemble)
for q in dense:
 original=q.q_net[0];layer=nn.Linear(original.in_features,original.out_features,device=original.weight.device);layer.load_state_dict(original.state_dict());q.q_net[0]=layer
results=[]
with torch.no_grad():
 for n in (1,64):
  obs=torch.as_tensor(np.tile(o,(n,1)),device='cuda:2');obs52=torch.cat((obs,obs.new_zeros((n,1))),1);act=torch.as_tensor(np.tile(a,(n,1)),device='cuda:2');q0=torch.stack([q(obs,act) for q in old.learner.agent.ensemble]);qd=torch.stack([q(obs52,act) for q in dense]);qs=torch.stack([q(obs52,act) for q in split.learner.agent.ensemble]);assert torch.equal(q0,qs)
  results.append(dict(batch=n,dense_vs_old_max_abs=float((qd-q0).abs().max()),split_vs_old_max_abs=float((qs-q0).abs().max()),old_values=q0[:,0].reshape(-1).cpu().tolist(),dense_values=qd[:,0].reshape(-1).cpu().tolist(),split_values=qs[:,0].reshape(-1).cpu().tolist()))
report=dict(passed=True,time=time.time(),methods=['impedance'],results=results,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),checkpoint_sha256=binding['checkpoint_sha256'],scope='Actual saved89 first-row action/input at original context. Direct forward comparison confirms dense-zero CUDA rounding vs split-zero preservation at batch1/64. No physics or optimizer update; not a general error bound.',physics=0,optimizer_updates=0)
with (D/'LAYOUT_DIAGNOSIS.json').open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
