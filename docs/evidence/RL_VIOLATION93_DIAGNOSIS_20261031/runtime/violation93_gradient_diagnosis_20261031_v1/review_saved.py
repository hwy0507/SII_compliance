from pathlib import Path
import json,time,hashlib,math,os
os.sched_setaffinity(0,{11})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_gradient_diagnosis_20261031_v1';rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=rd(O/'REVIEW.json');n=rd(O/'NEIGHBOR_REVIEW.json');assert r['passed'] and n['passed'] and rd(O/'FINISHED.json')['passed'];checks={}
def check_rel(a,b,relation):
 a=a.astype(float);b=b.astype(float);dot=math.fsum(float(x)*float(y) for x,y in zip(a,b));na=math.sqrt(math.fsum(float(x)*float(x) for x in a));nb=math.sqrt(math.fsum(float(x)*float(x) for x in b))
 np.testing.assert_allclose([dot,na,nb],[relation['dot'],relation['norm_left'],relation['norm_right']],rtol=1e-10,atol=1e-8)
 if na==0 or nb==0:assert relation['cosine'] is None
 else:np.testing.assert_allclose(dot/(na*nb),relation['cosine'],rtol=1e-10,atol=1e-10)
for cycle,v in r['cycles'].items():
 aa=[];bb=[]
 for c in v['critics']:
  p=Path(c['gradients']['path']);assert sha(p)==c['gradients']['sha256'] and p.stat().st_size==c['gradients']['bytes']
  with np.load(p) as z:a=z['known_aborts'];b=z['other_terminals'];total=z['all_terminals'];assert all(np.isfinite(x).all() for x in [a,b,total]);assert len(a)==sum(c['parameter_sizes'])
  check_rel(a,b,c['relation']);res=float(np.linalg.norm(total.astype(float)-a.astype(float)-b.astype(float)));np.testing.assert_allclose(res,c['gradient_sum_residual_norm'],rtol=1e-12,atol=1e-12)
  assert res<=2e-5*max(1.,float(np.linalg.norm(total.astype(float))));aa.append(a);bb.append(b)
 check_rel(np.concatenate(aa),np.concatenate(bb),v['aggregate']);assert v['exact_saved_predictions'] and v['full_learner_optimizer_replay_rng_and_parameter_grads_unchanged'];checks[cycle]=dict(all5_gradients_and_aggregate_arithmetic_checked=True)
p=Path(n['values']['path']);assert sha(p)==n['values']['sha256']
with np.load(p) as z:vals={k:z[k].copy() for k in z.files}
x=np.concatenate([vals['observations'],vals['actions']],1).astype(float);reward=vals['rewards'];ids=vals['indices'];np.testing.assert_array_equal(np.where(x.std(0)>1e-8,x.std(0),1.),vals['scale'])
for name,y in [('native_units',x),('unit_std',x/vals['scale'])]:
 # Independently use centered Gram distances for exhaustive minima; saved distances use direct differences.
 y=y-y.mean(0);norm=(y*y).sum(1);dist2=np.maximum(norm[:,None]+norm[None,:]-2*y@y.T,0);np.fill_diagonal(dist2,np.inf)
 for label,allowed in [('nearest',np.ones((len(y),len(y)),dtype=bool)),('opposite',np.sign(reward[:,None])!=np.sign(reward[None,:]))]:
  pidx=vals[name+'_'+label+'_positions'];saved=vals[name+'_'+label+'_distances'];assert np.all(pidx!=np.arange(len(y)));np.testing.assert_allclose(np.linalg.norm(y-y[pidx],axis=1),saved,rtol=1e-10,atol=1e-10)
  d2=np.where(allowed,dist2,np.inf);np.testing.assert_allclose(saved*saved,d2.min(1),rtol=1e-7,atol=1e-8)
 assert int(np.count_nonzero(np.sign(reward)!=np.sign(reward[vals[name+'_nearest_positions']])))==n['metrics'][name]['nearest_opposite_sign_count']
 assert n['unique_inputs']==len(np.unique(x,axis=0))
checks['neighbors']=dict(all2755_rows_and_both_metric_minima_independently_checked=True)
fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True);xs=np.arange(5)
for offset,(cycle,v) in zip([-.18,.18],r['cycles'].items()):
 values=[np.nan if q['relation']['cosine'] is None else q['relation']['cosine'] for q in v['critics']];ax.bar(xs+offset,values,width=.36,label='full'+cycle)
ax.text(1,0,'N/A: no abort mask',ha='center',va='bottom',fontsize=9);ax.axhline(0,color='black',lw=.7);ax.set_ylim(-1,1);ax.set_xticks(xs);ax.set_xlabel('Critic index');ax.set_ylabel('Gradient cosine: known aborts vs all other fixed92 terminals');ax.set_title('Impedance, all2755 fixed92 terminal inputs; zero optimizer updates\nNegative = local opposing gradients; not historical causal proof');ax.legend();ax.grid(axis='y',alpha=.2);fig.savefig(O/'gradient_cosines.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5),constrained_layout=True)
for key,label in [('nearest','Nearest any row'),('opposite','Nearest opposite reward sign')]:
 d=np.sort(vals['unit_std_'+key+'_distances']);ax.plot(d,np.arange(1,len(d)+1)/len(d),label=label)
ax.set_xscale('log');ax.set_xlabel('Joint52 observation+5 action Euclidean distance / per-column std');ax.set_ylabel('Empirical cumulative fraction');ax.set_title('All2755 fixed92 impedance terminal rows; diagnostic scaling only\nNearby inputs do not establish unavoidable label ambiguity');ax.grid(alpha=.2);ax.legend();fig.savefig(O/'neighbor_distances.png',dpi=150);plt.close(fig)
with (O/'SAVED_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),checks=checks,source_sha256=sha(__file__),actual_plot_inspection_pending=True,new_physics=0,optimizer_updates=0),f,indent=2);f.write('\n')
print(json.dumps(checks))
