from pathlib import Path
import json,hashlib,os,subprocess,sys,time
os.sched_setaffinity(0,{53})
OUT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def live(j):
    p=Path(f'/proc/{j["pid"]}/stat')
    if not p.exists():return False
    s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
try:
    plan=read(OUT/'PLAN.json');root=Path(plan['parent_run']);review=Path(plan['parent_review'])
    for n,h in plan['sources'].items():assert sha(OUT/n)==h
    assert sha(root/'LAUNCH.json')==plan['parent_launch_sha256']
    deadline=time.monotonic()+7200
    while True:
        assert not (root/'ARCHIVE_REVIEW_FAILURE.json').exists()
        for j in plan['learners']:assert not (root/j['controller']/'train/FAILURE.json').exists()
        if (root/'ARCHIVE_REVIEW_FINISHED.json').exists():
            assert read(root/'ARCHIVE_REVIEW_FINISHED.json')['completed'] and read(review/'FINISHED.json')['completed'] and read(review/'REVIEW.json')['passed']
            if not any(live(j) for j in plan['learners']):break
        else:assert live(plan['monitor']),'Original monitor disappeared without completion'
        assert time.monotonic()<deadline,'Fixed7200s observation expired; no restart'
        time.sleep(5)
    binding=dict(checkpoint=ref(Path(plan['final_checkpoint'])),health=ref(review/'health/DIAGNOSIS.json'),review=ref(review/'REVIEW.json'))
    (OUT/'FINAL_BINDING.json').write_text(json.dumps(binding,indent=2)+'\n')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    for n in ['compare.py','review_values.py']:subprocess.run([sys.executable,str(OUT/n)],check=True,env=env)
    (OUT/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time()))+'\n')
except BaseException as error:
    (OUT/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error)))+'\n');raise
