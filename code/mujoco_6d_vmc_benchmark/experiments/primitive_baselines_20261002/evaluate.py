"""Deterministic evaluation against the immutable campaign worker.

Validation is a diagnostic; fixed step budgets, global classical selection and
reserved test fixtures are chosen independently of validation performance.
"""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
FROZEN=ROOT/'frozen_adapter02'/'primitive_baselines_20261002'
sys.path.insert(0,str(FROZEN))
import train as frozen_train
from train import Episode,OfficialOfficeAgent,dump,SCENES

def sha(p):
 return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def normalization_hash(agent):
    """Fingerprint full normalizer state, including moments and return accumulator."""
    digest=hashlib.sha256()
    normalizers=[('obs',agent.observation_normalizer.obs_rms),('reward',agent.reward_normalizer.G_rms)]
    for prefix,state in normalizers:
        for key in ('mean','var','count'):
            value=np.asarray(getattr(state,key))
            digest.update((prefix+'.'+key+str(value.shape)+str(value.dtype)).encode());digest.update(value.tobytes())
    for key in ('G','G_r_max'):
        value=np.asarray(getattr(agent.reward_normalizer,key))
        digest.update((key+str(value.shape)+str(value.dtype)).encode());digest.update(value.tobytes())
    return digest.hexdigest()

def evaluate(a):
 out=a.output;out.mkdir(parents=True,exist_ok=False)
 worker_path=FROZEN/'worker.py'
 if a.detailed_contact:
  frozen_train.HERE=Path(__file__).resolve().parent/'contact_audit';worker_path=frozen_train.HERE/'worker.py'
 fixtures=json.loads((ROOT/'ANCHORS.json').read_text())
 if a.split=='reference':fs=[fixtures[s] for s in SCENES]
 else:fs=[f for f in json.loads((ROOT/'FIXTURES.json').read_text()) if f['split']==a.split and f['index'] in a.indices]
 if a.scenes:fs=[f for f in fs if f['scene'] in a.scenes]
 agent=None;checkpoint_hashes=None;parameters={}
 if a.method=='rl':
  if a.checkpoint is None:raise ValueError('RL requires checkpoint')
  state=json.loads((a.checkpoint/'official_agent_state.json').read_text());c=state['config'];utd=state['utd']
  agent=OfficialOfficeAgent(c['seed'],int(c['learning_rate_decay_step'])//utd,utd=utd,gamma=c['gamma'],entropy_coef=c['temp_target_entropy_coef'],initial_temperature=c['temp_initial_value'])
  agent.load(a.checkpoint);before=agent.diagnostics();normalization_before=normalization_hash(agent)
  checkpoint_hashes={str(p.relative_to(a.checkpoint)):sha(p) for p in a.checkpoint.rglob('*') if p.is_file() and p.name!='replay.npz'}
 elif a.method in ('admittance','impedance'):
  if a.selection is None:raise ValueError('Classical evaluation requires saved train-only selection')
  selected=json.loads(a.selection.read_text())['selected'][a.method];parameters=selected['parameters']
 protocol=dict(method=a.method,split=a.split,fixtures=[f['id'] for f in fs],checkpoint=str(a.checkpoint) if a.checkpoint else None,checkpoint_hashes=checkpoint_hashes,normalization_hash=normalization_before if agent else None,parameters=parameters,selection=str(a.selection) if a.selection else None,worker=str(worker_path),worker_sha256=sha(worker_path),frozen_worker_sha256=sha(FROZEN/'worker.py'),deterministic=True,save_substeps=True,source_sha256=sha(__file__),started_epoch=time.time(),physical_gate='external penetration <= 0.2 mm and finite peak torque; not a complete physical certificate',contact_gate='nonzero force exposure to scene-specific obstacle geoms')
 dump(out/'PROTOCOL.json',protocol);rows=[]
 for f in fs:
  epout=out/f['id'];request=dict(fixture=f,method=a.method,parameters=parameters,output=str(epout),save_substeps=True)
  if agent:
   episode=Episode(request)
   try:
    event=episode.read()
    while event['kind']!='terminal':
     action=agent.sample_action(np.asarray(event['observation'],np.float32),training=False)
     event=episode.step(action)
    episode.close();row=event['result']
   except RuntimeError as exc:
    if episode.p.poll() is None:episode.p.terminate()
    episode.p.wait(timeout=60);episode.err.close()
    if 'Initial robot/obstacle overlap' not in str(exc) and 'Randomized initial state overlaps' not in str(exc):raise
    row=dict(fixture_id=f['id'],scene=f['scene'],method=a.method,initial_state_rejected=True,error=str(exc))
   after=agent.diagnostics()
   if before!=after or normalization_before!=normalization_hash(agent):raise RuntimeError('Evaluation mutated training statistics')
  else:
   rp=out/(f['id']+'_request.json');dump(rp,request)
   with (out/(f['id']+'_process.log')).open('w') as log:
    rc=subprocess.run([sys.executable,str(worker_path),'--request',str(rp)],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'),timeout=900).returncode
   if rc:
    error=(epout/'ERROR.txt').read_text() if (epout/'ERROR.txt').exists() else 'Worker failed without error record'
    if 'Initial robot/obstacle overlap' not in error and 'Randomized initial state overlaps' not in error:raise RuntimeError(error)
    row=dict(fixture_id=f['id'],scene=f['scene'],method=a.method,initial_state_rejected=True,error=error)
   else:row=json.loads((epout/'result.json').read_text())
  row['evaluation_output']=str(epout);rows.append(row);dump(out/'ROWS.json',rows)
  dump(out/'STATE.json',dict(completed=len(rows),total=len(fs),latest=f['id']))
  print(json.dumps(dict(completed=len(rows),total=len(fs),fixture=f['id'],task=row.get('task_success'),physical=row.get('physical_valid'),contact=row.get('contact_exposed'))),flush=True)
 dump(out/'COMPLETE.json',dict(completed=len(rows),finished_epoch=time.time(),normalizers_unchanged=True if agent else None))

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--method',choices=['rl','admittance','impedance','zero'],required=True);p.add_argument('--checkpoint',type=Path);p.add_argument('--selection',type=Path);p.add_argument('--split',choices=['reference','validation','test'],required=True);p.add_argument('--indices',type=int,nargs='+',default=[0,1,2]);p.add_argument('--scenes',nargs='+',choices=SCENES);p.add_argument('--detailed-contact',action='store_true');evaluate(p.parse_args())
if __name__=='__main__':main()
