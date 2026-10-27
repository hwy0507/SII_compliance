from pathlib import Path
import ast,json,hashlib,shutil,time,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';T=R/'code/mujoco_6d_vmc_benchmark/tools';O=B/'runs/serl_recovery_frozen_preparation_20261027_v1';O.mkdir();RT=B/'runtime'/O.name
source=T/'evaluate_serl_capacity_frozen_20261027.py';s=source.read_text()
def once(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
once("if not args.check_only and args.expected_cycle != 26:","if not args.check_only and args.expected_cycle != 29:")
once("Physical evaluation is registered only for complete26","Physical evaluation is registered only for complete29")
once("if args.expected_cycle < 24:","if args.expected_cycle < 27:")
once("Expanded replay checkpoints only","Complete recovered take27 or later checkpoints only")
a=s.index('    # Restore the persisted2m replay');b=s.index('    replay.load_state_dict',a)
s=s[:a]+'''    # Validate recovery contracts as recorded; never relabel partial25 as complete.
    import resume_serl_take_recovery_continuation_20261027 as continuation
    import resume_serl_recovery26_take27_20261027 as entry
    import resume_serl_interrupted25_20261027 as recovery
    import resume_serl_capacity_reviewed_continuation_20261027 as old
    from train_serl_state_20261026 import Replay
    stage = protocol['recovery_continuation_stage']
    validator = entry if stage['parent_cycle'] == 26 else continuation
    previous = validator.validate_protocol(stage['parent_registration']['sha256'], protocol, sha(args.registration))
    continuation.validate_parent(checkpoint, protocol)
    original = continuation.original_recovery_protocol(protocol)
    interrupted = recovery.validate_protocol(original['interrupted_stream_recovery']['parent_registration']['sha256'], original, '')
    old.validate(interrupted['resume_parent_registration']['sha256'], interrupted, '')
    old.validate_capacity(protocol, previous)
    required_modules = ['resume_serl_recovery26_take27_20261027.py',
        'resume_serl_interrupted25_20261027.py', 'resume_serl_capacity_reviewed_continuation_20261027.py',
        'serl_replay_capacity_20261027.py', 'serl_multistep_state_adapter_20261026.py',
        'serl_multistep_replay_gather_20261026.py', 'train_serl_state_20261026.py',
        'validate_serl_state_20261026.py']
    for name in required_modules:
        if sha(Path(__file__).with_name(name)) != stage['source_hashes'][name]:
            raise ValueError('Frozen recovery dependency drift: '+name)
    for name, expected in stage['source_hashes'].items():
        if sha(Path(stage['runtime'])/name) != expected:
            raise ValueError('Original continuation dependency drift: '+name)
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        if sha(root/'source'/name) != expected:
            raise ValueError('Frozen source mismatch: '+name)
    if checkpoint['replay'].get('replay_capacity_extension') != protocol['replay_capacity_stage']['marker']:
        raise ValueError('Persisted capacity marker required; evaluation cannot migrate')
    # Bind all930 quarantined tails to the original interrupted snapshot, not just their count.
    interrupted_ref = protocol['interrupted_stream_recovery']['checkpoint']
    if sha(interrupted_ref['path']) != interrupted_ref['sha256']:
        raise ValueError('Original interrupted snapshot hash drift')
    interrupted_checkpoint = torch.load(interrupted_ref['path'], map_location='cpu', weights_only=False)
    recovery.validate_parent(interrupted_checkpoint, protocol['interrupted_stream_recovery'])
    extra = checkpoint['replay']['multistep_target_extension']
    old_extra = interrupted_checkpoint['replay']['multistep_target_extension']
    if digest(extra['pending']) != digest(old_extra['pending']):
        raise ValueError('Original930 pending queues changed')
    pending_indices = np.asarray([i for rows in extra['pending'].values() for i in rows], dtype=np.int64)
    if len(pending_indices) != 930 or len(np.unique(pending_indices)) != 930:
        raise ValueError('Expected930 distinct quarantined rows')
    for name, values in interrupted_checkpoint['replay']['arrays'].items():
        np.testing.assert_array_equal(checkpoint['replay']['arrays'][name][pending_indices], values[pending_indices])
    for name in ['target_rewards','target_bootstrap','target_endpoints','target_lengths']:
        np.testing.assert_array_equal(extra[name][pending_indices], old_extra[name][pending_indices])
    if not np.all(extra['target_endpoints'][pending_indices] == -1) or set(pending_indices).intersection(extra['ready']):
        raise ValueError('Quarantined pending row became mature/sampleable')
    if checkpoint['cycles'][:len(interrupted_checkpoint['cycles'])] != interrupted_checkpoint['cycles']:
        raise ValueError('Pre-interruption complete-cycle history changed')
    recovery_state = dict(quarantined_pending=930, original_pending_exact=True,
        original_pending_raw_derived_exact=True, pending_not_mature_or_sampleable=True,
        original_interrupted_checkpoint_sha256=interrupted_ref['sha256'],
        pending_digest=digest(extra['pending']), complete25_invented=False,
        complete_cycles_after_recovery=[c['cycle'] for c in checkpoint['cycles'] if c['cycle'] >= 25])
    del interrupted_checkpoint, old_extra
    expanded = old.capacity_replay(Replay, protocol, checkpoint)
    guarded = recovery.quarantine_replay(expanded, extra['pending'])
    replay = guarded(7, 49, 20261079)
''' + s[b:]
once("history_digest=history_digest, replay_capacity=replay.capacity,", "history_digest=history_digest, recovery_state=recovery_state, replay_capacity=replay.capacity,")
once("checkpoint_sha256=sha(snapshot), cycle=checkpoint['cycle']))", "checkpoint_sha256=sha(snapshot), cycle=checkpoint['cycle'], recovery_state=recovery_state))")
once("replay_digest=replay_digest, history_digest=history_digest))", "replay_digest=replay_digest, history_digest=history_digest, recovery_state=recovery_state))")
ast.parse(s);target=T/'evaluate_serl_recovery_frozen_20261027.py';assert not target.exists();target.write_text(s)
# Snapshot original active28 source tree, then add this separate candidate. No formal runtime mutation.
shutil.copytree(B/'runtime/serl_take_cycle28_20261027_v1',RT,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copyfile(target,RT/target.name)
old_review=B/'runtime/serl_cycle26_frozen_full30_20261027_v1/review_serl26_frozen_matrix_20261027.py';review=old_review.read_text().replace("reg['cycle'] == 26","reg['cycle'] == 29").replace("restore['cycle'] == 26","restore['cycle'] == 29").replace('direct_formal26_frozen_stochastic','direct_recovery29_frozen_stochastic').replace('Frozen complete26','Frozen recovered complete29')
seam="        assert restore['checkpoint_sha256'] == reg['inputs']['checkpoint']['sha256']"
assert review.count(seam)==1
review=review.replace(seam,seam+"\n        recovery=restore['recovery_state'];assert recovery['quarantined_pending']==930 and recovery['original_pending_exact'] and recovery['original_pending_raw_derived_exact'] and recovery['pending_not_mature_or_sampleable']\n        assert not recovery['complete25_invented'] and recovery['complete_cycles_after_recovery']==[26,27,28,29]\n        assert state['recovery_state']==recovery")
ast.parse(review);(RT/'review_serl29_recovery_frozen_matrix_20261027.py').write_text(review)
# Ensure inherited raw-substep/actor/filter/torque audit files are identical to original26 evaluator snapshot.
oldrt=old_review.parent
helpers=['audit_published_episode_20261025.py','summarize_published_episode_audit_20261025.py','replay_published_filter_audit_20261025.py','replay_published_torque_audit_20261025.py']
for name in helpers:
 assert (RT/name).read_bytes()==(oldrt/name).read_bytes(),name
# The external seeded policy sampler and physical evaluation loop remain byte-exact.
old=source.read_text()
a=old[old.index('def case_action_seed'):old.index('def evaluate')];b=s[s.index('def case_action_seed'):s.index('def evaluate')];assert a==b
start='    receipt = dict(scope=';end='    replay_unchanged ='
assert old[old.index(start):old.index(end)]==s[s.index(start):s.index(end)]
(O/'evaluator.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=source.name,tofile=target.name)))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
manifest={p.name:sha(p) for p in RT.iterdir() if p.is_file()};(O/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(O/'STATIC_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),runtime=str(RT),candidate_sha256=sha(target),original_evaluator_sha256=sha(source),manifest_sha256=sha(O/'SOURCE_MANIFEST.json'),source_files=len(manifest),external_seeded_action_function_exact=True,physical_loop_exact=True,physical_filter_torque_audit_helpers_exact=helpers,full_restore_validation=False,actual29_restore=False,new_physics=0,optimizer_updates=0),indent=2)+'\n')
print('Candidate frozen recovery evaluator',sha(target),'files',len(manifest))
