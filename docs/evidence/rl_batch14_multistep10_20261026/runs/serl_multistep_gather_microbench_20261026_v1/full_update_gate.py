from pathlib import Path
import os,sys,json,copy,time
os.sched_setaffinity(0,{52})
import torch
torch.set_num_threads(1)
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent
sys.path.insert(0,str(b/'runtime/source_train17_clock/source/tools'))
sys.path.insert(0,str(b/'runtime/serl_state_adapter_20261026_v1'))
sys.path.insert(0,str(b/'runtime/serl_multistep_cycle10_20261026_v2'))
from train_serl_state_20261026 import Replay
from serl_multistep_state_adapter_20261026 import replay_class,SerlMultistepLearner
from serl_multistep_replay_gather_20261026 import optimized_class
from validate_serl_state_20261026 import digest
ck=torch.load(b/'runs/serl_multistep_preparation_20261026_v2/prepared_cycle09.pt',map_location='cpu',weights_only=False)
a=SerlMultistepLearner(b/'runtime/source_train17_clock',upstream=b/'runtime/serl_upstream_1fa2af7',upstream_manifest=b/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',dimension=7,direct=True,seed=20261026,device='cuda:0')
cls=replay_class(Replay);outcomes=[]
for impl in [cls,optimized_class(cls)]:
 replay=impl(7,49,27);replay.load_state_dict(copy.deepcopy(ck['replay']));a.load_state_dict(copy.deepcopy(ck['learner']));assert digest(a.state_dict())==digest(ck['learner'])
 metrics=a.update(replay.sample(32768));outcomes.append(dict(state=digest(a.state_dict()),rng=digest(replay.rng.bit_generator.state),metrics=metrics))
assert outcomes[0]==outcomes[1]
(out/'FULL_UPDATE_GATE.json').write_text(json.dumps(dict(passed=True,full_next_update_state_metrics_rng_exact=True,auxiliary_critic_updates=16,auxiliary_actor_updates=2,weights_saved=False,live_training_changed=False,completed_unix=time.time()),indent=2)+'\n')
