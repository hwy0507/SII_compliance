"""Single foreground five-hour campaign. No scheduler, cron or heartbeat."""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
def epoch(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def main():
 p=argparse.ArgumentParser();p.add_argument('--role',choices=['metric','office_task','classical'],required=True);a=p.parse_args();root=ROOT/'campaign01';root.mkdir(exist_ok=True)
 if a.role=='classical':
  command=[sys.executable,str(HERE/'classical.py'),'--output',str(root/'classical'),'--deadline',str(epoch('2026-10-02T11:30:00Z'))]
  return subprocess.call(command)
 for seed in [74001,74002]:
  if time.time()>=epoch('2026-10-02T11:40:00Z'):break
  out=root/f'{a.role}_seed{seed}';command=[sys.executable,str(HERE/'train.py'),'--output',str(out),'--reward',a.role,'--seed',str(seed),'--steps','60000','--deadline',str(epoch('2026-10-02T11:40:00Z'))]
  with (root/f'{a.role}_seed{seed}.log').open('w') as log:rc=subprocess.call(command,stdout=log,stderr=subprocess.STDOUT)
  print(json.dumps(dict(seed=seed,reward=a.role,returncode=rc)),flush=True)
  if rc:return rc
 return 0
if __name__=='__main__':sys.exit(main())
