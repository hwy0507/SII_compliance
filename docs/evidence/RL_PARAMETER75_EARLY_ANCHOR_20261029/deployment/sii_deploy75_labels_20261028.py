from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rt=B/'runtime/parameter_task_label_audit75_20261028_v1';out=B/'runs/parameter_task_label_audit75_20261028_v1';root=B/'runs/parameter_capacity_pool30_cycle75_20261026_v1'
cmd=[str(B/'env/bin/python'),str(rt/'audit_labels.py'),'--before','74','--after','75','--output',str(out/'COMPLETE74_75.json')];r=subprocess.run(cmd,capture_output=True,text=True)
assert r.returncode!=0 and 'Incomplete cycle 75' in r.stderr and not (out/'COMPLETE74_75.json').exists()
(out/'INCOMPLETE75_REJECTION.json').write_text(json.dumps(dict(passed=True,time=time.time(),command=cmd,returncode=r.returncode,stderr=r.stderr,no_output=True),indent=2)+'\n')
p=read(B/'runs/parameter_task_label_audit74_20261028_v1/PLAN74.json');p.update(time=time.time(),parent_run=str(root),parent_launch_sha256=sha(root/'LAUNCH.json'),jobs=read(root/'LAUNCH.json')['jobs'],monitor=read(root/'MONITOR_LAUNCH.json'),sources={n:sha(rt/n) for n in ['audit_labels.py','wait75.py','review_labels75.py']})
for key in ['registered_during74','registered_before_complete74','independent_saved_review_requires_full74_loss']:p[key.replace('74','75')]=p.pop(key)
assert sha(Path(p['regression_review']['path']))==p['regression_review']['sha256']
for j in p['jobs']+[p['monitor']]:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
assert not (root/'ARCHIVE_REVIEW_FINISHED.json').exists()
(out/'PLAN75.json').write_text(json.dumps(p,indent=2)+'\n')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (out/'driver.log').open('x') as log:child=subprocess.Popen([str(B/'env/bin/python'),str(rt/'wait75.py')],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
j=dict(pid=child.pid,proc_start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(out/'PLAN75.json'))
(out/'LAUNCH75.json').write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j,indent=2))
