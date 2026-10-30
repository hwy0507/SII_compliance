from pathlib import Path
import hashlib,json,math,time,os
os.sched_setaffinity(0,{54})
p=Path(__file__).parent;b=p.parents[1]
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
plan=json.loads((p/'PLAN.json').read_text());r=json.loads((p/'REVIEW.json').read_text());assert r['passed'] and sha(p/'audit.py')==plan['source_sha256'];assert sha(p/'loss.png')==r['plot_sha256']
for m,info in r['methods'].items():
 saved=p/f'{m}_first5000.jsonl';assert sha(saved)==r['inputs'][m]['sha256'];source=b/f'runs/parameter_partial75_recovery_cycle83_20261029_v1/{m}/train/optimizer.jsonl'
 with source.open('rb') as f:prefix=b''.join(f.readline() for _ in range(5000))
 assert prefix==saved.read_bytes();rows=list(map(json.loads,prefix.splitlines()));assert len(rows)==5000;assert all(x['step']==rows[0]['step']+i for i,x in enumerate(rows));assert all(math.isfinite(v) for x in rows for v in x.values() if isinstance(v,(int,float)))
 for k,s in info['metrics'].items():
  v=[x[k] for x in rows]
  for name,value in [('first1000',math.fsum(v[:1000])/1000),('last1000',math.fsum(v[-1000:])/1000),('mean',math.fsum(v)/5000),('maximum',max(v))]:assert math.isclose(value,s[name],rel_tol=1e-12,abs_tol=1e-12)
(p/'SAVED_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),all3_prefixes_exact=True,all_numeric_fields_finite=True,steps_contiguous=True,independent_scalar_arithmetic=True,source_sha256=sha(Path(__file__)),registered_after_prefix_available=True,plot_inspected=False,convergence_claim=False),indent=2)+'\n')
print(json.dumps(r['methods'],indent=2))
