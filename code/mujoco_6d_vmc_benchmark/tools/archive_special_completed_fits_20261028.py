"""Archive the entire completed, audited new-scene fit grid without pruning."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile


def require(test, message):
    if not test:
        raise ValueError(message)


def digest(stream):
    value = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1 << 20), b''):
        value.update(chunk)
    return value.hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return digest(stream)


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--fit-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    require(not output.exists() and output != root and root not in output.parents,
            'Use a new archive directory outside the training run')
    state = read(root/'execution.json')
    require(state['status'] == 'complete' and len(state['fits']) == 75
            and all(r['status'] == 'complete' for r in state['fits']), 'Complete original75 required')
    audit = read(args.fit_audit)
    require(audit['status'] == 'passed' and len(audit['candidate_jobs']) == 75
            and len(audit['frozen_actor_replays']) == 9, 'Complete fit audit required')
    require(audit['model_lock_sha256'] == state['model_lock_sha256'] == sha(root/'MODEL_LOCK.json'), 'Model lock changed')
    require(audit['dataset_sha256'] == sha(root/'data/training_data.npz'), 'Dataset changed')
    audited = {r['name']: r for r in audit['candidate_jobs']}
    for row in state['fits']:
        folder = Path(row['output']).resolve()
        require(folder.parent == root/'learning', 'Candidate outside registered learning root')
        require(sha(folder/'checkpoint.npz') == row['checkpoint_sha256'] == audited[row['name']]['checkpoint_sha256'], 'Candidate changed')
        require(sha(folder/'TRAINING_COMPLETE.json') == row['metadata_sha256'], 'Candidate receipt changed')
    files = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'Symlink not an archive payload')
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            require(path.suffix != '.tmp', 'Incomplete temporary file present')
            files['training/'+path.relative_to(root).as_posix()] = path
    files['FIT_AUDIT.json'] = args.fit_audit.resolve()
    files['archive_tool.py'] = Path(__file__).resolve()
    manifest = {}
    for name, path in files.items():
        before = path.stat()
        h = sha(path)
        after = path.stat()
        require((before.st_size,before.st_mtime_ns) == (after.st_size,after.st_mtime_ns), 'Source changed while hashing')
        manifest[name] = dict(bytes=after.st_size, sha256=h)
    header = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_root=str(root),
        scope='Entire completed75 fit jobs/108 candidates, selected9 lock, dataset, schedules, histories, receipts and fitting sources; no new108 physical trajectories and no old failed teacher runs (archived separately).',
        model_lock_sha256=audit['model_lock_sha256'], dataset_sha256=audit['dataset_sha256'], files=manifest)
    data = (json.dumps(header,indent=2)+'\n').encode()
    output.mkdir(parents=True)
    partial = output/'COMPLETE_FITS.tar.gz.partial'
    with tarfile.open(partial,'w:gz',compresslevel=1) as archive:
        for name, path in files.items():
            archive.add(path,arcname=name,recursive=False)
        info = tarfile.TarInfo('MANIFEST.json');info.size=len(data)
        archive.addfile(info,io.BytesIO(data))
    expected = {**manifest,'MANIFEST.json':dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())}
    seen = set()
    with tarfile.open(partial,'r:gz') as archive:
        for member in archive:
            require(member.isfile() and member.name in expected and member.name not in seen, 'Unexpected archive member')
            target = expected[member.name]
            require(member.size == target['bytes'] and digest(archive.extractfile(member)) == target['sha256'], 'Archive payload mismatch')
            seen.add(member.name)
    require(seen == set(expected), 'Incomplete archive')
    for name,path in files.items():
        require(path.stat().st_size == manifest[name]['bytes'] and sha(path) == manifest[name]['sha256'], 'Source changed during packaging')
    final = output/'COMPLETE_FITS.tar.gz'
    partial.rename(final)
    result = dict(status='local_complete_fit_archive_verified_not_yet_shared', archive=str(final),
        bytes=final.stat().st_size, sha256=sha(final), payload_files=len(files),
        manifest_sha256=expected['MANIFEST.json']['sha256'], source_and_archive_payloads_match=True,
        model_lock_sha256=audit['model_lock_sha256'], dataset_sha256=audit['dataset_sha256'])
    (output/'LOCAL_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
