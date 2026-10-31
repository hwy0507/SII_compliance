"""Preparation of an explicitly versioned raw-bit pipeline; no online dispatch."""
from pathlib import Path
import json,hashlib,copy
from persisted_history_critic import KEY as HK,marker as hm,history_class
from persisted_violation_critic import KEY as VK,marker as vm,violation_class,violation_replay_class

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def validate_registration(p):
 a=p['violation_critic_amendment'];parent=read(a['parent_registration']['path'])
 if sha(a['parent_registration']['path'])!=a['parent_registration']['sha256']:raise ValueError('Original89 registration drift')
 if {k:v for k,v in p.items() if k!='violation_critic_amendment'}!=parent:raise ValueError('Changed scientific or historical contract')
 if (a['scope'],a['first_cycle'],a['online_launch'],a['physics_steps'],a['formal_updates'])!=('migration_preparation_only',90,False,0,0):raise ValueError('Preparation does not authorize science')
 if set(a)!={'binding','parent_registration','parent_checkpoint','snapshot','scope','first_cycle','online_launch','physics_steps','formal_updates'}:raise ValueError('Unexpected amendment fields')
 b=a['binding'];vm(b)
 if b['history_binding']!=p['history_critic_amendment']['binding'] or b['checkpoint_sha256']!=a['parent_checkpoint']['sha256']:raise ValueError('Original history or parent changed')
 return parent

def validate_parent(ck,p):
 parent=validate_registration(p);a=p['violation_critic_amendment'];b=a['binding'];s=parent['post_interruption_continuation']
 if ck['protocol_sha256']!=a['parent_registration']['sha256'] or ck['controller']!=b['method'] or ck['seed']!=20261025:raise ValueError('Parent identity changed')
 if ck['cycle']!=89 or ck['boundary']!='complete_condition_cycle' or ck['environment_state_saved'] or ck['steps']!=b['rows']:raise ValueError('Complete89 boundary required')
 if ck['cycles'][-1]['cycle']!=89 or any(c['cycle']==75 for c in ck['cycles']):raise ValueError('Complete historical cycles changed')
 if ck['recovery_continuation']!=s or ck['interruption_recovery']!=parent['interrupted_episode_recovery']:raise ValueError('Recovery metadata drift')
 if ck['history_critic_amendment']!=p['history_critic_amendment']:raise ValueError('History amendment drift')
 if s['parent_cycle']!=88 or s['new_cycle']!=89:raise ValueError('Original stage changed')
 for key in ('learner','replay'):
  if ck[key].get(HK)!=hm(b['history_binding']) or VK in ck[key]:raise ValueError('Original history51 state required')
 if ck['replay']['size']!=ck['steps'] or any(ck['replay']['arrays'][k].shape[1]!=51 for k in ('observations','next_observations')):raise ValueError('Parent replay changed')
 return parent

def validate_migrated(ck,p,registration):
 validate_registration(p);a=p['violation_critic_amendment'];b=a['binding']
 if ck.get('violation_critic_amendment')!=a or ck['protocol_sha256']!=sha(registration):raise ValueError('Migrated metadata drift')
 if ck['cycle']!=89 or ck['boundary']!='complete_condition_cycle' or ck['environment_state_saved'] or ck['steps']!=b['rows'] or ck['controller']!=b['method'] or ck['seed']!=20261025:raise ValueError('Migrated89 boundary required')
 if ck['history_critic_amendment']!=p['history_critic_amendment'] or ck['recovery_continuation']!=p['post_interruption_continuation'] or ck['interruption_recovery']!=p['interrupted_episode_recovery']:raise ValueError('Original scientific metadata drift')
 if ck['cycles'][-1]['cycle']!=89 or any(c['cycle']==75 for c in ck['cycles']):raise ValueError('Historical incomplete75 cannot become complete')
 for k in ('learner','replay'):
  if ck[k].get(HK)!=hm(b['history_binding']) or ck[k].get(VK)!=vm(b):raise ValueError('Both exact architecture markers required')
 if ck['replay']['size']!=b['rows'] or ck['replay']['capacity']!=4_000_000 or ck['replay']['cursor']!=b['rows']:raise ValueError('Append-only replay changed')
 if any(ck['replay']['arrays'][k].shape!=(b['rows'],52) for k in ('observations','next_observations')):raise ValueError('Full52 replay required')

def require_online_launch(p):
 # This source snapshot is specifically preparation-only. A future finite driver
 # must be separately registered with its scientific evidence before physics.
 raise ValueError('Preparation trainer cannot launch online90; finite scientific driver not registered')

def transform_trainer(source):
 changes=[("    protocol = json.loads(args.registration.read_text())", "    protocol = json.loads(args.registration.read_text())\n    from violation_pipeline import require_online_launch\n    require_online_launch(protocol)"),
 ("        history_critic_amendment=protocol['history_critic_amendment'],", "        history_critic_amendment=protocol['history_critic_amendment'],\n        violation_critic_amendment=protocol['violation_critic_amendment'],"),
 ("            history_critic_amendment=protocol['history_critic_amendment'],", "            history_critic_amendment=protocol['history_critic_amendment'],\n            violation_critic_amendment=protocol['violation_critic_amendment'],"),
 ("plateau_status([c for c in cycles if c['cycle'] >= 88])", "plateau_status([c for c in cycles if c['cycle'] >= 90])")]
 # Match full lines to avoid the8-space metadata seam also matching12 spaces.
 for old,new in changes:
  old='\n'+old;new='\n'+new
  if old.startswith('\nplateau'):
   old=old[1:];new=new[1:]
  if source.count(old)!=1:raise ValueError('Pinned trainer seam changed: '+old)
  source=source.replace(old,new)
 return source

def classes(p):
 from published_compliance_learner_20261025 import PublishedLearner
 from published_pair_reduction_learner_20261026 import pair_class
 from train_published_compliance_20261025 import Replay
 from parameter_replay_capacity4m_20261027 import replay_class
 b=p['violation_critic_amendment']['binding'];base=pair_class(PublishedLearner,'minimum' if b['method']=='impedance' else 'mean')
 return violation_class(history_class(base,b['history_binding']),b),violation_replay_class(replay_class(Replay),b)
