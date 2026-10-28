from pathlib import Path
import json,hashlib,time,os,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/vmc66_terminal_anchor_followup_20261028_v1';run=B/'runs/parameter_capacity_pool30_cycle66_20261026_v1';helper=B/'runtime/parameter_capacity_pool30_cycle66_20261026_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,v):
 with p.open('x') as f:f.write(json.dumps(v,indent=2)+'\n')
old=read(B/'runs/vmc65_terminal_anchor_followup_20261028_v1/PLAN.json');jobs=read(run/'LAUNCH.json')['jobs'];monitor=read(run/'MONITOR_LAUNCH.json')
for j in jobs+[monitor]:
 st=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert st[19]==j['proc_start_ticks'] and st[0]!='Z'
assert not(run/'ARCHIVE_REVIEW_FINISHED.json').exists();assert read(out/'ANCHOR_REVIEW.json')['passed'] and read(out/'ANCHOR_SAVED_REVIEW.json')['passed']
inputs={k:ref(p) for k,p in {'registration':run/'vmc/REGISTRATION.json','anchor_values':out/'anchor65.npz','anchor_review':out/'ANCHOR_REVIEW.json','anchor_saved_review':out/'ANCHOR_SAVED_REVIEW.json','prior65_review':B/'runs/vmc65_terminal_anchor_followup_20261028_v1/REVIEW.json'}.items()};inputs['historical58_focus_context']=old['inputs']['historical58_focus_context'];assert ref(Path(inputs['historical58_focus_context']['path']))==inputs['historical58_focus_context']
plan=dict(time=time.time(),parent_run=str(run),parent_review=str(B/'runs/parameter_capacity_pool30_cycle66_review_20261026_v1'),final_checkpoint=str(B/'runs/parameter_capacity_pool30_cycle66_archive_20261026_v1/vmc/cycle_00066.pt'),learners=jobs,monitor=monitor,parent_launch_sha256=sha(run/'LAUNCH.json'),helper_runtime=str(helper),digest_helper_sha256=sha(helper/'validate_published_finite_check_20261025.py'),inputs=inputs,sources={n:sha(out/n) for n in ['track.py','review_values.py','wait.py']},focus_replay_indices=old['focus_replay_indices'],fixed_anchor_rows=1974,expected_complete66_terminal_rows=2004,registered_during66=True,registered_before_complete66=True,wait_seconds=7200,automatic_training=False,convergence_claim=False,limitation='Complete65 vs complete66 frozen CPU critic forward on all1974 fixed65 terminal observations/actions/rewards/masks plus allnew30. Registered during66 beforecompletion, notbeforetraining. Same3 historical focus and58 short0600 failure/short0200 success retained. Allrows old/current denominators; no online loss/gradient causal claim, no optimization/physics/replay mutation or new stopping threshold.')
write(out/'PLAN.json',plan)
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (out/'driver.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(out/'wait.py')],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
st=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split();j=dict(pid=p.pid,proc_start_ticks=st[19],time=time.time(),plan_sha256=sha(out/'PLAN.json'));write(out/'LAUNCH.json',j);print(json.dumps(j,indent=2))
