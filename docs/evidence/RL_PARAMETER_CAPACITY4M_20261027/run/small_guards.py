from pathlib import Path
import os,sys,json,copy,hashlib,time
os.sched_setaffinity(0,{54});os.nice(15)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter_capacity4m_preparation_20261027_v1';rt=B/'runtime'/O.name
sys.path[:0]=[str(rt),str(B/'runtime/parameter_capacity_pool30_cycle45_20261026_v1'),str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
from train_published_compliance_20261025 import Replay
from parameter_replay_capacity4m_20261027 import replay_class,MARKER,ORIGINAL_MARKER
from validate_published_finite_check_20261025 import digest
before_source=hashlib.sha256((rt/'parameter_replay_capacity4m_20261027.py').read_bytes()).hexdigest()
rows={k:np.ones((8,w),np.float32) for k,w in dict(observations=3,next_observations=3,actions=2,rewards=1,dones=1,masks=5).items()}
s=dict(capacity=2_000_000,size=8,cursor=8,arrays=rows,rng=np.random.default_rng(2026102748).bit_generator.state,replay_capacity_extension=copy.deepcopy(ORIGINAL_MARKER))
c=replay_class(Replay,digest(s))(2,3,0);c.load_state_dict(s);valid=copy.deepcopy(c.state_dict());reference=digest(valid);guards=[]
def reject(name,change):
 bad=copy.deepcopy(valid);change(bad)
 try:c.load_state_dict(bad)
 except (ValueError,TypeError):pass
 else:raise AssertionError(name)
 assert digest(c.state_dict())==reference;guards.append(name)
reject('wrong_dtype',lambda x:x['arrays'].__setitem__('actions',x['arrays']['actions'].astype(np.float64)))
reject('nonfinite_row',lambda x:x['arrays']['rewards'].__setitem__((0,0),np.nan))
reject('nonbinary_masks',lambda x:x['arrays']['masks'].__setitem__((0,0),.5))
reject('wrong_shape',lambda x:x['arrays'].__setitem__('observations',np.ones((8,4),np.float32)))
reject('missing_array',lambda x:x['arrays'].pop('dones'))
reject('extra_array',lambda x:x['arrays'].__setitem__('invented',np.zeros((8,1),np.float32)))
reject('invalid_rng',lambda x:x.__setitem__('rng',{}))
reject('negative_size',lambda x:x.__setitem__('size',-1))
reject('float_size',lambda x:x.__setitem__('size',8.0))
reject('historical_marker_missing',lambda x:x.pop('replay_capacity_extension'))
reject('unexpected_state_key',lambda x:x.__setitem__('invented',1))
# Exercise the final valid insertion, then require rejection before overwriting it.
c.size=c.cursor=c.capacity-1
row=dict(observations=np.full(3,2,np.float32),next_observations=np.full(3,3,np.float32),actions=np.full(2,.25,np.float32),rewards=np.ones(1,np.float32),dones=np.ones(1,np.float32))
c.add(**row);assert c.size==c.cursor==4_000_000
for k,v in row.items():np.testing.assert_array_equal(c.arrays[k][-1],v)
last={k:a[-1].copy() for k,a in c.arrays.items()};rng=copy.deepcopy(c.rng.bit_generator.state)
try:c.add(**row)
except ValueError:pass
else:raise AssertionError('full capacity accepted')
assert digest(c.rng.bit_generator.state)==digest(rng)
for k,v in last.items():np.testing.assert_array_equal(v,c.arrays[k][-1])
for k,v in s['arrays'].items():np.testing.assert_array_equal(v,c.arrays[k][:8])
assert c.size==c.cursor==4_000_000
assert hashlib.sha256((rt/'parameter_replay_capacity4m_20261027.py').read_bytes()).hexdigest()==before_source
(O/'SMALL_GUARDS_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),helper_sha256=before_source,guards_rejected_before_state_mutation=guards,last_valid_insertion_at=3999999,full_refusal_preserved_first_rows_last_row_rng_size_cursor=True,synthetic_only=True,optimizer_updates=0,new_physics=0,formal_deployment=False),indent=2)+'\n');print('passed',len(guards),'malformed state guards and final-slot insertion/overflow')
