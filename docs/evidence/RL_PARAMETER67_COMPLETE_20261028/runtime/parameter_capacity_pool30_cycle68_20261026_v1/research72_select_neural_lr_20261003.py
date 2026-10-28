"""Select shared neural learning rates from identity-validation MSE only.

All three seeds are retained. Original-rate winners reuse the already registered
development experiment; only new-rate groups need additional physical episodes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--original',type=Path,required=True)
    p.add_argument('--refinement',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();pdigest=sha(a.root/'PROTOCOL.json')
    seeds=read(a.root/'PROTOCOL.json')['budget_caps']['training_seeds']
    groups={};data_sha=None
    for cohort,directory in [('original',a.original.resolve()),('refinement',a.refinement.resolve())]:
        spec=read(directory/'SPECIFICATION.json');state=read(directory/'execution.json')
        assert spec['protocol_sha256']==pdigest and state['status']=='complete'
        assert state['specification_sha256']==sha(directory/'SPECIFICATION.json')
        if data_sha is None:data_sha=spec['data_sha256']
        assert data_sha==spec['data_sha256']
        assert {r['name'] for r in state['rows']}=={j['name'] for j in spec['jobs']}
        assert all(sha(directory/'source'/k)==h for k,h in read(directory/'SOURCE_HASHES.json').items())
        for job in spec['jobs']:
            if job['family'] in ('esn','memoryless'):continue
            row=next(r for r in state['rows'] if r['name']==job['name'])
            cp=directory/job['name']/'checkpoint.npz';metadata=cp.parent/'TRAINING_COMPLETE.json'
            assert row['returncode']==0 and sha(cp)==row['checkpoint_sha256']
            assert sha(metadata)==row['training_metadata_sha256']
            values=read(metadata)
            assert values.get('training_data_sha256',values.get('data_sha256'))==data_sha
            assert all(x['data_role'] in ('train','imitation_validation') for x in values['lineage'])
            mse=values.get('holdout_mse')
            if mse is None:mse=values['groups']['real_identity_validation']['action_mse']
            lr=float(job['extra'][job['extra'].index('--learning-rate')+1])
            candidate=dict(name=job['name'],category=job['family'],variant=job['variant'],seed=job['seed'],
                checkpoint=str(cp),checkpoint_sha256=sha(cp),config={})
            key=(job['family'],job['variant'])
            groups.setdefault(key,{}).setdefault(lr,[]).append(dict(candidate=candidate,validation_mse=mse,
                selected_update=values['selected_update'],cohort=cohort,metadata_sha256=sha(metadata)))
    assert len(groups)==8
    decisions=[];selected=[];additional=[]
    for (family,variant),rates in sorted(groups.items()):
        assert len(rates)==3
        scores=[]
        for lr,rows in rates.items():
            assert sorted(r['candidate']['seed'] for r in rows)==sorted(seeds)
            scores.append(dict(learning_rate=lr,mean_validation_mse=statistics.mean(r['validation_mse'] for r in rows),
                original=all(r['cohort']=='original' for r in rows),rows=rows))
        best=min(v['mean_validation_mse'] for v in scores)
        tied=[v for v in scores if v['mean_validation_mse']<=best+1e-12]
        winner=min(tied,key=lambda v:(not v['original'],v['learning_rate']))
        selected.extend(r['candidate'] for r in winner['rows'])
        if not winner['original']:additional.extend(r['candidate'] for r in winner['rows'])
        decisions.append(dict(family=family,variant=variant,selected_learning_rate=winner['learning_rate'],
            reuse_original_development=winner['original'],scores=scores))
    conditions=[c['id'] for c in read(a.root/'CONDITIONS.json')['conditions'] if c['role']=='development']
    assert len(conditions)==8 and len(selected)==24
    result=dict(registered_utc=datetime.now(timezone.utc).isoformat(),protocol_sha256=pdigest,
        source_sha256=sha(Path(__file__)),data_sha256=data_sha,decisions=decisions,
        selected_candidates=selected,candidates=additional,conditions=conditions,
        additional_episodes=len(additional)*len(conditions),
        selection='One learning rate per subfamily/loss by mean identity-validation action MSE across three seeds. Ties within1e-12 prefer original rate, then smaller rate. No closed-loop selection here.',
        reuse='Original winners reuse prior development rows. Every changed-rate group includes all three seeds.',
        caution='Training-regression correction within predeclared cap, not evidence of task success or final superiority.')
    with a.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(selected_models=24,additional_models=len(additional),episodes=result['additional_episodes'],
        sha256=sha(a.output))))


if __name__=='__main__':main()
