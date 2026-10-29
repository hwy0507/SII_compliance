from pathlib import Path
import ast,difflib,json,time,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1';OUT=B/'runs/parameter_partial75_recovery_cycle78_review_20261029_v1';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();files=[]
def save(name,source,new,dest=OUT):
 s=source.read_text();ast.parse(new);(dest/name).write_text(new);(dest/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=str(source),tofile=str(dest/name))));files.append(dict(path=str(dest/name),name=name,source=str(source),parent_sha256=sha(source),sha256=sha(dest/name)))
def advance(s):
 # Protect the original75->76 recovery fields; only the current completed parent advances.
 protected=["recovery['new_cycle']==76","x['interruption_recovery']['new_cycle']==76"]
 for i,v in enumerate(protected):s=s.replace(v,f'__HISTORICAL_{i}__')
 s=s.replace('77','__NEXT__').replace('76','77').replace('__NEXT__','78')
 for i,v in enumerate(protected):s=s.replace(f'__HISTORICAL_{i}__',v)
 return s
for name in ['review.py','coordinator.py']:
 source=OLD/name;v=advance(source.read_text())
 if name=='review.py':
  needle="    previous=read(reg['post_interruption_continuation']['parent_registration']['path'])"
  assert needle in v;v=v.replace(needle,needle+"\n    assert old['recovery_continuation']==previous['post_interruption_continuation']")
 save(name,source,v)
for name in ['diagnose_published_training_20261025.py','diagnose_serl_training_20261025.py']:
 source=OLD/name
 if source.exists():save(name,source,source.read_text())
source=B/'runtime/prepare_recovery77_20261029_v1/startup77.py';v=advance(source.read_text());needle=" previous=json.loads(Path(reg['post_interruption_continuation']['parent_registration']['path']).read_text())";assert needle in v;v=v.replace(needle,needle+"\n assert old['recovery_continuation']==previous['post_interruption_continuation']");save('startup78.py',source,v,D)
source=B/'runtime/prepare_recovery77_20261029_v1/archive77.py';save('archive78.py',source,advance(source.read_text()),D)
assert "recovery['parent_cycle']==75 and recovery['new_cycle']==76" in (OUT/'review.py').read_text()
assert "x['interruption_recovery']['parent_cycle']==75 and x['interruption_recovery']['new_cycle']==76" in (D/'startup78.py').read_text()
r=dict(passed=True,time=time.time(),files=[x for x in files if Path(x['path']).parent==OUT],actual78_not_started=True,full77_not_yet_complete=True,scope='Only current78/complete77 paths and metadata, plus prior continuation checkpoint match. Original75->76 interruption preserved; original full reward/replay/history/optimizer/30condition/health checks unchanged.')
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');(D/'FUTURE_REVIEW_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,actual78_not_started=True),indent=2)+'\n')
print('Future78 startup/archive/fullreview sources prepared; no launch')
