"""User-authorized synthetic GPU occupancy, excluded from scientific metrics.
STOP file ends supervisor and workers. No training checkpoint access.
"""
from pathlib import Path
import os,sys,time,json,subprocess,signal
ROOT=Path(__file__).resolve().parent

def write(p,d):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(d)+'\n');t.replace(p)

def worker(gpu):
 os.sched_setaffinity(0,{52,53,54})
 import torch
 torch.set_num_threads(1);torch.cuda.set_device(gpu)
 torch.manual_seed(20261028+gpu)
 a=torch.randn((1024,1024),device=f'cuda:{gpu}',dtype=torch.float16)*.02
 b=torch.randn_like(a)*.02;c=torch.empty_like(a)
 # One static graph reduces CPU launch overhead; output checked periodically.
 stream=torch.cuda.Stream(device=gpu,priority=0)
 with torch.cuda.stream(stream):
  for _ in range(5):torch.mm(a,b,out=c)
 stream.synchronize()
 graph=torch.cuda.CUDAGraph()
 with torch.cuda.graph(graph,stream=stream):
  for _ in range(100):torch.mm(a,b,out=c)
 done=torch.cuda.Event(blocking=True)
 cycles=0;last=time.monotonic()
 while not (ROOT/'STOP').exists():
  cfg=json.loads((ROOT/'CONTROL.json').read_text());duty=cfg['duty'][str(gpu)]
  if duty<=0:time.sleep(.2);continue
  start=time.monotonic();busy=.02*duty
  while time.monotonic()-start<busy:
   graph.replay();done.record();done.synchronize();cycles+=1
  if time.monotonic()-last>=10:
   assert bool(torch.isfinite(c).all()),'nonfinite synthetic output'
   write(ROOT/f'worker{gpu}.json',dict(pid=os.getpid(),gpu=gpu,graphs=cycles,time=time.time(),synthetic=True,duty=duty));last=time.monotonic()
  time.sleep(max(0,.02-(time.monotonic()-start)))

def supervisor():
 import fcntl
 lock=(ROOT/'LOCK').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 os.sched_setaffinity(0,{52,53,54});duties={str(i):.75 for i in range(4)};write(ROOT/'CONTROL.json',dict(duty=duties))
 children={}
 def spawn(i):
  p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(i)],stdout=(ROOT/f'worker{i}.log').open('a'),stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
  children[i]=p
 for i in range(4):spawn(i)
 write(ROOT/'LAUNCH.json',dict(pid=os.getpid(),workers={str(i):p.pid for i,p in children.items()},time=time.time(),synthetic=True,scientific_updates=0,target_floor=50,control_target=70,stop_file=str(ROOT/'STOP')))
 try:
  with (ROOT/'samples.jsonl').open('a',buffering=1) as log:
   while not (ROOT/'STOP').exists():
    for i,p in list(children.items()):
     if p.poll() is not None:
      raise RuntimeError(f'Guard worker{i} exited {p.returncode}; inspect worker log')
    raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True)
    rows=[]
    for line in raw.strip().splitlines():
     g,u,mem=[int(x.strip()) for x in line.split(',')];key=str(g);rows.append(dict(gpu=g,utilization=u,memory_mib=mem,duty=duties[key]))
     if u<65:duties[key]=min(.9,duties[key]+.1)
     elif u>92:duties[key]=max(.70,duties[key]-.1)
    log.write(json.dumps(dict(time=time.time(),gpus=rows,synthetic_guard_included=True))+'\n');write(ROOT/'CONTROL.json',dict(duty=duties,time=time.time()))
    time.sleep(5)
 finally:
  for p in children.values():
   if p.poll() is None:p.terminate()
  for p in children.values():p.wait()

if __name__=='__main__':
 try:
  if len(sys.argv)>1:worker(int(sys.argv[2]))
  else:supervisor()
 except BaseException as e:
  if len(sys.argv)==1:write(ROOT/'FAILURE.json',dict(time=time.time(),error=repr(e)))
  raise
