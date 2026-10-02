"""Describe predeclared contact/efficiency metrics for every frozen method.

All-success and paired-success summaries have explicit denominators. No-contact
is NA. Do not use changed contact exposure or failed low-error runs as evidence
of superior compliance. This script never ranks or selects controllers.
"""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now

EVENTS = ('ball', 'human', 'rod', 'unknown_edge', 'pillar')
SCALARS = ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps', 'final_stable_placement_reached_s',
           'time_above_25mm_s', 'position_error_integral_m_s', 'absolute_joint_mechanical_work_j',
           'torque_total_variation_nm')


def stats(values):
    values = [float(v) for v in values if v is not None]
    assert all(np.isfinite(values))
    return dict(n=len(values), median=float(np.median(values)), minimum=min(values), maximum=max(values)) if values else dict(n=0, median=None, minimum=None, maximum=None)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--contact-windows',type=Path,required=True)
    a=p.parse_args(); report=json.loads(a.report.read_text()); rows=report['rows']; out=a.output.resolve()
    windows=json.loads(a.contact_windows.read_text());assert windows['report_sha256']==sha(a.report)
    index={(r['tier'],r['condition'],r['name']):r for r in windows['rows']}
    assert len(index)==len(rows)
    for row in rows:
        extra=index[(row['tier'],row['condition'],row['name'])];assert row['trace_sha256']==extra['trace_sha256']
        row['full_task_contact']={event:extra['events'][event]['full_observed_task'] for event in EVENTS}
        row['off_window_contact']={event:extra['events'][event]['off_window'] for event in EVENTS}
    out.mkdir(parents=True, exist_ok=False)
    groups=[]; pairs=[]; contact_rows=[]
    tiers=list(dict.fromkeys(r['tier'] for r in rows)); names=list(dict.fromkeys(r['name'] for r in rows))
    for tier in tiers:
        for name in names:
            sample=[r for r in rows if r['tier']==tier and r['name']==name]
            if not sample: continue
            strict=[r for r in sample if r['strict_success']]
            g=dict(tier=tier, name=name, n=len(sample), task=sum(r['task_success'] for r in sample),
                   strict=len(strict), full=sum(r['full_horizon'] for r in sample),
                   metrics_strict={key:stats([r[key] for r in strict]) for key in SCALARS}, contact={}, recovery={})
            for event in EVENTS:
                exposed=[r for r in strict if r['contact'][event]['exposure']]
                item=dict(all_exposed=sum(r['contact'][event]['exposure'] for r in sample),
                          strict_exposed=len(exposed), strict_unexposed=len(strict)-len(exposed),
                          **{key:stats([r['contact'][event][key] for r in exposed]) for key in
                             ('contact_p95_force_n', 'impulse_ns', 'contact_duration_s', 'peak_force_n')})
                g['contact'][event]=item
                contact_rows.append(dict(tier=tier,name=name,event=event,n=len(sample),strict=len(strict),
                    all_exposed=item['all_exposed'],strict_exposed=len(exposed),
                    **{key+'_'+measure:v[measure] for key,v in item.items() if isinstance(v,dict) for measure in ('median','minimum','maximum')}))
            for event in ('ball','human','rod'):
                records=[r['recovery'][event] for r in strict]
                g['recovery'][event]=dict(exposed=sum(x['exposed'] for x in records),
                    recovered=sum(x['settled_rejoin_time_s'] is not None for x in records),
                    right_censored=sum(x['right_censored'] for x in records),
                    rejoin_time_observed_only=stats([x['settled_rejoin_time_s'] for x in records]),
                    censored_observation_windows_s=[x['observation_window_s'] for x in records if x['right_censored']])
            g['rod_hold_gap_s']=stats([r['contact']['rod']['extended_no_contact_longest_s'] for r in strict])
            for scope in ('full_task_contact','off_window_contact'):
                g[scope]={}
                for event in EVENTS:
                    exposed=[r for r in strict if r[scope][event]['exposure']]
                    g[scope][event]=dict(strict_exposed=len(exposed),all_exposed=sum(r[scope][event]['exposure'] for r in sample),
                        **{key:stats([r[scope][event][key] for r in exposed]) for key in ('contact_p95_force_n','impulse_ns','contact_duration_s')})
            groups.append(g)
        for esn in ('recovery035_esn_fixed','recovery035_esn_seed2'):
            left={r['condition']:r for r in rows if r['tier']==tier and r['name']==esn}
            for other in names:
                if other==esn: continue
                right={r['condition']:r for r in rows if r['tier']==tier and r['name']==other}
                common=sorted(left.keys() & right.keys())
                if not common: continue
                success=[c for c in common if left[c]['strict_success'] and right[c]['strict_success']]
                paired=dict(tier=tier, esn=esn, other=other, common_conditions=common,
                            both_strict_conditions=success, n_common=len(common), n_both_strict=len(success),
                            esn_only_strict=sum(left[c]['strict_success'] and not right[c]['strict_success'] for c in common),
                            other_only_strict=sum(right[c]['strict_success'] and not left[c]['strict_success'] for c in common),
                            differences_esn_minus_other={}, contact={})
                for key in SCALARS:
                    paired['differences_esn_minus_other'][key]=stats([left[c][key]-right[c][key] for c in success])
                for event in EVENTS:
                    both=[c for c in success if left[c]['contact'][event]['exposure'] and right[c]['contact'][event]['exposure']]
                    paired['contact'][event]=dict(both_exposed_conditions=both,
                        different_exposure_conditions=[c for c in success if left[c]['contact'][event]['exposure'] != right[c]['contact'][event]['exposure']],
                        differences_esn_minus_other={key:stats([left[c]['contact'][event][key]-right[c]['contact'][event][key] for c in both])
                          for key in ('contact_p95_force_n','impulse_ns','contact_duration_s')})
                paired['full_task_contact']={}
                for event in EVENTS:
                    both=[c for c in success if left[c]['full_task_contact'][event]['exposure'] and right[c]['full_task_contact'][event]['exposure']]
                    paired['full_task_contact'][event]=dict(both_exposed_conditions=both,
                        differences_esn_minus_other={key:stats([left[c]['full_task_contact'][event][key]-right[c]['full_task_contact'][event][key] for c in both])
                          for key in ('contact_p95_force_n','impulse_ns','contact_duration_s')})
                pairs.append(paired)
    result=dict(created_utc=now(),source_sha256=sha(Path(__file__)),report_sha256=sha(a.report),contact_window_audit_sha256=sha(a.contact_windows),groups=groups,pairs=pairs,
                rules=['No combined score or model selection.', 'All tier denominators remain separate.',
                       'Both contact exposure and strict success are required for paired force differences.',
                       'Actual contact trajectories are not equalized; paired loads alone do not identify intrinsic compliance.',
                       'Recovery summaries are observed-only, with censoring denominators; not an unconditional recovery average.',
                       'Peak speed is reported, not maximized or minimized as a performance objective.',
                       'Two seed rows share physical conditions and are not independent environment replicates.'])
    write(out/'COMPLIANCE.json',result)
    with (out/'contacts.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(contact_rows[0]));w.writeheader();w.writerows(contact_rows)
    lines=['# Descriptive contact results', '', 'Only strict-success rows enter the force medians below. Each cell states the exposed denominator; no contact is NA.',
           'The first table in each tier uses predeclared commanded-event windows; the second reports supplementary full-task contacts including recontacts.',
           'Different actual contact duration/location still prevents a causal claim from lower forces alone.', '']
    for tier in tiers:
        lines += ['## '+tier,'','| Method | Strict / all | Human p95 N (exposed) | Rod p95 N (exposed) | Stable-placement time s |',
                  '|---|---:|---:|---:|---:|']
        for g in [v for v in groups if v['tier']==tier]:
            force=[]
            for event in ('human','rod'):
                item=g['contact'][event];m=item['contact_p95_force_n']['median']
                force.append(f'{m:.3f} ({item["strict_exposed"]}/{g["strict"]})' if m is not None else 'NA')
            value=g['metrics_strict']['final_stable_placement_reached_s']['median']
            time=f'{value:.3f}' if value is not None else 'NA'
            lines.append(f'| {g["name"]} | {g["strict"]}/{g["n"]} | {force[0]} | {force[1]} | {time} |')
        lines.append('')
        lines += ['### Full-task contact coverage supplement','','| Method | Strict / all | Human p95 N (exposed) | Rod p95 N (exposed) | Human off-window contacts (strict rows) |',
                  '|---|---:|---:|---:|---:|']
        for g in [v for v in groups if v['tier']==tier]:
            force=[]
            for event in ('human','rod'):
                item=g['full_task_contact'][event];m=item['contact_p95_force_n']['median']
                force.append(f'{m:.3f} ({item["strict_exposed"]}/{g["strict"]})' if m is not None else 'NA')
            lines.append(f'| {g["name"]} | {g["strict"]}/{g["n"]} | {force[0]} | {force[1]} | {g["off_window_contact"]["human"]["strict_exposed"]}/{g["strict"]} |')
        lines.append('')
    (out/'CONTACT_TABLE.md').write_text('\n'.join(lines))
    print(json.dumps(dict(groups=len(groups),paired_comparisons=len(pairs),contact_rows=len(contact_rows))))


if __name__=='__main__':
    main()
