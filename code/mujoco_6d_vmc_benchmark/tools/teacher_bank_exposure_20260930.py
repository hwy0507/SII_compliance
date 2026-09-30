"""Read-only, training-only contact exposure audit; never an actor input.

4-ms samples are for inspection. Sparse contiguous-contact runs retain the
physical-substep evidence needed to audit timing without downsampling aliasing.
Task success and ball rebound remain independent evaluator requirements.
"""
import json
from array import array
from pathlib import Path

import numpy as np

SAMPLE_DT = .004
FORCE_N = .05
MIN_PASSIVE_CONTACT_S = .0002
MIN_UPWARD_M = .0001
MIN_LONG_CONTACT_S = .4
MIN_DISPLACEMENT_M = .01
MIN_SEPARATION_S = .2
RUN_FIELDS = ('first_s', 'end_s', 'duration_s', 'max_tangent_m',
              'max_displacement_m', 'max_upward_m', 'peak_force_n')
PERSON_RAW_FIELDS = ('time_s', 'dt_s', 'force_n', 'hand_x_m', 'hand_y_m', 'hand_z_m')
PERSON_RUN_FIELDS = RUN_FIELDS + ('max_signed_push_m',)


def person_window_runs(raw, fixture):
    """Recompute schema-2 directional person evidence from every physical sample.

    The person's positive rail stroke moves along -fixture.axis. Only complete
    sampled intervals inside [start, start+press+hold] qualify; discarding the
    at-most-two boundary substeps prevents credit for motion outside that window.
    Origin is the first in-window contact pose, never the preceding free pose.
    """
    raw = np.asarray(raw, dtype=float)
    if raw.ndim != 2 or raw.shape[1] != len(PERSON_RAW_FIELDS):
        raise ValueError('Invalid person physical evidence shape')
    if not np.isfinite(raw).all():
        raise ValueError('Nonfinite person physical evidence')
    if len(raw) and (np.any(raw[:, 1] <= 0) or np.any(raw[:, 1] > SAMPLE_DT + 1e-8)
                    or np.any(raw[:, 2] < 0)
                    or not np.allclose(raw[1:, 0], raw[:-1, 0]+raw[:-1, 1], rtol=0, atol=1e-8)):
        raise ValueError('Invalid person physical time/force evidence')
    axis = np.asarray(fixture['axis'], dtype=float)
    if axis.shape != (3,) or not np.isfinite(axis).all() or np.linalg.norm(axis) < 1e-12:
        raise ValueError('Invalid person drive axis')
    axis = axis / np.linalg.norm(axis)
    start = float(fixture['start_s'])
    retract = start + float(fixture['press_s']) + float(fixture['hold_s'])
    if not np.isfinite([start, retract]).all() or retract <= start:
        raise ValueError('Invalid person press/hold window')
    rows, current, origin = [], None, None
    for time, dt, force, x, y, z in raw:
        contact = force > FORCE_N and time >= start-1e-9 and time+dt <= retract+1e-9
        if not contact:
            if current is not None:
                rows.append(current)
                current = None
            continue
        hand = np.array([x, y, z])
        if current is None:
            origin = hand.copy()
            current = [time, time, 0., 0., 0., 0., 0., 0.]
        delta = hand-origin
        axial = float(delta @ axis)
        current[1] = time+dt
        current[2] += dt
        current[3] = max(current[3], float(np.linalg.norm(delta-axis*axial)))
        current[4] = max(current[4], float(np.linalg.norm(delta)))
        current[5] = max(current[5], float(delta[2]))
        current[6] = max(current[6], force)
        current[7] = max(current[7], -axial)
    if current is not None:
        rows.append(current)
    return np.asarray(rows, dtype=float).reshape(-1, len(PERSON_RUN_FIELDS))


