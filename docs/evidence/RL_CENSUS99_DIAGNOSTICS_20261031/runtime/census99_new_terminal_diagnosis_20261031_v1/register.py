from pathlib import Path
import json,time,sys,subprocess,ast
D=Path(__file__).resolve().parent;B=D.parents[1];sys.path.insert(0,str(D));import wait_diagnosis as w
O=w.O;R=w.R;F=w.F;C=w.C;V=w.V;T=B/'runtime/census99_continuation_20261031_v1';PRE=B/'runs/census98_new_terminal_diagnosis_20261031_v1';Fplan=w.read(F/'PLAN.json')
assert w.read(O/'REPORT_CONTRACT_REVIEW.json')['passed'];methods={};fixed=[]
for m,e in Fplan['methods'].items():
 methods[m]=dict(old_terminal_rows=e['terminal_rows'],prediction_block_boundaries=e['prediction_block_boundaries'])
 fixed.extend([PRE/f'reference98/{m}_values.npz',PRE/f'reference98/{m}_REVIEW.json',R/m/'REGISTRATION.json'])
assert sum(e['old_terminal_rows'] for e in methods.values())==8803
fixed.extend([PRE/'reference98/REVIEW.json',PRE/'DIAGNOSIS.json',PRE/'SAVED_ARITHMETIC_REVIEW.json',B/'runs/census97_new_terminal_diagnosis_20261031_v1/BIND_REPAIR_REVIEW.json',T/'SCIENTIFIC_DECISION.json',T/'SOURCES.json',F/'PLAN.json',C/'WAIT_PLAN.json',O/'REPORT_CONTRACT_REVIEW.json'])
consumers=[dict(identity=w.read(R/'MONITOR_LAUNCH.json'),finished=str(V/'FINISHED.json')),dict(identity=w.read(F/'PROCESS.json'),finished=str(F/'FINISHED.json')),dict(identity=w.read(C/'PROCESS.json'),finished=str(C/'COMPARISON_FINISHED.json'))]
for j in consumers:w.live(j['identity']);assert not Path(j['finished']).exists()
for p in D.glob('*.py'):ast.parse(p.read_text())
deadline=min(w.read(F/'PLAN.json')['wait_deadline_unix'],w.read(C/'WAIT_PLAN.json')['deadline']);assert deadline==min(j['time'] for j in w.read(R/'LAUNCH.json')['jobs'])+14400
w.put(O/'WAIT_PLAN.json',dict(time=time.time(),methods=methods,source_hashes={p.name:w.sha(p) for p in sorted(D.glob('*.py'))},fixed_inputs={str(p):w.sha(p) for p in fixed},runtime_hashes=w.read(T/'SOURCES.json')['files'],restore_runtime=str(T),original_consumers=consumers,deadline_unix=deadline,analysis_budget_seconds=1200,physics_steps=0,optimizer_updates=0,automatic100=False,scope='Wait for actual99 core, fixed8803 old-terminal and all90/cache reviews, then build8893 terminal reference and diagnose all90 new99 rows. Root/per-method fixed report schema checked before any inference; original97 binding failure/repair retained. No100 launch.'))
repo=B/'repository/SII_compliance';w.put(D/'REMOTE_START.json',dict(time=time.time(),main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=repo,text=True).strip(),baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=repo,text=True).strip(),actual_query_fetch_read_both=True))
print('New99 terminal consumer registered; no inference')
