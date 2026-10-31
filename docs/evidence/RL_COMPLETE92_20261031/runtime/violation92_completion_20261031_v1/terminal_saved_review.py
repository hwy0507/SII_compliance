from pathlib import Path
import json,time,hashlib,math
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';r=json.loads((O/'REVIEW.json').read_text());assert r['passed'];summary={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for m,x in r['methods'].items():
 p=O/(m+'_values.npz');assert sha(p)==x['values_sha256'] and x['full_learner_replay_rng_unchanged']
 with np.load(p) as a:
  for label in ['initial_control','complete88','complete89','complete90','complete91','complete92']:
   target=x['stats'][label];sq=(a[label].astype(np.float64)-a['rewards'].astype(np.float64))**2
   for j in range(5):
    masked=math.fsum(float(v)*float(w) for v,w in zip(sq[:,j],a['masks'][:,j]));allrows=math.fsum(map(float,sq[:,j]));count=math.fsum(map(float,a['masks'][:,j]))
    assert math.isclose(masked,target['masked_sse'][j],rel_tol=1e-12,abs_tol=1e-8) and math.isclose(allrows,target['all_row_sse'][j],rel_tol=1e-12,abs_tol=1e-8) and count==target['mask_counts'][j] and math.isclose(masked/count,target['masked_mse'][j],rel_tol=1e-12,abs_tol=1e-8)
 a0=math.fsum(x['stats']['complete91']['masked_sse']);z=math.fsum(x['stats']['complete92']['masked_sse']);summary[m]=dict(total_masked_sse91=a0,total_masked_sse92=z,relative_total_change=z/a0-1,per_critic_delta=x['complete92_minus91_masked_sse'],all_row_delta=[b-a for a,b in zip(x['stats']['complete91']['all_row_sse'],x['stats']['complete92']['all_row_sse'])])
with (D/'TERMINAL_SAVED_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),all_saved87_88_89_90_91_92_all5_scalar_statistics_verified=True,summary=summary,network_forwards=0,optimizer_updates=0,physics_steps=0),f,indent=2);f.write('\n')
print(json.dumps(summary,indent=2))
