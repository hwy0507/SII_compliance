"""Render immutable saved states, without advancing or re-simulating physics."""
import argparse,hashlib,json,os
from pathlib import Path
os.environ.setdefault('MUJOCO_GL','egl')
import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def main():
 p=argparse.ArgumentParser();p.add_argument('episode',type=Path);p.add_argument('--output',type=Path);p.add_argument('--label',default='');a=p.parse_args();e=a.episode;out=a.output or e/'media';out.mkdir(parents=True,exist_ok=True)
 if (out/'RENDER.json').exists():raise FileExistsError(out/'RENDER.json')
 result=json.loads((e/'result.json').read_text());states=np.load(e/'render_states.npz');scene=result['scene'];m=mujoco.MjModel.from_binary_path(str(e/'model.mjb'));d=mujoco.MjData(m)
 m.vis.global_.offwidth=640;m.vis.global_.offheight=480
 renderer=mujoco.Renderer(m,height=480,width=640)
 overview=mujoco.MjvCamera();overview.type=mujoco.mjtCamera.mjCAMERA_FREE;overview.lookat[:]=[.44,0.,.34];overview.distance=1.6;overview.azimuth=135;overview.elevation=-28
 detail=mujoco.MjvCamera();detail.type=mujoco.mjtCamera.mjCAMERA_FREE
 if scene=='table_corner':
  overview.lookat[:]=[.50,0,.48];overview.distance=1.55;overview.elevation=-22;detail.lookat[:]=[.70,0,.64];detail.distance=.82;detail.azimuth=90;detail.elevation=-8
 elif scene=='push':
  detail.lookat[:]=[.55,-.01,.56];detail.distance=.78;detail.azimuth=140;detail.elevation=-12
 elif scene=='corner':
  detail.lookat[:]=[.57,0,.56];detail.distance=.9;detail.azimuth=95;detail.elevation=-22
 else:
  detail.lookat[:]=[.54,.025,.54];detail.distance=.9;detail.azimuth=90;detail.elevation=-60
 # The shared source moves its diagnostic mocap far outside the scene every step.
 # Other mocaps are nominal/actual visualization markers, also hidden for replay.
 # No moving physical geometry uses these three diagnostic/marker mocaps.
 mocap_names=[]
 for body in range(m.nbody):
  i=int(m.body_mocapid[body])
  if i>=0:
   name=mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_BODY,body);mocap_names.append(name)
   if name not in ['moving_obstacle','nominal_marker','actual_marker']:raise ValueError('Unrecorded physical mocap: '+str(name))
   d.mocap_pos[i]=[3,3,3];d.mocap_quat[i]=[1,0,0,0]
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
 label=a.label or result['method'];times=states['time'];maxerr=0.
 def frame(i,speed_label):
  d.qpos[:]=states['qpos'][i];d.qvel[:]=states['qvel'][i];d.ctrl[:]=states['ctrl'][i];d.time=float(times[i]);mujoco.mj_forward(m,d)
  canvas=Image.new('RGB',(1280,544),(12,20,28));draw=ImageDraw.Draw(canvas)
  draw.text((12,7),f'{scene} | {label} | {times[i]:.3f} s | {speed_label}',font=font,fill='white')
  draw.text((12,33),f'Task {result["task_success"]} | intended contact {result["contact_exposed"]} | RMSE {result["rmse_m"]:.4f} m | peak torque {result["peak_torque_nm"]:.1f} Nm',font=font,fill=(177,211,200))
  for j,cam in enumerate([overview,detail]):
   renderer.update_scene(d,camera=cam);canvas.paste(Image.fromarray(renderer.render()),(640*j,64))
  return np.asarray(canvas)
 requested=np.arange(0,float(times[-1]),.04);indices=np.clip(np.searchsorted(times,requested,side='left'),0,len(times)-1)
 with imageio.get_writer(str(out/'full_1x.mp4'),fps=25,codec='libx264',quality=8,macro_block_size=16,ffmpeg_params=['-movflags','+faststart']) as w:
  for target,i in zip(requested,indices):
   maxerr=max(maxerr,abs(float(times[i]-target)));w.append_data(frame(int(i),'1x; saved states'))
 prefix={'ball':'primitive_free_ball','push':'push_rod','corner':'primitive_corner','table_corner':'table_side'}[scene]
 contacts=[v for k,v in result['contacts'].items() if prefix in k]
 first=min((v['first_s'] for v in contacts),default=None)
 contactframes=[]
 if first is not None:
  select=np.flatnonzero((times>=max(0,first-.35)) & (times<=first+.65))
  with imageio.get_writer(str(out/'contact_025x.mp4'),fps=25,codec='libx264',quality=9,macro_block_size=16,ffmpeg_params=['-movflags','+faststart']) as w:
   for i in select:w.append_data(frame(int(i),'0.25x contact replay; 100 Hz states'))
  for delta in [-.12,-.04,0,.02,.06,.14]:
   i=int(np.argmin(abs(times-(first+delta))));contactframes.append(Image.fromarray(frame(i,'contact frames')).resize((640,272)))
  sheet=Image.new('RGB',(1280,816))
  for j,im in enumerate(contactframes):sheet.paste(im,((j%2)*640,(j//2)*272))
  sheet.save(out/'contact_sheet.jpg',quality=94)
 posteridx=int(np.argmin(abs(times-(first+.03 if first is not None else min(2,times[-1])))))
 Image.fromarray(frame(posteridx,'1x; saved states')).save(out/'poster.jpg',quality=94)
 renderer.close()
 metadata=dict(episode=str(e),label=label,model_sha256=hashlib.sha256((e/'model.mjb').read_bytes()).hexdigest(),states_sha256=hashlib.sha256((e/'render_states.npz').read_bytes()).hexdigest(),mujoco=mujoco.__version__,nq=m.nq,nv=m.nv,nmocap=m.nmocap,frame_count=len(indices),fps=25,simulation_duration_s=float(times[-1]),video_duration_s=len(indices)/25,max_sample_time_error_s=maxerr,first_intended_contact_s=first,physics_advanced=False,interpolation=False,diagnostic_mocap_position=[3,3,3],hidden_mocaps=mocap_names,limitations=['State replay uses archived initial MJB; no new physical metrics inferred from replay.', '100 Hz replay resolves motion, not native substep contact force.', 'Global metrics displayed summarize entire episode, not current frame.'])
 (out/'RENDER.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata),flush=True)
if __name__=='__main__':main()
