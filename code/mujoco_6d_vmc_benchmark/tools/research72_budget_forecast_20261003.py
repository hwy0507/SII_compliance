"""Read-only capacity forecast from a public exposure snapshot, never a dispatcher.

The lower bound assumes perfect sharing of four slots. Real lease scheduling,
GPU contention, startup, retries (not automatically allowed), and audits can
only add time. No heldout identities, candidate scores or success ranking enter.
"""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import statistics


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, q):
    ordered = sorted(values)
    index = (len(ordered)-1)*q
    left = int(index)
    right = min(left+1, len(ordered)-1)
    return ordered[left]+(ordered[right]-ordered[left])*(index-left)


def forecast(snapshot, protocol, throughput, optional_episodes=144, reserve_hours=2.):
    assert snapshot['sealed_contents_read'] is False
    snapshot_time = datetime.fromisoformat(snapshot['created_utc'])
    end = datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    development_end = datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    counts = dict(learning_development_v1=264, controller_confirmation_v1=64,
        nominal_development=8, neural_lr_development=168, development=168,
        collection=40, evaluation=1)
    if any(Path(p['path']).name == 'public_numerical_probe_v1' and p['status'] != 'not_started'
           for p in snapshot['physics']):
        # Deliberately charge a full55s-equivalent for each registered3s probe;
        # small conservative overhead instead of claiming an exact speedup.
        counts['public_numerical_probe_v1'] = 3
    pending = []
    for phase in snapshot['physics']:
        label = Path(phase['path']).name
        if label not in counts:
            continue
        completed = phase.get('totals', {}).get('completed', 0)
        assert 0 <= completed <= counts[label]
        pending.append(dict(phase=phase['path'], maximum_registered_episodes=counts[label],
            completed=completed, remaining_including_inflight=counts[label]-completed))
    assert len(pending) == len(counts), 'Missing public phase is not zero remaining work'
    # Full-length attempts of every outcome, with recent common implementation.
    timings = [r['wall_seconds'] for p in snapshot['physics']
        if Path(p['path']).name == 'learning_development_v1' for r in p.get('rows', [])
        if r['completed'] and r['full_horizon'] and r['wall_seconds'] is not None]
    assert timings and all(t > 0 for t in timings)
    cap = protocol['budget_caps']['rl_adaptation_steps_per_family_seed']
    rl = snapshot['rl']
    assert rl['registered_models'] == 15
    interactions = sum(r['cumulative_steps'] for r in rl['rows'])
    assert interactions == rl['totals']['completed_interaction_steps']
    assert len(rl['rows']) <= 15 and all(0 <= r['cumulative_steps'] <= cap for r in rl['rows'])
    remaining_steps = 15*cap-interactions
    # A nominal full episode has1375 actor steps. Early failures may add launches;
    # this is only a physics-duration equivalent, not a count of future episodes.
    rl_equivalent = remaining_steps/1375
    isolated_gpu_s = max(r['steady_action_mean_s']+r['steady_two_updates_mean_s']
        for r in throughput['rows'])
    scenarios = []
    for name, episode_s in [('median', statistics.median(timings)), ('p90', percentile(timings, .9))]:
        prereq = sum(r['remaining_including_inflight'] for r in pending
            if Path(r['phase']).name in ('learning_development_v1', 'controller_confirmation_v1'))
        queued = sum(r['remaining_including_inflight'] for r in pending)-prereq
        # Charge GPU learning at every remaining step (including warmup) as an
        # explicit conservative learner estimate, while sharing slots ideally.
        learner_hours = remaining_steps*isolated_gpu_s/3600
        base_hours = ((prereq+queued+rl_equivalent)*episode_s/3600+learner_hours)/4
        optional_hours = optional_episodes*episode_s/3600/4
        final_hours = 38*24*episode_s/3600/4
        scenarios.append(dict(episode_time_basis=name, episode_wall_s=episode_s,
            ideal_remaining_development_hours=base_hours,
            isolated_learning_slot_hours=learner_hours,
            optional_development_ideal_hours=optional_hours,
            development_window_remaining_hours=(development_end-snapshot_time).total_seconds()/3600,
            development_ideal_slack_with_optional_hours=(development_end-snapshot_time).total_seconds()/3600-base_hours-optional_hours,
            final_physics_ideal_hours=final_hours, reporting_reserve_hours=reserve_hours,
            latest_final_start_with_assumed_reserve_utc=(end-timedelta(hours=final_hours+reserve_hours)).isoformat(),
            total_ideal_slack_with_optional_and_reserve_hours=(end-snapshot_time).total_seconds()/3600-base_hours-optional_hours-final_hours-reserve_hours))
    return dict(snapshot_utc=snapshot['created_utc'], forecast_only=True,
        final_condition_contents_read=False, optional_fits_authorized_by_this_report=False,
        full_horizon_timing_samples=len(timings), pending_phases=pending,
        rl_remaining_interactions_to_all_caps=remaining_steps,
        rl_full_episode_duration_equivalent=rl_equivalent,
        optional_episodes_hypothetical=optional_episodes, scenarios=scenarios,
        limitations=['No new work or amendment is registered by this forecast.',
            'Ideal four-slot sharing is a capacity estimate, not a scheduling or completion guarantee.',
            'Full-horizon timing includes every observed outcome. Short attempts remain in exposure costs, but do not set full-episode timing.',
            'Inflight episodes are conservatively charged a complete future episode; teacher recollection is charged40 until its recorded closure.',
            'RL physics equivalent excludes extra launch overhead from short failures; GPU timing is isolated, not three-learner contention.',
            'Two reporting hours are an explicit planning assumption, not measured media/audit completion.',
            'Three RL queues can hold leases; competing one-queue cohorts can cause idle capacity or starvation. Positive slack is insufficient to admit extra work.'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('snapshot', 'protocol', 'throughput', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--optional-episodes', type=int, default=144)
    a = p.parse_args()
    assert a.optional_episodes >= 0
    snapshot, protocol, throughput = read(a.snapshot), read(a.protocol), read(a.throughput)
    assert snapshot['protocol_sha256'] == digest(a.protocol)
    assert throughput['status'] == 'complete' and throughput['physics_steps'] == 0
    result = forecast(snapshot, protocol, throughput, a.optional_episodes)
    result.update(source_sha256=digest(Path(__file__)),
        inputs={str(path.resolve()): digest(path) for path in (a.snapshot, a.protocol, a.throughput)})
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(a.output), sha256=digest(a.output), scenarios=result['scenarios'])))


if __name__ == '__main__':
    main()
