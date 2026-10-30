from pathlib import Path
import os,json,time,hashlib,collections,gc,traceback
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import torch
D=Path(__file__).parent;B=D.parents[1];read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def array_digest(a):
 h=hashlib.sha256(str((a.shape,a.dtype)).encode());h.update(memoryview(a).cast('B'));return h.hexdigest()
plan=read(D/'PLAN.json');os.sched_setaffinity(0,{plan['cpu']});torch.set_num_threads(1);start=time.monotonic()
def budget():assert time.monotonic()-start<plan['budget_seconds']
try:
 for x in plan['inputs']:assert sha(x['path'])==x['sha256']
 old=read(B/'runs/recovery85_history_reconstruction_20261030_v1/REVIEW.json');methods={}
 for m in plan['methods']:
  budget();a=old['methods'][m];cp85=Path(a['checkpoint']['path']);assert sha(cp85)==a['checkpoint']['sha256'];base=torch.load(cp85,map_location='cpu',weights_only=False);n0=base['steps'];assert n0==a['retained_rows'];prefix={k:array_digest(v) for k,v in base['replay']['arrays'].items()};del base;gc.collect()
  cp=B/f'runs/parameter_partial75_recovery_cycle87_archive_20261029_v1/{m}/cycle_00087.pt';cph=sha(cp);full=read(B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1/REVIEW.json');assert cph==full['methods'][m]['checkpoint_sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);arr=ck['replay']['arrays'];n=ck['steps'];assert n==n0+82500==ck['replay']['size'] and ck['cycle']==87
  assert set(arr)==set(prefix)
  for k,v in arr.items():assert array_digest(v[:n0])==prefix[k],k
  oldpath=Path(a['sidecar']['path']);assert sha(oldpath)==a['sidecar']['sha256'];oldside=np.load(oldpath,mmap_mode='r');assert oldside.shape==(n0,2)
  sidepath=D/(m+'_causal_history.npy');side=np.lib.format.open_memmap(sidepath,mode='w+',dtype=np.float64,shape=(n,2));side[:n0]=oldside;side[n0:]=np.nan;seen=np.zeros(82500,bool);episodes=[];inputs=[];scale=ck['learner']['observation_scale']
  for cycle in [86,87]:
   train=B/f'runs/parameter_partial75_recovery_cycle{cycle}_20261029_v1/{m}/train';tp=train/'transitions.jsonl';inputs.append(ref(tp));groups=collections.defaultdict(list)
   with tp.open() as f:
    for line in f:
     t=json.loads(line);assert t['cycle']==cycle;groups[t['condition']].append(t)
   assert len(groups)==30 and sum(map(len,groups.values()))==41250
   for condition,ts in groups.items():
    budget();assert len(ts)==1375;idx=np.array([t['step']-1 for t in ts]);local=idx-n0;assert np.all((local>=0)&(local<82500)) and not seen[local].any();assert [bool(t['done']) for t in ts]==[False]*1374+[True]
    folder=train/f'cycle_{cycle:05d}'/condition;jp=folder/'actor_intervals.jsonl';term=folder/'TERMINAL.json';inputs +=[ref(jp),ref(term)]
    js=[json.loads(l) for l in jp.read_text().splitlines()];end=read(term);assert len(js)==1375 and js[0]['interval'] is None
    pre=np.array([0. if j['interval'] is None else j['interval']['external_penetration_peak_m'] for j in js]);nxt=np.r_[pre[1:],end['interval']['external_penetration_peak_m']];assert np.isfinite(pre).all() and np.isfinite(nxt).all() and np.all(pre>=0) and np.all(nxt>=pre)
    raw=np.asarray([j['observation'] for j in js],dtype=np.float32);obs=raw/scale;ctx=np.array([t['context'] for t in ts],np.float32);clock=np.array([(1375-i)/1375 for i in range(1375)],np.float32)
    np.testing.assert_array_equal(arr['observations'][idx],np.column_stack([obs,ctx,clock]))
    np.testing.assert_array_equal(arr['actions'][idx]*ctx[:,None],np.asarray([j['action'] for j in js],np.float32))
    np.testing.assert_array_equal(arr['rewards'][idx,0],np.array([t['reward'] for t in ts],np.float32));np.testing.assert_array_equal(arr['dones'][idx,0],np.array([t['done'] for t in ts],np.float32))
    nextobs=np.vstack([obs[1:],obs[-1:]]);nextctx=np.r_[ctx[1:],ctx[-1]];nextclock=np.array([(1374-i)/1375 for i in range(1375)],np.float32)
    np.testing.assert_array_equal(arr['next_observations'][idx],np.column_stack([nextobs,nextctx,nextclock]))
    side[idx,0]=pre;side[idx,1]=nxt;seen[local]=True
    episodes.append(dict(cycle=cycle,condition=condition,journal=str(jp),terminal=str(term),transition_log=str(tp),first_global_step=int(idx[0]+1),last_global_step=int(idx[-1]+1),actions=1375,preaction_violation_rows=int((pre>.0002).sum()),final_pre_peak=float(pre[-1]),final_next_peak=float(nxt[-1]),all_current50_next50_action_reward_done_exact=True))
  assert seen.all() and np.isfinite(side).all();np.testing.assert_array_equal(side[:n0],oldside);side.flush();del side
  for x in inputs:assert sha(x['path'])==x['sha256']
  assert sha(cp)==cph and sha(cp85)==a['checkpoint']['sha256'];rows=ref(sidepath)
  methods[m]=dict(prefix_rows=n0,added_rows=82500,total_rows=n,all_original_prefix_replay_fields_exact=True,prefix_array_digests=prefix,old_sidecar=a['sidecar'],sidecar=rows,episodes=episodes,inputs=inputs,checkpoint87=ref(cp),actual_terminal_rows=int(arr['dones'].sum()),original_partial_cohorts_preserved=True,all_appended_rows_written_once=True)
  put(D/(m+'_REVIEW.json'),dict(passed=True,**methods[m]));print('HISTORY87',m,n,flush=True);del ck,arr,oldside,seen,groups,js;gc.collect()
 put(D/'REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,methods=methods,plan_sha256=sha(D/'PLAN.json'),new_physics=0,new_network_forward=0,new_optimizer_updates=0,replay_writes=0,scope='Exact85 saved causal prefix plus complete86/87 appended journal histories; all original replay fields preserved. Not independent physical-substep reconstruction or proof of representation benefit.'))
except BaseException as e:put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
