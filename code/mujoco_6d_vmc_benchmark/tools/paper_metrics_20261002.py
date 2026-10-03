"""Predeclared contact/recovery diagnostics; never replaces task/strict gates."""
import argparse
import json
import shutil
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now

FORCE_THRESHOLD_N = .05
REJOIN_ERROR_M = .025
SETTLED_SPEED_MPS = .025
HOLD_S = .5


def segments(mask):
    padded = np.r_[False, mask, False].astype(np.int8)
    return zip(np.flatnonzero(np.diff(padded) == 1), np.flatnonzero(np.diff(padded) == -1))


def force_statistics(time, dt, force, mask, semantics):
    """Observed support only; integral is of summed magnitudes, not net force."""
    active = mask & (force > FORCE_THRESHOLD_N)
    ids = np.flatnonzero(active)
    return dict(observed_duration_s=float(dt[mask].sum()), exposure=bool(len(ids)),
        force_semantics=semantics, contact_duration_s=float(dt[active].sum()),
        impulse_ns=float(np.sum(force[mask]*dt[mask])),
        peak_force_n=float(force[mask].max(initial=0.)),
        contact_p95_force_n=float(np.percentile(force[active], 95)) if len(ids) else None,
        contact_rms_force_n=float(np.sqrt(np.sum(force[active]**2*dt[active])/dt[active].sum())) if len(ids) else None,
        force_squared_integral_n2s=float(np.sum(force[mask]**2*dt[mask])),
        first_contact_s=float(time[ids[0]]) if len(ids) else None,
        last_contact_s=float(time[ids[-1]]) if len(ids) else None)


