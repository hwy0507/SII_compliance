"""Compare train-only prefixes across fixed-budget runs without selecting models."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical48_rl_env_20260923 import save_json,sha


def prefix(path,count):
    chunks={key:[] for key in ('observation','action','phase_reward_metadata')}
    files=[];remaining=count
    for file in sorted((path/'train').glob('episode_*/actor_trace.npz')):
        with np.load(file,allow_pickle=False) as archive:
            n=min(remaining,len(archive['action']))
            for key in chunks:chunks[key].append(archive[key][:n].copy())
        remaining-=n;files.append(dict(file=str(file),sha256=sha(file),samples_used=n))
        if not remaining:break
    if remaining:raise ValueError(f'Need {remaining} additional archived transitions at {path}')
    return {key:np.concatenate(value) for key,value in chunks.items()},files


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--old',type=Path,required=True)
    parser.add_argument('--new',type=Path,required=True)
    parser.add_argument('--steps',type=int,default=640)
    parser.add_argument('--atol',type=float,default=1e-6)
    parser.add_argument('--rtol',type=float,default=1e-6)
    args=parser.parse_args()
    old,oldfiles=prefix(args.old,args.steps);new,newfiles=prefix(args.new,args.steps)
    comparisons={}
    for key in old:
        a,b=old[key],new[key]
        if a.shape!=b.shape:raise AssertionError(f'Unexpected shape mismatch {key}')
        diff=np.asarray(a,dtype=float)-np.asarray(b,dtype=float)
        comparisons[key]=dict(shape=list(a.shape),bit_equal=bool(np.array_equal(a,b)),
            within_tolerance=bool(np.allclose(a,b,atol=args.atol,rtol=args.rtol)),
            max_abs_error=float(np.max(np.abs(diff))),rms_error=float(np.sqrt(np.mean(diff**2))))
    manifests=[json.loads((p/'manifest.json').read_text()) for p in (args.old,args.new)]
    ignored={'timesteps','periodic_checkpoint_interval'}
    parameters=[{k:v for k,v in m['training'].items() if k not in ignored} for m in manifests]
    report=dict(steps=args.steps,scope='train observations/actions only; diagnostic, no model selection',
        atol=args.atol,rtol=args.rtol,comparisons=comparisons,
        all_within_tolerance=all(r['within_tolerance'] for r in comparisons.values()),
        same_training_parameters_except_budget_checkpoint_logging=parameters[0]==parameters[1],
        old_files=oldfiles,new_files=newfiles,
        bridge_hashes=[m['source_hashes']['scripts/canonical48_rl_env_20260923.py'] for m in manifests])
    save_json(args.new/'PREFIX_COMPARISON.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
