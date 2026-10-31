"""Audit and extract causal potential-only diagnostics from all retained full93 replay."""
from pathlib import Path
import os,sys,time,json,hashlib,collections,gc,traceback
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import numpy as np
import torch
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_potential_audit_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),bytes=Path(p).stat().st_size,sha256=sha(p))
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def stat(p):
 s=p.stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
def features(phi):
 assert phi.ndim==1 and len(phi)>0 and np.isfinite(phi).all() and np.all((phi>=0)&(phi<=1))
 delta=np.r_[0.,np.diff(phi)/.04];w=np.lib.stride_tricks.sliding_window_view(np.pad(phi,(13,0),mode='edge'),14)
 return np.column_stack([phi,delta,w.max(1)-w.min(1)])
def main(m):
 start=time.monotonic();plan=rd(O/'PLAN.json');e=plan['methods'][m];os.sched_setaffinity(0,{e['cpu']});torch.set_num_threads(1);assert sha(__file__)==rd(O/'SOURCE_LOCK.json')['extract.py'];cp=Path(e['checkpoint']['path']);assert sha(cp)==e['checkpoint']['sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False)
 sys.path[:0]=[str(B/'runtime/violation90_frozen_preparation_20261030_v1'),str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation93_terminal_followup_20261031_v1')]
 from compare93 import validate_complete93
 validate_complete93(ck,rd(e['registration']));n=e['rows'];assert ck['steps']==n;arr=ck['replay']['arrays'];scale=ck['learner']['observation_scale'];assert scale.shape==(48,)
 out=O/(m+'_causal_potential.npy');side=np.lib.format.open_memmap(out,mode='w+',dtype=np.float64,shape=(n,6));side[:]=np.nan;seen=np.zeros(n,bool);term_records=[];episode_records=[];inputs=[];potential_count=0;terminal_next_copies=0;raw_missing_rows=0;maxphi_error=0.;old=rd(e['old_episode_binding']['path']) if False else None
 oldmap={}
 assert sha(e['old_episode_binding']['path'])==e['old_episode_binding']['sha256']
 for l in Path(e['old_episode_binding']['path']).read_text().splitlines():
  row=json.loads(l);oldmap[row['journal']['path']]=row
 # Prefix invariance: changing future potential values cannot alter earlier features.
 probe=np.array([.1,.11,.12,.08,.13,.2,.19,.18,.15,.16,.14,.13,.11,.17,.2,.21]);f=features(probe);changed=probe.copy();changed[10:]=.9;np.testing.assert_array_equal(f[:10],features(changed)[:10]);np.testing.assert_array_equal(f[:8],features(probe[:8]))
 with (O/(m+'_progress.jsonl')).open('x') as log:
  for ri,root in enumerate(e['roots']):
   assert time.monotonic()-start<plan['budget_seconds_per_method'];train=Path(root['train']);tp=train/'transitions.jsonl';before=stat(tp);h=hashlib.sha256();groups=collections.defaultdict(list)
   with tp.open('rb') as fi:
    for line in fi:h.update(line);t=json.loads(line);groups[t['cycle'],t['condition']].append(t)
   assert stat(tp)==before and h.hexdigest()==root['transitions']['sha256'];inputs.append(root['transitions']);kept=0
   for (cycle,condition),ts_all in groups.items():
    ts=[t for t in ts_all if root['selected_first_step']<=t['step']<=root['selected_last_step']]
    if not ts:continue
    k=len(ts);assert ts==ts_all[:k];idx=np.array([t['step']-1 for t in ts],np.int64);assert not seen[idx].any();done=np.array([t['done'] for t in ts],bool);assert done.sum()<=1 and (not done.any() or done[-1]);folder=train/f'cycle_{cycle:05d}'/condition;jp=folder/'actor_intervals.jsonl';st=stat(jp);jh=hashlib.sha256();journal=[]
    with jp.open('rb') as fi:
     for line in fi:jh.update(line);journal.append(json.loads(line))
    assert stat(jp)==st;need=k if done[-1] else k+1;assert len(journal)>=need and journal[0]['interval'] is None
    if str(jp) in oldmap:assert jh.hexdigest()==oldmap[str(jp)]['journal']['sha256']
    phi=np.array([j['payload_potential'] for j in journal],np.float64);feat=features(phi);raw=np.array([j['observation'] for j in journal],np.float32);obs=raw[:k]/scale;ctx=np.array([t['context'] for t in ts],np.float32)
    np.testing.assert_array_equal(arr['observations'][idx,:48],obs);np.testing.assert_array_equal(arr['observations'][idx,48],ctx);np.testing.assert_array_equal(arr['observations'][idx,49],np.array([(1375-i)/1375 for i in range(k)],np.float32));np.testing.assert_array_equal(arr['actions'][idx]*ctx[:,None],np.asarray([j['action'] for j in journal[:k]],np.float32));np.testing.assert_array_equal(arr['rewards'][idx,0],np.array([t['reward'] for t in ts],np.float32));np.testing.assert_array_equal(arr['dones'][idx,0],done.astype(np.float32))
    reward_phi=np.array([t['reward_terms']['current_potential'] for t in ts]);np.testing.assert_array_equal(phi[:k],reward_phi);np.testing.assert_array_equal(phi[1:],np.array([j['interval']['payload_potential'] for j in journal[1:]]));potential_count+=k;side[idx,:3]=feat[:k]
    nextobs=np.empty_like(obs);nextfeat=np.empty((k,3));future=np.empty(k);terminal_ref=None
    for i,t in enumerate(ts):
     if t['done']:
      term=rd(folder/'TERMINAL.json');terminal_ref=ref(folder/'TERMINAL.json');future[i]=term['payload_potential'];nextobs[i]=obs[i];nextfeat[i]=feat[i];terminal_next_copies+=1
      term_records.append(dict(index=int(idx[i]),cycle=cycle,condition=condition,episode=str(folder),journal_row=i,features=feat[i].tolist(),task=bool(t['reward_terms']['task_success']),strict=bool(t['reward_terms']['strict_success'])))
     else:nextobs[i]=raw[i+1]/scale;nextfeat[i]=feat[i+1];future[i]=phi[i+1]
    np.testing.assert_array_equal(future,np.array([t['reward_terms']['next_potential'] for t in ts]));np.testing.assert_array_equal(arr['next_observations'][idx,:48],nextobs);np.testing.assert_array_equal(arr['next_observations'][idx,49],np.array([(1374-i)/1375 for i in range(k)],np.float32));side[idx,3:]=nextfeat;seen[idx]=True;kept+=k;missing=not (folder/'rollout.npz').exists();raw_missing_rows+=k if missing else 0
    episode_records.append(dict(episode=str(folder),cycle=cycle,condition=condition,retained_rows=k,terminal_retained=bool(done[-1]),missing_raw=missing,journal=dict(path=str(jp),bytes=st[2],sha256=jh.hexdigest(),rows=len(journal)),terminal=terminal_ref,first_index=int(idx[0]),last_index=int(idx[-1]),feature_min=feat[:k].min(0).tolist(),feature_max=feat[:k].max(0).tolist()))
   assert kept==root['retained_transitions'];side.flush();log.write(json.dumps(dict(time=time.time(),method=m,root=ri+1,roots=len(e['roots']),mapped_rows=int(seen.sum()),expected=n))+'\n');log.flush()
 assert seen.all() and np.isfinite(side).all() and potential_count==n;term_records.sort(key=lambda x:x['index']);idx=np.array([x['index'] for x in term_records],np.int64);np.testing.assert_array_equal(idx,np.flatnonzero(arr['dones'][:,0]==1));np.testing.assert_array_equal(side[idx,:3],np.array([x['features'] for x in term_records]));np.testing.assert_array_equal(side[idx,3:],side[idx,:3]);saved=O/(m+'_terminal_values.npz');np.savez_compressed(saved,indices=idx,observations=arr['observations'][idx],actions=arr['actions'][idx],rewards=arr['rewards'][idx,0],masks=arr['masks'][idx],features=side[idx,:3],cycles=np.array([x['cycle'] for x in term_records]),conditions=np.array([x['condition'] for x in term_records]))
 for name,rows in [('episodes',episode_records),('terminals',term_records)]:
  with (O/(m+'_'+name+'.jsonl')).open('x') as fi:
   for row in rows:fi.write(json.dumps(row)+'\n')
 side.flush();del side;assert sha(cp)==e['checkpoint']['sha256'];put(O/(m+'_INPUTS.json'),dict(files=inputs));put(O/(m+'_REVIEW.json'),dict(passed=True,time=time.time(),method=m,rows=n,episode_cohorts=len(episode_records),terminal_rows=len(idx),partial_cohorts=sum(not x['terminal_retained'] for x in episode_records),missing_raw_retained_rows=raw_missing_rows,current_potential_reward_binding_exact_rows=potential_count,terminal_next_copies=terminal_next_copies,all_rows_once=True,all_source_journals_hashed=True,old85_journal_hashes_match=True,prefix_invariance_passed=True,checkpoint_sha256=e['checkpoint']['sha256'],checkpoint_unchanged=True,sidecar=ref(out),terminal_values=ref(saved),episode_values=ref(O/(m+'_episodes.jsonl')),terminal_records=ref(O/(m+'_terminals.jsonl')),elapsed_s=time.monotonic()-start,new_physics=0,optimizer_updates=0,replay_writes=0,scope='Full93 retained-row causal potential/history availability and exact current48/context/clock/action/reward/done/next48/clock plus both reward potentials. Existing52 history/bit and masks copied unchanged for terminal diagnostic; no new52 migration. Terminal next features copy current per original next-observation semantics.'))
 print(json.dumps(dict(method=m,rows=n,terminals=len(idx),elapsed=time.monotonic()-start)),flush=True)
if __name__=='__main__':
 m=sys.argv[1]
 try:main(m)
 except BaseException:
  put(O/(m+'_FAILURE.json'),dict(time=time.time(),traceback=traceback.format_exc()));raise
