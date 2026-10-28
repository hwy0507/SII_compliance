"""Collect actual trajectories from the development-selected teacher, once.

Forty existing public train/validation identities; no new parameter search or
sealed access. The original48 attempts remain untouched. If the selected
configuration is identical, skip rather than duplicate demonstrations.
"""
import argparse
from datetime import datetime,timezone,timedelta
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from research72_slots_20261003 import simulation_slot
from run_all_methods_formal_20261003 import V6,MENAGERIE
from run_paper_final_validation_20261003 import ENV


def read(p):
    import json
    return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('root','output','predecessor'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve();protocol=read(root/'PROTOCOL.json')
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    conditions=[c for c in read(root/'CONDITIONS.json')['conditions'] if c['role'] in ('train','imitation_validation')]
    assert len(conditions)==40
    deadline=datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    out.mkdir(parents=True,exist_ok=False)
    specification=dict(registered_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),
        conditions=[c['id'] for c in conditions],maximum_episodes=40,source_sha256=sha(Path(__file__)),
        teacher='One already registered development-selected enhanced teacher, no new parameter candidate.',
        data_roles='Same public32 train/8 validation identities; actual new executions, no relabeling or development history as data.',
        use='Export strict/full-horizon demonstrations for all learned families alike. Future refits require their own predeclared budget; this collector does not train or choose a student.',
        resources='One managed lease held through collection,1thread/3GiB; old four-queue predecessor finishes first.',
        deadline_utc=deadline.isoformat(),skip='If selected configuration equals the initial teacher, avoid duplicate trajectories.')
    write(out/'SPECIFICATION.json',specification)
    state=dict(status='waiting_for_predecessor',started_utc=now(),specification_sha256=sha(out/'SPECIFICATION.json'))
    write(out/'execution.json',state)
    phase=None;queue_state=None;bank=None
    try:
        while True:
            previous=read(a.predecessor/'execution.json')
            if previous['status']=='complete':break
            assert previous['status']=='waiting_for_controller_screen' or previous['status'].startswith('running_')
            assert datetime.now(timezone.utc)<deadline,'No new development after cutoff'
            time.sleep(30)
        choice_path=a.predecessor/'CONTROLLER_CHOICE.json';choice=read(choice_path)
        assert choice['protocol_sha256']==specification['protocol_sha256']
        assert choice['outcome']=='one per family selected on all eight development identities'
        candidate=next(c for c in choice['candidates'] if c['category']=='enhanced_teacher')
        state.update(choice_sha256=sha(choice_path),selected_teacher=candidate)
        if candidate['config']==read(root/'teacher.json'):
            state.update(status='complete_skipped_identical_teacher',new_physics_episodes=0);return
        bank=out/'collection';bank.mkdir();phase=bank/'queue_0';phase.mkdir();source=phase/'source'
        for folder in ('scripts','tools','assets'):
            shutil.copytree(ROOT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
        write(bank/'SOURCE_HASHES.json',{str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()})
        config=bank/'teacher.json';write(config,candidate['config'])
        write(bank/'TEACHER_SELECTION.json',dict(protocol_sha256=specification['protocol_sha256'],
            choice_path=str(choice_path),choice_sha256=sha(choice_path),candidate=candidate,teacher_config_sha256=sha(config)))
        queue_state=dict(status='waiting_for_lease',started_utc=now(),rows=[])
        write(phase/'execution.json',queue_state);write(bank/'execution.json',dict(status='running',started_utc=now()))
        state['status']='waiting_for_lease';write(out/'execution.json',state)
        with simulation_slot(root,deadline) as lease:
            queue_state.update(status='running',lease=lease);state.update(status='collecting',lease=lease)
            write(out/'execution.json',state)
            for condition in conditions:
                if datetime.now(timezone.utc)>=deadline:
                    queue_state['status']='deadline_no_new_dispatch';break
                name=condition['id'];run=phase/name
                command=[sys.executable,str(source/'tools/research72_worker_20261003.py'),
                    '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',specification['protocol_sha256'],
                    '--research-condition',name,'--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),
                    '--config',str(config),'--output',str(run),'--contact-audit','--physics-dt',str(protocol['physics_dt_s'])]
                row=dict(name=name,role=condition['role'],command=command,started_utc=now());queue_state['rows'].append(row)
                write(phase/'execution.json',queue_state)
                env={**os.environ,**ENV,'MUJOCO_MENAGERIE_PATH':str(MENAGERIE),
                    'SII_SOURCE_BASE_COMMIT':os.environ['SII_SOURCE_BASE_COMMIT']}
                with (phase/(name+'.log')).open('x') as log:
                    rc=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
                row.update(returncode=rc,ended_utc=now());write(phase/'execution.json',queue_state)
                assert rc==0,'Interrupted attempt retained, no automatic retry'
                row.update(audit=read(run/'AUDIT.json'),audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'))
                write(phase/'execution.json',queue_state)
            else:queue_state['status']='complete'
        queue_state['ended_utc']=now();write(phase/'execution.json',queue_state)
        with (out/'audit.log').open('x') as log:
            subprocess.run([sys.executable,str(ROOT/'tools/audit_paper_phase_20261003.py'),'--phase',str(phase),
                '--output',str(bank/'queue_0_analysis'),'--model-sha256',protocol['formal_model_sha256']],check=True,stdout=log,stderr=subprocess.STDOUT)
        rows=[dict(r,run=str(phase/r['name'])) for r in queue_state['rows']]
        write(bank/'SUMMARY.json',dict(rows=rows,count=len(rows),task=sum(r['audit']['task_success'] for r in rows),
            strict=sum(r['audit']['strict_success'] for r in rows)))
        write(bank/'execution.json',dict(status=queue_state['status'],ended_utc=now(),episodes=len(rows)))
        state.update(status=queue_state['status'],new_physics_episodes=len(rows))
        if queue_state['status']=='complete':
            state['status']='exporting';write(out/'execution.json',state)
            with (out/'export.log').open('x') as log:
                subprocess.run([sys.executable,str(ROOT/'tools/research72_build_demonstrations_20261003.py'),
                    '--root',str(root),'--refined-teacher-bank',str(bank),'--output',str(out/'demonstrations')],
                    check=True,stdout=log,stderr=subprocess.STDOUT)
            state.update(status='complete',dataset_metadata_sha256=sha(out/'demonstrations/DATA_COMPLETE.json'))
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc))
        if phase is not None and queue_state is not None and queue_state['status'] in ('running','waiting_for_lease'):
            queue_state.update(status='failed_preserved',error=repr(exc),ended_utc=now());write(phase/'execution.json',queue_state)
        if bank is not None:
            write(bank/'execution.json',dict(status='failed_preserved',error=repr(exc),ended_utc=now(),
                queue_status=queue_state['status'] if queue_state else None))
        raise
    finally:state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
