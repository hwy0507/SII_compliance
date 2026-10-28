"""Freeze SAC201 unchanged plus explicitly reviewed deployment additions; no physics."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ADDITIONS = (
    'scripts/canonical48_vmc_tuning_20260924.py',
    'scripts/canonical48_sac_deployment_20260925.py',
    'scripts/run_panel_sac_deployment_20260925.py',
    'scripts/run_panel_zero_20260924.py',
    'scripts/canonical48_paired_deployment_20260924.py',
    'scripts/run_panel_paired_deployment_20260924.py',
    'tools/prepare_sac_deployment_20260925.py',
    'tools/run_sac_deployment_20260925.py',
    'tools/report_sac_deployment_20260925.py',
    'tools/prepare_paired_multiseed_deployment_20260925.py',
    'tools/prepare_paired_six_fixture_deployment_20260924.py',
    'tools/run_paired_six_fixture_deployment_20260924.py',
    'tools/report_paired_six_fixture_20260924.py',
    'tools/run_paired_multiseed_deployment_20260925.py',
    'tools/audit_sac_startup_pair_20260925.py',
    'tools/audit_sac_deployment_replay_20260925.py',
    'tools/audit_paired_deployment_replay_20260924.py',
    'tools/audit_sac_zero_replay_20260925.py',
    'tools/audit_canonical48_sac_final_20260925.py',
    'tools/audit_paired_transitions_20260924.py',
    'tools/prepare_sac_deployment_snapshot_20260925.py',
    'docs/CANONICAL48_SAC_DEPLOYMENT_PROTOCOL_20260925.md',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build(training_root, output, check_only=False):
    source = training_root / 'source'
    require(not output.exists(), 'Fresh independent deployment snapshot required')
    build_path = training_root / 'BUILD.json'
    original_build = json.loads(build_path.read_text())
    files = {str(path.relative_to(source)): path for path in source.rglob('*')
             if path.is_file() and '__pycache__' not in path.parts}
    original_hashes = {name: sha(path) for name, path in files.items()}
    require(len(files) == 201 and original_hashes == original_build['source_sha256'], 'Original SAC201 source drift')
    require(all(not (path.stat().st_mode & 0o222) for path in files.values()), 'Original SAC source must remain readonly')
    training_hashes = {}
    for branch in ('online_only', 'demo_prefill'):
        directory = training_root / 'training' / branch
        require(not (directory / 'FAILED.json').exists(), 'Failed SAC training cannot deploy')
        manifest = json.loads((directory / 'manifest.json').read_text())
        complete = json.loads((directory / 'COMPLETE.json').read_text())
        require(complete['status'] == 'complete' and manifest['branch'] == complete['branch'] == branch, 'Incomplete/wrong branch')
        require(manifest['algorithm'] == 'standard SAC' and manifest['training']['seed'] == 20260923,
                'Wrong SAC identity')
        require(complete['training_steps'] == 8192 and complete['updates'] == 8092, 'Wrong completed SAC budget')
        require(all(original_hashes.get(name) == value for name, value in manifest['source_hashes'].items()),
                'Training manifest not bound to preserved source')
        for name, key in (('sac_final.zip', 'checkpoint_sha256'), ('vecnormalize_train_only.pkl', 'normalizer_sha256')):
            require(sha(directory / name) == complete[key], 'Final artifact drift')
        training_hashes[branch] = {name: sha(directory / name) for name in
                                   ('manifest.json', 'COMPLETE.json', 'sac_final.zip', 'vecnormalize_train_only.pkl')}
    additions = {}
    for name in ADDITIONS:
        candidate = ROOT / name
        require(candidate.is_file() and not candidate.is_symlink(), 'Missing/symlink reviewed addition: ' + name)
        digest = sha(candidate)
        require(name not in original_hashes or original_hashes[name] == digest, 'Addition would replace original SAC source: ' + name)
        files[name] = candidate
        additions[name] = digest
    require(not any(path.is_symlink() for path in files.values()), 'Source symlinks forbidden')
    # Static closure: every import that resolves to a workspace-local tool/script
    # must exist in the assembled snapshot. Do not import or execute target code.
    workspace_modules = {path.stem: str(path.relative_to(ROOT)) for directory in ('scripts', 'tools')
                         for path in (ROOT / directory).glob('*.py')}
    closure = {}
    for name in ADDITIONS:
        if not name.endswith('.py'):
            continue
        tree = ast.parse(files[name].read_bytes(), filename=name)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.add(node.module.split('.')[0])
        local = sorted(workspace_modules[module] for module in imports if module in workspace_modules)
        require(all(path in files for path in local), 'Missing declared import dependency for ' + name + ': ' + repr(local))
        closure[name] = local
    for name, path in files.items():
        if name.endswith('.py'):
            compile(path.read_bytes(), name, 'exec')
    record = dict(simulator_steps=0, gradient_updates=0, builder_sha256=sha(__file__),
                  original_training_root=str(training_root), training_build_sha256=sha(build_path),
                  original_training_file_count=201, training_artifact_sha256=training_hashes,
                  source_sha256={name: sha(path) for name, path in sorted(files.items())}, additions=additions,
                  reviewed_local_import_closure=closure, original_source_unchanged=True,
                  protocol_sha256=additions['docs/CANONICAL48_SAC_DEPLOYMENT_PROTOCOL_20260925.md'])
    if check_only:
        return dict(passed=True, files=len(files), additions=len(additions), original_training_file_count=201,
                    simulator_steps=0, gradient_updates=0, wrote_files=False)
    output.mkdir(parents=True, exist_ok=False)
    destination = output / 'source'
    for name, path in sorted(files.items()):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        require(sha(target) == record['source_sha256'][name], 'Copied bytes changed: ' + name)
    with (output / 'BUILD.json').open('x') as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
    for path in sorted(destination.rglob('*'), reverse=True):
        path.chmod(0o555 if path.is_dir() else 0o444)
    destination.chmod(0o555)
    return dict(passed=True, files=len(files), build_sha256=sha(output / 'BUILD.json'), simulator_steps=0, gradient_updates=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--training-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(build(args.training_root.resolve(), args.output.resolve(), args.check_only)))


if __name__ == '__main__':
    main()
