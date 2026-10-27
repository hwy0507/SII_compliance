"""Package a complete independently audited six-controller condition, read-only.

Does not transfer, delete source files, alter experiment state, or include the
active episode. Reuses the existing streaming archive verification helpers.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
from datetime import datetime, timezone

from archive_nonrl_new30_physics_20261026 import digest_stream, sha, require


def package(root,audit_path,output,auditor_source):
    require(not output.exists(),'Never overwrite an archive directory')
    root=root.resolve();audit=json.loads(audit_path.read_text())
    lock=json.loads((root/'MODEL_LOCK.json').read_text())
    registration=json.loads((root/'REGISTRATION.json').read_text())
    require(registration['schema']=='sii-nonrl-task-conditional-classical-v1','Wrong study')
    require(audit['status']=='completed_classical_condition_audit_passed_not_final','Complete condition audit required')
    require(Path(audit['root']).resolve()==root,'Wrong audited run')
    require(sha(root/'REGISTRATION.json')==audit['registration_sha256'],'Registration changed')
    require(sha(root/'MODEL_LOCK.json')==audit['model_lock_sha256']==registration['models_sha256'],'Model lock changed')
    require(sha(auditor_source)==audit['auditor_sha256'],'Provide the exact audited source version')
    models={m['name'] for m in lock['models']}
    require(lock['status']=='frozen' and len(models)==6 and all(m['worker_kind']=='classical' for m in lock['models']),'Frozen classical roster only')
    rows=audit['rows'];condition=audit['condition']
    require(len(rows)==6 and {r['method'] for r in rows}==models,'All6 configurations must be present')
    execution_bytes=(root/'execution.json').read_bytes();state=json.loads(execution_bytes)
    complete={e['name'] for e in state['evaluation'] if e['status']=='complete'}
    mapping={'audit_sha256':'AUDIT.json','trace_sha256':'rollout.npz','execution_sha256':'execution.json',
             'model_sha256':'rollout.mjb','chain_sha256':'execution_chain.npz',
             'substep_metrics_sha256':'rollout_metrics/substep_metrics.npz','research_substeps_sha256':'research_substeps.npz'}
    files={'run/'+n:root/n for n in ('REGISTRATION.json','MODEL_LOCK.json','CONDITIONS.json','PROTOCOL.json')}
    files.update({'audit/CONDITION_AUDIT.json':audit_path.resolve(),
                  'tools/auditor.py':auditor_source.resolve(),'tools/'+Path(__file__).name:Path(__file__).resolve(),
                  'tools/archive_nonrl_new30_physics_20261026.py':Path(__file__).with_name('archive_nonrl_new30_physics_20261026.py')})
    for row in rows:
        require(row['condition']==condition,'Mixed conditions')
        name=row['method']+'__'+condition;run=root/'evaluation'/name
        require(Path(row['run']).resolve()==run and name in complete,'Unfinished/wrong episode')
        require(json.loads((run/'execution.json').read_text())['status']=='complete','Worker not complete')
        for key,relative in mapping.items():
            require(sha(run/relative)==row['source_hashes'][key],'Audited evidence changed: '+str(run/relative))
        metric=root/'metrics'/f'{name}.json'
        require(sha(metric)==row['source_hashes']['metric_sha256'],'Metric changed')
        files['run/metrics/'+metric.name]=metric
        for path in sorted(run.rglob('*')):
            require(not path.is_symlink(),'Do not follow archive symlinks')
            if path.is_file():
                require(path.suffix!='.tmp','Temporary/incomplete file')
                files['run/'+path.relative_to(root).as_posix()]=path
    metadata={}
    for name,path in files.items():
        before=path.stat();digest=sha(path);after=path.stat()
        require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'File changed while hashing')
        metadata[name]={'sha256':digest,'bytes':after.st_size}
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),root=str(root),condition=condition,
                  episodes=6,files=metadata,scope='Complete classical condition only; remaining conditions and final180 not included')
    extra={'MANIFEST.json':(json.dumps(manifest,indent=2)+'\n').encode(),
           'EXECUTION_SNAPSHOT.json':execution_bytes}
    output.mkdir(parents=True,exist_ok=False);partial=output/'PHYSICS_BUNDLE.tar.gz.partial'
    with tarfile.open(partial,'w:gz',compresslevel=1) as tar:
        for name,path in sorted(files.items()):tar.add(path,arcname=name,recursive=False)
        for name,data in extra.items():
            info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
    expected={**metadata,**{k:dict(sha256=hashlib.sha256(v).hexdigest(),bytes=len(v)) for k,v in extra.items()}}
    with tarfile.open(partial,'r:gz') as tar:
        seen=set()
        for member in tar:
            require(member.isfile() and member.name in expected and member.name not in seen,'Unexpected archive member')
            target=expected[member.name]
            require(member.size==target['bytes'] and digest_stream(tar.extractfile(member))==target['sha256'],'Archive payload differs')
            seen.add(member.name)
        require(seen==set(expected),'Missing archive file')
    for name,path in files.items():
        require(path.stat().st_size==metadata[name]['bytes'] and sha(path)==metadata[name]['sha256'],'Source changed during packaging')
    final=output/'PHYSICS_BUNDLE.tar.gz';partial.rename(final)
    receipt=dict(status='local_package_verified_not_yet_shared',condition=condition,episodes=6,
        archive=str(final.resolve()),sha256=sha(final),bytes=final.stat().st_size,
        source_files=len(files),source_bytes=sum(x['bytes'] for x in metadata.values()),
        manifest_sha256=expected['MANIFEST.json']['sha256'],source_before_after_and_archive_payload_verified=True)
    (output/'LOCAL_PACKAGE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','audit','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--auditor-source',type=Path,default=Path(__file__).with_name('audit_nonrl_classical_extension_20261027.py'))
    a=p.parse_args();print(json.dumps(package(a.root,a.audit,a.output,a.auditor_source)))
