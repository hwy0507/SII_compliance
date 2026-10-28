"""Complete paired final tables and figures, without a weighted winner score."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--supplementary',action='store_true')
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    lockpath=root/'final_model_lock/VALIDATION_LOCK.json';lock=json.loads(lockpath.read_text())
    assert lock['status']=='models_frozen_before_final_evaluation'
    candidates=lock['candidates'];names=[c['name'] for c in candidates];rows=[];audit_hashes={}
    def row_from(phase,name,tier,condition):
        run=root/phase/name;analysis=root/('_analysis' if phase=='native_anchor' else phase+'_analysis')
        state=json.loads((analysis/'execution.json').read_text());assert state['status']=='complete'
        auditpath=analysis/'INDEPENDENT_AUDIT.json';audit_hashes[str(auditpath)]=sha(auditpath)
        audit=json.loads(auditpath.read_text());assert not audit['pending']
        physical=next(r for r in audit['rows'] if Path(r['run']).name==name)
        assert physical['frozen_source_hashes_verified'] and physical['actuator_amplitude_and_command_slew_valid']
        summary=json.loads((run/'rollout.json').read_text());metricpath=analysis/(name+'.metrics.json')
        execution=json.loads((run/'execution.json').read_text())
        development=Path(next(e['development_run'] for e in lock['development_evidence'] if e['name']==name))
        original=json.loads((development/'execution.json').read_text())
        candidate=next(c for c in candidates if c['name']==name)
        assert execution['config']==original['config']==candidate.get('config',{})
        assert execution['checkpoint_sha256']==original['checkpoint_sha256']==candidate.get('checkpoint_sha256')
        frozen=original['runtime_provenance'];current=execution['runtime_provenance']
        if candidate.get('rl_case'):
            for key in ('case','bridge_sha256','policy_source_sha256'):
                assert current[key]==frozen[key], 'RL changed after development: '+key
            original_policy=json.loads((development/'rollout.json').read_text())['baseline_policy']
            actual_policy=summary['baseline_policy']
            assert actual_policy['normalization_hash']==original_policy['normalization_hash']
            assert actual_policy['normalizers_unchanged'] and actual_policy['training'] is False
        elif candidate.get('controller'):
            for key in ('parameter_prior','parameter_source_sha256','controller'):
                assert current[key]==frozen[key], 'Classical law/prior changed: '+key
        elif candidate.get('checkpoint'):
            assert summary['arguments']['teacher']=='none' and summary['arguments']['esn_mode']=='control'
        metric=json.loads(metricpath.read_text());assert physical['trace_sha256']==metric['trace_sha256']==sha(run/'rollout.npz')
        row=dict(name=name,tier=tier,condition=condition,run=str(run),
                 task_success=physical['task_success'],strict_success=physical['strict_success'],
                 full_horizon=physical['full_horizon'],stage=physical['stage'],abort_reason=physical['abort_reason'],
                 rmse_mm=physical['rmse_mm'],peak_torque_nm=physical['peak_torque_nm'],
                 peak_speed_mps=physical['peak_speed_mps'],penetration_mm=physical['penetration_mm'],
                 edge_penetration_mm=physical['edge_penetration_mm'],final_xy_mm=physical['placement_error_xy_m']*1000,
                 placement_hold_s=summary['placement_hold_s'],
                 final_stable_placement_reached_s=55-summary['placement_hold_s']+.5 if physical['task_success'] else None,
                 duration_s=metric['duration_s'],trace_sha256=metric['trace_sha256'],
                 position_error_integral_m_s=metric['position_error_integral_m_s'],
                 time_above_25mm_s=metric['time_above_25mm_s'],
                 absolute_joint_mechanical_work_j=metric['absolute_joint_mechanical_work_j'],
                 torque_total_variation_nm=sum(metric['torque_total_variation_nm_by_joint']),
                 model_sha256=metric['model_sha256'],metrics_sha256=sha(metricpath),
                 frozen_model_configuration_verified=True,
                 contact=metric['contact'],recovery=metric['recovery'])
        row['failure_reasons']=('; '.join(filter(None,[
            physical['abort_reason'],
            'no_final_released_stable_placement' if not physical['task_success'] else None,
            'external_penetration_above_0.2mm' if physical['penetration_mm']>.2 else None,
            'edge_penetration_above_0.2mm' if physical['edge_penetration_mm']>.2 else None,
        ])) if not physical['strict_success'] else '')
        for event,m in metric['contact'].items():
            for key in ('exposure','contact_p95_force_n','contact_duration_s','impulse_ns','extended_no_contact_longest_s'):
                row[event+'_'+key]=m.get(key)
        return row
    for e in lock['development_evidence']:
        rows.append(row_from(Path(e['development_run']).parent.name,e['name'],'development','anchor'))
    for condition in ('h1','h2','h3','h4'):
        phase='heldout_'+condition;state=json.loads((root/phase/'execution.json').read_text())
        assert state['status']=='complete' and state['validation_lock_sha256']==sha(lockpath)
        assert [r['name'] for r in state['rows']]==names
        for name in names:rows.append(row_from(phase,name,'heldout_development_dt',condition))
    formal=json.loads((root/'final_model_lock/formal_manifest.json').read_text())['candidates']
    seen=[]
    for phase in sorted(root.glob('formal_[1-4]')):
        state=json.loads((phase/'execution.json').read_text());assert state['status']=='complete'
        assert state['validation_lock_sha256']==sha(lockpath)
        for entry in state['rows']:
            seen.append(entry['name']);rows.append(row_from(phase.name,entry['name'],'formal_resolution','anchor'))
    assert sorted(seen)==sorted(c['name'] for c in formal) and len(seen)==len(set(seen))
    if a.supplementary:
        supplement=json.loads((root/'sensitivity_coordinator/execution.json').read_text())
        assert supplement['status']=='complete' and supplement['validation_lock_sha256']==sha(lockpath)
        for condition in ('s1','s2','s3','s4','s5','s6','s7','s8'):
            phase='random_'+condition;state=json.loads((root/phase/'execution.json').read_text())
            assert state['status']=='complete' and state['validation_lock_sha256']==sha(lockpath)
            assert [r['name'] for r in state['rows']]==[c['name'] for c in formal]
            for candidate in formal:rows.append(row_from(phase,candidate['name'],'supplementary_random_dt',condition))
    groups=[]
    for name in names:
        sample=[r for r in rows if r['name']==name and r['tier']=='heldout_development_dt']
        complete=[r for r in sample if r['full_horizon']];strict=[r for r in sample if r['strict_success']]
        group=dict(name=name,n=4,task_successes=sum(r['task_success'] for r in sample),
                   strict_successes=len(strict),full_horizon_count=len(complete),
                   failure_stages=[dict(condition=r['condition'],stage=r['stage'],abort=r['abort_reason'],
                       task=r['task_success'],strict=r['strict_success']) for r in sample if not r['strict_success']])
        for label,subset in (('all_full_horizon',complete),('strict_only',strict)):
            group[label]={key:dict(median=float(np.median([r[key] for r in subset])),
                                  minimum=min(r[key] for r in subset),maximum=max(r[key] for r in subset)) if subset else None
                          for key in ('rmse_mm','peak_torque_nm','peak_speed_mps','penetration_mm')}
        groups.append(group)
    supplementary_groups=[]
    if a.supplementary:
        for candidate in formal:
            sample=[r for r in rows if r['name']==candidate['name'] and r['tier']=='supplementary_random_dt']
            assert len(sample)==8
            supplementary_groups.append(dict(name=candidate['name'],n=8,
                task_successes=sum(r['task_success'] for r in sample),strict_successes=sum(r['strict_success'] for r in sample),
                full_horizon_count=sum(r['full_horizon'] for r in sample),
                conditions=[{k:r[k] for k in ('condition','task_success','strict_success','stage','abort_reason','rmse_mm',
                            'peak_torque_nm','peak_speed_mps','penetration_mm','edge_penetration_mm','final_xy_mm')} for r in sample]))
    paired=[]
    for seed,left,right in ((1,'recovery035_esn_fixed','paired_feature_matched_rnn'),
                            (2,'recovery035_esn_seed2','paired_feature_matched_rnn_seed2')):
        for condition in ('h1','h2','h3','h4')+(('s1','s2','s3','s4','s5','s6','s7','s8') if a.supplementary else ()):
            x=next(r for r in rows if r['name']==left and r['condition']==condition)
            y=next(r for r in rows if r['name']==right and r['condition']==condition)
            pair=dict(seed=seed,condition=condition,tier=x['tier'],esn_strict=x['strict_success'],rnn_strict=y['strict_success'],
                      both_strict=x['strict_success'] and y['strict_success'],deltas_esn_minus_rnn={})
            if pair['both_strict']:
                for key in ('rmse_mm','peak_torque_nm','peak_speed_mps','final_stable_placement_reached_s'):
                    pair['deltas_esn_minus_rnn'][key]=x[key]-y[key]
                for event in ('human','rod','unknown_edge','pillar'):
                    xc=x['contact'][event];yc=y['contact'][event]
                    pair['deltas_esn_minus_rnn'][event+'_p95_force_n']=(xc['contact_p95_force_n']-yc['contact_p95_force_n']
                        if xc['exposure'] and yc['exposure'] else None)
                    pair['deltas_esn_minus_rnn'][event+'_impulse_ns']=(xc['impulse_ns']-yc['impulse_ns']
                        if xc['exposure'] and yc['exposure'] else None)
            paired.append(pair)
    result=dict(created_utc=now(),source_sha256=sha(Path(__file__)),validation_lock_sha256=sha(lockpath),
                rows=rows,heldout_summary=groups,supplementary_random_summary=supplementary_groups,
                paired_esn_rnn=paired,independent_audit_hashes=audit_hashes,
                limitations=['Four predeclared paired perturbations are not independent random population draws.',
                    'Two initialization seeds are paired, not extra independent environments.',
                    'Development exposure and parameter counts differ; feature-matched RNN warm-start is disclosed.',
                    'Formal-resolution eligibility is development strict success, not a new model-selection rule.',
                    'No-contact is NA for contact comparisons; lower loads may reflect changed exposure.',
                    'Supplementary random conditions include development-qualified models only. Noneligible methods are untested, not failures. Do not pool this cohort with the four designed conditions or formal resolution.',
                    'All failed and aborted episodes remain in success denominators; short-run RMSE is not mixed into full-horizon medians.'])
    write(out/'results.json',result)
    keys=[k for k,v in rows[0].items() if not isinstance(v,(dict,list))]
    with (out/'episodes.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)
    lines=['# Frozen final validation','',f'{len(names)} models × four paired conditions; {len(formal)} development-qualified formal reruns.','',
           '| Model | Development task/strict | Heldout task/strict (n=4) | Formal task/strict | Full 55s | RMSE median/range mm (full runs) |',
           '|---|---|---|---|---|---|']
    verdict=lambda r:f"{int(r['task_success'])}/{int(r['strict_success'])}"
    for g in groups:
        dev=next(r for r in rows if r['name']==g['name'] and r['tier']=='development')
        formalrow=next((r for r in rows if r['name']==g['name'] and r['tier']=='formal_resolution'),None)
        m=g['all_full_horizon']['rmse_mm'];label=f"{m['median']:.3f} [{m['minimum']:.3f}, {m['maximum']:.3f}]" if m else 'NA'
        lines.append(f"| {g['name']} | {verdict(dev)} | {g['task_successes']}/{g['strict_successes']} | {verdict(formalrow) if formalrow else 'not eligible'} | {g['full_horizon_count']}/4 | {label} |")
    lines+=['','Task and strict counts are separate. The table includes all frozen models, not only successes.',
            'Formal is the anchor at 5e-5 s; the four paired perturbations use 1e-4 s and must not be pooled with formal.','']
    if a.supplementary:
        lines+=['## Supplementary random conditions (development-qualified models only)','',
                '| Model | Task / 8 | Strict / 8 | Full 55s / 8 |','|---|---:|---:|---:|']
        for g in supplementary_groups:
            lines.append(f"| {g['name']} | {g['task_successes']} | {g['strict_successes']} | {g['full_horizon_count']} |")
        lines+=['','All other models were not eligible and are not counted as failures in this supplementary cohort.','']
    (out/'TABLE.md').write_text('\n'.join(lines))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,BoundaryNorm
    columns=[('development','anchor'),*[('heldout_development_dt',c) for c in ('h1','h2','h3','h4')],('formal_resolution','anchor')]
    values=np.full((len(names),6),-1.);labels=np.full((len(names),6),'—',dtype='<U8')
    for i,name in enumerate(names):
        for j,(tier,condition) in enumerate(columns):
            row=next((r for r in rows if r['name']==name and r['tier']==tier and r['condition']==condition),None)
            if row is None:continue
            values[i,j]=2 if row['strict_success'] else 1 if row['task_success'] else 0
            labels[i,j]='S' if row['strict_success'] else 'T' if row['task_success'] else 'F' if row['full_horizon'] else 'ABORT'
    fig,ax=plt.subplots(figsize=(13,12));ax.imshow(values,aspect='auto',cmap=ListedColormap(['#e5e7eb','#efb5b5','#f5d68b','#99cfb3']),norm=BoundaryNorm([-1.5,-.5,.5,1.5,2.5],4))
    ax.set_xticks(range(6),['Dev anchor','h1','h2','h3','h4','Formal anchor\n5e-5 s'])
    ax.set_yticks(range(len(names)),names,fontsize=8)
    for i in range(len(names)):
        for j in range(6):ax.text(j,i,labels[i,j],ha='center',va='center',fontsize=8)
    ax.set_title('All frozen models: S = strict success; T = task only; F = failure\nGray = not development-qualified for formal; all failures retained',fontsize=11)
    fig.tight_layout();fig.savefig(out/'success_matrix.png',dpi=160);fig.savefig(out/'success_matrix.pdf');plt.close(fig)
    if a.supplementary:
        values=np.zeros((len(formal),8));labels=np.full((len(formal),8),'F',dtype='<U8')
        for i,candidate in enumerate(formal):
            for j,condition in enumerate(('s1','s2','s3','s4','s5','s6','s7','s8')):
                row=next(r for r in rows if r['name']==candidate['name'] and r['condition']==condition)
                values[i,j]=2 if row['strict_success'] else 1 if row['task_success'] else 0
                labels[i,j]='S' if row['strict_success'] else 'T' if row['task_success'] else 'F' if row['full_horizon'] else 'ABORT'
        fig,ax=plt.subplots(figsize=(13,5));ax.imshow(values,aspect='auto',cmap=ListedColormap(['#efb5b5','#f5d68b','#99cfb3']),norm=BoundaryNorm([-.5,.5,1.5,2.5],3))
        ax.set_xticks(range(8),['s'+str(i+1) for i in range(8)]);ax.set_yticks(range(len(formal)),[c['name'] for c in formal],fontsize=8)
        for i in range(len(formal)):
            for j in range(8):ax.text(j,i,labels[i,j],ha='center',va='center',fontsize=9)
        ax.set_title('Predeclared random perturbations, development-qualified frozen models only\nS = strict; T = task only; F = failure. Other methods not tested in this cohort.',fontsize=11)
        fig.tight_layout();fig.savefig(out/'supplementary_success_matrix.png',dpi=160);fig.savefig(out/'supplementary_success_matrix.pdf');plt.close(fig)
    print(json.dumps(dict(models=len(names),episodes=len(rows),heldout_episodes=4*len(names),formal_episodes=len(formal),supplementary_episodes=8*len(formal) if a.supplementary else 0)))


if __name__=='__main__':main()
