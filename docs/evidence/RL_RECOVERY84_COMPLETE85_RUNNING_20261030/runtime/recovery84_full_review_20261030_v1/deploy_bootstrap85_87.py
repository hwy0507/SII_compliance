from pathlib import Path
import json,time,hashlib,ast,difflib,subprocess,sys
B=Path(__file__).resolve().parents[2];W=B/'runs/parameter_recovery85_87_reward_stability_20261030_v1';O=B/'runs/recovery82_84_bootstrap_scalar_review_20261030_v1';D=B/'runs/recovery85_87_bootstrap_scalar_review_20261030_v1'
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
launch=read(W/'LAUNCH.json');s=Path(f'/proc/{launch["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==launch['proc_start_ticks'] and s[0]!='Z'
assert read(W/'PLAN.json')['cycles']==[85,86,87] and read(W/'PLAN.json')['bootstrap_seed']==2026102858
assert not (B/'runs/parameter_partial75_recovery_cycle85_20261029_v1/ARCHIVE_REVIEW_FINISHED.json').exists()
D.mkdir();files=[]
for name in ['audit.py','wait.py']:
 src=(O/name).read_text();s=src.replace('2026102855','2026102858').replace('82_84','85_87');ast.parse(s);(D/name).write_text(s);(D/(name+'.diff')).write_text(''.join(difflib.unified_diff(src.splitlines(True),s.splitlines(True),fromfile=str(O/name),tofile=str(D/name))));files.append(dict(parent=ref(O/name),source=ref(D/name)))
pre=dict(time=time.time(),registered_before_complete85_87=True,window=str(W),inputs=[ref(W/n) for n in ['PLAN.json','LAUNCH.json','wait_register_and_audit.py','audit.py','review_saved.py']]+[ref(D/n) for n in ['audit.py','wait.py']]+[ref(O/'REVIEW.json')],original_waiter=launch,original_deadline_unix=launch['time']+14400,automatic_training=False,limitation='Prospective numerical supplement for original85-87 bootstrap: same seed2026102858,5000stratified draws,real outcomes and episode lengths. Independent math.fsum/manual quantile, shared NumPy RNG. Original deadline preserved; not independent training seeds, not a convergence gate; no scientific dispatch.')
(D/'PRE_REGISTRATION.json').write_text(json.dumps(pre,indent=2)+'\n');(D/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,only_window_name_and_seed_changed=True),indent=2)+'\n')
with (D/'driver.log').open('x') as f:p=subprocess.Popen([sys.executable,str(D/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(D/'LAUNCH.json').write_text(json.dumps(dict(time=time.time(),pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],automatic_training=False),indent=2)+'\n');print('85-87 scalar bootstrap supplement waiting under original deadline')
