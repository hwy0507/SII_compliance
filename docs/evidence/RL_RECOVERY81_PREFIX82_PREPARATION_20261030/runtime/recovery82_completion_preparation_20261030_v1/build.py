from pathlib import Path
import ast, difflib, hashlib, json, re, subprocess, time
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
D = Path(__file__).parent
OLD = B / 'runtime/recovery81_completion_preparation_20261030_v1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def sub_once(s, old, new):
    assert s.count(old) == 1, (old, s.count(old))
    return s.replace(old, new)
old = (OLD / 'decision81.py').read_text()
s = old
for before, after in [
    ('prepare_recovery81_20261030_v1', 'prepare_recovery82_20261030_v1'),
    ('parameter_recovery80_loss_', 'parameter_recovery81_loss_'),
    ('parameter_recovery80_task_labels_', 'parameter_recovery81_task_labels_'),
    ('COMPLETE79_80', 'COMPLETE80_81'),
    ('recovery80_terminal_followup_', 'recovery81_terminal_followup_'),
    ('fixed_anchor_rows\']==2364', 'fixed_anchor_rows\']==2394'),
    ('prior80_', 'prior81_'), ('prior80_decision', 'prior81_decision')]:
    s = s.replace(before, after)
s = re.sub('cycle80|cycle81', lambda m: {'cycle80': 'cycle81', 'cycle81': 'cycle82'}[m[0]], s)
s = s.replace("prior=B/'runtime/recovery80_abort_aware_decision_20261030_v2/DECISION80.json'", "prior=B/'runtime/recovery81_completion_preparation_20261030_v1/DECISION81.json'")
s = sub_once(s, "old['parent_cycle']==79 and old['new_cycle']==80 and old['decision_rule_version']==2 and old['prior_safety_abort_preserved']", "old['parent_cycle']==80 and old['new_cycle']==81 and not old['configuration_changed'] and not old['automatic_followup']")
s = sub_once(s, "for m in ['impedance','admittance','vmc']:required['restore_'+m]", "for suffix,name in [('result','REVIEW.json'),('saved','SAVED_ARITHMETIC_REVIEW.json'),('plot','PLOT_INSPECTION.json')]:required['completed79_81_'+suffix]=required['prospective79_81_plan'].parent/name\n assert read(required['completed79_81_result'])['passed'] and read(required['completed79_81_saved'])['passed'], 'Complete original79-81 arithmetic required'\n for m in ['impedance','admittance','vmc']:required['restore_'+m]")
s = sub_once(s, "'original_window76_78_plot']:assert", "'original_window76_78_plot','completed79_81_plot']:assert")
s = sub_once(s, 'parent_cycle=80,new_cycle=81', 'parent_cycle=81,new_cycle=82')
s = s.replace("D/'DECISION81.json'", "D/'DECISION82.json'")
s = s.replace('original76_78_window_completed_and_reviewed=True', 'original76_78_window_completed_and_reviewed=True,original79_81_window_completed_and_reviewed=True')
s = s.replace('Complete80 archive/review not ready', 'Complete81 archive/review not ready')
s = s.replace('Original80 still running', 'Original81 still running')
s = s.replace('Actual full80 and original76–78 interpretation required', 'Actual full81, original76–78 and completed79–81 interpretation required')
s = s.replace('Full80, original76–78 and exact81 readiness checked', 'Full81, original76–78, completed79–81 and exact82 readiness checked')
s = s.replace('Require full80 interpretation AND completed original76–78 statistics', 'Require full81 interpretation AND completed original76–78 and79–81 statistics')
files = []
def save(name, parent, src, new):
    ast.parse(new)
    p = D / name
    with p.open('x') as f: f.write(new)
    (D / (name + '.diff')).write_text(''.join(difflib.unified_diff(src.splitlines(True), new.splitlines(True), fromfile=str(parent), tofile=str(p))))
    files.append(dict(path=str(p), sha256=sha(p), parent_path=str(parent), parent_sha256=sha(parent)))
save('decision82.py', OLD / 'decision81.py', old, s)
old = (OLD / 'launch81.py').read_text()
s = old
for before, after in [('recovery81', 'recovery82'), ('automatic82', 'automatic83'), ('decision81', 'decision82'), ('DECISION81', 'DECISION82'), ('resume_recovery80.py', 'resume_recovery81.py'), ('startup81.py', 'startup82.py'), ('archive81.py', 'archive82.py'), ('deploy_loss81.py', 'deploy_loss82.py')]:
    s = s.replace(before, after)
s = s.replace("decision['parent_cycle']==80 and decision['new_cycle']==81", "decision['parent_cycle']==81 and decision['new_cycle']==82")
s = s.replace('full80 reviewed decision', 'full81 and completed79-81 reviewed decision').replace('Finite81', 'Finite82')
save('launch82.py', OLD / 'launch81.py', old, s)
old = (OLD / 'deploy_loss81.py').read_text()
s = old.replace('cycle81', 'cycle82').replace('recovery81_loss_', 'recovery82_loss_')
save('deploy_loss82.py', OLD / 'deploy_loss81.py', old, s)
(D / 'LAUNCH_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True, time=time.time(), files=files,
    requires_complete81_and_original79_81_result=True, exact_prospective_plan_preserved=True,
    parent81_driver81_verified=True, automatic_training=False), indent=2) + '\n')
for name, expected in [('decision82.py', 'Complete81 archive/review not ready'), ('launch82.py', 'Explicit reviewed DECISION82 required'), ('deploy_loss82.py', 'LAUNCH.json')]:
    run = subprocess.run([str(B / 'env/bin/python'), str(D / name)], capture_output=True, text=True)
    assert run.returncode != 0 and expected in run.stderr, (name, run.stderr)
    (D / (name + '.REJECTION.json')).write_text(json.dumps(dict(passed=True, time=time.time(), source_sha256=sha(D / name), returncode=run.returncode, stderr=run.stderr, missing_prerequisite=expected), indent=2) + '\n')
assert not (D / 'DECISION82.json').exists()
assert not (B / 'runs/parameter_partial75_recovery_cycle82_20261029_v1/LAUNCH.json').exists()
print('82 decision/launcher/loss prepared; complete81 and original79-81 required; three actual missing-prerequisite refusals passed.')
