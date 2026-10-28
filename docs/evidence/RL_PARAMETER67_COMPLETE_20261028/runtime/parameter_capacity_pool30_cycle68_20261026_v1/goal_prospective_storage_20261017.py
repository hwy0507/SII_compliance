"""Prospective working-set storage; never authorizes historical artifact removal.

Only new rl_goal_stream_* registrations sealed before ANY job output exists are
eligible. Every closed episode, including failures, is retained byte-for-byte on
the archive server before releasing its four large temporary files. The newest
two checkpoints remain local; every earlier checkpoint remains recoverable.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import tarfile
import tempfile

HOST = 'arm1@192.168.31.70'
BASE = '/home/arm1/sii_shared/SII_compliance'
FILES = ('research_substeps.npz', 'independent_contacts.npz',
         'rollout_metrics/substep_metrics.npz', 'rollout.mjb')
SCHEMA = 'sii-prospective-working-set-v1'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(Path(path).parent, os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def canonical(path, parent):
    path, parent = Path(path), Path(parent).resolve()
    if not path.is_absolute() or not path.is_relative_to(parent) or path.resolve() != path:
        raise ValueError('Expected canonical descendant without symlinks')
    return path


def regular(path):
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid():
        raise ValueError('Expected owned regular file with one link')
    return st


def registration(root):
    root = Path(root)
    if root.resolve() != root or root.parent.name != 'outputs' or not root.name.startswith('rl_goal_stream_'):
        raise ValueError('Only distinct prospective stream roots are supported')
    reg = read(root/'REGISTRATION.json')
    if (reg.get('schema') != 'sii-rl-persistent-goal-stage-v1' or
            reg.get('run_root') != str(root) or reg.get('working_set_policy') != SCHEMA or
            reg.get('server_compute') is not False):
        raise ValueError('Missing prospective storage registration')
    for job in reg['jobs']:
        output = canonical(job['output'], root)
        if output.parent != root or output.name != job['name']:
            raise ValueError('Job output must be an immediate named child')
    return reg


def seal(root):
    """Called after frozen registration, before preflight/launch/output creation."""
    root = Path(root); reg = registration(root)
    if any((root/name).exists() for name in ('execution.json','LAUNCH.json')) or any(
            Path(job['output']).exists() for job in reg['jobs']):
        raise ValueError('Cannot retrofit storage policy onto any existing training')
    policy = dict(schema=SCHEMA, registered_utc=datetime.now(timezone.utc).isoformat(),
        run_root=str(root), registration_sha256=sha(root/'REGISTRATION.json'),
        helper_sha256=sha(Path(__file__)), outputs=[j['output'] for j in reg['jobs']],
        absent_outputs_at_seal=True, archive_host=HOST,
        release_files=list(FILES), checkpoints='newest two local; all retained remotely',
        historical_removal_authorized=False)
    write_new(root/'STORAGE_POLICY.json', policy)
    return policy


def validate(root):
    root = Path(root); reg = registration(root); policy = read(root/'STORAGE_POLICY.json')
    if (policy['schema'] != SCHEMA or policy['run_root'] != str(root) or
            policy['registration_sha256'] != sha(root/'REGISTRATION.json') or
            policy['helper_sha256'] != sha(Path(__file__)) or
            policy['outputs'] != [j['output'] for j in reg['jobs']] or
            policy['release_files'] != list(FILES) or
            policy['archive_host'] != HOST or not policy['absent_outputs_at_seal'] or
            policy['historical_removal_authorized'] is not False):
        raise ValueError('Prospective policy identity changed')
    return reg, policy


def prepare(previous, destination):
    """New copy of an unlaunched occupancy pilot; never alter its old snapshot."""
    from datetime import timedelta
    from rl_goal_stage_20261016 import verify_inputs, manifest, write, BENCH
    from goal_tracking_pilot_20261016 import validate_pair, require_predecessor_complete
    previous,destination=Path(previous),Path(destination)
    old=read(previous/'REGISTRATION.json');verify_inputs(old);validate_pair(old)
    require_predecessor_complete(old)
    if old['experiment_kind']!='fresh_parameter_occupancy_pilot': raise ValueError('Only prepared occupancy pair supported')
    if any((previous/name).exists() for name in ('LAUNCH.json','execution.json')) or any(
            Path(j['output']).exists() for j in old['jobs']): raise ValueError('Pilot already launched')
    if destination.exists() or not destination.name.startswith('rl_goal_stream_'):
        raise ValueError('New prospective root required')
    destination.mkdir(parents=True)
    source=destination/'source';parameter=destination/'parameter_n25'
    ignore=shutil.ignore_patterns('__pycache__','*.pyc')
    shutil.copytree(old['source'],source,ignore=ignore)
    shutil.copytree(old['parameter_source'],parameter,ignore=ignore)
    for name in ('goal_prospective_storage_20261017.py','train_v4_recovery_rl_20261016.py','rl_goal_stage_20261016.py'):
        shutil.copy2(BENCH/'tools'/name,source/'tools'/name)
    started=datetime.now(timezone.utc)
    jobs=[]
    for job in old['jobs']:
        output=destination/job['name']
        jobs.append(dict(job,output=str(output),unit='sii-rl-goal-'+hashlib.sha256(str(output).encode()).hexdigest()[:12]))
    reg=dict(old,run_root=str(destination),source=str(source),parameter_source=str(parameter),
        source_manifest=manifest(source),parameter_manifest=manifest(parameter),jobs=jobs,
        registered_utc=started.isoformat(),dispatch_deadline_utc=(started+timedelta(hours=24)).isoformat(),
        stop_file=str(destination/'STOP_REQUESTED'),
        coordinator_unit='sii-rl-goal-stage-'+hashlib.sha256(str(destination).encode()).hexdigest()[:12],
        working_set_policy=SCHEMA,storage_resources=dict(cpu=6,memory_max_bytes=1024**3,swap_max_bytes=0),
        storage_predecessor=dict(root=str(previous),registration_sha256=sha(previous/'REGISTRATION.json')),
        source_worktree_state='Unlaunched occupancy pilot physics, rewards, seed and limits unchanged; prospective storage helper and boundary dispatch added. Manifests authoritative.')
    validate_pair(reg);write(destination/'REGISTRATION.json',reg)
    seal(destination)
    return reg


def verify_preflight(root):
    _,policy=validate(root)
    record=read(Path(root)/'STORAGE_PREFLIGHT.json')
    if (record.get('status')!='passed' or record.get('registration_sha256')!=policy['registration_sha256'] or
            record.get('helper_sha256')!=policy['helper_sha256'] or
            record.get('roundtrip_sha256')!=sha(record['roundtrip_receipt'])):
        raise ValueError('Prospective storage requires actual archive/restore preflight')
    trial=read(record['roundtrip_receipt'])
    if not (trial['real_remote_verified'] and trial['exact_restore'] and trial['checkpoint_preserved']):
        raise ValueError('Incomplete real storage roundtrip')


def boundary(root, episode, python):
    """Separate bounded local helper; caller waits, with no simulator alive."""
    reg,_=validate(root);verify_preflight(root)
    if reg['storage_resources']!=dict(cpu=6,memory_max_bytes=1024**3,swap_max_bytes=0):
        raise ValueError('Storage helper resource registration mismatch')
    available=next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()
                   if line.startswith('MemAvailable:'))
    if available < 1024**3+768*1024**2:
        raise RuntimeError('Insufficient memory for bounded archive helper; checkpoint retained')
    unit='sii-rl-storage-'+hashlib.sha256(str(episode).encode()).hexdigest()[:16]
    command=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
        '-p','MemoryMax=1G','-p','MemorySwapMax=0','-p','AllowedCPUs=6','-p','RuntimeMaxSec=900',
        'taskset','-c','6',python,str(Path(__file__).resolve()),'archive','--root',str(root),'--episode',str(episode)]
    with (Path(episode).parent/(Path(episode).name+'.storage.log')).open('x') as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=960)


def release_old_checkpoints(root, run):
    """Release only checkpoints created under this prospective registration."""
    _, policy=validate(root)
    if str(run) not in policy['outputs']: raise ValueError('Unregistered run')
    state=read(run/'execution.json')
    rows=sorted(state['checkpoint_rows'], key=lambda c:c['step'])
    for cp in rows[:-2]:
        path=canonical(cp['path'],run)
        row=next(r for r in state['rows'] if r.get('step_after')==cp['step'] and r.get('ended_utc'))
        box=run/'storage_receipts'/Path(row['run']).name
        receipt=read(box/'PLANNED.json')
        read(box/'RELEASED.json')
        if (receipt['registration_sha256']!=sha(root/'REGISTRATION.json') or
                receipt['policy_sha256']!=sha(root/'STORAGE_POLICY.json') or receipt['checkpoint']!=cp):
            raise ValueError('Old checkpoint storage identity mismatch')
        remote_verify(receipt['remote'],receipt['archive_bytes'],receipt['archive_sha256'])
        candidates=[]
        for name,digest in cp['hashes'].items():
            p=canonical(path/name,path)
            if name=='office_runner.json': continue
            if p.exists():
                regular(p)
                if sha(p)!=digest: raise ValueError('Checkpoint changed before release')
                candidates.append(p)
        marker=box/'CHECKPOINT_RELEASED.json'
        if not marker.exists(): write_new(marker,dict(receipt=str(box/'PLANNED.json'),checkpoint=cp))
        for p in candidates: p.unlink()


def restore(root, episode, archive):
    """Exact local restore from a downloaded archive; never rebuilds an MJB."""
    root,episode,archive=Path(root),Path(episode),Path(archive)
    _,policy=validate(root)
    canonical(episode,root)
    if str(episode.parent) not in policy['outputs']: raise ValueError('Unregistered episode')
    receipt=read(episode.parent/'storage_receipts'/episode.name/'PLANNED.json')
    if (receipt['registration_sha256']!=sha(root/'REGISTRATION.json') or
            receipt['policy_sha256']!=sha(root/'STORAGE_POLICY.json') or
            receipt['episode']!=str(episode) or
            archive.stat().st_size!=receipt['archive_bytes'] or sha(archive)!=receipt['archive_sha256']):
        raise ValueError('Restore identity/hash mismatch')
    verify_archive(archive,receipt['members'])
    expected={r['member']:r for r in receipt['members']}
    cp=canonical(receipt['checkpoint']['path'],episode.parent)
    if cp.parent!=episode.parent or not cp.name.startswith('checkpoint_'):
        raise ValueError('Unexpected checkpoint destination')
    for record in receipt['members']:
        p=canonical(root/record['member'],root)
        if not (p.is_relative_to(episode) or p.is_relative_to(cp)):
            raise ValueError('Unexpected restore destination')
        if p.exists():
            regular(p)
            if sha(p)!=record['sha256']: raise ValueError('Refusing to overwrite different data')
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            if member.name not in expected: continue
            path=root/member.name
            if path.exists(): continue
            path.parent.mkdir(parents=True,exist_ok=True)
            fd,temporary=tempfile.mkstemp(prefix='.restore-',dir=path.parent)
            try:
                with os.fdopen(fd,'wb') as output,tar.extractfile(member) as source:
                    for block in iter(lambda:source.read(1024*1024),b''): output.write(block)
                    output.flush();os.fsync(output.fileno())
                if sha(temporary)!=expected[member.name]['sha256']: raise ValueError('Restore hash mismatch')
                os.link(temporary,path)
            finally: Path(temporary).unlink()


def closed(root, episode):
    reg, policy = validate(root)
    episode = canonical(episode, root)
    if str(episode.parent) not in policy['outputs'] or not episode.name.startswith('episode_'):
        raise ValueError('Episode outside prospectively registered jobs')
    run = episode.parent; state = read(run/'execution.json')
    row = next((r for r in state['rows'] if r['run'] == str(episode)), None)
    if not row or not row.get('ended_utc') or row.get('step_after') is None:
        raise ValueError('Episode is still in flight')
    if sha(episode/'AUDIT.json') != row['audit_sha256'] or sha(episode/'rollout.npz') != row['trace_sha256']:
        raise ValueError('Native closed receipt hash mismatch')
    if not read(episode/'AUDIT.json').get('training') or not read(episode/'execution.json').get('ended_utc'):
        raise ValueError('Expected closed training episode')
    cp = canonical(run/f"checkpoint_{row['step_after']:07d}", run)
    saved = next((c for c in state['checkpoint_rows'] if c['path'] == str(cp)), None)
    runner = read(cp/'office_runner.json')
    if not saved or runner['step'] != row['step_after'] or not runner['episode_boundary'] or runner['pending_transition'] is not None:
        raise ValueError('Closed checkpoint required before archiving')
    for name, digest in saved['hashes'].items():
        if sha(canonical(cp/name, cp)) != digest:
            raise ValueError('Checkpoint member changed')
    return row, saved


def verify_archive(archive, records):
    expected = {r['member']:r for r in records}; seen = set()
    if len(expected) != len(records): raise ValueError('Duplicate requested member')
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in expected: continue
            record = expected[member.name]
            if member.name in seen or not member.isfile() or member.size != record['bytes']:
                raise ValueError('Invalid archive member')
            with tar.extractfile(member) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
                    raise ValueError('Archive member hash mismatch')
            seen.add(member.name)
    if seen != set(expected): raise ValueError('Missing archive members')


def ssh(command):
    return subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',
                                   HOST,command], text=True, timeout=120)


def remote_verify(remote, size, digest):
    lines = ssh('stat -c %s '+shlex.quote(remote)+' && sha256sum '+shlex.quote(remote)).splitlines()
    if len(lines) != 2 or int(lines[0]) != size or lines[1].split()[0] != digest:
        raise ValueError('Remote archive does not match')


def publish(archive, receipt):
    """Exclusive final publication; existing final is accepted only if identical."""
    remote = receipt['remote']; final = str(Path(remote).parent)
    if ssh('if test -e '+shlex.quote(final)+'; then echo exists; else echo absent; fi').strip() == 'exists':
        remote_verify(remote, receipt['archive_bytes'], receipt['archive_sha256']); return
    incoming = BASE+'/incoming/'+Path(final).name
    ssh('mkdir -p '+shlex.quote(incoming))
    target = incoming+'/evidence.tar.gz'
    subprocess.run(['rsync','-a','--partial','--timeout=60',str(archive),HOST+':'+target], check=True, timeout=600)
    remote_verify(target, receipt['archive_bytes'], receipt['archive_sha256'])
    ssh('mkdir '+shlex.quote(final)+' && mv -n '+shlex.quote(target)+' '+shlex.quote(remote))
    remote_verify(remote, receipt['archive_bytes'], receipt['archive_sha256'])


def archive_episode(root, episode):
    """Must run while trainer waits at its safe checkpoint boundary."""
    root, episode = Path(root), Path(episode)
    row, checkpoint = closed(root, episode)
    box = episode.parent/'storage_receipts'/episode.name
    box.mkdir(parents=True, exist_ok=True)
    archive = box/'transfer.tar.gz'; plan = box/'PLANNED.json'
    if (box/'RELEASED.json').exists():
        receipt = read(box/'PLANNED.json')
        remote_verify(receipt['remote'],receipt['archive_bytes'],receipt['archive_sha256'])
        release_old_checkpoints(root,episode.parent)
        return receipt
    if plan.exists():
        receipt = read(plan)
        if sha(archive) != receipt['archive_sha256']: raise ValueError('Transfer cache changed')
        verify_archive(archive,receipt['members'])
    else:
        if archive.exists(): raise ValueError('Incomplete archive retained; inspect before retry')
        files = sorted(p for p in episode.rglob('*') if p.is_file())
        files += sorted(p for p in Path(checkpoint['path']).rglob('*') if p.is_file())
        records = []
        for path in files:
            canonical(path, root); st = regular(path)
            records.append(dict(member=str(path.relative_to(root)),bytes=st.st_size,sha256=sha(path)))
        with tarfile.open(archive,'x:gz',compresslevel=1) as tar:
            for path in files: tar.add(path,arcname=str(path.relative_to(root)),recursive=False)
        verify_archive(archive,records)
        identity = hashlib.sha256((str(root)+'/'+str(episode.relative_to(root))).encode()).hexdigest()[:24]
        receipt = dict(schema=SCHEMA,registration_sha256=sha(root/'REGISTRATION.json'),
            policy_sha256=sha(root/'STORAGE_POLICY.json'),episode=str(episode),row=row,checkpoint=checkpoint,
            members=records,archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
            remote=BASE+'/runs/main/goal-stream-'+identity+'/evidence.tar.gz',host=HOST)
        write_new(plan,receipt)
    if receipt['registration_sha256'] != sha(root/'REGISTRATION.json') or receipt['policy_sha256'] != sha(root/'STORAGE_POLICY.json'):
        raise ValueError('Registration changed after archive')
    publish(archive,receipt)
    if not (box/'VERIFIED.json').exists():
        write_new(box/'VERIFIED.json',dict(remote=receipt['remote'],sha256=receipt['archive_sha256'],
            bytes=receipt['archive_bytes'],verified_utc=datetime.now(timezone.utc).isoformat()))
    # Validate all release candidates before touching any. Idempotent after a
    # partial release: absent candidates have durable PLANNED/VERIFIED receipts.
    release = []
    by_name = {r['member']:r for r in receipt['members']}
    for name in FILES:
        path = canonical(episode/name,episode)
        record = by_name[str(path.relative_to(root))]
        if path.exists():
            st=regular(path)
            if st.st_size!=record['bytes'] or sha(path)!=record['sha256']:
                raise ValueError('Working file changed; preserve all remaining copies')
            release.append((path,st))
    for path, before in release:
        after=regular(path)
        if (before.st_ino,before.st_mtime_ns,before.st_size)!=(after.st_ino,after.st_mtime_ns,after.st_size):
            raise ValueError('Working file changed during release')
        path.unlink()
    write_new(box/'RELEASED.json',dict(utc=datetime.now(timezone.utc).isoformat(),
        files=[str(episode/name) for name in FILES],remote=receipt['remote'],
        checkpoint_files_removed=0,historical_files_removed=0))
    archive.unlink()  # Sole transfer cache; durable exact archive verified above.
    release_old_checkpoints(root,episode.parent)
    return receipt


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','seal','archive','restore'))
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--episode',type=Path)
    parser.add_argument('--archive',type=Path)
    parser.add_argument('--previous',type=Path)
    args=parser.parse_args()
    if args.mode=='prepare':
        if args.previous is None: parser.error('prepare requires previous')
        print(json.dumps(prepare(args.previous.resolve(),args.root.resolve())))
    elif args.mode=='seal': print(json.dumps(seal(args.root)))
    elif args.mode=='archive':
        if args.episode is None: parser.error('archive requires --episode')
        print(json.dumps(archive_episode(args.root,args.episode)))
    else:
        if args.episode is None or args.archive is None: parser.error('restore requires episode and archive')
        restore(args.root,args.episode,args.archive)
