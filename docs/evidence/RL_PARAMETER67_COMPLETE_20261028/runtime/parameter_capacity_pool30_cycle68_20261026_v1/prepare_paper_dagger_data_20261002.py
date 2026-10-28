"""Append declared student development histories with counterfactual VMC labels.

Never relabel success status, reuse held-out physical conditions, or treat expert
actions on a student's observations as an expert's executed trajectory.
"""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
from train_tool_vmc_memory_20261002 import filtered_labels
from optimize_tool_contact_20261002 import ROOT,sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--traces',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--weight',type=float,default=16.)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    metadata=json.loads(a.metadata.read_text())
    assert sha(a.data)==metadata['training_data_sha256']
    assert np.isfinite(a.weight) and a.weight>0
    keys=('observation','episode','train','requested_teacher_action','filtered_teacher_action','importance')
    with np.load(a.data) as z:arrays={k:[z[k].copy()] for k in keys}
    next_ep=int(arrays['episode'][0].max())+1
    lineage=list(metadata['lineage'])
    seen={x['sha256'] for x in lineage}
    sources=[Path(__file__),ROOT/'tools/train_tool_vmc_memory_20261002.py',ROOT/'tools/optimize_tool_contact_20261002.py']+sorted((ROOT/'scripts').glob('*.py'))
    hashes={str(f.relative_to(ROOT)):sha(f) for f in sources}
    subprocess.run(['tar','-czf',str(out/'source_overlay.tar.gz'),*hashes],cwd=ROOT,check=True)
    for index,path in enumerate(a.traces):
        execution=path.parent/'execution.json'
        if execution.exists():
            provenance=json.loads(execution.read_text()).get('runtime_provenance',{})
            if provenance.get('condition_id','development_anchor')!='development_anchor' or provenance.get('physics_tier')=='formal_resolution':
                raise ValueError('Heldout/formal history prohibited as training labels: '+str(path))
        digest=sha(path)
        if digest in seen:raise ValueError('History already present: '+str(path))
        seen.add(digest)
        with np.load(path) as trace:obs=trace['observation'].copy()
        summary=json.loads(path.with_suffix('.json').read_text())
        raw,filtered=filtered_labels(obs,metadata['config'])
        new=dict(observation=obs,episode=np.full(len(obs),next_ep+index),train=np.ones(len(obs),bool),
                 requested_teacher_action=raw,filtered_teacher_action=filtered,importance=np.full(len(obs),a.weight))
        for key in keys:arrays[key].append(new[key])
        lineage.append(dict(path=str(path.resolve()),sha256=digest,actual_execution_labels=False,
            counterfactual_relabel=True,task_success=summary['task_success'],strict_success=summary['strict_success'],
            development_only=True,episode_id=next_ep+index))
    joined={key:np.concatenate(value) for key,value in arrays.items()}
    np.savez_compressed(out/'training_data.npz',**joined)
    for key in keys:
        np.testing.assert_array_equal(joined[key][~joined['train']],arrays[key][0][~arrays['train'][0]])
    result=dict(completed_utc=now(),config=metadata['config'],config_sha256=metadata['config_sha256'],
        training_data_sha256=sha(out/'training_data.npz'),lineage=lineage,
        position_error_context=bool(metadata.get('position_error_context',False)),
        parent_data_sha256=sha(a.data),parent_metadata_sha256=sha(a.metadata),source_sha256=hashes,
        weight=a.weight,added_development_episodes=len(a.traces),heldout_histories_unchanged=True,
        limitation='Counterfactual expert labels on failed or successful student histories; statuses preserved, no new expert physical execution, no final validation identities included.')
    assert all(sha(ROOT/k)==h for k,h in hashes.items())
    write(out/'DATA_COMPLETE.json',result)
    print(json.dumps({k:result[k] for k in ('training_data_sha256','added_development_episodes','heldout_histories_unchanged')}))


if __name__=='__main__':main()
