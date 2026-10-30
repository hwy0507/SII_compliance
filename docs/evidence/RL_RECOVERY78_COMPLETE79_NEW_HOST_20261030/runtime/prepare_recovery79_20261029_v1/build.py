from pathlib import Path
import ast,json,hashlib,difflib,time,re
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runtime/prepare_recovery78_20261029_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def advance(s):
 # Restore constructors' dummy RNG seed is unchanged; full RNG is loaded from checkpoint.
 s=s.replace('20261078','__RESTORE_DUMMY_SEED__')
 s=re.sub('78|77',lambda m:{'78':'79','77':'78'}[m[0]],s)
 return s.replace('__RESTORE_DUMMY_SEED__','20261078').replace('prepare_recovery78_20261029_v1/resume_recovery76.py','prepare_recovery78_20261029_v1/resume_recovery77.py')
files=[]
for source,name in [('resume_recovery77.py','resume_recovery78.py'),('prepare.py','prepare.py'),('wait_prepare.py','wait_prepare.py'),('deploy.py','deploy.py'),('test_contract.py','test_contract.py')]:
 old=(OLD/source).read_text();new=advance(old)
 if name=='test_contract.py':new=new.replace("T=D/'contract_fixtures'","T=D/'contract_fixtures_retry'")
 if name=='prepare.py':
  needle=" assert not OUT.exists();OUT.mkdir()"
  assert needle in new
  new=new.replace(needle," assert os.environ.get('CUDA_VISIBLE_DEVICES')!='','CUDA visibility must retain checkpoint CUDA RNG; do not hide devices for CPU check-only'\n"+needle)
 ast.parse(new);(D/name).write_text(new);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(OLD/source),tofile=str(D/name))))
 files.append(dict(name=name,parent_path=str(OLD/source),parent_sha256=sha(OLD/source),sha256=sha(D/name)))
oldns={'__name__':'old_static'};newns={'__name__':'new_static'}
exec(compile((OLD/'resume_recovery77.py').read_text(),str(OLD/'resume_recovery77.py'),'exec'),oldns);exec(compile((D/'resume_recovery78.py').read_text(),str(D/'resume_recovery78.py'),'exec'),newns)
original=(B/'runs/parameter_capacity_pool30_cycle75_20261026_v1/impedance/trainer_registered.py').read_text();patched=newns['transform'](original);assert patched==oldns['transform'](original)
restore=patched
for added in ["\n        _verify_initial_state(learner, replay, checkpoint, out.parent)","            interruption_recovery=protocol['interrupted_episode_recovery'],\n","            recovery_continuation=protocol['post_interruption_continuation'],\n","\n        interruption_recovery=protocol['interrupted_episode_recovery'],","\n        recovery_continuation=protocol['post_interruption_continuation'],"]:
 assert restore.count(added)==1;restore=restore.replace(added,'')
assert restore==original
(D/'DRIVER_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,parent_source_sha256=sha(OLD/'resume_recovery77.py'),driver_sha256=sha(D/'resume_recovery78.py'),scientific_trainer_inverse_exact=True,trainer_byte_identical_to78=True,trainer_additions=5,previous_continuation_recursively_validated=True,parent_checkpoint_continuation_must_match=True,restore_constructor_dummy_seed_unchanged=True,cuda_visibility_guard_added_before_output_creation=True,actual_full78_restore_not_yet_available=True,automatic_training=False),indent=2)+'\n')
print('79 restore sources prepared; scientific trainer byte-identical to78')
