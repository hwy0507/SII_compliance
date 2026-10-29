"""Independent replay review for the vertical-stage progress teacher."""
import hashlib
import tarfile
from pathlib import Path

import numpy as np
import audit_vertical_aware_cross_track_probe_20261030 as base
from collect_special_scene_actions_20261028 import read, sha, write
from vertical_stage_progress_teacher_20261030 import VerticalStageProgressTeacher

base.make_teacher = VerticalStageProgressTeacher


def expected(config, checkpoint, observations, prefix):
    teacher = VerticalStageProgressTeacher(config); teacher.reset()
    from current_student_policy_20260921 import load_current
    student = load_current(checkpoint); student.reset()
    teachers, students = [], []
    for obs in observations:
        teacher.observe(obs.copy())
        teachers.append(teacher.act(obs[39:45].copy(), .04))
        students.append(student.act(obs.copy()))
    t, s = np.asarray(teachers), np.asarray(students)
    mask = np.arange(len(observations)) >= prefix
    return t, s, np.where(mask[:, None], t, s), mask


base.expected = expected


def audit(folder):
    folder = Path(folder)
    receipt = read(folder / 'HANDOFF_EXECUTION.json')
    source_archive = folder / 'teacher_extension_source.tar.gz'
    with tarfile.open(folder / 'teacher_extension_source.tar.gz') as archive:
        for member in archive.getmembers():
            payload = archive.extractfile(member).read()
            assert hashlib.sha256(payload).hexdigest() == receipt['sources']['tools/' + member.name]
    original_qualify = base.qualify
    def qualify_with_extension_receipt(path):
        independent = read(path / 'INDEPENDENT_AUDIT.json')
        independent.update(progress_teacher_sha256=sha(Path(__file__).with_name('vertical_stage_progress_teacher_20261030.py')),
            progress_auditor_sha256=sha(Path(__file__)),
            progress_source_archive_sha256=sha(source_archive))
        independent['input_hashes']['teacher_extension_source.tar.gz'] = sha(source_archive)
        write(path / 'INDEPENDENT_AUDIT.json', independent)
        return original_qualify(path)
    base.qualify = qualify_with_extension_receipt
    try:
        result = base.audit(folder)
    finally:
        base.qualify = original_qualify
    independent = read(folder / 'INDEPENDENT_AUDIT.json')
    result.update(progress_teacher_sha256=independent['progress_teacher_sha256'],
        progress_auditor_sha256=independent['progress_auditor_sha256'],
        progress_source_archive_sha256=independent['progress_source_archive_sha256'],
        qualification_sha256=sha(folder / 'DEMONSTRATION_QUALIFICATION.json'),
        handoff_execution_sha256=sha(folder / 'HANDOFF_EXECUTION.json'),
        independent_audit_sha256=sha(folder / 'INDEPENDENT_AUDIT.json'))
    write(folder / 'HANDOFF_REVIEW.json', result)
    return result


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('folder', type=Path)
    print(audit(p.parse_args().folder.resolve()))
