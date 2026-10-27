from pathlib import Path
import json,time,hashlib,subprocess,os,ast,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');S=B/'runs/parameter49_preparation_20261027_v1';O=B/'runs/parameter50_preparation_20261027_v1';RUN=B/'runs/parameter_capacity_pool30_cycle49_20261026_v1'
O.mkdir();(O/'sources').mkdir();(O/'templates').mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def shift(s):
 for a,b in [('cycle49','cycle50'),('cycle48','cycle49'),('cycle_00049','cycle_00050'),('cycle_00048','cycle_00049'),('complete49','complete50'),('complete48','complete49'),('Original49','Original50'),('Original48','Original49'),('Cycle49','Cycle50'),('Cycle48','Cycle49'),('Bounded48','Bounded49'),("'--cycle','49'","'--cycle','50'"),("['cycle']==49","['cycle']==50"),("['cycle']==48","['cycle']==49"),("['parent_cycle']=48","['parent_cycle']=49"),('parent_cycle=48','parent_cycle=49')]:s=s.replace(a,b)
 return s
files=[];diffs=[]
for rel,expected in json.loads((S/'SOURCE_MANIFEST.json').read_text()).items():
 p=S/rel;assert sha(p)==expected;q=O/rel
 if rel.startswith('sources/'):
  q.write_bytes(p.read_bytes());assert sha(q)==sha(p)
 else:
  old=p.read_text();new=shift(old);q.write_text(new);diffs.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel+'49',tofile=rel+'50'))
 ast.parse(q.read_text());files.append(q)
assert len(files)==10
for n in ['review.py','startup_review.py']:
 s=(O/'templates'/n).read_text();assert "old['cycle']==49" in s and "followup['parent_cycle']==47" in s and '4_000_000' in s
for n in ['diagnose_published_training_20261025.py','diagnose_published_value_bound_20261025.py']:assert (O/'templates'/n).read_bytes()==(S/'templates'/n).read_bytes()
write(O/'SOURCE_MANIFEST.json',{str(p.relative_to(O)):sha(p) for p in files});(O/'SOURCE_DIFF.txt').write_text(''.join(diffs))
wait=shift((S/'wait_prepare.py').read_text());(O/'wait_prepare.py').write_text(wait);ast.parse(wait)
jobs=json.loads((RUN/'LAUNCH.json').read_text())['jobs'];ids={}
for j in jobs:
 p=Path(f"/proc/{j['pid']}");st=(p/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and RUN.name.encode() in (p/'cmdline').read_bytes();ids[str(j['pid'])]=dict(start_ticks=st[19],controller=j['controller'])
plan=dict(time=time.time(),wait_seconds=7200,static_directory=str(O),static_manifest_sha256=sha(O/'SOURCE_MANIFEST.json'),waiter_sha256=sha(O/'wait_prepare.py'),parent_identities=ids,automatic_training=False,capacity=4000000,historical_entries=[23,47])
write(O/'PLAN.json',plan);write(O/'STATIC_REVIEW.json',dict(passed=True,time=time.time(),only_current_parent_target_cycles_changed=True,operational_source_count=10,source=str(S),health_and_driver_helper_byte_identical=True,historical_followup_parent_cycle=47,actual_parent_cycle=49,next_cycle=50,no_actual49_checkpoint_restore_yet=True,new_physics=0,optimizer_updates=0))
cmd=[str(B/'env/bin/python'),str(O/'wait_prepare.py')]
with (O/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
write(O/'LAUNCH.json',dict(time=time.time(),pid=p.pid,command=cmd,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]));print(p.pid)
