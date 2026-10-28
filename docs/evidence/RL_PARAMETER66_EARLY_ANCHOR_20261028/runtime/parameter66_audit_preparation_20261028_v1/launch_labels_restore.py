from pathlib import Path
import os,json,hashlib,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');run=B/'runs/parameter_capacity_pool30_cycle66_20261026_v1';py=str(B/'env/bin/python')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,v):
 with p.open('x') as f:f.write(json.dumps(v,indent=2)+'\n')
def live(j):
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
jobs=read(run/'LAUNCH.json')['jobs'];monitor=read(run/'MONITOR_LAUNCH.json')
for j in jobs+[monitor]:live(j)
assert not(run/'ARCHIVE_REVIEW_FINISHED.json').exists()
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
def launch(script,args,log,receipt,plan):
 with log.open('x') as f:p=subprocess.Popen([py,str(script)]+args,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 st=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split();j=dict(pid=p.pid,proc_start_ticks=st[19],time=time.time(),plan_sha256=sha(plan));write(receipt,j);print(json.dumps(j))
root=B/'runtime/prepare_parameter67_20261028_v1';p=root/'REGISTRATION.json';write(p,dict(time=time.time(),jobs=dict(parameter=dict(parent_run=str(run),parent_review=str(B/'runs/parameter_capacity_pool30_cycle66_review_20261026_v1'),parent_launch_sha256=sha(run/'LAUNCH.json'),learners=jobs,monitor=monitor,prepare_source=str(root/'prepare_parameter67.py'),prepare_source_sha256=sha(root/'prepare_parameter67.py'),python=py)),automatic_training=False,wait_deadline_seconds=14400))
r=subprocess.run([py,str(root/'launch_parameter67.py')],capture_output=True,text=True,env=env);assert r.returncode!=0 and 'DECISION67.json' in r.stderr and not(B/'runs/parameter_capacity_pool30_cycle67_20261026_v1').exists();write(root/'UNREVIEWED_LAUNCH_REJECTION.json',dict(time=time.time(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,no_training_run_created=True))
launch(root/'wait_prepare.py',['parameter'],root/'parameter_driver.log',root/'parameter_LAUNCH.json',p)
root=B/'runtime/parameter_task_label_audit66_20261028_v1';out=B/'runs/parameter_task_label_audit66_20261028_v1';p=out/'PLAN66.json';old=read(B/'runs/parameter_task_label_audit65_20261028_v1/PLAN65.json')
plan=dict(time=time.time(),parent_run=str(run),parent_launch_sha256=sha(run/'LAUNCH.json'),jobs=jobs,monitor=monitor,sources={n:sha(root/n) for n in ['audit_labels.py','wait66.py']},wait_seconds=7200,new_physics=0,optimizer_updates=0,automatic_training=False,regression_review=old['regression_review'],registered_during66=True,registered_before_complete66=True);assert ref(Path(plan['regression_review']['path']))==plan['regression_review'];write(p,plan)
r=subprocess.run([py,str(root/'audit_labels.py'),'--before','65','--after','66','--output',str(out/'COMPLETE65_66.json')],capture_output=True,text=True,env=env);assert r.returncode!=0 and not(out/'COMPLETE65_66.json').exists();write(out/'INCOMPLETE_REJECTION.json',dict(time=time.time(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,no_output=True))
launch(root/'wait66.py',[],out/'wait66.log',out/'LAUNCH66.json',p)
