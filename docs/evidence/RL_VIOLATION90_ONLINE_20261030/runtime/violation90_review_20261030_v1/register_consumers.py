from pathlib import Path
import ast,json,hashlib,time
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
for p in D.glob('*.py'):ast.parse(p.read_text())
# Review the concrete cycle and schema seams, retaining original scientific consumers.
s=(D/'startup90.py').read_text();r=(D/'review90.py').read_text();a=(D/'archive90.py').read_text();h=(D/'health90.py').read_text();l=(D/'loss90.py').read_text()
assert "old['cycle']==89 and x['cycle']==90" in s
assert "x['history_critic_amendment']['first_cycle']==88" in a and "x['violation_critic_amendment']['first_cycle']==90" in a
assert "np.testing.assert_array_equal(v,a[k][:n])" in s and "assert np.array_equal(v,arr[k][:n])" in r
assert 'validate_migrated' not in h and "violation_class(history_class(PublishedLearner, binding), bit)" in h
assert "reg['violation_critic_amendment']['binding']['rows']" in l
assert 'count<=41250' in l and '/min(1000,len(a))' in l
assert "t['cycle']==90" in r
assert "replay_observation_dimension']==52" in s and "replay_observation_dimension']==52" in r
assert "np.testing.assert_array_equal(arr['observations'][k,:50],expected_current)" in r
assert "float(nxt['interval']['external_penetration_peak_m']>.0002)" in s and "float(nxt['interval']['external_penetration_peak_m']>.0002)" in r
put(D/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),scope='Source/AST/explicit finite-cycle and52-column schema seams reviewed. Actual90 startup and full-cycle consumers must still execute.',formal_updates=0,physics=0,full_trained90_review=False,files={p.name:sha(p) for p in D.glob('*.py')}))
put(D/'SOURCES.json',dict(time=time.time(),files={p.name:sha(p) for p in D.glob('*.py')}))
print('Finite90 consumer sources registered')
