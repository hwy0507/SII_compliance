"""One-shot sequential final reports, state/contact audits and complete media.

Waits for the already-running frozen validation jobs. Never starts simulations
or fitting. All h1 models and all formal-eligible models are rendered regardless
of outcome, with aborted histories at their real duration. Not a timer service.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT, sha, write, now

DEADLINE=datetime(2026,10,3,2,11,36,tzinfo=timezone.utc)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=root/'final_delivery_coordinator';out.mkdir(exist_ok=False)
    state=dict(status='running',started_utc=now(),argv=sys.argv,source_sha256=sha(Path(__file__)),steps=[],
               operations='Postprocess only. No fitting, tuning, physical integration or scheduled invocation.')
    def save():write(out/'execution.json',state)
    def wait_for(relative):
        while True:
            check=json.loads((root/relative/'execution.json').read_text())
            if check['status']!='running':break
            if datetime.now(timezone.utc)>=DEADLINE:raise RuntimeError('Authorized deadline while waiting for '+relative)
            time.sleep(15)
        assert check['status']=='complete','Preserve incomplete upstream evidence: '+relative
        state[relative+'_sha256']=sha(root/relative/'execution.json');save()
    def run(tool,args,label):
        assert datetime.now(timezone.utc)<DEADLINE
        source=ROOT/'tools'/tool;command=[sys.executable,str(source),*map(str,args)]
        entry=dict(label=label,command=command,source_sha256=sha(source),started_utc=now())
        state['steps'].append(entry);save()
        with (out/(label+'.log')).open('x') as log:
            proc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        entry.update(returncode=proc.returncode,ended_utc=now());save()
        assert proc.returncode==0,label+' failed; preserve outputs'
        assert sha(source)==entry['source_sha256']
    save()
    try:
        wait_for('final_validation_coordinator')
        run('report_paper_final_validation_20261003.py',['--root',root,'--output',root/'primary_final_report'],'primary_report')
        primary=json.loads((root/'primary_final_report/results.json').read_text())
        for tier,condition,folder in (('heldout_development_dt','h1','media_final_h1'),('formal_resolution','anchor','media_formal')):
            selected=[r for r in primary['rows'] if r['tier']==tier and r['condition']==condition]
            expected=26 if tier=='heldout_development_dt' else 7;assert len(selected)==expected
            display='h1 dt=1e-4' if tier=='heldout_development_dt' else 'formal anchor dt=5e-5'
            run('render_paper_gallery_20261003.py',['--runs',*[r['run'] for r in selected],
                '--labels',*[display+' / '+r['name'] for r in selected],'--output',root/folder,'--allow-aborted'],folder)
        gallery=json.loads((root/'media_final_h1/execution.json').read_text())
        by_name={Path(r['run']).name:r for r in gallery['rows']}
        for seed,left,right in ((1,'recovery035_esn_fixed','paired_feature_matched_rnn'),(2,'recovery035_esn_seed2','paired_feature_matched_rnn_seed2')):
            x,y=by_name[left],by_name[right]
            summaries=[json.loads((Path(row['run'])/'rollout.json').read_text()) for row in (x,y)]
            if all(s['full_task_horizon_completed'] for s in summaries):
                run('combine_paper_comparison_video_20261003.py',['--top',x['output'],'--bottom',y['output'],
                    '--output',root/('comparison_final_h1_seed'+str(seed))],'comparison_seed'+str(seed))
            else:
                state.setdefault('unstacked_short_videos',[]).append(dict(seed=seed,reason='Do not pad an aborted method to match 55s'));save()
        figures=[('final_h1_learned_curves',('recovery035_esn_fixed','recovery035_esn_seed2','paired_feature_matched_rnn','paired_feature_matched_rnn_seed2'),
                  ('ESN seed 1','ESN seed 2','Matched RNN seed 1','Matched RNN seed 2')),
                 ('final_h1_controller_curves',('recovery035_esn_fixed','recovery_lift0.035_distance0.02','original_vmc_04','admittance_01','impedance_12','zero'),
                  ('ESN seed 1','Enhanced VMC teacher','Tuned original VMC','Tuned admittance','Tuned impedance','Nominal'))]
        for folder,names,labels in figures:
            run('plot_paper_trajectories_20261003.py',['--runs',*[root/'heldout_h1'/name for name in names],
                '--labels',*labels,'--output',root/folder],folder)
        wait_for('sensitivity_coordinator')
        run('report_paper_final_validation_20261003.py',['--root',root,'--output',root/'final_report','--supplementary'],'complete_report')
        report=root/'final_report/results.json';windows=root/'FINAL_CONTACT_WINDOWS.json'
        run('audit_paper_contact_windows_20261003.py',['--report',report,'--output',windows],'contact_windows')
        run('describe_paper_compliance_20261003.py',['--report',report,'--contact-windows',windows,'--output',root/'final_compliance'],'compliance')
        run('audit_paper_final_placement_20261003.py',['--report',report,'--output',root/'final_placement_audits'],'placement_audits')
        state.update(status='complete',result_sha256=sha(report),contact_window_audit_sha256=sha(windows),
                     compliance_sha256=sha(root/'final_compliance/COMPLIANCE.json'))
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();save()


if __name__=='__main__':main()
