"""Verify actual online total terminal-population diagnostic against transition done events.

A prefix without new terminals cannot prove growth. Full mode requires complete98
and checks all replay dones against the retained full97 population and98 journal.
Per-stratum online tensor contents are not logged, so no such observation is claimed.
"""
from pathlib import Path
import sys,os,json,time,hashlib,math,gc
os.sched_setaffinity(0,{12});D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle98_20261031_v1';V=B/'runs/parameter_census_cycle98_review_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def first_lines(p,n):
 with p.open('rb') as f:return b''.join(next(f) for _ in range(n))
def audit_rows(transitions,updates,parent_steps,parent_count):
 if len(transitions)!=len(updates):raise ValueError('Journal/update length mismatch')
 count=parent_count;changes=[]
 for i,(t,u) in enumerate(zip(transitions,updates),parent_steps+1):
  if t['step']!=i or u['step']!=i or t['cycle']!=98 or u['update_index']!=0:raise ValueError('Noncontiguous98 journal/update binding')
  if type(t['done']) is not bool:raise ValueError('Nonboolean done')
  count+=int(t['done'])
  if type(u['agent_train/terminal_population']) is not int or u['agent_train/terminal_population']!=count:raise ValueError('Online population differs from inclusive journal done count')
  if not 0<=u['agent_train/sampled_terminal_rows']<=65536:raise ValueError('Sampled terminal count out of range')
  if t['done']:changes.append(dict(step=i,replay_index=i-1,condition=t['condition'],population=count))
 return dict(rows=len(transitions),parent_population=parent_count,final_population=count,new_terminal_rows=len(changes),changes=changes)
def main():
 import numpy as np
 plan=read(D/'CACHE_POPULATION_PLAN.json')
 assert sha(__file__)==plan['source_sha256']
 for p,h in plan['inputs'].items():assert sha(p)==h,p
 full='--complete' in sys.argv
 if full:
  assert read(V/'FINISHED.json')['completed'];review=read(V/'REVIEW.json');assert review['passed']
 results={}
 for m,e in plan['methods'].items():
  reg=read(R/m/'REGISTRATION.json');n=reg['post_interruption_continuation']['parent_steps']
  with np.load(e['baseline_values']) as z:indices=z['indices'].copy();masks=z['masks'].copy()
  assert len(indices)==e['terminal_rows'];tp=R/m/'train/transitions.jsonl';up=R/m/'train/optimizer.jsonl'
  tbytes=tp.read_bytes() if full else first_lines(tp,5000);ubytes=up.read_bytes() if full else first_lines(up,5000)
  ts=[json.loads(l) for l in tbytes.splitlines()];us=[json.loads(l) for l in ubytes.splitlines()];s=audit_rows(ts,us,n,len(indices))
  if full:
   assert s['rows']==review['methods'][m]['new_transitions']
   sys.path.insert(0,plan['restore_runtime']);from driver import validate_checkpoint
   import torch
   torch.set_num_threads(1);cp=B/'runs/parameter_census_cycle98_archive_20261031_v1'/m/'cycle_00098.pt';h=review['methods'][m]['checkpoint_sha256'];assert sha(cp)==h;ck=torch.load(cp,map_location='cpu',weights_only=False);validate_checkpoint(ck,reg,complete=True);arrays=ck['replay']['arrays'];done=arrays['dones'][:,0]
   np.testing.assert_array_equal(np.flatnonzero(done[:n]),indices);np.testing.assert_array_equal(arrays['masks'][indices],masks);np.testing.assert_array_equal(done[n:],np.array([int(t['done']) for t in ts]));assert int(done.sum())==s['final_population']
   assert s['new_terminal_rows']==len(reg['conditions'])==len(set(x['condition'] for x in s['changes']))==30
   terminal_mask=arrays['masks'][np.flatnonzero(done)];assert np.all((terminal_mask==0)|(terminal_mask==1));codes=(terminal_mask*np.array([1,2,4,8,16])).sum(1).astype(int);s['checkpoint_32strata_population']=np.bincount(codes,minlength=32).tolist();s['checkpoint_sha256']=h;assert sha(cp)==h;del ck,arrays;gc.collect()
  else:
   assert first_lines(tp,5000)==tbytes and first_lines(up,5000)==ubytes
  s.update(transitions_sha256=hashlib.sha256(tbytes).hexdigest(),optimizer_sha256=hashlib.sha256(ubytes).hexdigest(),online_total_count_checked=True,online_new_terminal_growth_observed=s['new_terminal_rows']>0);results[m]=s
 result=dict(passed=True,time=time.time(),methods=results,full98=full,physics_steps=0,optimizer_updates=0,scope='Every optimizer total population compared to inclusive98 done cumsum plus all retained97 terminals; full mode additionally binds all98 replay dones. Online per-stratum tensor contents not logged; no observation claim for them.')
 with (D/('CACHE_POPULATION_FULL_REVIEW.json' if full else 'CACHE_POPULATION_PREFIX_REVIEW.json')).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print({m:(r['rows'],r['new_terminal_rows'],r['final_population']) for m,r in results.items()})
if __name__=='__main__':main()
