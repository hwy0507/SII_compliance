"""Eight predeclared pure-network readout calibrations, no runtime adapter.

This is seen-environment policy calibration, not teacher-only distillation or
a held-out benchmark. All candidates must remain in the physical result table.
"""
import argparse
from pathlib import Path
import shutil
import numpy as np
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN

GRID=[('z110',1.,1.1,0.),('rot015',1.,1.,.15),('rot040',1.,1.,.4),
      ('xy025',.25,1.,0.),('xy025_z110_rot015',.25,1.1,.15),
      ('z090_rot015',1.,.9,.15),('z110_rot040',1.,1.1,.4),('xy025_z090_rot040',.25,.9,.4)]

def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    with np.load(args.parent,allow_pickle=False) as z:original={k:z[k].copy() for k in z.files}
    np.testing.assert_array_equal(original['scale'][3:],np.ones(3))
    if np.any(original['weights'][:,4:]!=0) or np.any(original['output_w'][4:]!=0):
        raise ValueError('Registered screen requires a zero-angular-readout parent')
    source=out/'source';source.mkdir();shutil.copy2(__file__,source/Path(__file__).name)
    shutil.copy2(ROOT/'scripts/office_vmc_memory_esn_20260927.py',source/'office_vmc_memory_esn_20260927.py')
    batch=dict(protocol='fixed_tool_contact_four_hour_20261002',registered_before_rollouts=True,
               purpose='Pure ESN neural readout calibration; not a new teacher or unchanged imitation-only checkpoint',
               contact_audit=True,parent_checkpoint_sha256=sha(args.parent),candidates={},checkpoint_by_candidate={})
    for name,xy,z_gain,rotation in GRID:
        row=out/name;row.mkdir();model={k:v.copy() for k,v in original.items()}
        model['weights'][:,1:3]*=xy;model['output_w'][1:3]*=xy
        model['weights'][:,3]*=z_gain;model['output_w'][3]*=z_gain
        for axis in range(3):model['weights'][3+axis,4+axis]+=rotation
        checkpoint=row/'checkpoint.npz';np.savez_compressed(checkpoint,**model)
        actor=OfficeVMCMemoryESN(checkpoint)
        rng=np.random.default_rng(2026100227)
        for _ in range(50):
            obs=rng.normal(0,2,48);obs[39:45]=0;actor.reset()
            np.testing.assert_array_equal(actor.act(obs),np.zeros(7))
        for key in ('win','w','leak'):
            np.testing.assert_array_equal(model[key],original[key])
        write(row/'CALIBRATION.json',dict(created_utc=now(),parent=str(args.parent.resolve()),
              parent_sha256=sha(args.parent),checkpoint_sha256=sha(checkpoint),xy_gain=xy,z_gain=z_gain,
              estimated_moment_skip_readout_gain=rotation,reservoir_and_input_contract_unchanged=True,
              exact_zero_equilibrium=True,source_sha256={f.name:sha(f) for f in source.iterdir()},
              limitation='Weights calibrated on the seen development scene; no additional controller, teacher call, phase or environmental input at inference'))
        batch['candidates'][name]={};batch['checkpoint_by_candidate'][name]=str(checkpoint)
    write(out/'batch.json',batch)
    print(str(out/'batch.json'))

if __name__=='__main__':main()
