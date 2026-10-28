"""Inspect two completed office traces at fixed saved times, without stepping.

Forward kinematics/contact geometry is recomputed from saved qpos/mocap.
This is not a dynamics replay or a replacement for saved physical audits.
Orange marks the unexpected edge, green the carried object, for display only.
"""
import argparse
import os
from pathlib import Path
os.environ.setdefault('MUJOCO_GL','egl')

import mujoco
import numpy as np
from PIL import Image,ImageDraw,ImageFont

from collect_special_scene_actions_20261028 import read,sha,write


def render(baseline,candidate,output):
    assert not output.exists()
    frames=[];rows=[];model_hash=None
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    for label,folder in (('historical',baseline),('candidate',candidate)):
        audit=read(folder/'AUDIT.json');assert audit['full_horizon']
        assert sha(folder/'rollout.npz')==audit['trace_sha256']
        assert sha(folder/'rollout.mjb')==audit['model_sha256']
        if model_hash:assert model_hash==audit['model_sha256']
        else:model_hash=audit['model_sha256']
        with np.load(folder/'rollout.npz',allow_pickle=False) as trace:
            arrays={k:trace[k].copy() for k in ('time','qpos','qvel','ctrl','mocap_pos','mocap_quat','stage','hand')}
        model=mujoco.MjModel.from_binary_path(str(folder/'rollout.mjb'))
        data=mujoco.MjData(model)
        model.vis.global_.offwidth=400;model.vis.global_.offheight=300
        model.vis.headlight.ambient[:]=.65;model.vis.headlight.diffuse[:]=.8
        edge=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'office_v5_unexpected_edge')
        payload=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'target_object_geom')
        hand=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'hand')
        assert min(edge,payload,hand)>=0
        renderer=mujoco.Renderer(model,height=300,width=400)
        try:
            for target_time in (24.,46.,54.):
                i=int(np.argmin(np.abs(arrays['time']-target_time)))
                for key in ('qpos','qvel','ctrl','mocap_pos','mocap_quat'):
                    getattr(data,key)[:]=arrays[key][i]
                data.time=float(arrays['time'][i]);mujoco.mj_forward(model,data)
                contacts=[]
                for j in range(data.ncon):
                    contact=data.contact[j]
                    if edge in (contact.geom1,contact.geom2):
                        contacts.append(dict(geoms=[mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,int(g)) for g in (contact.geom1,contact.geom2)],
                            separation_m=float(contact.dist),world_contact_position=contact.pos.tolist()))
                panel=Image.new('RGB',(400,650),(15,22,30));draw=ImageDraw.Draw(panel)
                draw.text((8,5),f'{label} | t={data.time:.2f}s | stage={int(arrays["stage"][i])}',font=font,fill='white')
                draw.text((8,27),f'Task={audit["task_success"]}, Strict={audit["strict_success"]}',font=font,fill='white')
                for k,(azimuth,elevation,distance) in enumerate(((90,-12,.65),(90,-80,.65))):
                    camera=mujoco.MjvCamera();camera.lookat[:]=data.geom_xpos[edge]
                    camera.distance=distance;camera.azimuth=azimuth;camera.elevation=elevation
                    renderer.update_scene(data,camera=camera)
                    for geom in renderer.scene.geoms[:renderer.scene.ngeom]:
                        if geom.objtype==mujoco.mjtObj.mjOBJ_GEOM:
                            if geom.objid==edge:geom.rgba[:]=[1.,.35,.02,1.]
                            elif geom.objid==payload:geom.rgba[:]=[.1,1.,.2,1.]
                    panel.paste(Image.fromarray(renderer.render()),(0,50+300*k))
                frames.append(panel)
                rows.append(dict(label=label,folder=str(folder),frame=i,saved_time_s=data.time,
                    task=audit['task_success'],strict=audit['strict_success'],
                    edge_center=data.geom_xpos[edge].tolist(),edge_halfsize=model.geom_size[edge].tolist(),
                    reconstructed_hand=data.xpos[hand].tolist(),reconstructed_object=data.geom_xpos[payload].tolist(),
                    saved_vs_forward_hand_distance_m=float(np.linalg.norm(arrays['hand'][i]-data.xpos[hand])),
                    reconstructed_edge_contacts=contacts,
                    inputs={n:sha(folder/n) for n in ('AUDIT.json','rollout.npz','rollout.mjb')}))
        finally:renderer.close()
    output.mkdir(parents=True)
    canvas=Image.new('RGB',(1200,1330),(15,22,30))
    ImageDraw.Draw(canvas).text((10,6),'Saved-state inspection only | orange: unexpected edge | green: payload | side / top',font=font,fill='white')
    for k,frame in enumerate(frames):canvas.paste(frame,((k%3)*400,30+(k//3)*650))
    canvas.save(output/'edge_states.png')
    write(output/'REVIEW.json',dict(status='complete',physics_steps=0,rows=rows,
        model_sha256=model_hash,source_sha256=sha(Path(__file__)),image_sha256=sha(output/'edge_states.png'),
        limitation='Saved qpos forward-geometry reconstruction, no dynamics integration/contact-force replay. Saved xpos can precede the last physics integration, so its measured discrepancy is reported. Display colors/cameras do not alter source MJB, labels or gates.'))
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','candidate','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();render(a.baseline.resolve(),a.candidate.resolve(),a.output.resolve())
