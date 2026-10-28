"""Archive the stopped35 and complete10 without pruning physical failures."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1 << 20), b''):
        h.update(block)
    return h.hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return digest(stream)


def read(path):
    return json.loads(path.read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--old', type=Path, required=True)
    p.add_argument('--controls', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    old, controls, output = a.old.resolve(), a.controls.resolve(), a.output.resolve()
    assert not output.exists()
    assert output not in (old, controls) and old not in output.parents and controls not in output.parents
    state = read(old/'execution.json')
    assert state['status'] == 'stopped_at_episode_boundary'
    assert state['completed'] == len(state['results']) == len(state['rows']) == 35
    complete = read(controls/'execution.json')
    assert complete['status'] == 'complete_pending_review' and len(complete['episodes']) == 10
    review = read(controls/'REVIEW.json')
    assert review['execution_sha256'] == sha(controls/'execution.json')
    files = {}
    for prefix, root in (('stopped35', old), ('controls10', controls)):
        for path in sorted(root.rglob('*')):
            assert not path.is_symlink(), path
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                assert path.suffix != '.tmp', path
                files[prefix+'/'+path.relative_to(root).as_posix()] = path
    files['archive_tool.py'] = Path(__file__).resolve()
    manifest = {name: dict(bytes=path.stat().st_size, sha256=sha(path)) for name, path in files.items()}
    header = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  scope='All completed35 frozen-test failures plus complete10 matched diagnostic controls, including raw trajectories, physical substeps, checkpoints, sources, registrations, failure labels and review. No in-flight teacher-factor experiment.',
                  source_roots=[str(old), str(controls)], files=manifest)
    payload = (json.dumps(header, indent=2)+'\n').encode()
    output.mkdir(parents=True)
    partial = output/'FULL_REGRESSION.tar.partial'
    with tarfile.open(partial, 'w') as archive:
        for name, path in files.items():
            archive.add(path, arcname=name, recursive=False)
        info = tarfile.TarInfo('MANIFEST.json')
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    expected = dict(manifest, **{'MANIFEST.json': dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())})
    seen = set()
    with tarfile.open(partial) as archive:
        for member in archive:
            assert member.isfile() and member.name in expected and member.name not in seen
            assert member.size == expected[member.name]['bytes']
            assert digest(archive.extractfile(member)) == expected[member.name]['sha256']
            seen.add(member.name)
    assert seen == set(expected)
    for name, path in files.items():
        assert path.stat().st_size == manifest[name]['bytes'] and sha(path) == manifest[name]['sha256']
    final = output/'FULL_REGRESSION.tar'
    partial.rename(final)
    result = dict(status='locally_verified_pending_share', archive=str(final),
                  bytes=final.stat().st_size, sha256=sha(final), payload_files=len(files),
                  source_and_archive_match=True, scope=header['scope'])
    (output/'LOCAL_RECEIPT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
