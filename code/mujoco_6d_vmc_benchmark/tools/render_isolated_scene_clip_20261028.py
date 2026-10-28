"""Render a real saved trajectory; only camera/light/text are changed."""
import argparse
import json
import os
import hashlib
import subprocess
from pathlib import Path
os.environ.setdefault('MUJOCO_GL', 'egl')
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene', type=Path, required=True)
    p.add_argument('--ffmpeg', type=Path, required=True)
    a = p.parse_args()
    scene = a.scene.resolve()
    stem = scene/'run/rollout'
    record = json.loads(stem.with_suffix('.json').read_text())
    assert digest(stem.with_suffix('.mjb')) == record['model_sha256']
    with np.load(stem.with_suffix('.npz')) as z:
        trace = {k: z[k] for k in ('time', 'qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat') if k in z}
    model = mujoco.MjModel.from_binary_path(str(stem.with_suffix('.mjb')))
    model.vis.global_.offwidth = 640
    model.vis.global_.offheight = 480
    model.vis.headlight.ambient[:] = .65
    model.vis.headlight.diffuse[:] = .8
    data = mujoco.MjData(model)
    settings = {
        'passive_corner': ('Passive: rigid table edge', 0., 25., 2., 4),
        'active_short': ('Active short: ball impact', 1., 4., .5, 1),
        'active_long': ('Active long: sustained rod push', 10., 24., 1., 2),
    }
    label, start, end, speed, stride = settings[scene.name]
    selected = np.flatnonzero((trace['time'] >= start) & (trace['time'] <= end))[::stride]
    assert len(selected) > 10
    dt = float(np.median(np.diff(trace['time'])))
    fps = speed/(dt*stride)
    cameras = []
    for lookat, distance, azimuth, elevation in [
        ([.58, -.12, .48], 2.1, 135, -23),
        ([.57, -.19, .60], .85, 105, -20),
    ]:
        cam = mujoco.MjvCamera()
        cam.lookat[:] = lookat
        cam.distance, cam.azimuth, cam.elevation = distance, azimuth, elevation
        cameras.append(cam)
    out = scene/'media'
    out.mkdir(exist_ok=False)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    writer = subprocess.Popen([str(a.ffmpeg), '-hide_banner', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x528', '-r', str(fps), '-i', '-',
        '-an', '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-threads', '1', '-crf', '20',
        '-movflags', '+faststart', str(out/'scene.mp4')], stdin=subprocess.PIPE)
    renderer = mujoco.Renderer(model, height=480, width=640)
    frames = []
    try:
        for n, index in enumerate(selected):
            for key in ('qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat'):
                if key in trace:
                    getattr(data, key)[:] = trace[key][index]
            data.time = float(trace['time'][index])
            mujoco.mj_forward(model, data)
            frame = Image.new('RGB', (1280, 528), (18, 24, 32))
            draw = ImageDraw.Draw(frame)
            draw.text((12, 12), f'{label} | new30 VMC teacher | t={data.time:.2f}s | {speed:g}x', font=font, fill='white')
            for panel, camera in enumerate(cameras):
                renderer.update_scene(data, camera=camera)
                frame.paste(Image.fromarray(renderer.render()), (panel*640, 48))
            writer.stdin.write(np.asarray(frame).tobytes())
            frames.append(frame.resize((960, 396)))
            if n in (0, len(selected)//2, len(selected)-1):
                frame.save(out/f'preview_{n:04d}.png')
    finally:
        writer.stdin.close()
        if writer.wait() != 0:
            raise RuntimeError('Video encoder failed')
        renderer.close()
    frames[0].save(out/'scene.gif', save_all=True, append_images=frames[1:],
                   duration=round(1000/fps), loop=0)
    with Image.open(out/'scene.gif') as gif:
        assert gif.n_frames == len(frames)
        for i in range(gif.n_frames):
            gif.seek(i)
            gif.load()
    manifest = dict(scene=scene.name, source=str(stem), render_only=True,
        clip_actual_time_s=[float(trace['time'][selected[0]]), float(trace['time'][selected[-1]])],
        fps=fps, playback_speed=speed, frames=len(frames), label=label,
        source_hashes={ext: digest(stem.with_suffix(ext)) for ext in ('.npz', '.json', '.mjb')},
        renderer_sha256=digest(Path(__file__)), gif_decoded_all_frames=True,
        media_hashes={ext: digest(out/('scene'+ext)) for ext in ('.gif', '.mp4')})
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
