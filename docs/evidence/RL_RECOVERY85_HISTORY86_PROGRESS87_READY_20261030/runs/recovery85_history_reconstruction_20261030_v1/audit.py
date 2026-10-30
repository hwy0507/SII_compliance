from pathlib import Path
import json,time,os,hashlib,collections,traceback,gc
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import numpy as np
import torch
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def stat(p):
 s=p.stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
plan=read(D/'PLAN.json');os.sched_setaffinity(0,{plan['cpu']});torch.set_num_threads(plan['torch_threads']);start=time.monotonic()
def budget():assert time.monotonic()-start<plan['budget_seconds'],'Registered history reconstruction budget expired'
try:
 for x in plan['inputs']:assert sha(Path(x['path']))==x['sha256']
 inv=read(Path(plan['inventory']));assert inv['passed'];full=read(B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1/REVIEW.json');methods={}
 with (D/'PROGRESS.jsonl').open('x') as log:
  for m in plan['methods']:
   budget();mi=inv['methods'][m];cp=B/f'runs/parameter_partial75_recovery_cycle85_archive_20261029_v1/{m}/cycle_00085.pt';before_cp=ref(cp);assert before_cp['sha256']==full['methods'][m]['checkpoint_sha256'];x=torch.load(cp,map_location='cpu',weights_only=False);arr=x['replay']['arrays'];n=x['replay']['size'];assert n==x['steps']==mi['retained_transition_rows'];scale=x['learner']['observation_scale'];assert scale.shape==(48,)
   dest=D/(m+'_causal_history.npy');assert not dest.exists();side=np.lib.format.open_memmap(dest,mode='w+',dtype=np.float64,shape=(n,2));side[:]=np.nan;seen=np.zeros(n,dtype=bool);episodes=[];next_context_checked=0;next_context_missing=0;prebad_total=0;nextbad_total=0;terminal_total=0
   for ri,root in enumerate(mi['roots']):
    budget();train=Path(root['train']);p=train/'transitions.jsonl';st=stat(p);h=hashlib.sha256();groups=collections.defaultdict(list)
    with p.open('rb') as f:
     for line in f:
      h.update(line);t=json.loads(line);groups[(t['cycle'],t['condition'])].append(t)
    assert stat(p)==st and h.hexdigest()==root['transitions']['sha256'];lo=root['selected_first_step'];hi=root['selected_last_step'];kept=0
    for (cycle,condition),all_ts in groups.items():
     ts=[t for t in all_ts if lo<=t['step']<=hi]
     if not ts:continue
     budget();k=len(ts);assert k<=1375;indices=np.array([t['step']-1 for t in ts],dtype=np.int64);assert not seen[indices].any();done=np.array([bool(t['done']) for t in ts]);assert done.sum()<=1 and (not done.any() or done[-1])
     folder=train/f'cycle_{cycle:05d}'/condition;jp=folder/'actor_intervals.jsonl';jstat=stat(jp);jh=hashlib.sha256();journal=[]
     with jp.open('rb') as f:
      for line in f:jh.update(line);journal.append(json.loads(line))
     assert stat(jp)==jstat;need=k if done[-1] else k+1;assert len(journal)>=need,(m,str(folder),len(journal),need);assert journal[0]['interval'] is None
     # Read every journal entry but derive replay-aligned histories only for retained transitions.
     all_peaks=np.array([0. if j['interval'] is None else j['interval']['external_penetration_peak_m'] for j in journal],dtype=np.float64);assert np.isfinite(all_peaks).all() and np.all(all_peaks>=0) and np.all(np.diff(all_peaks)>=0);assert all(j['interval'] is not None for j in journal[1:])
     raw=np.asarray([j['observation'] for j in journal],np.float32);assert raw.shape==(len(journal),48) and np.isfinite(raw).all();obs=raw[:k]/scale
     contexts=np.array([t['context'] for t in ts],dtype=np.float32);assert np.isfinite(contexts).all();clock=np.array([(1375-i)/1375 for i in range(k)],np.float32)
     np.testing.assert_array_equal(arr['observations'][indices,:48],obs);np.testing.assert_array_equal(arr['observations'][indices,48],contexts);np.testing.assert_array_equal(arr['observations'][indices,49],clock)
     mixed=np.asarray([j['action'] for j in journal[:k]],np.float32);np.testing.assert_array_equal(arr['actions'][indices]*contexts[:,None],mixed)
     np.testing.assert_array_equal(arr['rewards'][indices,0],np.array([t['reward'] for t in ts],np.float32));np.testing.assert_array_equal(arr['dones'][indices,0],done.astype(np.float32))
     nextobs=np.empty_like(obs);nctx=np.empty(k,dtype=np.float32);ctx_known=np.zeros(k,dtype=bool);pre=all_peaks[:k];npeak=np.empty(k,dtype=np.float64);termref=None
     for i,t in enumerate(ts):
      if t['done']:
       terminal=read(folder/'TERMINAL.json');termref=ref(folder/'TERMINAL.json');nextobs[i]=obs[i];npeak[i]=terminal['interval']['external_penetration_peak_m'];nctx[i]=contexts[i];ctx_known[i]=True
      else:
       nextobs[i]=raw[i+1]/scale;npeak[i]=all_peaks[i+1]
       if i+1<len(all_ts):nctx[i]=np.float32(all_ts[i+1]['context']);ctx_known[i]=True
     assert np.isfinite(npeak).all() and np.all(npeak>=pre)
     np.testing.assert_array_equal(arr['next_observations'][indices,:48],nextobs);np.testing.assert_array_equal(arr['next_observations'][indices,49],np.array([(1374-i)/1375 for i in range(k)],np.float32));np.testing.assert_array_equal(arr['next_observations'][indices[ctx_known],48],nctx[ctx_known])
     side[indices,0]=pre;side[indices,1]=npeak;seen[indices]=True;kept+=k;nb=int((pre>.0002).sum());nn=int((npeak>.0002).sum());prebad_total+=nb;nextbad_total+=nn;terminal_total+=int(done.sum());next_context_checked+=int(ctx_known.sum());next_context_missing+=int((~ctx_known).sum())
     bad=np.flatnonzero(pre>.0002);episodes.append(dict(train=str(train),cycle=cycle,condition=condition,retained_transitions=k,first_global_step=int(indices[0]+1),last_global_step=int(indices[-1]+1),terminal_retained=bool(done[-1]),journal=dict(path=str(jp),bytes=jstat[2],sha256=jh.hexdigest(),rows=len(journal)),terminal=termref,first_preaction_peak=float(pre[0]),last_preaction_peak=float(pre[-1]),last_next_peak=float(npeak[-1]),preaction_violation_rows=nb,next_violation_rows=nn,first_bad_preaction_index=int(bad[0]) if len(bad) else None,unknown_next_context_rows=int((~ctx_known).sum()),replay_current50_action_reward_done_next48_clock_exact=True))
    assert kept==root['retained_transitions'];side.flush();log.write(json.dumps(dict(time=time.time(),method=m,root_index=ri+1,roots=len(mi['roots']),mapped_rows=int(seen.sum()),expected=n))+'\n');log.flush()
   assert seen.all() and np.isfinite(side).all() and np.all(side[:,1]>=side[:,0]);assert n==next_context_checked+next_context_missing;assert int((side[:,0]>.0002).sum())==prebad_total and int((side[:,1]>.0002).sum())==nextbad_total
   epout=D/(m+'_episodes.jsonl')
   with epout.open('x') as f:
    for e in episodes:f.write(json.dumps(e)+'\n')
   side.flush();del side;assert ref(cp)==before_cp
   methods[m]=dict(retained_rows=n,episode_cohorts=len(episodes),retained_terminal_rows=terminal_total,retained_partial_episode_cohorts=sum(not e['terminal_retained'] for e in episodes),all_rows_written_once=True,current50_and_mixed_actions_rewards_dones_and_next48_clock_exact=True,next_context_checked_rows=next_context_checked,next_context_unavailable_rows=next_context_missing,preaction_violation_rows=prebad_total,next_violation_rows=nextbad_total,episodes_with_preaction_violation=sum(e['preaction_violation_rows']>0 for e in episodes),sidecar=ref(dest),episode_review=ref(epout),checkpoint=before_cp,checkpoint_unchanged=True,no_replay_writes=True)
   put(D/(m+'_REVIEW.json'),dict(passed=True,time=time.time(),method=m,**methods[m]));print(m,methods[m],flush=True);del x,arr,seen,groups,journal,all_ts,ts;gc.collect()
 assert sum(x['retained_rows'] for x in methods.values())==plan['expected_total_retained_transitions']
 for x in plan['inputs']:assert sha(Path(x['path']))==x['sha256']
 put(D/'REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,methods=methods,plan=ref(D/'PLAN.json'),new_physics=0,new_network_forward=0,optimizer_updates=0,replay_writes=0,scientific_configuration_changed=False,limitation='Causal cumulative history derived from original journals and aligned against every retained complete85 replay row. Current50/action-mix/reward/done/next48-clock checked exact; next-context availability counted explicitly. Not independent physical-substep reconstruction, historical minibatch inclusion, or a scientific amendment.'))
 put(D/'FINISHED.json',dict(time=time.time(),passed=True,completed=True,automatic_training=False))
except BaseException as e:
 put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
