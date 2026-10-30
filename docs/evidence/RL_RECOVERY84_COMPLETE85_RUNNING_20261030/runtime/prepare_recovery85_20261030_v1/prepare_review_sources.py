from pathlib import Path
import ast,difflib,json,time,hashlib,re
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_partial75_recovery_cycle84_review_20261029_v1';OUT=B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1';OUT.mkdir(exist_ok=True);assert not (OUT/'SOURCE_REVIEW.json').exists();assert not (B/'runs/parameter_partial75_recovery_cycle85_20261029_v1/LAUNCH.json').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
def advance(s):return re.sub('84|83',lambda m:{'84':'85','83':'84'}[m[0]],s)
def save(name,source,advance_cycle,dest=OUT):
 s=source.read_text();v=advance(s) if advance_cycle else s
 if advance_cycle:assert re.sub('85|84',lambda m:{'85':'84','84':'83'}[m[0]],v)==s
 ast.parse(v);p=dest/name
 if p.exists():assert p.read_text()==v
 else:p.write_text(v)
 (dest/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(source),tofile=str(p))))
 files.append(dict(path=str(p),name=name,source=str(source),parent_sha256=sha(source),sha256=sha(p),cycle_metadata_only=advance_cycle,byte_identical=not advance_cycle))
for name in ['review.py','coordinator.py']:save(name,OLD/name,True)
for name in ['diagnose_published_training_20261025.py','diagnose_published_value_bound_20261025.py']:
 assert (OLD/name).exists();save(name,OLD/name,False)
for old,new in [('startup84.py','startup85.py'),('archive84.py','archive85.py')]:save(new,B/'runtime/prepare_recovery84_20261030_v1'/old,True,D)
assert "recovery['parent_cycle']==75 and recovery['new_cycle']==76" in (OUT/'review.py').read_text()
assert "x['interruption_recovery']['parent_cycle']==75 and x['interruption_recovery']['new_cycle']==76" in (D/'startup85.py').read_text()
for p in [OUT/'review.py',D/'startup85.py']:
 assert "old['recovery_continuation']==previous['post_interruption_continuation']" in p.read_text()
r=dict(passed=True,time=time.time(),files=[x for x in files if Path(x['path']).parent==OUT],actual85_not_started=True,full84_not_yet_complete=True,scope='Current cycle/path metadata84→85 and parent83→84 only. All full reward/replay/history/optimizer/30condition/health checks unchanged. Original75→76 interruption and markers23/47 retained. Both required health sources copied exact, including previously repaired value-bound dependency.')
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');(D/'FUTURE_REVIEW_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,actual85_not_started=True),indent=2)+'\n')
print('Future85 startup/archive/fullreview sources ready; no training launch')
