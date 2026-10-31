from pathlib import Path
import sys,json,time
import numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).resolve().parent
sys.path[:0]=[str(D),str(B/'runtime/violation93_continuation_20261031_v1'),str(B/'runtime/source_train17_clock/source/tools')]
from census_native import CensusCache
from train_published_compliance_20261025 import Replay
r=Replay(1,52,123,capacity=8)
a=np.zeros(52,np.float32)
r.add(observations=a,next_observations=a,actions=np.zeros(1,np.float32),rewards=np.zeros(1,np.float32),dones=np.ones(1,np.float32))
c=CensusCache(r,'cuda:0');assert len(c.terminal_indices)==1
state=dict(r.state_dict());state['size']=0;state['cursor']=0;state['arrays']={k:v[:0] for k,v in state['arrays'].items()}
c.load_state_dict(state)
result=dict(time=time.time(),expected_terminal_count=0,indices_count=len(c.terminal_indices),cached_tensor_rows=len(c.terminal['rewards']),defect_reproduced=len(c.terminal['rewards'])!=0,optimizer_updates=0,new_physics=0)
(B/'runs/census93_native_compatibility_20261031_v1/EMPTY_RELOAD_DEFECT.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
