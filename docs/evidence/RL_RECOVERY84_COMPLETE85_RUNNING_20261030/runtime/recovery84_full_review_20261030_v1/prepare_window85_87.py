from pathlib import Path
import json,time,hashlib,ast,re,difflib
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;O=B/'runs/parameter_recovery82_84_reward_stability_20261030_v1';OUT=B/'runs/parameter_recovery85_87_reward_stability_20261030_v1'
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
assert read(B/'runs/parameter_partial75_recovery_cycle84_review_20261029_v1/REVIEW.json')['passed']
assert read(O/'REVIEW.json')['passed'] and read(O/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(O/'PLOT_INSPECTION.json')['actual_image_viewed']
assert not (B/'runs/parameter_partial75_recovery_cycle85_20261029_v1/LAUNCH.json').exists()
assert ref(O/'PLAN.json')['sha256']=='ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c'
OUT.mkdir();files=[]
for name in ['audit.py','review_saved.py','wait_register_and_audit.py']:
 src=(O/name).read_text();s=re.sub(r'\b(82|83|84)\b',lambda m:str(int(m[0])+3),src)
 s=s.replace('2026102855','2026102858').replace('82-84','85-87').replace('82-87','85-87').replace('paired82_to84','paired85_to87').replace('first82','first85')
 ast.parse(s);(OUT/name).write_text(s);(OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(src.splitlines(True),s.splitlines(True),fromfile=str(O/name),tofile=str(OUT/name))))
 a=[x.value for x in ast.walk(ast.parse(src)) if isinstance(x,ast.Constant) and type(x.value) in (int,float)];z=[x.value for x in ast.walk(ast.parse(s)) if isinstance(x,ast.Constant) and type(x.value) in (int,float)];assert len(a)==len(z) and all(y=={82:85,83:86,84:87,2026102855:2026102858}.get(x,x) for x,y in zip(a,z))
 files.append(dict(parent=ref(O/name),source=ref(OUT/name)))
plan=read(O/'PLAN.json');plan.update(time=time.time(),cycles=[85,86,87],bootstrap_seed=2026102858,source_sha256=ref(OUT/'audit.py')['sha256'],saved_review_source_sha256=ref(OUT/'review_saved.py')['sha256'],registration_state='Complete84 and original82-84 fully reviewed; no85 launch and no86/87 authorization. All85-87 outcomes future.',registration_progress=read(B/'runs/parameter_partial75_recovery_cycle84_review_20261029_v1/REVIEW.json')['methods'],reason='Preserve all original windows and failures. Register next nonoverlapping85-87 before85 launch, same5percent/nearzero1/5000stratified bootstrap/anchor55 and seed2026102858. Every training cycle still requires a separate evidence-based finite decision; this plan starts no training and does not declare convergence.',previous_plan=ref(O/'PLAN.json'),previous_result=ref(O/'REVIEW.json'),previous_saved_arithmetic=ref(O/'SAVED_ARITHMETIC_REVIEW.json'),waiter_launched=False,waiter_start_policy='After actual85 launch; never launches85/86/87 itself.',run_paths={str(c):str(B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1') for c in [85,86,87]},review_paths={str(c):str(B/f'runs/parameter_partial75_recovery_cycle{c}_review_20261029_v1') for c in [85,86,87]})
for x in plan['anchor_protocol55'].values():assert ref(Path(x['path']))==x
(OUT/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,only_window_cycle_literals_and_bootstrap_seed_changed=True,original_arithmetic_physics_and_thresholds_unchanged=True,automatic_training=False),indent=2)+'\n');print('Prospective85-87 registered before85 launch; not deployed')
