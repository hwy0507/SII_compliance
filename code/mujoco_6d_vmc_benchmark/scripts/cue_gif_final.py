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
L.STATIC_HY = 0.03
L.STATIC_Z = 0.08
L._os.environ["LIFT_BOARD_TILT_DEG"] = "0.0"

L._os.environ["LIFT_BOARD_HX"] = "0.20"
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
    class TeacherWrap:
        def reset(self): self._t = L.LiftTeacher(y_yield=0.85, pre_t=2.7)
        def act(self, *args, **kwargs):
            hand = kwargs.get("hand_y", 0.0)
            return type("R", (), {"bounded_filter_action": self._t.act(*args, **kwargs)})()
    controllers = [("FW", NeutralPolicy()), ("TEACHER", "teacher")]
    try:
        import cv2
    except ImportError:
        cv2 = None
    OUTDIR.mkdir(parents=True, exist_ok=True)
    board = ("static", 0.10, 15.0)
    for azim, elev, tag in ((180, -5, "facing"),):
     for name, policy in controllers:
        env = L.build_env(*board) if board[0]=="blocking" else D._env_for(board)
        m = L.rollout(env, 7, NeutralPolicy())
        env.close()
        env = L.build_env(*board) if board[0]=="blocking" else D._env_for(board)
        env.reset(seed=7, options={"fixture_index": 0})
        env.model.vis.global_.offwidth = 1280
        env.model.vis.global_.offheight = 720
        renderer = mujoco.Renderer(env.model, 720, 1280)
        cam = mujoco.MjvCamera()
        cam.lookat = np.array([0.52, 0.0, 0.63])
        cam.distance = 0.65
        cam.azimuth = azim
        cam.elevation = elev
        frames = []
        done, step = False, 0
        if policy != "teacher":
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
            if policy == "teacher":
                from extraction_experiment import board_force
                hand = env.data.xpos[env._hand_id]
                action = np.asarray(L.LiftTeacher(y_yield=0.85, pre_t=2.7).act(
                    *args, **kw, hand_x=float(hand[0]), hand_y=float(hand[1]),
                    hand_z=float(hand[2]), contact=board_force(env) > 2.0,
                    time_s=float(d["time_s"]),
                    nominal_y=float(d["nominal_position"][1])), dtype=float)
            else:
                action = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
            _, _, done, _, _ = env.step(action)
            step += 1
        renderer.close()
        env.close()
        import imageio.v3 as iio
        path = OUTDIR / f"multi_{tag}_{name.lower()}.gif"
        iio.imwrite(path, frames[::2], duration=40, loop=0)
        print(f"wrote {path}  (peak={m['peak']:.0f}N Fint={m['Fint']:.0f} "
              f"errF={m['errF_mm']:.1f}mm ok={int(m['completed'])})", flush=True)


if __name__ == "__main__":
    main()
