"""One preregistered original-ESN transfer to the archived September 28 office.

Loads the exact archived binary. No training, geometry tuning, or gate changes.
Uses the existing current evaluator/nominal controller and audited action adapter.
"""
import json
from pathlib import Path
import sys
import time

import mujoco
import numpy as np
import optimize_tool_contact_20261002 as worker

ROOT = worker.ROOT
OLD = ROOT / 'outputs/esn_office_delayed_conservative_full_20260928'
MODEL_SHA = '586dd7f279dc511983910661b0941846a2a8bb8d8d4afb312907d3634cd5a620'
CHECKPOINT = ROOT / 'outputs/paired_baseline_development_20261012_v2/checkpoints/esn.npz'
CHECKPOINT_SHA = 'acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7'


def audit(run, config, checkpoint, memory_ablation):
    """Same physical/replay checks, compatible with a scene without an edge."""
    from current_student_policy_20260921 import load_current
    result = json.loads((run / 'rollout.json').read_text())
    reference = json.loads((OLD / 'rollout.json').read_text())
    for key in ('schedule', 'observer_settings'):
        assert result[key] == reference[key], key
    # September 28 predates these metadata fields. Absence is not equality.
    placement_metadata = {}
    for key in ('placement_destination', 'placement_support_geoms'):
        if key in reference:
            assert result[key] == reference[key], key
            placement_metadata[key] = 'equal'
        else:
            placement_metadata[key] = 'not recorded in historical reference'
    assert worker.sha(run / 'rollout.mjb') == MODEL_SHA
    assert worker.sha(checkpoint) == CHECKPOINT_SHA
    actor = load_current(checkpoint)
    filt = worker.VelocityResidualActionFilter(worker.VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
    with np.load(run / 'rollout.npz') as z, np.load(run / 'execution_chain.npz') as c:
        for i, obs in enumerate(z['observation']):
            action = actor.act(obs)
            np.testing.assert_array_equal(action, z['applied_action'][i])
            np.testing.assert_array_equal(actor.state, z['reservoir_state'][i])
            np.testing.assert_array_equal(action, c['requested_action'][i])
            filtered = filt.filter(action, .04)
            np.testing.assert_array_equal(filtered.raw_action_clipped, c['clipped_action'][i])
            np.testing.assert_array_equal(filtered.cartesian_yield_twist, c['yield_twist'][i])
            assert filtered.wbc_scale == c['wbc_scale'][i]
    with np.load(run / 'rollout_metrics/substep_metrics.npz') as z:
        dt = z['dt']; error = z['error'].astype(float)
        rmse = float(np.sqrt(np.sum(error**2 * dt[:, None]) / dt.sum()))
        torque = float(np.max(np.abs(z['qfrc_actuator'])))
        speed = float(np.max(np.linalg.norm(z['twist'][:, :3].astype(float), axis=1)))
        duration = float(dt.sum()); samples = len(dt)
        for k in z.files:
            assert np.isfinite(z[k]).all(), k
    np.testing.assert_allclose([rmse, torque, speed], [result['metrics'][k] for k in
        ('position_rmse_3d_m', 'generalized_actuator_torque_peak_nm', 'linear_speed_peak_mps')], rtol=3e-7, atol=1e-7)
    if result['full_task_horizon_completed']:
        assert abs(duration - 55) < 1e-7
    row = dict(task_success=result['task_success'], strict_success=result['strict_success'],
        stage=result['final_task_stage'], full_horizon=result['full_task_horizon_completed'],
        rmse_mm=rmse*1000, peak_torque_nm=torque, peak_speed_mps=speed,
        penetration_mm=result['stats']['max_external_penetration_m']*1000,
        edge_penetration_mm=0., edge_present=False, physical_seconds=duration, samples=samples,
        abort_reason=result['abort_reason'], task_events=result['task_events'],
        action_replay_max_abs=0., reservoir_replay_max_abs=0., common_filter_replay_max_abs=0.,
        old_schedule_observer_match=True, historical_placement_metadata=placement_metadata,
        model_sha256=worker.sha(run / 'rollout.mjb'), checkpoint_sha256=worker.sha(checkpoint),
        trace_sha256=worker.sha(run / 'rollout.npz'), chain_sha256=worker.sha(run / 'execution_chain.npz'),
        metrics_sha256=worker.sha(run / 'rollout_metrics/substep_metrics.npz'))
    worker.write(run / 'AUDIT.json', row)
    return row


def recover_audit(run):
    """Audit completed evidence without rerunning physics or rewriting execution."""
    import tarfile
    run = run.resolve()
    receipt_path = run / 'AUDIT_RECOVERY.json'
    if receipt_path.exists():
        raise FileExistsError(receipt_path)
    execution_path = run / 'execution.json'
    original_hash = worker.sha(execution_path)
    record = json.loads(execution_path.read_text())
    assert record['status'] == 'failed_preserved'
    assert record['error'] == "KeyError('placement_destination')"
    result = json.loads((run / 'rollout.json').read_text())
    assert result['execution_complete'] and result['full_task_horizon_completed']
    # Verify the executed source snapshot; the audit-only fix is a separate source.
    with tarfile.open(run / 'source_overlay.tar.gz') as archive:
        for name, expected in record['source_sha256'].items():
            assert worker.hashlib.sha256(archive.extractfile(name).read()).hexdigest() == expected, name
    unchanged = [name for name in record['source_sha256'] if name != 'tools/' + Path(__file__).name]
    assert all(worker.sha(ROOT / name) == record['source_sha256'][name] for name in unchanged)
    assert worker.sha(run / 'executed_fr3_scene.py.txt') == record['runtime_provenance']['executed_constructor_sha256']
    row = audit(run, record['config'], run / 'checkpoint.npz', 'none')
    with np.load(run / 'independent_contacts.npz') as z:
        values = [float(z[k].max()*1000) for k in ('external_penetration_m', 'edge_penetration_m')]
        assert len(z['time']) == row['samples']
    np.testing.assert_allclose(values, [row['penetration_mm'], row['edge_penetration_mm']], rtol=0, atol=1e-12)
    assert worker.sha(execution_path) == original_hash
    receipt = dict(status='audit_recovered', time_utc=worker.now(), physics_rerun=False,
        historical_execution_status=record['status'], historical_error=record['error'],
        execution_sha256=original_hash, audit_source_sha256=worker.sha(__file__),
        source_archive_verified=True, unchanged_runtime_sources=len(unchanged),
        independent_contact_max_mm=values,
        input_sha256={name:worker.sha(run/name) for name in
            ('rollout.json','rollout.npz','checkpoint.npz','rollout.mjb','source_overlay.tar.gz','independent_contacts.npz')},
        audit_sha256=worker.sha(run/'AUDIT.json'), result=row)
    worker.write(receipt_path, receipt)
    print(json.dumps(receipt, indent=2))


def wait_for_capacity(out):
    own = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    cap = int((own / 'memory.max').read_text())
    assert cap == 1536 * 1024**2
    deadline = time.monotonic() + 1800
    while True:
        available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))) * 1024
        running = []
        for cg in own.parent.glob('sii-fair-p[0-9]*.service'):
            try:
                used = int((cg / 'memory.current').read_text())
                if used:
                    running.append(dict(unit=cg.name, used=used, cap=int((cg / 'memory.max').read_text())))
            except FileNotFoundError:
                continue
        needed = cap + sum(max(0, r['cap'] - r['used']) for r in running) + 768 * 1024**2
        admit = len(running) < 4 and available >= needed
        worker.write(out.parent / 'RESOURCE_ADMISSION.json', dict(time_utc=worker.now(), admitted=admit,
            available=available, required=needed, own_cap=cap, other_workers=running,
            no_other_job_stopped=True))
        if admit:
            print('Memory admission passed', available, needed, flush=True)
            return
        if time.monotonic() >= deadline:
            raise RuntimeError('Memory admission timeout; no physical episode started')
        time.sleep(1)


