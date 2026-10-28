"""Copy frozen SAC source bytes and explicitly add reviewed no-physics replay tools."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ADDITIONS = (
    'scripts/canonical48_paired_deployment_20260924.py',
    'scripts/canonical48_sac_deployment_20260925.py',
    'scripts/run_panel_sac_deployment_20260925.py',
    'tools/audit_paired_deployment_replay_20260924.py',
    'tools/audit_sac_deployment_replay_20260925.py',
    'tools/audit_sac_zero_replay_20260925.py',
    'docs/CANONICAL48_SAC_DEPLOYMENT_PROTOCOL_20260925.md',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.training_root.resolve() / 'source'
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Fresh replay snapshot required')
    build = json.loads((args.training_root / 'BUILD.json').read_text())
    actual = {str(path.relative_to(source)): sha(path) for path in source.rglob('*')
              if path.is_file() and '__pycache__' not in path.parts}
    if actual != build['source_sha256'] or len(actual) != 201:
        raise ValueError('Original frozen SAC201 bytes changed')
    files = {name: source / name for name in actual}
    for name in ADDITIONS:
        if name in files and sha(ROOT / name) != actual[name]:
            raise ValueError('Cannot overwrite existing source: ' + name)
        files[name] = ROOT / name
    if any(path.is_symlink() for path in files.values()):
        raise ValueError('Source symlinks not allowed')
    output.mkdir(parents=True, exist_ok=False)
    destination = output / 'source'
    for name, path in sorted(files.items()):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        if sha(path) != sha(target):
            raise ValueError('Copy drift')
        if name.endswith('.py'):
            compile(target.read_bytes(), str(target), 'exec')
    record = dict(simulator_steps=0, gradient_updates=0, builder_sha256=sha(__file__),
                  training_build_sha256=sha(args.training_root / 'BUILD.json'), preserved_training_files=201,
                  source_sha256={name: sha(destination / name) for name in files},
                  additions={name: sha(destination / name) for name in ADDITIONS})
    with (output / 'BUILD.json').open('x') as stream:
        json.dump(record, stream, indent=2)
    for path in sorted(destination.rglob('*'), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    destination.chmod(0o555)
    print(json.dumps(dict(files=len(files), build_sha256=sha(output / 'BUILD.json'), simulator_steps=0)))


if __name__ == '__main__':
    main()
