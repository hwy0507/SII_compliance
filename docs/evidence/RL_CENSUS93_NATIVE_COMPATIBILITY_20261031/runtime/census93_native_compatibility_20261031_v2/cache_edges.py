from pathlib import Path
import sys,json,time,copy
import numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).resolve().parent;O=B/'runs/census93_native_compatibility_20261031_v2'
sys.path[:0]=[str(D),str(B/'runtime/violation93_continuation_20261031_v1'),str(B/'runtime/source_train17_clock/source/tools')]
from census_native import CensusCache
from train_published_compliance_20261025 import Replay
r=Replay(1,52,123,capacity=64);a=np.zeros(52,np.float32)
row=dict(observations=a,next_observations=a,actions=np.zeros(1,np.float32),rewards=np.zeros(1,np.float32),dones=np.ones(1,np.float32))
c=CensusCache(r,'cuda:0');assert len(c.terminal_indices)==len(c.terminal['rewards'])==0
empty=copy.deepcopy(r.state_dict());c.add(**row);assert len(c.terminal_indices)==1
c.load_state_dict(empty);assert len(c.terminal_indices)==len(c.terminal['rewards'])==0 and int(c.population.sum())==0
nonterminal=dict(row,dones=np.zeros(1,np.float32));c.add(**nonterminal);plain=copy.deepcopy(r.state_dict());c.add(**row);assert len(c.terminal_indices)==1
c.load_state_dict(plain);assert len(c.terminal_indices)==len(c.terminal['rewards'])==0
start=c.scanned_rows_total
for i in range(16):c.add(**(row if i%3==0 else nonterminal))
assert c.scanned_rows_total-start==16 and len(c.terminal_indices)==6
idx=np.flatnonzero(r.arrays['dones'][:r.size,0]==1);np.testing.assert_array_equal(idx,c.terminal_indices)
for k,v in c.terminal.items():np.testing.assert_array_equal(v.cpu().numpy(),r.arrays[k][idx])
scanned=c.scanned_rows_total;c.refresh();assert scanned==c.scanned_rows_total
rejects=[]
for key in ['dones','masks']:
 bad=copy.deepcopy(r.state_dict());bad['arrays'][key][0,0]=.5
 try:c.load_state_dict(bad)
 except ValueError:rejects.append(key)
 else:raise AssertionError(key)
assert rejects==['dones','masks']
result=dict(passed=True,time=time.time(),fresh_empty=True,nonempty_to_empty=True,nonempty_to_nonterminal=True,incremental_scan16_only=True,full_compact_arrays_exact=True,no_append_refresh_no_rescan=True,invalid_restores_rejected=rejects,optimizer_updates=0,new_physics=0)
(O/'CACHE_EDGE_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
