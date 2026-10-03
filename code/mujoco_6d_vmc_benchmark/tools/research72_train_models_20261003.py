"""Sequential same-data width-128 fitting, with a frozen pre-fit job specification.

No simulator and no final/development outcomes are used for offline selection.
Both ordinary and feature-matched MLP/RNN controls receive both loss variants.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(p.read_text())
def write(p,value):
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(p)


def jobs(seeds):
    result=[]
    for seed in seeds:
        for variant in ('point','temporal'):
            result.append(dict(name=f'esn_{seed}_{variant}',family='esn',seed=seed,variant=variant,
                script='train_paper_context_esn_20261003.py',extra=[] if variant=='point' else ['--delta-weight','.25','--integral-weight','.1']))
        result.append(dict(name=f'memoryless_{seed}',family='memoryless',seed=seed,variant='point',
            script='train_paper_context_esn_20261003.py',extra=['--memory-reset']))
        for family in ('mlp','rnn'):
            for variant in ('point','temporal'):
                parent=f'memoryless_{seed}' if family=='mlp' else f'esn_{seed}_{variant}'
                result.append(dict(name=f'matched_{family}_{seed}_{variant}',family='matched_'+family,seed=seed,variant=variant,
                    parent=parent,script='train_paper_feature_matched_network_20261003.py',
                    extra=['--kind',family,'--updates','4000','--learning-rate','.0001','--integral-weight','0' if variant=='point' else '.1']))
                result.append(dict(name=f'ordinary_{family}_{seed}_{variant}',family='ordinary_'+family,seed=seed,variant=variant,
                    script='train_office_mlp_rnn_20261002.py',extra=['--kind',family,'--updates','4000',
                        '--learning-rate','.001','--target','requested','--absolute-inputs','--precision','float64',
                        '--drift-weight','0' if variant=='point' else '.1']))
    assert len(result)==33 and len({j['name'] for j in result})==33
    return result


def neural_refinement_jobs(seeds):
    result=[]
    for seed in seeds:
        for family in ('mlp','rnn'):
            for variant in ('point','temporal'):
                parent=f'memoryless_{seed}' if family=='mlp' else f'esn_{seed}_{variant}'
                for lr in ('.000001','.00001'):
                    result.append(dict(name=f'matched_{family}_{seed}_{variant}_lr{lr[1:]}',
                        family='matched_'+family,seed=seed,variant=variant,learning_rate=float(lr),parent=parent,
                        script='train_paper_feature_matched_network_20261003.py',
                        extra=['--kind',family,'--updates','4000','--learning-rate',lr,
                            '--integral-weight','0' if variant=='point' else '.1']))
                for lr in ('.0001','.0003'):
                    result.append(dict(name=f'ordinary_{family}_{seed}_{variant}_lr{lr[1:]}',
                        family='ordinary_'+family,seed=seed,variant=variant,learning_rate=float(lr),
                        script='train_office_mlp_rnn_20261002.py',extra=['--kind',family,'--updates','4000',
                            '--learning-rate',lr,'--target','requested','--absolute-inputs','--precision','float64',
                            '--drift-weight','0' if variant=='point' else '.1']))
    assert len(result)==48 and len({j['name'] for j in result})==48
    return result


def contextual_gate_jobs(seeds,selection):
    rates={(d['family'],d['variant']):d['selected_learning_rate'] for d in selection['decisions']}
    result=[]
    for seed in seeds:
        for variant in ('point','temporal'):
            result.append(dict(name=f'gated_esn_{seed}_{variant}',family='esn',seed=seed,variant='gated_'+variant,
                script='train_paper_context_esn_20261003.py',extra=['--leak-gate']+([] if variant=='point' else ['--delta-weight','.25','--integral-weight','.1'])))
        result.append(dict(name=f'gated_memoryless_{seed}',family='memoryless',seed=seed,variant='gated_point',
            script='train_paper_context_esn_20261003.py',extra=['--leak-gate','--memory-reset']))
        for family in ('mlp','rnn'):
            for variant in ('point','temporal'):
                parent=f'gated_memoryless_{seed}' if family=='mlp' else f'gated_esn_{seed}_{variant}'
                result.append(dict(name=f'gated_matched_{family}_{seed}_{variant}',family='matched_'+family,
                    seed=seed,variant='gated_'+variant,parent=parent,script='train_paper_feature_matched_network_20261003.py',
                    extra=['--kind',family,'--updates','4000','--learning-rate',str(rates['matched_'+family,variant]),
                           '--integral-weight','0' if variant=='point' else '.1']))
    assert len(result)==21
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--register-only',action='store_true')
    p.add_argument('--neural-lr-refinement',action='store_true')
    p.add_argument('--parent-learning',type=Path)
    p.add_argument('--contextual-gate-extension',action='store_true')
    p.add_argument('--amendment',type=Path)
    p.add_argument('--learning-rate-selection',type=Path)
    a=p.parse_args();out=a.output.resolve();protocol=read(a.protocol);meta=read(a.metadata)
    assert meta['all_real_execution'] and meta['protocol_sha256']==sha(a.protocol)
    assert meta['training_data_sha256']==sha(a.data)
    assert all(x['data_role'] in ('train','imitation_validation') and x['actual_execution_labels'] for x in meta['lineage'])
    out.mkdir(parents=True,exist_ok=True)
    parent_root=a.parent_learning.resolve() if a.parent_learning else out
    assert not (a.neural_lr_refinement and a.contextual_gate_extension)
    if a.contextual_gate_extension:
        assert a.amendment and a.learning_rate_selection and not a.parent_learning
        amendment=read(a.amendment);selection=read(a.learning_rate_selection)
        assert amendment['protocol_sha256']==selection['protocol_sha256']==sha(a.protocol)
        assert amendment['learning_rate_selection_sha256']==sha(a.learning_rate_selection)
        assert amendment['new_learning_cap_per_family_seed']==48 and amendment['sealed_contents_read'] is False
        assert amendment['scope']=='fixed_proprioceptive_contextual_leak_extension'
    if a.neural_lr_refinement:
        assert a.parent_learning is not None
        assert read(parent_root/'execution.json')['status']=='complete'
        original=read(parent_root/'SPECIFICATION.json')
        assert original['protocol_sha256']==sha(a.protocol) and original['data_sha256']==sha(a.data)
        assert protocol['budget_caps']['learning_candidates_per_family_seed']>=12
    spec=dict(protocol_sha256=sha(a.protocol),data_sha256=sha(a.data),metadata_sha256=sha(a.metadata),
        jobs=(contextual_gate_jobs(protocol['budget_caps']['training_seeds'],selection) if a.contextual_gate_extension else
              (neural_refinement_jobs if a.neural_lr_refinement else jobs)(protocol['budget_caps']['training_seeds'])),width=128,
        shared_data_roles=['train','imitation_validation'],closed_loop_development_used=False,
        selection='Each model uses whole-identity validation MSE (ordinary temporal nets also their registered integrated proxy). Later common development budget is separate.',
        fair_budget_caveats=['Same width is not same parameters/FLOPs.',
            'ESN fits 12 ridge/input/spectral candidates per loss/seed; memoryless fits 12 additional ablation candidates.',
            'Matched networks inherit a frozen same-data parent then get 4000 gradient updates; disclose parent fit cost.',
            'Ordinary nets train from scratch; both neural baseline families get the temporal-loss choice.',
            'ESN point uses no delta term; historical networks retain their fixed .25 delta term. Temporal ablation adds .1 integration.'])
    if a.neural_lr_refinement:
        spec.update(stage='neural_learning_rate_refinement',parent_learning=str(parent_root),
            parent_specification_sha256=sha(parent_root/'SPECIFICATION.json'),
            rationale='Original feature-matched fits all selected update zero, and validation worsened after updates. Check smaller fixed learning rates using the same identity holdout, no closed-loop or final feedback.',
            accounting='4 additional candidates per subfamily/seed, plus original2 =6. Pooling ordinary+matched within MLP/RNN gives12 per family/seed, within cap24. 4000 updates per added fit; parent cost remains visible.',
            next_selection='For each subfamily/loss select one shared learning rate by mean validation action MSE across all three seeds, including original rate; retain all three seeds. Closed-loop success is separate.')
    if a.contextual_gate_extension:
        spec.update(stage='contextual_gate_extension',amendment_sha256=sha(a.amendment),
            learning_rate_selection_sha256=sha(a.learning_rate_selection),
            mechanism='Existing fixed random sigmoid gate modulates reservoir leak using the same twelve proprioceptive context values. Only ESN readout learns; matched networks get the identical fixed gate.',
            accounting='Additional24 ridge candidates per ESN seed,12 memoryless,2 gradient fits per matched neural family. ESN cumulative48; memoryless24; ordinary+matched MLP/RNN pooled14 each. Parent fit cost separate.',
            next_selection='All21 models on the same8 development conditions; compare variants across all3 seeds by the existing strict/task/horizon/penetration/RMSE/torque rule. No new data or synthetic-probe labels.')
    if (out/'SPECIFICATION.json').exists():assert read(out/'SPECIFICATION.json')==spec
    else:write(out/'SPECIFICATION.json',spec)
    if a.register_only:print(json.dumps(dict(jobs=len(spec['jobs']),specification_sha256=sha(out/'SPECIFICATION.json'))));return
    import fcntl
    with (out/'fitting.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
        memory=(cg/'memory.max').read_text().strip();assert memory!='max' and int(memory)<=3*1024**3
        assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        source=out/'source'
        if not source.exists():
            for folder in ('scripts','tools','assets'):
                shutil.copytree(ROOT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
            write(out/'SOURCE_HASHES.json',{str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()})
        assert all(sha(source/k)==h for k,h in read(out/'SOURCE_HASHES.json').items())
        state=read(out/'execution.json') if (out/'execution.json').exists() else dict(status='running',started_utc=now(),rows=[])
        state['specification_sha256']=sha(out/'SPECIFICATION.json');write(out/'execution.json',state)
        deadline=min(datetime.fromisoformat(protocol['dispatch_deadline_utc']),datetime.fromisoformat(protocol['authorization_start_utc'])+__import__('datetime').timedelta(hours=48))
        try:
            for job in spec['jobs']:
                dest=out/job['name'];previous=next((r for r in state['rows'] if r['name']==job['name']),None)
                if previous:
                    assert previous.get('returncode')==0 and sha(dest/'checkpoint.npz')==previous['checkpoint_sha256']
                    continue
                if datetime.now(timezone.utc)>=deadline:state['status']='deadline_no_new_dispatch';break
                assert not dest.exists(), 'Unregistered interrupted fit preserved'
                command=[sys.executable,str(source/'tools'/job['script']),'--data',str(a.data.resolve()),'--metadata',str(a.metadata.resolve()),
                    '--output',str(dest),'--seed',str(job['seed']),*job['extra']]
                if job.get('parent'):
                    parent=parent_root/job['parent'];command+=['--checkpoint',str(parent/'checkpoint.npz'),'--parent-metadata',str(parent/'TRAINING_COMPLETE.json')]
                row=dict(name=job['name'],family=job['family'],command=command,started_utc=now());state['rows'].append(row);write(out/'execution.json',state)
                with (out/(job['name']+'.log')).open('x') as log:
                    rc=subprocess.run(command,cwd=source,stdout=log,stderr=subprocess.STDOUT).returncode
                row.update(returncode=rc,ended_utc=now());write(out/'execution.json',state)
                if rc:raise RuntimeError(job['name']+' failed; keep original output')
                record=read(dest/'TRAINING_COMPLETE.json')
                assert record.get('training_data_sha256',record.get('data_sha256'))==sha(a.data)
                row.update(checkpoint_sha256=sha(dest/'checkpoint.npz'),training_metadata_sha256=sha(dest/'TRAINING_COMPLETE.json'))
                write(out/'execution.json',state)
            else:state['status']='complete'
        except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
        finally:state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
