from pathlib import Path
import os,json,time,hashlib,subprocess,sys
os.sched_setaffinity(0,{53});OUT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def live(j):
    try:f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split()
    except FileNotFoundError:return False
    return f[19]==j['proc_start_ticks'] and f[0]!='Z'
try:
    plan=read(OUT/'PLAN.json');follow=Path(plan['follow63']);assert sha(OUT/'audit.py')==plan['audit_sha256'];assert sha(OUT/'wait.py')==plan['wait_sha256'];deadline=time.monotonic()+7200
    while not (follow/'FINISHED.json').exists():
        assert not (follow/'WAIT_FAILURE.json').exists()
        assert live(plan['original_terminal_waiter']),'Original terminal audit vanished without FINISHED; do not restart science'
        assert time.monotonic()<deadline,'Observation expired; do not restart science'
        time.sleep(5)
    assert read(follow/'FINISHED.json')['completed']
    subprocess.run([sys.executable,str(OUT/'audit.py')],check=True)
    (OUT/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time()))+'\n')
except BaseException as e:
    (OUT/'WAIT_FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
