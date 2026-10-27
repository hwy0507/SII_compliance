from pathlib import Path
import json,hashlib,re,ast,time,subprocess,os,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';out=B/'runs/admittance41_terminal_anchor_followup_20261027_v1';out.mkdir(exist_ok=False)
os.sched_setaffinity(0,{52})
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
old=B/'runtime/track_vmc39_terminal_anchors_20261027.py';s=old.read_text()
changes={'1603101':'1687237','1164':'1224','1194':'1254','39':'41','38':'40'}
s=re.sub('|'.join(changes),lambda m:changes[m[0]],s).replace('VMC','Admittance').replace("'vmc'","'admittance'").replace('active_short_train_0600','active_long_train_0500')
ast.parse(s);source=B/'runtime/track_admittance41_terminal_anchors_20261027.py';source.write_text(s);(R/'code/mujoco_6d_vmc_benchmark/tools'/source.name).write_text(s)
assert 'fixed1224' in s and 'terminal41_values.npz' in s and 'old40_denominator' in s and 'len(terminal) == 1254' in s
subprocess.run([str(B/'env/bin/python'),str(source),'--help'],check=True,stdout=subprocess.DEVNULL)
anchor=B/'runs/admittance39_40_terminal_concentration_20261027_v1';formal=B/'runs/parameter_capacity_pool30_cycle41_20261026_v1/admittance/train';full=B/'runs/parameter_capacity_pool30_cycle41_review_20261026_v1'
assert not (full/'FINISHED.json').exists();assert Path('/proc/2369249').exists()
plan=dict(time=time.time(),cycle=41,anchor_cycle=40,focus_replay_index=1687237,expected_old_terminal_count=1224,source_sha256=sha(source),saved_review_source=ref(B/'runtime/review_parameter_terminal_anchor_followup_20261027.py'),inputs=dict(anchor_registration=ref(anchor/'REGISTRATION.json'),anchor_values=ref(anchor/'cycle40_terminal_values.npz'),anchor_review=ref(anchor/'REVIEW.json'),saved_value_review=ref(anchor/'SAVED_VALUE_REVIEW.json')),registration_state='Formal41 already running, full41 unavailable; defined after complete40 diagnostic, not before training41',registration_progress=json.loads((formal/'PROGRESS.json').read_text()),optimizer_updates=0,new_physics=0,wait_seconds=7200,execution_timeout_seconds=600,reason='Track all1224 fixed40 inputs/actions/rewards/masks and old denominator to assess whether broad retained-row error growth recovers in41. Primary result is all rows; auxiliary fixed worst40 row1687237 long0500 accounts for only6.32% of40 terminal contribution. Reuse40 predictions, one41 CPU forward,0updates/physics/replaywrites and no automatic training.')
(out/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
wold=B/'runtime/wait_vmc39_terminal_anchors_20261027.py';w=wold.read_text().replace('vmc39_terminal_anchor_followup','admittance41_terminal_anchor_followup').replace('track_vmc39_terminal_anchors','track_admittance41_terminal_anchors').replace("'1387247fde9946a5792fd2b6ee9854b69735f4af948800f5c4f0b08a2d825786'",repr(sha(out/'PLAN.json')))
w=w.replace('cycle39','cycle41').replace('cycle_00039','cycle_00041').replace('/vmc/','/admittance/').replace('health39','health41').replace('review39','review41').replace('checkpoint39','checkpoint41').replace('Complete39 fixed1164','Complete41 fixed1224')
ast.parse(w);wait=B/'runtime/wait_admittance41_terminal_anchors_20261027.py';wait.write_text(w)
assert 'vmc39' not in w and '/vmc/' not in w and 'cycle39' not in w and sha(out/'PLAN.json') in w
(out/'SOURCE.diff').write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),s.splitlines(True),fromfile=str(old),tofile=str(source)))+''.join(difflib.unified_diff(wold.read_text().splitlines(True),w.splitlines(True),fromfile=str(wold),tofile=str(wait))))
with (out/'wait.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(wait)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
(out/'LAUNCH.json').write_text(json.dumps(dict(time=time.time(),pid=p.pid,wait_source_sha256=sha(wait),plan_sha256=sha(out/'PLAN.json'),static_checks_passed=True,automatic_training=False),indent=2)+'\n');print('Original fixed1224 follow41 waiter',p.pid)
