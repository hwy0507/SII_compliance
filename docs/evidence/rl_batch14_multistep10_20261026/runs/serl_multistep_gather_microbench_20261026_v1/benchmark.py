from pathlib import Path
import os,sys,json,time,copy,hashlib
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent
sys.path.insert(0,str(b/'runtime/source_train17_clock/source/tools'))
sys.path.insert(0,str(b/'runtime/serl_state_adapter_20261026_v1'))
sys.path.insert(0,str(b/'runtime/serl_multistep_cycle10_20261026_v2'))
from train_serl_state_20261026 import Replay
from serl_multistep_state_adapter_20261026 import replay_class
from serl_multistep_replay_gather_20261026 import optimized_class
from validate_published_finite_check_20261025 import digest
cp=b/'runs/serl_multistep_preparation_20261026_v2/prepared_cycle09.pt'
ck=torch.load(cp,map_location='cpu',weights_only=False);state=ck['replay'];before=digest(state)
base=replay_class(Replay);fast=optimized_class(base);a=base(7,49,27);z=fast(7,49,27)
a.load_state_dict(copy.deepcopy(state));z.load_state_dict(copy.deepcopy(state));assert digest(a.state_dict())==digest(z.state_dict())==before
for size in [1,31,32,256,4096,32768,65536]*4:
 left,right=a.sample(size),z.sample(size)
 assert set(left)==set(right)
 for key in left:np.testing.assert_array_equal(left[key],right[key])
 assert digest(a.rng.bit_generator.state)==digest(z.rng.bit_generator.state)
rows=[]
for rep in range(5):
 pair={}
 for label,obj in ([('original',a),('optimized',z)] if rep%2==0 else [('optimized',z),('original',a)]):
  obj.rng.bit_generator.state=copy.deepcopy(state['rng'])
  start=time.perf_counter()
  for _ in range(100):obj.sample(32768)
  pair[label]=(time.perf_counter()-start)/100
 assert digest(a.rng.bit_generator.state)==digest(z.rng.bit_generator.state)
 rows.append(pair)
assert digest(state)==before
report=dict(passed=True,exact_batch_comparisons=28,fields_exact=True,rng_exact=True,rounds=rows,median_seconds={key:float(np.median([v[key] for v in rows])) for key in ['original','optimized']},new_physics=0,optimizer_updates=0,live_training_changed=False,limitation='CPU-only frozen replay microbenchmark under concurrent formal workload; no proven online speedup, no change deployed to current10.')
(out/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
