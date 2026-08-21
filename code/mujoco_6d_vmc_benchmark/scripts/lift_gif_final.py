#!/usr/bin/env python3
"""Final GIFs from the OVERNIGHT CHAMPION replicate (rep170: ESN 10.11 vs
MLP 12.29) on the most visual board: the payload-height plank strike."""
from __future__ import annotations

import os as _os
import sys
from pathlib import Path

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import mujoco
import numpy as np

import lift_experiment as L
from extraction_experiment import NeutralPolicy, UngatedESN, UngatedMLP
from direct_esn_compliance import DirectESNController

CHAMP = Path("/home/arm1/vmc_mujoco_runtime/outputs/lift_esn")  # v7 champion (4/6 completed)
OUTDIR = Path("/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/docs/lift_results")
BOARD = (("static", 0.05, 25.0) if _os.environ.get("GIF_BOARD", "static") == "static"
         else ("plank_payload", 3.00, 0.62, 1.0))


def main() -> None:
    from mlp_compliance_baseline import MLPComplianceController
    esn = L.EnsemblePolicy([UngatedESN(DirectESNController.from_npz(p))
                            for p in sorted(CHAMP.glob("esn_s*.npz"))])
    mlp = L.EnsemblePolicy([UngatedMLP(MLPComplianceController.from_npz(p))
                            for p in sorted(CHAMP.glob("mlp_s*.npz"))])
    controllers = [("FW", NeutralPolicy()), ("VMC", L._tuned_vmc()),
                   ("MLP", mlp), ("ESN", esn)]
    try:
        import cv2
    except ImportError:
        cv2 = None
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for name, policy in controllers:
        env = L.build_env(*BOARD, seed=7)
        m = L.rollout(env, 7, policy)
        env.close()
        env = L.build_env(*BOARD, seed=7)
        env.reset(seed=7, options={"fixture_index": 0})
        env.model.vis.global_.offwidth = 1280
        env.model.vis.global_.offheight = 720
        renderer = mujoco.Renderer(env.model, 720, 1280)
        cam = mujoco.MjvCamera()
        cam.lookat = np.array([0.52, 0.02, 0.64])
        cam.distance = 1.25
        cam.azimuth = 135
        cam.elevation = -18
        frames = []
        done, step = False, 0
        policy.reset()
        while not done:
            renderer.update_scene(env.data, camera=cam)
            frame = renderer.render()
            if cv2 is not None:
                cv2.putText(frame, name, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                            1.2, (255, 255, 0), 2)
                cv2.putText(frame, f"t={step*0.04:4.1f}s", (1150, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
            frames.append(frame.copy())
            d = env.diagnostics()
            args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
            kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
            action = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
            _, _, done, _, _ = env.step(action)
            step += 1
        renderer.close()
        env.close()
        import imageio.v3 as iio
        tag = _os.environ.get("GIF_BOARD", "static")
        path = OUTDIR / f"final_{tag}_{name.lower()}.gif"
        iio.imwrite(path, frames[::2], duration=40, loop=0)
        print(f"wrote {path}  (peak={m['peak']:.0f}N Fint={m['Fint']:.0f} "
              f"errF={m['errF_mm']:.1f}mm ok={int(m['completed'])})", flush=True)


if __name__ == "__main__":
    main()
