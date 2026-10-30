"""Read-only raw-history boundary and exact saved-SSE decomposition review.

This verifies the proposed feature semantics, not a new fitting experiment.
"""
from pathlib import Path
import hashlib,json,math,time
import numpy as np
D=Path(__file__).resolve().parent; B=D.parents[1]
def read(p): return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
source=B/'runtime/source_train17_clock/source'
gate=source/'scripts/validate_office_apparatus_v5_20260917.py'
adapter=source/'tools/published_compliance_episode_20261025.py'
hashes=read(source.parent/'SOURCE_HASHES.json')
for p in (gate,adapter):assert sha(p)==hashes[str(p.relative_to(source))]
assert "physical_valid=abort_reason is None and stats['max_external_penetration_m']<=.0002" in gate.read_text()
assert "result['strict_success']=bool(result['task_success'] and result['physical_valid'])" in gate.read_text()
assert "result['strict_success']=bool(result['strict_success'] and result['unexpected_edge_safe'])" in gate.read_text()
history=B/'runtime/history88_frozen_preparation_20261030_v1/persisted_history_critic.py'
assert '(value / (value + 0.0002)).astype(np.float32)' in history.read_text()
old=read(D/'FIXED87_SSE_CONTRIBUTORS.json'); follow=B/'runs/history89_fixed87_terminal_followup_20261030_v1'
full=read(follow/'REVIEW.json'); extensions=B/'runs/recovery87_history_extension_20261030_v1'; meta=read(extensions/'REVIEW.json'); results={}
for m in ('impedance','admittance','vmc'):
 p=follow/(m+'_values.npz'); assert sha(p)==old['methods'][m]['values_sha256']==full['methods'][m]['values_sha256']
 side=Path(meta['methods'][m]['sidecar']['path']); assert sha(side)==meta['methods'][m]['sidecar']['sha256']
 peaks=np.load(side,mmap_mode='r'); assert peaks.shape==(meta['methods'][m]['total_rows'],2)
 # Actual history mapping is float64 division followed by float32 storage.
 raw=peaks[:,0]; feature=(raw/(raw+.0002)).astype(np.float32)
 assert np.isfinite(raw).all() and (raw>=0).all()
 raw_bad=raw>.0002; rounded_bad=feature>.5
 with np.load(p) as z:
  idx=z['indices']; np.testing.assert_array_equal(feature[idx],z['feature'].reshape(-1)); np.testing.assert_array_equal(feature[idx],z['observations51'][:,50])
  reward=z['rewards'].astype(np.float64); mask=z['masks'].astype(np.float64); q0=z['complete88'].astype(np.float64); q1=z['complete89'].astype(np.float64)
  delta=((q1-reward)**2-(q0-reward)**2)*mask
  for c in old['methods'][m]['critics']:
   j=c['critic']; values=delta[:,j]
   assert math.isclose(math.fsum(values),c['total_masked_sse_delta'],rel_tol=1e-12,abs_tol=1e-8)
   assert int((values>0).sum())==c['worsened_rows'] and int((values<0).sum())==c['improved_rows']
   assert math.isclose(math.fsum(values[values>0]),c['positive_sse_delta_sum'],rel_tol=1e-12,abs_tol=1e-8)
   assert math.isclose(math.fsum(values[values<0]),c['negative_sse_delta_sum'],rel_tol=1e-12,abs_tol=1e-8)
   for row in c['top10_worsening']:
    k=int(np.flatnonzero(idx==row['replay_row'])[0])
    assert row['reward']==float(reward[k,0]) and row['history_feature']==float(feature[idx[k]])
    assert row['q88']==float(q0[k,j]) and row['q89']==float(q1[k,j])
    assert row['original_mask']==float(mask[k,j]) and row['sse_delta']==float(values[k])
  results[m]=dict(sidecar=ref(side),values=ref(p),all_retained87_rows=len(raw),original87_terminal_rows=len(idx),raw_preaction_violation_rows=int(raw_bad.sum()),rounded_feature_boundary_disagreements=int(np.count_nonzero(raw_bad!=rounded_bad)),terminal_boundary_disagreements=int(np.count_nonzero(raw_bad[idx]!=rounded_bad[idx])),all_saved_terminal_features_exact=True,all5_saved_sse_contributors_recomputed=True,minimum_terminal_distance_to_threshold_m=float(np.abs(raw[idx]-.0002).min()))
# A counterexample shows why float32 feature>.5 cannot define the raw physical gate.
x=np.nextafter(np.float64(.0002),np.inf); f=np.float32(x/(x+.0002));assert x>.0002 and f==.5
report=dict(passed=True,time=time.time(),sources=[ref(p) for p in (Path(__file__),gate,adapter,history)],methods=results,raw_gate='external cumulative penetration <=0.0002m, no tolerance in frozen source; abort/task/additional unexpected-edge checks also apply',causal_candidate='float(raw_preaction_cumulative_external_penetration_m > 0.0002), not rounded history_feature >0.5',float32_counterexample=dict(raw_m=float(x),feature=float(f),raw_violation=True,rounded_feature_violation=False),interpretation='Explicit bit is only a known penetration-violation flag. It is not Task/Strict outcome, contains no future information, and does not replace additional gates. Continuous feature quantization mismatch can occur mathematically even if absent from current saved rows. No evidence that rounding caused observed critic regressions.',new_neural_forwards=0,optimizer_updates=0,physics_steps=0,new_architecture_implemented=False,fitting_registered=False,cycle90_launched=False)
with (D/'BOUNDARY_AND_CONTRIBUTORS_REVIEW.json').open('x') as out:json.dump(report,out,indent=2,allow_nan=False);out.write('\n')
print(json.dumps(report,indent=2))
