"""Public diagnostic of impact timing versus the recorded actor update clock.

Reads all initial learned candidates and the original teacher on five complete
public development identities. No model selection, fitting or new physics.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np

THRESHOLD_N = .05


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def timing(time, dt, force, actor_time, start, end):
    time, dt, force, actor_time = [np.asarray(v, dtype=float) for v in (time, dt, force, actor_time)]
    assert len(time) == len(dt) == len(force) and len(time) and len(actor_time)
    assert np.all(np.diff(time) > 0) and np.all(np.diff(actor_time) > 0) and np.all(dt > 0)
    assert all(np.isfinite(v).all() for v in (time, dt, force, actor_time))
    eligible = (time >= start) & (time <= end)
    active = eligible & (force > THRESHOLD_N)
    ids = np.flatnonzero(active)
    if not len(ids):
        return dict(exposed=False, first_contact_s=None, next_actor_update_s=None,
                    window_peak_before_next_actor_update=None, first_bout_ended_before_next_actor_update=None)
    first = int(ids[0]); tail = np.flatnonzero(~active[first:])
    stop = first+int(tail[0]) if len(tail) else len(time)
    bout_peak = first+int(np.argmax(force[first:stop]))
    eligible_ids = np.flatnonzero(eligible)
    window_peak = int(eligible_ids[np.argmax(force[eligible])])
    # neuron_time is the actual pre-action observation timestamp. Native force
    # samples are stamped after the completed physics step, so timing is only
    # resolved to one dt. An exactly coincident update is potentially available.
    next_id = int(np.searchsorted(actor_time, time[first]-1e-10))
    next_time = float(actor_time[next_id]) if next_id < len(actor_time) else None
    def before(index):
        return bool(time[index]+dt[index] < next_time) if next_time is not None else None
    return dict(exposed=True, first_contact_s=float(time[first]),
        first_contact_time_resolution_s=float(dt[first]),
        actor_update_before_contact_s=float(actor_time[next_id-1]) if next_id else None,
        next_actor_update_s=next_time,
        time_until_next_actor_update_ms=1000*(next_time-float(time[first])) if next_time is not None else None,
        first_bout_end_s=float(time[stop-1]), first_bout_duration_ms=float(dt[first:stop].sum()*1000),
        first_bout_peak_force_n=float(force[bout_peak]), first_bout_peak_time_s=float(time[bout_peak]),
        window_peak_force_n=float(force[window_peak]), window_peak_time_s=float(time[window_peak]),
        first_bout_peak_before_next_actor_update=before(bout_peak),
        window_peak_before_next_actor_update=before(window_peak),
        first_bout_ended_before_next_actor_update=before(stop-1),
        actor_update_interval_median_ms=float(np.median(np.diff(actor_time))*1000))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); root = a.root.resolve(); out = a.output.resolve()
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    protocol = read(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']
    conditions = [f'development_{i:03d}' for i in range(5)]
    roles = {c['id']: c['role'] for c in read(root/'CONDITIONS.json')['conditions']}
    assert all(roles[c] == 'development' for c in conditions)
    spec = read(root/'LEARNING_DEVELOPMENT_SPECIFICATION.json')
    assert spec['protocol_sha256'] == sha(root/'PROTOCOL.json') and len(spec['candidates']) == 33
    names = {c['name'] for c in spec['candidates']}; planned = []
    for q in sorted((root/'learning_development_v1').glob('queue_[0-3]/execution.json')):
        for row in read(q)['rows']:
            if row['condition_id'] in conditions:
                assert 'audit_sha256' in row, 'Wait until all five public identities are complete'
                planned.append(dict(candidate=row['candidate'], condition=row['condition_id'],
                    category=row['category'], run=str(q.parent/row['name']), audit_sha256=row['audit_sha256']))
    for condition in conditions:
        rows = [r for r in planned if r['condition'] == condition]
        assert len(rows) == 33 and {r['candidate'] for r in rows} == names
        paths = list((root/'teacher_bank').glob('queue_*/'+condition)); assert len(paths) == 1
        planned.append(dict(candidate='original_teacher', category='enhanced_teacher', condition=condition,
            run=str(paths[0]), audit_sha256=sha(paths[0]/'AUDIT.json')))
    out.mkdir(parents=True, exist_ok=False)
    write(out/'SPECIFICATION.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)), protocol_sha256=sha(root/'PROTOCOL.json'),
        learned_spec_sha256=sha(root/'LEARNING_DEVELOPMENT_SPECIFICATION.json'),
        conditions=conditions, planned=planned, threshold_n=THRESHOLD_N,
        diagnostic_only=True, physics_episodes=0, fitting_updates=0, sealed_contents_read=False))
    result = []
    for entry in planned:
        run = Path(entry['run']); audit = read(run/'AUDIT.json'); summary = read(run/'rollout.json')
        assert sha(run/'AUDIT.json') == entry['audit_sha256']
        assert read(run/'execution.json')['status'] == 'complete'
        channels = read(run/'research_channels.json')
        assert sha(run/'research_substeps.npz') == channels['telemetry_sha256']
        with np.load(run/'rollout.npz') as z:
            actor_time = z['neuron_time'].copy()
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            time, dt = z['time'].copy(), z['dt'].copy()
        with np.load(run/'research_substeps.npz') as z:
            force = z['contact_force_sum'][:, 1].copy()
        metrics = timing(time, dt, force, actor_time, summary['ball_launch_time_s'], summary['arguments']['person_start'])
        result.append(dict(entry, **metrics, task=audit['task_success'], strict=audit['strict_success'],
            full_horizon=audit['full_horizon'], trace_sha256=sha(run/'rollout.npz'),
            physical_metrics_sha256=sha(run/'rollout_metrics/substep_metrics.npz'),
            contact_metrics_sha256=channels['telemetry_sha256']))
    exposed = [r for r in result if r['exposed']]
    report = dict(completed_utc=datetime.now(timezone.utc).isoformat(), specification_sha256=sha(out/'SPECIFICATION.json'),
        rows=result, episodes=len(result), exposed=len(exposed),
        window_peak_before_first_available_actor_update=sum(r['window_peak_before_next_actor_update'] is True for r in exposed),
        first_bout_ended_before_first_available_actor_update=sum(r['first_bout_ended_before_next_actor_update'] is True for r in exposed),
        physics_episodes=0, fitting_updates=0, sealed_contents_read=False,
        limitations=['Timing alone does not identify a controller action effect or prove a force reduction.',
            'Public diagnostic chosen after development inspection, not an initial primary endpoint.',
            'Precontact pose/action can differ between methods; the 4ms WBC and passive dynamics still respond within an actor interval.',
            'First postcontact actor evaluation is only the earliest opportunity, not proof that the filtered load estimate already changes the action.',
            'Peak before that evaluation cannot demonstrate reactive 25Hz policy attenuation of the same first peak.',
            'Force magnitudes come from the frozen simulated contact model, not a calibrated human-safety measurement.'])
    write(out/'IMPACT_TIMING.json', report)
    print(json.dumps({k: report[k] for k in ('episodes', 'exposed', 'window_peak_before_first_available_actor_update',
        'first_bout_ended_before_first_available_actor_update')}))


if __name__ == '__main__':
    main()
