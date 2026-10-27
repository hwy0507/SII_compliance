from pathlib import Path
import ast
R=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/SII_compliance/code/mujoco_6d_vmc_benchmark/tools');src=R/'resume_serl_recovery26_take27_20261027.py';out=R/'resume_serl_take_recovery_continuation_20261027.py';assert not out.exists();s=src.read_text();s=s.replace(s[:s.index('from pathlib')],'''"""One reviewed finite continuation after complete take27.

Retain the exact recovery26/take27 lineage, original930 quarantined tails,
all learner/replay/RNG/history and verified take gather. Never resume partial.
"""
''',1)
a=s.index('def validate_protocol(');b=s.index('\ndef transform(',a)
s=s[:a]+'''def validate_stage_contract(protocol, previous):
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

''' + s[b:]
s=s.replace("'complete26 to27; retain partial25 exposure and930 quarantined tails; reuse fully flushed streams30-59'","'reviewed complete-cycle continuation after take27; retain partial25 exposure and930 quarantined tails; reuse fully flushed streams30-59'")
s=s.replace("interrupted = recovery.validate_protocol(previous['interrupted_stream_recovery']['parent_registration']['sha256'],previous,'')","original = original_recovery_protocol(previous)\n    interrupted = recovery.validate_protocol(original['interrupted_stream_recovery']['parent_registration']['sha256'],original,'')")
s=s.replace('Exact source and complete26 checkpoint required','Exact source and latest complete checkpoint required').replace('Actual complete26 restore and prelaunch review required','Actual latest complete restore and prelaunch review required').replace('<registered_complete26_take27>','<registered_take_recovery_continuation>').replace('new_cycle=27,maximum_new_actions=41250','new_cycle=stage[\'new_cycle\'],maximum_new_actions=41250')
ast.parse(s);out.write_text(s);print(out)
