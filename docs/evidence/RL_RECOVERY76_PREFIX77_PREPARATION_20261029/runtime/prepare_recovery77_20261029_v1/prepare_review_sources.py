from pathlib import Path
import ast,difflib,json,time,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;old=B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1';out=B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[]
def save(name,source,v,destination=out):
 s=source.read_text();ast.parse(v);(destination/name).write_text(v);(destination/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(source),tofile=str(destination/name))));files.append(dict(path=str(destination/name),name=name,source=str(source),parent_sha256=sha(source),sha256=sha(destination/name)))
paths={'parameter_partial75_recovery_cycle76_20261029_v1':'parameter_partial75_recovery_cycle77_20261029_v1','parameter_partial75_recovery_cycle76_archive_20261029_v1':'parameter_partial75_recovery_cycle77_archive_20261029_v1','parameter_partial75_recovery_cycle76_review_20261029_v1':'parameter_partial75_recovery_cycle77_review_20261029_v1'}
s=(old/'review.py').read_text();v=s
for a,b in paths.items():v=v.replace(a,b)
v=v.replace('cycle_00076.pt','cycle_00077.pt').replace('Cycle76 archive','Cycle77 archive').replace("x['cycle']==76","x['cycle']==77").replace("x['cycles'][-1]['cycle']==76","x['cycles'][-1]['cycle']==77").replace("t['cycle']==76","t['cycle']==77").replace("e['cycle']==76","e['cycle']==77").replace('Exact parent is explicitly audited partial75; it is not a complete cycle.','Exact parent is complete recovery76; incomplete75 remains absent from complete-cycle history.')
v=v.replace("reg['interrupted_episode_recovery']['parent_registration']","reg['post_interruption_continuation']['parent_registration']").replace("old['cycle']==75","old['cycle']==76").replace("old['boundary']=='partial_episode_valid_replay_reset_environment_on_resume'","old['boundary']=='complete_condition_cycle'")
v=v.replace("assert sha(parent)==recovery['checkpoint']['sha256']", "continuation=reg['post_interruption_continuation']\n    assert x['recovery_continuation']==continuation and continuation['parent_cycle']==76 and continuation['new_cycle']==77\n    assert old['interruption_recovery']==recovery and sha(parent)==continuation['checkpoint']['sha256']")
save('review.py',old/'review.py',v)
s=(old/'coordinator.py').read_text();v=s
for a,b in paths.items():v=v.replace(a,b)
v=v.replace("'--cycle','76'","'--cycle','77'");save('coordinator.py',old/'coordinator.py',v)
for n in ['diagnose_published_training_20261025.py','diagnose_serl_training_20261025.py']:
 if (old/n).exists():save(n,old/n,(old/n).read_text())
startup=B/'runtime/parameter75_interruption_recovery_20261029_v1/startup76.py';v=startup.read_text().replace("old['boundary']=='partial_episode_valid_replay_reset_environment_on_resume' and old['cycle']==75 and x['cycle']==76","old['boundary']=='complete_condition_cycle' and old['cycle']==76 and x['cycle']==77").replace("reg['interrupted_episode_recovery']['parent_registration']","reg['post_interruption_continuation']['parent_registration']").replace("old['cycle']==75","old['cycle']==76").replace('cycle_00076','cycle_00077')
v=v.replace("previous=json.loads(Path", "assert x['recovery_continuation']==reg['post_interruption_continuation'] and x['recovery_continuation']['parent_cycle']==76 and x['recovery_continuation']['new_cycle']==77\n previous=json.loads(Path")
save('startup77.py',startup,v,D)
archive=B/'runtime/parameter75_interruption_recovery_20261029_v1/archive76.py';v=archive.read_text()
for a,b in paths.items():v=v.replace(a,b)
v=v.replace("x['cycle']==76","x['cycle']==77").replace("and x['interruption_recovery']['parent_cycle']==75", "and x['interruption_recovery']['parent_cycle']==75 and x['recovery_continuation']['parent_cycle']==76").replace('cycle_00076','cycle_00077').replace('cycle=76','cycle=77')
save('archive77.py',archive,v,D)
report=dict(passed=True,time=time.time(),files=[f for f in files if Path(f['path']).parent==out],actual77_not_started=True,full76_not_yet_complete=True,scope='Only context paths and explicit complete76 parent/recovery77 metadata adaptation. All original new reward/old replay/history/optimizer/30conditions checks retained. No full77 result.')
(out/'SOURCE_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');(D/'FUTURE_REVIEW_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,actual77_not_started=True),indent=2)+'\n')
# Adapting sources must not introduce accidental claims of a complete75 or change initial historical recovery fields.
assert "recovery['parent_cycle']==75 and recovery['new_cycle']==76" in (out/'review.py').read_text()
assert "x['interruption_recovery']['parent_cycle']==75 and x['interruption_recovery']['new_cycle']==76" in (D/'startup77.py').read_text()
print('Future77 startup/archive/fullreview sources prepared; not launched')
