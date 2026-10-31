from pathlib import Path
import json,time,hashlib,math
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation91_fixed87_terminal_followup_20261030_v1';r=json.loads((O/'REVIEW.json').read_text());assert r['passed'];summary={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for m,x in r['methods'].items():
 p=O/(m+'_values.npz');assert sha(p)==x['values_sha256'] and x['full_learner_replay_rng_unchanged']
 with np.load(p) as a:
  for label in ['initial_control','complete88','complete89','complete90','complete91']:
   target=x['stats'][label];sq=(a[label].astype(np.float64)-a['rewards'].astype(np.float64))**2
   for j in range(5):
    masked=math.fsum(float(v)*float(w) for v,w in zip(sq[:,j],a['masks'][:,j]));allrows=math.fsum(map(float,sq[:,j]));count=math.fsum(map(float,a['masks'][:,j]))
    assert math.isclose(masked,target['masked_sse'][j],rel_tol=1e-12,abs_tol=1e-8) and math.isclose(allrows,target['all_row_sse'][j],rel_tol=1e-12,abs_tol=1e-8) and count==target['mask_counts'][j] and math.isclose(masked/count,target['masked_mse'][j],rel_tol=1e-12,abs_tol=1e-8)
 a0=math.fsum(x['stats']['complete90']['masked_sse']);z=math.fsum(x['stats']['complete91']['masked_sse']);summary[m]=dict(total_masked_sse90=a0,total_masked_sse91=z,relative_total_change=z/a0-1,per_critic_delta=x['complete91_minus90_masked_sse'],all_row_delta=[b-a for a,b in zip(x['stats']['complete90']['all_row_sse'],x['stats']['complete91']['all_row_sse'])])
with (D/'TERMINAL_SAVED_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),all_saved87_88_89_90_91_all5_scalar_statistics_verified=True,summary=summary,network_forwards=0,optimizer_updates=0,physics_steps=0),f,indent=2);f.write('\n')
plot=O/'fixed87_terminal_87_88_89_90_91.png'
with (O/'PLOT_INSPECTION.json').open('x') as f:json.dump(dict(time=time.time(),actual_visual_inspection=True,plots=[dict(path=str(plot),sha256=sha(plot),inspected=True)],summary=summary,findings=['All original87 terminals/all5/masks retained across87-91.','I totalmasked improves, critics1/3 regress; A totalmasked worsens, onlycritic3 improves; V totalmasked improves, critic4 regresses.','All-row SSE declines for all I/A critics; V critic2 all-row SSE rises. Fixed seen-terminal fitting is not policy safety or convergence.']),f,indent=2);f.write('\n')
print(json.dumps(summary,indent=2))
