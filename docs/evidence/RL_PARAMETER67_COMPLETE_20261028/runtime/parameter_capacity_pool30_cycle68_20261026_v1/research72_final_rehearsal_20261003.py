"""One known-training replay through the final adapter, never real heldout data.

The private synthetic lock/receipt exercise execution plumbing only. They must
not be copied to the authoritative research root or used as final evidence.
Wait for the old unleased predecessor; then share one managed simulation slot.
"""
import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from research72_final_lock_20261003 import runtime_hashes
from research72_slots_20261003 import simulation_slot
from run_paper_final_validation_20261003 import ENV
from run_all_methods_formal_20261003 import MENAGERIE


def read(path):
    return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','output','predecessor'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve();out=args.output.resolve()
    protocol=read(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    known=next(c for c in read(root/'CONDITIONS.json')['conditions'] if c['id']=='train_000')
    assert known['role']=='train'
    matches=list((root/'teacher_bank').glob('queue_*/train_000'))
    assert len(matches)==1
    reference=matches[0];assert read(reference/'execution.json')['status']=='complete'
    deadline=datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    out.mkdir(parents=True,exist_ok=False)
    specification=dict(registered_utc=now(),source_sha256=sha(Path(__file__)),
        actual_research_protocol_sha256=sha(root/'PROTOCOL.json'),known_training_condition=known,
        original_trace_sha256=sha(reference/'rollout.npz'),maximum_physics_episodes=1,
        deadline_utc=deadline.isoformat(),real_heldout_access=False,
        purpose='Private synthetic final-adapter rehearsal using the already public train_000 and original teacher. Not a blind test, not new training data, not a method-selection result.')
    write(out/'SPECIFICATION.json',specification)
    state=dict(status='waiting_for_predecessor',started_utc=now(),specification_sha256=sha(out/'SPECIFICATION.json'))
    write(out/'execution.json',state)
    try:
        while read(args.predecessor/'execution.json')['status']!='complete':
            old=read(args.predecessor/'execution.json')['status']
            assert old.startswith('running_') or old=='waiting_for_controller_screen',old
            assert datetime.now(timezone.utc)<deadline
            time.sleep(30)
        assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
        sandbox=out/'synthetic_protocol';(sandbox/'sealed').mkdir(parents=True)
        # The filenames exercise the adapter, but contain exactly one *known*
        # training condition. No real research sealed file is opened or hashed.
        synthetic=dict(known,id='rehearsal_of_known_train_000',role='heldout')
        write(sandbox/'sealed/HELDOUT.json',dict(conditions=[synthetic],
            diagnostic_only=True,origin='Already public train_000; not sampled or blinded'))
        private=dict(protocol,diagnostic_only=True,
            sealed_condition_sha256=sha(sandbox/'sealed/HELDOUT.json'))
        write(sandbox/'PROTOCOL.json',private)
        phase=out/'evaluation';queue=phase/'queue_0';queue.mkdir(parents=True)
        source=queue/'source'
        for folder in ('scripts','tools','assets'):
            shutil.copytree(ROOT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
        name='known_teacher__known_train_000';run=queue/name
        lock=dict(schema='sii-research72-final-lock-v1',diagnostic_only=True,
            frozen_utc=now(),training_closed=True,all_registered_finalists_included=True,
            protocol_sha256=sha(sandbox/'PROTOCOL.json'),amendment_sha256={},
            sealed_condition_sha256=private['sealed_condition_sha256'],
            runtime_source_sha256=runtime_hashes(source),
            candidates=[dict(name='known_teacher',category='enhanced_teacher',config=read(root/'teacher.json'))])
        lock_path=sandbox/'SYNTHETIC_LOCK.json';write(lock_path,lock)
        write(sandbox/'FINAL_UNSEAL_RECEIPT.json',dict(diagnostic_only=True,output=str(phase),
            protocol_sha256=sha(sandbox/'PROTOCOL.json'),sealed_condition_sha256=private['sealed_condition_sha256'],
            model_lock_sha256=sha(lock_path)))
        state['status']='waiting_for_lease';write(out/'execution.json',state)
        command=[sys.executable,str(source/'tools/research72_final_worker_20261003.py'),
            '--root',str(sandbox),'--model-lock',str(lock_path),'--lock-sha256',sha(lock_path),
            '--candidate','known_teacher','--condition',synthetic['id'],'--output',str(run)]
        row=dict(name=name,command=command,diagnostic_only=True)
        qstate=dict(status='waiting_for_lease',rows=[row])
        write(queue/'execution.json',qstate)
        with simulation_slot(root,deadline) as lease:
            state.update(status='running_known_training_replay',lease=lease);write(out/'execution.json',state)
            row['started_utc']=now();qstate['status']='running';write(queue/'execution.json',qstate)
            env={**os.environ,**ENV,'MUJOCO_MENAGERIE_PATH':str(MENAGERIE),
                 'SII_SOURCE_BASE_COMMIT':os.environ['SII_SOURCE_BASE_COMMIT']}
            with (out/'replay.log').open('x') as log:
                rc=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            row.update(returncode=rc,ended_utc=now());write(queue/'execution.json',qstate)
            assert rc==0, 'Engineering failure preserved, no automatic repeat'
        row.update(audit=read(run/'AUDIT.json'),audit_sha256=sha(run/'AUDIT.json'),
                   trace_sha256=sha(run/'rollout.npz'))
        qstate['status']='complete';write(queue/'execution.json',qstate)
        state['status']='auditing';write(out/'execution.json',state)
        with (out/'audit.log').open('x') as log:
            subprocess.run([sys.executable,str(ROOT/'tools/audit_paper_phase_20261003.py'),
                '--phase',str(queue),'--output',str(phase/'queue_0_analysis'),
                '--model-sha256',protocol['formal_model_sha256']],check=True,stdout=log,stderr=subprocess.STDOUT)
        compared={}
        for name in ('rollout.npz','execution_chain.npz','rollout_metrics/substep_metrics.npz','research_substeps.npz'):
            with np.load(reference/name) as a,np.load(run/name) as b:
                keys=(['observation','applied_action','qpos','qvel','ctrl'] if name=='rollout.npz' else a.files)
                assert set(keys)<=set(b.files)
                for key in keys:
                    np.testing.assert_array_equal(a[key],b[key])
                compared[name]=list(keys)
        assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
        result=dict(completed_utc=now(),diagnostic_only=True,real_heldout_access=False,
            original_run=str(reference),rehearsal_run=str(run),compared_arrays_exact=compared,
            actual_research_protocol_sha256=sha(root/'PROTOCOL.json'),
            synthetic_protocol_sha256=sha(sandbox/'PROTOCOL.json'),synthetic_lock_sha256=sha(lock_path),
            source_hashes=runtime_hashes(source),trace_sha256=sha(run/'rollout.npz'),
            original_trace_sha256=sha(reference/'rollout.npz'),audit_sha256=sha(phase/'queue_0_analysis/INDEPENDENT_AUDIT.json'),
            limitation='One known teacher identity validates adapter plumbing, not final queue orchestration, all controller dispatches, or unseen-condition performance.')
        write(out/'REHEARSAL.json',result);state.update(status='complete',result_sha256=sha(out/'REHEARSAL.json'))
        print(json.dumps(dict(status='complete',real_heldout_access=False,physics_episodes=1)))
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':
    main()
