"""Adversarial parameter safety contracts, independent of MuJoCo rollouts."""
import json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,'/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/source_scene_20260918/scripts')
sys.path.insert(0,str(HERE))
from controllers import ParameterShield

def main():
 priors=json.loads((HERE/'PRIORS.json').read_text())['methods'];reports=[]
 for method,p in priors.items():
  sh=ParameterShield(method,p);rng=np.random.default_rng(1092);limited=0
  for i in range(600):
   old=sh.theta.copy();z=rng.normal(0,.2,6);v=rng.normal(0,.4,6);a=rng.choice([-1.,1.],p['action_dimension']);next_=sh.update(a,z,v);row=sh.records[-1]
   assert np.max(abs(np.log(next_/old)))<=1.6*.04+1e-10
   assert np.all(next_>=sh.bounds[:,0]-1e-10) and np.all(next_<=sh.bounds[:,1]+1e-10)
   assert abs(row['energy_after_j']-(row['energy_before_j']+row['recharge_j']-row['debit_j']+row['credit_j']))<1e-10
   assert row['debit_j']<=row['energy_before_j']+row['recharge_j']-.08+1e-10
   limited+=row['energy_scale']<.999
  empty=ParameterShield(method,p);empty.energy=.08;empty.update(np.ones(p['action_dimension']),np.ones(6)*.2,np.zeros(6));assert empty.records[-1]['debit_j']<1e-10
  zero=ParameterShield(method,p)
  for i in range(20):zero.update(np.zeros(p['action_dimension']),np.ones(6)*.2,np.ones(6)*.5)
  error=float(np.max(abs(zero.theta-zero.center)));assert error<1e-10
  for bad in [np.full(p['action_dimension'],np.nan),np.zeros(p['action_dimension']+1),np.full(p['action_dimension'],1.2)]:
   try:zero.update(bad,np.zeros(6),np.zeros(6))
   except ValueError:pass
   else:raise AssertionError('Invalid parameter action accepted')
  reports.append(dict(method=method,adversarial_updates=600,energy_limited_updates=limited,zero_action_parameter_error=error))
 root=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl');root.mkdir(exist_ok=True);(root/'SHIELD_AUDIT.json').write_text(json.dumps(reports,indent=2));print(json.dumps(reports))
if __name__=='__main__':main()
