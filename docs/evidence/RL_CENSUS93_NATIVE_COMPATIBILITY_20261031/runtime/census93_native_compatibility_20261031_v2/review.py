"""Independent saved-state/prefix/counter/RNG review; zero updates and physics."""
from pathlib import Path
import os,sys,json,time,hashlib,copy,ast
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np,torch
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census93_native_compatibility_20261031_v2'
sys.path[:0]=[str(D),str(B/'runtime/violation93_continuation_20261031_v1'),str(B/'runtime/source_train17_clock/source/tools')]
from census_native import KEY,marker
from validate_published_finite_check_20261025 import digest
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
os.sched_setaffinity(0,{10});torch.set_num_threads(1);p=rd(O/'PLAN.json');result={}
for name,h in rd(O/'SOURCE_LOCK.json').items():assert sha(D/name)==h;ast.parse((D/name).read_text())
for n in ['CACHE_EDGE_REVIEW.json','LOSS_EDGE_REVIEW.json','ADAM_ALIAS_REVIEW.json']:assert rd(O/n)['passed']
for m,e in p['methods'].items():
 r=rd(O/m/'REVIEW.json');arms=rd(O/m/'ARM_RESULTS.json');assert r['passed'] and r['arms']==arms and r['disposable_updates']==32 and r['formal_updates']==r['new_physics']==0
 assert len(r['negative_guards'])==9 and r['source_receipt']['native_code_exact']
 for k in ['metrics','rng','draws','components','state','replay']:
  assert arms['candidate'][k]==arms['candidate_repeat'][k]==arms['candidate_restart'][k],(m,k)
 for k in ['rng','draws','replay']:assert arms['native_control'][k]==arms['candidate'][k]
 for label,a in arms.items():
  assert a['updates']==8 and len(a['metrics'])==len(a['rng'])==len(a['draws'])==8 and a['actor_target_temperature_updated']
  for met in a['metrics']:
   assert all(np.isfinite(v) for v in met.values())
   if label!='native_control':assert met['agent_train/q_loss']==met['agent_train/conditional_terminal_q_loss'] and 'agent_train/original_sampled_q_loss' in met
 ref=arms['candidate_restart']['restart'];assert sha(ref['path'])==ref['sha256'] and Path(ref['path']).stat().st_size==ref['bytes'];assert sha(e['checkpoint'])==e['checkpoint_sha256']
 ck=torch.load(e['checkpoint'],map_location='cpu',weights_only=False,mmap=True);rs=torch.load(ref['path'],map_location='cpu',weights_only=False,mmap=True);n=ck['steps'];a=ck['replay']['arrays'];b=rs['replay']['arrays']
 assert rs['learner'][KEY]==marker() and rs['learner']['num_gradient_steps']==ck['learner']['num_gradient_steps']+4
 counters={}
 for key in ['q_optimizer','actor_optimizer','alpha_optimizer']:
  old=ck['learner'][key];new=rs['learner'][key];assert old['param_groups']==new['param_groups'];changes=[]
  for i in old['state']:
   delta=float(new['state'][i]['step']-old['state'][i]['step']);assert delta==4, (m,key,i,delta);changes.append(delta)
  counters[key]=dict(tensors=len(changes),increment=4)
 for k in ck['replay']:
  if k not in ['size','cursor','arrays','rng']:assert digest(ck['replay'][k])==digest(rs['replay'][k])
 assert rs['replay']['size']==rs['replay']['cursor']==n+4
 for k in a:np.testing.assert_array_equal(a[k],b[k][:n])
 ti=np.flatnonzero(a['dones'][:,0]==1);nt=np.flatnonzero(a['dones'][:,0]==0);fixtures=[ti[-1],nt[-1],ti[-1],nt[-1]];rng=np.random.default_rng();rng.bit_generator.state=copy.deepcopy(ck['replay']['rng']);idxhash=[]
 for offset,row in enumerate(fixtures):
  for k in a:
   if k!='masks':np.testing.assert_array_equal(b[k][n+offset],a[k][row])
  np.testing.assert_array_equal(b['masks'][n+offset],rng.binomial(1,.8,5))
  while True:
   idx=rng.integers(n+offset+1,size=65536)
   if np.all(b['masks'][idx].sum(0)>0):break
  idxhash.append(digest(idx))
 assert idxhash==arms['candidate']['draws'][:4] and digest(rng.bit_generator.state)==digest(rs['replay']['rng'])
 losses={name:dict(q_loss=[x['agent_train/q_loss'] for x in arm['metrics']],original_sampled=[x.get('agent_train/original_sampled_q_loss',x['agent_train/q_loss']) for x in arm['metrics']]) for name,arm in arms.items() if name in ['native_control','candidate']}
 result[m]=dict(passed=True,original_steps=n,restart_steps=n+4,full_original_replay_prefix_exact=True,four_fixture_rows_and_bootstrap_masks_exact=True,independent_accepted_draws_and_replay_RNG_exact=True,optimizer_counter_increments=counters,repeat_and_restart_all_fields_exact=True,native_control_rng_and_draws_exact=True,gradient_max_abs_error=r['gradient_max_abs_error'],terminal_population_initial=r['initial_terminal_rows'],terminal_population_final=arms['candidate']['terminal_count'],losses=losses,restart_file=ref)
 del ck,rs,a,b
v1=B/'runs/census93_native_compatibility_20261031_v1';assert rd(v1/'EMPTY_RELOAD_DEFECT.json')['defect_reproduced'];assert 'AssertionError: state' in rd(v1/'impedance_FAILURE.json')['traceback']
summary=dict(passed=True,time=time.time(),methods=result,maximum_and_actual_v2_disposable_updates=96,prior_v1_impedance_updates=32,total_disposable_updates=128,v1_failures_retained=True,original_physics_and_formal_updates=0,offline_weights_promoted=False,scope='Full native implementation compatibility, not reward convergence, online stability, or rollout generalization; online94 still unregistered.')
with (O/'SAVED_REVIEW.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
print(json.dumps(dict(passed=True,methods=list(result),disposable_updates=128,new_physics=0)),flush=True)
