"""Compare archived upstream trajectories to new same-runtime reproductions."""
import argparse,json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream',type=Path,required=True);p.add_argument('--phase',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    protocol=json.loads((a.upstream/'PROTOCOL.json').read_text())
    ids={x['id'] for x in protocol['cases']};state=json.loads((a.phase/'execution.json').read_text())
    assert state['status']=='complete'
    rows=[];unmatched=[]
    for entry in state['rows']:
        name=entry['name']
        if name not in ids:unmatched.append(name);continue
        old=a.upstream/name;new=a.phase/name
        original=json.loads((old/'rollout.json').read_text());current=json.loads((new/'rollout.json').read_text())
        assert original['model_sha256']==current['model_sha256']
        channels={}
        with np.load(old/'rollout.npz') as x,np.load(new/'rollout.npz') as y:
            for key in ('time','observation','applied_action','qpos','qvel','ctrl','object_position','stage'):
                if key not in x.files or key not in y.files:continue
                u,v=x[key],y[key];same_shape=u.shape==v.shape
                channels[key]=dict(shape_original=list(u.shape),shape_current=list(v.shape),
                    exact_equal=bool(np.array_equal(u,v)),max_abs=float(np.max(abs(u.astype(float)-v))) if same_shape else None,
                    first_max_abs=float(np.max(abs(u[0].astype(float)-v[0]))) if u.shape[1:]==v.shape[1:] else None)
        statuses={key:dict(original=original.get(key),current=current.get(key),equal=original.get(key)==current.get(key))
                  for key in ('task_success','strict_success','full_task_horizon_completed','final_task_stage','abort_reason')}
        rows.append(dict(name=name,channels=channels,statuses=statuses,model_sha256=current['model_sha256'],
                         original_trace_sha256=sha(old/'rollout.npz'),current_trace_sha256=sha(new/'rollout.npz')))
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),rows=rows,unmatched_added_baselines=unmatched,
                        all_compared_channels_exact=all(c['exact_equal'] for r in rows for c in r['channels'].values()),
                        limitation='Exact equality checks reproduction on archived trajectories only; does not establish task success or physical realism.'))
    print(json.dumps(dict(rows=len(rows),exact=all(c['exact_equal'] for r in rows for c in r['channels'].values()))))

if __name__=='__main__':main()
