"""Run one unchanged scene worker in-process with the wide-model loader."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
import current_student_policy_20260921 as legacy_policy
from current_student_policy_mlp384_20261031 import load_current

legacy_policy.load_current = load_current
namespace = runpy.run_path(str(ROOT/'tools/run_video_reference_coverage_20261029.py'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenes', nargs='+', choices=('corner', 'rod', 'ball'), required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cg/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3*1024**3
    assert (cg/'memory.swap.max').read_text().strip() == '0'
    assert os.sched_getaffinity(0) == {6}
    out.mkdir(parents=True, exist_ok=False)
    lock = (ROOT/'outputs/.local-rl-compute.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    rows = []
    for scene in args.scenes:
        namespace['worker'](out, scene)
        rows.append(dict(scene=scene, returncode=0))
    (out/'execution.json').write_text(json.dumps(dict(status='complete', rows=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
