"""Render logged office states from the saved model; never run live physics."""
import argparse
import hashlib
import json
import os
from pathlib import Path
os.environ.setdefault('MUJOCO_GL','egl')
import imageio_ffmpeg
import mujoco
import numpy as np
from PIL import Image,ImageDraw,ImageFont


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--rollout',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--label',required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    record=json.loads(a.rollout.with_suffix('.json').read_text())
    model_path=a.rollout.with_suffix('.mjb')
    if digest(model_path)!=record['model_sha256']:raise ValueError('Saved model hash mismatch')
    model=mujoco.MjModel.from_binary_path(str(model_path));data=mujoco.MjData(model)
    model.vis.global_.offwidth=640;model.vis.global_.offheight=480
    model.vis.headlight.ambient[:]=.65;model.vis.headlight.diffuse[:]=.8
    renderer=mujoco.Renderer(model,height=480,width=640)
    cameras=[]
    for lookat,distance,azimuth,elevation in [([.64,-.02,.45],2.5,135,-20),([.54,.03,.52],1.35,115,-25)]:
        cam=mujoco.MjvCamera();cam.lookat[:]=lookat;cam.distance=distance;cam.azimuth=azimuth;cam.elevation=elevation;cameras.append(cam)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    names=['approach','align','grasp','lift','carry','load transfer','release','retreat']
    trace=np.load(a.rollout.with_suffix('.npz'),allow_pickle=False)
    chosen=list(range(0,len(trace['time']),5));chosen=sorted(set(chosen+[len(trace['time'])-1]))
    writer=imageio_ffmpeg.write_frames(str(a.output/'replay.mp4'),(1280,560),fps=10,codec='libx264',pix_fmt_out='yuv420p',output_params=['-movflags','+faststart'])
    writer.send(None);gif_frames=[]
    try:
        for i in chosen:
            data.qpos[:]=trace['qpos'][i];data.qvel[:]=trace['qvel'][i];data.ctrl[:]=trace['ctrl'][i]
            data.mocap_pos[:]=trace['mocap_pos'][i];data.mocap_quat[:]=trace['mocap_quat'][i]
            data.time=float(trace['time'][i]);mujoco.mj_forward(model,data)
            im=Image.new('RGB',(1280,560),(15,22,30));draw=ImageDraw.Draw(im)
            draw.text((12,8),f'{a.label} | office-v5 | t={data.time:.2f}s | {names[int(trace["stage"][i])]} | replay 2x',font=font,fill='white')
            draw.text((12,34),f'Task: {record["task_success"]} | strict: {record["strict_success"]} | max penetration {1000*record["stats"]["max_external_penetration_m"]:.6f} mm',font=font,fill=(255,215,130))
            for panel,cam in enumerate(cameras):
                renderer.update_scene(data,camera=cam);im.paste(Image.fromarray(renderer.render()),(640*panel,80))
            writer.send(np.asarray(im));gif_frames.append(im.resize((960,420)))
            if abs(data.time-5)<.11 or i==chosen[-1]:im.save(a.output/f'frame_{i:04d}.png')
    finally:writer.close();renderer.close();trace.close()
    gif_frames[0].save(a.output/'replay.gif',save_all=True,append_images=gif_frames[1:],duration=100,loop=0)
    manifest=dict(record=str(a.rollout),render_only=True,physics_rerun=False,source_sha256=digest(Path(__file__)),
                  input_sha256={ext:digest(a.rollout.with_suffix(ext)) for ext in ('.json','.npz','.mjb')},
                  output_sha256={ext:digest(a.output/('replay'+ext)) for ext in ('.mp4','.gif')},stride=5,playback_speed=2)
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
