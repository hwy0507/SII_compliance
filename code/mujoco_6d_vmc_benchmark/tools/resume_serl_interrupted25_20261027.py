"""Exact partial25 learner/replay restoration, with disjoint new episode streams.

All old replay rows, targets, ready order and pending queues remain byte-exact.
Unfinished tails cannot mature without their lost environment: they remain
explicitly quarantined, unsampled as before, never terminated or discarded.
One newly registered complete26 cycle is additional exposure, not completion25.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,inspect,json,os,sys,time

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def stream_id(slot):
    if type(slot) is not int or not 0 <= slot < 30:raise ValueError('Invalid new episode slot')
    return slot+30

def transform(source):
    if source.count('stream=slot') != 5:raise ValueError('Native stream call seams drifted')
    source=source.replace('stream=slot', 'stream=_recovery_stream(slot)')
    seam="            environment_state_saved=False,"
    if source.count(seam)!=1:raise ValueError('Checkpoint metadata seam drifted')
    source=source.replace(seam,"            interruption_recovery=protocol['interrupted_stream_recovery'],\n"+seam)
    source=source.replace("            resume_semantics='retain completed transitions and learner state; start new episodes after partial boundary'", "            resume_semantics='partial25 retained; streams0-29 quarantined unchanged; fresh physical streams30-59 in separately budgeted complete26'")
    seam="        steps, cycles, start_cycle = checkpoint['steps'], checkpoint['cycles'], checkpoint['cycle']+1"
    if source.count(seam)!=1:raise ValueError('Restore audit seam drifted')
    source=source.replace(seam,seam+"\n        _verify_initial_state(learner, replay, checkpoint, out.parent)")
    # Record the exact raw replay stream alongside the existing physical transition journal.
    source=source.replace("dict(step=steps, cycle=cycle, condition=state['condition']['id'],", "dict(step=steps, cycle=cycle, recovery_stream=_recovery_stream(slot), condition=state['condition']['id'],")
    return source

def validate_protocol(checkpoint_digest, protocol, current_digest):
    stage=protocol['interrupted_stream_recovery']
    ref=stage['parent_registration']
    if sha(ref['path'])!=ref['sha256'] or checkpoint_digest!=ref['sha256']:
        raise ValueError('Exact interrupted25 registration required')
    previous=json.loads(Path(ref['path']).read_text())
    if {k:v for k,v in protocol.items() if k!='interrupted_stream_recovery'} != previous:
        raise ValueError('Original training contract changed')
    if (stage['parent_cycle']!=25 or stage['new_cycle']!=26 or stage['new_cycles']!=1
        or stage['new_streams']!=list(range(30,60)) or stage['quarantined_streams']!=list(range(30))
        or stage['pending_count']!=930 or stage['parent_steps']!=1039290
        or stage['maximum_new_actions']!=41250 or stage['new_optimizer_settings']
        or stage['old_window_continuity_claim'] or stage['automatic_followup']):
        raise ValueError('Unregistered interrupted-stream recovery semantics')
    return previous

def verify_initial_state(learner,replay,checkpoint,output):
    from validate_serl_state_20261026 import digest
    ld,rd=digest(learner.state_dict()),digest(replay.state_dict())
    if ld!=digest(checkpoint['learner']) or rd!=digest(checkpoint['replay']):
        raise ValueError('Restored full learner/replay differs from parent')
    write(output/'INITIAL_STATE_REVIEW.json',dict(passed=True,time=time.time(),learner_digest=ld,replay_digest=rd,
        steps=checkpoint['steps'],history_digest=digest(checkpoint['cycles']),
        old_pending_count=930,optimizer_updates=0,new_physics=0))

def validate_parent(ck,stage):
    extra=ck['replay']['multistep_target_extension']
    if (ck['steps']!=1039290 or ck['cycle']!=25 or ck['controller']!='direct' or ck['seed']!=20261026
        or ck['boundary']!='partial_episode_valid_replay_reset_environment_on_resume'
        or ck['environment_state_saved'] or ck['cycles'][-1]['cycle']!=24
        or any(c['cycle']==25 for c in ck['cycles']) or ck['learner']['outer_updates']!=1034291
        or ck['learner']['num_gradient_steps']!=8274328
        or set(extra['pending'])!=set(range(30)) or any(len(v)!=31 for v in extra['pending'].values())
        or len(extra['ready'])!=1038360):raise ValueError('Unexpected interrupted checkpoint boundary')

def quarantine_replay(base, old_pending):
    """Runtime guard only; serialized replay schema stays unchanged and strict."""
    class Guarded(base):
        def add(self, *, stream, **transition):
            if stream not in range(30,60):raise ValueError('Cannot append to a quarantined/unknown stream')
            super().add(stream=stream,**transition)
        def state_dict(self):
            state=super().state_dict()
            p=state['multistep_target_extension']['pending']
            if any(p.get(k)!=v for k,v in old_pending.items()):
                raise ValueError('Historical interrupted pending queue changed')
            return state
    return Guarded

def main(args):
    import torch,numpy as np
    torch.set_num_threads(1)
    os.sched_setaffinity(0,set(range(13)))
    protocol=json.loads(args.registration.read_text());stage=protocol['interrupted_stream_recovery']
    if sha(__file__)!=stage['driver_sha256'] or sha(args.resume)!=stage['checkpoint']['sha256'] or str(args.resume)!=stage['checkpoint']['path']:
        raise ValueError('Exact recovery source/checkpoint required')
    rt=Path(stage['runtime'])
    for n,h in stage['source_hashes'].items():
        if sha(rt/n)!=h:raise ValueError('Recovery dependency drift: '+n)
    root=args.runtime.resolve();adapter=Path(protocol['source_adapter'])
    sys.path[:0]=[str(rt),str(adapter),str(root/'source/tools')]
    import resume_serl_capacity_reviewed_continuation_20261027 as old
    ck=torch.load(args.resume,map_location='cpu',weights_only=False)
    previous=validate_protocol(ck['protocol_sha256'],protocol,sha(args.registration));validate_parent(ck,stage)
    # Validate the actual historic complete24->25 contract as itself; never relabel partial25 as complete.
    old.validate(previous['resume_parent_registration']['sha256'],previous,sha(stage['parent_registration']['path']))
    for n,h in previous['gather_stage']['source_hashes'].items():
        if sha(rt/n)!=h:raise ValueError('Original gather dependency drift')
    for n,h in previous['source_adapter_hashes'].items():
        if sha(adapter/n)!=h:raise ValueError('Original adapter drift')
    for n,h in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/n)!=h:raise ValueError('Frozen physical source drift')
    old.validate_sampler_pool(protocol,args,list(range(13)))
    spec=importlib.util.spec_from_file_location('frozen_serl_interrupted_base',adapter/'train_serl_state_20261026.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    old_source=old.transform_main(inspect.getsource(module.main))
    if hashlib.sha256(old_source.encode()).hexdigest()!=previous['reviewed_continuation_stage']['patched_main_sha256']:
        raise ValueError('Previously registered trainer changed')
    candidate=transform(old_source)
    if hashlib.sha256(candidate.encode()).hexdigest()!=stage['patched_main_sha256']:raise ValueError('Recovery main drift')
    expanded=old.capacity_replay(module.Replay,previous,ck)
    guarded=quarantine_replay(expanded,ck['replay']['multistep_target_extension']['pending'])
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from validate_serl_state_20261026 import digest
    if args.check_only:
        os.sched_setaffinity(0,{0})
        learner=transfer_class(SerlMultistepLearner)(root,upstream=args.serl_upstream,
            upstream_manifest=args.serl_manifest,dimension=7,direct=True,seed=20261026,device=args.device)
        learner.load_state_dict(ck['learner'])
        checks=old.check_replay_restore(module.Replay,guarded,ck,learner)
        replay=guarded(7,49,1);replay.load_state_dict(ck['replay'])
        assert digest(replay.state_dict())==digest(ck['replay'])
        # Synthetic stream-isolation test in a disposable replay copy, zero learner updates/physics.
        raw={k:v[-1].copy() for k,v in ck['replay']['arrays'].items() if k!='masks'}
        raw['rewards']=np.array([1.],np.float32);raw['dones']=np.array([0.],np.float32)
        for s in range(30):
            try:replay.add(stream=s,**raw)
            except ValueError:pass
            else:raise AssertionError('Quarantined append accepted')
        assert digest(replay.state_dict())==digest(ck['replay'])
        for step in range(32):
            for slot in range(30):replay.add(stream=stream_id(slot),**raw)
        extra=replay.state_dict()['multistep_target_extension'];start=ck['steps']
        assert extra['ready'][:len(ck['replay']['multistep_target_extension']['ready'])]==ck['replay']['multistep_target_extension']['ready']
        assert set(extra['ready'][1038360:])==set(range(start,start+30))
        for slot in range(30):
            assert extra['target_endpoints'][start+slot]==start+930+slot
            assert extra['target_lengths'][start+slot]==32
        raw['dones']=np.array([1.],np.float32)
        for slot in range(30):replay.add(stream=stream_id(slot),**raw)
        state=replay.state_dict();extra=state['multistep_target_extension']
        assert extra['pending']==ck['replay']['multistep_target_extension']['pending']
        assert len(extra['ready'])==1038360+990
        for name,value in ck['replay']['arrays'].items():assert np.array_equal(state['arrays'][name][:start],value)
        for name in ['target_rewards','target_bootstrap','target_endpoints','target_lengths']:
            assert np.array_equal(extra[name][:start],ck['replay']['multistep_target_extension'][name])
        reloaded=guarded(7,49,2);reloaded.load_state_dict(state)
        assert digest(reloaded.state_dict())==digest(state)
        assert digest(reloaded.sample(65536))==digest(replay.sample(65536))
        assert digest(learner.state_dict())==digest(ck['learner'])
        # Only episode clocks reset for disjoint new environments; network, Adam and RNG stay exact.
        before=digest(learner.state_dict())
        for slot in range(30):learner.reset_episode(stream=stream_id(slot))
        assert digest(learner.state_dict())==before
        rejects=0
        for key,value in [('new_cycles',2),('new_streams',list(range(30))),('pending_count',0),('old_window_continuity_claim',True)]:
            bad=copy.deepcopy(protocol);bad['interrupted_stream_recovery'][key]=value
            try:validate_protocol(ck['protocol_sha256'],bad,'')
            except ValueError:rejects+=1
            else:raise AssertionError('Invalid recovery contract accepted')
        result=dict(passed=True,time=time.time(),checkpoint_sha256=sha(args.resume),full_learner_digest=before,
            full_replay_digest=digest(ck['replay']),history_digest=digest(ck['cycles']),**checks,
            old_pending_preserved=930,new_streams_disjoint=True,synthetic_transitions_discarded=990,
            raw_and_derived_old_prefix_exact=True,quarantined_append_rejections=30,negative_protocol_guards=rejects,
            new_physics=0,optimizer_updates=0,weights_saved=False,cycle25_complete=False)
        write(args.output.parent/'CHECK_ONLY_REVIEW.json',result);print(json.dumps(result),flush=True);return
    review=json.loads((args.output.parent/'CHECK_ONLY_REVIEW.json').read_text())
    if not review['passed'] or review['checkpoint_sha256']!=sha(args.resume):raise ValueError('Actual partial restore review required')
    gate=json.loads((args.output.parent/'PRELAUNCH_REVIEW.json').read_text())
    if not gate['passed'] or gate['registration_sha256']!=sha(args.registration):raise ValueError('Independent prelaunch review required')
    args.controller,args.algorithm,args.seed='direct','serl_state',20261026
    args.cycles=1
    module.PublishedLearner=transfer_class(SerlMultistepLearner);module.Replay=guarded
    module.validate_resume_protocol=validate_protocol
    ns=module.__dict__;ns.update(_validate_sampler_pool=old.validate_sampler_pool,_sampler_affinity=old.sampler_affinity,
        _recovery_stream=stream_id,_verify_initial_state=verify_initial_state)
    exec(compile(candidate,'<registered_interrupted25_stream_recovery>','exec'),ns)
    write(args.output.parent/'RECOVERY_EXECUTION.json',dict(time=time.time(),pid=os.getpid(),checkpoint=stage['checkpoint'],
        registration_sha256=sha(args.registration),driver_sha256=sha(__file__),new_cycle=26,maximum_new_actions=41250,
        old_pending_quarantined=930,complete25_claim=False,automatic_followup=False))
    (args.output.parent/'SAMPLER_MAIN.py.txt').write_text(candidate)
    del ck
    module.main(args)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['runtime','registration','resume','output','serl-upstream','serl-manifest','sampler-python']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--device',default='cuda:0');p.add_argument('--cpus',required=True);p.add_argument('--workers',type=int,default=30);p.add_argument('--check-only',action='store_true')
    a=p.parse_args()
    try:main(a)
    except BaseException as e:
        write(a.output.parent/('CHECK_ONLY_FAILURE.json' if a.check_only else 'DRIVER_FAILURE.json'),dict(time=time.time(),error=repr(e)));raise
