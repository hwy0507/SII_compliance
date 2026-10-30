from pathlib import Path
import os,sys,json,time,hashlib
D=Path(__file__).parent;B=D.parents[1];os.sched_setaffinity(0,{12});os.environ['CUDA_VISIBLE_DEVICES']=''
import torch
torch.set_num_threads(1)
sys.path[:0]=[str(D),str(B/'runtime/parameter86_frozen_switches_20261030_v1'),str(B/'runtime/source_train17_clock/source/tools')]
from published_compliance_learner_20261025 import PublishedLearner
from validate_published_finite_check_20261025 import digest
from evaluate_parameter29_seeded_switch_20261026 import gate
from half_std_probe import install_probe
rows=[]
for dimension in [5,7]:
 learner=PublishedLearner(B/'runtime/source_train17_clock',dimension=dimension,direct=False,seed=20261025,device='cpu',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True)
 observations=[[0.]*48 for _ in range(3)]
 install=install_probe(learner,observations,digest)
 result=gate(learner,{'steps':3600000},observations,2026102633,'active_short_train_0600',digest)
 assert result['passed']
 rows.append(dict(dimension=dimension,installation=install,native_gate=result))
(D/'PROBE_NATIVE_INTERFACE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),native_published_actor_clock_hook_exercised=True,methods=rows,random_initialization_interface_test_only=True,actual86_checkpoint_preflight_still_required=True,new_physics=0,new_optimizer_updates=0,probe_sha256=hashlib.sha256((D/'half_std_probe.py').read_bytes()).hexdigest()),indent=2)+'\n')
print('NATIVE HOOK AND BOTH ACTION DIMENSIONS PASS')
