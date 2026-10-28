from pathlib import Path
import json,subprocess,os,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=B/'runs/parameter55_frozen_full30_20261028_v1/validation53'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1,2,3',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
procs=[];records=[]
for job in json.loads((OUT/'COMMANDS.json').read_text())['jobs']:
 p=subprocess.Popen(job['command'],stdout=(OUT/job['controller']/'check_only.log').open('x'),stderr=subprocess.STDOUT,env=env)
 procs.append((job['controller'],p));records.append(dict(job,pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().split(') ')[1].split()[19]))
write(OUT/'CHILDREN.json',dict(time=time.time(),jobs=records))
codes={m:p.wait() for m,p in procs};write(OUT/'EXIT_CODES.json',codes)
assert all(v==0 for v in codes.values()),codes
reviews={m:json.loads((OUT/m/'CHECK_ONLY_REVIEW.json').read_text()) for m,_ in procs}
assert all(v['passed'] and v['full_replay_restored_exact'] and v['validated_parent_cycle']==53 for v in reviews.values())
write(OUT/'REVIEW.json',dict(time=time.time(),passed=True,methods=reviews,new_physics=0,optimizer_updates=0,actual55_restore=False))
