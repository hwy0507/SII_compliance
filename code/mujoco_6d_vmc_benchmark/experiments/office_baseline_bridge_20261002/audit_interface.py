"""Read-only comparison of saved office interface checks, including NaN sentinels."""
import argparse,json
from pathlib import Path
import numpy as np
EXPECTED='b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1'
def audit(root):
    a=np.load(root/'nominal/rollout.npz');b=np.load(root/'zero_bridge/rollout.npz')
    fields={}
    for key in a.files:
        x,y=a[key],b[key]
        if not np.issubdtype(x.dtype,np.number):continue
        exact=np.array_equal(x,y,equal_nan=True)
        mask=np.isfinite(x)&np.isfinite(y)
        same_finiteness=np.array_equal(np.isfinite(x),np.isfinite(y))
        diff=float(np.max(np.abs(x[mask].astype(float)-y[mask].astype(float)))) if mask.any() else None
        fields[key]=dict(exact_including_nan_positions=bool(exact),finite_pattern_matches=bool(same_finiteness),finite_max_abs=diff,nan_count=int(np.isnan(x).sum()))
        if not exact:raise RuntimeError('Zero callback differs: '+key)
    cases=[]
    for p in sorted(root.glob('*/EXECUTION.json')):
        ex=json.loads(p.read_text());r=json.loads((p.parent/'rollout.json').read_text());z=np.load(p.parent/'rollout.npz')
        assert ex['status']=='complete' and r['model_sha256']==EXPECTED
        for k in ['qpos','qvel','ctrl','observation','applied_action']:assert np.isfinite(z[k]).all()
        assert len(z['time'])==2 and abs(z['time'][-1]-.08)<1e-10
        case=dict(name=p.parent.name,model_sha256=r['model_sha256'],finite_physics_and_observation=True,steps=2)
        if 'baseline_policy' in r:case['baseline']=r['baseline_policy']
        cases.append(case)
    out=dict(exact_zero_callback=True,field_comparison=fields,cases=cases,scope='80 ms interface checks only; no contact or full-horizon task claim',prior_audit='ZERO_EQUIVALENCE.json contained a NaN diagnostic difference for an intentionally unavailable task_carry_load field; this audit explicitly compares NaN positions and finite values.')
    (root/'INTERFACE_AUDIT.json').write_text(json.dumps(out,indent=2,allow_nan=False))
    print(json.dumps(dict(exact=True,cases=len(cases),finite=True)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();audit(a.directory)
