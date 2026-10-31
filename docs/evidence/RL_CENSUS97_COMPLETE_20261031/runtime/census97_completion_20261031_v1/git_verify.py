"""Verify only this handoff's explicit Git paths and archive manifest."""
from pathlib import Path
import subprocess, json, hashlib, tarfile, argparse, time

D = Path(__file__).resolve().parent
B = D.parents[1]
R = B / 'repository/SII_compliance'
TAG = 'RL_CENSUS97_COMPLETE_20261031'
E = R / 'docs/evidence' / TAG
A = B / 'repository' / TAG
parser = argparse.ArgumentParser()
parser.add_argument('--committed', action='store_true')
args = parser.parse_args()
git = lambda *a: subprocess.check_output(['git', *a], cwd=R)
digest = lambda data: hashlib.sha256(data).hexdigest()
receipt = json.loads((A / 'RECEIPT.json').read_text())
manifest = json.loads((E / 'MANIFEST.json').read_text())['files']
paths = [str((E / x['relative']).relative_to(R)) for x in manifest]
paths += [str((E / 'MANIFEST.json').relative_to(R)), 'AGENTS.md', 'HANDOFF.md', 'UPDATE_LOG.md',
          'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md', 'docs/' + TAG + '.md', 'docs/' + TAG + '_SAVE.json']
if not args.committed:
    assert set(paths) == set(git('diff', '--cached', '--name-only').decode().splitlines())
archive = Path(receipt['archive'])
assert digest(archive.read_bytes()) == receipt['sha256']
with tarfile.open(archive) as t:
    assert len(t.getmembers()) == receipt['members']
    for entry in t.getmembers():
        assert t.extractfile(entry).read() == (E / entry.name).read_bytes()
for row in manifest:
    data = (E / row['relative']).read_bytes()
    assert len(data) == row['bytes'] and digest(data) == row['sha256']
checked = []
for name in paths:
    data = (R / name).read_bytes()
    assert data == git('show', ':' + name)
    if args.committed:
        assert data == git('show', 'HEAD:' + name)
    checked.append(dict(path=name, bytes=len(data), sha256=digest(data)))
result = dict(passed=True, time=time.time(), commit=git('rev-parse', 'HEAD').decode().strip(),
              committed=args.committed, files=checked, archive_sha256=receipt['sha256'])
if args.committed:
    with (A / 'GIT_BYTES_REVIEW.json').open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
print(json.dumps(dict(passed=True, committed=args.committed, files=len(paths))))
