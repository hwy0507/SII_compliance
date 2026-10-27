from pathlib import Path
import hashlib,ast,json,time,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');src=B/'runs/serl_recovery27_preparation_20261027_v1';O=B/'runs/serl_take28_preparation_20261027_v1';D=O/'templates';D.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changes=[('serl_recovery26_take27_20261027_v1','serl_take_cycle28_20261027_v1'),('serl_recovery26_take27_archive_20261027_v1','serl_take_cycle28_archive_20261027_v1'),('serl_recovery26_take27_review_20261027_v1','serl_take_cycle28_review_20261027_v1'),('audit_serl_recovery27_replay_20261027','audit_serl_take28_replay_20261027'),('cycle_00027','cycle_00028'),("['cycle']==27","['cycle']==28"),("old['cycle']==26","old['cycle']==27"),("['parent_cycle']==26","['parent_cycle']==27"),('complete_parent26=True','complete_parent27=True'),('Take27 archive','Take28 archive'),('take27: optimizer','take28: optimizer'),('len(terminal)==810','len(terminal)==840'),('terminal_count=810','terminal_count=840')]
files={}
for p in (src/'templates').glob('*.py'):
 s=p.read_text();original=s
 for a,b in changes:s=s.replace(a,b)
 if p.name in ['review.py','startup_review.py']:
  line="assert x['recovery_continuation']==reg['recovery_continuation_stage']"
  indent='    ' if p.name=='review.py' else ' '
  s=s.replace(line,line+'\n'+indent+"assert old['recovery_continuation']==parent_reg['recovery_continuation_stage']\n"+indent+"assert reg['recovery_continuation_stage']['new_cycle']==28")
 ast.parse(s);name=p.name.replace('audit_serl_recovery27','audit_serl_take28');(D/name).write_text(s);files[name]=sha(D/name)
 (O/(name+'.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='27/'+p.name,tofile='28/'+name)))
s=(src/'launch.py').read_text();original=s
for a,b in changes:s=s.replace(a,b)
s=s.replace('complete26 ->27','complete27 ->28').replace('/proc/645388','/proc/3712293');ast.parse(s);(O/'launch.py').write_text(s)
(O/'launch.py.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='27/launch.py',tofile='28/launch.py')))
for p in D.glob('*.py'):
 s=p.read_text();assert 'cycle_00027' not in s and "['cycle']==27" not in s.replace("old['cycle']==27",'')
 assert 'serl_recovery26_take27' not in s
assert "row['cycle']==28" in (D/'audit_serl_take28_replay_20261027.py').read_text()
assert 'len(terminal)==840' in (D/'diagnose.py').read_text()
(O/'MONITOR_TEMPLATE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,parent_cycle=27,new_cycle=28,terminal_count=840,quarantine_rows=930,original_physics_and_learner_unchanged=True,static_only=True,actual_complete27_restore=False,new_physics=0,optimizer_updates=0,launch_sha256=sha(O/'launch.py')),indent=2)+'\n');print(files)
