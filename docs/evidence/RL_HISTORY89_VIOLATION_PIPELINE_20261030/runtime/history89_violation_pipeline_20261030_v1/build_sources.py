from pathlib import Path
import shutil,ast,difflib,json,hashlib,time
D=Path(__file__).resolve().parent;B=D.parents[1];OLD=B/'runtime/history88_frozen_preparation_20261030_v1';C=B/'runtime/history89_violation_consumers_20261030_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for p in OLD.glob('*.py'):
 if p.name not in ('evaluate_history88.py','check_updated_frozen.py','prepare_frozen88.py','register_complete88.py','save_progress.py'):shutil.copyfile(p,D/p.name)
for name in ('persisted_violation_critic.py','violation_consumers.py'):shutil.copyfile(C/name,D/name)
shutil.copyfile(B/'runtime/history89_review_20261030_v1/diagnose_published_value_bound_20261025.py',D/'diagnose_published_value_bound_20261025.py')
records={}
def save(old,name,s):
 ast.parse(s);(D/name).write_text(s);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),s.splitlines(True),fromfile=str(old),tofile=name)));records[name]=dict(parent=str(old),parent_sha256=sha(old),sha256=sha(D/name))
def replace(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
# Exercise the actual evaluator's restoration, source/model gates, replay and RNG
# gate. Physics is deliberately disabled in this preparation-only entrypoint.
p=OLD/'evaluate_history88.py';s=p.read_text().replace('complete88','migrated complete89').replace('expected_cycle=88','expected_cycle=89').replace('expected_cycle in (88,)','expected_cycle in (89,)').replace('expected_cycle not in (88,)','expected_cycle not in (89,)').replace('choices=[88], default=88','choices=[89], default=89')
s=replace(s,'    if expected_cycle != 88 and not check_only:\n        raise ValueError("Only planned88 may execute physics; validation87 is check-only")','    if not check_only:\n        raise ValueError("Migration preparation has no physical evaluation authorization")')
s=replace(s,'    binding = protocol[\'history_critic_amendment\'][\'binding\']',"    binding = protocol['history_critic_amendment']['binding']\n    from violation_pipeline import validate_migrated\n    from persisted_violation_critic import violation_class, violation_replay_class\n    vb = protocol['violation_critic_amendment']['binding']\n    validate_migrated(ck, protocol, reg['training_registration'])")
s=s.replace('history_replay_class(replay_class(Replay), binding)(ck[\'replay\'][\'arrays\'][\'actions\'].shape[1], 51, 2026102638)','violation_replay_class(replay_class(Replay), vb)(ck[\'replay\'][\'arrays\'][\'actions\'].shape[1], 52, 2026102638)')
s=replace(s,'learner = history_class(pair_class(PublishedLearner, reduction), binding)(root','learner = violation_class(history_class(pair_class(PublishedLearner, reduction), binding), vb)(root')
s=replace(s,"    validate_recovery(ck, protocol, expected_cycle)","    validate_recovery(ck, protocol, expected_cycle)\n    assert protocol['violation_critic_amendment']['scope'] == 'migration_preparation_only'")
s=s.replace('History51','Violation52')
s=replace(s,'    if check_only:\n        assert digest(replay.state_dict()) == replay_digest\n        return',"    if check_only:\n        assert digest(replay.state_dict()) == replay_digest\n        assert digest(learner.state_dict()) == initial and sha(reg['checkpoint']) == reg['checkpoint_sha256']\n        return")
save(p,'evaluate_violation_preparation.py',s)
p=OLD/'frozen_helpers.py';s=p.read_text().replace('History51','Violation52').replace('obs.shape == (51,)','obs.shape == (52,)');save(p,'frozen_helpers.py',s)
# Existing full health diagnosis, preserving its explicitly unprojected TD rule.
p=B/'runtime/history89_review_20261030_v1/health89.py';s=p.read_text()
s=replace(s,"        if checkpoint['protocol_sha256'] != execution['protocol_sha256']:","        protocol = json.loads((args.registrations/method/'REGISTRATION.json').read_text())\n        from violation_pipeline import validate_migrated\n        validate_migrated(checkpoint, protocol, args.registrations/method/'REGISTRATION.json')\n        if protocol['violation_critic_amendment']['parent_registration']['sha256'] != execution['protocol_sha256']:")
s=replace(s,"        protocol = json.loads((folder.resolve().parent/'REGISTRATION.json').read_text())", "        from persisted_violation_critic import violation_class\n        vb = protocol['violation_critic_amendment']['binding']")
s=replace(s,'learner = history_class(PublishedLearner, binding)(root','learner = violation_class(history_class(PublishedLearner, binding), vb)(root')
s=s.replace('remaining time and causal history;', 'remaining time, causal history and raw violation bit;')
s=replace(s,"    parser.add_argument('--runtime', type=Path, required=True)","    parser.add_argument('--runtime', type=Path, required=True)\n    parser.add_argument('--registrations', type=Path, required=True)")
save(p,'health_violation_preparation.py',s)
(D/'SOURCE_ADAPTATION.json').write_text(json.dumps(dict(time=time.time(),files=records,physical_steps=0,formal_updates=0,online90=False),indent=2)+'\n')
print('Sources prepared',len(list(D.glob('*.py'))))
