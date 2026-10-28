"""Three predeclared3s numerical probes of known train_000, not task evaluations.

Only the diagnostic timestep changes. Formal comparison stays5e-5. This finite
coordinator waits for the unleased predecessor and holds one of four shared
leases; no recurring automation, model selection, retries or heldout access.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
import mujoco
import paper_office_worker_20261002 as office
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from research72_slots_20261003 import simulation_slot
from run_all_methods_formal_20261003 import V6, MENAGERIE
from run_paper_final_validation_20261003 import ENV

DTS = (.0001, .00005, .000025)
HORIZON = 3.


def read(path):
    return json.loads(path.read_text())


def model_digest(model):
    buffer = np.empty(mujoco.mj_sizeModel(model), np.uint8)
    mujoco.mj_saveModel(model, None, buffer)
    return hashlib.sha256(buffer.tobytes()).hexdigest()


def derive_timestep(model_path, dt):
    assert dt in DTS
    original = sha(model_path)
    model = mujoco.MjModel.from_binary_path(str(model_path))
    before = float(model.opt.timestep)
    assert model_digest(model) == original
    model.opt.timestep = dt
    changed = model_digest(model)
    model.opt.timestep = before
    assert model_digest(model) == original, 'Changing and restoring dt must preserve every byte'
    return changed, dict(original_model_sha256=original, original_dt_s=before,
        diagnostic_model_sha256=changed, diagnostic_dt_s=dt, restored_bytes_exact=True,
        changed_model_fields=['opt.timestep'])


def known_condition(root):
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    protocol = read(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']
    condition = next(c for c in read(root/'CONDITIONS.json')['conditions'] if c['id'] == 'train_000')
    assert condition['role'] == 'train'
    assert sha(root/'teacher.json') == protocol['teacher_config_sha256']
    return protocol, condition


def worker(root, out, dt):
    assert os.environ.get('SII_R72_SIMULATION_LEASE') == '1'
    owner = os.environ.get('SII_R72_LEASE_OWNER_PID', '')
    assert owner.isdigit() and Path('/proc', owner).exists(), 'Numerical worker requires a live shared lease owner'
    protocol, condition = known_condition(root)
    original = office.evaluation_settings
    def settings(v6, requested_dt, condition_file=None, condition_id=None):
        assert requested_dt == dt and condition_file is None and condition_id is None
        formal, overrides, provenance = original(v6, .00005)
        assert formal == protocol['formal_model_sha256']
        expected, derivation = derive_timestep(v6/'construction/rollout.mjb', dt)
        overrides.update(condition['overrides'])
        overrides.update(dt=dt, physics_probe_s=HORIZON)
        provenance.update(physics_dt_s=dt, physics_tier='numerical_diagnostic_only',
            numerical_probe_horizon_s=HORIZON, condition_id='train_000', data_role='numerical_diagnostic',
            public_condition=condition, numerical_model_derivation=derivation,
            diagnostic_wrapper_sha256=sha(Path(__file__)), protocol_sha256=sha(root/'PROTOCOL.json'),
            use='Not training data, not a task trial, not a method selection or final result')
        return expected, overrides, provenance
    office.evaluation_settings = settings
    sys.argv = [sys.argv[0], '--v6-input', str(V6), '--physics-dt', str(dt),
        '--reference', str(V6/'esn_original_v2/rollout.json'), '--config', str(root/'teacher.json'),
        '--output', str(out), '--contact-audit']
    try:
        office.main()
    finally:
        if out.exists():
            write(out/'NUMERICAL_ROLE.json', dict(condition_id='train_000', data_role='numerical_diagnostic',
                protocol_sha256=sha(root/'PROTOCOL.json'), diagnostic_dt_s=dt, horizon_s=HORIZON,
                source_sha256=sha(Path(__file__)), training_label_eligible=False, final_result_eligible=False))


def metrics(run):
    audit, summary = read(run/'AUDIT.json'), read(run/'rollout.json')
    assert read(run/'execution.json')['status'] == 'complete'
    assert not audit['full_horizon'] and not audit['task_success'] and not audit['strict_success']
    assert summary['purpose'] == 'short_horizon_physics_probe_not_task_evaluation'
    assert audit['action_replay_max_abs'] == 0 and audit['common_filter_replay_max_abs'] == 0
    with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
        times, dt = z['time'].copy(), z['dt'].copy()
    channels = read(run/'research_channels.json')
    assert sha(run/'research_substeps.npz') == channels['telemetry_sha256']
    with np.load(run/'research_substeps.npz') as z:
        force = z['contact_force_sum'][:, 1].astype(float)
    assert len(force) == len(times) == len(dt)
    mask = (times >= 2.) & (times <= HORIZON+1e-8)
    contact = mask & (force > 1e-9)
    return dict(run=str(run), dt_s=float(np.median(dt)), physical_seconds=float(dt.sum()),
        aborted=summary['abort_reason'], ball_exposed=bool(contact.any()),
        ball_peak_force_n=float(force[mask].max(initial=0)),
        ball_force_norm_integral_ns=float(np.sum(force[mask]*dt[mask])),
        ball_contact_duration_ms=float(dt[contact].sum()*1000),
        ball_first_contact_s=float(times[contact][0]) if contact.any() else None,
        external_penetration_mm=audit['penetration_mm'], peak_torque_nm=audit['peak_torque_nm'],
        peak_speed_mps=audit['peak_speed_mps'], model_sha256=audit['model_sha256'],
        trace_sha256=audit['trace_sha256'], audit_sha256=sha(run/'AUDIT.json'),
        contacts_sha256=channels['telemetry_sha256'], physical_metrics_sha256=audit['metrics_sha256'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--predecessor', type=Path)
    p.add_argument('--worker-dt', type=float, choices=DTS)
    a = p.parse_args(); root, out = a.root.resolve(), a.output.resolve()
    if a.worker_dt is not None:
        worker(root, out, a.worker_dt); return
    assert a.predecessor is not None
    protocol, condition = known_condition(root)
    deadline = datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    out.mkdir(parents=True, exist_ok=False)
    specification = dict(registered_utc=now(), protocol_sha256=sha(root/'PROTOCOL.json'),
        source_sha256=sha(Path(__file__)), known_public_condition=condition, teacher_config_sha256=sha(root/'teacher.json'),
        timesteps_s=list(DTS), horizon_each_s=HORIZON, maximum_new_physics_episodes=3,
        maximum_total_simulated_seconds=9., maximum_substeps=210000,
        scope='Numerical diagnostic only, same original teacher and public train_000. No candidate fit or ranking.',
        predecessor=str(a.predecessor.resolve()), deadline_utc=deadline.isoformat(),
        resources='After all unleased work: one shared lease,1thread,3GiB; no existing process is restarted.',
        formal_comparison_unchanged=True, sealed_conditions_read=False)
    write(out/'SPECIFICATION.json', specification)
    state = dict(status='waiting_for_predecessor', started_utc=now(), rows=[],
        specification_sha256=sha(out/'SPECIFICATION.json'))
    write(out/'execution.json', state)
    queue = None; queue_state = None
    try:
        while True:
            previous = read(a.predecessor/'execution.json')['status']
            if previous == 'complete': break
            assert previous.startswith('running_') or previous == 'waiting_for_controller_screen'
            assert datetime.now(timezone.utc) < deadline
            time.sleep(30)
        known_condition(root)
        queue = out/'queue_0'; queue.mkdir()
        source = queue/'source'
        for folder in ('scripts', 'tools', 'assets'):
            shutil.copytree(ROOT/folder, source/folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs'))
        write(out/'SOURCE_HASHES.json', {str(f.relative_to(source)): sha(f) for f in source.rglob('*') if f.is_file()})
        queue_state = dict(status='waiting_for_lease', rows=[])
        state['status'] = 'waiting_for_lease'; write(out/'execution.json', state)
        with simulation_slot(root, deadline) as lease:
            state.update(status='running', lease=lease); write(out/'execution.json', state)
            queue_state.update(status='running', lease=lease)
            for dt in DTS:
                assert datetime.now(timezone.utc) < deadline
                name = f'dt_{round(dt*1e6):03d}us'; run = queue/name
                command = [sys.executable, str(source/'tools'/Path(__file__).name),
                    '--root', str(root), '--output', str(run), '--worker-dt', str(dt)]
                row = dict(name=name, condition_id='train_000', category='numerical_teacher_probe',
                    role='numerical_diagnostic', command=command, started_utc=now())
                queue_state['rows'].append(row); write(queue/'execution.json', queue_state)
                env = {**os.environ, **ENV, 'MUJOCO_MENAGERIE_PATH': str(MENAGERIE),
                    'SII_SOURCE_BASE_COMMIT': os.environ['SII_SOURCE_BASE_COMMIT']}
                with (queue/(name+'.log')).open('x') as log:
                    row['returncode'] = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
                row['ended_utc'] = now(); write(queue/'execution.json', queue_state)
                assert row['returncode'] == 0, 'Failed diagnostic retained, no automatic retry'
                row.update(audit_sha256=sha(run/'AUDIT.json'), trace_sha256=sha(run/'rollout.npz'))
                state['rows'].append(metrics(run)); write(out/'execution.json', state)
                write(queue/'execution.json', queue_state)
            queue_state['status'] = 'complete'; write(queue/'execution.json', queue_state)
        reference = root/'teacher_bank/queue_0/train_000/rollout.npz'
        common = queue/'dt_050us/rollout.npz'
        with np.load(reference) as full, np.load(common) as probe:
            for key in ('time', 'qpos', 'qvel', 'ctrl', 'observation', 'applied_action'):
                np.testing.assert_array_equal(probe[key], full[key][:len(probe[key])])
        state.update(status='complete', formal_prefix_exact=True,
            reference_trace_sha256=sha(reference), physics_episodes_completed=3, formal_comparison_unchanged=True,
            caveats=['Only the first ball encounter on one known teacher training identity, not whole-horizon convergence or method superiority.',
                'Norm-integrated contact load is not a signed net impulse. Peak sensitivity can persist despite a stable integral.',
                'No real material/sensor calibration or human-safety conclusion. Do not change formal gates or dt using these results.',
                'Short probes are ineligible for task success or training labels; do not count them as task-failure trials.'])
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc))
        if queue_state is not None and queue_state['status'] != 'complete':
            queue_state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
            write(queue/'execution.json', queue_state)
        raise
    finally:
        state['ended_utc'] = now(); write(out/'execution.json', state)


if __name__ == '__main__':
    main()
