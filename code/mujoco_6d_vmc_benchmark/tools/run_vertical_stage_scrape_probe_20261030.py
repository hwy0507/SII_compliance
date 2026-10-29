"""Run one registered physical probe with contact-before-progress recovery."""
import argparse
import tarfile
from pathlib import Path

import run_vertical_aware_cross_track_probe_20261030 as probe
from collect_special_scene_actions_20261028 import read, sha, write
from vertical_stage_scrape_teacher_20261030 import VerticalStageScrapeTeacher


def run(output, scene, student_steps=0):
    probe.VerticalAwareCrossTrackTeacher = VerticalStageScrapeTeacher
    probe.worker(output, student_steps, scene)
    folder = output / scene
    members = [Path(__file__), Path(__file__).with_name('vertical_stage_scrape_teacher_20261030.py'),
               Path(__file__).with_name('audit_vertical_stage_scrape_probe_20261030.py')]
    archive = folder / 'teacher_extension_source.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for member in members:
            tar.add(member, arcname=member.name)
    receipt = read(folder / 'HANDOFF_EXECUTION.json')
    receipt['input_hashes']['teacher_extension_source.tar.gz'] = sha(archive)
    receipt['teacher_extension'] = [dict(name=p.name, sha256=sha(p)) for p in members]
    write(folder / 'HANDOFF_EXECUTION.json', receipt)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--scene', choices=('rod', 'ball', 'corner'), required=True)
    p.add_argument('--student-steps', type=int, default=0)
    a = p.parse_args()
    run(a.output.resolve(), a.scene, a.student_steps)
