from pathlib import Path
import json,math,time,hashlib,os
os.sched_setaffinity(0,{11})
D=Path(__file__).parent
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=json.loads((D/'REVIEW.json').read_text());assert r['passed']
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for i,m in enumerate(['vmc','admittance']):
 x=r['methods'][m];cycles=[84,85,86,87]
 for c in x['critics']:axes[i,0].plot(cycles,[c['sse'+str(k)] for k in cycles],'o-',label='critic'+str(c['critic']))
 axes[i,0].set(title=m+' fixed2514: all5 critics',ylabel='In-mask squared error sum');axes[i,0].legend()
 axes[i,1].plot(cycles,[x['total_sse'][str(k)] for k in cycles],'o-');axes[i,1].set(title=m+' total over all5',ylabel='In-mask squared error sum')
 for a in axes[i]:a.set_xticks(cycles);a.grid(alpha=.2)
fig.suptitle('Same2514 inputs/actions/rewards/masks across84-87; descriptive only')
fig.savefig(D/'fixed2514_84_87.png',dpi=150);plt.close(fig)
(D/'PLOT_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),plot_sha256=hashlib.sha256((D/'fixed2514_84_87.png').read_bytes()).hexdigest(),all5critics=True,actual_image_viewed=False),indent=2)+'\n')
