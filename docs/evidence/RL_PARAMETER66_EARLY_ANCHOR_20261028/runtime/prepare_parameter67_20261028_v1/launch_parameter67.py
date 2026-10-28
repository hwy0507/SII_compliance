"""Dispatch one explicitly reviewed stage67; preserve all learned state."""
from pathlib import Path
import json,hashlib,subprocess,os,shutil,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');root=Path(__file__).parent;out=B/'runs/parameter_capacity_pool30_cycle67_20261026_v1'
def verified_copy(src, dst):
 src,dst=Path(src),Path(dst)
 data=src.read_bytes()
 assert data==src.read_bytes(), f'Source changed while copying: {src}'
 with dst.open('xb') as stream:
  stream.write(data);stream.flush();os.fsync(stream.fileno())
 assert dst.read_bytes()==data, f'Copied bytes differ: {dst}'
 shutil.copystat(src,dst)
 return str(dst)

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert not (out/'LAUNCH.json').exists()
for name,h in read(root/'LAUNCH_SOURCE_REVIEW.json')['files'].items():assert sha(root/name)==h
decision=read(root/'DECISION67.json');assert decision['passed'] and decision['plot_inspected'] and not decision['convergence_claim']
assert decision['parent_cycle']==66 and decision['new_cycle']==67
assert {'parent_review','health','loss','paired_gate','check_only','reward_window56_58'} <= set(decision['evidence'])
for x in decision['evidence'].values():assert sha(Path(x['path']))==x['sha256']
assert read(root/'parameter_FINISHED.json')['prepared']
assert read(out/'CHECK_ONLY_COMPLETE.json')['passed'];assert all(v==0 for v in read(out/'CHECK_ONLY_EXIT_CODES.json').values())
write(out/'PRELAUNCH_SCIENTIFIC_REVIEW.json',dict(decision,time=time.time(),parent_cycle=66,new_cycle=67,new_cycles=1,automatic_followup=False))
verified_copy(root/'startup67.py',out/'startup_review.py')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');jobs=read(out/'COMMANDS.json')['jobs']
for j in jobs:
 p=subprocess.Popen(j['command'],stdout=(out/(j['controller']+'_driver.log')).open('x'),stderr=subprocess.STDOUT,env=env,start_new_session=True)
 j.update(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().split(') ')[1].split()[19],time=time.time())
write(out/'LAUNCH.json',dict(time=time.time(),jobs=jobs,new_cycles=1,automatic_followup=False))
monitor=out/'archive_review.py';verified_copy(B/'runtime/resume_sources_20261028_v1/archive_review_next_20261028.py',monitor)
p=subprocess.Popen([str(B/'env/bin/python'),str(monitor),'parameter_capacity_pool30','67'],stdout=(out/'archive_review.log').open('x'),stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(out/'MONITOR_LAUNCH.json',dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().split(') ')[1].split()[19],time=time.time(),script_sha256=sha(monitor)));print(json.dumps(dict(jobs=jobs,monitor_pid=p.pid),indent=2))

p=subprocess.Popen([str(B/'env/bin/python'),str(out/'startup_review.py')],stdout=(out/'startup_review.log').open('x'),stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(out/'STARTUP_LAUNCH.json',dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().split(') ')[1].split()[19],time=time.time(),script_sha256=sha(out/'startup_review.py')))