def measure(run):
    summary = json.loads((run/'rollout.json').read_text())
    state = json.loads((run/'execution.json').read_text())
    channels = json.loads((run/'research_channels.json').read_text())
    assert sha(run/'research_substeps.npz') == channels['telemetry_sha256']
    with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
        time, dt, error, velocity, torque, stage = [z[k].copy() for k in
            ('time', 'dt', 'error', 'twist', 'qfrc_actuator', 'stage')]
    with np.load(run/'research_substeps.npz') as z:
        values = {k: z[k].copy() for k in z.files}
    assert all(len(x) == len(time) and np.isfinite(x).all() for x in [dt, error, velocity, torque, *values.values()])
    assert np.all(dt > 0) and np.all(np.diff(time) > 0)
    error = error.astype(float); velocity = velocity.astype(float); torque = torque.astype(float)
    position_error = np.linalg.norm(error, axis=1)
    speed = np.linalg.norm(velocity[:, :3], axis=1)
    np.testing.assert_allclose(values['hand_position']-values['reference_position'], error, rtol=0, atol=1.3e-7)
    duration = float(dt.sum())
    total_variation = np.sum(np.abs(np.diff(torque, axis=0)), axis=0)
    args = summary['arguments']
    windows = dict(ball=(summary['ball_launch_time_s'], args['person_start'], 1),
                   human=(args['person_start'], args['person_start']+7, 2),
                   rod=(args['rod_start'], args['rod_start']+1.5+args['rod_hold']+2, 3),
                   unknown_edge=(0., time[-1], 4), pillar=(0., time[-1], 5))
    contact = {}
    force = values['contact_force_sum'].astype(float)
    for name, (start, end, column) in windows.items():
        window = (time >= start) & (time <= end)
        active = window & (force[:, column] > FORCE_THRESHOLD_N)
        ids = np.flatnonzero(active)
        row = dict(window_s=[float(start), float(end)], observed_duration_s=float(dt[window].sum()),
                   exposure=bool(len(ids)), force_semantics=channels['force_columns'][column],
                   contact_duration_s=float(dt[active].sum()), impulse_ns=float(np.sum(force[window, column]*dt[window])),
                   peak_force_n=float(force[window, column].max(initial=0.)),
                   contact_p95_force_n=float(np.percentile(force[active, column], 95)) if len(ids) else None,
                   contact_rms_force_n=float(np.sqrt(np.sum(force[active, column]**2*dt[active])/dt[active].sum())) if len(ids) else None,
                   force_squared_integral_n2s=float(np.sum(force[window, column]**2*dt[window])))
        if len(ids):
            after_contact = window & (time >= time[ids[0]])
            row.update(first_contact_s=float(time[ids[0]]), last_contact_s=float(time[ids[-1]]),
                       hand_max_displacement_during_event_m=float(np.max(np.linalg.norm(
                           values['hand_position'][after_contact]-values['hand_position'][ids[0]], axis=1))),
                       displacement_window='First actual contact through event-window end',
                       hand_path_during_contact_m=float(np.sum(speed[active]*dt[active])))
        contact[name] = row
    # This is a gap in robot/rod force during the fixed fully-extended interval,
    # not a success gate and not proof of hand-only sliding or placement.
    start = args['rod_start']+1.5; end = start+args['rod_hold']
    rod_on = force[:, 3] > FORCE_THRESHOLD_N
    first = np.flatnonzero(rod_on & (time >= args['rod_start']) & (time <= end))
    rod_gap = None
    if len(first):
        eligible = (time >= max(start, time[first[0]])) & (time <= end)
        spans = [(float(dt[s:e].sum()), float(time[s]), float(time[e-1]))
                 for s, e in segments(eligible & ~rod_on)]
        rod_gap = max(spans) if spans else (0., None, None)
    contact['rod']['extended_no_contact_longest_s'] = rod_gap[0] if rod_gap else None
    contact['rod']['extended_no_contact_interval_s'] = list(rod_gap[1:]) if rod_gap else None
    contact['rod']['gap_requires_prior_contact'] = True
    # Supplemental after public development inspection, before final opening.
    # Preserve original commanded-event windows above exactly. Static human
    # geometry can be encountered again during placement; report those loads.
    all_samples = np.ones(len(time), dtype=bool)
    whole = {'external_robot': force_statistics(time, dt, force[:, 0], all_samples,
                                               channels['force_columns'][0])}
    outside = {}
    for name, (start, end, column) in windows.items():
        whole[name] = force_statistics(time, dt, force[:, column], all_samples,
                                       channels['force_columns'][column])
        if name in ('ball', 'human', 'rod'):
            outside[name] = force_statistics(time, dt, force[:, column],
                (time < start) | (time > end), channels['force_columns'][column])
            outside[name]['excluded_event_window_s'] = [float(start), float(end)]
    # Rejoin is explicitly settled rejoin plus reference progress. Fast traversal
    # need not pass it; task completion/progress remain separate primary outcomes.
    recovery = {}
    cursor = values['route_cursor']
    for name, unload, censor in [('ball', summary['ball_launch_time_s'], args['person_start']),
                                 ('human', args['person_start']+7, args['rod_start']),
                                 ('rod', args['rod_start']+1.5+args['rod_hold']+2, float(time[-1]))]:
        observed = contact[name]['exposure']
        if name == 'ball' and observed:
            unload = contact[name]['last_contact_s']
        if name == 'rod':
            next_obstacle = np.flatnonzero((time >= unload) & np.any(force[:, 4:6] > FORCE_THRESHOLD_N, axis=1))
            if len(next_obstacle):
                censor = min(censor, float(time[next_obstacle[0]]))
        # An aborted rollout cannot supply observation time after its last
        # physical sample, even when the scheduled next disturbance is later.
        planned_censor = censor
        censor = min(censor, float(time[-1]))
        index = int(np.searchsorted(time, unload)); index = min(index, len(time)-1)
        progress = (stage > stage[index]) | ((stage == stage[index]) & (cursor > cursor[index]))
        band = ((time >= unload) & (time <= censor) & (position_error <= REJOIN_ERROR_M)
                & (speed <= SETTLED_SPEED_MPS) & progress)
        reached = None
        if observed:
            for s, e in segments(band):
                if dt[s:e].sum() >= HOLD_S-1e-10:
                    reached = float(time[s]-unload); break
        recovery[name] = dict(exposed=observed, unload_s=float(unload), censor_s=float(censor),
                              planned_censor_s=float(planned_censor),
                              settled_rejoin_time_s=reached, right_censored=bool(observed and reached is None),
                              applicable=observed, observation_window_s=max(0., float(censor-unload)),
                              criterion='position<=25mm, actual speed<=25mm/s, continuous0.5s and at least one subsequent route cursor/task stage')
    result = dict(created_utc=now(), metric_version='4-supplemental-whole-horizon-contact',
                  run=str(run.resolve()), metric_source_sha256=sha(Path(__file__)),
                  constants=dict(force_threshold_n=FORCE_THRESHOLD_N, rejoin_error_m=REJOIN_ERROR_M,
                                 settled_speed_mps=SETTLED_SPEED_MPS, hold_s=HOLD_S),
                  task_success=summary['task_success'], strict_success=summary['strict_success'],
                  full_horizon=summary['full_task_horizon_completed'], abort_reason=summary['abort_reason'],
                  final_stage=summary['final_task_stage'], sample_count=len(time), duration_s=duration,
                  rmse_mm=float(1000*np.sqrt(np.sum(position_error**2*dt)/duration)),
                  position_error_integral_m_s=float(np.sum(position_error*dt)),
                  time_above_25mm_s=float(np.sum(dt[position_error > .025])),
                  peak_torque_nm=float(np.max(np.abs(torque))), peak_speed_mps=float(speed.max()),
                  torque_total_variation_nm_by_joint=total_variation.tolist(),
                  absolute_joint_mechanical_work_j=float(np.sum(np.abs(torque*values['dq']).sum(axis=1)*dt)),
                  contact=contact, recovery=recovery,
                  supplemental_contact=dict(whole_observed_horizon=whole, outside_event_window=outside,
                      note='Supplemental descriptive metrics registered after public development inspection, before final opening. Outside means before OR after the original window. No invented future time for aborted runs. External robot excludes payload; edge includes robot OR payload, so channels are not disjoint or additive. No change to event metrics or task/strict gates.'),
                  final_route_cursor=int(cursor[-1]), placement_error_xy_mm=float(summary['placement_error_xy_m']*1000),
                  model_sha256=sha(run/'rollout.mjb'), trace_sha256=sha(run/'rollout.npz'),
                  native_metrics_sha256=sha(run/'rollout_metrics/substep_metrics.npz'),
                  research_metrics_sha256=channels['telemetry_sha256'], execution_sha256=sha(run/'execution.json'),
                  limitation='Descriptive paired-development contact/recovery metrics; no-contact is NA. Task and safety dominate. Held-step force/post-step velocity work is diagnostic, not a passivity certificate. A lower first impact peak cannot establish 25Hz feedback response.')
    assert result['model_sha256'] == state['runtime_provenance']['model_sha256']
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    source_copy = a.output.with_suffix('.source.py')
    if source_copy.exists():
        raise FileExistsError(source_copy)
    result = measure(a.run)
    shutil.copy2(__file__, source_copy)
    write(a.output, result)
    print(json.dumps({k: result[k] for k in ('task_success', 'strict_success', 'rmse_mm', 'final_stage')}))
