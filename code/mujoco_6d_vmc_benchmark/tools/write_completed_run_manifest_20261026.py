"""SHA256 manifest of a terminal run for independent shared-archive checking."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, required=True)
a = p.parse_args()
root = a.root.resolve()
assert json.loads((root/'execution.json').read_text())['status'] == 'complete'
manifest = root/'SHA256SUMS'
assert not manifest.exists(), 'Do not replace an existing archive manifest'
lines = []
for f in sorted(root.rglob('*')):
    if not f.is_file() or '__pycache__' in f.parts:
        continue
    name = f.relative_to(root).as_posix()
    assert '\n' not in name and '\\' not in name
    h = hashlib.sha256()
    with f.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    lines.append(h.hexdigest()+'  '+name+'\n')
manifest.write_text(''.join(lines))
print(json.dumps({'files': len(lines), 'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest()}))
