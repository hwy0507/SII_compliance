"""Archive terminal non-RL collections or controls, preserving every failure."""
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
    p.add_argument('--old', type=Path)
    p.add_argument('--controls', type=Path)
    p.add_argument('--collection', type=Path)
    p.add_argument('--probe', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    output = a.output.resolve()
    assert not output.exists()
    if a.probe:
        assert a.old is None and a.controls is None and a.collection is None
        probe = a.probe.resolve()
        state, reg = read(probe/'execution.json'), read(probe/'REGISTRATION.json')
        assert state['status'] == 'complete_pending_review'
        assert state['registration_sha256'] == sha(probe/'REGISTRATION.json')
        assert len(state['episodes']) == len(reg['cases']) == reg['maximum_episodes']
        for case, row in zip(reg['cases'], state['episodes']):
            assert case['id'] == row['id'] and row['returncode'] == 0
            folder = probe/case['id']
            if case['kind'] == 'scene':
                folder /= case['scene']
                q = read(folder/'DEMONSTRATION_QUALIFICATION.json')
                assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == row['qualification_sha256']
                for name, h in q['input_hashes'].items():
                    assert sha(folder/name) == h
            else:
                assert sha(folder/'AUDIT.json') == row['audit_sha256']
                for name, key in [('rollout.npz', 'trace_sha256'), ('rollout.mjb', 'model_sha256'),
                                  ('execution_chain.npz', 'chain_sha256'),
                                  ('rollout_metrics/substep_metrics.npz', 'metrics_sha256')]:
                    assert sha(folder/name) == row['audit'][key]
        roots = [('probe', probe)]
        scope = 'Every terminal registered probe identity (teacher controls or student diagnostics), including failures, raw physical substeps, source snapshots, configurations and complete qualification/audit receipts. Actor roles and model identities remain in the original execution records. No in-flight successor or student training.'
        filename = 'FULL_PROBE.tar'
    elif a.collection:
        assert a.old is None and a.controls is None
        collection = a.collection.resolve()
        state = read(collection/'COLLECTION_PROGRESS.json')
        plan = read(collection/'COLLECTION_PLAN.json')
        assert state['status'] in ('qualified_complete', 'finished_with_nonqualified_demonstrations')
        assert len(state['episodes']) == len(plan['episodes']) == 30
        assert state['plan_sha256'] == sha(collection/'COLLECTION_PLAN.json')
        for entry, receipt in zip(plan['episodes'], state['episodes']):
            assert entry['id'] == receipt['id']
            folder = Path(entry['folder'])
            q = read(folder/'DEMONSTRATION_QUALIFICATION.json')
            assert q['status'] == receipt['status']
            for name, h in q['input_hashes'].items():
                assert sha(folder/name) == h
        roots = [('collection30', collection)]
        scope = 'All30 completed collection identities including every nonqualified demonstration; raw trajectories, physical substeps, source snapshots, configuration and qualifications. No student fitting or in-flight follow-up probes.'
        filename = 'FULL_COLLECTION.tar'
    else:
        assert a.old is not None and a.controls is not None
        old, controls = a.old.resolve(), a.controls.resolve()
        state = read(old/'execution.json')
        assert state['status'] == 'stopped_at_episode_boundary'
        assert state['completed'] == len(state['results']) == len(state['rows']) == 35
        complete = read(controls/'execution.json')
        assert complete['status'] == 'complete_pending_review' and len(complete['episodes']) == 10
        review = read(controls/'REVIEW.json')
        assert review['execution_sha256'] == sha(controls/'execution.json')
        roots = [('stopped35', old), ('controls10', controls)]
        scope = 'All completed35 frozen-test failures plus complete10 matched diagnostic controls, including raw trajectories, physical substeps, checkpoints, sources, registrations, failure labels and review. No in-flight teacher-factor experiment.'
        filename = 'FULL_REGRESSION.tar'
    assert all(output != root and root not in output.parents for _,root in roots)
    files = {}
    for prefix, root in roots:
        for path in sorted(root.rglob('*')):
            assert not path.is_symlink(), path
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                assert path.suffix != '.tmp', path
                files[prefix+'/'+path.relative_to(root).as_posix()] = path
    files['archive_tool.py'] = Path(__file__).resolve()
    manifest = {name: dict(bytes=path.stat().st_size, sha256=sha(path)) for name, path in files.items()}
    header = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  scope=scope, source_roots=[str(root) for _,root in roots], files=manifest)
    payload = (json.dumps(header, indent=2)+'\n').encode()
    output.mkdir(parents=True)
    partial = output/(filename+'.partial')
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
    final = output/filename
    partial.rename(final)
    result = dict(status='locally_verified_pending_share', archive=str(final),
                  bytes=final.stat().st_size, sha256=sha(final), payload_files=len(files),
                  source_and_archive_match=True, scope=header['scope'])
    (output/'LOCAL_RECEIPT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
