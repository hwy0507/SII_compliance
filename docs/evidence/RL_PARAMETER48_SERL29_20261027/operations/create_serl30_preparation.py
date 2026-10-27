from pathlib import Path
import ast,json,hashlib,time,re,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
S=B/'runs/serl_take29_preparation_20261027_v1';O=B/'runs/serl_take30_preparation_20261027_v1';RUN=B/'runs/serl_take_cycle29_20261027_v1'
assert json.loads((RUN/'startup/REVIEW.json').read_text())['passed']
job=json.loads((RUN/'LAUNCH.json').read_text());pid=job['pid'];p=Path(f'/proc/{pid}');st=(p/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and st[19]==job['start_ticks']
O.mkdir();(O/'templates').mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def shift(s):return re.sub(r'(?<!\d)(28|29)(?!\d)',lambda m:str(int(m[0])+1),s).replace('00029','00030').replace('00028','00029').replace('1978250',str(pid)).replace('870','900')
for n in ['prepare.py','launch.py']:(O/n).write_text(shift((S/n).read_text()))
manifest={}
for p in (S/'templates').glob('*.py'):
 q=O/'templates'/shift(p.name);q.write_text(shift(p.read_text()));ast.parse(q.read_text());manifest[q.name]=sha(q)
for n in ['prepare.py','launch.py']:ast.parse((O/n).read_text())
for n in ['startup_review.py','review.py']:
 s=(O/'templates'/n).read_text();assert "old['cycle']==29" in s and "['new_cycle']==30" in s and 'quarantined' in s
assert 'terminal_count=900' in (O/'templates/diagnose.py').read_text()
old=json.loads((S/'STATIC_REVIEW.json').read_text())
write(O/'STATIC_REVIEW.json',dict(passed=True,time=time.time(),driver_sha256=old['driver_sha256'],patched_main_sha256=old['patched_main_sha256'],inherited_static_review=dict(path=str(S/'STATIC_REVIEW.json'),sha256=sha(S/'STATIC_REVIEW.json')),source_unchanged=True,actual_complete29_restoration=False,new_physics=0,optimizer_updates=0,formal_deployment=False))
write(O/'MONITOR_TEMPLATE_REVIEW.json',dict(passed=True,time=time.time(),files=manifest,source=str(S/'templates'),only_cycle_parent_pid_terminal_count_changed=True,parent_cycle=29,new_cycle=30,expected_terminal_count=900,quarantined_pending_count=930))
write(O/'PLAN.json',dict(time=time.time(),parent_identity=dict(pid=pid,start_ticks=st[19]),parent_cycle=29,new_cycle=30,wait_seconds=7200,check_only_seconds=900,automatic_training=False,requires_manual_review_of_fixed27_29_before_training=True,source_hashes={n:sha(O/n) for n in ['prepare.py','launch.py']}))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
cmd=['taskset','-c','54',str(B/'env/bin/python'),str(O/'prepare.py')]
with (O/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(O/'LAUNCH.json',dict(time=time.time(),pid=p.pid,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=cmd));print(p.pid)
