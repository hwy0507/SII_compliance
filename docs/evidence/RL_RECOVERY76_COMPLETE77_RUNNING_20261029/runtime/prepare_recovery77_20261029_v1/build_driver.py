from pathlib import Path
import ast,difflib,json,time,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;old=B/'runtime/parameter75_interruption_recovery_20261029_v1/resume_partial75.py'
s=old.read_text();v=s
v=v.replace('Preserve audited partial75 learner/replay; start one new complete76 physics cycle.','Preserve audited complete recovery76 state; prepare one finite77 with interrupted75 history retained.')
assert v.count(' return source\n')==1
v=v.replace(' return source\n', ' source=source.replace("            environment_state_saved=False,", "            recovery_continuation=protocol[\'post_interruption_continuation\'],\\n            environment_state_saved=False,")\n source=source.replace("        completed_stage_continuation=stage,", "        completed_stage_continuation=stage,\\n        recovery_continuation=protocol[\'post_interruption_continuation\'],")\n return source\n')
a=v.index('def validate_protocol(');b=v.index('def verify_initial_state(',a)
v=v[:a]+'''def validate_protocol(checkpoint_digest,protocol,current_digest):
 st=protocol['post_interruption_continuation'];prior=st['parent_registration'];previous=read(prior['path'])
 if sha(prior['path'])!=prior['sha256'] or checkpoint_digest!=prior['sha256']:raise ValueError('Exact recovery76 registration required')
 if {k:v for k,v in protocol.items() if k!='post_interruption_continuation'}!=previous:raise ValueError('Scientific or historical recovery protocol changed')
 if (st['parent_cycle']!=76 or st['new_cycle']!=77 or st['new_cycles']!=1 or st['maximum_new_actions']!=41250 or st['environment_state_saved'] or st['old_window_continuity_claim'] or st['automatic_followup'] or st['optimizer_settings_changed']):raise ValueError('Invalid complete recovery continuation semantics')
 for key in ['cycle_review','health_review']:
  if sha(st[key]['path'])!=st[key]['sha256']:raise ValueError('Complete76 review binding changed')
 review=read(st['cycle_review']['path']);health=read(st['health_review']['path']);m=st['controller']
 if not review['passed'] or review['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256'] or health['methods'][m]['checkpoint_sha256']!=st['checkpoint']['sha256']:raise ValueError('Evidence must cover exact complete76 checkpoint')
 if sha(st['recovery_driver']['path'])!=st['recovery_driver']['sha256']:raise ValueError('Original recovery driver changed')
 return previous

def validate_parent(ck,st):
 review=read(st['cycle_review']['path'])['methods'][st['controller']]
 previous=read(st['parent_registration']['path'])
 if (ck['cycle']!=76 or ck['boundary']!='complete_condition_cycle' or ck['environment_state_saved'] or ck['steps']!=review['steps'] or ck['seed']!=20261025 or any(c['cycle']==75 for c in ck['cycles']) or ck['cycles'][-1]['cycle']!=76 or ck['interruption_recovery']!=previous['interrupted_episode_recovery']):raise ValueError('Not the exact complete recovery76 boundary')

'''+v[b:]
v=v.replace('all_partial75_rows_retained=True','all_complete76_and_partial75_rows_retained=True')
v=v.replace("st=p['interrupted_episode_recovery']","st=p['post_interruption_continuation']")
needle=" old.validate(previous['resume_parent_registration']['sha256'],previous,sha(st['parent_registration']['path']))"
replacement=""" recovery_spec=importlib.util.spec_from_file_location('validated_original_recovery',st['recovery_driver']['path']);recovery_module=importlib.util.module_from_spec(recovery_spec);recovery_spec.loader.exec_module(recovery_module)
 base75=recovery_module.validate_protocol(previous['interrupted_episode_recovery']['parent_registration']['sha256'],previous,sha(st['parent_registration']['path']))
 old.validate(base75['resume_parent_registration']['sha256'],base75,sha(previous['interrupted_episode_recovery']['parent_registration']['path']))"""
assert needle in v;v=v.replace(needle,replacement)
v=v.replace("('new_cycle',75)","('new_cycle',76)").replace("bad['interrupted_episode_recovery'][key]","bad['post_interruption_continuation'][key]")
v=v.replace('exact partial75 check-only passed','exact complete76 check-only passed')
v=v.replace('frozen_partial75_recovery','frozen_recovery76_continuation').replace('validate_partial_stage','validate_recovery_stage')
v=v.replace('new_cycle=76,maximum_new_actions=41250','new_cycle=77,maximum_new_actions=41250')
ast.parse(v)
# Trainer changes are metadata/initial-state receipt only. Invert every insertion to frozen scientific source.
ns={};exec(compile(v,str(D/'resume_recovery76.py'),'exec'),dict(__name__='static_review'),ns)
# Use import-like shared namespace so global helpers resolve correctly when called later.
mod={'__name__':'static_review'};exec(compile(v,str(D/'resume_recovery76.py'),'exec'),mod)
original=(B/'runs/parameter_capacity_pool30_cycle75_20261026_v1/impedance/trainer_registered.py').read_text();patched=mod['transform'](original)
restore=patched
for added in ["\n        _verify_initial_state(learner, replay, checkpoint, out.parent)","            interruption_recovery=protocol['interrupted_episode_recovery'],\n","            recovery_continuation=protocol['post_interruption_continuation'],\n","\n        interruption_recovery=protocol['interrupted_episode_recovery'],","\n        recovery_continuation=protocol['post_interruption_continuation'],"]:
 assert restore.count(added)==1,(added,restore.count(added));restore=restore.replace(added,'')
assert restore==original
(D/'resume_recovery76.py').write_text(v);(D/'resume_recovery76.py.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(old),tofile=str(D/'resume_recovery76.py'))))
(D/'DRIVER_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),parent_source_sha256=hashlib.sha256(s.encode()).hexdigest(),driver_sha256=hashlib.sha256(v.encode()).hexdigest(),scientific_trainer_inverse_exact=True,trainer_additions=5,actual_full76_restore_not_yet_available=True,automatic_training=False),indent=2)+'\n')
print('Recovery77 driver static source inverse verified')
