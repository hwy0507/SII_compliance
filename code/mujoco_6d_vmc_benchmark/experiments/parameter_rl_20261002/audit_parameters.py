"""Audit applied parameters in completed episodes without changing a policy."""
import argparse,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def audit(root,controller,output):
    prior=json.loads((HERE/"PRIORS.json").read_text())["methods"][controller]
    center=np.asarray(prior["center"]);bounds=np.asarray(prior["bounds"]);rows=[]
    for p in sorted(root.rglob("parameter_actions.npz")):
        if not (p.parent/"result.json").exists() and not (p.parent/"rollout.json").exists():continue
        z=np.load(p);theta=z["parameters"];action=z["raw_action"];tank=z["tank"];scale=z["energy_scale"]
        if not len(theta):continue
        assert theta.shape==action.shape and theta.shape[1]==len(center)
        assert all(np.isfinite(x).all() for x in [theta,action,tank,scale])
        assert np.all(theta>=bounds[:,0]-1e-10) and np.all(theta<=bounds[:,1]+1e-10)
        assert np.max(abs(action))<=1.000001
        log_steps=np.diff(np.log(np.vstack([center,theta])),axis=0)
        maximum=float(abs(log_steps).max())
        assert maximum<=prior["max_log_rate_per_s"]*.04+1e-9
        assert tank.min()>=.08-1e-10 and tank.max()<=1.2+1e-10
        trace=json.loads((p.parent/"parameter_trace.json").read_text())
        assert len(trace)==len(theta)
        balance=max(abs(t["energy_after_j"]-(t["energy_before_j"]+t["recharge_j"]-t["debit_j"]+t["credit_j"])) for t in trace)
        assert balance<1e-9
        rows.append(dict(episode=str(p.parent),updates=len(theta),parameter_min=theta.min(axis=0).tolist(),parameter_max=theta.max(axis=0).tolist(),
            ratio_min=(theta/center).min(axis=0).tolist(),ratio_max=(theta/center).max(axis=0).tolist(),maximum_log_step=maximum,
            nonzero_parameter_updates=int(np.sum(np.max(abs(log_steps),axis=1)>1e-9)),minimum_tank_j=float(tank.min()),limited_updates=int(np.sum(scale<.999999)),maximum_budget_balance_error_j=balance))
    if not rows:raise ValueError("No completed parameter episodes")
    result=dict(controller=controller,prior=prior["center"],keys=prior["keys"],episodes=len(rows),updates=sum(r["updates"] for r in rows),nonzero_parameter_updates=sum(r["nonzero_parameter_updates"] for r in rows),
        limited_updates=sum(r["limited_updates"] for r in rows),minimum_tank_j=min(r["minimum_tank_j"] for r in rows),rows=rows,
        scope="Applied bounded/rate-limited parameters and local bookkeeping only; no global passivity or efficacy claim. Completed episodes only.")
    output.parent.mkdir(exist_ok=True,parents=True);output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in result.items() if k not in ["rows","prior","keys"]}))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);p.add_argument("--controller",choices=["admittance","impedance","vmc"],required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();audit(a.root,a.controller,a.output)
