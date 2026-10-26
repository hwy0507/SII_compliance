"""CPU-only full-parent replay migration and synthetic boundary verification."""
from pathlib import Path
import argparse,copy,hashlib,json,os,sys,time

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(args):
    os.sched_setaffinity(0,{53})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg=json.loads(args.registration.read_text())
    for ref in reg['sources'].values():assert sha(ref['path'])==ref['sha256']
    sys.path[:0]=[str(Path(__file__).parent),reg['adapter_runtime'],str(Path(reg['runtime'])/'source/tools')]
    from train_published_compliance_20261025 import Replay
    from parameter_replay_capacity_20261026 import replay_class,MARKER
    from published_replay_device_cache_20261025 import DeviceReplayCache
    from published_exact_pipeline_20261026 import cache_class
    from validate_published_finite_check_20261025 import digest
    methods={}
    for method,ref in reg['checkpoints'].items():
        assert sha(ref['path'])==ref['sha256']
        ck=torch.load(ref['path'],map_location='cpu',weights_only=False)
        assert ck['cycle']==22 and ck['boundary']=='complete_condition_cycle'
        state=ck['replay'];original=digest(state);learner=digest(ck['learner'])
        assert state['size']==ck['steps'] and state['capacity']==1_000_000 and state['cursor']==state['size']
        cls=replay_class(Replay,original);candidate=cls(state['arrays']['actions'].shape[1],state['arrays']['observations'].shape[1],20261078)
        candidate.load_state_dict(state)
        expected=dict(state,capacity=2_000_000,replay_capacity_extension=MARKER)
        assert digest(candidate.state_dict())==digest(expected)
        candidate.load_state_dict(candidate.state_dict())
        assert digest(candidate.state_dict())==digest(expected)
        native=Replay(state['arrays']['actions'].shape[1],state['arrays']['observations'].shape[1],20261078);native.load_state_dict(state)
        cache=cache_class(DeviceReplayCache)(candidate,'cpu')
        for count in [1,32,256,65536]:
            a=native.sample(count);z=cache.sample(count)
            assert digest(a)==digest({k:v.numpy() for k,v in z.items()})
            assert digest(native.rng.bit_generator.state)==digest(candidate.rng.bit_generator.state)
        candidate.load_state_dict(state)
        guards=[]
        def reject(name,bad,loader=candidate):
            before=digest(loader.state_dict())
            try:loader.load_state_dict(bad)
            except (ValueError,TypeError):pass
            else:raise AssertionError('Accepted '+name)
            assert digest(loader.state_dict())==before;guards.append(name)
        bad=dict(expected);bad.pop('replay_capacity_extension');reject('missing_marker',bad)
        bad=dict(expected,replay_capacity_extension=dict(MARKER,capacity=3_000_000));reject('changed_marker',bad)
        bad=dict(expected,cursor=0);reject('wrapped_cursor',bad)
        bad=dict(state,rng=np.random.default_rng(42).bit_generator.state);reject('different_legacy_rng',bad)
        bad=dict(expected,capacity=1_000_000);reject('expanded_marker_old_capacity',bad)
        bad=dict(expected,size=2_000_001);reject('oversize',bad)
        assert digest(state)==original and digest(ck['learner'])==learner and sha(ref['path'])==ref['sha256']
        methods[method]=dict(checkpoint_sha256=ref['sha256'],legacy_replay_digest=original,learner_digest_unchanged=learner,size=state['size'],old_capacity=1_000_000,new_capacity=2_000_000,all_old_arrays_and_rng_exact=True,repeated_restore_exact=True,cpu_device_cache_batches_exact=[1,32,256,65536],negative_guards=guards)
        del cache,native,candidate,ck,state,expected
    # A unique synthetic pre-boundary state, never saved to a formal replay.
    native=Replay(7,49,2026102620);n=999998
    for key,a in native.arrays.items():a[:n]=1 if key=='masks' else 0
    native.arrays['rewards'][:n,0]=np.arange(n,dtype=np.float32)/1_000_000
    native.size=n;native.cursor=n;state=native.state_dict()
    candidate=replay_class(Replay,digest(state))(7,49,2026102620);candidate.load_state_dict(state)
    prefix=digest(state['arrays']);cache=cache_class(DeviceReplayCache)(candidate,'cpu')
    row=dict(observations=np.zeros(49,np.float32),next_observations=np.zeros(49,np.float32),actions=np.zeros(7,np.float32),rewards=np.array([.75],np.float32),dones=np.zeros(1,np.float32))
    for i in range(4):
        cache.add(**row)
        if i<2:
            native.add(**row)
            assert digest({k:v[:native.size] for k,v in candidate.arrays.items()})==digest(native.state_dict()['arrays'])
            assert digest(native.rng.bit_generator.state)==digest(candidate.rng.bit_generator.state)
    assert candidate.size==candidate.cursor==1_000_002
    assert digest({k:v[:n] for k,v in candidate.arrays.items()})==prefix
    assert all(torch.equal(cache.arrays[k][:candidate.size],torch.from_numpy(v[:candidate.size])) for k,v in candidate.arrays.items())
    saved=candidate.state_dict();restored=replay_class(Replay)(7,49,0);restored.load_state_dict(saved)
    assert digest(restored.state_dict())==digest(saved)
    assert digest(restored.sample(65536))==digest({k:v.numpy() for k,v in cache.sample(65536).items()})
    assert digest(restored.rng.bit_generator.state)==digest(candidate.rng.bit_generator.state)
    # Exercise the final refusal before touching array storage or RNG.
    candidate.size=candidate.cursor=candidate.capacity;before=digest(candidate.rng.bit_generator.state)
    try:cache.add(**row)
    except ValueError:pass
    else:raise AssertionError('Expanded-capacity overwrite accepted')
    assert digest(candidate.rng.bit_generator.state)==before
    report=dict(time=time.time(),passed=True,helper_sha256=sha(Path(__file__).with_name('parameter_replay_capacity_20261026.py')),methods=methods,synthetic_boundary=dict(initial_size=n,final_size=1_000_002,retained_prefix_exact=True,cache_mirror_exact=True,restored_marker_and_batch_exact=True,full_capacity_rejected_before_rng_or_write=True),optimizer_updates=0,new_physics=0,weights_saved=False,deployed=False,limitation='Real complete22 parent replay and full unchanged learner digests plus CPU device-cache batches; synthetic crossing of old1m boundary. Formal deployment must restore latest complete23 with new persistent marker and verify actual interaction. No GPU cache update or task improvement claim.')
    (args.output/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print('passed',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registration',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    try:main(args)
    except BaseException as e:
        (args.output/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
