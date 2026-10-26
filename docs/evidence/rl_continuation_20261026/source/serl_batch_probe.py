import os
os.sched_setaffinity(0, {0})
from pathlib import Path
import sys,json,time,copy,hashlib
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).parent
sys.path.insert(0,str(B/'runtime/serl_state_adapter_20261026_v1'))
from serl_state_adapter_20261026 import SerlStateLearner
from validate_serl_state_20261026 import digest
reg=json.loads((OUT/'REGISTRATION.json').read_text())
with Path(reg['checkpoint']).open('rb') as f:
    assert hashlib.file_digest(f,'sha256').hexdigest()==reg['checkpoint_sha256']
x=torch.load(reg['checkpoint'],map_location='cpu',weights_only=False)
assert x['boundary']=='complete_condition_cycle' and x['cycle']==1
a=SerlStateLearner(B/'runtime/source_train17_clock',upstream=B/'runtime/serl_upstream_1fa2af7',
    upstream_manifest=B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',dimension=7,direct=True,seed=20261026,device='cuda:0')
arrays=x['replay']['arrays'];results=[]
initial=digest(x['learner'])
for size in reg['batch_sizes']:
    a.load_state_dict(copy.deepcopy(x['learner']))
    assert digest(a.state_dict())==initial
    rng=np.random.default_rng(20261026)
    def batch():
        idx=rng.integers(x['replay']['size'],size=size)
        return {k:v[idx] for k,v in arrays.items()}
    # One explicit compile/update, then restore; excluded from throughput timing.
    a.update(batch())
    a.load_state_dict(copy.deepcopy(x['learner']))
    assert digest(a.state_dict())==initial
    rng=np.random.default_rng(20261026)
    start=time.monotonic()
    for i in range(reg['outer_updates_per_arm']):
        metrics=a.update(batch())
    elapsed=time.monotonic()-start
    assert a.outer_updates-x['learner']['outer_updates']==reg['outer_updates_per_arm']
    assert digest(x['learner'])==initial
    row=dict(batch_size=size,critic_batch_size=size//8,outer_updates=reg['outer_updates_per_arm'],
        duration_s=elapsed,outer_updates_per_s=reg['outer_updates_per_arm']/elapsed,
        sampled_rows_per_s=reg['outer_updates_per_arm']*size/elapsed,
        finite_state=True,last_metrics=metrics,parent_state_unchanged=True)
    results.append(row)
    (OUT/'PROGRESS.json').write_text(json.dumps(row,indent=2)+'\n')
report=dict(results=results,total_auxiliary_critic_updates=8*len(results)*(reg['outer_updates_per_arm']+1),
    compile_updates_included_in_budget=True,new_physics=0,weights_saved=False,weight_promotion=False,
    limitation='Short throughput/finite-state measurement. Different batch sizes change gradients; no policy or convergence conclusion.')
(OUT/'FINISHED.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
