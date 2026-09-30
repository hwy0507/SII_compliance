"""Render an archived office rollout with three synchronized camera views."""
import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MUJOCO_GL', 'egl')
import imageio_ffmpeg
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--rollout', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--stride', type=int, default=5)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)

    record = json.loads(args.rollout.with_suffix('.json').read_text())
    model_path = args.rollout.with_suffix('.mjb')
    if digest(model_path) != record['model_sha256']:
        raise ValueError('Saved model hash mismatch')
    trace_path = args.rollout.with_suffix('.npz')
    with np.load(trace_path, allow_pickle=False) as z:
        trace = {key: z[key].copy() for key in z.files}

    model = mujoco.MjModel.from_binary_path(str(model_path))
    data = mujoco.MjData(model)
    model.vis.global_.offwidth = 640
    model.vis.global_.offheight = 480
    model.vis.headlight.ambient[:] = .65
    model.vis.headlight.diffuse[:] = .8
    renderer = mujoco.Renderer(model, height=480, width=640)
    cameras = [
        ('overview', [.64, -.02, .45], 2.5, 135, -20),
        ('end-effector', [.58, -.05, .58], 1.40, 110, -25),
        ('pillar-corner', [.57, -.24, .58], 1.20, 75, -20),
    ]
    camera_objs = []
    for _, lookat, distance, azimuth, elevation in cameras:
        cam = mujoco.MjvCamera()
        cam.lookat[:] = lookat
        cam.distance = distance
        cam.azimuth = azimuth
        cam.elevation = elevation
        camera_objs.append(cam)

    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    names = ['approach', 'align', 'grasp', 'lift', 'carry', 'load transfer', 'release', 'retreat']
    chosen = list(range(0, len(trace['time']), max(1, args.stride)))
    chosen = sorted(set(chosen + [len(trace['time']) - 1]))
    width, height = 1920, 560
    writer = imageio_ffmpeg.write_frames(
        str(args.output / 'replay_threeview.mp4'), (width, height), fps=10,
        codec='libx264', pix_fmt_out='yuv420p',
        output_params=['-movflags', '+faststart', '-crf', '20'])
    writer.send(None)
    gif_frames = []
    try:
        for frame_no, index in enumerate(chosen):
            data.qpos[:] = trace['qpos'][index]
            data.qvel[:] = trace['qvel'][index]
            data.ctrl[:] = trace['ctrl'][index]
            if 'mocap_pos' in trace:
                data.mocap_pos[:] = trace['mocap_pos'][index]
            if 'mocap_quat' in trace:
                data.mocap_quat[:] = trace['mocap_quat'][index]
            data.time = float(trace['time'][index])
            mujoco.mj_forward(model, data)
            frame = Image.new('RGB', (width, height), (15, 22, 30))
            draw = ImageDraw.Draw(frame)
            stage = names[int(trace['stage'][index])]
            draw.text((12, 8), f'{args.label} | office-v5 | t={data.time:.2f}s | {stage}', font=font, fill='white')
            draw.text((12, 34),
                      f"task={record['task_success']} | strict={record['strict_success']} | "
                      f"external penetration={1000 * record['stats']['max_external_penetration_m']:.6f} mm",
                      font=font, fill=(255, 215, 130))
            for panel, ((name, *_), cam) in enumerate(zip(cameras, camera_objs)):
                renderer.update_scene(data, camera=cam)
                frame.paste(Image.fromarray(renderer.render()), (640 * panel, 80))
                draw.rounded_rectangle((640 * panel + 8, 88, 640 * panel + 180, 118), radius=5, fill=(8, 14, 22))
                draw.text((640 * panel + 16, 94), name, font=font, fill=(238, 243, 249))
            writer.send(np.asarray(frame))
            gif_frames.append(frame.resize((1440, 420)))
            if frame_no in (0, len(chosen) - 1):
                frame.save(args.output / f'frame_{index:04d}.png')
    finally:
        writer.close()
        renderer.close()

    gif_frames[0].save(args.output / 'replay_threeview.gif', save_all=True,
                       append_images=gif_frames[1:], duration=100, loop=0)
    manifest = {
        'render_only': True,
        'physics_rerun': False,
        'camera_views': [name for name, *_ in cameras],
        'stride': args.stride,
        'record': str(args.rollout),
        'input_sha256': {ext: digest(args.rollout.with_suffix(ext)) for ext in ('.json', '.npz', '.mjb')},
        'output_sha256': {
            '.mp4': digest(args.output / 'replay_threeview.mp4'),
            '.gif': digest(args.output / 'replay_threeview.gif'),
        },
    }
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
