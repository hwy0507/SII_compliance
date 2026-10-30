"""Verify split affine outputs/gradients against dense float64 reference."""
from pathlib import Path
import os,sys,json,hashlib,time
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='1';os.sched_setaffinity(0,{13})
D=Path(__file__).resolve().parent;B=D.parents[1];sys.path[:0]=[str(D),str(B/'runtime/history88_frozen_preparation_20261030_v1')]
import torch
from persisted_violation_critic import PreservedHistoryLinear
from torch import nn
torch.set_num_threads(1);torch.manual_seed(2026103090);results=[]
for dim in (5,7):
 for n in (1,17,256):
  model=PreservedHistoryLinear(52+dim,128,dtype=torch.float64);dense=nn.Linear(52+dim,128,dtype=torch.float64);dense.load_state_dict(model.state_dict());x=torch.randn(n,52+dim,dtype=torch.float64,requires_grad=True);x2=x.detach().clone().requires_grad_();y=model(x);y2=dense(x2);err=float((y-y2).abs().max());assert err<1e-12
  y.square().sum().backward();y2.square().sum().backward();errors=dict(input=float((x.grad-x2.grad).abs().max()),weight=float((model.weight.grad-dense.weight.grad).abs().max()),bias=float((model.bias.grad-dense.bias.grad).abs().max()));assert max(errors.values())<1e-10
  results.append(dict(action_dimension=dim,batch=n,max_abs_output=err,max_abs_gradient=errors))
out=dict(passed=True,time=time.time(),cases=results,split_source_sha256=hashlib.sha256((D/'persisted_violation_critic.py').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),random_fixture_only=True,formal_updates=0,physics=0)
with (D/'AFFINE_REVIEW.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
