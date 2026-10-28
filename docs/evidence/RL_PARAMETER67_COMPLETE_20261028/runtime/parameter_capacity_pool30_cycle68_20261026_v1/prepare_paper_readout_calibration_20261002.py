"""Predeclare identical bounded readout calibration for pure ESN/MLP/RNN.

Changes learned readout coefficients only; no runtime teacher, observation,
world, common action filter, task gate or actuator changes.
"""
import argparse
from pathlib import Path
import json
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--expected-sha256',required=True)
    p.add_argument('--method',choices=('esn','mlp','rnn'),required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--gain-values',type=float,nargs='+',default=[.8,1.2])
    p.add_argument('--groups',choices=('all','translation','rotation'),nargs='+',default=['all','translation','rotation'])
    p.add_argument('--name-prefix',default='')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    assert all(np.isfinite(g) and .5<=g<=1.5 for g in a.gain_values)
    assert not a.name_prefix or (Path(a.name_prefix).name==a.name_prefix and a.name_prefix not in ('.','..'))
    assert sha(a.checkpoint)==a.expected_sha256
    with np.load(a.checkpoint,allow_pickle=False) as z:base={k:z[k].copy() for k in z.files}
    assert bool(base.get('axis_separable',base.get('norm_slowdown',False)))
    rows=[]
    for group in a.groups:
        for gain in a.gain_values:
            factor=np.ones(7)
            if group=='all':factor[1:]=gain
            elif group=='translation':factor[1:4]=gain
            else:factor[4:]=gain
            values={k:v.copy() for k,v in base.items()}
            if a.method=='esn':
                values['weights']*=factor[None,:]
                if 'output_w' in values:values['output_w']*=factor[:,None]
            else:values['output_w']*=factor[:,None]
            name=f'{a.name_prefix}{a.method}_{group}_{gain}'
            checkpoint=out/(name+'.npz');np.savez_compressed(checkpoint,**values)
            rows.append(dict(name=name,category=a.method+'_development',checkpoint=str(checkpoint),
                             checkpoint_sha256=sha(checkpoint),calibration=dict(group=group,gain=gain,factors=factor.tolist())))
    write(out/'manifest.json',dict(created_utc=now(),source_sha256=sha(Path(__file__)),parent_checkpoint=str(a.checkpoint.resolve()),
        parent_checkpoint_sha256=a.expected_sha256,candidates=rows,
        selection='task/strict first; safety margin, completion time and fixed full-horizon diagnostics; no scalar superiority claim',
        groups=a.groups,gain_values=a.gain_values,
        limitation='Registered identical candidate gains for every learned architecture; each physical evaluation counts toward development budget. Readout calibration can overfit one development scene; separate final validation required.'))


if __name__=='__main__':main()
