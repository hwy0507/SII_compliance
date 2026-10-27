"""One reviewed finite continuation after complete take27.

Retain the exact recovery26/take27 lineage, original930 quarantined tails,
all learner/replay/RNG/history and verified take gather. Never resume partial.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def read_ref(ref):
    if sha(ref['path']) != ref['sha256']:
        raise ValueError('Evidence hash drift: '+ref['path'])
    return json.loads(Path(ref['path']).read_text())


def validate_stage_contract(protocol, previous):
    stage = protocol['recovery_continuation_stage']
    earlier = previous['recovery_continuation_stage']
    protected = lambda p: {k:v for k,v in p.items() if k != 'recovery_continuation_stage'}
    if protected(protocol) != protected(previous):
        raise ValueError('Protected original recovery contract changed')
    if (type(stage['parent_cycle']) is not int or stage['parent_cycle'] < 27
            or stage['parent_cycle'] != earlier['new_cycle']
            or stage['new_cycle'] != stage['parent_cycle']+1
            or stage['new_cycles'] != 1 or stage['maximum_new_actions'] != 41250
            or stage['maximum_physical_substeps'] != 33000000
            or stage['automatic_followup'] or stage['auxiliary_weights_imported']
            or stage['optimizer_settings_changed'] or stage['quarantined_pending'] != 930
            or stage['active_streams'] != list(range(30,60))):
        raise ValueError('One consecutive unchanged complete cycle required')
    for key in ['gather_gate','gather_saved_review','gather_sha256','sample_source_sha256']:
        if stage[key] != earlier[key]:
            raise ValueError('Historical equivalent-gather evidence changed: '+key)


def validate_stage_evidence(stage):
    review,health = read_ref(stage['cycle_review']),read_ref(stage['health_review'])
    gate,saved = read_ref(stage['gather_gate']),read_ref(stage['gather_saved_review'])
    if (not review['passed'] or not health['network_optimizer_rng_unchanged']
            or review['methods']['direct']['checkpoint_sha256'] != stage['checkpoint']['sha256']
            or health['checkpoint_sha256'] != stage['checkpoint']['sha256']
            or not gate['passed'] or not gate['full_next_update_state_metrics_rng_exact']
            or gate['candidate_sha256'] != stage['gather_sha256']
            or gate['weights_saved'] or gate['new_physics'] != 0
            or not saved['passed'] or saved['review_sha256'] != stage['gather_gate']['sha256']):
        raise ValueError('Missing exact-parent review or original gather evidence')


def validate_protocol(checkpoint_digest, protocol, current_digest):
    import resume_serl_recovery26_take27_20261027 as entry
    stage = protocol['recovery_continuation_stage']
    if checkpoint_digest != stage['parent_registration']['sha256']:
        raise ValueError('Exact latest complete parent registration required')
    current,seen,first = protocol,set(),None
    while current['recovery_continuation_stage']['parent_cycle'] >= 27:
        stage = current['recovery_continuation_stage']
        ref = stage['parent_registration']
        if ref['path'] in seen:
            raise ValueError('Cyclic continuation lineage')
        seen.add(ref['path'])
        previous = read_ref(ref)
        if first is None:
            first = previous
        validate_stage_contract(current,previous)
        validate_stage_evidence(stage)
        current = previous
    if first is None or current['recovery_continuation_stage']['parent_cycle'] != 26:
        raise ValueError('Continuation must descend from the original take27 entry')
    entry.validate_protocol(current['recovery_continuation_stage']['parent_registration']['sha256'],current,'')
    return first


def original_recovery_protocol(protocol):
    current,seen = protocol,set()
    while 'recovery_continuation_stage' in current:
        ref = current['recovery_continuation_stage']['parent_registration']
        if ref['path'] in seen:
            raise ValueError('Cyclic original-recovery lineage')
        seen.add(ref['path']);current = read_ref(ref)
    return current


def validate_parent(ck, previous):
    extra = ck['replay']['multistep_target_extension']
    stage = previous['recovery_continuation_stage']
    cycle = stage['new_cycle']
    complete_after_recovery = [c['cycle'] for c in ck['cycles'] if c['cycle'] >= 25]
    if (type(cycle) is not int or cycle < 27 or ck['cycle'] != cycle
            or ck['boundary'] != 'complete_condition_cycle'
            or ck['controller'] != 'direct' or ck['seed'] != 20261026
            or ck['cycles'][-1]['cycle'] != cycle
            or complete_after_recovery != list(range(26,cycle+1))
            or ck['interruption_recovery'] != previous['interrupted_stream_recovery']
            or ck['recovery_continuation'] != stage
            or not 1039290 < ck['steps'] <= 1039290+(cycle-25)*41250
            or ck['replay']['size'] != ck['steps'] or ck['replay']['cursor'] != ck['steps']
            or set(extra['pending']) != set(range(30))
            or any(len(v) != 31 for v in extra['pending'].values())
            or len(extra['ready']) != ck['steps']-930
            or ck['learner']['outer_updates'] != 1034291+ck['steps']-1039290
            or ck['learner']['num_gradient_steps'] != 8274328+8*(ck['steps']-1039290)):
        raise ValueError('Expected complete parent with unchanged recovery history and930 pending')


def transform(source):
    import resume_serl_interrupted25_20261027 as recovery
    source = recovery.transform(source)
    old = 'partial25 retained; streams0-29 quarantined unchanged; fresh physical streams30-59 in separately budgeted complete26'
    if source.count(old) != 1:
        raise ValueError('Recovery metadata seam drifted')
    source = source.replace(old, 'reviewed complete-cycle continuation after take27; retain partial25 exposure and930 quarantined tails; reuse fully flushed streams30-59')
    seam = "            interruption_recovery=protocol['interrupted_stream_recovery'],"
    if source.count(seam) != 1:
        raise ValueError('Recovery checkpoint seam drifted')
    return source.replace(seam, seam+"\n            recovery_continuation=protocol['recovery_continuation_stage'],")


def main(args):
    import torch
    torch.set_num_threads(1)
    os.sched_setaffinity(0, set(range(13)))
    protocol = json.loads(args.registration.read_text())
    stage = protocol['recovery_continuation_stage']
    if (sha(__file__) != stage['driver_sha256'] or str(args.resume) != stage['checkpoint']['path']
            or sha(args.resume) != stage['checkpoint']['sha256']):
        raise ValueError('Exact source and latest complete checkpoint required')
    rt = Path(stage['runtime'])
    for name, expected in stage['source_hashes'].items():
        if sha(rt/name) != expected:
            raise ValueError('Continuation dependency drift: '+name)
    root, adapter = args.runtime.resolve(), Path(protocol['source_adapter'])
    sys.path[:0] = [str(rt),str(adapter),str(root/'source/tools')]
    import resume_serl_capacity_reviewed_continuation_20261027 as old
    import resume_serl_interrupted25_20261027 as recovery
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from serl_replay_take_gather_20261027 import take_class
    from validate_serl_state_20261026 import digest
    ck = torch.load(args.resume,map_location='cpu',weights_only=False)
    previous = validate_protocol(ck['protocol_sha256'],protocol,sha(args.registration))
    validate_parent(ck,previous)
    # Verify each historical contract as itself, never relabel an incomplete25.
    original = original_recovery_protocol(previous)
    interrupted = recovery.validate_protocol(original['interrupted_stream_recovery']['parent_registration']['sha256'],original,'')
    old.validate(interrupted['resume_parent_registration']['sha256'],interrupted,'')
    for name, expected in previous['interrupted_stream_recovery']['source_hashes'].items():
        if sha(rt/name) != expected:
            raise ValueError('Original recovery dependency drift: '+name)
    for folder, hashes in [(adapter,protocol['source_adapter_hashes']),
                           (root/'source',json.loads((root/'SOURCE_HASHES.json').read_text()))]:
        for name, expected in hashes.items():
            if sha(folder/name) != expected:
                raise ValueError('Frozen source drift: '+name)
    old.validate_sampler_pool(protocol,args,list(range(13)))
    spec = importlib.util.spec_from_file_location('frozen_recovery_continuation_base',adapter/'train_serl_state_20261026.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    native = old.transform_main(inspect.getsource(module.main))
    if hashlib.sha256(native.encode()).hexdigest() != protocol['reviewed_continuation_stage']['patched_main_sha256']:
        raise ValueError('Original trainer main drift')
    candidate_main = transform(native)
    if hashlib.sha256(candidate_main.encode()).hexdigest() != stage['patched_main_sha256']:
        raise ValueError('Continuation main drift')
    base = old.capacity_replay(module.Replay,previous,ck)
    guarded = recovery.quarantine_replay(base,ck['replay']['multistep_target_extension']['pending'])
    if sha(rt/'serl_replay_take_gather_20261027.py') != stage['gather_sha256']:
        raise ValueError('Gather helper drift')
    candidate = take_class(guarded,stage['sample_source_sha256'])
    cls = transfer_class(SerlMultistepLearner)
    if args.check_only:
        os.sched_setaffinity(0,{0})
        learner = cls(root,upstream=args.serl_upstream,upstream_manifest=args.serl_manifest,
                      dimension=7,direct=True,seed=20261026,device=args.device)
        learner.load_state_dict(ck['learner'])
        before = digest(learner.state_dict())
        checks = old.check_replay_restore(module.Replay,candidate,ck,learner)
        left,right = guarded(7,49,1),candidate(7,49,2)
        left.load_state_dict(ck['replay']);right.load_state_dict(ck['replay'])
        for _ in range(3):
            assert digest(left.sample(65536)) == digest(right.sample(65536))
            assert digest(left.rng.bit_generator.state) == digest(right.rng.bit_generator.state)
        assert digest(left.state_dict()) == digest(right.state_dict())
        assert digest(learner.state_dict()) == before == digest(ck['learner'])
        rejects = 0
        for key,value in [('cycle',25),('boundary','partial_episode_valid_replay_reset_environment_on_resume')]:
            bad = dict(ck);bad[key] = value
            try:validate_parent(bad,previous)
            except ValueError:rejects += 1
            else:raise AssertionError('Invalid boundary accepted')
        write(args.output.parent/'CHECK_ONLY_REVIEW.json',dict(passed=True,time=time.time(),
              checkpoint_sha256=sha(args.resume),registration_sha256=sha(args.registration),
              full_learner_digest=before,full_replay_digest=digest(ck['replay']),history_digest=digest(ck['cycles']),
              candidate_vs_original_three_batches_exact=True,old_pending_preserved=930,
              negative_boundary_guards=rejects,new_physics=0,optimizer_updates=0,weights_saved=False,**checks))
        return
    review = json.loads((args.output.parent/'CHECK_ONLY_REVIEW.json').read_text())
    prelaunch = json.loads((args.output.parent/'PRELAUNCH_REVIEW.json').read_text())
    if (not review['passed'] or review['checkpoint_sha256'] != sha(args.resume)
            or review['registration_sha256'] != sha(args.registration)
            or not prelaunch['passed'] or prelaunch['registration_sha256'] != sha(args.registration)):
        raise ValueError('Actual latest complete restore and prelaunch review required')
    args.controller,args.algorithm,args.seed,args.cycles = 'direct','serl_state',20261026,1
    module.PublishedLearner,module.Replay = cls,candidate
    module.validate_resume_protocol = validate_protocol
    module.__dict__.update(_validate_sampler_pool=old.validate_sampler_pool,_sampler_affinity=old.sampler_affinity,
                           _recovery_stream=recovery.stream_id,_verify_initial_state=recovery.verify_initial_state)
    exec(compile(candidate_main,'<registered_take_recovery_continuation>','exec'),module.__dict__)
    write(args.output.parent/'CONTINUATION_EXECUTION.json',dict(time=time.time(),pid=os.getpid(),
          checkpoint=stage['checkpoint'],registration_sha256=sha(args.registration),driver_sha256=sha(__file__),
          new_cycle=stage['new_cycle'],maximum_new_actions=41250,old_pending_quarantined=930,automatic_followup=False))
    (args.output.parent/'SAMPLER_MAIN.py.txt').write_text(candidate_main)
    del ck
    module.main(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['runtime','registration','resume','output','serl-upstream','serl-manifest','sampler-python']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--device',default='cuda:0')
    parser.add_argument('--cpus',required=True)
    parser.add_argument('--workers',type=int,default=30)
    parser.add_argument('--check-only',action='store_true')
    args = parser.parse_args()
    try:main(args)
    except BaseException as error:
        write(args.output.parent/('CHECK_ONLY_FAILURE.json' if args.check_only else 'DRIVER_FAILURE.json'),
              dict(time=time.time(),error=repr(error)))
        raise
