"""Prepare eight controls after a verified terminal or reclaimed original unit.

All are development controls, with no automatic fitting or test replacement.
Original gates and all failed/unfinished receipts are retained.
"""
import argparse
import re
import fcntl
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from collect_special_scene_coverage_20261029 import require_resources


def now():
    return datetime.now(timezone.utc).isoformat()


def process_identity(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    except FileNotFoundError:
        return None


def service_state(name):
    raw = subprocess.check_output(['systemctl', '--user', 'show', name,
        '-p', 'LoadState', '-p', 'ActiveState', '-p', 'Result', '-p', 'MainPID',
        '-p', 'InvocationID', '-p', 'ControlGroup', '-p', 'ExecMainCode', '-p', 'ExecMainStatus'], text=True)
    return dict(line.split('=', 1) for line in raw.splitlines())


def require_finished_service(reg, current, observed_ticks, boot_id, cgroup_exists):
    """Missing units do not prove exit success; require independent science first.

    The caller verifies all 108 terminal results and their independent audit
    before reaching this guard. Reclaimed-route approval only establishes no
    remaining registered process/cgroup; the original exit code is unavailable.
    """
    assert boot_id == reg['prerequisite_boot_id'], 'Boot changed since registration'
    assert re.fullmatch(r'[0-9a-f]{32}', reg['prerequisite_invocation_id'])
    assert reg['prerequisite_cgroup'].endswith('/'+reg['prerequisite_service'])
    assert current['ActiveState'] == 'inactive', 'Original service not inactive'
    assert int(current['MainPID']) == 0, 'Original service still owns a process'
    assert observed_ticks != reg['prerequisite_start_ticks'], 'Original process still exists outside service'
    if current['LoadState'] == 'loaded':
        assert current['InvocationID'] == reg['prerequisite_invocation_id'], 'Different invocation'
        assert current['Result'] == 'success' and current['ExecMainCode'] == '1' and current['ExecMainStatus'] == '0'
        return dict(route='retained_unit_normal_exit', service_exit_zero_verified=True)
    assert current['LoadState'] == 'not-found', 'Unexpected load state'
    assert current['InvocationID'] == '' and current['ControlGroup'] == '', 'Unit identity not reclaimed'
    assert not cgroup_exists, 'Original cgroup still exists'
    return dict(route='reclaimed_unit_complete_science_and_no_original_process_or_cgroup',
                service_exit_zero_verified=False,
                limitation='Not-found defaults are not an exit receipt. Full108 audited artifacts, '
                            'registered boot/PID identity and absent original cgroup establish handoff eligibility.')


def prepare(root):
    assert not root.exists()
    collection = ROOT/'outputs/special_scene_vmc_collection_20261029_v8'
    plan = read(collection/'COLLECTION_PLAN.json')
    original = next(e for e in plan['episodes'] if e['id']=='ball_00')
    assert original['split']=='train'
    cases=[]
    for axis in ('x','y'):
        for sign in (-1,1):
            for angle in (-.8,.8):
                parameters=dict(original['scene_parameters'])
                parameters.update(VMC_COVERAGE_INITIAL_X_M=sign*.05 if axis=='x' else 0.,
                    VMC_COVERAGE_INITIAL_Y_M=sign*.05 if axis=='y' else 0.,
                    VMC_COVERAGE_INITIAL_Z_M=-.06,
                    VMC_COVERAGE_CARRY_X_M=-sign*.085 if axis=='x' else 0.,
                    VMC_COVERAGE_CARRY_Y_M=-sign*.085 if axis=='y' else 0.,
                    VMC_BALL_ANGLE_RAD=angle,VMC_BALL_EVENT_STAGE='approach')
                cases.append(dict(id=f'ball_{axis}_{sign:+d}_angle_{angle:+.1f}',
                    scene='ball',seed=original['seed'],split='development_control',parameters=parameters))
    names=('run_video_reference_coverage_20261029.py','run_video_reference_vmc_20261028.py',
           'optimize_tool_contact_20261002.py','intent_recovery_teacher_20261029.py',
           'intent_equilibrium_teacher_20261029.py','collect_special_scene_actions_20261028.py',
           'audit_video_reference_vmc_20261028.py','qualify_special_scene_demo_20261028.py',
           'qualify_ball_coverage_demo_20261029.py','collect_special_scene_coverage_20261029.py',Path(__file__).name)
    files=list((ROOT/'scripts').glob('*.py'))+[ROOT/'tools'/n for n in names]
    service_name = 'sii-special-frozen108-v8-20261029.service'
    current = service_state(service_name)
    pid = int(current['MainPID']); ticks = process_identity(pid)
    assert current['LoadState'] == 'loaded' and current['ActiveState'] == 'active' and ticks is not None
    cmd = [s.decode() for s in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0') if s]
    assert re.fullmatch(r'[0-9a-f]{32}', current['InvocationID'])
    assert current['ControlGroup'].endswith('/'+service_name)
    assert Path('/sys/fs/cgroup'+current['ControlGroup']).is_dir()
    assert '--root' in cmd and '--run' in cmd
    assert any(Path(s).name == 'prepare_special_frozen_test_20261028.py' for s in cmd)
    parent_root = Path(cmd[cmd.index('--root')+1])
    if not parent_root.is_absolute():
        parent_root = Path(f'/proc/{pid}/cwd').resolve()/parent_root
    prerequisite_preparation = ROOT/'outputs/special_scene_frozen108_preparation_20261029_v8'
    assert parent_root.resolve() == prerequisite_preparation
    registration=dict(schema='sii-ball-coverage-development-eight-v3',registered_utc=now(),
        maximum_episodes=8,cases=cases,teacher_config=plan['teacher_config'],
        teacher_sha256=sha(Path(plan['teacher_config'])),parent_collection_plan_sha256=sha(collection/'COLLECTION_PLAN.json'),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
        prerequisite_matrix=str(ROOT/'outputs/special_scene_frozen108_20261029_v8'),
        prerequisite_service=service_name, prerequisite_pid=pid, prerequisite_start_ticks=ticks,
        prerequisite_boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        prerequisite_invocation_id=current['InvocationID'], prerequisite_cgroup=current['ControlGroup'],
        service_handoff='Full108 independent audit first; then same-boot original PID gone and either '
                        'retained exact invocation exited zero or reclaimed unit with original cgroup absent. '
                        'Reclaimed route does not certify the original process exit code.',
        prerequisite_preparation=str(prerequisite_preparation),
        prerequisite_preparation_sha256=sha(prerequisite_preparation/'REGISTRATION.json'),
        prerequisite_audit='FROZEN108_AUDIT.json',
        resources=dict(simulators=1,threads=1,cpu_limit_cores=1,
                       cpu_enforcement='cgroup quota <=1 CPU or inherited single-CPU affinity',
                       memory_max_bytes=3221225472,swap_bytes=0),
        interpretation='Eight fixed physical development controls inside the actual free-ball scene. '
        'Four cardinal approach/carry directions and two bounded impact angles. No test trajectories/labels, '
        'no validation identities, no fitting, no actor-input/gate/filter/actuator/dt change. '
        'Initial IK and ball angle may change resulting physical trajectories; passing is not assumed. '
        'Review all eight including failures before proposing a shared training dataset; rod/corner remain mandatory.')
    root.mkdir(parents=True);write(root/'REGISTRATION.json',registration)
    print(json.dumps(dict(root=str(root),episodes=8,status='prepared_not_started',sha256=sha(root/'REGISTRATION.json'))))


def run(root):
    lock=(root/'.probe.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    reg=read(root/'REGISTRATION.json')
    assert reg['schema'] == 'sii-ball-coverage-development-eight-v3', 'Use the service-bound preparation'
    assert not (root/'execution.json').exists(), 'No automatic replay'
    matrix=Path(reg['prerequisite_matrix'])
    state=read(matrix/'execution.json')
    assert state['status']=='complete' and state['completed']==108, 'Original108 must finish first'
    audit=read(matrix/reg['prerequisite_audit'])
    assert audit['status']=='frozen108_saved_evidence_audit_passed' and audit['verified_episodes']==108
    assert audit['report_sha256']==sha(matrix/'REPORT.json')
    parent = Path(reg['prerequisite_preparation'])
    assert sha(parent/'REGISTRATION.json') == reg['prerequisite_preparation_sha256']
    assert Path(audit['preparation']) == parent
    assert audit['model_lock_sha256'] == sha(matrix/'INPUT_MODEL_LOCK.json')
    terminal_service = service_state(reg['prerequisite_service'])
    handoff = require_finished_service(reg, terminal_service,
        process_identity(reg['prerequisite_pid']),
        Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        Path('/sys/fs/cgroup'+reg['prerequisite_cgroup']).exists())
    resources = require_resources()
    for n,h in reg['source_sha256'].items(): assert sha(ROOT/n)==h,n
    assert sha(Path(reg['teacher_config']))==reg['teacher_sha256']
    execution=dict(status='running',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),
                   actual_resources=resources, prerequisite_service_snapshot=terminal_service,
                   prerequisite_handoff=handoff, episodes=[])
    write(root/'execution.json',execution)
    try:
        for case in reg['cases']:
            for n,h in reg['source_sha256'].items(): assert sha(ROOT/n)==h,n
            env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','USER','LANG','LD_LIBRARY_PATH','TMPDIR')}
            env.update({k:str(v) for k,v in case['parameters'].items()})
            env.update(VMC_TEACHER_CONFIG=reg['teacher_config'],VMC_SCENE_SEED=str(case['seed']),MUJOCO_GL='egl',
                PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
                OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
            out=root/case['id']
            execution.update(current=case['id'],updated_utc=now());write(root/'execution.json',execution)
            with (root/(case['id']+'.log')).open('x') as log:
                subprocess.run([sys.executable,str(ROOT/'tools/run_video_reference_coverage_20261029.py'),
                    '--output',str(out),'--scenes','ball'],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            for name in ('audit_video_reference_vmc_20261028.py','qualify_ball_coverage_demo_20261029.py'):
                with (out/(name+'.log')).open('x') as log:
                    subprocess.run([sys.executable,str(ROOT/'tools'/name),str(out/'ball')],env=env,cwd=ROOT,
                        stdout=log,stderr=subprocess.STDOUT,check=True)
            q=out/'ball/DEMONSTRATION_QUALIFICATION.json'
            execution['episodes'].append(dict(id=case['id'],qualification=read(q),qualification_sha256=sha(q)))
            write(root/'execution.json',execution)
        execution.update(status='complete_pending_review',ended_utc=now())
    except BaseException as e:
        execution.update(status='failed_preserved',error=repr(e),ended_utc=now())
        raise
    finally:
        write(root/'execution.json',execution)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args();(run if args.run else prepare)(args.root.resolve())
