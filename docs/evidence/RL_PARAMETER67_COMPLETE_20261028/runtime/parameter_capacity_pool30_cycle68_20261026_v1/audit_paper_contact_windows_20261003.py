"""Supplement commanded-event metrics with full-task and off-window contacts.

Predeclared event windows remain unchanged. This diagnostic was added after
development trace plots exposed late human recontacts; it is not a new gate,
selection criterion, or confirmatory superiority endpoint.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now


def describe(force,dt,mask):
    active=mask & (force>.05)
    return dict(exposure=bool(active.any()), contact_duration_s=float(dt[active].sum()),
                impulse_ns=float(np.sum(force[mask]*dt[mask])),
                peak_force_n=float(force[mask].max(initial=0)),
                contact_p95_force_n=float(np.percentile(force[active],95)) if active.any() else None)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();report=json.loads(a.report.read_text());rows=[]
    for row in report['rows']:
        run=Path(row['run']);assert sha(run/'rollout.npz')==row['trace_sha256']
        channels=json.loads((run/'research_channels.json').read_text())
        assert sha(run/'research_substeps.npz')==channels['telemetry_sha256']
        with np.load(run/'research_substeps.npz') as z:forces=z['contact_force_sum'].astype(float)
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:time=z['time'].astype(float);dt=z['dt'].astype(float)
        assert forces.shape==(len(time),6) and np.isfinite(forces).all() and np.all(forces>=0) and np.all(dt>0)
        result={}
        for event,column in (('ball',1),('human',2),('rod',3),('unknown_edge',4),('pillar',5)):
            original=row['contact'][event];start,end=original['window_s']
            window=(time>=start)&(time<=end);force=forces[:,column]
            within=describe(force,dt,window);outside=describe(force,dt,~window);full=describe(force,dt,np.ones(len(time),bool))
            for key,value in within.items():
                if value is None or isinstance(value,bool):assert value==original[key]
                else:np.testing.assert_allclose(value,original[key],rtol=0,atol=1e-8)
            for key in ('contact_duration_s','impulse_ns'):
                np.testing.assert_allclose(within[key]+outside[key],full[key],rtol=0,atol=1e-8)
            outside_indices=np.flatnonzero((~window)&(force>.05))
            result[event]=dict(predeclared_window_s=[start,end],predeclared=within,full_observed_task=full,off_window=outside,
                first_off_window_contact_s=float(time[outside_indices[0]]) if len(outside_indices) else None,
                last_off_window_contact_s=float(time[outside_indices[-1]]) if len(outside_indices) else None)
        rows.append(dict(name=row['name'],tier=row['tier'],condition=row['condition'],run=str(run),
            task_success=row['task_success'],strict_success=row['strict_success'],full_horizon=row['full_horizon'],
            trace_sha256=row['trace_sha256'],research_sha256=channels['telemetry_sha256'],
            force_semantics=channels['force_semantics'],events=result))
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),report_sha256=sha(a.report),rows=rows,
        declaration='2026-10-02 after development trace inspection; supplementary measurement-coverage audit only. Does not replace predeclared windows or select models.',
        limitation='Full observed horizon for aborts is shorter; not a complete 55s force comparison. Sum of magnitudes integrated over time is not net momentum change. Event-specific metrics may miss later contacts; all-horizon values are supplied transparently.'))
    print(json.dumps(dict(episodes=len(rows),with_off_window_human=sum(r['events']['human']['off_window']['exposure'] for r in rows))))


if __name__=='__main__':main()