def summarize_arrays(arrays, fixture):
    """Recompute exposure gates from saved run aggregates, without MuJoCo."""
    schema = int(np.asarray(arrays['schema']))
    if schema not in (1, 2):
        raise ValueError('Unsupported exposure schema')
    runs = np.asarray(arrays['contact_runs'], dtype=float).reshape(-1, len(RUN_FIELDS))
    terminal = float(np.asarray(arrays['terminal_time_s']))
    time = np.asarray(arrays['time'], dtype=float)
    end = np.asarray(arrays['interval_end'], dtype=float)
    dt = np.asarray(arrays['dt'], dtype=float)
    contact = np.asarray(arrays['contact_duration'], dtype=float)
    force = np.asarray(arrays['force'], dtype=float)
    peaks = np.asarray(arrays['force_peak'], dtype=float)
    hand = np.asarray(arrays['hand'], dtype=float)
    stage = np.asarray(arrays['stage'], dtype=float)
    if (time.ndim != 1 or any(a.shape != time.shape for a in (end, dt, contact, force, peaks, stage))
            or hand.shape != (len(time), 3)):
        raise ValueError('Invalid exposure aggregate shapes')
    if any(not np.isfinite(a).all() for a in (time, end, dt, contact, force, peaks, hand, stage)):
        raise ValueError('Nonfinite exposure aggregates')
    if (np.any(dt <= 0) or np.any(dt > SAMPLE_DT + 1e-8)
            or not np.allclose(end-time, dt, rtol=0, atol=1e-8)
            or not np.allclose(time[1:], end[:-1], rtol=0, atol=1e-8)
            or np.any(contact < 0) or np.any(contact > dt + 1e-8)
            or np.any(force < 0) or np.any(peaks < force - 1e-8)
            or np.any(stage != np.floor(stage)) or np.any((stage < 0) | (stage > 7))
            or (len(time) and (abs(float(end[-1])-terminal) > 1e-8
                or abs(float(dt.sum())-(terminal-float(time[0]))) > 1e-8))
            or (not len(time) and (terminal != 0 or len(runs)))):
        raise ValueError('Inconsistent exposure times, force, stages or durations')
    if not np.isfinite(runs).all() or not np.isfinite(terminal):
        raise ValueError('Nonfinite contact evidence')
    if len(runs) and (np.any(runs[:, 1] < runs[:, 0]) or
                      np.any(runs[:, 2:] < 0) or
                      np.any(runs[:, 2] > runs[:, 1]-runs[:, 0] + 1e-8) or
                      np.any(runs[:, 6] <= FORCE_N) or
                      np.any(runs[1:, 0] < runs[:-1, 1] - 1e-9) or
                      runs[0, 0] < time[0] - 1e-8 or
                      terminal < runs[-1, 1] - 1e-9):
        raise ValueError('Invalid contact run ordering or duration')
    if abs(float(runs[:, 2].sum()) - float(contact.sum())) > 1e-8:
        raise ValueError('Contact run duration differs from 4ms aggregate duration')
    reasons = []
    category = fixture['category']
    first = float(runs[0, 0]) if len(runs) else None
    duration = float(runs[:, 2].sum()) if len(runs) else 0.
    diagnostics = dict(schema=schema, first_contact_s=first, contact_duration_s=duration,
        longest_contact_s=float(runs[:, 2].max()) if len(runs) else 0.,
        max_tangent_m=float(runs[:, 3].max()) if len(runs) else 0.,
        max_displacement_m=float(runs[:, 4].max()) if len(runs) else 0.,
        max_upward_m=float(runs[:, 5].max()) if len(runs) else 0.,
        contact_run_count=len(runs), accepted_run_indices=[],
        task_success_checked_here=False, ball_rebound_checked_here=False,
        timing_resolution='physical-substep contact runs; 4ms display aggregates')
    if category == 'passive_corner':
        good = [i for i, r in enumerate(runs)
                if r[2] > MIN_PASSIVE_CONTACT_S + 1e-12 and r[5] >= MIN_UPWARD_M]
        if not len(runs):
            reasons.append('no_load_bearing_lift_carry_edge_contact')
        elif not good:
            reasons.append('insufficient_upward_motion_during_edge_contact')
    elif category == 'active_short':
        good = list(range(len(runs))) if duration > MIN_PASSIVE_CONTACT_S + 1e-12 else []
        if not good:
            reasons.append('ball_contact_missing_or_too_short')
        if first is not None and first < float(fixture['start_s']) - 1e-9:
            reasons.append('ball_contact_before_launch')
    elif category == 'active_long':
        start = float(fixture['start_s'])
        retract = start + float(fixture['press_s']) + float(fixture['hold_s'])
        diagnostics['retract_start_s'] = retract
        sustained = [i for i, r in enumerate(runs)
                     if r[0] >= start - 1e-9 and r[2] > MIN_LONG_CONTACT_S + 1e-12]
        if not sustained and fixture['apparatus'] == 'rod':
            reasons.append('continuous_push_contact_not_over_0p4s')
        if fixture['apparatus'] == 'rod':
            moved = [i for i in sustained if runs[i, 3] >= MIN_DISPLACEMENT_M]
            if not moved:
                reasons.append('rod_contact_tangent_displacement_below_1cm')
            good = []
            gaps = []
            for i, r in enumerate(runs):
                next_time = runs[i+1, 0] if i+1 < len(runs) else terminal
                gap = max(0., min(float(next_time), retract) - float(r[1]))
                gaps.append(gap)
                if i in moved and gap >= MIN_SEPARATION_S - 1e-9:
                    good.append(i)
            diagnostics['separation_before_retract_s'] = gaps
            if not good:
                reasons.append('no_0p2s_separation_after_slide_before_rod_retract')
        elif fixture['apparatus'] == 'person':
            good = []
            diagnostics['accepted_run_index_space'] = 'person_window_runs'
            if schema == 1:
                # Norm-only runs and 4ms poses cannot recover exact signed
                # physical-substep motion. Never retroactively promote them.
                reasons.append('directional_yield_unverified')
                diagnostics['directional_verification'] = 'unverified_legacy_schema1'
            else:
                raw = np.asarray(arrays['person_physics'], dtype=float)
                window_runs = person_window_runs(raw, fixture)
                saved_runs = np.asarray(arrays['person_window_runs'], dtype=float)
                if saved_runs.shape != window_runs.shape or not np.isfinite(saved_runs).all():
                    raise ValueError('Invalid person window runs')
                if not np.allclose(saved_runs, window_runs, rtol=0, atol=1e-10):
                    raise ValueError('Person window runs differ from physical evidence')
                if (bool(len(raw)) != bool(len(time)) or (len(raw) and
                    (abs(raw[0, 0]-time[0]) > 1e-8 or abs(raw[-1, 0]+raw[-1, 1]-terminal) > 1e-8))):
                    raise ValueError('Person physical horizon differs from exposure aggregates')
                if len(raw):
                    indices = np.searchsorted(raw[:, 0], time-1e-9)
                    ends = np.r_[indices[1:], len(raw)]
                    if np.any(indices >= len(raw)) or np.any(ends <= indices):
                        raise ValueError('Person physical buckets differ from exposure aggregates')
                    comparisons = (
                        (raw[indices, 0], time),
                        (np.add.reduceat(raw[:, 1], indices), dt),
                        (np.add.reduceat(raw[:, 1]*(raw[:, 2] > FORCE_N), indices), contact),
                        (np.add.reduceat(raw[:, 1]*raw[:, 2], indices), force*dt),
                        (np.maximum.reduceat(raw[:, 2], indices), peaks),
                        (raw[ends-1, 3:], hand),
                    )
                    if any(not np.allclose(a, b, rtol=0, atol=1e-8) for a, b in comparisons):
                        raise ValueError('Person physical values differ from exposure aggregates')
                sustained_window = [i for i, row in enumerate(window_runs)
                                    if row[2] > MIN_LONG_CONTACT_S + 1e-12]
                good = [i for i in sustained_window if window_runs[i, 7] >= MIN_DISPLACEMENT_M]
                if not sustained_window:
                    reasons.append('continuous_press_hold_hand_contact_not_over_0p4s')
                if not good:
                    reasons.append('signed_hand_yield_along_push_below_1cm')
                diagnostics.update(directional_verification='verified_physical_substep_schema2',
                    person_push_direction=(-np.asarray(fixture['axis'], dtype=float)/np.linalg.norm(fixture['axis'])).tolist(),
                    person_window_contact_duration_s=float(window_runs[:, 2].sum()),
                    person_window_longest_contact_s=float(window_runs[:, 2].max()) if len(window_runs) else 0.,
                    person_max_signed_push_m=float(window_runs[:, 7].max()) if len(window_runs) else 0.,
                    person_window_run_count=len(window_runs),
                    meaning='signed kinematic displacement under contact; not causal attribution against nominal motion')
        else:
            raise ValueError('Unknown long-contact apparatus')
    else:
        raise ValueError('Unknown category')
    diagnostics['accepted_run_indices'] = good
    return dict(passed=not reasons, reasons=reasons, diagnostics=diagnostics)


