from pathlib import Path
import itertools,json,time,hashlib
import numpy as np
import torch
from conditional import weights
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_terminal_census_ablation_20261031_v1'
torch.set_num_threads(1);tm=np.array([[1,1,0,1,1]]*2+[[1,0,1,1,1]]*2+[[0,1,1,1,1]]*2+[[0,0,0,0,0]]);slots=[[0,1],[0,1],[2,3],[4,5],[4,5],[6]];fixed=np.array([[1,1,1,1,1],[1,1,1,1,1]]);bm=np.vstack([fixed,tm[[s[0] for s in slots]]]);d=np.r_[np.zeros(2),np.ones(len(slots))];w,den,pop,c=weights(tm,bm,d)
x=torch.tensor([-.2,.9,.3,-.7,.5,1.2,.4],dtype=torch.float64);target=torch.tensor([-25,25,-17,18,-20,22,0],dtype=torch.float64);theta=torch.tensor([.2,-.3,.4,.1,-.2],dtype=torch.float64,requires_grad=True);err=(x[:,None]*theta[None,:]-target[:,None])**2;non=(theta-1)**2+(theta+2)**2;census=(non/torch.tensor(den)+(err*torch.tensor(w)).sum(0)).sum();cg=torch.autograd.grad(census,theta,retain_graph=True)[0];losses=[];grads=[]
for chosen in itertools.product(*slots):
 e=err[list(chosen)];sampled=(non/torch.tensor(den)+(128*e*torch.tensor(tm[list(chosen)])/torch.tensor(den)).sum(0)).sum();losses.append(float(sampled.detach()));grads.append(torch.autograd.grad(sampled,theta,retain_graph=True)[0].numpy())
np.testing.assert_allclose(np.mean(losses),float(census.detach()),rtol=1e-12,atol=1e-10);np.testing.assert_allclose(np.mean(grads,axis=0),cg.numpy(),rtol=1e-12,atol=1e-10);assert np.var(losses)>0
rejected=[]
for name,mask,done in [('nonbinary_mask',bm+.5,d),('nonbinary_done',bm,d+.5),('absent_pattern',np.vstack([fixed,np.ones((6,5))]),d),('zero_denominator',np.zeros_like(bm),d)]:
 try:weights(tm,mask,done)
 except ValueError:rejected.append(name)
 else:raise AssertionError(name)
assert len(rejected)==4
r=dict(passed=True,time=time.time(),exhaustive_draws=len(losses),original_mean_loss=float(np.mean(losses)),conditional_loss=float(census.detach()),original_loss_variance=float(np.var(losses)),conditional_variance_given_patterns=0.,mean_original_gradient=np.mean(grads,axis=0).tolist(),conditional_gradient=cg.tolist(),loss_and_gradient_expectation_exact_float64=True,negative_controls=rejected,source_sha256=hashlib.sha256((D/'conditional.py').read_bytes()).hexdigest(),scope='Finite exhaustive witness for algebraic conditional expectation at fixed theta/replay and full mask/done pattern. Does not imply equal Adam trajectory, unchanged finite-sample loss, or unbiased squared-mean replacement. Mean of squared residuals used.')
with (O/'MATH_PREFLIGHT.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r))
