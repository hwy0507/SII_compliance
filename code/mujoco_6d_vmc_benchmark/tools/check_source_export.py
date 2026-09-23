"""Check server provenance and Python syntax without importing simulation code."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'docs/server_source_20260923.json').read_text())
    problems = []
    for relative, info in manifest['files'].items():
        path = ROOT / relative
        if not path.is_file():
            problems.append(f'missing: {relative}')
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != info['sha256']:
            problems.append(f'differs from captured server source: {relative}')
        try:
            ast.parse(raw, filename=relative)
        except SyntaxError as error:
            problems.append(str(error))
    if problems:
        raise SystemExit('\n'.join(problems))
    print(f"Verified {len(manifest['files'])} captured server files and their Python syntax")


if __name__ == '__main__':
    main()
