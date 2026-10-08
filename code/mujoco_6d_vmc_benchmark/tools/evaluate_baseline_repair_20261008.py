"""Development evaluation and locked final16x24, with independent metric audits.

Final identities cannot be read until a complete model/source lock exists.
Development and final evidence live in separate directories. No learner runs
inside this tool, and failed/incomplete attempts are never silently replaced.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import fcntl
from pathlib import Path
import subprocess
import sys
from office_v7_uniform24_20261008 import read,write,sha,now,V6,FAMILIES
from run_baseline_repair_screen_20261008 import managed
from research72_checkpoint_20261003 import checkpoint_hashes


BASELINES={'classical_'+m for m in ('vmc','admittance','impedance')}|{
    'parameter_vmc','parameter_admittance','parameter_impedance','direct_metric','direct_office_task'}


def validate_candidate(c):
    family=c['family']
    assert family in FAMILIES
    if family.startswith('classical_'):
        assert c.get('controller')==family.removeprefix('classical_') and not c.get('adapted_rl')
    elif family in BASELINES:
        rl=c['adapted_rl']
        expected=family.removeprefix('parameter_') if family.startswith('parameter_') else None
        assert rl['controller']==expected and rl['parameter_source']==c['parameter_source']
    elif family not in ('enhanced_teacher','nominal_zero'):
        assert c.get('checkpoint'), 'Learned policy cannot silently become teacher/zero'
    if c.get('checkpoint'):
        assert sha(c['checkpoint'])==c['checkpoint_sha256']
    if c.get('adapted_rl'):
        a=c['adapted_rl'];assert sha(a['manifest'])==a['manifest_sha256']
        manifest=read(a['manifest'])
        assert str(Path(a['checkpoint']).resolve())==manifest['checkpoint']
        assert checkpoint_hashes(Path(a['checkpoint']))==manifest['hashes']
        assert sha(manifest['training_protocol'])==manifest['training_protocol_sha256']
    if c['family'] in BASELINES:
        assert c['selection_evidence'] and c['parameter_source']
        for path,digest in c['selection_evidence'].items():assert sha(path)==digest
        assert c['parameter_source_hashes']
        for rel,digest in c['parameter_source_hashes'].items():assert sha(Path(c['parameter_source'])/rel)==digest


def freeze(root,models,source):
    assert not (root/'FINAL_MODEL_LOCK.json').exists()
    protocol=read(root/'PROTOCOL.json');candidates=read(models)['candidates']
    assert len(candidates)==16 and {c['family'] for c in candidates}==set(FAMILIES)
    reference=read(root/'REFERENCE_MODELS.json')['candidates']
    assert sha(root/'REFERENCE_MODELS.json')==protocol['reference_models_sha256']
    for c in candidates:
        validate_candidate(c)
        if c['family'] not in BASELINES:
            assert c==next(x for x in reference if x['family']==c['family']), 'Reference model changed'
    sources={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file() and p.suffix in ('.py','.json')}
    write(root/'FINAL_MODEL_LOCK.json',dict(status='frozen',frozen_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),
        models=str(models.resolve()),models_sha256=sha(models),source=str(source.resolve()),source_hashes=sources,
        note='Written before final conditions are read; final outcomes cannot select a checkpoint'))


def one(root,source,out,phase,c,d):
    name=c['name']+'__'+d['id'] if phase=='development' else c['family']+'__'+d['id']
    assert '/' not in name
    run=out/'episodes'/name;receipt=out/'episodes'/(name+'.execution.json')
    if receipt.exists():
        old=read(receipt)
        assert old['status']=='complete', 'Incomplete attempt preserved: '+name
        assert sha(run/'AUDIT.json')==old['audit_sha256'] and sha(run/'rollout.npz')==old['trace_sha256']
        assert sha(old['metrics'])==old['metrics_sha256']
        return old
    protocol=read(root/'PROTOCOL.json')
    assert datetime.now(timezone.utc)<datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    config=out/'episodes'/(name+'.config.json');write(config,c.get('config',{}))
    kind='adapted_rl' if c.get('adapted_rl') else 'nominal' if c.get('nominal') else 'classical' if c.get('controller') else 'office'
    command=[sys.executable,str(source/'tools/baseline_repair_worker_20261008.py'),
        '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
        '--research-condition',d['id'],'--phase',phase,'--worker-kind',kind,'--v6-input',str(V6),
        '--reference',str(V6/'esn_original_v2/rollout.json'),'--config',str(config),'--output',str(run),
        '--contact-audit','--physics-dt','.00005']
    if c.get('adapted_rl'):
        rl=c['adapted_rl'];command+=['--agent-checkpoint',rl['checkpoint'],'--checkpoint-manifest',rl['manifest'],
            '--parameter-source',rl['parameter_source']]
        if rl.get('controller'):command+=['--controller',rl['controller']]
    elif c.get('controller'):command+=['--controller',c['controller'],'--parameter-source',c['parameter_source']]
    elif c.get('checkpoint'):command+=['--checkpoint',c['checkpoint']]
    row=dict(name=name,family=c['family'],candidate=c['name'],condition_id=d['id'],phase=phase,
        started_utc=now(),status='running',command=command)
    write(receipt,row)
    with (out/'episodes'/(name+'.log')).open('x') as f:
        rc=subprocess.run(managed(source,command,'sii-r15-eval-'+out.name+'-'+name.replace('_','-')),
            stdout=f,stderr=subprocess.STDOUT).returncode
    row.update(returncode=rc,ended_utc=now())
    if rc:
        row['status']='infrastructure_failure_preserved';write(receipt,row)
        raise RuntimeError(name+' physics failed; original attempt retained')
    audit=read(run/'AUDIT.json');actual=read(run/'execution.json')['arguments']
    assert audit['model_sha256']==protocol['formal_model_sha256']
    assert all(actual[k]==v for k,v in d['overrides'].items())
    metric=out/'analysis'/(name+'.json')
    cmd=[sys.executable,str(source/'tools/paper_metrics_20261002.py'),'--run',str(run),'--output',str(metric)]
    with (out/'analysis'/(name+'.log')).open('x') as f:
        rc=subprocess.run(managed(source,cmd,'sii-r15-metric-'+out.name+'-'+name.replace('_','-')),
            stdout=f,stderr=subprocess.STDOUT).returncode
    if rc:
        row['status']='independent_audit_failure_preserved';write(receipt,row)
        raise RuntimeError(name+' independent audit failed')
    m=read(metric)
    for k in ('rmse_mm','peak_torque_nm','peak_speed_mps'):
        assert abs(m[k]-audit[k])<1e-4
    for k in ('task_success','strict_success','full_horizon'):assert m[k]==audit[k]
    row.update(status='complete',audit=audit,audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'),
        metrics=str(metric),metrics_sha256=sha(metric));write(receipt,row)
    return row


def run(root,models,source,out,phase,workers,condition_ids):
    protocol=read(root/'PROTOCOL.json');candidates=read(models)['candidates']
    assert len({c['name'] for c in candidates})==len(candidates)
    if phase=='final':
        lock=read(root/'FINAL_MODEL_LOCK.json')
        assert lock['status']=='frozen' and lock['protocol_sha256']==sha(root/'PROTOCOL.json')
        assert lock['models_sha256']==sha(models) and lock['source']==str(source.resolve())
        for rel,digest in lock['source_hashes'].items():assert sha(source/rel)==digest
        assert condition_ids is None
        conditions_path=root/'sealed/HELDOUT.json'
        assert sha(conditions_path)==protocol['sealed_condition_sha256']
    else:
        conditions_path=root/'CONDITIONS.json'
        assert sha(conditions_path)==protocol['condition_file_sha256']
    conditions=[d for d in read(conditions_path)['conditions'] if d['role']==phase]
    if condition_ids:
        wanted=set(condition_ids.split(','));conditions=[d for d in conditions if d['id'] in wanted]
        assert {d['id'] for d in conditions}==wanted
    assert conditions
    for c in candidates:validate_candidate(c)
    out.mkdir(parents=True,exist_ok=True)
    guard=(out/'.lock').open('a');fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for folder in ('episodes','analysis'):(out/folder).mkdir(exist_ok=True)
    # Independent report tools consume these derived files; the physical
    # worker still verifies the original campaign protocol/role on every run.
    model_value=read(models);condition_value=dict(conditions=conditions)
    for name,value in [('MODEL_MANIFEST.json',model_value),('CONDITIONS.json',condition_value)]:
        if (out/name).exists():assert read(out/name)==value
        else:write(out/name,value)
    derived=dict(protocol,parent_protocol=str(root/'PROTOCOL.json'),parent_protocol_sha256=sha(root/'PROTOCOL.json'),
        model_manifest_sha256=sha(out/'MODEL_MANIFEST.json'),condition_file_sha256=sha(out/'CONDITIONS.json'),
        phase=phase,source=str(source))
    if (out/'PROTOCOL.json').exists():assert read(out/'PROTOCOL.json')==derived
    else:write(out/'PROTOCOL.json',derived)
    jobs=[(c,d) for d in conditions for c in candidates];failures=[]
    write(out/'execution.json',dict(status='running',started_utc=now(),expected=len(jobs),workers=workers))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(one,root,source,out,phase,c,d) for c,d in jobs]
        for f in as_completed(futures):
            try:f.result()
            except Exception as exc:failures.append(repr(exc))
    rows=[read(p) for p in (out/'episodes').glob('*.execution.json')]
    result=dict(status='complete' if not failures else 'incomplete_preserved',ended_utc=now(),expected=len(jobs),
        completed=sum(r['status']=='complete' for r in rows),failures=failures)
    write(out/'execution.json',result)
    if phase=='final':
        from report_office_v7_uniform24_20261008 import build,markdown
        report=build(out)
        report['interpretation']='Repaired baseline cohort: independent new24 final conditions, frozen model per family; prior weak-baseline matrix not reused. Equal evaluation does not mean equal historical training.'
        write(out/'REPORT.json',report);(out/'REPORT.md').write_text(markdown(report))
    if failures:raise RuntimeError(failures)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--models',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path)
    p.add_argument('--phase',choices=('development','final'),default='development')
    p.add_argument('--freeze',action='store_true');p.add_argument('--workers',type=int,default=1)
    p.add_argument('--conditions',help='Explicit development identities only')
    a=p.parse_args();assert 1<=a.workers<=10
    if a.freeze:freeze(a.root,a.models,a.source)
    else:
        assert a.output is not None
        run(a.root,a.models,a.source,a.output,a.phase,a.workers,a.conditions)


if __name__=='__main__':main()
