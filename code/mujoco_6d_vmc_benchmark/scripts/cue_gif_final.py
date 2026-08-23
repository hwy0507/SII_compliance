#!/usr/bin/env python3
"""Champion (rep004) cue-board comparison GIFs: FW hard hit vs ESN-DL
anticipatory pre-yield.  Same board, same strike, five controllers."""
from __future__ import annotations

import os as _os
from pathlib import Path

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import mujoco
import numpy as np

import delayline_experiment as D
import lift_experiment as L
L.STATIC_HY = 0.06
L.STATIC_Z = 0.02
L._os.environ["LIFT_BOARD_TILT_DEG"] = "10.0"
from extraction_experiment import NeutralPolicy
from direct_esn_compliance import DirectESNController

CHAMP = Path("/home/arm1/vmc_mujoco_runtime/outputs/overnight_v18/rep004")
OUTDIR = Path("/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/docs/lift_results")


def main() -> None:
    esn = D.DelayLineEnsemble(
        [D.DelayLineESN(DirectESNController.from_npz(p))
         for p in sorted(CHAMP.glob("dl_s*.npz"))])
    mlp = D._load_mlp(CHAMP / "mlp_raw")
    mlpdl = D._load_mlp(CHAMP / "mlp_dl", dl=True)
    controllers = [("FW", NeutralPolicy()), ("VMC", L._tuned_vmc()),
                   ("MLP", mlp), ("MLP-DL", mlpdl), ("ESN-DL", esn)]
    try:
        import cv2
    except ImportError:
        cv2 = None
    OUTDIR.mkdir(parents=True, exist_ok=True)
    board = ("static", 0.05, 10.0, 0.0, 0.0)
    for name, policy in controllers:
        env = D._env_for(board)
        m = L.rollout(env, 7, policy)
        env.close()
        env = D._env_for(board)
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
        path = OUTDIR / f"block_{name.replace('-', '').lower()}.gif"
        iio.imwrite(path, frames[::2], duration=40, loop=0)
        print(f"wrote {path}  (peak={m['peak']:.0f}N Fint={m['Fint']:.0f} "
              f"errF={m['errF_mm']:.1f}mm ok={int(m['completed'])})", flush=True)


if __name__ == "__main__":
    main()
