from pathlib import Path
import os,sys,json,copy,time,hashlib
os.sched_setaffinity(0,{52})
import numpy as np
import torch
torch.set_num_threads(1)
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent
sys.path.insert(0,str(b/'runtime/source_train17_clock/source/tools'))
sys.path.insert(0,str(b/'runtime/serl_state_adapter_20261026_v1'))
sys.path.insert(0,str(b/'runtime/serl_multistep_gather_cycle11_20261026_v1'))
from train_serl_state_20261026 import Replay
from serl_multistep_state_adapter_20261026 import replay_class,SerlMultistepLearner
from serl_multistep_replay_gather_20261026 import optimized_class
from serl_multistep_batch_transfer_20261026 import transfer_class
from validate_serl_state_20261026 import digest
cp=b/'runs/serl_multistep_cycle10_archive_20261026_v1/direct/cycle_00010.pt'
reg=json.loads((out/'REGISTRATION.json').read_text())
with cp.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==reg['checkpoint_sha256']
for n,h in reg['source_hashes'].items():assert hashlib.sha256((out/n).read_bytes()).hexdigest()==h
ck=torch.load(cp,map_location='cpu',weights_only=False);before=digest(ck['learner'])
kwargs=dict(upstream=b/'runtime/serl_upstream_1fa2af7',upstream_manifest=b/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',dimension=7,direct=True,seed=20261026,device='cuda:0')
a=SerlMultistepLearner(b/'runtime/source_train17_clock',**kwargs);z=transfer_class(SerlMultistepLearner)(b/'runtime/source_train17_clock',**kwargs)
a.load_state_dict(copy.deepcopy(ck['learner']));z.load_state_dict(copy.deepcopy(ck['learner']));assert digest(a.state_dict())==digest(z.state_dict())==before
replay=optimized_class(replay_class(Replay))(7,49,27);replay.load_state_dict(copy.deepcopy(ck['replay']))
for size in [1,31,256,4096,32768,65536]:
 batch=replay.sample(size);assert digest(a.jax.device_get(a.batch(batch)))==digest(z.jax.device_get(z.batch(batch)))
batch=replay.sample(32768)
invalid=[]
for key in ['observations','next_observations']:
 for value in [np.full((2,49),np.nan,np.float32),np.zeros((2,48),np.float32),np.full((2,49),2.,np.float32)]:
  bad=dict(batch);bad[key]=value;invalid.append(bad)
for value in [np.zeros(1,np.float32),np.full(32768,np.nan,np.float32),np.full(32768,-.1,np.float32),np.full(32768,1.1,np.float32)]:
 bad=dict(batch);bad['_bootstrap']=value;invalid.append(bad)
bad=dict(batch);bad.pop('_bootstrap');invalid.append(bad)
for bad in invalid:
 for learner in [a,z]:
  try:learner.batch(bad)
  except ValueError:pass
  else:raise AssertionError('Invalid batch accepted')
rounds=[]
for i in range(5):
 row={}
 for name,learner in ([('original',a),('single_transfer',z)] if i%2==0 else [('single_transfer',z),('original',a)]):
  start=time.perf_counter()
  for _ in range(100):learner.jax.block_until_ready(learner.batch(batch))
  row[name]=(time.perf_counter()-start)/100
 rounds.append(row)
assert digest(a.state_dict())==digest(z.state_dict())==before
left=a.update(batch);right=z.update(batch);assert left==right and digest(a.state_dict())==digest(z.state_dict())
report=dict(passed=True,checkpoint_sha256=reg['checkpoint_sha256'],batch_pytree_exact=True,batch_sizes=[1,31,256,4096,32768,65536],invalid_batches_rejected_by_both=len(invalid),full_next_update_state_metrics_exact=True,auxiliary_critic_updates=16,auxiliary_actor_updates=2,rounds=rounds,median_seconds={k:float(np.median([r[k] for r in rounds])) for k in ['original','single_transfer']},weights_saved=False,live_training_changed=False,new_physics=0,limitation='Read-only transfer timing under concurrent formal11 and frozen10 inference. Not online throughput or pure-formal GPU compliance.',finished_unix=time.time())
(out/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
