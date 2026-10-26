"""Audit derived replay, streamed maturity and full state before finite online use."""
from pathlib import Path
import os, sys, json, copy, time, hashlib
os.sched_setaffinity(0,{0})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
P=Path(__file__).parent
OUT=B/'runs/serl_multistep_preparation_20261026_v2'
OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
sys.path.insert(0,str(B/'runtime/serl_state_adapter_20261026_v1'))
from train_serl_state_20261026 import Replay
from serl_clock_state_adapter_20261026 import SerlClockLearner
from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class, MARKER
from probe_serl_multistep_20261026 import derive, sha, write
from validate_serl_state_20261026 import digest

try:
    probe=B/'runs/serl_cycle09_multistep_probe_20261026_v3'
    reg=json.loads((probe/'REGISTRATION.json').read_text())
    scientific=json.loads((probe/'REVIEW.json').read_text());assert scientific['passed']
    gate=json.loads((probe/'result/REPLAY_GATE.json').read_text());assert gate['passed']
    parent=Path(reg['checkpoint']['path']);assert sha(parent)==reg['checkpoint']['sha256']
    ck=torch.load(parent,map_location='cpu',weights_only=False)
    arrays=ck['replay']['arrays'];groups={}
    for journal in gate['journals']:
        assert sha(journal['path'])==journal['sha256']
        with Path(journal['path']).open() as f:
            for line in f:
                row=json.loads(line);groups.setdefault((row['cycle'],row['condition']),[]).append(row['step']-1)
    derived=derive(arrays,groups,32,.9995)
    assert digest(derived)==gate['derived_sha256']['32']
    R=replay_class(Replay)
    replay=R(7,49,20261026+53)
    replay.import_one_step_state(copy.deepcopy(ck['replay']),derived)
    migrated=replay.state_dict();extra=migrated.pop('multistep_target_extension')
    assert digest(migrated)==digest(ck['replay'])
    assert not extra['pending'] and len(extra['ready'])==400935
    # Interleaved short and full-window streams; all old and new raw fields survive.
    empty=Replay(7,49,27,capacity=200)
    test=R(7,49,27,capacity=200)
    test.import_one_step_state(empty.state_dict(),dict(rewards=np.empty(0),bootstrap=np.empty(0),endpoints=np.empty(0),lengths=np.empty(0)))
    seq={};lengths=[4,35,66]
    for step in range(max(lengths)):
        for stream,length in enumerate(lengths):
            if step>=length:continue
            i=test.size;seq.setdefault(stream,[]).append(i)
            obs=np.full(49,step+stream/10,np.float32);obs[48]=(1375-step)/1375
            nxt=np.full(49,step+1+stream/10,np.float32);nxt[48]=(1374-step)/1375
            row=dict(observations=obs,next_observations=nxt,actions=np.zeros(7,np.float32),rewards=[np.float32((-1)**step*(step+.1))],dones=[float(step==length-1)])
            test.add(stream=stream,**row);empty.add(**row)
            snapshot=test.state_dict();restored=R(7,49,27,capacity=200);restored.load_state_dict(copy.deepcopy(snapshot))
            assert digest(restored.state_dict())==digest(snapshot)
            if test.ready:
                assert digest(test.sample(16))==digest(restored.sample(16))
            restored.rng.bit_generator.state=copy.deepcopy(snapshot['rng'])
            test=restored
    expected=derive(empty.state_dict()['arrays'],seq,32,.9995)
    for attr,key in [('target_rewards','rewards'),('target_bootstrap','bootstrap'),('target_endpoints','endpoints'),('target_lengths','lengths')]:
        np.testing.assert_array_equal(getattr(test,attr)[:test.size],expected[key])
    raw=test.state_dict();raw.pop('multistep_target_extension');raw['rng']=empty.state_dict()['rng']
    assert digest(raw)==digest(empty.state_dict()) and not test.pending
    bad=replay.state_dict();bad['multistep_target_extension']['marker']['horizon']=31
    try:R(7,49,27).load_state_dict(bad)
    except ValueError:pass
    else:raise AssertionError('Changed horizon accepted')
    kwargs=dict(upstream=Path(reg['upstream']),upstream_manifest=Path(reg['upstream_manifest']),dimension=7,direct=True,seed=20261026,device='cuda:0')
    learner=SerlMultistepLearner(Path(reg['runtime']),**kwargs)
    learner.import_one_step_state(copy.deepcopy(ck['learner']))
    migrated_state=copy.deepcopy(learner.state_dict());stripped=copy.deepcopy(migrated_state);assert stripped.pop('multistep_target_extension')==MARKER
    assert digest(stripped)==digest(ck['learner'])
    for bad in [ck['learner'],dict(migrated_state,multistep_target_extension={})]:
        try:learner.load_state_dict(bad)
        except ValueError:pass
        else:raise AssertionError('Missing/changed multistep marker accepted')
    learner.load_state_dict(copy.deepcopy(migrated_state))
    assert digest(learner.state_dict())==digest(migrated_state)
    initial_replay=copy.deepcopy(replay.state_dict());batch=replay.sample(32768)
    # Compare actual target batch to the finite-probe construction.
    rng=np.random.default_rng();rng.bit_generator.state=copy.deepcopy(initial_replay['rng']);ids=rng.integers(400935,size=32768)
    np.testing.assert_array_equal(batch['rewards'][:,0],derived['rewards'][ids])
    np.testing.assert_array_equal(batch['_bootstrap'],derived['bootstrap'][ids])
    np.testing.assert_array_equal(batch['observations'],arrays['observations'][ids])
    np.testing.assert_array_equal(batch['next_observations'],arrays['next_observations'][derived['endpoints'][ids]])
    first=learner.update(batch);after=digest(learner.state_dict())
    learner.load_state_dict(copy.deepcopy(migrated_state));second=learner.update(batch)
    assert digest(learner.state_dict())==after and first==second
    learner.load_state_dict(copy.deepcopy(migrated_state));replay.load_state_dict(copy.deepcopy(initial_replay))
    assert digest(learner.state_dict())==digest(migrated_state)
    prepared=dict(ck,learner=learner.state_dict(),replay=replay.state_dict())
    assert prepared['cycles']==ck['cycles'] and prepared['steps']==ck['steps']
    torch.save(prepared,OUT/'prepared_cycle09.pt')
    assert sha(parent)==reg['checkpoint']['sha256']
    write(OUT/'REVIEW.json',dict(passed=True,time=time.time(),checkpoint_sha256=sha(parent),prepared_checkpoint_sha256=sha(OUT/'prepared_cycle09.pt'),
        original_full_learner_recovered_exactly=True,old_replay_recovered_exactly=True,history_retained=True,
        repeated_restore_next_update_exact=True,online_interleaved_rows_checked=sum(lengths),all_historical_rows_checked=400935,
        marker_negative_guards=True,derived_batch_matches_probe=True,auxiliary_critic_updates=16,auxiliary_actor_updates=2,
        auxiliary_weights_promoted=False,new_physics=0,source_hashes={f.name:sha(f) for f in [Path(__file__),P/'serl_multistep_state_adapter_20261026.py']},
        probe_review=dict(path=str(probe/'REVIEW.json'),sha256=sha(probe/'REVIEW.json'))))
except BaseException as error:
    write(OUT/'FAILURE.json',dict(error=repr(error)))
    raise
