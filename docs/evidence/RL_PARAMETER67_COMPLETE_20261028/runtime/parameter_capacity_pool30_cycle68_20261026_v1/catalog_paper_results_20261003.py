"""Snapshot all registered rows, including failures and pending evaluations.

This is an evidence index, not a post-hoc weighted ranking or an independent
physics audit. Completed audit/metric sources are linked by exact hashes.
"""
import argparse,collections,csv,json
from pathlib import Path
from optimize_tool_contact_20261002 import sha,write,now

FIELDS=('task_success','strict_success','full_horizon','stage','rmse_mm','peak_torque_nm',
        'peak_speed_mps','penetration_mm','edge_penetration_mm','placement_error_xy_m','abort_reason')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phases',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--analyses',type=Path,nargs='*',default=[])
    p.add_argument('--allow-running',action='store_true')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    analyses={}
    for path in a.analyses:
        record=json.loads((path/'execution.json').read_text())
        if record['status']!='complete':raise ValueError('Only completed analyses: '+str(path))
        analyses[str(Path(record['phase']).resolve())]=path
    rows=[];phases=[]
    for phase in a.phases:
        phase=phase.resolve();record=json.loads((phase/'execution.json').read_text())
        if record['status']=='running' and not a.allow_running:raise ValueError('Batch still running: '+str(phase))
        manifest=json.loads((phase/'manifest.json').read_text())
        candidates={c['name']:c for c in manifest['candidates']}
        actual={r['name']:r for r in record['rows']}
        names=record.get('selected_candidate_names',list(actual))
        for name in names:
            candidate=candidates[name];row=dict(phase=phase.name,name=name,category=candidate['category'],
                run=str(phase/name),state='not_started',checkpoint_sha256=candidate.get('checkpoint_sha256'),
                manifest_sha256=sha(phase/'manifest.json'),**{f:None for f in FIELDS})
            if name in actual:
                entry=actual[name];row.update(started_utc=entry['started_utc'],ended_utc=entry.get('ended_utc'),returncode=entry.get('returncode'))
                row['state']='running' if entry.get('returncode') is None else ('complete' if entry['returncode']==0 else 'failed_preserved')
                audit=phase/name/'AUDIT.json'
                if audit.exists():
                    result=json.loads(audit.read_text());row.update({f:result.get(f) for f in FIELDS})
                    row.update(audit_sha256=sha(audit),trace_sha256=result['trace_sha256'])
                    summary=phase/name/'rollout.json';s=json.loads(summary.read_text())
                    row['placement_hold_s']=s.get('placement_hold_s')
                    row['final_stable_placement_reached_s']=(s['arguments']['duration']-s['placement_hold_s']+.5 if s['task_success'] else None)
                    row['success_definition']=s['success_definition']
                analysis=analyses.get(str(phase))
                if analysis is not None:
                    metrics=analysis/(name+'.metrics.json')
                    if metrics.exists():
                        measured=json.loads(metrics.read_text());assert measured['trace_sha256']==row['trace_sha256']
                        row['contact_metrics_sha256']=sha(metrics)
                        row['contact']=measured['contact'];row['recovery']=measured['recovery']
                        for event,item in measured['contact'].items():
                            for key in ('exposure','contact_duration_s','impulse_ns','contact_p95_force_n','extended_no_contact_longest_s'):
                                row[event+'_'+key]=item.get(key)
            rows.append(row)
        phases.append(dict(path=str(phase),status=record['status'],execution_sha256=sha(phase/'execution.json')))
    counts=collections.Counter(r['state'] for r in rows)
    result=dict(created_utc=now(),source_sha256=sha(Path(__file__)),phases=phases,rows=rows,status_counts=dict(counts),
                task_success=sum(r['task_success'] is True for r in rows),strict_success=sum(r['strict_success'] is True for r in rows),
                registered_count=len(rows),limitation='All listed registered rows retained. This catalog does not rank methods or equalize training exposure. Pending rows are not failures or successes. Stable-placement time is final qualifying interval start plus 0.5s, not necessarily first-ever placement.')
    write(out/'catalog.json',result)
    keys=list(dict.fromkeys(k for row in rows for k,v in row.items() if not isinstance(v,(dict,list))))
    with (out/'catalog.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:result[k] for k in ('registered_count','status_counts','task_success','strict_success')}))

if __name__=='__main__':main()
