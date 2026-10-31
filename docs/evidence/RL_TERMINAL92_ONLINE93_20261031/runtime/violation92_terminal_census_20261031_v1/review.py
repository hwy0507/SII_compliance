from pathlib import Path
import hashlib,json,math,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_terminal_census_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def close(a,b):np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-8)
plan=read(O/'PLAN.json');rp=read(O/'REVIEW_PLAN.json');assert sha(__file__)==rp['source_sha256'];assert read(O/'FINISHED.json')['passed']
fig,axes=plt.subplots(3,2,figsize=(13,12),constrained_layout=True);results={}
for row,(method,entry) in enumerate(plan['methods'].items()):
 report=read(O/(method+'_REVIEW.json'));p=O/(method+'_values.npz');assert sha(p)==report['values_sha256'] and p.stat().st_size==report['values_bytes'] and report['passed']
 with np.load(p) as z:data={k:z[k].copy() for k in z.files}
 idx=data['indices'];obs=data['observations'];q=data['predictions'].astype(float);r=data['rewards'].astype(float);mask=data['masks'].astype(float);assert len(idx)==entry['terminal_count'] and np.all(np.diff(idx)>0)
 assert np.isfinite(q).all() and obs.shape==(len(idx),52) and mask.shape==(len(idx),5) and set(np.unique(mask))<={0,1}
 e=(q-r[:,None])**2;weighted=e*mask;sse=np.array([math.fsum(x) for x in weighted]);total=math.fsum(sse);order=np.argsort(-sse,kind='stable');den=data['replay_mask_counts']+127*data['terminal_mask_counts'];np.testing.assert_array_equal(den,data['weighted_replay_denominators']);np.testing.assert_array_equal(mask.sum(0),data['terminal_mask_counts'])
 for name,sel in [('all',np.ones(len(idx),dtype=bool)),('before92',idx<entry['parent_steps']),('new92',idx>=entry['parent_steps']),('bit0',obs[:,51]==0),('bit1',obs[:,51]==1)]:
  v=report['groups'][name];assert v['rows']==int(sel.sum());close(v['masked_sse'],math.fsum(sse[sel]));close(v['per_critic_masked_sse'],[math.fsum(weighted[sel,j]) for j in range(5)]);close(v['all_row_sse'],[math.fsum(e[sel,j]) for j in range(5)]);np.testing.assert_array_equal(v['per_critic_mask_count'],mask[sel].sum(0));close(v['full_replay_weighted_terminal_contribution'],sum(128*math.fsum(weighted[sel,j])/den[j] for j in range(5)))
 for k,value in report['top_k_fractions'].items():close(value,math.fsum(sse[order[:int(k)]])/total)
 for item,j in zip(report['top20'],order[:20]):
  assert item['replay_index']==int(idx[j]) and item['bit']==int(obs[j,51]);close(item['masked_sse'],sse[j]);close(item['fraction'],sse[j]/total);np.testing.assert_array_equal(item['q'],q[j]);np.testing.assert_array_equal(item['mask'],mask[j]);assert item['reward']==r[j]
 for item in report['known_aborts']:
  source=item['source'];i=item['replay_index'];where=np.flatnonzero(idx==i);assert len(where)==1;j=int(where[0]);assert item['rank']==int(np.flatnonzero(order==j)[0])+1
  for x in source['sources']:assert sha(x['path'])==x['sha256']
  path=Path(source['sources'][0]['path']);found=[]
  with path.open() as f:
   for line in f:
    x=json.loads(line)
    if x['step']==i+1:found.append(x)
  assert found==[source['transition']] and found[0]['done'];assert np.float32(found[0]['reward'])==r[j];roll=read(source['sources'][1]['path']);assert roll['abort_reason']=='global_penetration_exceeded_2mm';close(item['masked_sse'],sse[j]);close(item['fraction'],sse[j]/total);np.testing.assert_array_equal(item['q'],q[j]);np.testing.assert_array_equal(item['mask'],mask[j])
 ax=axes[row,0];ax.plot(np.arange(1,len(idx)+1),np.cumsum(sse[order])/total);ax.set_xscale('log');ax.set_ylim(0,1.02);ax.set_xlabel('Number of terminals, descending masked SSE');ax.set_ylabel('Fraction of all terminal masked SSE');ax.set_title(method+' concentration');ax.grid(alpha=.25)
 ax=axes[row,1]
 for j in range(5):ax.scatter(r,q[:,j],s=5,alpha=.25,label='critic'+str(j))
 limits=[min(r.min(),q.min())-2,max(r.max(),q.max())+2];ax.plot(limits,limits,'k--',linewidth=1);ax.set_xlabel('Stored terminal reward / target');ax.set_ylabel('Full92 Q');ax.set_title(method+' all five predictions; all rows retained');ax.legend(fontsize=7);ax.grid(alpha=.25)
 for item in report['known_aborts']:
  ax.scatter([item['reward']]*5,item['q'],marker='x',s=35,color='black');ax.annotate('abort'+str(item['cycle']),(item['reward'],max(item['q'])),fontsize=8)
 results[method]=dict(terminal_rows=len(idx),total_masked_sse=total,top_k_fractions=report['top_k_fractions'],known_aborts=report['known_aborts'],groups=report['groups'],all_scalar_groups_ranks_sources_checked=True,source_review_sha256=sha(O/(method+'_REVIEW.json')),values_sha256=sha(p))
fig.suptitle('Full92 all replay terminals, original masks; zero optimizer updates\nConcentration is descriptive, not irreducibility or historical online spike causality');fig.savefig(O/'terminal_concentration.png',dpi=150);plt.close(fig)
result=dict(passed=True,time=time.time(),methods=results,source_sha256=sha(__file__),plot_sha256=sha(O/'terminal_concentration.png'),optimizer_updates=0,new_physics=0,actual_plot_inspection_pending=True,convergence_claim=False)
with (O/'SAVED_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({m:dict(rows=x['terminal_rows'],sse=x['total_masked_sse'],top_k=x['top_k_fractions'],known_aborts=[{k:a[k] for k in ['cycle','rank','masked_sse','fraction','q','bit']} for a in x['known_aborts']]) for m,x in results.items()},indent=2))
