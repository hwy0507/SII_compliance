"""Prospective six-metric contract for isolated special scenes, not office gates."""
import math
import statistics


def completion_time(time, gate):
    """Confirm the terminal uninterrupted success suffix after 13 samples.

    At 25 Hz, 13 sampled states span 0.48 s. This is a sampled hold,
    not a claim of uninterrupted success at every physics substep.
    """
    assert len(time) == len(gate) > 0
    assert all(math.isfinite(t) for t in time)
    assert all(abs((b-a)-.04) < 1e-8 for a,b in zip(time,time[1:]))
    if not gate[-1]:
        return None
    start = max((i+1 for i,v in enumerate(gate) if not v), default=0)
    return float(time[start+12]) if len(time)-start >= 13 else None


def aggregate(rows, expected_cases):
    """All registered cells must exist once; no dropping unsuccessful episodes."""
    keys = [(r['method'],r['condition']) for r in rows]
    assert len(keys) == len(set(keys)) == len(expected_cases)
    assert set(keys) == set(expected_cases)
    for r in rows:
        assert r['scene'] in ('rod','ball','corner')
        assert not r['strict_success'] or r['task_success']
        if r['task_success']:
            assert isinstance(r['completion_time_s'],(int,float)) and math.isfinite(r['completion_time_s']) and r['completion_time_s'] > 0, 'Task success missing valid sampled hold completion'
        assert math.isfinite(r['peak_torque_nm']) and r['peak_torque_nm'] >= 0
        assert 0 <= r['proxy_below_threshold_s'] <= r['proxy_contact_s']
        assert r['human_contact_s'] is None, 'No human-force channel in this protocol; do not fabricate human contact time'
    both = [r for r in rows if r['task_success'] and r['strict_success']]
    tref = min((r['completion_time_s'] for r in both),default=None)
    groups = []
    for method in sorted({r['method'] for r in rows}):
        group = [r for r in rows if r['method']==method]
        good = [r for r in group if r['task_success'] and r['strict_success']]
        contact = sum(r['proxy_contact_s'] for r in group)
        compliant = sum(r['proxy_below_threshold_s'] for r in group)
        groups.append(dict(method=method,episodes=len(group),task_success=sum(r['task_success'] for r in group),
            strict_success=sum(r['strict_success'] for r in group),both_success=len(good),
            task_rate=sum(r['task_success'] for r in group)/len(group),
            strict_rate=sum(r['strict_success'] for r in group)/len(group),
            spt_both_conditional=statistics.mean(tref/max(tref,r['completion_time_s']) for r in good) if good else None,
            completion_time_both_mean_s=statistics.mean(r['completion_time_s'] for r in good) if good else None,
            peak_torque_mean_nm=statistics.mean(r['peak_torque_nm'] for r in group),
            human_comfort=None,human_contact_s=None,
            disturbance_contact_proxy_contact_s=contact,
            disturbance_contact_proxy_compliance=compliant/contact if contact else None,
            machine_compliance_rate=sum(r['machine_compliant'] for r in group)/len(group)))
    return dict(t_ref_s=tref,episodes=len(rows),methods=groups)
