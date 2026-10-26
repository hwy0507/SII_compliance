from pathlib import Path
import os,json,hashlib
os.sched_setaffinity(0,{52})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent;d=json.loads((p/'REVIEW.json').read_text());raw=[Path(x['path']) for x in d['inputs'] if x['path'].endswith('rollout.npz') and '/direct/' in x['path']];assert len(raw)==30
keys=['task_position_error_m','task_rotation_error_rad','task_speed_mps'];values={k:[] for k in keys};times=None
for f in raw:
 with np.load(f) as x:
  times=x['neuron_time'];assert len(times)==1375
  for k in keys:values[k].append(x[k])
fig,axes=plt.subplots(1,3,figsize=(14,4))
for ax,key,threshold in zip(axes,keys,[.012,.12,.025]):
 a=np.array(values[key]);mask=times<1.0
 ax.plot(times[mask],np.median(a[:,mask],axis=0),label='Direct13 median')
 ax.fill_between(times[mask],np.percentile(a[:,mask],10,axis=0),np.percentile(a[:,mask],90,axis=0),alpha=.25,label='10-90% across30')
 ax.axhline(threshold,color='red',ls='--',label='Task threshold')
 ax.set_title(key);ax.set_xlabel('Time (s)');ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.suptitle('Existing formal13 sampled telemetry: first second; not independent gate replay')
fig.tight_layout();fig.savefig(p/'initial_approach.png',dpi=150)
(p/'PLOT_RECEIPT.json').write_text(json.dumps(dict(review_sha256=hashlib.sha256((p/'REVIEW.json').read_bytes()).hexdigest(),plot_sha256=hashlib.sha256((p/'initial_approach.png').read_bytes()).hexdigest(),new_physics=0,optimizer_updates=0),indent=2)+'\n')
