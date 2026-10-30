from pathlib import Path
import json,hashlib,os,time,collections
os.environ['MPLBACKEND']='Agg';os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import matplotlib.pyplot as plt
os.sched_setaffinity(0,{53});D=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
assert read(D/'SAVED_REVIEW.json')['passed'];r=read(D/'REVIEW.json');methods=['impedance','admittance','vmc'];colors=['#0072B2','#D55E00','#009E73'];fig,axs=plt.subplots(2,2,figsize=(13,8.5));data={}
for m,color in zip(methods,colors):
 eps=[json.loads(l) for l in (D/(m+'_episodes.jsonl')).read_text().splitlines()];ordered=sorted(eps,key=lambda e:e['first_global_step']);x=np.arange(len(ordered));peak=np.array([e['last_next_peak']*1000 for e in ordered]);bad=np.array([e['preaction_violation_rows'] for e in ordered]);partial=np.array([not e['terminal_retained'] for e in ordered]);root=collections.OrderedDict()
 for e in ordered:
  s=root.setdefault(e['train'],dict(rows=0,bad=0,partial=0));s['rows']+=e['retained_transitions'];s['bad']+=e['preaction_violation_rows'];s['partial']+=int(not e['terminal_retained'])
 rr=list(root.values());xx=np.arange(1,len(rr)+1);fraction=[100*s['bad']/s['rows'] for s in rr]
 axs[0,0].plot(xx,np.cumsum([s['rows'] for s in rr])/1e6,label=m,color=color)
 axs[0,1].scatter(x,peak,s=5,alpha=.45,label=m,color=color)
 axs[1,0].plot(xx,fraction,label=m,color=color,linewidth=1)
 axs[1,1].plot(xx,np.cumsum([s['partial'] for s in rr]),label=m,color=color)
 data[m]=dict(roots=len(rr),cohorts=len(ordered),retained_rows=r['methods'][m]['retained_rows'],maximum_retained_next_peak_mm=float(peak.max()),preaction_violation_rows=int(bad.sum()),partial_cohorts=int(partial.sum()),sidecar=r['methods'][m]['sidecar'])
axs[0,0].set(title='Retained replay coverage through complete cycle 85',xlabel='Physical log in lineage order',ylabel='Cumulative retained transitions (million)')
axs[0,1].axhline(.2,color='black',ls='--',lw=1,label='Original 0.2 mm gate');axs[0,1].set_yscale('symlog',linthresh=.02);axs[0,1].set(title='All retained episode endpoints (partial included)',xlabel='Episode cohort in first-step order',ylabel='Cumulative peak at retained endpoint (mm)')
axs[1,0].set(title='Actions with already known penetration violation',xlabel='Physical log in lineage order',ylabel='Retained pre-action rows above 0.2 mm (%)')
axs[1,1].set(title='Interrupted episode cohorts preserved',xlabel='Physical log in lineage order',ylabel='Cumulative partial cohorts')
for ax in axs.flat:ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.suptitle('Historical journal reconstruction: descriptive coverage, no training amendment',fontsize=13);fig.tight_layout();fig.savefig(D/'history_coverage.png',dpi=150);plt.close(fig)
p=D/'history_coverage.png';out=dict(passed=True,time=time.time(),methods=data,figure=dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()),all_cohorts_included=True,partial_endpoints_not_claimed_terminal=True,new_physics=0,new_network_forward=0,optimizer_updates=0)
with (D/'PLOT_REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(data))