def audit_saved(path, fixture=None):
    """Audit a saved exposure.npz; embedded fixture is checked when supplied."""
    path = Path(path)
    if path.is_dir():
        path = path / 'exposure.npz'
    with np.load(path, allow_pickle=False) as data:
        if int(data['schema']) not in (1, 2):
            raise ValueError('Unsupported exposure schema')
        saved_fixture = json.loads(str(data['fixture_json']))
        if fixture is not None and fixture != saved_fixture:
            raise ValueError('Exposure fixture mismatch')
        return summarize_arrays(data, saved_fixture)


class TrainingExposure:
    """Callable observer injected after physics metric sampling.

    record() also accepts synthetic physical-substep observations for tests.
    Contact intervals use [time, time + dt); no signal is written to env/task.
    """
    def __init__(self, fixture):
        self.fixture = json.loads(json.dumps(fixture, allow_nan=False))
        axis = np.asarray(fixture.get('axis', [1., 0., 0.]), dtype=float)
        if axis.shape != (3,) or not np.isfinite(axis).all() or np.linalg.norm(axis) < 1e-12:
            raise ValueError('Finite nonzero three-dimensional axis required')
        self.axis = axis / np.linalg.norm(axis)
        self._geometry = None
        self._previous_hand = None
        self._terminal = None
        self._run = None
        self._runs = []
        self._bucket = None
        self._samples = []
        self._person_raw = array('d')

    def __call__(self, m, d, env, task):
        import mujoco
        if self._geometry is None:
            names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or ''
                     for i in range(m.ngeom)]
            robot = set(env._push_audit_robot_geom_ids)
            target_body = int(env._target_body_id)
            payload = {i for i in range(m.ngeom) if int(m.geom_bodyid[i]) == target_body}
            category = self.fixture['category']
            if category == 'passive_corner':
                obstacles = {i for i, n in enumerate(names) if n in
                    ('office_v5_corner_face', 'office_v5_corner_training_bridge',
                     'office_v5_corner_training_bridge_connector')}
                receivers = robot | payload
            elif category == 'active_short':
                obstacles = {i for i, n in enumerate(names) if n == 'office_v5_ball_geom'}
                receivers = robot
            elif category == 'active_long':
                prefix = 'office_v5_push_rod' if self.fixture['apparatus'] == 'rod' else 'office_v5_human_'
                obstacles = {i for i, n in enumerate(names) if n.startswith(prefix)}
                receivers = robot
            else:
                raise ValueError('Unknown category')
            if not obstacles or not receivers:
                raise ValueError('Required exposure geometry missing')
            self._geometry = obstacles, receivers
        obstacles, receivers = self._geometry
        force = 0.
        for i in range(d.ncon):
            c = d.contact[i]
            g1, g2 = int(c.geom1), int(c.geom2)
            if ((g1 in obstacles and g2 in receivers) or
                    (g2 in obstacles and g1 in receivers)):
                wrench = np.zeros(6)
                mujoco.mj_contactForce(m, d, i, wrench)
                magnitude = float(np.linalg.norm(wrench[:3]))
                if magnitude > FORCE_N:
                    force += magnitude
        # Observer is invoked after mj_step. Contact forces and live xpos are
        # retained from its dynamics evaluation; they are not newly computed
        # post-step kinematics. Timestamp this completed interval, without
        # writing/forwarding live data or pretending perfect synchrony.
        dt = float(m.opt.timestep)
        self.record(float(d.time) - dt, dt, force,
                    d.xpos[env._hand_id], int(task.index))

    def record(self, time, dt, force, hand, stage):
        hand = np.asarray(hand, dtype=float).copy()
        if (hand.shape != (3,) or not np.isfinite(np.r_[time, dt, force, hand]).all()
                or dt <= 0 or force < 0):
            raise ValueError('Invalid exposure observation')
        if self._terminal is not None and abs(time - self._terminal) > 1e-8:
            raise ValueError('Exposure observer must sample every physical substep')
        if self.fixture['category'] == 'active_long' and self.fixture.get('apparatus') == 'person':
            self._person_raw.extend((float(time), float(dt), float(force), *map(float, hand)))
        contact = force > FORCE_N
        if self.fixture['category'] == 'passive_corner':
            contact = contact and stage in (3, 4)
        if contact:
            if self._run is None:
                origin = self._previous_hand.copy() if self._previous_hand is not None else hand.copy()
                self._run = dict(first=time, end=time, duration=0., origin=origin,
                                 tangent=0., displacement=0., upward=0., peak=0.)
            run = self._run
            delta = hand - run['origin']
            tangent = delta - self.axis * float(delta @ self.axis)
            run['end'] = time + dt
            run['duration'] += dt
            run['tangent'] = max(run['tangent'], float(np.linalg.norm(tangent)))
            run['displacement'] = max(run['displacement'], float(np.linalg.norm(delta)))
            run['upward'] = max(run['upward'], float(delta[2]))
            run['peak'] = max(run['peak'], force)
        elif self._run is not None:
            self._runs.append(self._run_array())
            self._run = None
        bucket_id = int(np.floor((time + 1e-10) / SAMPLE_DT))
        if self._bucket is not None and bucket_id != self._bucket['id']:
            self._flush_bucket()
        if self._bucket is None:
            self._bucket = dict(id=bucket_id, time=time, end=time+dt, dt=0., force_integral=0.,
                                force_peak=0., contact_s=0., hand=hand, stage=stage)
        bucket = self._bucket
        bucket.update(end=time+dt, hand=hand, stage=stage)
        bucket['dt'] += dt
        bucket['force_integral'] += force * dt
        bucket['force_peak'] = max(bucket['force_peak'], force)
        bucket['contact_s'] += dt if contact else 0.
        self._terminal = time + dt
        self._previous_hand = hand

    def _run_array(self):
        r = self._run
        return [r['first'], r['end'], r['duration'], r['tangent'],
                r['displacement'], r['upward'], r['peak']]

    def _bucket_array(self):
        b = self._bucket
        return [b['time'], b['end'], b['dt'], b['force_integral']/b['dt'],
                b['force_peak'], b['contact_s'], *b['hand'], b['stage']]

    def _flush_bucket(self):
        self._samples.append(self._bucket_array())
        self._bucket = None

    def arrays(self):
        samples = self._samples + ([self._bucket_array()] if self._bucket is not None else [])
        rows = np.asarray(samples, dtype=float).reshape(-1, 10)
        runs = self._runs + ([self._run_array()] if self._run is not None else [])
        person_raw = np.frombuffer(self._person_raw, dtype=np.float64).reshape(-1, len(PERSON_RAW_FIELDS)).copy()
        window_runs = (person_window_runs(person_raw, self.fixture)
                       if self.fixture['category'] == 'active_long' and self.fixture.get('apparatus') == 'person'
                       else np.empty((0, len(PERSON_RUN_FIELDS))))
        return dict(schema=np.array(2), fixture_json=np.array(json.dumps(self.fixture, sort_keys=True)),
            time=rows[:, 0], interval_end=rows[:, 1], dt=rows[:, 2], force=rows[:, 3],
            force_peak=rows[:, 4], contact_duration=rows[:, 5], hand=rows[:, 6:9],
            stage=rows[:, 9].astype(np.int32), contact_runs=np.asarray(runs).reshape(-1, len(RUN_FIELDS)),
            contact_run_fields=np.array(RUN_FIELDS), terminal_time_s=np.array(self._terminal or 0.),
            person_physics=person_raw, person_physics_fields=np.array(PERSON_RAW_FIELDS),
            person_window_runs=window_runs, person_window_run_fields=np.array(PERSON_RUN_FIELDS))

    def summary(self):
        return summarize_arrays(self.arrays(), self.fixture)

    def save(self, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / 'exposure.npz'
        np.savez_compressed(path, **self.arrays())
        return path
