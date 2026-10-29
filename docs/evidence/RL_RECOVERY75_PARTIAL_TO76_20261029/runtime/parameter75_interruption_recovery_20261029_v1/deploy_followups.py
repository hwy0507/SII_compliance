from pathlib import Path
import json,hashlib,ast,time,subprocess,os,re,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';L=B/'runs/parameter_recovery76_loss_20261029_v1';OLD=B/'runs/parameter75_loss_20261028_v1';W=B/'runs/parameter_recovery76_78_reward_stability_20261029_v1';OW=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
L.mkdir(exist_ok=False);records=[]
helper="""\ndef episode_file(c,m):
    if c==75:raise ValueError('Interrupted75 has no complete-cycle reward')
    if c==76:return B/f'runs/parameter_partial75_recovery_cycle76_20261029_v1/{m}/train/episodes.jsonl'
    return B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl'
"""
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py']:
 a=(OLD/name).read_text();s=a.replace('parameter_capacity_pool30_cycle75_20261026_v1','parameter_partial75_recovery_cycle76_20261029_v1').replace('[74,75]','[74,76]').replace('reward75','reward76').replace('complete75','complete76').replace('Complete75','Complete76').replace('full75','full76')
 if name=='audit.py':
  assert ',73,74,75]:' in s;s=s.replace(',73,74,75]:',',73,74,76]:').replace('Reward49-75 is descriptive','Reward49-74 plus76 is descriptive;75 is interrupted and explicitly unavailable; this gap is additional partial75 training exposure')
 for key in ["B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1/{m}/train/episodes.jsonl'","B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl'",'B/f"runs/parameter_capacity_pool30_cycle{h[\'cycle\']}_20261026_v1/{m}/train/episodes.jsonl"']:
  arg='cycle' if '{cycle}' in key else "h['cycle']" if "h['cycle']" in key else 'c';s=s.replace(key,'episode_file('+arg+',m)')
 if name!='wait.py':
  pos=s.index('\ndef sha(');s=s[:pos]+helper+s[pos:]
 if name=='audit.py':
  s=s.replace("limitation='Complete76", "interrupted75=dict(complete=False,audit=str(B/'runs/parameter75_interruption_recovery_20261029_v1/REVIEW.json')),limitation='Complete76")
 if name=='paired_gate.py':s=s.replace("limitation='All30 paired", "limitation='Comparison74to76 spans retained partial75 exposure; not adjacent complete training cycles. All30 paired")
 if name=='wait.py':
  s=s.replace(" (OUT/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True)))", " (OUT/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),completed=True)))\n subprocess.run([plan['python'],str(OUT/'review_saved.py')],check=True)")
 ast.parse(s);(L/name).write_text(s);(L/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(OLD/name),tofile=str(L/name))))
 records.append(dict(name=name,parent=str(OLD/name),parent_sha256=sha(OLD/name),sha256=sha(L/name)))
assert 'for cycle in [49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,76]' in (L/'audit.py').read_text()
write(L/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=records,history49_74_retained=True,partial75_explicitly_unavailable=True,new76_full_loss=True,paired74_76_descriptive_across_partial75_exposure=True,original_formulas_and_gates_unchanged=True))
launch=read(R/'LAUNCH.json');write(L/'PLAN.json',dict(time=time.time(),parent_run=str(R),jobs=launch['jobs'],python=str(B/'env/bin/python'),sources={n:sha(L/n) for n in ['audit.py','paired_gate.py','review_saved.py','wait.py']},partial75_audit=dict(path=str(B/'runs/parameter75_interruption_recovery_20261029_v1/REVIEW.json'),sha256=sha(B/'runs/parameter75_interruption_recovery_20261029_v1/REVIEW.json')),automatic_training=False))
# Keep the original window arithmetic; only cycle names and explicitly registered run paths differ.
for name in ['wait_register_and_audit.py','review_saved.py']:
 a=(OW/name).read_text();s=re.sub(r'(?<!\d)(74|75|76)(?!\d)',lambda m:{'74':'76','75':'77','76':'78'}[m.group()],a)
 if name=='wait_register_and_audit.py':
  s=s.replace("root/'audit_parameter76_78_reward_stability_20261028.py'","root/'audit.py'")
  s=s.replace("B/'runs'/f'parameter_capacity_pool30_cycle{cycle}_review_20261026_v1'","Path(plan['review_paths'][str(cycle)])")
  s=s.replace("B/'runs'/f'parameter_capacity_pool30_cycle{cycle}_20261026_v1'","Path(plan['run_paths'][str(cycle)])")
 ast.parse(s);(W/name).write_text(s);(W/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(OW/name),tofile=str(W/name))))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
for folder,script in [(L,'wait.py'),(W,'wait_register_and_audit.py')]:
 assert not (folder/'LAUNCH.json').exists()
 for j in launch['jobs']:
  f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
 f=(folder/'driver.log').open('x');p=subprocess.Popen([str(B/'env/bin/python'),str(folder/script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True);f.close();receipt=dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(folder/'PLAN.json'),source_sha256=sha(folder/script),automatic_training=False);write(folder/'LAUNCH.json',receipt);print(folder.name,receipt,flush=True)
