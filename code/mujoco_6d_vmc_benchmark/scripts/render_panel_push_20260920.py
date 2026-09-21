"""Render audited physics states without changing or re-running the motion."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import imageio_ffmpeg
import numpy as np
os.environ.setdefault('MUJOCO_GL','egl')
import mujoco
from PIL import Image,ImageDraw,ImageFont


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    parser.add_argument('--preview-at',type=float)
    parser.add_argument('--start',type=float,default=0.)
    parser.add_argument('--end',type=float,default=float('inf'))
    parser.add_argument('--slowdown',type=float,default=1.)
    parser.add_argument('--prefix',default='rollout')
    parser.add_argument('--close-distance',type=float,default=1.0)
    parser.add_argument('--contact-object',default='push_rod_geom')
    args=parser.parse_args();dest=args.directory
    metadata=json.loads((dest/'rollout.json').read_text())
    workstation=metadata.get('experiment_contract',{}).get('panel_config',{}).get('workstation',False)
    m=mujoco.MjModel.from_binary_path(str(dest/'rollout.mjb'));d=mujoco.MjData(m)
    arr=np.load(dest/'physics_states.npz')
    contact_path=dest/'contact_samples.npz'
    contact=np.load(contact_path) if contact_path.exists() else None
    rod_col=(1+2*list(contact['names']).index(args.contact_object)) if contact is not None else None
    contact_label={'push_rod_geom':'ROD','push_front_guard':'FRONT GUARD','push_back_guard':'REAR GUARD'}.get(args.contact_object,args.contact_object)
    renderer=mujoco.Renderer(m,height=480,width=640)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    cams=[]
    for target,distance,azimuth,elevation in [([.48,0,.54],1.5,125,-25),([.54,0,.64],args.close_distance,135,-12)]:
        c=mujoco.MjvCamera();c.type=mujoco.mjtCamera.mjCAMERA_FREE
        c.lookat[:]=target;c.distance=distance;c.azimuth=azimuth;c.elevation=elevation
        cams.append(c)
    frames=[]
    indices=[i for i in range(0,len(arr['state']),2) if args.start<=arr['state'][i,0]<=args.end]
    if args.preview_at is not None:
        indices=[int(np.argmin(np.abs(arr['state'][:,0]-args.preview_at)))]
    proc=None
    if args.preview_at is None:
        proc=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x540','-r',str(12.5/args.slowdown),'-i','-','-an','-c:v','libx264','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart',str(dest/(args.prefix+'.mp4'))],stdin=subprocess.PIPE)
    for i in indices:
        if arr is not None:
            state=arr['state'][i];nq,nv,nu=int(arr['nq']),int(arr['nv']),int(arr['nu'])
            d.time=float(state[0]);d.qpos[:]=state[1:1+nq];d.qvel[:]=state[1+nq:1+nq+nv];d.ctrl[:]=state[1+nq+nv:1+nq+nv+nu]
        mujoco.mj_forward(m,d)
        im=Image.new('RGB',(1280,540),(18,25,34))
        for k,c in enumerate(cams):
            renderer.update_scene(d,camera=c)
            if workstation:
                # Dormant legacy disturbance marker; never activated in
                # these pusher fixtures. Hide its drawing only, leaving the
                # recorded model and all task collision shapes untouched.
                for g in renderer.scene.geoms[:renderer.scene.ngeom]:
                    if g.objtype==mujoco.mjtObj.mjOBJ_GEOM and g.objid>=0 and mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g.objid)=='moving_obstacle_geom':
                        g.rgba[3]=0.
            if k==1:
                # Rendering-only transparency: the stored MjModel, its
                # collisions, and recorded physics states are untouched.
                for g in renderer.scene.geoms[:renderer.scene.ngeom]:
                    if g.objtype==mujoco.mjtObj.mjOBJ_GEOM and g.objid>=0:
                        name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,g.objid) or ''
                        if name.startswith(('push_front_guard','push_back_guard')):
                            g.rgba[3]=.13
                for gid in range(m.ngeom):
                    name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,gid) or ''
                    if not name.startswith(('push_front_guard','push_back_guard')):continue
                    corners=np.array([[sx,sy,sz] for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)])*m.geom_size[gid]
                    corners=corners@d.geom_xmat[gid].reshape(3,3).T+d.geom_xpos[gid]
                    for a in range(8):
                        for bit in (1,2,4):
                            b=a^bit
                            if b<a:continue
                            g=renderer.scene.geoms[renderer.scene.ngeom]
                            mujoco.mjv_initGeom(g,mujoco.mjtGeom.mjGEOM_CAPSULE,np.zeros(3),np.zeros(3),np.eye(3).ravel(),np.array([.25,.65,.95,1.]))
                            mujoco.mjv_connector(g,mujoco.mjtGeom.mjGEOM_CAPSULE,.0008,corners[a],corners[b])
                            renderer.scene.ngeom+=1
            im.paste(Image.fromarray(renderer.render()),(k*640,60))
        dr=ImageDraw.Draw(im)
        title='6D VMC | open picking workstation | proprioceptive contact response' if workstation else '6D VMC | persistent rod | physical front/back panels | original grasp + lift'
        dr.text((12,5),title,font=font,fill='white')
        if contact is None:
            caption=f't = {d.time:.2f} s     LEFT: solid panels     RIGHT: transparent view only; identical collisions'
            color=(159,218,246)
        else:
            fraction=contact['samples'][i,rod_col]/.04
            peak=contact['samples'][i,rod_col+1]
            caption=f't={d.time:.2f}s | {contact_label} contact {fraction:.0%} of last 40ms; peak {peak:.1f}N | RIGHT: transparent panels'
            color=(100,255,150) if fraction>0 else (159,218,246)
        dr.text((12,30),caption,font=font,fill=color)
        if proc is not None:
            proc.stdin.write(im.tobytes())
        frames.append(im.resize((960,405)))
    if args.preview_at is not None:
        frames[0].save(dest/'view_preview.png');renderer.close();return
    if proc is not None:
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError('video encoding failed')
    if args.prefix=='rollout':
        frames[0].save(dest/'start.png')
        for fraction in (0.25,0.5,0.75,1.):
            frames[min(len(frames)-1,int(fraction*(len(frames)-1)))].save(dest/f'frame_{int(fraction*100):03d}.png')
    if len(frames)>1:
        frames[0].save(dest/(args.prefix+'.gif'),save_all=True,append_images=frames[1:],duration=round(80*args.slowdown),loop=0,optimize=False)
    renderer.close()
    print(str(dest/(args.prefix+'.mp4')),flush=True)


if __name__=='__main__':main()
