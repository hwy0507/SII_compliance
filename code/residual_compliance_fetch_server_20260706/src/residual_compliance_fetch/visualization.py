from __future__ import annotations

from pathlib import Path

import numpy as np

CAMERA_PRESETS = {
    # Oblique view, good for seeing the whole Fetch arm and the crossing sphere.
    "iso": {"dist": 2.7, "pitch": -0.34, "yaw": -2.30},
    # Lower side view, usually the clearest for showing arm compliance.
    "side": {"dist": 2.35, "pitch": -0.12, "yaw": -1.62},
    # View from the front of the arm workspace.
    "front": {"dist": 2.45, "pitch": -0.16, "yaw": -0.10},
    # Close-up around wrist/forearm and dynamic obstacle.
    "close": {"dist": 1.65, "pitch": -0.10, "yaw": -1.35},
    # Old high angle for debugging global layout.
    "top": {"dist": 4.2, "pitch": -0.72, "yaw": -2.35},
}


def rgba_to_rgb_array(rgba):
    if hasattr(rgba, "cpu"):
        rgba = rgba.cpu().numpy()
    elif isinstance(rgba, list):
        if len(rgba) > 0 and hasattr(rgba[0], "cpu"):
            rgba = [x.cpu().numpy() for x in rgba]
        rgba = np.asarray(rgba)

    while rgba.ndim > 3 and rgba.shape[0] == 1:
        rgba = rgba[0]

    if rgba.dtype.kind == "f":
        return np.clip(rgba[..., :3] * 255.0, 0, 255).astype(np.uint8)
    return rgba[..., :3].astype(np.uint8)


def look_at_pose(target_pos, dist=2.35, pitch=-0.12, yaw=-1.62):
    import sapien
    import trimesh.transformations as tra

    target_pos = np.asarray(target_pos, dtype=np.float32)
    z = dist * np.sin(-pitch)
    xy = dist * np.cos(-pitch)
    x = xy * np.cos(yaw)
    y = xy * np.sin(yaw)
    cam_pos = target_pos + np.array([x, y, z], dtype=np.float32)

    forward = target_pos - cam_pos
    forward = forward / np.linalg.norm(forward)
    world_up = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    cam_x = forward
    cam_y = np.cross(world_up, forward)
    if np.linalg.norm(cam_y) < 1e-6:
        cam_y = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    cam_y = cam_y / np.linalg.norm(cam_y)
    cam_z = np.cross(cam_x, cam_y)

    mat44 = np.eye(4)
    mat44[:3, 0] = cam_x
    mat44[:3, 1] = cam_y
    mat44[:3, 2] = cam_z
    mat44[:3, 3] = cam_pos
    quat = tra.quaternion_from_matrix(mat44)
    return sapien.Pose(p=mat44[:3, 3], q=quat)


class ThirdPersonCamera:
    def __init__(self, scene, target_pos, width: int, height: int, view: str = "side"):
        self.scene = scene
        self.width = int(width)
        self.height = int(height)
        self.frames: list[np.ndarray] = []
        preset = CAMERA_PRESETS.get(view, CAMERA_PRESETS["side"])
        self.camera = scene.add_camera(
            name="residual_demo_camera",
            width=self.width,
            height=self.height,
            fovy=np.deg2rad(60.0),
            near=0.1,
            far=100.0,
            pose=look_at_pose(target_pos, **preset),
        )
        scene.set_ambient_light([0.48, 0.48, 0.48])
        scene.add_directional_light([1, 1, -1], [0.9, 0.9, 0.9], shadow=True)
        scene.add_directional_light([-1, -0.5, -1], [0.45, 0.45, 0.55], shadow=True)

    def capture(self) -> None:
        self.scene.update_render()
        self.camera.take_picture()
        self.frames.append(rgba_to_rgb_array(self.camera.get_picture("Color")))

    def save_gif(self, path: str | Path, fps: float) -> Path:
        import imageio.v2 as imageio

        if not self.frames:
            raise RuntimeError("No frames captured.")
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        imageio.mimsave(str(out), self.frames, fps=float(fps))
        return out
