"""Write the source-domain coverage protocol; it does not collect labels."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np


def build(seed=2026091761):
    rng=np.random.default_rng(seed); rows=[]
    ranges={
        'ball':dict(n=24, duration=18., mass=(.10,.35), speed=(1.,2.2), angle=(-.20,.20), offset=(-.025,.025)),
        'push':dict(n=24, duration=28., hold=(1.5,7.), stroke=(.07,.20), force=(6.,18.), angle=(-.35,.35)),
        'corner':dict(n=24, duration=40., yaw=(-.30,.30), width=(.040,.075), friction=(.18,.65), height=(.63,.73)),
        'free':dict(n=12, duration=28., yaw=(-.25,.25), shift=(-.04,.04)),
    }
    for split, mult in (('train',1),('validation',3)):
        for scene,spec in ranges.items():
            n=spec['n']//mult
            for i in range(n):
                f=dict(scene=scene,seed=int(rng.integers(10000,9999999)),duration=spec['duration'],nominal_speed=float(rng.uniform(.035,.085)))
                f['robot_state_family']=('approach','pregrasp','loaded_lift','carry','recovery')[i%5]
                for key,bounds in spec.items():
                    if key=='n' or key=='duration':continue
                    lo,hi=bounds
                    f[key]=float(rng.uniform(lo,hi))
                ident=f'{scene}_{split}_{i:03d}'
                physical={k:v for k,v in f.items() if k!='seed'}
                rows.append(dict(id=ident,scene=scene,split=split,flags=f,fixture_hash=hashlib.sha256(json.dumps(physical,sort_keys=True).encode()).hexdigest()))
    assert len({r['fixture_hash'] for r in rows})==len(rows)
    return dict(contract='primitive_v5',rows=rows,office_geometry_used=False,office_data_used=False,
      split='fixture_hash disjoint',train_counts={s:ranges[s]['n'] for s in ranges},
      validation_counts={s:ranges[s]['n']//3 for s in ranges},
      status='design_only_not_executable_collection_flags',
      collection_adapter_implemented=False,actual_teacher_traces_collected=0,
      covariates=['ball impact mass/speed/angle/offset','push hold/stroke/force/angle','corner yaw/width/friction/height','nominal speed'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--seed',type=int,default=2026091761);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(build(a.seed),indent=2));print(a.output)
