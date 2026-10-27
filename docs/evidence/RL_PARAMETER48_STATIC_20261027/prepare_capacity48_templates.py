from pathlib import Path
import ast,hashlib,json,re,shutil,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';O=B/'runs/parameter48_static_preparation_20261027_v1';O.mkdir();T=O/'templates';T.mkdir()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,s):ast.parse(s);p.write_text(s)
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def labels(s,old,new):
 for a,b in [(f'cycle{old}',f'cycle{new}'),(f'cycle_000{old}',f'cycle_000{new}'),(f"['cycle']=={old}",f"['cycle']=={new}"),(f"'--cycle','{old}'",f"'--cycle','{new}'"),(f'Cycle{old} archive',f'Cycle{new} archive')]:s=s.replace(a,b)
 return s
oldreview=B/'runs/parameter_capacity_pool30_cycle46_review_20261026_v1'
for src in oldreview.glob('*.py'):
 s=labels(src.read_text(),46,48)
 if src.name=='review.py':
  s=once(s,'from parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER','from parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER\nfrom parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER\nfrom validate_published_finite_check_20261025 import digest')
  s=once(s,"assert x['replay']['capacity']==2_000_000", "assert x['replay']['capacity']==4_000_000 and x['replay']['replay_capacity_followup']==FOLLOWUP_MARKER")
  s=once(s,"    n=old['replay']['size'];arr=x['replay']['arrays']", """    previous=read(reg['resume_parent_registration']['path'])
    assert sha(reg['resume_parent_registration']['path'])==reg['resume_parent_registration']['sha256']
    assert reg['replay_capacity_stage']==previous['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
    followup=reg['replay_capacity_followup_stage']
    assert followup['marker']==FOLLOWUP_MARKER and followup['parent_cycle']==47
    assert followup['entry_checkpoint']==dict(path=str(parent),sha256=sha(parent))
    assert followup['entry_replay_digest']==digest(old['replay']) and old['cycle']==47
    baseline_deps=previous['batch_size_stage']['dependency_hashes'];deps=reg['batch_size_stage']['dependency_hashes']
    assert set(deps)-set(baseline_deps)=={'parameter_replay_capacity4m_20261027.py','resume_cheq_capacity4m_pool30_20261027.py'}
    assert all(deps[k]==v for k,v in baseline_deps.items())
    for name,expected in deps.items():assert sha(B/'runtime/parameter_capacity_pool30_cycle48_20261026_v1'/name)==expected
    n=old['replay']['size'];arr=x['replay']['arrays']""")
  s=once(s,'replay_capacity_extension=CAPACITY_MARKER, replay_size=',"replay_capacity_extension=CAPACITY_MARKER, replay_capacity_followup=FOLLOWUP_MARKER, current_replay_capacity=4_000_000, historical_entry_cycle=23, crossed_second_capacity=x['replay']['size']>2_000_000, rows_beyond_second_capacity=max(0,x['replay']['size']-2_000_000), replay_size=")
 put(T/src.name,s)
s=labels((B/'runs/parameter_capacity_pool30_cycle46_20261026_v1/startup_review.py').read_text(),46,48)
s=once(s,'from parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER','from parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER\nfrom parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER\nfrom validate_published_finite_check_20261025 import digest')
s=once(s,"assert x['replay']['capacity']==2_000_000","assert x['replay']['capacity']==4_000_000 and x['replay']['replay_capacity_followup']==FOLLOWUP_MARKER")
s=once(s," conditions={c['id']:c for c in reg['conditions']};models=0", """ previous=json.loads(Path(reg['resume_parent_registration']['path']).read_text())
 assert sha(reg['resume_parent_registration']['path'])==reg['resume_parent_registration']['sha256']
 assert reg['replay_capacity_stage']==previous['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
 followup=reg['replay_capacity_followup_stage']
 assert followup['marker']==FOLLOWUP_MARKER and followup['parent_cycle']==47 and old['cycle']==47
 assert followup['entry_checkpoint']==dict(path=str(parent),sha256=sha(parent)) and followup['entry_replay_digest']==digest(old['replay'])
 for name,expected in reg['batch_size_stage']['dependency_hashes'].items():assert sha(B/'runtime/parameter_capacity_pool30_cycle48_20261026_v1'/name)==expected
 conditions={c['id']:c for c in reg['conditions']};models=0""")
