"""Archive the complete audited special-scene frozen108 and its exact sources.

Read-only toward experiments. Refuses partial matrices and missing contact
diagnostics. Does not run physics, transfer data, prune failures, or certify
visual review/goal completion. The full training archive is separate.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile

from archive_nonrl_new30_physics_20261026 import digest_stream, require, sha
from prepare_special_frozen_test_20261028 import manifest as source_manifest


def read(path):
    return json.loads(path.read_text())


def package(handoff, output):
    handoff, output = handoff.resolve(), output.resolve()
    require(not output.exists(), 'Use a new archive directory')
    state = read(handoff / 'execution.json')
    require(state['status'] == 'complete_pending_visual_review_and_archive',
            'Original handoff must finish all108 and postprocessing first')
    plan = read(handoff / 'REGISTRATION.json')
    require(sha(handoff / 'REGISTRATION.json') == state['registration_sha256'], 'Handoff registration changed')
    preparation, root = Path(plan['preparation']).resolve(), Path(plan['evaluation']).resolve()
    roots = {'evaluation': root, 'handoff': handoff, 'preparation': preparation}
    require(all(output != p and p not in output.parents and output not in p.parents
                for p in roots.values()), 'Archive must be outside all experiment roots')
    require(sha(preparation / 'REGISTRATION.json') == plan['preparation_sha256'], 'Preparation changed')
    for name, digest in plan['snapshot_sha256'].items():
        require(sha(handoff / 'tools' / name) == digest, 'Handoff source changed')
    audit_path = handoff / 'FINAL_AUDIT.json'
    audit = read(audit_path)
    require(sha(audit_path) == state['final_audit_sha256'], 'Final audit changed')
    require(audit['status'] == 'frozen108_saved_evidence_audit_passed'
            and audit['verified_episodes'] == 108, 'Full108 audit required')
    require(Path(audit['preparation']).resolve() == preparation, 'Wrong audit preparation')
    report, execution = read(root / 'REPORT.json'), read(root / 'execution.json')
    require(report['status'] == execution['status'] == 'complete'
            and execution['completed'] == execution['expected'] == 108, 'Full108 completion required')
    require(sha(root / 'REPORT.json') == audit['report_sha256'] == execution['report_sha256'], 'Report changed')
    require(sha(root / 'INPUT_MODEL_LOCK.json') == audit['model_lock_sha256'], 'Model lock changed')
    lock = read(root / 'INPUT_MODEL_LOCK.json')
    models = {m['name'] for m in lock['models']}
    model_records = {m['name']: m for m in lock['models']}
    prep = read(preparation / 'REGISTRATION.json')
    require(source_manifest(root / 'source') == prep['physics_source_sha256'], 'Frozen physics sources changed')
    conditions = set(prep['conditions'])
    require(len(models) == 9 and len(conditions) == 12, 'Wrong matrix size')
    expected = Counter({(m, c): 1 for m in models for c in conditions})
    require(Counter((r['method'], r['condition']) for r in report['rows']) == expected, 'Missing/duplicate matrix cells')
    contact = read(handoff / 'CONTACT_DIAGNOSTICS.json')
    require(contact['status'] == 'complete108_contact_diagnostics'
            and contact['audit_sha256'] == sha(audit_path)
            and contact['report_sha256'] == audit['report_sha256'], 'Complete matching contact supplement required')
    require(Counter((r['method'], r['condition']) for r in contact['rows']) == expected, 'Incomplete contact diagnostics')
    presentation = read(handoff / 'PRESENTATION/PRESENTATION_RECEIPT.json')
    require(presentation['status'] == 'rendered_from_complete_audited_new108'
            and presentation['audit_sha256'] == sha(audit_path), 'Matching final presentation required')
    require(presentation['report_sha256'] == audit['report_sha256']
            and presentation['model_lock_sha256'] == audit['model_lock_sha256'], 'Presentation lineage changed')
    for name, digest in presentation['figures'].items():
        require(sha(handoff / 'PRESENTATION' / name) == digest, 'Final figure changed')
    require(sha(handoff / 'PRESENTATION/REPORT.md') == presentation['markdown_sha256'], 'Final markdown changed')
    learning = read(handoff / 'LEARNING_CURVES/LEARNING_CURVE_EVIDENCE.json')
    require(learning['model_lock_sha256'] == audit['model_lock_sha256'], 'Learning plots used another model lock')
    for name, digest in learning['figures'].items():
        require(sha(handoff / 'LEARNING_CURVES' / name) == digest, 'Learning figure changed')
    fields = {'audit_sha256': 'AUDIT.json', 'trace_sha256': 'rollout.npz',
              'model_sha256': 'rollout.mjb', 'execution_sha256': 'execution.json',
              'chain_sha256': 'execution_chain.npz',
              'substep_metrics_sha256': 'rollout_metrics/substep_metrics.npz',
              'research_substeps_sha256': 'research_substeps.npz'}
    for row in report['rows']:
        run = root / 'evaluation' / (row['method'] + '__' + row['condition'])
        require(Path(row['run']).resolve() == run and read(run / 'execution.json')['status'] == 'complete', 'Wrong/unfinished episode')
        require(sha(run / 'checkpoint.npz') == model_records[row['method']]['checkpoint_sha256'], 'Physical checkpoint changed')
        for key, relative in fields.items():
            require(sha(run / relative) == row[key], 'Audited episode changed: ' + str(run / relative))
        require(sha(root / 'metrics' / (run.name + '.json')) == row['metric_sha256'], 'Episode metric changed')
    files = {}
    for label, folder in roots.items():
        for path in sorted(folder.rglob('*')):
            require(not path.is_symlink(), 'Do not archive symlinks')
            if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ('.pyc', '.lock'):
                require(path.suffix not in ('.tmp', '.partial'), 'Unfinished file retained; inspect before archive')
                files[label + '/' + path.relative_to(folder).as_posix()] = path
    files['archive_tools/' + Path(__file__).name] = Path(__file__).resolve()
    helper = Path(__file__).with_name('archive_nonrl_new30_physics_20261026.py')
    files['archive_tools/' + helper.name] = helper
    metadata = {}
    for name, path in files.items():
        before = path.stat(); digest = sha(path); after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'File changed while hashing')
        metadata[name] = dict(bytes=after.st_size, sha256=digest)
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                    roots={k: str(v) for k, v in roots.items()}, episodes=108, files=metadata,
                    report_sha256=audit['report_sha256'], model_lock_sha256=audit['model_lock_sha256'],
                    scope='All108 physical episodes including failures; all evaluation, preparation and handoff sources/receipts/plots/contact diagnostics. Full training and older failed collection archives are separate. No visual-review or goal-completion certification.')
    content = (json.dumps(manifest, indent=2) + '\n').encode()
    output.mkdir(parents=True)
    partial = output / 'FROZEN108.tar.gz.partial'
    with tarfile.open(partial, 'w:gz', compresslevel=1) as archive:
        for name, path in files.items():
            archive.add(path, arcname=name, recursive=False)
        info = tarfile.TarInfo('MANIFEST.json'); info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    expected_files = {**metadata, 'MANIFEST.json': dict(bytes=len(content), sha256=hashlib.sha256(content).hexdigest())}
    seen = set()
    with tarfile.open(partial, 'r:gz') as archive:
        for member in archive:
            require(member.isfile() and member.name in expected_files and member.name not in seen, 'Unexpected archive member')
            target = expected_files[member.name]
            require(member.size == target['bytes'] and digest_stream(archive.extractfile(member)) == target['sha256'], 'Archive payload differs')
            seen.add(member.name)
    require(seen == set(expected_files), 'Missing archive members')
    for name, path in files.items():
        require(path.stat().st_size == metadata[name]['bytes'] and sha(path) == metadata[name]['sha256'], 'Source changed during packaging')
    final = output / 'FROZEN108.tar.gz'; partial.rename(final)
    receipt = dict(status='local_full108_archive_verified_not_yet_shared', archive=str(final),
                   bytes=final.stat().st_size, sha256=sha(final), payload_files=len(files), episodes=108,
                   manifest_sha256=expected_files['MANIFEST.json']['sha256'],
                   source_before_after_and_archive_payloads_verified=True)
    (output / 'LOCAL_RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.handoff, args.output)))
