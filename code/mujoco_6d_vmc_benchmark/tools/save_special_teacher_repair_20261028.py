"""Save bounded repair evidence, including rejected handoffs and live identity."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now


def save(output):
    if output.exists():
        raise FileExistsError(output)
    base = ROOT/'outputs'
    mappings = {
        'V6_COLLECTION_PLAN.json': 'special_scene_vmc_collection_20261028_v6/COLLECTION_PLAN.json',
        'V6_COLLECTION_PROGRESS.json': 'special_scene_vmc_collection_20261028_v6/COLLECTION_PROGRESS.json',
        'V6_FULL_REVIEW.json': 'special_scene_vmc_collection_20261028_v6/FULL_COLLECTION_REVIEW.json',
        'V6_FAILED_HANDOFF.json': 'special_scene_learning_handoff_20261028_v3/execution.json',
        'V6_HANDOFF_REGISTRATION.json': 'special_scene_learning_handoff_20261028_v3/REGISTRATION.json',
        'UNUSED_STUDENT18_PREPARATION.json': 'special_scene_student_closure_20261028_v1/PREPARATION.json',
        'UNUSED_FROZEN108_PREPARATION.json': 'special_scene_frozen108_repaired_preparation_20261028_v1/REGISTRATION.json',
        'TAIL_REGISTRATION.json': 'special_teacher_tail_repair_20261028_v2/REGISTRATION.json',
        'TAIL_COMPLETE.json': 'special_teacher_tail_repair_20261028_v2/execution.json',
        'TAIL_REVIEW.json': 'special_teacher_midpoint_20261028_v1/PARENT_REVIEW.json',
        'MIDPOINT_REGISTRATION.json': 'special_teacher_midpoint_20261028_v1/REGISTRATION.json',
        'V6_ARCHIVE_LOCAL_RECEIPT.json': 'special_v6_full_archive_20261028_v1/LOCAL_RECEIPT.json',
        'TAIL_ARCHIVE_LOCAL_RECEIPT.json': 'special_teacher_tail_archive_20261028_v1/LOCAL_RECEIPT.json',
    }
    if (base/'special_teacher_midpoint_20261028_v1/REVIEW.json').exists():
        mappings.update({
            'MIDPOINT_COMPLETE.json':'special_teacher_midpoint_20261028_v1/execution.json',
            'MIDPOINT_REVIEW.json':'special_teacher_midpoint_20261028_v1/REVIEW.json',
            'OFFICE_REGISTRATION.json':'special_teacher_midpoint_office_20261028_v1/REGISTRATION.json',
        })
    if (base/'special_recovery_release_20261028_v1/REGISTRATION.json').exists():
        mappings.update({
            'MIDPOINT_OFFICE_COMPLETE.json':'special_teacher_midpoint_office_20261028_v1/execution.json',
            'RELEASE_REGISTRATION.json':'special_recovery_release_20261028_v1/REGISTRATION.json',
            'RELEASE_DIAGNOSIS.json':'special_recovery_release_20261028_v1/DIAGNOSIS.json',
        })
    if (base/'special_recovery_release005_20261029_v1/REGISTRATION.json').exists():
        mappings.update({
            'RELEASE025_COMPLETE.json':'special_recovery_release_20261028_v1/execution.json',
            'RELEASE025_COMPLETE_REVIEW.json':'special_recovery_release005_20261029_v1/PARENT_COMPLETE_REVIEW.json',
            'RELEASE005_REGISTRATION.json':'special_recovery_release005_20261029_v1/REGISTRATION.json',
        })
    output.mkdir(parents=True)
    copied = {}
    for name, relative in mappings.items():
        source, destination = base/relative, output/name
        before = sha(source)
        shutil.copyfile(source, destination)
        assert before == sha(destination) == sha(source)
        copied[name] = dict(source=str(source), sha256=before, bytes=destination.stat().st_size)
    unit = 'sii-special-teacher-midpoint-v1-20261028.service'
    current = 'special_teacher_midpoint_20261028_v1'
    if (base/'special_teacher_midpoint_office_20261028_v1/execution.json').exists():
        unit = 'sii-special-teacher-midpoint-office-v1-20261028.service'
        current = 'special_teacher_midpoint_office_20261028_v1'
    if (base/'special_recovery_release_20261028_v1/execution.json').exists():
        unit = 'sii-special-recovery-release-v1-20261028.service'
        current = 'special_recovery_release_20261028_v1'
    if (base/'special_recovery_release005_20261029_v1/execution.json').exists():
        unit = 'sii-special-recovery-release005-v1-20261029.service'
        current = 'special_recovery_release005_20261029_v1'
    props = subprocess.check_output(['systemctl', '--user', 'show', unit,
        '-p', 'MainPID', '-p', 'ActiveState', '-p', 'MemoryCurrent', '-p', 'MemoryMax',
        '-p', 'MemorySwapMax', '-p', 'ControlGroup', '-p', 'CPUQuotaPerSecUSec'], text=True)
    properties = dict(line.split('=', 1) for line in props.splitlines())
    snapshot = dict(captured_utc=now(), service=unit, properties=properties,
                    execution=read(base/current/'execution.json'))
    if properties['ActiveState'] == 'active':
        pid = int(properties['MainPID'])
        snapshot['parent_proc_stat'] = Path(f'/proc/{pid}/stat').read_text()
        snapshot['children'] = Path(f'/proc/{pid}/task/{pid}/children').read_text()
        cg = Path('/sys/fs/cgroup')/properties['ControlGroup'].lstrip('/')
        snapshot['cgroup'] = {n:(cg/n).read_text() for n in
                              ('memory.events', 'memory.current', 'memory.max', 'memory.swap.current', 'memory.swap.max')}
        assert snapshot['cgroup']['memory.max'].strip() == '3221225472'
        assert snapshot['cgroup']['memory.swap.max'].strip() == '0'
    write(output/'MIDPOINT_SNAPSHOT.json', snapshot)
    journals = {}
    for name in ('sii-special-teacher-tail-repair-v1-20261028.service',
                 'sii-special-preflight-rejection-check-v2-20261028.service'):
        journals[name] = subprocess.check_output(['journalctl', '--user', '-u', name,
                                                   '-n', '70', '--no-pager'], text=True)
    write(output/'INFRASTRUCTURE_AND_NEGATIVE_CHECKS.json', dict(
        recorded_utc=now(), journals=journals,
        tail_v1='Preparation rejected an incorrect assumption that all failed identities were training. A dependent launch was mistakenly issued without checking that failure, then failed before physics because REGISTRATION was absent. v2 explicitly excluded validation from probe cases; the v1 failure is preserved.',
        unused_preparations='Bound to the rejected v6 handoff and nonexistent training output. No18 or repaired108 physics; new successful collection needs new preparation paths.'))
    write(output/'MANIFEST.json', dict(created_utc=now(), copied=copied,
                                      other_files={p.name:sha(p) for p in output.iterdir() if p.name not in copied}))
    print(json.dumps(dict(output=str(output), copied_files=len(copied),
                          snapshot_status=snapshot['execution']['status'],
                          completed=len(snapshot['execution']['episodes']))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    save(args.output.resolve())
