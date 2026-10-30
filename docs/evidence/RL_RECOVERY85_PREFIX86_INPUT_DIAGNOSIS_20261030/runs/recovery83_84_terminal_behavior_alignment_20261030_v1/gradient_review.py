from pathlib import Path
import hashlib,json,time,os,sys,math
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
D=Path(__file__).parent;B=D.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
try:
 plan=read(D/'GRADIENT_PLAN.json');assert ref(Path(__file__))==plan['source']
 for r in plan['inputs']:assert ref(Path(r['path']))==r
 inputs=read(D/'INPUT_REVIEW.json');result={};started=time.monotonic();forward_count=0;backward_count=0
 for m in plan['methods']:
  assert time.monotonic()-started<plan['max_seconds']
  t=B/f'runs/{m}_recovery84_terminal_followup_20261029_v1';tp=read(t/'PLAN.json');binding=read(t/'FINAL_BINDING.json');reg=read(Path(tp['inputs']['registration']['path']));runtime=Path(reg['runtime']);helper=Path(tp['helper_runtime'])
  assert sha(runtime/'RUNTIME.json')==reg['runtime_sha256']
  for name,h in read(runtime/'SOURCE_HASHES.json').items():assert sha(runtime/'source'/name)==h
  for name,h in reg['batch_size_stage']['dependency_hashes'].items():assert sha(helper/name)==h
  sys.path[:0]=[str(helper),str(runtime/'source/tools')]
  from published_compliance_learner_20261025 import PublishedLearner
  from validate_published_finite_check_20261025 import digest
  assert sha(helper/'validate_published_finite_check_20261025.py')==tp['digest_helper_sha256']
  cp=Path(binding['checkpoint']['path']);assert sha(cp)==binding['checkpoint']['sha256']
  ck=torch.load(cp,map_location='cpu',weights_only=False);assert ck['cycle']==84 and ck['controller']==m and ck['boundary']=='complete_condition_cycle';state=ck['learner']
  anchor=B/f'runs/{m}_recovery85_terminal_followup_20261029_v1/anchor84.npz'
  with np.load(anchor,allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
  assert a['features'].shape==(2514,57);indices=a['indices'];positions={int(v):i for i,v in enumerate(indices)};raw=ck['replay']['arrays']
  np.testing.assert_array_equal(a['features'][:,:50],raw['observations'][indices]);np.testing.assert_array_equal(a['features'][:,50:],raw['actions'][indices]);np.testing.assert_array_equal(a['rewards'],raw['rewards'][indices,0]);np.testing.assert_array_equal(a['masks'],raw['masks'][indices].T)
  learner=PublishedLearner(runtime,dimension=7,direct=False,seed=42,device='cpu',algorithm=state['algorithm'],**{k:state[k] for k in ['critic_layer_norm','numerical_amendments','critic_clock']})
  agent=learner.learner.agent;agent.load_state_dict(state['agent']);before=digest(agent.state_dict());assert before==digest(state['agent']);rng=torch.get_rng_state().clone()
  obs=torch.as_tensor(a['features'][:,:50]);act=torch.as_tensor(a['features'][:,50:]);rewards=a['rewards'].astype(float)
  with torch.no_grad():reproduced=torch.stack([agent.get_q_value(obs,act,c,target=False).reshape(-1) for c in range(5)]).numpy()
  forward_count+=5;np.testing.assert_array_equal(reproduced,a['q_after'])
  del raw,ck
  pairs=[];max_error=0.
  for row in inputs['methods'][m]['all30_new_terminal_rows']:
   i=positions[row['replay_index']]
   for n in row['nearest_by_active_critic']:
    assert time.monotonic()-started<plan['max_seconds'];assert forward_count+2<=plan['max_forward_calls'] and backward_count+2<=plan['max_autograd_calls']
    c=n['critic'];j=positions[n['index']];assert a['masks'][c,i]==a['masks'][c,j]==1
    parameters=tuple(agent.ensemble[c].parameters());vectors=[];qs=[]
    for k in [i,j]:
     value=agent.get_q_value(obs[k:k+1],act[k:k+1],c,target=False).reshape(());forward_count+=1
     error=abs(float(value.detach())-float(a['q_after'][c,k]));max_error=max(max_error,error);assert error<=plan['single_row_q_abs_tolerance']
     gradients=torch.autograd.grad(value,parameters,create_graph=False,retain_graph=False);backward_count+=1
     vector=np.concatenate([v.detach().numpy().reshape(-1) for v in gradients]).astype(float);assert np.isfinite(vector).all();vectors.append(vector);qs.append(float(value.detach()))
    u,v=vectors;dot=float(u@v);u2=float(u@u);v2=float(v@v)
    # Independently accumulate each dot and norm with math.fsum.
    for actual,expected in [(math.fsum(float(x)*float(y) for x,y in zip(u,v)),dot),(math.fsum(float(x)*float(x) for x in u),u2),(math.fsum(float(y)*float(y) for y in v),v2)]:assert math.isclose(actual,expected,rel_tol=1e-11,abs_tol=1e-9)
    assert u2>0 and v2>0;jacobian_cos=dot/math.sqrt(u2*v2);ei=qs[0]-rewards[i];ej=qs[1]-rewards[j];scale=4*ei*ej
    loss_cos=math.copysign(1,scale)*jacobian_cos if scale else None
    pairs.append(dict(condition=row['condition'],critic=c,neighbor_sign=n['sign'],row_index=int(indices[i]),neighbor_index=int(indices[j]),input_l2=n['input_l2'],rewards=[float(rewards[i]),float(rewards[j])],q_values=qs,residuals=[ei,ej],parameters=len(u),q_jacobian_dot=dot,q_jacobian_norm_sq=[u2,v2],q_jacobian_cosine=jacobian_cos,squared_error_gradient_dot=scale*dot,squared_error_gradient_cosine=loss_cos,finite_parameters=True))
  assert digest(agent.state_dict())==before and torch.equal(rng,torch.get_rng_state()) and all(p.grad is None for p in agent.parameters());assert sha(cp)==binding['checkpoint']['sha256']
  result[m]=dict(pairs=pairs,all30_conditions=len({x['condition'] for x in pairs})==30,all_active_critics_and_both_neighbor_signs=True,full2514_saved_q_bit_exact=True,max_single_row_q_abs_error=max_error,network_state_and_rng_unchanged=True,parameter_grad_buffers_unmodified=True,checkpoint=ref(cp),parameter_count_by_critic=[sum(p.numel() for p in net.parameters()) for net in agent.ensemble])
  del agent,learner,state
 for r in plan['inputs']:assert ref(Path(r['path']))==r
 put(D/'GRADIENT_REVIEW.json',dict(passed=True,time=time.time(),methods=result,forward_calls=forward_count,autograd_calls=backward_count,elapsed=time.monotonic()-started,new_physics=0,optimizer_updates=0,replay_writes=0,convergence_claim=False,limitation='Retrospective frozen84 local per-sample squared terminal error gradients for all30 new rows of each method and each active critic, nearest same/opposite reward-sign neighbors in fixed2514 inputs. Positive terminal weight and denominator do not change cosine. This is not an actual optimizer minibatch/Adam direction or historical sampling reconstruction; no fitting experiment, causal attribution, threshold or scientific amendment. CPU readonly autograd, no optimizer step.'))
 saved=read(D/'GRADIENT_REVIEW.json');assert saved['methods']==result
 for m,x in result.items():
  for row in x['pairs']:
   u2,v2=row['q_jacobian_norm_sq'];dot=row['q_jacobian_dot'];ei,ej=row['residuals'];assert math.isclose(dot/math.sqrt(u2*v2),row['q_jacobian_cosine'],rel_tol=1e-12);assert math.isclose(4*ei*ej*dot,row['squared_error_gradient_dot'],rel_tol=1e-12,abs_tol=1e-9)
 put(D/'GRADIENT_SAVED_REVIEW.json',dict(passed=True,time=time.time(),all_pair_scalar_dots_norms_cosines_read_back=True,all_gradient_dot_norms_independent_math_fsum=True,review=ref(D/'GRADIENT_REVIEW.json')))
 for m,x in result.items():
  print(m,'pairs',len(x['pairs']),'negative_loss_cosine',sum(r['squared_error_gradient_cosine'] is not None and r['squared_error_gradient_cosine']<0 for r in x['pairs']),'q_max_error',x['max_single_row_q_abs_error'])
  for r in x['pairs']:
   if m=='vmc' and r['condition']=='active_short_train_0600' and r['neighbor_sign']=='opposite':print(json.dumps(r))
except BaseException as e:
 put(D/'GRADIENT_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
