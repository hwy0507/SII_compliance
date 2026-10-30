"""Bind actual frozen88 launch and collect all90 saved comparisons/audits once."""
from pathlib import Path
import json,hashlib,os,sys,time,subprocess,traceback
D=Path(__file__).resolve().parent;B=D.parents[1]
O=B/'runs/parameter88_history_frozen_full30_20261030_v1';A=B/'runs/parameter88_history_frozen_saved_audit_20261030_v1';C=O/'comparison82_88'
os.sched_setaffinity(0,{10})
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def live(j):
    p=Path(f"/proc/{j['pid']}/stat")
    if not p.exists():return False
    f=p.read_text().rsplit(')',1)[1].split()
    return f[0]!='Z' and f[19]==j['start']
try:
    for n,h in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
    pre=read(D/'PRE_REGISTRATION.json');r=pre['current_preregistration'];assert sha(r['path'])==r['sha256']
    r=pre['prior_review'];assert sha(r['path'])==r['sha256']
    evaluation=read(O/'PLAN.json');launch=read(O/'REVIEW_LAUNCH.json')
    assert evaluation['parent_cycle']==88 and evaluation['case_ids']==pre['case_ids']
    assert evaluation['preregistration']['sha256']==pre['current_preregistration']['sha256']
    assert sha(A/'audit.py')==read(A/'PLAN.json')['source']['sha256']
    assert not C.exists();C.mkdir()
    put(C/'PLAN.json',dict(time=time.time(),source=ref(D/'compare82_88.py'),prior_review=pre['prior_review'],evaluation_plan=ref(O/'PLAN.json'),all90_paired=True,physics_steps=0,optimizer_updates=0))
    put(D/'LAUNCH_BINDING.json',dict(time=time.time(),original_reviewer=launch,evaluation_plan=ref(O/'PLAN.json'),deadline=launch['time']+21600,physics_steps=0,optimizer_updates=0))
    deadline=launch['time']+21600
    while True:
        assert not (O/'REVIEW_FAILURE.json').exists()
        assert all(not (O/m/'FAILURE.json').exists() for m in evaluation['controllers'])
        if (O/'REVIEW.json').exists() and not live(launch):break
        assert live(launch),'Original collector exited before completion'
        assert time.time()<deadline,'Original frozen review deadline expired; no automatic extension'
        time.sleep(5)
    assert read(O/'REVIEW.json')['passed']
    for source,logfile in [(D/'compare82_88.py',C/'driver.log'),(A/'audit.py',A/'driver.log')]:
        with logfile.open('x') as log:
            subprocess.run([str(B/'env/bin/python'),'-u',str(source)],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=3600)
    assert read(C/'REVIEW.json')['passed'] and read(C/'SAVED_REVIEW.json')['passed']
    assert read(A/'REVIEW.json')['passed'] and read(A/'SAVED_REVIEW.json')['passed']
    put(A/'FINISHED.json',dict(time=time.time(),passed=True,new_physics=0,new_optimizer_updates=0))
    put(D/'FINISHED.json',dict(time=time.time(),passed=True,comparison=ref(C/'REVIEW.json'),raw_audit=ref(A/'REVIEW.json'),new_physics=0,new_optimizer_updates=0))
except BaseException as exc:
    put(D/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(exc),traceback=traceback.format_exc()));raise