s=once(s,'replay_capacity_extension=CAPACITY_MARKER,parent_sha256=', 'replay_capacity_extension=CAPACITY_MARKER,replay_capacity_followup=FOLLOWUP_MARKER,current_replay_capacity=4_000_000,historical_entry_cycle=23,parent_sha256=')
put(T/'startup_review.py',s)
# Build preparation without modifying the original47 waiter/runtime.
s=(B/'runtime/prepare_parameter_capacity47_20261026.py').read_text()
# Replace only stage identifiers, not CPU numbers or historical entry23.
replacements={'cycle46':'cycle47','cycle47':'cycle48','cycle_00046':'cycle_00047',"parent_cycle=46":"parent_cycle=47","['parent_cycle']=46":"['parent_cycle']=47","['cycle']==46":"['cycle']==47","complete46":"complete47","cycle47,":"cycle48,","finite cycle47.":"finite cycle48.","Original46":"Original47"}
pattern=re.compile('|'.join(re.escape(k) for k in sorted(replacements,key=len,reverse=True)))
s=pattern.sub(lambda m:replacements[m[0]],s)
s=once(s,'from parameter_replay_capacity_20261026 import MARKER','from parameter_replay_capacity_20261026 import MARKER\nfrom parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER')
s=once(s,"assert all(not Path(f'/proc/{pid}').exists() for pid in [1829718,1829722,1829726]), 'Original47 learners must exit before reusing their CPUs'", "parent_jobs=json.loads((B/'runs'/oldname/'LAUNCH.json').read_text())['jobs']\nassert all(not Path(f\"/proc/{job['pid']}\").exists() for job in parent_jobs), 'Original47 learners must exit before reusing their CPUs'")
s=once(s,"driver='resume_cheq_capacity_pool30_20261026.py';helper='parameter_replay_capacity_20261026.py'", "driver='resume_cheq_capacity4m_pool30_20261027.py';helper='parameter_replay_capacity_20261026.py';followup_helper='parameter_replay_capacity4m_20261027.py'")
s=once(s,'for n in [driver,helper]:','for n in [driver,followup_helper]:')
s=once(s,'capacity_after=2_000_000','capacity_after=4_000_000')
s=s.replace('retaining2m replay capacity and all persisted state/markers','expanding2m to4m append capacity and retaining all persisted state/historical markers').replace('retain2m replay, all rows/RNG/history','expand2m to4m append capacity, retain all rows/RNG/history')
s=once(s," assert ck['cycle']==47", " assert 'replay_capacity_followup' not in s and 'replay_capacity_followup_stage' not in p\n assert ck['cycle']==47")
s=once(s,' del ck,s',""" expansion=B/'runs/parameter_capacity4m_preparation_20261027_v1'
 p['replay_capacity_followup_stage']=dict(marker=FOLLOWUP_MARKER,parent_cycle=47,old_capacity=2_000_000,new_capacity=4_000_000,historical_entry_cycle=23,auxiliary_weights_imported=False,optimizer_settings_changed=False,entry_checkpoint=ref(cp),entry_replay_digest=digest(s),preparation_review=ref(expansion/'REVIEW.json'),malformed_state_review=ref(expansion/'SMALL_GUARDS_REVIEW.json'),helper_sha256=sha(RT/followup_helper))
 baseline=json.loads(parentreg.read_text())['batch_size_stage']['dependency_hashes']
 trial['dependency_hashes'][followup_helper]=sha(RT/followup_helper)
 assert all(trial['dependency_hashes'][k]==v for k,v in baseline.items())
 assert set(trial['dependency_hashes'])-set(baseline)=={driver,followup_helper}
 del ck,s""")
# Existing inherited dependency files must remain byte-exact, not be recopied from moving checkout.
s=once(s,"for n in [driver,followup_helper]:shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/n,RT/n)","for n in [driver,followup_helper]:shutil.copyfile(Path(__file__).parent/'sources'/n,RT/n)")
s=once(s,'statuses={method:proc.wait() for method,proc in checks}', 'statuses={method:proc.wait(timeout=900) for method,proc in checks}')
put(O/'prepare.py',s)
# Manual launch requires independent scientific prelaunch; no auto-training waiter here.
s=(B/'runtime/launch_parameter_capacity47_20261026.py').read_text();s=pattern.sub(lambda m:replacements[m[0]],s)
s=once(s,"for pid in [1829718,1829722,1829726]:assert not Path(f'/proc/{pid}').exists()", "parent_jobs=json.loads((B/'runs/parameter_capacity_pool30_cycle47_20261026_v1/LAUNCH.json').read_text())['jobs']\nfor job in parent_jobs:assert not Path(f\"/proc/{job['pid']}\").exists()")
s=once(s,"subprocess.run(['python',str(B/'runtime/setup_parameter_capacity47_monitors_20261026.py')],check=True)", "subprocess.run([str(B/'env/bin/python'),str(Path(__file__).parent/'setup_monitors.py')],check=True)")
put(O/'launch.py',s)
s=(B/'runtime/setup_parameter_capacity47_monitors_20261026.py').read_text()
start=s.index('def adapt(s):');end=s.index('env=dict(',start)
s=s[:start]+"templates=Path(__file__).parent/'templates'\nfor src in templates.glob('*.py'):\n dest=out/src.name if src.name=='startup_review.py' else review/src.name\n content=src.read_text();ast.parse(content);dest.write_text(content)\n"+s[end:]
s=pattern.sub(lambda m:replacements[m[0]],s)
put(O/'setup_monitors.py',s)
# Freeze new candidate source separately; no formal48 directory or processes created.
(O/'sources').mkdir()
for name in ['parameter_replay_capacity4m_20261027.py','resume_cheq_capacity4m_pool30_20261027.py']:shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/name,O/'sources'/name)
files={str(p.relative_to(O)):sha(p) for p in O.rglob('*.py')}
(O/'SOURCE_MANIFEST.json').write_text(json.dumps(files,indent=2)+'\n')
(O/'PLAN.json').write_text(json.dumps(dict(time=time.time(),parent_cycle=47,new_cycle=48,capacity_before=2000000,capacity_after=4000000,historical_entry_cycle=23,formal_deployment=False,actual_complete47_restore=False,automatic_training=False,waiter_started=False,required_before_launch=['complete47 fullreview and health','original47 learners exited','actual47 fullstate and next65536 restore','independent PRELAUNCH_SCIENTIFIC_REVIEW'],source_manifest_sha256=sha(O/'SOURCE_MANIFEST.json')),indent=2)+'\n')
print(O,len(files))
