from pathlib import Path
import json,hashlib,time,ast,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runs/parameter_recovery79_81_reward_stability_20261030_v1';out=B/'runs/parameter_recovery82_84_reward_stability_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert read(old/'REVIEW.json')['passed'] and read(old/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(old/'PLOT_INSPECTION.json')['actual_image_viewed']
assert read(B/'runs/parameter_partial75_recovery_cycle81_review_20261029_v1/REVIEW.json')['passed']
assert not (B/'runs/parameter_partial75_recovery_cycle82_20261029_v1/LAUNCH.json').exists()
out.mkdir()
files=[]
for name in ['audit.py','review_saved.py','wait_register_and_audit.py']:
 s=(old/name).read_text();n=s.replace('79-81','82-84').replace('[79, 80, 81]','[82, 83, 84]').replace('[79,80,81]','[82,83,84]').replace('paired79_to81','paired82_to84').replace('first79 protocol','first82 protocol')
 if name=='wait_register_and_audit.py':
  needle="    subprocess.run([str(B/'env/bin/python'), str(source), '--root', str(root)], check=True)"
  assert n.count(needle)==1
  n=n.replace(needle,needle+"\n    assert sha(root/'review_saved.py') == plan['saved_review_source_sha256']\n    subprocess.run([str(B/'env/bin/python'), str(root/'review_saved.py')], check=True)")
 ast.parse(n);(out/name).write_text(n);(out/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),n.splitlines(True),fromfile=str(old/name),tofile=str(out/name))))
 files.append(dict(parent=ref(old/name),new=ref(out/name)))
plan=read(old/'PLAN.json');plan.update(time=time.time(),cycles=[82,83,84],source_sha256=sha(out/'audit.py'),saved_review_source_sha256=sha(out/'review_saved.py'),registration_state='Complete81 and original79-81 fully reviewed; no82 launch,83/84 not prepared or automatically authorized.',registration_progress=read(B/'runs/parameter_partial75_recovery_cycle81_review_20261029_v1/REVIEW.json')['methods'],waiter_launched=False,waiter_start_policy='After actual82 launch; never launches82/83/84 itself.',previous_plan=ref(old/'PLAN.json'),previous_result=ref(old/'REVIEW.json'),previous_saved_arithmetic=ref(old/'SAVED_ARITHMETIC_REVIEW.json'))
plan['run_paths']={str(c):str(B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1') for c in [82,83,84]};plan['review_paths']={str(c):str(B/f'runs/parameter_partial75_recovery_cycle{c}_review_20261029_v1') for c in [82,83,84]}
put(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,changes='Only future window identifiers/labels and one sequential independent saved-review call; unchanged seed5000 bootstrap,nearzero1,relative5%,real aborts and lengths.',automatic_training=False))
put(out/'PLAN.json',plan)
print(json.dumps(dict(registered=True,plan=ref(out/'PLAN.json'),training_started=False)))
