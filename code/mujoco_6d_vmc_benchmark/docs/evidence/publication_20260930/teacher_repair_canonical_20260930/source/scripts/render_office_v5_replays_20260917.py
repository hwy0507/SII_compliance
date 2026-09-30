"""Bright replay of recorded simulation states; never alters physics results."""
import argparse,hashlib,json,os
from pathlib import Path
os.environ.setdefault('MUJOCO_GL','egl')
import mujoco,numpy as np,imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
from audit_office_complex_scene_v5_20260917 import make

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/office_complex_scene_v5_20260917'


def render(stem):
    result=json.loads((OUT/(stem+'.json')).read_text())
    expected=result['source_sha256']['office_complex_scene_v5_20260917.py']
    actual=hashlib.sha256((ROOT/'scripts/office_complex_scene_v5_20260917.py').read_bytes()).hexdigest()
    if actual!=expected:raise ValueError('Geometry changed after recorded rollout')
    env,_,_=make(result['fixture']);m,d=env.model,env.data
    # The backend parks its obsolete diagnostic mocap outside the workspace
    # on every physics step. qpos does not include mocap state; restore this
    # constant too, otherwise a phantom legacy red sphere appears in replay.
    d.mocap_pos[env._obstacle_mocap]=[3.,3.,3.]
    m.vis.global_.offwidth=640;m.vis.global_.offheight=480
    m.vis.headlight.ambient[:]=[.65,.65,.65];m.vis.headlight.diffuse[:]=[.8,.8,.8];m.vis.headlight.specular[:]=[.15,.15,.15]
    renderer=mujoco.Renderer(m,height=480,width=640)
    overview=mujoco.MjvCamera();overview.lookat[:]=[.64,-.02,.45];overview.distance=2.5;overview.azimuth=135;overview.elevation=-20
    detail=mujoco.MjvCamera();detail.lookat[:]=[.60,-.10,.61];detail.distance=1.20;detail.azimuth=105;detail.elevation=-22
    out=OUT/'media';out.mkdir(exist_ok=True)
    writer=imageio_ffmpeg.write_frames(str(out/(stem+'.mp4')),(1280,528),fps=25,codec='libx264',output_params=['-movflags','+faststart']);writer.send(None)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
    frames=[]
    with np.load(OUT/(stem+'.npz')) as a:
        for i,t in enumerate(a['time']):
            d.qpos[:]=a['qpos'][i];mujoco.mj_forward(m,d)
            renderer.update_scene(d,camera=overview);left=Image.fromarray(renderer.render())
            renderer.update_scene(d,camera=detail);right=Image.fromarray(renderer.render())
            frame=Image.new('RGB',(1280,528),(25,33,44));frame.paste(left,(0,48));frame.paste(right,(640,48))
            label='WBC pose-hold apparatus check' if stem=='demo_25us' else 'WBC pick / carry / place integration'
            stage=int(a['stage'][i])
            ImageDraw.Draw(frame).text((12,12),f'{label} | recorded t={t:.2f}s | stage {stage} | no learned controller',font=font,fill='white')
            writer.send(np.asarray(frame));frames.append(frame)
    writer.close();renderer.close();env.close()
    frames[0].save(out/(stem+'.png'))
    if stem=='demo_25us':
        frames[0].save(out/(stem+'.gif'),save_all=True,append_images=frames[1:],duration=40,loop=0)
        for second in (.12,5.,13.):frames[min(len(frames)-1,round(second/.04))].save(out/(stem+f'_at_{second:g}.png'))
    print(json.dumps(dict(stem=stem,frames=len(frames),duration_s=len(frames)/25,geometry_sha_verified=True)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stem',choices=('demo_25us','task_integration'),required=True)
    render(p.parse_args().stem)
