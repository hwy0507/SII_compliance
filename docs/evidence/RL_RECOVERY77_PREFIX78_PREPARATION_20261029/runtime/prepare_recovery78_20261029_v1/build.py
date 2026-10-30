from pathlib import Path
import ast,json,hashlib,difflib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runtime/prepare_recovery77_20261029_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def advance(s):return s.replace('77','__NEXT__').replace('76','77').replace('__NEXT__','78')
def output(name,s,new):
 ast.parse(new);(D/name).write_text(new);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=str(OLD/('resume_recovery76.py' if name=='resume_recovery77.py' else name)),tofile=str(D/name))))
s=(OLD/'resume_recovery76.py').read_text();v=advance(s)
v=v.replace("if {k:v for k,v in protocol.items() if k!='post_interruption_continuation'}!=previous:","if {k:v for k,v in protocol.items() if k!='post_interruption_continuation'}!={k:v for k,v in previous.items() if k!='post_interruption_continuation'}:")
needle=" if sha(st['recovery_driver']['path'])!=st['recovery_driver']['sha256']:raise ValueError('Original recovery driver changed')\n return previous"
replacement=""" if sha(st['recovery_driver']['path'])!=st['recovery_driver']['sha256']:raise ValueError('Original recovery driver changed')
 prior_stage=previous['post_interruption_continuation'];prior_driver=st['previous_driver']
 if sha(prior_driver['path'])!=prior_driver['sha256'] or prior_driver['sha256']!=prior_stage['driver_sha256']:raise ValueError('Previous continuation driver changed')
 spec=importlib.util.spec_from_file_location('validated_previous_recovery77',prior_driver['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.validate_protocol(prior_stage['parent_registration']['sha256'],previous,prior['sha256'])
 return previous"""
assert needle in v;v=v.replace(needle,replacement)
needle="or ck['interruption_recovery']!=previous['interrupted_episode_recovery'])"
assert needle in v;v=v.replace(needle,"or ck['interruption_recovery']!=previous['interrupted_episode_recovery'] or ck.get('recovery_continuation')!=previous['post_interruption_continuation'])")
needle="previous['interrupted_episode_recovery']['parent_registration']['sha256'],previous,sha(st['parent_registration']['path']))"
assert needle in v;v=v.replace(needle,"previous['interrupted_episode_recovery']['parent_registration']['sha256'],{k:v for k,v in previous.items() if k!='post_interruption_continuation'},sha(st['parent_registration']['path']))")
output('resume_recovery77.py',s,v)
oldns={'__name__':'old_static'};newns={'__name__':'new_static'};exec(compile(s,str(OLD/'resume_recovery76.py'),'exec'),oldns);exec(compile(v,str(D/'resume_recovery77.py'),'exec'),newns)
original=(B/'runs/parameter_capacity_pool30_cycle75_20261026_v1/impedance/trainer_registered.py').read_text();patched=newns['transform'](original);assert patched==oldns['transform'](original)
restore=patched
for added in ["\n        _verify_initial_state(learner, replay, checkpoint, out.parent)","            interruption_recovery=protocol['interrupted_episode_recovery'],\n","            recovery_continuation=protocol['post_interruption_continuation'],\n","\n        interruption_recovery=protocol['interrupted_episode_recovery'],","\n        recovery_continuation=protocol['post_interruption_continuation'],"]:
 assert restore.count(added)==1;restore=restore.replace(added,'')
assert restore==original
for n in ['prepare.py','wait_prepare.py','deploy.py']:
 s=(OLD/n).read_text();v=advance(s)
 if n=='prepare.py':
  needle="driver_sha256=sha(D/'resume_recovery77.py'),"
  assert needle in v;v=v.replace(needle,"previous_driver=ref(B/'runtime/prepare_recovery77_20261029_v1/resume_recovery76.py'),"+needle)
 output(n,s,v)
(D/'DRIVER_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),parent_source_sha256=sha(OLD/'resume_recovery76.py'),driver_sha256=sha(D/'resume_recovery77.py'),scientific_trainer_inverse_exact=True,trainer_byte_identical_to77=True,trainer_additions=5,previous_continuation_recursively_validated=True,parent_checkpoint_continuation_must_match=True,actual_full77_restore_not_yet_available=True,automatic_training=False),indent=2)+'\n')
print('78 restore driver prepared; trainer identical, exact historical continuation checked')
