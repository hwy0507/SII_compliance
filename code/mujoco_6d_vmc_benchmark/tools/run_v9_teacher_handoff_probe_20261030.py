"""Finite development probe, mixed behavior; never a pure teacher demonstration.

Reuse the frozen physical worker without editing its source. Keep its raw
student-diagnostic execution manifest and add an authoritative mixed-behavior
receipt and separately archived adapter source. Only complete, independently
qualified executed teacher suffixes may later supply imitation labels.
"""
import argparse
import os
from pathlib import Path
import sys
import tarfile
import numpy as np
import run_video_reference_coverage_20261029 as physical
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from development_teacher_handoff_20261030 import DevelopmentTeacherHandoff
from select_v9_closed_loop_candidates_v3_20261029 import check_resources


def worker(output, prefix):
    check_resources()
    assert not os.environ.get('VMC_COLLECTION_PLAN'), 'Not the old pure-teacher collector'
    assert os.environ.get('VMC_STUDENT_CHECKPOINT')
    assert 0 < prefix < 500
    assert not output.exists(), 'Never overwrite or restart an incomplete probe'
    output.mkdir(parents=True)
    sources = {str(p.relative_to(ROOT)): sha(p) for folder in ('scripts','tools')
               for p in (ROOT/folder).glob('*.py')}
    write(output/'PROBE_REGISTRATION.json', dict(student_steps=prefix, sources=sources,
        role='development_student_prefix_then_teacher_suffix',
        checkpoint_sha256=sha(Path(os.environ['VMC_STUDENT_CHECKPOINT'])),
        no_training_labels_yet=True))
    actors = []
    original = physical.make_actor

    class Recorded(DevelopmentTeacherHandoff):
        def __init__(self, config, checkpoint):
            super().__init__(config, checkpoint, prefix)
            self.rows = []
        def act(self, wrench, dt=.04):
            action = super().act(wrench, dt)
            self.rows.append((self.last_teacher_action.copy(), self.last_student_action.copy(),
                              self.last_behavior_role))
            return action

    def factory(config, checkpoint=None):
        assert checkpoint is not None
        actor = Recorded(config, checkpoint)
        actors.append(actor)
        return actor

    physical.make_actor = factory
    try:
        physical.worker(output, 'rod')
    finally:
        physical.make_actor = original
        folder = output/'rod'
        if (folder/'execution.json').exists():
            execution = read(folder/'execution.json')
            rows = actors[0].rows if actors else []
            n = execution.get('steps', 0)
            # An action can be requested just before a physical exception.
            # Keep attempts but never label that uncompleted row as executed.
            if rows:
                np.savez_compressed(folder/'handoff_actions.npz',
                    teacher=np.asarray([r[0] for r in rows]),
                    student=np.asarray([r[1] for r in rows]),
                    role=np.asarray([r[2] for r in rows]),
                    physical_step_completed=np.arange(len(rows)) < n,
                    teacher_loss_mask=(np.arange(len(rows)) >= prefix) & (np.arange(len(rows)) < n))
            adapter_names = ['tools/'+name for name in (
                'run_v9_teacher_handoff_probe_20261030.py', 'development_teacher_handoff_20261030.py',
                'audit_v9_teacher_handoff_probe_20261030.py')]
            with tarfile.open(folder/'handoff_source.tar.gz', 'w:gz') as archive:
                for name in adapter_names:
                    archive.add(ROOT/name, arcname=name)
            stable = all(sha(ROOT/name)==digest for name,digest in sources.items())
            write(folder/'HANDOFF_EXECUTION.json', dict(
                status='complete_pending_independent_review' if execution['status']=='complete' and stable else 'failed_preserved',
                controller_role='development_student_prefix_then_teacher_suffix', student_steps=prefix,
                attempted_actions=len(rows), completed_steps=n,
                executed_teacher_steps=max(0,n-prefix), prefix_teacher_outputs='counterfactual; loss mask false',
                labels_eligible_for_training=False, source_stable=stable,
                sources=sources, input_hashes={name:sha(folder/name) for name in (
                    'execution.json','trajectory.npz','teacher.json','student_checkpoint.npz',
                    'handoff_actions.npz','handoff_source.tar.gz') if (folder/name).exists()},
                raw_manifest_note='execution.json is the reused physical worker student-diagnostic record; this receipt specifies actual mixed behavior. Not a pure student or pure teacher rollout.'))
    assert read(output/'rod/HANDOFF_EXECUTION.json')['status']=='complete_pending_independent_review'


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--student-steps',type=int,required=True)
    args=parser.parse_args()
    worker(args.output.resolve(),args.student_steps)
