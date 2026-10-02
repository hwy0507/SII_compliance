"""Counterfactual teacher replay on a student's history, never task evidence.

Stage/contact truth is used only for post-hoc analysis. Neither enters the
teacher/actor. Filtered action integrals are a drift proxy, not robot motion.
"""
import argparse
from pathlib import Path
import json
import numpy as np
from optimize_tool_contact_20261002 import ParameterTeacher, sha, write, now
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--teacher-config', type=Path, required=True)
    parser.add_argument('--rollout', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    teacher = ParameterTeacher(json.loads(args.teacher_config.read_text()))
    teacher.reset()
    config = VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    teacher_filter = VelocityResidualActionFilter(config)
    student_filter = VelocityResidualActionFilter(config)
    with np.load(args.rollout, allow_pickle=False) as z:
        obs, actions, time, stage = (z[k] for k in ('observation', 'applied_action', 'time', 'stage'))
        requested, teacher_twist, student_twist = [], [], []
        for o, action in zip(obs, actions):
            teacher.observe(o)
            target = teacher.act(o[39:45])
            requested.append(target)
            teacher_twist.append(teacher_filter.filter(target, .04).cartesian_yield_twist)
            student_twist.append(student_filter.filter(action, .04).cartesian_yield_twist)
    requested = np.asarray(requested)
    teacher_twist, student_twist = np.asarray(teacher_twist), np.asarray(student_twist)
    error = student_twist[:, :3] - teacher_twist[:, :3]
    groups = {}
    for k in np.unique(stage):
        mask = stage == k
        groups[str(k)] = dict(
            start_s=float(time[mask][0]), end_s=float(time[mask][-1]), samples=int(mask.sum()),
            action_mse=float(np.mean((actions[mask] - requested[mask])**2)),
            mean_translation_error_mps=error[mask].mean(0).tolist(),
            integrated_action_error_m=(error[mask].sum(0)*.04).tolist(),
            maximum_translation_error_mps=float(np.linalg.norm(error[mask], axis=1).max()))
    np.savez_compressed(args.output/'counterfactual.npz', time=time, stage=stage,
                        teacher_requested=requested, student_requested=actions,
                        teacher_filtered_twist=teacher_twist, student_filtered_twist=student_twist)
    write(args.output/'DIAGNOSIS.json', dict(
        created_utc=now(), trace_sha256=sha(args.rollout), config_sha256=sha(args.teacher_config),
        source_sha256=sha(Path(__file__)), groups=groups,
        evidence_sha256=sha(args.output/'counterfactual.npz'),
        limitation='Counterfactual labels on the observed student history; teacher not physically executed here. Integrated action error is not actual position error. Stage used only for post-hoc grouping.'))
    print(json.dumps(groups))


if __name__ == '__main__':
    main()
