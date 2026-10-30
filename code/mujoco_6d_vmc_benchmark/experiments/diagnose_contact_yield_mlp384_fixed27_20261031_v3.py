"""Fixed27 run using an in-process versioned worker shim for wide checkpoints."""
import argparse
from pathlib import Path

import diagnose_contact_yield_mlp384_fixed27_20261031_v2 as v2

ROOT = v2.ROOT
TARGET = ROOT/'outputs/contact_yield_mlp384_fixed27_20261031_v3'
PRIOR = ROOT/'outputs/contact_yield_mlp384_fixed27_20261031_v2'
V2_CHECK = v2.check

v2.TARGET = TARGET
v2.PRIOR = PRIOR
v2.RUNNER = ROOT/'tools/run_video_reference_coverage_mlp384_20261031_v3.py'
v2.v1.TARGET = TARGET


def check(reg):
    assert reg['schema'] == 'sii-contact-yield-mlp384-fixed27-diagnosis-v3'
    compatible = dict(reg)
    compatible['schema'] = 'sii-contact-yield-mlp384-fixed27-diagnosis-v2'
    V2_CHECK(compatible)
    source = str(Path(__file__).relative_to(ROOT))
    assert reg['source_sha256'][source] == v2.v1.sha(Path(__file__))


def prepare(root):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    v2.check = V2_CHECK
    v2.prepare(root)
    path = root/'REGISTRATION.json'
    reg = v2.v1.read(path)
    reg['schema'] = 'sii-contact-yield-mlp384-fixed27-diagnosis-v3'
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = v2.v1.sha(Path(__file__))
    v2.v1.write(path, reg)
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
        v2.v1.diagnosis.check = check
        v2.v1.diagnosis.run(root)
    else:
        assert args.output is not None
        v2.v1.diagnosis.check = check
        v2.v1.diagnosis.review(root, args.output.resolve())


if __name__ == '__main__':
    main()