def main():
    import fr3_scene
    out = Path(sys.argv[sys.argv.index('--output') + 1]).resolve()
    wait_for_capacity(out)
    assert worker.sha(OLD / 'rollout.mjb') == MODEL_SHA
    assert worker.sha(CHECKPOINT) == CHECKPOINT_SHA
    assert Path(sys.argv[sys.argv.index('--reference') + 1]).resolve() == OLD / 'rollout.json'
    assert Path(sys.argv[sys.argv.index('--checkpoint') + 1]).resolve() == CHECKPOINT
    source = (ROOT / 'scripts/fr3_scene.py').read_text()
    needle = '    model = mujoco.MjModel.from_xml_string(xml)'
    assert source.count(needle) == 1
    # Keep construction/initialization code; only swap compiled geometry for the
    # already archived model before it is used. Do not edit global MjModel APIs.
    executed = source.replace(needle, needle + '\n    model = mujoco.MjModel.from_binary_path(' + repr(str(OLD / 'rollout.mjb')) + ')')
    exec(compile(executed, str(fr3_scene.__file__) + '[archived-old-office]', 'exec'), fr3_scene.__dict__)
    worker.EXPECTED_MJB = MODEL_SHA
    worker.AUDIT_FUNCTION = audit
    worker.EXTRA_SOURCE_FILES = [Path(__file__)]
    worker.RUNTIME_ARGUMENT_OVERRIDES = dict(interaction_demo=False, corner_placement=False,
        combined_demo=False, combined_contact_v2=False, relaxed_pillar=False,
        combined_thick_corner_pillar_v1=False, combined_thick_corner_pillar_v2=False,
        combined_thick_corner_pillar_v3=False, combined_thick_corner_pillar_v4=False,
        planned_hand_corner=False, unexpected_edge=False, allow_lateral_rejoin=False,
        hybrid_vmc_blend=0., interaction_schedule='legacy')
    worker.RUNTIME_PROVENANCE = dict(
        purpose='Single current-original-ESN frozen-weight cross-layout demonstration',
        old_model_sha256=MODEL_SHA, checkpoint_sha256=CHECKPOINT_SHA,
        old_reference_sha256=worker.sha(OLD / 'rollout.json'),
        protocol_sha256=worker.sha(out.parent / 'PROTOCOL.json'),
        executed_constructor_sha256=worker.hashlib.sha256(executed.encode()).hexdigest(),
        actor_input='Unchanged canonical48 proprioceptive/reference-relative fields',
        teacher_at_runtime=False, training=False, server_compute=False,
        limitation='One historical layout, not a multi-layout success rate. Current evaluator source, not bitwise reproduction of the old controller runtime.')
    try:
        worker.main()
    finally:
        if out.exists():
            (out / 'executed_fr3_scene.py.txt').write_text(executed)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--audit-only':
        recover_audit(Path(sys.argv[2]))
    else:
        main()
