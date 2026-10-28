from pathlib import Path
import json,time,hashlib,re,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');run=B/'runs/parameter_capacity_pool30_cycle64_20261026_v1';out=B/'runs/vmc64_terminal_anchor_followup_20261028_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else [];return bool(s and s[19]==j['proc_start_ticks'] and s[0]!='Z')
launch=json.loads((run/'LAUNCH.json').read_text());monitor=json.loads((run/'MONITOR_LAUNCH.json').read_text());assert all(live(j) for j in launch['jobs']) and live(monitor)
assert not (run/'ARCHIVE_REVIEW_FINISHED.json').exists()
mp={'00062':'00063','00063':'00064','62':'63','63':'64','1884':'1914','1914':'1944'};rx=re.compile(r'(?<!\d)('+ '|'.join(mp)+r')(?!\d)')
s=(B/'runs/vmc63_terminal_anchor_followup_20261028_v1/PLAN.json').read_text()
s=''.join(x if re.fullmatch(r'[a-f0-9]{64}',x) else rx.sub(lambda m:mp[m[0]],x) for x in re.split(r'([a-f0-9]{64})',s));plan=json.loads(s)
plan.update(time=time.time(),learners=launch['jobs'],monitor=monitor,parent_launch_sha256=sha(run/'LAUNCH.json'),sources={n:sha(out/n) for n in ['track.py','review_values.py','wait.py']})
plan['inputs']={k:ref(Path(v['path'])) for k,v in plan['inputs'].items()}
assert json.loads((out/'ANCHOR_SAVED_REVIEW.json').read_text())['passed']
assert plan['parent_run']==str(run) and plan['fixed_anchor_rows']==1914 and plan['expected_complete64_terminal_rows']==1944
write(out/'PLAN.json',plan)
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
label=B/'runs/parameter_task_label_audit64_20261028_v1';src=B/'runtime/parameter_task_label_audit64_20261028_v1'
probe=subprocess.run([str(B/'env/bin/python'),str(src/'audit_labels.py'),'--before','63','--after','64','--output',str(label/'REJECT_INCOMPLETE.json')],capture_output=True,text=True,env=env)
assert probe.returncode!=0 and 'Incomplete cycle 64' in probe.stderr and not (label/'REJECT_INCOMPLETE.json').exists();write(label/'INCOMPLETE_REJECTION.json',dict(passed=True,returncode=probe.returncode,stderr=probe.stderr,no_output_created=True,time=time.time()))
for script,folder,name,planfile,log in [(out/'wait.py',out,'LAUNCH.json','PLAN.json','driver.log'),(src/'wait64.py',label,'LAUNCH64.json','PLAN64.json','wait64.log')]:
 assert not (folder/name).exists()
 with (folder/log).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(script)],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 job=dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(folder/planfile));assert live(job);write(folder/name,job);print(folder.name,json.dumps(job))
