from pathlib import Path
import json,hashlib,time,os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).parent;os.sched_setaffinity(0,{54});r=json.loads((D/'UPDATE_AVAILABILITY_REVIEW.json').read_text());b=json.loads((D/'REVIEW.json').read_text())
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for i,m in enumerate(['admittance','vmc']):
 rows=r['methods'][m];a=axes[i,0]
 for x in rows:
  changed=next(p for p in b['methods'][m]['pairs'] if p['condition']==x['condition'])['task_changed']
  a.scatter(x['optimizer_updates_after_append_including_same_step'],x['terminal_prediction']['complete82_masked_sse'],color='crimson' if changed else 'steelblue',s=28)
 a.set_xscale('log');a.set_yscale('symlog',linthresh=.1);a.set_ylim(bottom=0);a.set(title=m+': all30 new82 terminals',xlabel='Logged update opportunities after append',ylabel='Masked terminal SSE at complete82');a.grid(alpha=.25)
 pairs=b['methods'][m]['pairs'];xs=np.arange(30);old=[p['cases']['81']['terminal_prediction']['complete82_masked_sse'] for p in pairs];new=[p['cases']['82']['terminal_prediction']['complete82_masked_sse'] for p in pairs]
 ax=axes[i,1];ax.scatter(xs,old,label='Old81 rows, evaluated at82',s=18);ax.scatter(xs,new,label='New82 rows, evaluated at82',s=18);ax.set_yscale('symlog',linthresh=.1);ax.set(title=m+': all30 condition pairs',xlabel='Sorted condition index',ylabel='Masked terminal SSE');ax.legend(fontsize=8);ax.grid(alpha=.25)
fig.suptitle('Complete82 terminal diagnostics: different states/masks, no sampling or causal claim\nRed = Task label changed81 to82; opportunities are not actual row inclusion',fontsize=10);p=D/'terminal_age_alignment.png';fig.savefig(p,dpi=140);plt.close(fig)
(D/'PLOT_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,rows_per_method=30,plotted_methods=['admittance','vmc'],plot_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_image_viewed=False,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
