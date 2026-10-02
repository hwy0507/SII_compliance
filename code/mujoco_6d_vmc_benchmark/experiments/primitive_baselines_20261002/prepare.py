"""Recover exact four video sources and register disjoint physical samples."""
import copy,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
OLD=Path('/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark')
IDS={'ball':'ball_013_000','push':'push_001_102','corner':'corner_013_repeat_1_901','table_corner':'table_corner_003_201'}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def main():
 anchors={}
 for scene,name in IDS.items():
  p=OLD/'outputs/esn128x128_four_scene_20260918/teacher_gallery'/name
  c=json.loads((p/'command.json').read_text());argv=c['argv'][2:];flags={};i=0
  while i<len(argv):
   key=argv[i][2:].replace('-','_');i+=1
   value=True if i==len(argv) or argv[i].startswith('--') else argv[i]
   if value is not True:i+=1
   flags[key]=value
  flags.pop('render',None);flags.pop('trace_output',None);flags.pop('output',None)
  entry=flags.pop('entry','render_compliance_audited.py')
  if entry=='run_loaded_push_audit_20260918.py':entry='run_core_vmc_push_20260918.py'
  if scene=='table_corner':
   flags['controller']='paper_mpc';flags['esn']=str(OLD/'outputs/esn_multiscene_capacity_best.npz');flags['no_render']=True
  anchors[scene]=dict(id=scene+'_reference',scene=scene,split='reference',entry=entry,flags=flags,environment=c['environment'],source=str(p),source_command_sha256=hashlib.sha256((p/'command.json').read_bytes()).hexdigest())
 rows=[]
 for split,count,seed in [('train',1000,720100),('validation',12,820100),('test',12,920100)]:
  for si,scene in enumerate(IDS):
   for i in range(count):
    f=copy.deepcopy(anchors[scene]);rng=np.random.default_rng(seed+si*100000+i);v=f['flags'];e=f['environment'];strength=(.35,.7,1.)[i%3]
    f.update(id=f'{scene}_{split}_{i:04d}',split=split,index=i);v['seed']=int(rng.integers(10000,99999999))
    if scene!='table_corner':e['DATASET_INITIAL_QDELTA']=json.dumps(rng.normal(0,.004*strength,7).tolist())
    if scene=='ball':
     v.update(ball_mass=float(rng.uniform(.25,.65)),ball_speed=float(rng.uniform(1.6,2.8)),ball_angle=float(rng.uniform(-.35,.35)),ball_height_offset=float(rng.uniform(-.008,.008)),shift=float(rng.uniform(.008,.028)),payload_mass=float(rng.uniform(.07,.13)),event_stage=('approach','pregrasp','loaded_lift')[i%3])
    elif scene=='push':
     v.update(push_angle=float(v['push_angle'])+float(rng.uniform(-.12,.12)*strength),push_height=float(v['push_height'])+float(rng.uniform(-.006,.006)*strength),push_stroke=float(v['push_stroke'])+float(rng.uniform(-.015,.008)*strength),push_press=float(v['push_press'])*float(rng.uniform(.9,1.1)),payload_mass=float(rng.uniform(.08,.12)),push_hold=1000000.)
     if i%5==4:v['event_stage']='loaded_lift'
    elif scene=='corner':
     v.update(yaw=float(v['yaw'])+float(rng.uniform(-.16,.16)*strength),shift=float(v['shift'])+float(rng.uniform(-.012,.012)*strength),width=float(v['width'])*float(rng.uniform(.88,1.12)),corner_height=float(v['corner_height'])+float(rng.uniform(-.012,.015)*strength),corner_friction=float(rng.uniform(.15,.45)),payload_mass=float(rng.uniform(.075,.13)))
    else:e.update(TABLE_X_SHIFT_M=str(-.01+float(rng.uniform(-.012,.012)*strength)),TABLE_HEIGHT_OFFSET_M=str(-.003+float(rng.uniform(-.004,.004)*strength)),INIT_JOINT_PERTURB_STD_RAD=str(float(rng.uniform(.0005,.003)*strength)))
    f['physical_hash']=digest({'flags':v,'environment':e});rows.append(f)
 assert len({f['physical_hash'] for f in rows})==len(rows)
 (ROOT/'ANCHORS.json').write_text(json.dumps(anchors,indent=2))
 (ROOT/'FIXTURES.json').write_text(json.dumps(rows,indent=2))
 (ROOT/'SOURCE_HASHES.json').write_text(json.dumps({str(p.relative_to(ROOT/'source_scene_20260918')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'source_scene_20260918').rglob('*.py'))},indent=2))
 print('registered',len(rows),'physical definitions, not completed trajectories')
if __name__=='__main__':main()
