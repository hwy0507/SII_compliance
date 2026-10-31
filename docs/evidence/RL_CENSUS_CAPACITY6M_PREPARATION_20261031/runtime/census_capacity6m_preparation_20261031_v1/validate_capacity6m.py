"""Read-only full95 replay/census compatibility and synthetic capacity boundaries."""
from pathlib import Path
import copy, gc, hashlib, json, os, sys, time, traceback
D = Path(__file__).resolve().parent
B = D.parents[1]
OUT = B/'runs/census_capacity6m_preparation_20261031_v1'
OLD = B/'runtime/census96_continuation_20261031_v1'
sys.path[:0] = [str(D), str(OLD), str(B/'runtime/source_train17_clock/source/tools')]
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def put(name, data):
    with (OUT/name).open('x') as f: json.dump(data, f, indent=2); f.write('\n')

def main():
    os.sched_setaffinity(0, {54}); os.nice(15)
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from train_published_compliance_20261025 import Replay
    from parameter_replay_capacity4m_20261027 import replay_class as old_class
    from parameter_replay_capacity6m import replay_class, KEY, MARKER
    from persisted_history_critic import KEY as HK
    from persisted_violation_critic import KEY as VK, violation_replay_class
    from census_native import CensusCache
    from validate_published_finite_check_20261025 import digest
    plan = json.loads((OUT/'PLAN.json').read_text())
    for p, h in plan['sources'].items(): assert sha(p) == h
    methods = {}
    for method, ref in plan['parents'].items():
        assert sha(ref['checkpoint']['path']) == ref['checkpoint']['sha256']
        ck = torch.load(ref['checkpoint']['path'], map_location='cpu', weights_only=False)
        p = json.loads(Path(ref['parent_registration']['path']).read_text())
        assert sha(ref['parent_registration']['path']) == ref['parent_registration']['sha256']
        assert ck['cycle'] == 95 and ck['boundary'] == 'complete_condition_cycle'
        assert ck['protocol_sha256'] == ref['parent_registration']['sha256']
        s = ck['replay']; before = digest(s); learner_before = digest(ck['learner'])
        assert s['size'] == ck['steps'] == ref['steps'] and s['cursor'] == s['size']
        stripped = {k:v for k,v in s.items() if k not in (HK,VK)}
        binding = p['violation_critic_amendment']['binding']; dimension = binding['action_dimension']
        candidate = violation_replay_class(replay_class(Replay, digest(stripped)),binding)(dimension,52,0,capacity=6_000_000)
        candidate.load_state_dict(s)
        expected = dict(s,capacity=6_000_000,**{KEY:MARKER})
        assert digest(candidate.state_dict()) == digest(expected)
        candidate.load_state_dict(candidate.state_dict())
        assert digest(candidate.state_dict()) == digest(expected)
        native = violation_replay_class(old_class(Replay),binding)(dimension,52,0)
        native.load_state_dict(s)
        cache = CensusCache(candidate,'cpu')
        terminal = np.flatnonzero(s['arrays']['dones'][:,0] == 1)
        codes = (s['arrays']['masks'][terminal].astype(np.int64)*np.array([1,2,4,8,16])).sum(1)
        assert np.array_equal(cache.terminal_indices,terminal)
        assert np.array_equal(cache.population.numpy(),np.bincount(codes,minlength=32))
        for count in [1,32,256,65536]:
            a = native.sample(count); b = cache.sample(count)
            assert digest(a) == digest({k:v.numpy() for k,v in b.items()})
            assert digest(native.rng.bit_generator.state) == digest(candidate.rng.bit_generator.state)
        cache.load_state_dict(expected)
        assert digest(candidate.state_dict()) == digest(expected)
        assert np.array_equal(cache.terminal_indices,terminal)
        assert np.array_equal(cache.population.numpy(),np.bincount(codes,minlength=32))
        assert digest(s) == before and digest(ck['learner']) == learner_before
        assert sha(ref['checkpoint']['path']) == ref['checkpoint']['sha256']
        methods[method] = dict(rows=s['size'],terminals=len(terminal),parent_replay_digest=before,
                              learner_digest=learner_before,old_arrays_rng_markers_exact=True,
                              restored_census_population_exact=True,cpu_batches_exact=[1,32,256,65536],
                              checkpoint_sha256=ref['checkpoint']['sha256'])
        put(method+'_REVIEW.json',dict(passed=True,**methods[method]))
        print(method,'passed',flush=True)
        del cache,candidate,native,ck,s,stripped,expected,a,b; gc.collect()

    # Independent small fixtures exercise rejection before any replay/RNG change.
    old = old_class(Replay)(7,52,20261031)
    row = dict(observations=np.zeros(52,np.float32),next_observations=np.zeros(52,np.float32),
               actions=np.zeros(7,np.float32),rewards=np.ones(1,np.float32),dones=np.zeros(1,np.float32))
    for _ in range(3): old.add(**row)
    s = copy.deepcopy(old.state_dict()); candidate = replay_class(Replay,digest(s))(7,52,1)
    candidate.load_state_dict(s); expected = copy.deepcopy(candidate.state_dict()); rejected=[]
    def reject(name,bad):
        before=digest(candidate.state_dict())
        try: candidate.load_state_dict(bad)
        except (ValueError,TypeError,KeyError): pass
        else: raise AssertionError('Accepted malformed '+name)
        assert digest(candidate.state_dict()) == before; rejected.append(name)
    for key in ['replay_capacity_extension','replay_capacity_followup',KEY]:
        bad=copy.deepcopy(expected);bad.pop(key);reject('missing_'+key,bad)
        bad=copy.deepcopy(expected);bad[key]['capacity']=-1;reject('changed_'+key,bad)
    for key,value in [('capacity',4_000_000),('cursor',0),('size',-1),('size',3.0),('size',6_000_001),('extra',True),('rng',{})]:
        reject(str((key,value)),dict(expected,**{key:value}))
    reject('unbound_parent_rng',dict(s,rng=np.random.default_rng(42).bit_generator.state))
    for name in ['dtype','nan','mask','done','shape','missing_array','extra_array']:
        bad=copy.deepcopy(expected);arrays=bad['arrays']
        if name=='dtype':arrays['rewards']=arrays['rewards'].astype(np.float64)
        elif name=='nan':arrays['rewards'][0,0]=np.nan
        elif name=='mask':arrays['masks'][0,0]=.5
        elif name=='done':arrays['dones'][0,0]=.5
        elif name=='shape':arrays['actions']=arrays['actions'][:,:-1]
        elif name=='missing_array':arrays.pop('actions')
        else:arrays['extra']=arrays['actions']
        reject(name,bad)
    del candidate,old,s,expected;gc.collect()

    # Cross the actual 4m boundary with distinguishable synthetic retained rows.
    native=old_class(Replay)(7,52,20261031); n=3_999_998
    for key,arr in native.arrays.items():arr[:n]=1 if key=='masks' else 0
    native.arrays['rewards'][:n,0]=np.arange(n,dtype=np.float32)/4_000_000
    native.arrays['dones'][::1000,0]=1
    native.size=native.cursor=n;s=native.state_dict();prefix=digest(s['arrays'])
    candidate=replay_class(Replay,digest(s))(7,52,0);candidate.load_state_dict(s)
    cache=CensusCache(candidate,'cpu');start_terminals=len(cache.terminal_indices)
    row['dones']=np.ones(1,np.float32)
    for i in range(4):
        cache.add(**row)
        if i<2:
            native.add(**row)
            for key in native.arrays:assert np.array_equal(candidate.arrays[key][n+i],native.arrays[key][n+i])
            assert digest(native.rng.bit_generator.state)==digest(candidate.rng.bit_generator.state)
    assert candidate.size==candidate.cursor==4_000_002
    assert digest({k:v[:n] for k,v in candidate.arrays.items()})==prefix
    assert len(cache.terminal_indices)==start_terminals+4
    for key,arr in candidate.arrays.items():assert torch.equal(cache.arrays[key][:candidate.size],torch.from_numpy(arr[:candidate.size]))
    restored=replay_class(Replay)(7,52,1);restored.load_state_dict(candidate.state_dict())
    assert digest(restored.state_dict())==digest(candidate.state_dict())
    assert digest(restored.sample(65536))==digest({k:v.numpy() for k,v in cache.sample(65536).items()})
    assert digest(restored.rng.bit_generator.state)==digest(candidate.rng.bit_generator.state)
    del cache,native,restored,s;gc.collect()
    # Populate remaining rows before digesting full capacity (no uninitialized data).
    for key,arr in candidate.arrays.items():arr[candidate.size:]=1 if key=='masks' else 0
    candidate.size=candidate.cursor=5_999_999
    prefix=digest({k:v[:candidate.size] for k,v in candidate.arrays.items()})
    candidate.add(**row)
    assert candidate.size==candidate.cursor==6_000_000
    assert digest({k:v[:5_999_999] for k,v in candidate.arrays.items()})==prefix
    before=digest(candidate.state_dict())
    try:candidate.add(**row)
    except ValueError:pass
    else:raise AssertionError('Capacity overwrite accepted')
    assert digest(candidate.state_dict())==before
    for p,h in plan['sources'].items():assert sha(p)==h
    put('REVIEW.json',dict(passed=True,time=time.time(),methods=methods,negative_guards=rejected,
        synthetic_boundary=dict(start=3_999_998,end=4_000_002,old_prefix_exact=True,census_growth=4,
          all_cache_fields_exact=True,restored_sample65536_and_rng_exact=True,last_slot_written=True,
          full6m_rejected_before_mutation=True),physics_steps=0,optimizer_updates=0,
        formal_deployment=False,full96_parent_tested=False,gpu_cache_tested=False,
        limitation='Full95 CPU preparation only; full96 restore, GPU update, finite97 protocol and complete96 scientific review remain required.'))
    print('all passed',flush=True)

if __name__=='__main__':
    try:main()
    except BaseException:
        put('FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
