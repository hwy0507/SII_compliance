from pathlib import Path
import re,ast,json,hashlib,time,difflib
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');rt=b/'runtime';o=b/'runs/serl26_static_preparation_20261027_v1';o.mkdir()
old=rt/'serl_capacity25_monitor_templates_20261027_v1';new=rt/'serl_capacity26_monitor_templates_20261027_v1';new.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def adapt(s):
 s=re.sub(r'(cycle_000|cycle|Cycle|capacity|serl|complete|full|Original|Prepared)(24|25)',lambda m:m[1]+str(int(m[2])+1),s)
 s=re.sub(r"(\['(?:cycle|parent_cycle)'\](?:==|=))(24|25)",lambda m:m[1]+str(int(m[2])+1),s)
 s=s.replace('len(terminal)==780','len(terminal)==810').replace('terminal_count=780','terminal_count=810')
 return s
records=[];diffs=[]
manifest=json.loads((old/'MANIFEST.json').read_text())
for name,h in manifest['templates'].items():assert sha(old/name)==h
files=[(rt/name,rt/adapt(name)) for name in ['prepare_serl_capacity25_20261027.py','launch_serl_capacity25_20261027.py','setup_serl_capacity25_monitors_20261027.py','wait_prepare_serl_capacity25_20261027.py']]+[(old/name,new/name) for name in ['startup_review.py','review.py','coordinator.py','diagnose.py']]
for source,target in files:
 assert not target.exists();before=source.read_text();after=adapt(before);ast.parse(after);target.write_text(after)
 records.append(dict(source=str(source),source_sha256=sha(source),path=str(target),sha256=sha(target)))
 diffs.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(source),tofile=str(target)))
p=(rt/'prepare_serl_capacity26_20261027.py').read_text()
assert "oldname='serl_capacity_batch65536_cycle25_20261027_v1'" in p
assert "name='serl_capacity_batch65536_cycle26_20261027_v1'" in p
assert "x['cycle']==25" in p and "stage['parent_cycle']=25" in p
assert "p['replay_capacity_stage']['parent_cycle']==23" in p and "p['batch_size_stage']==read(parent)['batch_size_stage']" in p
assert "os.sched_setaffinity(0,{0})" in p and '2_000_000' in p
assert 'setup_serl_capacity26_monitors_20261027.py' in (rt/'launch_serl_capacity26_20261027.py').read_text()
assert 'serl_capacity26_monitor_templates_20261027_v1' in (rt/'setup_serl_capacity26_monitors_20261027.py').read_text()
for name in ['review.py','startup_review.py']:
 s=(new/name).read_text();assert "old['cycle']==25" in s and "['parent_cycle']==25" in s
 assert "reg['replay_capacity_stage']==parent_reg['replay_capacity_stage']" in s
 assert "['parent_cycle']==23" in s and 'new_capacity=2_000_000' in s
assert 'len(terminal)==810' in (new/'diagnose.py').read_text()
(new/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),templates={n:sha(new/n) for n in ['startup_review.py','review.py','coordinator.py','diagnose.py']},historical_capacity_entry=23,diagnostic_terminal_count=810),indent=2)+'\n')
(o/'SOURCE.diff').write_text(''.join(diffs))
(o/'REGISTRATION.json').write_text(json.dumps(dict(time=time.time(),parent_cycle=25,next_cycle=26,files=records,templates_manifest_sha256=sha(new/'MANIFEST.json'),static_checks_passed=True,learner_source_unchanged=True,optimizer_updates=0,physics_steps=0,actual_parent_restore_executed=False,waiter_launched=False,training_launched=False,next_action='After actual25 launch, register bounded wait for complete25 review and released-CPU scheduler; then run check-only, inspect science and decide finite26 separately. No automatic training.'),indent=2)+'\n')
print('Prepared8 scripts/templates; no waiter or training launched')
