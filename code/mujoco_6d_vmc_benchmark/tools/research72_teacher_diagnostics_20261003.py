"""Read-only timing/exposure diagnostics on completed training identities only.

Contact truth is used for offline analysis, never for actor or imitation targets.
These are associations; short-latency impacts do not alone prove unavoidability.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for path in sorted((a.root/'teacher_bank').glob('queue_*/train_*/AUDIT.json')):
        run=path.parent;audit=json.loads(path.read_text());state=json.loads((run/'execution.json').read_text())
        assert state['status']=='complete' and state['runtime_provenance']['data_role']=='train'
        assert sha(run/'rollout.npz')==audit['trace_sha256']
        with np.load(run/'research_substeps.npz') as z:
            force=z['contact_force_sum'][:,5].copy();pen=z['external_penetration_m'].copy()
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            time=z['time'].copy();velocity=z['twist'][:,:3].copy()
        active=np.flatnonzero(force>.05);peak=int(np.argmax(pen))
        row=dict(condition_id=run.name,task=audit['task_success'],strict=audit['strict_success'],
            worst_pair=audit['worst_pair'],max_external_penetration_mm=float(pen[peak]*1000),
            peak_penetration_time_s=float(time[peak]),pillar_peak_force_n=float(force.max()),
            pillar_exposed=bool(len(active)),source_run=str(run),trace_sha256=audit['trace_sha256'],
            physics_sha256=sha(run/'research_substeps.npz'),metrics_sha256=audit['metrics_sha256'])
        if len(active):
            first=int(active[0]);t0=float(time[first]);window=(time>=max(0,t0-.04))&(time<=t0)
            with np.load(run/'rollout.npz') as z:
                clock=z['neuron_time'].copy();obs=z['observation'].copy();requests=z['applied_action'].copy()
            with np.load(run/'execution_chain.npz') as z:filtered=z['filtered_action'].copy()
            before=max(0,int(np.searchsorted(clock,t0,side='right')-1));after=np.flatnonzero((clock>=t0)&(clock<=t0+.16))
            row.update(first_pillar_contact_s=t0,hand_peak_speed_last40ms_mps=float(np.linalg.norm(velocity[window],axis=1).max(initial=0.)),
                previous_actor_time_s=float(clock[before]),time_since_actor_s=t0-float(clock[before]),
                precontact_estimated_wrench=obs[before,39:45].tolist(),precontact_request=requests[before].tolist(),
                precontact_filtered_action=filtered[before].tolist(),postcontact_actor_times_s=clock[after].tolist(),
                postcontact_estimated_wrench=obs[after,39:45].tolist(),postcontact_requests=requests[after].tolist(),
                peak_penetration_relative_to_first_pillar_s=float(time[peak]-t0),
                pillar_p95_active_force_n=float(np.percentile(force[active],95)))
        rows.append(row)
    assert len(rows)==32
    result=dict(completed_utc=now(),source_sha256=sha(Path(__file__)),rows=rows,
        count=len(rows),task=sum(r['task'] for r in rows),strict=sum(r['strict'] for r in rows),
        failed_worst_pairs=dict(Counter(str(r['worst_pair']) for r in rows if not r['strict'])),
        limitations='Training identities only; hand speed is not link7 normal approach speed. Aggregate external peak may belong to another contact than first pillar. Timing association is not a causal impossibility proof. No diagnostics fed to actor.')
    write(out/'DIAGNOSTICS.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main()
