from pathlib import Path
import json,hashlib,ast,time,subprocess,os,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
S=B/'runs/parameter48_static_preparation_20261027_v1';O=B/'runs/parameter49_preparation_20261027_v1';RUN=B/'runs/parameter_capacity_pool30_cycle48_20261026_v1'
assert (RUN/'LAUNCH.json').exists();O.mkdir();(O/'templates').mkdir();(O/'sources').mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def replace(s,a,b):
 assert a in s,a
 return s.replace(a,b)
def cycles(s):
 return s.replace('cycle48','cycle49').replace('cycle47','cycle48').replace('cycle_00048','cycle_00049').replace('cycle_00047','cycle_00048').replace('Cycle48','Cycle49').replace('Original47','Original48')
for n in ['resume_cheq_capacity4m_pool30_20261027.py','parameter_replay_capacity4m_20261027.py']:
 (O/'sources'/n).write_bytes((S/'sources'/n).read_bytes())
s=cycles((S/'prepare.py').read_text())
s=replace(s,'parent_cycle=47','parent_cycle=48');s=replace(s,"['parent_cycle']=47","['parent_cycle']=48")
s=replace(s,"ck['cycle']==47","ck['cycle']==48")
s=replace(s,"capacity_before=2_000_000","capacity_before=4_000_000")
s=s.replace('complete47','complete48').replace('expanding2m to4m append capacity','continuing4m append capacity').replace('expand2m to4m append capacity','retain4m append capacity')
s=replace(s,"s['capacity']==2_000_000 and s['size']==s['cursor']==ck['steps'] and s['size']<2_000_000","s['capacity']==4_000_000 and s['size']==s['cursor']==ck['steps'] and s['size']<4_000_000")
s=replace(s,"assert 'replay_capacity_followup' not in s and 'replay_capacity_followup_stage' not in p","assert s['replay_capacity_followup']==FOLLOWUP_MARKER and p['replay_capacity_followup_stage']['parent_cycle']==47")
a=s.index(" expansion=B/'runs/parameter_capacity4m_preparation_20261027_v1'");b=s.index(" baseline=json.loads(parentreg.read_text())",a)
s=s[:a]+" assert p['replay_capacity_followup_stage']==json.loads(parentreg.read_text())['replay_capacity_followup_stage']\n"+s[b:]
s=replace(s,"assert set(trial['dependency_hashes'])-set(baseline)=={driver,followup_helper}","assert trial['dependency_hashes']==baseline")
(O/'prepare.py').write_text(s)
for n in ['launch.py','setup_monitors.py']:(O/n).write_text(cycles((S/n).read_text()))
diffs=[]
for p in (S/'templates').glob('*.py'):
 s=cycles(p.read_text())
 if p.name in ['startup_review.py','review.py']:
  s=replace(s,"old['replay']['capacity']==2_000_000 and old['replay']['replay_capacity_extension']==CAPACITY_MARKER","old['replay']['capacity']==4_000_000 and old['replay']['replay_capacity_extension']==CAPACITY_MARKER and old['replay']['replay_capacity_followup']==FOLLOWUP_MARKER")
  s=replace(s,"old['cycle']==47","old['cycle']==48")
  if p.name=='startup_review.py':
   s=replace(s,"assert followup['entry_checkpoint']==dict(path=str(parent),sha256=sha(parent)) and followup['entry_replay_digest']==digest(old['replay'])","assert followup==previous['replay_capacity_followup_stage']\n assert sha(followup['entry_checkpoint']['path'])==followup['entry_checkpoint']['sha256']")
  else:
   s=replace(s,"assert followup['entry_checkpoint']==dict(path=str(parent),sha256=sha(parent))","assert followup==previous['replay_capacity_followup_stage']")
   s=replace(s,"assert followup['entry_replay_digest']==digest(old['replay']) and old['cycle']==48","assert sha(followup['entry_checkpoint']['path'])==followup['entry_checkpoint']['sha256'] and old['cycle']==48")
   s=replace(s,"assert set(deps)-set(baseline_deps)=={'parameter_replay_capacity4m_20261027.py','resume_cheq_capacity4m_pool30_20261027.py'}","assert deps==baseline_deps")
   s=replace(s,"['cycle']==48","['cycle']==49")
   # Previous parent is complete48; restore this one parent assertion.
   s=replace(s,"old['cycle']==49","old['cycle']==48")
 if p.name=='coordinator.py':s=replace(s,"'--cycle','48'","'--cycle','49'")
 (O/'templates'/p.name).write_text(s)
 diffs.extend(difflib.unified_diff(p.read_text().splitlines(True),s.splitlines(True),fromfile=p.name+'48',tofile=p.name+'49'))
files=[p for p in O.rglob('*.py')]
for p in files:ast.parse(p.read_text())
for n in ['diagnose_published_training_20261025.py','diagnose_published_value_bound_20261025.py']:
 assert (S/'templates'/n).read_bytes()==(O/'templates'/n).read_bytes()
for n in ['startup_review.py','review.py']:
 s=(O/'templates'/n).read_text();old=(S/'templates'/n).read_text()
 # Action, observation, reward reconstruction, and all other downstream checks remain unchanged except cycle names/numbers.
 marker=" ts=" if n=='startup_review.py' else "    transitions="
 normalized=cycles(old[old.index(marker):]).replace("['cycle']==48","['cycle']==49")
 assert s[s.index(marker):]==normalized
 assert "followup['parent_cycle']==47" in s and "old['cycle']==48" in s
write(O/'SOURCE_MANIFEST.json',{str(p.relative_to(O)):sha(p) for p in files})
(O/'TEMPLATE_DIFF.txt').write_text(''.join(diffs))
jobs=json.loads((RUN/'LAUNCH.json').read_text())['jobs'];identities={}
for j in jobs:
 p=Path(f"/proc/{j['pid']}");st=(p/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and RUN.name.encode() in (p/'cmdline').read_bytes()
 identities[str(j['pid'])]=dict(start_ticks=st[19],controller=j['controller'])
w=(B/'runs/parameter48_preparation_20261027_v1/wait_prepare.py').read_text()
w=cycles(w).replace('Bounded47','Bounded48').replace('complete47','complete48').replace('actual_complete47_restore','actual_complete48_restore')
(O/'wait_prepare.py').write_text(w);ast.parse(w)
plan=dict(time=time.time(),wait_seconds=7200,static_directory=str(O),static_manifest_sha256=sha(O/'SOURCE_MANIFEST.json'),waiter_sha256=sha(O/'wait_prepare.py'),parent_identities=identities,automatic_training=False,capacity=4000000,historical_entries=[23,47])
write(O/'PLAN.json',plan)
write(O/'STATIC_REVIEW.json',dict(passed=True,time=time.time(),operational_source_count=len(files),health_sources_byte_identical=True,action_reward_mapping_unchanged_except_cycle=True,historical_followup_parent_cycle=47,actual_parent_cycle=48,next_cycle=49,no_actual48_checkpoint_restore_yet=True,new_physics=0,optimizer_updates=0))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
cmd=[str(B/'env/bin/python'),str(O/'wait_prepare.py')]
with (O/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(O/'LAUNCH.json',dict(time=time.time(),pid=p.pid,command=cmd,start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]));print(p.pid)
