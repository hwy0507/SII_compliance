from pathlib import Path
import json,hashlib,time,math,statistics,os
import numpy as np
D=Path(__file__).parent;P=D.parent/'vmc80_frozen_loss_sampling_20261030_v1'
os.sched_setaffinity(0,{0})
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for d in [P,D]:assert read(d/'REVIEW.json')['passed'] and read(d/'SAVED_REVIEW.json')['passed']
a=[json.loads(l) for l in (P/'BATCHES.jsonl').read_text().splitlines()];b=[json.loads(l) for l in (D/'BATCHES.jsonl').read_text().splitlines()]
assert len(a)==len(b)==512
for x,y in zip(a,b):
 for k in ['batch','sample_indices_sha256','target_pair','denominators','terminal_draws','new30_draws','focus_draws']:assert x[k]==y[k],k
out={}
for key in ['native_loss','terminal_contribution','nonterminal_contribution','new30_contribution','focus_contribution']:
 delta=[y[key]-x[key] for x,y in zip(a,b)]
 out[key]=dict(mean80=statistics.mean(x[key] for x in a),mean81_fixed80=statistics.mean(y[key] for y in b),paired_mean_change=statistics.mean(delta),paired_min_change=min(delta),paired_max_change=max(delta),decrease_batches=sum(v<0 for v in delta),increase_batches=sum(v>0 for v in delta))
 for k in ['mean80','mean81_fixed80','paired_mean_change']:assert math.isfinite(out[key][k])
result=dict(passed=True,time=time.time(),batches=512,all_sample_hashes_target_pairs_denominators_terminal_counts_exact=True,statistics=out,original80_review_sha256=sha(P/'REVIEW.json'),frozen81_review_sha256=sha(D/'REVIEW.json'),convergence_claim=False,causal_claim=False,limitation=read(D/'PRE_REGISTRATION.json')['limitation'])
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(1,2,figsize=(12,4),constrained_layout=True)
for rows,label in [(a,'Model80, replay80'),(b,'Model81, replay80')]:axs[0].plot([r['native_loss'] for r in rows],label=label,lw=.8)
axs[0].set(xlabel='Identical diagnostic batch',ylabel='Weighted critic loss');axs[0].legend()
for key,label in [('native_loss','Total'),('terminal_contribution','Terminal'),('nonterminal_contribution','Nonterminal')]:axs[1].plot([y[key]-x[key] for x,y in zip(a,b)],label=label,lw=.8)
axs[1].axhline(0,color='black',lw=.5);axs[1].set(xlabel='Identical diagnostic batch',ylabel='Frozen81 minus frozen80');axs[1].legend()
fig.suptitle('Paired frozen loss on complete80 replay; all learner state changes together')
fig.savefig(D/'paired_loss.png',dpi=140);plt.close(fig)
result['plot_sha256']=sha(D/'paired_loss.png')
with (D/'PAIRED_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
