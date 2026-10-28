"""Offline large CLOSED training artifacts only after exact archive verification.

Never handles checkpoints, sources, active runs or acceptance. Small receipts and
25/250Hz diagnostic traces stay local. Restore uses archived bytes, not rebuilds.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import stat
import subprocess
import tarfile
import tempfile

BENCH = Path(__file__).resolve().parents[1]
HOST = 'arm1@192.168.31.70'
REMOTE_BASE = '/home/arm1/sii_shared/SII_compliance/runs/main/'
FILES = ('research_substeps.npz', 'independent_contacts.npz',
         'rollout_metrics/substep_metrics.npz', 'rollout.mjb')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, data):
    with Path(path).open('x') as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def safe_path(path, base):
    path, base = Path(path), Path(base).resolve()
    if not path.is_absolute() or not path.is_relative_to(base) or path.resolve() != path:
        raise ValueError('Artifact must be an absolute canonical path without symlinks')
    return path


def closed_episode(episode, bench=BENCH):
    bench = Path(bench).resolve()
    episode = safe_path(episode, bench/'outputs')
    run, root = episode.parent, episode.parent.parent
    if not root.name.startswith('rl_goal_') or not episode.name.startswith('episode_'):
        raise ValueError('Only registered Goal training episodes are eligible')
    reg = read(root/'REGISTRATION.json')
    if reg['schema'] != 'sii-rl-persistent-goal-stage-v1' or reg['run_root'] != str(root):
        raise ValueError('Registration root mismatch')
    if not any(j['output'] == str(run) for j in reg['jobs']):
        raise ValueError('Episode is outside registered jobs')
    state = read(run/'execution.json')
    if state['status'] != 'complete':
        raise ValueError('Training arm must be terminal before offlining')
    row = next((r for r in state['rows'] if r['run'] == str(episode)), None)
    if not row or not row.get('ended_utc') or 'step_after' not in row:
        raise ValueError('Episode is not closed')
    if sha(episode/'AUDIT.json') != row['audit_sha256']:
        raise ValueError('Audit hash mismatch')
    audit = read(episode/'AUDIT.json')
    if not audit.get('training') or not read(episode/'execution.json').get('ended_utc'):
        raise ValueError('Only closed training artifacts supported')
    # Failed and early episodes are equally eligible; never select by success.
    return dict(registration_sha256=sha(root/'REGISTRATION.json'),
                training_execution_sha256=sha(run/'execution.json'),
                audit_sha256=row['audit_sha256'])


def remote_verify(remote, size, digest):
    path = PurePosixPath(remote)
    if (not remote.startswith(REMOTE_BASE) or str(path) != remote or
            '..' in path.parts or len(path.parts) != len(PurePosixPath(REMOTE_BASE).parts)+2 or
            path.name != 'evidence.tar.gz'):
        raise ValueError('Expected independent final run archive, never incoming')
    command = 'stat -c %s ' + shlex.quote(remote) + ' && sha256sum ' + shlex.quote(remote)
    lines = subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',
                                     HOST,command], text=True, timeout=60).splitlines()
    if len(lines) != 2 or int(lines[0]) != size or lines[1].split()[0] != digest:
        raise ValueError('Remote archive size/hash mismatch')


def regular(path):
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid():
        raise ValueError('Expected owned ordinary file with one link')
    return st


def verify_members(archive, records):
    # A compressed tar cannot seek backwards cheaply. Scan it once, including
    # the tail, so a later duplicate is still rejected without repeatedly
    # decompressing every checkpoint between the requested episode members.
    expected = {record['member']: record for record in records}
    if len(expected) != len(records):
        raise ValueError('Duplicate requested archive member')
    seen = set()
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            if member.name not in expected:
                continue
            record = expected[member.name]
            if member.name in seen or not member.isfile() or member.size != record['bytes']:
                raise ValueError('Missing, duplicate, linked or wrong-sized archive member')
            with tar.extractfile(member) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
                    raise ValueError('Archive member bytes differ from original')
            seen.add(member.name)
    if seen != set(expected):
        raise ValueError('Missing archive member')


def plan(episode, archive, remote, digest, bench=BENCH):
    episode = Path(episode)
    identity = closed_episode(episode, bench)
    archive = Path(archive).resolve()
    if sha(archive) != digest:
        raise ValueError('Local archive hash mismatch')
    size = archive.stat().st_size
    remote_verify(remote, size, digest)
    records = []
    for name in FILES:
        path = safe_path(episode/name, episode)
        st = regular(path)
        records.append(dict(path=str(path), member=str(path.relative_to(bench)),
                            bytes=st.st_size, sha256=sha(path), inode=st.st_ino,
                            device=st.st_dev, mtime_ns=st.st_mtime_ns))
    verify_members(archive, records)
    return dict(schema='sii-goal-offline-episode-v1', created_utc=datetime.now(timezone.utc).isoformat(),
                episode=str(episode), identity=identity, archive_sha256=digest,
                archive_bytes=size, archive_local=str(archive), archive_host=HOST,
                archive_remote=remote, files=records, total_bytes=sum(r['bytes'] for r in records),
                scope='Only four large training artifacts; failures retained remotely, all checkpoints remain local')


def validate_receipt(receipt, archive, bench=BENCH):
    if receipt['schema'] != 'sii-goal-offline-episode-v1' or receipt['archive_host'] != HOST:
        raise ValueError('Unsupported receipt')
    episode = Path(receipt['episode'])
    if closed_episode(episode, bench) != receipt['identity']:
        raise ValueError('Closed experiment identity changed')
    if len(receipt['files']) != len(FILES):
        raise ValueError('Artifact allowlist mismatch')
    for record, name in zip(receipt['files'], FILES):
        path = safe_path(episode/name, episode)
        if record['path'] != str(path) or record['member'] != str(path.relative_to(bench)):
            raise ValueError('Artifact path or member was changed')
    if Path(archive).stat().st_size != receipt['archive_bytes'] or sha(archive) != receipt['archive_sha256']:
        raise ValueError('Local archive changed')
    remote_verify(receipt['archive_remote'], receipt['archive_bytes'], receipt['archive_sha256'])
    verify_members(archive, receipt['files'])


def evict(receipt, archive, journal, bench=BENCH):
    validate_receipt(receipt, archive, bench)
    for record in receipt['files']:
        path = Path(record['path']); st = regular(path)
        if ((st.st_ino, st.st_dev, st.st_mtime_ns, st.st_size) !=
                (record['inode'], record['device'], record['mtime_ns'], record['bytes']) or
                sha(path) != record['sha256']):
            raise ValueError('Original artifact changed since planning; nothing removed')
    with Path(journal).open('x') as stream:
        for record in receipt['files']:
            path = Path(record['path']); st = regular(path)
            if (st.st_ino, st.st_dev, st.st_mtime_ns) != (record['inode'], record['device'], record['mtime_ns']):
                raise ValueError('Artifact changed during removal; inspect journal')
            stream.write(json.dumps(dict(event='before_remove',**record))+'\n')
            stream.flush(); os.fsync(stream.fileno())
            path.unlink()
            stream.write(json.dumps(dict(event='removed',path=str(path)))+'\n')
            stream.flush(); os.fsync(stream.fileno())


def restore(receipt, archive, bench=BENCH):
    validate_receipt(receipt, archive, bench)
    # No tar extraction: only verified allowlisted members are written, exclusively.
    with tarfile.open(archive, 'r:gz') as tar:
        for record in receipt['files']:
            path = Path(record['path'])
            if path.exists():
                regular(path)
                if sha(path) != record['sha256']:
                    raise ValueError('Refusing to overwrite an existing different artifact')
                continue
            descriptor, temporary = tempfile.mkstemp(prefix='.restore-',dir=path.parent)
            try:
                with os.fdopen(descriptor,'wb') as output, tar.extractfile(record['member']) as source:
                    for block in iter(lambda: source.read(1024*1024), b''):
                        output.write(block)
                    output.flush(); os.fsync(output.fileno())
                if sha(temporary) != record['sha256']:
                    raise ValueError('Restored byte hash mismatch')
                os.link(temporary,path)  # Exclusive: refuses any concurrently created destination.
            finally:
                Path(temporary).unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('plan','evict','restore'))
    parser.add_argument('--episode',type=Path)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--remote')
    parser.add_argument('--sha256')
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--journal',type=Path)
    args=parser.parse_args()
    if args.mode=='plan':
        if not all((args.episode,args.remote,args.sha256)):parser.error('plan requires episode, remote and sha256')
        receipt=plan(args.episode,args.archive,args.remote,args.sha256)
        write_new(args.receipt,receipt)
        print(json.dumps(dict(planned_files=len(receipt['files']),bytes=receipt['total_bytes'])))
    elif args.mode=='evict':
        if not args.journal:parser.error('evict requires an exclusive journal path')
        evict(read(args.receipt),args.archive,args.journal)
        print('Archived copies retained; four allowlisted local artifacts removed')
    else:
        restore(read(args.receipt),args.archive)
        print('All four artifacts present with original hashes')


if __name__=='__main__':
    main()
