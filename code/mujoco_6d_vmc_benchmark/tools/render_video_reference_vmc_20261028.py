"""Render the original video scene families from newly simulated VMC states."""
import argparse
import json
import os
from pathlib import Path
import subprocess
os.environ.setdefault('MUJOCO_GL', 'egl')
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from run_video_reference_vmc_20261028 import sha, write


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',type=Path,required=True)
    p.add_argument('--ffmpeg',type=Path,required=True)
    a=p.parse_args(); folder=a.scene.resolve(); kind=folder.name
    manifest=json.loads((folder/'execution.json').read_text())
    assert sha(folder/'scene.mjb')==manifest['model_sha256']
    with np.load(folder/'trajectory.npz') as z:
        trace={k:z[k] for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat')}
    model=mujoco.MjModel.from_binary_path(str(folder/'scene.mjb'));data=mujoco.MjData(model)
    model.vis.global_.offwidth=640;model.vis.global_.offheight=480
    model.vis.headlight.ambient[:]=.5;model.vis.headlight.diffuse[:]=.7
    views={
        'corner':[([.71,-.02,.49],1.50,45,-18),([.72,0.,.59],.65,90,-5)],
        'rod':[([.48,0.,.54],1.5,125,-25),([.54,0.,.64],1.,135,-12)],
        'ball':[([.44,0.,.34],1.6,135,-28),([.54,.025,.54],.9,90,-60)],
    }
    labels={'corner':'Thick table corner: pick below / apron contact / place',
            'rod':'Persistent rod with physical front/back guards',
            'ball':'Free ball impact / grasp and lift'}
    cams=[]
    for target,distance,azimuth,elevation in views[kind]:
        cam=mujoco.MjvCamera();cam.lookat[:]=target
        cam.distance=distance;cam.azimuth=azimuth;cam.elevation=elevation;cams.append(cam)
    out=folder/'media';out.mkdir(exist_ok=False)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
    renderer=mujoco.Renderer(model,height=480,width=640)
    proc=subprocess.Popen([str(a.ffmpeg),'-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
        '-s','1280x540','-r','25','-i','-','-an','-c:v','libx264','-crf','20','-threads','1',
        '-pix_fmt','yuv420p','-movflags','+faststart',str(out/'new30_vmc.mp4')],stdin=subprocess.PIPE)
    frames=[]
    try:
        for i,t in enumerate(trace['time']):
            for k in ('qpos','qvel','ctrl','mocap_pos','mocap_quat'):
                getattr(data,k)[:]=trace[k][i]
            data.time=float(t);mujoco.mj_forward(model,data)
            frame=Image.new('RGB',(1280,540),(16,23,31))
            for j,cam in enumerate(cams):
                renderer.update_scene(data,camera=cam)
                if kind=='rod' and j==1:
                    for g in renderer.scene.geoms[:renderer.scene.ngeom]:
                        if g.objtype==mujoco.mjtObj.mjOBJ_GEOM and g.objid>=0:
                            name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,g.objid) or ''
                            if name.startswith(('push_front_guard','push_back_guard')):
                                g.rgba[3]=.18
                frame.paste(Image.fromarray(renderer.render()),(j*640,60))
            draw=ImageDraw.Draw(frame)
            draw.text((12,7),f'new30 VMC teacher | {labels[kind]}',font=font,fill='white')
            draw.text((12,33),f't={t:.2f}s | 1x | actual saved trajectory'+
                      (' | RIGHT: transparent guards (render only)' if kind=='rod' else ''),font=font,fill=(180,220,230))
            proc.stdin.write(np.asarray(frame).tobytes())
            if i%2==0:frames.append(frame.resize((960,405)))
            if i in (0,len(trace['time'])//3,2*len(trace['time'])//3,len(trace['time'])-1):
                frame.save(out/f'preview_{i:04d}.png')
    finally:
        proc.stdin.close()
        assert proc.wait()==0
        renderer.close()
    frames[0].save(out/'new30_vmc.gif',save_all=True,append_images=frames[1:],duration=80,loop=0)
    with Image.open(out/'new30_vmc.gif') as gif:
        assert gif.n_frames==len(frames)
        for i in range(gif.n_frames):gif.seek(i);gif.load()
    subprocess.run([str(a.ffmpeg),'-v','error','-threads','1','-i',str(out/'new30_vmc.mp4'),'-f','null','-'],check=True)
    write(out/'manifest.json',dict(physics_rerun=False,all_gif_frames_decoded=True,mp4_full_decode=True,
        frames=len(trace['time']),gif_frames=len(frames),fps=25.,playback_speed=1.,
        simulation_interval_s=[float(trace['time'][0]),float(trace['time'][-1])],
        model_sha256=sha(folder/'scene.mjb'),trace_sha256=sha(folder/'trajectory.npz'),
        render_source_sha256=sha(Path(__file__)),
        media_sha256={ext:sha(out/('new30_vmc'+ext)) for ext in ('.gif','.mp4')}))


if __name__=='__main__':main()
