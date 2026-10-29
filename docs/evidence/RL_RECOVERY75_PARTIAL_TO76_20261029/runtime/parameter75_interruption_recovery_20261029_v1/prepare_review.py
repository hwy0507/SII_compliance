from pathlib import Path
import re,json,ast,hashlib,time,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_capacity_pool30_cycle74_review_20261026_v1';OUT=B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes={
'runs/parameter_capacity_pool30_cycle74_20261026_v1':'runs/parameter_partial75_recovery_cycle76_20261029_v1',
'runs/parameter_capacity_pool30_cycle74_archive_20261026_v1':'runs/parameter_partial75_recovery_cycle76_archive_20261029_v1',
'runtime/parameter_capacity_pool30_cycle74_20261026_v1':'runtime/parameter_capacity_pool30_cycle75_20261026_v1',
'cycle_00074.pt':'cycle_00076.pt',"['cycle']==74":"['cycle']==76",'Cycle74':'Cycle76',"'--cycle','74'":"'--cycle','76'",
"previous=read(reg['resume_parent_registration']['path'])":"previous=read(reg['interrupted_episode_recovery']['parent_registration']['path'])",
"assert sha(reg['resume_parent_registration']['path'])==reg['resume_parent_registration']['sha256']":"assert sha(reg['interrupted_episode_recovery']['parent_registration']['path'])==reg['interrupted_episode_recovery']['parent_registration']['sha256']",
"old['cycle']==73":"old['cycle']==75"}
records=[]
for name in ['review.py','coordinator.py','diagnose_published_training_20261025.py','diagnose_published_value_bound_20261025.py']:
 a=(OLD/name).read_text();s=a
 if name in ['review.py','coordinator.py']:
  pattern=re.compile('|'.join(re.escape(k) for k in sorted(changes,key=len,reverse=True)));s=pattern.sub(lambda m:changes[m.group()],a)
 if name=='review.py':
  seam="    n=old['replay']['size'];arr=x['replay']['arrays']"
  extra="""    recovery=reg['interrupted_episode_recovery']
    assert old['boundary']=='partial_episode_valid_replay_reset_environment_on_resume' and not old['environment_state_saved']
    assert x['interruption_recovery']==recovery and recovery['parent_cycle']==75 and recovery['new_cycle']==76
    assert not any(c['cycle']==75 for c in x['cycles'])
    assert read(run.parent/'CHECK_ONLY_REVIEW.json')['passed'] and read(run.parent/'INITIAL_STATE_REVIEW.json')['passed']
    assert sha(recovery['partial_audit']['path'])==recovery['partial_audit']['sha256']
    assert sha(parent)==recovery['checkpoint']['sha256']
"""
  assert seam in s;s=s.replace(seam,extra+seam)
  s=s.replace("# Exact stage parent is the formal cycle14 checkpoint already checked above.","# Exact parent is explicitly audited partial75; it is not a complete cycle.")
 ast.parse(s);(OUT/name).write_text(s);(OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(OLD/name),tofile=str(OUT/name))))
 records.append(dict(name=name,parent=str(OLD/name),parent_sha256=sha(OLD/name),sha256=sha(OUT/name)))
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,files=records,changes=changes,additional_checks='Explicit partial75 boundary/recovery metadata/actual initial fullstate and next65536 reviews; old75 never counted complete. Original reward/replay/history/optimizer/full30 checks retained.',automatic_training=False),indent=2)+'\n')
print('Full76 review and original health diagnostics prepared')
