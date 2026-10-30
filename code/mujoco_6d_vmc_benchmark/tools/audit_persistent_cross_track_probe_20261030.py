"""Independent pure-controller replay and unchanged qualification of mixed probes.

Does not reuse the collector switch implementation to generate expected labels.
New cross-track teacher, three development scenes.
No integration, fitting, test input, or conversion of counterfactual labels.
"""
import argparse
import hashlib
from pathlib import Path
import sys
import tarfile
import numpy as np
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from current_student_policy_20260921 import load_current
from persistent_cross_track_teacher_20261030 import PersistentCrossTrackRecoveryTeacher as make_teacher
import audit_video_reference_vmc_20261028 as actor_audit
from qualify_ball_coverage_demo_20261029 import qualify


def expected(config,checkpoint,observations,prefix):
    teacher=make_teacher(config); teacher.reset()
    student=load_current(checkpoint); student.reset()
    teachers=[];students=[]
    for obs in observations:
        teacher.observe(obs.copy())
        teachers.append(teacher.act(obs[39:45].copy(),.04))
        students.append(student.act(obs.copy()))
    t=np.asarray(teachers);s=np.asarray(students)
    mask=np.arange(len(observations))>=prefix
    return t,s,np.where(mask[:,None],t,s),mask


def audit(folder):
    assert not (folder/'INDEPENDENT_AUDIT.json').exists()
    receipt=read(folder/'HANDOFF_EXECUTION.json')
    assert receipt['status']=='complete_pending_independent_review'
    for name,digest in receipt['sources'].items():assert sha(ROOT/name)==digest,name
    for name,digest in receipt['input_hashes'].items():assert sha(folder/name)==digest,name
    with tarfile.open(folder/'handoff_source.tar.gz') as archive:
        for member in archive.getmembers():
            assert hashlib.sha256(archive.extractfile(member).read()).hexdigest()==receipt['sources'][member.name]
    with np.load(folder/'trajectory.npz',allow_pickle=False) as z:obs=z['observation'].copy();actions=z['action'].copy()
    with np.load(folder/'handoff_actions.npz',allow_pickle=False) as z:labels={k:z[k].copy() for k in z.files}
    prefix=receipt['student_steps'];n=len(obs)
    scene=read(folder/'execution.json')['scene']
    assert n==dict(rod=500,ball=750,corner=325)[scene]==receipt['completed_steps']==receipt['attempted_actions']
    cfg=read(folder/'teacher.json');checkpoint=folder/'student_checkpoint.npz'
    t,s,behavior,mask=expected(cfg,checkpoint,obs,prefix)
    for a,b in [(t,labels['teacher']),(s,labels['student']),(behavior,actions),
                (mask,labels['teacher_loss_mask']), (np.ones(n,dtype=bool),labels['physical_step_completed'])]:
        np.testing.assert_array_equal(a,b)
    np.testing.assert_array_equal(labels['role'],np.where(mask,'executed_teacher_suffix','student_prefix'))
    assert receipt['executed_teacher_steps']==int(mask.sum())
    # The old auditor independently checks every public-filter output; supply
    # independently reconstructed behavior instead of claiming pure-student replay.
    class IndependentHistory:
        def __init__(self):self.index=0;self.pending=None
        def observe(self,o):
            assert self.pending is None
            np.testing.assert_array_equal(o,obs[self.index]);self.pending=o.copy()
        def act(self,wrench,dt=.04):
            assert self.pending is not None and dt==.04
            np.testing.assert_array_equal(wrench,self.pending[39:45])
            value=behavior[self.index].copy();self.index+=1;self.pending=None;return value
    original=actor_audit.make_actor;argv=sys.argv.copy()
    actor_audit.make_actor=lambda *a,**kw:IndependentHistory()
    try:
        sys.argv=[str(Path(actor_audit.__file__)),str(folder)]
        actor_audit.main()
    finally:actor_audit.make_actor=original;sys.argv=argv
    # Bind the adapter independently of the base auditor provenance.
    independent=read(folder/'INDEPENDENT_AUDIT.json')
    independent.update(mixed_behavior_adapter_sha256=sha(Path(__file__)),
        handoff_execution_sha256=sha(folder/'HANDOFF_EXECUTION.json'),
        input_hashes={**independent['input_hashes'],**{name:sha(folder/name) for name in (
            'HANDOFF_EXECUTION.json','handoff_actions.npz','handoff_source.tar.gz')}})
    write(folder/'INDEPENDENT_AUDIT.json',independent)
    # Unmodified geometric order/hold, contact, safety and Task gates.
    import subprocess
    if scene=='rod':
        subprocess.run([sys.executable,str(ROOT/'tools/audit_rod_yield_rejoin_v3_20261028.py'),str(folder)],check=True)
    qualification=qualify(folder)
    result=dict(status='reviewed', qualified=qualification['status']=='qualified',
        teacher_suffix_candidate_only=qualification['status']=='qualified',
        executed_teacher_rows=int(mask.sum()),counterfactual_prefix_rows=prefix,
        no_training_performed=True, no_final_test_performed=True,
        qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),
        handoff_execution_sha256=sha(folder/'HANDOFF_EXECUTION.json'),
        independent_audit_sha256=sha(folder/'INDEPENDENT_AUDIT.json'),reviewer_sha256=sha(Path(__file__)),
        limitation='Full mixed rollout gates; does not establish recovery from every state, nor authorize counterfactual-prefix imitation labels. Any augmentation/retraining needs a separate shared-data protocol.')
    write(folder/'HANDOFF_REVIEW.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    print(audit(parser.parse_args().folder.resolve()))
