"""Descriptive fixed92 error changes: all known aborts vs every other terminal, all five critics."""
from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{10})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
plan=read(D/'DECOMPOSITION_PLAN.json');assert sha(Path(__file__))==plan['source_sha256'];report=read(O/'REVIEW.json');assert report['passed'] and read(O/'SAVED_REVIEW.json')['passed'] and read(O/'FINISHED.json')['passed'];results={};fig,axs=plt.subplots(3,1,figsize=(12,10),constrained_layout=True)
for ax,(m,r) in zip(axs,report['methods'].items()):
 p=O/(m+'_values.npz');assert sha(p)==r['values_sha256']
 with np.load(p) as z:values={k:z[k].copy() for k in z.files}
 ids=values['indices'];mask=values['masks'].astype(float);y=values['rewards'].astype(float)
 old=(values['complete92'].astype(float)-y[:,None])**2*mask;new=(values['complete93'].astype(float)-y[:,None])**2*mask
 known={x['replay_index'] for x in r['known_aborts']};assert known==set(plan['known_abort_indices'][m]);flags=np.isin(ids,list(known));assert int(flags.sum())==len(known)
 groups={}
 for name,select in [('known_aborts',flags),('other_terminals',~flags),('all',np.ones(len(ids),dtype=bool))]:
  before=[math.fsum(old[select,j]) for j in range(5)];after=[math.fsum(new[select,j]) for j in range(5)];delta=[b-a for a,b in zip(before,after)]
  groups[name]=dict(rows=int(select.sum()),mask_counts=mask[select].sum(0).tolist(),sse92=before,sse93=after,delta=delta,total92=math.fsum(before),total93=math.fsum(after),total_delta=math.fsum(delta),regressing_critics=[j for j,v in enumerate(delta) if v>0])
 for cycle in ['92','93']:np.testing.assert_allclose(groups['all']['sse'+cycle],r['stats']['complete'+cycle]['masked_sse'],rtol=1e-12,atol=1e-8)
 for k in ['total92','total93','total_delta']:assert math.isclose(groups['all'][k],groups['known_aborts'][k]+groups['other_terminals'][k],abs_tol=1e-8)
 delta=(new-old).sum(1);order=np.argsort(delta,kind='stable');ranked={}
 for label,positions in [('largest_increases',order[-10:][::-1]),('largest_decreases',order[:10])]:
  ranked[label]=[dict(replay_index=int(ids[j]),known_abort=bool(flags[j]),reward=float(y[j]),mask=mask[j].tolist(),sse92=math.fsum(old[j]),sse93=math.fsum(new[j]),delta=math.fsum(new[j])-math.fsum(old[j])) for j in positions]
 results[m]=dict(groups=groups,ranked=ranked,inputs=ref(p),all_rows_retained=True)
 x=np.arange(5);ax.bar(x-.18,groups['known_aborts']['delta'],width=.36,label='Known abort terminals');ax.bar(x+.18,groups['other_terminals']['delta'],width=.36,label='All other terminals');ax.axhline(0,color='black',lw=.5);ax.set_title(m+': masked SSE93 minus92');ax.set_xlabel('Critic index');ax.set_ylabel('SSE change');ax.legend();ax.grid(axis='y',alpha=.2)
fig.suptitle('All fixed92 terminals, original masks; positive = worse\nError redistribution is descriptive, not causal evidence of interference');fig.savefig(D/'terminal_error_decomposition.png',dpi=150);plt.close(fig)
out=dict(passed=True,time=time.time(),methods=results,source=ref(Path(__file__)),inputs=[ref(O/'REVIEW.json'),ref(O/'SAVED_REVIEW.json'),ref(O/'FINISHED.json')],plot=ref(D/'terminal_error_decomposition.png'),new_physics=0,optimizer_updates=0,convergence_claim=False,scope=plan['scope'])
with (D/'TERMINAL_DECOMPOSITION.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({m:x['groups'] for m,x in results.items()},indent=2))
