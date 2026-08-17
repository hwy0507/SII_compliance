#!/usr/bin/env python3
"""Create deployable-input / privileged-label archives for Direct ESN fitting.

The input archive is normally exported by a MuJoCo rollout.  Student fields
are copied explicitly; teacher-only fields are read only to generate labels.
This separation makes it difficult to accidentally leak contact truth into the
deployed ESN.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from direct_esn_compliance import PrivilegedTeacherConfig, build_privileged_teacher_trace


REQUIRED = {
    "joint_position", "joint_velocity", "wbc_task_twist", "pose_error",
    "contact_force", "contact_normal", "contact_duration_s", "signed_distance_m",
}


def build_archive(input_path: Path, output_path: Path, *, sample_stride: int = 1, teacher_config: PrivilegedTeacherConfig = PrivilegedTeacherConfig()) -> dict:
    if sample_stride < 1:
        raise ValueError("sample_stride must be positive")
    with np.load(input_path, allow_pickle=False) as source:
        missing = REQUIRED - set(source.files)
        if missing:
            raise ValueError(f"{input_path}: missing required fields {sorted(missing)}")
        indices = slice(None, None, sample_stride)
        q = np.asarray(source["joint_position"])[indices]
        qdot = np.asarray(source["joint_velocity"])[indices]
        twist = np.asarray(source["wbc_task_twist"])[indices]
        pose_error = np.asarray(source["pose_error"])[indices]
        contact_force = np.asarray(source["contact_force"], dtype=float)[indices]
        contact_normal = np.asarray(source["contact_normal"], dtype=float)[indices]
        contact_duration_s = np.asarray(source["contact_duration_s"], dtype=float)[indices]
        signed_distance_m = np.asarray(source["signed_distance_m"], dtype=float)[indices]
        target = build_privileged_teacher_trace(
            contact_force,
            contact_normal,
            contact_duration_s,
            signed_distance_m,
            pose_error,
            config=teacher_config,
        )
    lengths = {len(q), len(qdot), len(twist), len(pose_error), len(target)}
    if len(lengths) != 1:
        raise ValueError("student trace and teacher labels have unequal lengths")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        joint_position=q,
        joint_velocity=qdot,
        wbc_task_twist=twist,
        pose_error=pose_error,
        teacher_action=target,
        contact_force=contact_force,
        contact_normal=contact_normal,
        contact_duration_s=contact_duration_s,
        signed_distance_m=signed_distance_m,
        teacher_config_json=json.dumps(teacher_config.__dict__),
    )
    return {"input": str(input_path), "output": str(output_path), "samples": len(target), "student_fields": ["joint_position", "joint_velocity", "wbc_task_twist"], "teacher_label": "privileged_teacher_action"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-stride", type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(build_archive(args.input, args.output, sample_stride=args.sample_stride), indent=2))


if __name__ == "__main__":
    main()
