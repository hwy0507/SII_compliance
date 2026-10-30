from pathlib import Path
import hashlib,json,os,subprocess,time,traceback
D=Path(__file__).resolve().parent; B=D.parents[1]
os.sched_setaffinity(0,{11})
read=lambda p:json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
try:
    plan=read(D/'PLAN.json'); launch=read(D/'LAUNCH.json')
    assert sha(D/'PLAN.json')==launch['plan_sha256'] and sha(__file__)==launch['waiter_sha256']
    run=B/'runs/parameter_history_cycle88_20261030_v2'
    deadline=launch['time']+7200
    while not (run/'ARCHIVE_REVIEW_FINISHED.json').exists():
        assert time.time()<deadline,'Finite waiting deadline exceeded'
        assert not (run/'ARCHIVE_REVIEW_FAILURE.json').exists(),'Complete88 review failed'
        for m in plan['methods']:
            assert not (run/m/'train/FAILURE.json').exists() and not (run/m/'DRIVER_FAILURE.json').exists()
        pid=launch['archive_monitor']['pid']; fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        assert fields[0]!='Z' and fields[19]==launch['archive_monitor']['start_ticks'],'Archive monitor identity lost'
        time.sleep(5)
    assert sha(D/'compare.py')==plan['script_sha256']
    with (D/'compare.log').open('x') as log:
        subprocess.run([str(B/'env/bin/python'),'-u',str(D/'compare.py')],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=plan['budget_seconds']+60)
    assert read(D/'REVIEW.json')['passed']
    put(D/'FINISHED.json',dict(time=time.time(),passed=True,plot_still_requires_actual_inspection=True,training_authorized=False))
except BaseException as e:
    put(D/('WAIT_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
