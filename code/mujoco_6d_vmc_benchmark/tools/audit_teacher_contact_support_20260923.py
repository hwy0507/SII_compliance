"""Train/validation contact-stage audit, streaming one short trace at a time.

Does not read test rows, create a simulator, relabel data, or choose models.
Loaded contact observation matching uses the previous recorded 25Hz force to
align pre-step observations with post-step force; it is not substep contact.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def resolve(path, root):
    path = Path(path)
    return path if path.is_absolute() else root/path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank',type=Path,required=True)
    p.add_argument('--esn',type=Path,required=True)
    p.add_argument('--campaign',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    manifest=json.loads((args.bank/'manifest.json').read_text())
    counts=defaultdict(lambda:defaultdict(Counter));support={};nearest_train=[];train_ids=[];episodes=[]
    for split in ('train','validation'):
        pooled=[];stage_count=Counter();sparse_contact_count=Counter();config_hashes=[];rotations=[];fixture_stages=defaultdict(Counter)
        for row in manifest[split]:
            result_path=resolve(row.get('result',row.get('source_result')),ROOT)
            result=json.loads(result_path.read_text());contact=result.get('contact',{})
            key=split+'/'+row['scene'];counts[key]['episodes']['total']+=1
            for field,value in [('requested_event_stage',result.get('requested_event_stage',result.get('arguments',{}).get('event_stage'))),
                                ('actual_first_stage',contact.get('first_stage')),
                                ('actual_first_stage_name',contact.get('first_stage_name')),
                                ('first_payload_held',contact.get('first_payload_held'))]:
                counts[key][field][str(value)]+=1
            if row['scene']!='push': continue
            config=json.loads(resolve(row['source_search_result'],ROOT).read_text())['config']
            config_hashes.append(hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest())
            rotations.append(config.get('axis_rotation_rpy',[0,0,0]))
            fixture_stages[row['physical_fixture']][str(contact.get('first_stage'))]+=1
            with np.load(resolve(row['trace'],args.bank),allow_pickle=False) as z:
                obs=z['observation'];times=z['command_time_s']
            with np.load(result_path.with_suffix('.npz'),allow_pickle=False) as z:
                source_time=z['time'];post_force=z['force'];source_obs=z['observation']
            if len(obs)!=len(post_force): raise ValueError('Trace length mismatch '+row['id'])
            # Conversion copies source post-step time despite naming this field
            # command_time_s. Observation/action are still pre-step quantities.
            if not np.allclose(times,source_time,atol=1e-7): raise ValueError('Time mismatch '+row['id'])
            times=times-.04
            if not np.allclose(obs[:,:39],source_obs[:,:39],atol=1e-7): raise ValueError('Observation mismatch '+row['id'])
            stages=np.zeros(len(obs),dtype=int)
            for event in result['events']:
                stages[times>=event['t']-1e-8]=event['stage']
            pre_contact=np.r_[False,np.linalg.norm(post_force[:-1],axis=1)>.05]
            for s in np.unique(stages):
                stage_count[str(s)]+=int(np.sum(stages==s))
                sparse_contact_count[str(s)]+=int(np.sum((stages==s)&pre_contact))
            mask=(stages==3)&pre_contact
            ix=np.flatnonzero(mask)[::5]
            if len(ix):
                pooled.append(obs[ix])
                if split=='train': nearest_train.append(obs[ix]);train_ids.extend([row['id']]*len(ix))
            episodes.append(dict(id=row['id'],split=split,loaded_contact_samples=int(mask.sum()),
                                 loaded_samples=int(np.sum(stages==3)),actual_first_stage=contact.get('first_stage')))
        pooled=np.concatenate(pooled) if pooled else np.empty((0,48))
        support[split]=dict(stage_samples=dict(stage_count),stage_sparse_contact_samples=dict(sparse_contact_count),
            unique_actual_config_json_hashes=len(set(config_hashes)),
            axis_rotation_rpy_min=np.min(rotations,axis=0).tolist(),axis_rotation_rpy_max=np.max(rotations,axis=0).tolist(),
            actual_first_stage_by_fixture={k:dict(v) for k,v in fixture_stages.items()},
            loaded_contact_episodes=sum(x['split']==split and x['loaded_contact_samples']>0 for x in episodes),
            sampled_loaded_contact_rows=len(pooled),
            loaded_contact_obs_quantiles=np.quantile(pooled,[0,.01,.5,.99,1],axis=0).tolist() if len(pooled) else None)
    with np.load(args.esn,allow_pickle=False) as z: mean=z['mean'];std=z['std']
    bank=(np.concatenate(nearest_train)-mean)/std
    queries={}
    for method in ('vmc','mlp','esn','esn_lowpass_025'):
        with np.load(args.campaign/method/'9301'/'rollout'/'rollout.npz',allow_pickle=False) as z:obs=z['observation'][-25:]
        dist=[];ids=[]
        for q in (obs-mean)/std:
            d=np.mean((bank-q)**2,axis=1)**.5;i=int(np.argmin(d));dist.append(float(d[i]));ids.append(train_ids[i])
        queries[method]=dict(tail_nearest_loaded_contact_48d_rms_mean=float(np.mean(dist)),
                            episode_ids=ids,tail_wrench_mean=obs[:,39:45].mean(0).tolist())
    out=dict(scope='All train/validation source-result metadata; push-only aligned sparse contact support; no test read',
             manifest_sha256=hashlib.sha256((args.bank/'manifest.json').read_bytes()).hexdigest(),
             metadata={k:{kk:dict(vv) for kk,vv in v.items()} for k,v in counts.items()},
             push_support=support,push_episodes=episodes,queries=queries,
             limitations=['Sparse contact uses previous 25Hz force >0.05N, not exact physical contact duration.',
                         'Loaded lift stage3 applies to push; other scene stage numbers are not pooled.',
                         'Nearest current observations do not match hidden teacher or reservoir history.',
                         'No first-contact loaded episodes does not imply no loaded contact samples.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(metadata=out['metadata'],support={k:{a:b for a,b in v.items() if a!='loaded_contact_obs_quantiles'} for k,v in support.items()})))


if __name__=='__main__':main()
