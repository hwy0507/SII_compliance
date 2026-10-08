"""Read-only descriptive failure audit. No policy fitting or new simulation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import numpy as np


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    receipts=[json.loads(p.read_text()) for p in sorted((a.root/'episodes').glob('*.execution.json'))]
    rows=[]
    for d in receipts:
        if d['status']!='complete':continue
        run=a.root/'episodes'/d['name'];audit=d['audit']
        assert sha(run/'rollout.npz')==d['trace_sha256']
        with np.load(run/'rollout.npz',allow_pickle=False) as z:
            tail=z['time']>=z['time'][-1]-5.
            stages=z['stage']; changes=np.r_[0,1+np.flatnonzero(np.diff(stages))]
            row=dict(family=d['family'],condition=d['condition_id'],stage=audit['stage'],
                task=audit['task_success'],strict=audit['strict_success'],full_horizon=audit['full_horizon'],
                placement_error_mm=1000*audit['placement_error_xy_m'],
                final_stage_since_s=float(z['time'][changes[-1]]),
                final_stage_duration_s=float(z['time'][-1]-z['time'][changes[-1]]),
                tail_position_error_mm=float(np.median(z['task_position_error_m'][tail])*1000),
                tail_rotation_error_rad=float(np.median(z['task_rotation_error_rad'][tail])),
                tail_speed_mm_s=float(np.median(z['task_speed_mps'][tail])*1000),
                tail_action_median=np.median(z['applied_action'][tail],axis=0).tolist(),
                trace_sha256=d['trace_sha256'],audit_sha256=d['audit_sha256'])
        with np.load(run/'execution_chain.npz',allow_pickle=False) as z:
            row.update(slew_limited_fraction=float(np.mean(z['slew_limited'])),
                median_wbc_scale=float(np.median(z['wbc_scale'])),
                requested_action_bound_fraction=float(np.mean(np.max(abs(z['requested_action']),axis=1)>=.95)))
        metric=json.loads(Path(d['metrics']).read_text())
        row['final_route_cursor']=metric['final_route_cursor']
        row['contact_exposed']={k:v['exposure'] for k,v in metric['contact'].items()}
        # The first registered condition is an anchor, not selected by outcome.
        if d['condition_id']=='office_v7_24_000':
            channel=json.loads((run/'research_channels.json').read_text())
            assert sha(run/'research_substeps.npz')==channel['telemetry_sha256']
            with np.load(run/'research_substeps.npz',allow_pickle=False) as z:
                force=z['contact_force_sum'][-100000:]  # 5 seconds at frozen 5e-5 dt
                row['anchor_tail_contact_mean_n']=dict(zip(channel['force_columns'],
                    np.mean(force,axis=0,dtype=np.float64).tolist()))
                row['anchor_tail_contact_max_n']=dict(zip(channel['force_columns'],
                    np.max(force,axis=0).tolist()))
            row['research_metrics_sha256']=channel['telemetry_sha256']
        rows.append(row)
    groups=[]
    for c in json.loads((a.root/'MODEL_MANIFEST.json').read_text())['candidates']:
        rr=[r for r in rows if r['family']==c['family']]
        g=dict(family=c['family'],completed=len(rr),task=sum(r['task'] for r in rr),
               strict=sum(r['strict'] for r in rr),stage_counts=dict(Counter(r['stage'] for r in rr)))
        for k in ('tail_position_error_mm','tail_rotation_error_rad','tail_speed_mm_s',
                  'slew_limited_fraction','median_wbc_scale','requested_action_bound_fraction',
                  'final_stage_duration_s','placement_error_mm'):
            g[k]=statistics.fmean(r[k] for r in rr) if rr else None
        groups.append(g)
    result=dict(source_sha256=sha(Path(__file__)),protocol_sha256=sha(a.root/'PROTOCOL.json'),
                completed=len(rows),families=groups,rows=rows,
                limitation='Descriptive audit of completed public assessment traces; not a counterfactual or training set. Tail is last observed 5s; no gate changes.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(groups,indent=2))


if __name__=='__main__':main()
