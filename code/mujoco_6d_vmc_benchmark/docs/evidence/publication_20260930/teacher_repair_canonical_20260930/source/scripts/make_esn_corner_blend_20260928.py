"""Create a frozen readout interpolation for the corner-placement ablation."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--adapted',type=Path,required=True)
    p.add_argument('--beta',type=float,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if not 0.0 <= a.beta <= 1.0 or a.output.exists(): raise ValueError('invalid blend/output')
    with np.load(a.base,allow_pickle=False) as b, np.load(a.adapted,allow_pickle=False) as d:
        if str(b['contract']) != 'proprio48_esn128_action7_v1': raise ValueError('base contract')
        if str(d['contract']) != 'proprio48_esn128_action7_v1': raise ValueError('adapted contract')
        out={k:b[k] for k in b.files}
        out['w2']=((1-a.beta)*b['w2']+a.beta*d['w2']).astype(np.float32)
        out['b2']=((1-a.beta)*b['b2']+a.beta*d['b2']).astype(np.float32)
        metadata={'method':'fixed_readout_interpolation_corner_ablation',
                  'base_checkpoint_sha256':sha(a.base),'adapted_checkpoint_sha256':sha(a.adapted),
                  'beta':a.beta,'frozen_components':['48D normalization','reservoir','first readout layer','action projection','safety filter','task gates'],
                  'scope':'development corner placement only; physical validation required'}
        out['metadata']=np.asarray(json.dumps(metadata))
        a.output.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(a.output,**out)
    print(json.dumps({'output':str(a.output),'checkpoint_sha256':sha(a.output),'metadata':metadata},indent=2))
if __name__=='__main__': main()
