from pathlib import Path
import os,sys,time,json,hashlib,socket,gc,traceback,subprocess
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
D=Path(__file__).resolve().parent;B=D.parents[1];rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 import numpy as np
 import torch
 import mujoco
 p=rd(D/'RECOVERY_PLAN.json');start=time.monotonic();os.sched_setaffinity(0,{10});torch.set_num_threads(1);assert sha(p['direct_checkpoint'])==p['direct_sha256']
 for source,h in p['dependencies'].items():assert sha(source)==h,source
 sys.path[:0]=[p['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation93_terminal_followup_20261031_v1')]
 from violation_consumers import restore_learner
 from compare93 import validate_complete93
 from frozen_helpers import capture_rng
 from validate_published_finite_check_20261025 import digest
 results={}
 for m,e in p['methods'].items():
  assert time.monotonic()-start<p['budget_seconds'];cp=Path(e['checkpoint']);assert sha(cp)==e['checkpoint_sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);reg=rd(e['registration']);validate_complete93(ck,reg);a=ck['replay']['arrays'];before=digest(ck['replay']);l=restore_learner(ck['learner'],reg['violation_critic_amendment']['binding'],B/'runtime/source_train17_clock',e['device'],ck['seed']);initial=digest(l.state_dict());assert initial==digest(ck['learner']);rng=digest(capture_rng(l));ti=np.flatnonzero(a['dones'][:,0]==1)
  with np.load(e['terminal_values']['path']) as z:np.testing.assert_array_equal(ti,z['indices']);expected=z['initial_prediction'].copy()
  def pred(idx):
   ob=torch.as_tensor(a['observations'][idx],device=l.device);ac=torch.as_tensor(a['actions'][idx],device=l.device)
   with torch.no_grad():return torch.stack([q(ob,ac).reshape(-1) for q in l.learner.agent.ensemble],1).cpu().numpy()
  q=pred(ti);np.testing.assert_array_equal(q,expected);item=rd(e['raw_manifest']['path'])['files'][0];assert sha(item['path'])==item['sha256']
  with np.load(item['path']) as z:bidx=z['indices'].astype(np.int64);bq=z['q'].copy()
  nq=pred(bidx);np.testing.assert_array_equal(nq,bq);assert digest(l.state_dict())==initial and digest(capture_rng(l))==rng and digest(ck['replay'])==before and sha(cp)==e['checkpoint_sha256']
  results[m]=dict(steps=ck['steps'],terminal_rows=len(ti),all_terminal_predictions_exact=True,first_native65536_predictions_exact=True,full_learner_Adam_replay_RNG_unchanged=True,checkpoint_sha256=e['checkpoint_sha256'],device=e['device']);(D/'RESTORE_PROGRESS.json').write_text(json.dumps(dict(time=time.time(),method=m,passed=True))+'\n');del l,ck,a;gc.collect();torch.cuda.empty_cache()
 env=dict(host=socket.gethostname(),python=sys.version,numpy=np.__version__,torch=torch.__version__,cuda=torch.version.cuda,mujoco=mujoco.__version__,gpu=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,uuid,driver_version','--format=csv,noheader']).decode().strip())
 put(D/'COLD_RESTORE_REVIEW.json',dict(passed=True,time=time.time(),methods=results,direct33_hash_verified=p['direct_sha256'],dependencies_checked=len(p['dependencies']),environment=env,elapsed_s=time.monotonic()-start,optimizer_updates=0,new_physics=0,scope=p['scope']))
 print(json.dumps(dict(passed=True,methods=results,environment=env)),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException:put(D/'COLD_RESTORE_FAILURE.json',dict(time=time.time(),traceback=traceback.format_exc()));raise
