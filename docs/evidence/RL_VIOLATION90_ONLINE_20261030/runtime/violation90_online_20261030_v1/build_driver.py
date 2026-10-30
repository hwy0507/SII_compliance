from pathlib import Path
import shutil,ast,difflib
D=Path(__file__).resolve().parent;B=D.parents[1];old=B/'runtime/history89_continuation_20261030_v1';prep=B/'runtime/history89_violation_pipeline_20261030_v1'
for p in old.glob('*.py'):
 if p.name not in ('driver.py','register89.py','check_contract.py'):shutil.copyfile(p,D/p.name)
for n in ('persisted_violation_critic.py','violation_pipeline.py'):shutil.copyfile(prep/n,D/n)
s=(old/'driver.py').read_text();s=s.replace('One explicitly reviewed continuation from exact complete88, preserving history51; no automatic90.','One finite violation52 cycle90 from exact migrated89; no automatic91.').replace('parameter_history_cycle89_20261030_v1','parameter_violation_cycle90_20261030_v1')
start=s.index('def transform(source):');end=s.index('def verify_initial(')
s=s[:start]+'''def transform(source):
 edits=[("\\n        history_critic_amendment=protocol['history_critic_amendment'],", "\\n        history_critic_amendment=protocol['history_critic_amendment'],\\n        violation_critic_amendment=protocol['violation_critic_amendment'],"), ("\\n            history_critic_amendment=protocol['history_critic_amendment'],", "\\n            history_critic_amendment=protocol['history_critic_amendment'],\\n            violation_critic_amendment=protocol['violation_critic_amendment'],"), ("plateau_status([c for c in cycles if c['cycle'] >= 88])", "plateau_status([c for c in cycles if c['cycle'] >= 90])")]
 for old,new in edits:
  if source.count(old)!=1:raise ValueError('Exact89 trainer seam drift: '+old)
  source=source.replace(old,new)
 return source

def validate_protocol(parent_digest,p,current_digest=None):
 from violation_pipeline import validate_registration
 st=p['post_interruption_continuation'];previous=read(st['parent_registration']['path'])
 if sha(st['parent_registration']['path'])!=parent_digest or st['parent_registration']['sha256']!=parent_digest:raise ValueError('Exact migrated89 registration required')
 if {k:v for k,v in p.items() if k!='post_interruption_continuation'}!={k:v for k,v in previous.items() if k!='post_interruption_continuation'}:raise ValueError('Scientific/historical contract changed')
 if (st['parent_cycle'],st['new_cycle'],st['new_cycles'],st['maximum_new_actions'],st['automatic_followup'],st['optimizer_settings_changed'],st['old_window_continuity_claim'],st['environment_state_saved'])!=(89,90,1,41250,False,False,False,False):raise ValueError('Finite90 budget contract drift')
 if sha(__file__)!=st['driver_sha256']:raise ValueError('Driver drift')
 for key in ('cycle_review','health_review','previous_driver','loss_review','training_pair_review','scientific_decision','migration_review','migration_final_review','stability_plan','old_window_failure'):
  if sha(st[key]['path'])!=st[key]['sha256']:raise ValueError('Evidence drift: '+key)
 decision=read(st['scientific_decision']['path'])
 if (decision['parent_cycle'],decision['new_cycle'],decision['new_cycles'],decision['maximum_new_actions_per_method'],decision['automatic_followup'],decision['offline_weights_promoted'],decision['critic_revision'])!=(89,90,1,41250,False,False,'raw_violation52'):raise ValueError('Scientific decision drift')
 for x in decision['evidence']:
  if sha(x['path'])!=x['sha256']:raise ValueError('Decision evidence drift')
 original89=validate_registration(previous)
 spec=importlib.util.spec_from_file_location('validated_scientific89_driver',st['previous_driver']['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 old=original89['post_interruption_continuation'];module.validate_protocol(old['parent_registration']['sha256'],original89)
 migration=read(st['migration_review']['path']);m=st['controller'];binding=p['violation_critic_amendment']['binding']
 if not migration['passed'] or migration['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256'] or not read(st['migration_final_review']['path'])['passed']:raise ValueError('Migration does not bind checkpoint')
 if read(st['cycle_review']['path'])['methods'][m]['checkpoint_sha256']!=binding['checkpoint_sha256'] or read(st['health_review']['path'])['methods'][m]['checkpoint_sha256']!=binding['checkpoint_sha256']:raise ValueError('Scientific89 evidence does not bind original parent')
 if not read(st['loss_review']['path'])['passed']:raise ValueError('Loss review absent')
 window=read(st['stability_plan']['path'])
 if window['cycles']!=[90,91,92] or window['relative_limit']!=.05 or window['near_zero_guard']!=1. or window['replicates']!=5000 or window['automatic_training']:raise ValueError('New revision stability registration changed')
 if window['violation_amendment'][m]!=p['violation_critic_amendment']:raise ValueError('Window revision mismatch')
 return previous

def validate_parent(ck,p):
 from violation_pipeline import validate_migrated
 st=p['post_interruption_continuation'];previous=read(st['parent_registration']['path']);validate_migrated(ck,previous,st['parent_registration']['path'])
 if ck['violation_critic_amendment']!=p['violation_critic_amendment']:raise ValueError('Migration amendment changed')

''' +s[end:]
s=s.replace('full_complete88_learner_and_replay_exact','full_migrated89_learner_and_replay_exact')
s=s.replace("from persisted_history_critic import history_class,history_replay_class", "from violation_pipeline import classes")
s=s.replace("cls=history_class(pair_class(PublishedLearner,'minimum' if args.controller=='impedance' else 'mean'),h['binding']);replay_cls=history_replay_class(replay_class(Replay),h['binding'])",'cls,replay_cls=classes(p)')
s=s.replace("replay_cls(h['binding']['action_dimension'],51,20261078)","replay_cls(h['binding']['action_dimension'],52,20261078)")
s=s.replace("'history89_trainer'","'violation90_trainer'").replace("'HISTORY_EXECUTION.json'","'VIOLATION_EXECUTION.json'").replace('cycle=89,automatic_followup','cycle=90,automatic_followup')
ast.parse(s);(D/'driver.py').write_text(s);(D/'driver.py.diff').write_text(''.join(difflib.unified_diff((old/'driver.py').read_text().splitlines(True),s.splitlines(True),fromfile='scientific89/driver.py',tofile='violation90/driver.py')))
print('Finite90 driver generated')
