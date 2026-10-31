from pathlib import Path
import shutil,ast,difflib
D=Path(__file__).resolve().parent;B=D.parents[1];OLD=B/'runtime/violation90_online_20261030_v1'
exclude={'driver.py','register90.py','build_driver.py','check_contract.py','run_preflight.py'}
for p in OLD.glob('*.py'):
 if p.name not in exclude:shutil.copyfile(p,D/p.name)
old=(OLD/'driver.py').read_text();s=old.replace('One finite violation52 cycle90 from exact migrated89; no automatic91.','One finite continuation91 from exact trained90; preserve learned52 and no automatic92.').replace('parameter_violation_cycle90_20261030_v1','parameter_violation_cycle91_20261030_v1')
start=s.index('def transform(source):');end=s.index('def verify_initial(')
s=s[:start]+'''def transform(source):
 # Same52 revision: exact actual90 trainer bytes, no numerical/source changes.
 for seam,count in [("learner.load_state_dict(checkpoint['learner'])",1),("replay.load_state_dict(checkpoint['replay'])",1),("violation_critic_amendment=protocol['violation_critic_amendment']",2),("learner.consume_interval(event['interval'], stream=slot)",1),("plateau_status([c for c in cycles if c['cycle'] >= 90])",1)]:
  if source.count(seam)!=count:raise ValueError('Exact90 trainer seam drift: '+seam)
 if 'require_online_launch' in source or 'migrate_parent(' in source:raise ValueError('Migration trainer forbidden for learned90')
 return source

def validate_protocol(parent_digest,p,current_digest=None):
 st=p['post_interruption_continuation'];previous=read(st['parent_registration']['path'])
 if sha(st['parent_registration']['path'])!=parent_digest or st['parent_registration']['sha256']!=parent_digest:raise ValueError('Exact trained90 registration required')
 if {k:v for k,v in p.items() if k!='post_interruption_continuation'}!={k:v for k,v in previous.items() if k!='post_interruption_continuation'}:raise ValueError('Scientific/historical contract changed')
 if (st['parent_cycle'],st['new_cycle'],st['new_cycles'],st['maximum_new_actions'],st['automatic_followup'],st['optimizer_settings_changed'],st['old_window_continuity_claim'],st['environment_state_saved'])!=(90,91,1,41250,False,False,False,False):raise ValueError('Finite91 budget contract drift')
 if sha(__file__)!=st['driver_sha256']:raise ValueError('Driver drift')
 for key in ('cycle_review','health_review','previous_driver','loss_review','fixed_terminal_review','training_pair_review','scientific_decision','stability_plan','old_window_failure','abort_review'):
  if sha(st[key]['path'])!=st[key]['sha256']:raise ValueError('Evidence drift: '+key)
 decision=read(st['scientific_decision']['path'])
 if (decision['parent_cycle'],decision['new_cycle'],decision['new_cycles'],decision['maximum_new_actions_per_method'],decision['automatic_followup'],decision['offline_weights_promoted'],decision['critic_revision'])!=(90,91,1,41250,False,False,'raw_violation52'):raise ValueError('Scientific decision drift')
 for item in decision['evidence']:
  if sha(item['path'])!=item['sha256']:raise ValueError('Decision evidence drift')
 spec=importlib.util.spec_from_file_location('validated_scientific90_driver',st['previous_driver']['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 old=previous['post_interruption_continuation'];module.validate_protocol(old['parent_registration']['sha256'],previous)
 m=st['controller'];review=read(st['cycle_review']['path']);health=read(st['health_review']['path']);loss=read(st['loss_review']['path'])
 if not review['passed'] or not loss['passed'] or health['cycle']!=90 or health['optimizer_updates_performed']!=0:raise ValueError('Complete90 evidence missing')
 if review['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256'] or health['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256']:raise ValueError('Complete90 checkpoint binding mismatch')
 if loss['methods'][m]['rows']!=review['methods'][m]['new_transitions'] or not loss['methods'][m]['all_finite']:raise ValueError('Complete90 loss rows mismatch')
 if read(st['fixed_terminal_review']['path'])['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256']:raise ValueError('Fixed-terminal parent mismatch')
 window=read(st['stability_plan']['path'])
 if window['cycles']!=[90,91,92] or window['relative_limit']!=.05 or window['near_zero_guard']!=1. or window['replicates']!=5000 or window['bootstrap_seed']!=2026102861 or window['automatic_training']:raise ValueError('Revision stability registration changed')
 if window['violation_amendment'][m]!=p['violation_critic_amendment'] or window['history_amendment'][m]!=p['history_critic_amendment']:raise ValueError('Window revision mismatch')
 return previous

def validate_parent(ck,p):
 from persisted_history_critic import KEY as HK,marker as hm
 from persisted_violation_critic import KEY as VK,marker as vm
 from parameter_replay_capacity_20261026 import MARKER as OLD_CAP
 from parameter_replay_capacity4m_20261027 import MARKER as CAP
 st=p['post_interruption_continuation'];previous=read(st['parent_registration']['path']);review=read(st['cycle_review']['path'])['methods'][st['controller']];v=p['violation_critic_amendment'];h=p['history_critic_amendment'];n=review['steps']
 if ck['protocol_sha256']!=st['parent_registration']['sha256'] or ck['controller']!=st['controller'] or ck['controller']!=v['binding']['method'] or ck['seed']!=20261025:raise ValueError('Exact trained90 identity required')
 if ck['cycle']!=90 or ck['boundary']!='complete_condition_cycle' or ck['environment_state_saved'] or ck['steps']!=n:raise ValueError('Complete trained90 boundary required')
 if n!=v['binding']['rows']+review['new_transitions'] or not 0<review['new_transitions']<=41250:raise ValueError('Actual complete90 rows including abort required')
 if ck['cycles'][-1]['cycle']!=90 or any(c['cycle']==75 for c in ck['cycles']):raise ValueError('Historical complete cycles changed')
 if ck['recovery_continuation']!=previous['post_interruption_continuation'] or ck['interruption_recovery']!=p['interrupted_episode_recovery']:raise ValueError('Recovery metadata drift')
 if ck['history_critic_amendment']!=h or ck['violation_critic_amendment']!=v:raise ValueError('Trained architecture amendments changed')
 for key in ('learner','replay'):
  if ck[key].get(HK)!=hm(h['binding']) or ck[key].get(VK)!=vm(v['binding']):raise ValueError('Both learned architecture markers required')
 replay=ck['replay']
 if replay['size']!=n or replay['cursor']!=n or replay['capacity']!=4_000_000 or replay['replay_capacity_extension']!=OLD_CAP or replay['replay_capacity_followup']!=CAP:raise ValueError('Append-only replay metadata changed')
 if any(replay['arrays'][k].shape!=(n,52) for k in ('observations','next_observations')):raise ValueError('Full learned52 replay required')
 if ck['learner']['num_gradient_steps']!=review['updates']:raise ValueError('Trained optimizer counter changed')

''' +s[end:]
s=s.replace('full_migrated89_learner_and_replay_exact','full_trained90_learner_and_replay_exact').replace('learned_history_weights_and_adam_retained=True','learned_history_weights_and_adam_retained=True,learned_violation_weights_and_adam_retained=True')
s=s.replace("'violation90_trainer'","'violation91_trainer'").replace('cycle=90,automatic_followup','cycle=91,automatic_followup')
ast.parse(s);(D/'driver.py').write_text(s);(D/'driver.py.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(OLD/'driver.py'),tofile='driver91.py')))
