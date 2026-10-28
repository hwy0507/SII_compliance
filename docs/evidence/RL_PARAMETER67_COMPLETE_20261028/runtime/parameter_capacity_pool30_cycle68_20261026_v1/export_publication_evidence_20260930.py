"""Export small archived teacher evidence and index retained local artifacts.

Run from any directory. No simulation, remote access, or artifact deletion.
The manifest deliberately covers only results binaries, evidence MJB files,
and the three named teacher campaigns, not every historical output directory.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/evidence/publication_20260930'
CAMPAIGNS = (
    'teacher_repair_20260930',
    'teacher_repair_canonical_20260930',
    'teacher_repair_followup_20260930',
)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    entries = []
    paths = set()
    for directory, suffixes in ((ROOT / 'results', {'.npz', '.mjb'}),
                                (ROOT / 'docs/evidence', {'.mjb'})):
        paths.update(p for p in directory.rglob('*') if p.is_file() and p.suffix in suffixes)
    for name in CAMPAIGNS:
        campaign = ROOT / 'outputs' / name
        if not campaign.is_dir():
            raise FileNotFoundError(campaign)
        paths.update(p for p in campaign.rglob('*') if p.is_file())
    DEST.mkdir(parents=True, exist_ok=True)
    for path in sorted(paths):
        # Do not duplicate the follow-up's symlinked original references.
        if any(p.is_symlink() for p in (path, *path.parents)):
            continue
        before = path.stat()
        entry = {'path': str(path.relative_to(ROOT)), 'bytes': before.st_size,
                 'sha256': digest(path), 'storage': 'local_only'}
        if path.is_relative_to(ROOT / 'outputs') and path.suffix in {'.json', '.py', '.md'}:
            target = DEST / path.relative_to(ROOT / 'outputs')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            if digest(target) != entry['sha256']:
                raise RuntimeError(f'Copy changed: {path}')
            entry.update(storage='git_evidence_copy', copy=str(target.relative_to(ROOT)))
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError(f'Artifact changed during export: {path}')
        entries.append(entry)
    manifest = {'schema': 1, 'date': '2026-09-30',
                'scope': 'results NPZ/MJB, docs/evidence MJB, three teacher campaigns',
                'not_a_complete_raw_data_backup': True,
                'followup_original_references': 'teacher_repair_canonical_20260930/{corner,combined_v4}/original',
                'file_count': len(entries), 'total_bytes': sum(e['bytes'] for e in entries),
                'entries': entries}
    (DEST / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'entries'}))


if __name__ == '__main__':
    main()
