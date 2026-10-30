from pathlib import Path
import json,time,hashlib,re,ast,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_recovery76_78_reward_stability_20261029_v1';OUT=B/'runs/parameter_recovery79_81_reward_stability_20261030_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def read(p):return json.loads(p.read_text())
assert not (B/'runs/parameter_partial75_recovery_cycle79_20261029_v1/LAUNCH.json').exists()
assert read(OLD/'REVIEW.json')['passed'] and read(OLD/'SAVED_ARITHMETIC_REVIEW.json')['passed']
OUT.mkdir(exist_ok=False);files=[]
for n in ['audit.py','review_saved.py','wait_register_and_audit.py']:
 s=(OLD/n).read_text();v=re.sub('76|77|78',lambda m:{'76':'79','77':'80','78':'81'}[m[0]],s)
 v=v.replace('parameter_recovery79_81_reward_stability_20261029_v1','parameter_recovery79_81_reward_stability_20261030_v1')
 # Correct prospective timing wording; this window is now registered after78, before79.
 v=v.replace('first79 protocol is also compared against frozen55','first79 protocol is also compared against frozen55')
 ast.parse(v);(OUT/n).write_text(v);(OUT/(n+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(OLD/n),tofile=str(OUT/n))));files.append(dict(name=n,parent=ref(OLD/n),sha256=sha(OUT/n)))
p=read(OLD/'PLAN.json');p.update(cycles=[79,80,81],time=time.time(),source_sha256=sha(OUT/'audit.py'),registration_state='Complete78 audited; no79 training launched,80/81 not prepared or authorized automatically. Prospective next three complete cycles, conditional on later finite decisions.',registration_progress=read(B/'runs/parameter_partial75_recovery_cycle78_review_20261029_v1/REVIEW.json')['methods'],reason='Original76–78 fully retained: I nearzero unassessable relative stability, A fails5percent, V reward passes but loss health unproven. New prospective79–81 is additional evidence, not replacement or removal of any earlier result. Same5percent/nearzero1/bootstrap5000/seed2026102855/anchor55; no automatic training or stop.',previous_plan=ref(OLD/'PLAN.json'),previous_result=ref(OLD/'REVIEW.json'),previous_saved_arithmetic=ref(OLD/'SAVED_ARITHMETIC_REVIEW.json'),waiter_start_policy='After actual79 launch; never launches79/80/81 itself.',run_paths={str(c):str(B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1') for c in [79,80,81]},review_paths={str(c):str(B/f'runs/parameter_partial75_recovery_cycle{c}_review_20261029_v1') for c in [79,80,81]})
(OUT/'PLAN.json').write_text(json.dumps(p,indent=2)+'\n');(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,original_math_and_gates_retained=True,original76_78_result_retained=True,registered_before79=True,automatic_training=False),indent=2)+'\n');print('Prospective79–81 registered before79; no automatic80/81')
