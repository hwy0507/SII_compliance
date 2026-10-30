"""Use the v7 lock and the repository-pinned MuJoCo runtime for fixed27."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'experiments'))
import diagnose_contact_yield_recovery_v7_students_20261030 as v1

TARGET = ROOT/'outputs/contact_yield_recovery_student_development_20261030_v7'
v1.TARGET = TARGET
v1.diagnosis.TARGET = TARGET

from collect_special_scene_actions_20261028 import read, sha, write


def check(reg):
    v1.check(reg)
    relative = str(Path(__file__).relative_to(ROOT))
    assert reg['source_sha256'][relative] == sha(Path(__file__))
    assert reg['python'] == sys.executable
    assert reg['runtime_versions']['mujoco'] == '3.11.0'


def prepare(root):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    v1.prepare(root)
    path = root/'REGISTRATION.json'
    reg = read(path)
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    write(path, reg)
    check(reg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run', 'review'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.mode == 'prepare':
        prepare(root)
    elif args.mode == 'run':
        check(read(root/'REGISTRATION.json'))
        v1.diagnosis.run(root)
    else:
        assert args.output is not None
        check(read(root/'REGISTRATION.json'))
        v1.diagnosis.review(root, args.output.resolve())


if __name__ == '__main__':
    main()
