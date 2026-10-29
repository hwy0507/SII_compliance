from pathlib import Path
import json,hashlib,os,subprocess,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');W=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1';R=B/'runs/parameter_capacity_pool30_cycle74_20261026_v1';D=B/'runtime/prepare_parameter74_20261028_v1/DECISION74.json'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 f=p.read_text().rsplit(')',1)[1].split();return f[19]==j['proc_start_ticks'] and f[0]!='Z'
d=read(D);assert d['passed'] and d['parent_cycle']==73 and d['new_cycle']==74 and not d['automatic_followup'];assert d['plot_inspected'] and not d['convergence_claim']
for x in d['evidence'].values():assert sha(Path(x['path']))==x['sha256']
assert d['evidence']['future_window74_76_plan']==dict(path=str(W/'PLAN.json'),sha256=sha(W/'PLAN.json'))
assert sha(W/'PLAN.json')=='d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703'
for key,name in [('reward_window71_73','REVIEW.json'),('reward_window71_73_saved','SAVED_ARITHMETIC_REVIEW.json'),('reward_window71_73_plot','PLOT_INSPECTION.json')]:assert Path(d['evidence'][key]['path'])==B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'/name
assert read(B/'runs/parameter_capacity71_73_reward_stability_20261028_v1/SAVED_ARITHMETIC_REVIEW.json')['passed']
for item in read(W/'SOURCE_REVIEW.json')['files']:assert sha(W/item['name'])==item['sha256']
a=read(R/'LAUNCH.json');assert a['new_cycles']==1 and not a['automatic_followup'] and len(a['jobs'])==3 and all(live(j) for j in a['jobs'])
assert not (W/'LAUNCH.json').exists() and not (W/'REGISTRATION.json').exists() and not (W/'REVIEW.json').exists()
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
with (W/'driver.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(W/'wait_register_and_audit.py')],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
j=dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(W/'PLAN.json'),actual74_launch_sha256=sha(R/'LAUNCH.json'),decision74_sha256=sha(D),automatic_training=False,source_sha256=sha(Path(__file__)))
with (W/'LAUNCH.json').open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
assert live(j);print(json.dumps(j,indent=2))
