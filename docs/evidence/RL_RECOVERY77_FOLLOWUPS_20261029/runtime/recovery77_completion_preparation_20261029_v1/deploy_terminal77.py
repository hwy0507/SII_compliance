from pathlib import Path
import json,time,hashlib,subprocess,os,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';REV=B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def live(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
assert read(RUN/'startup/REVIEW.json')['passed']
for m in ['vmc','admittance']:
 old=B/f'runs/{m}_recovery76_terminal_followup_20261029_v1';out=B/f'runs/{m}_recovery77_terminal_followup_20261029_v1'
 assert not (out/'LAUNCH.json').exists()
 source=read(out/'SOURCE_REVIEW.json')
 for n,h in source['sources'].items():assert sha(out/n)==h;ast.parse((out/n).read_text())
 assert read(out/'ANCHOR_REVIEW.json')['passed'] and read(out/'ANCHOR_SAVED_REVIEW.json')['passed']
 oldplan=read(old/'PLAN.json');helper=Path(oldplan['helper_runtime'])
 inputs={k:v for k,v in oldplan['inputs'].items() if k.startswith('prior74_') or k.startswith('historical')}
 inputs.update({k:ref(out/n) for k,n in [('anchor_values','anchor76.npz'),('anchor_review','ANCHOR_REVIEW.json'),('anchor_saved_review','ANCHOR_SAVED_REVIEW.json'),('anchor_plan','ANCHOR_PLAN.json'),('source_review','SOURCE_REVIEW.json')]})
 inputs['registration']=ref(RUN/m/'REGISTRATION.json')
 inputs['prior76_review']=ref(old/'REVIEW.json');inputs['prior76_saved_review']=ref(old/'SAVED_VALUES_REVIEW.json')
 plan=dict(time=time.time(),parent_run=str(RUN),parent_review=str(REV),final_checkpoint=str(B/f'runs/parameter_partial75_recovery_cycle77_archive_20261029_v1/{m}/cycle_00077.pt'),learners=read(RUN/'LAUNCH.json')['jobs'],monitor=read(RUN/'MONITOR_LAUNCH.json'),parent_launch_sha256=sha(RUN/'LAUNCH.json'),helper_runtime=str(helper),digest_helper_sha256=oldplan['digest_helper_sha256'],inputs=inputs,sources=source['sources'],focus_replay_indices=oldplan['focus_replay_indices'],fixed_anchor_rows=2274,expected_complete77_terminal_rows=2304,wait_seconds=7200,automatic_training=False,convergence_claim=False,registered_during77=True,registered_before_complete77=True,limitation='Complete76 versus complete77 CPU critic forward on all2274 fixed terminal rows plus allnew30. Original focus unchanged; full population and both replay denominators retained. Original75 interrupted. No gradient causality, physics, optimizer/replay mutation or new convergence threshold.')
 for j in plan['learners']+[plan['monitor']]:live(j)
 for v in inputs.values():assert sha(Path(v['path']))==v['sha256']
 assert not (RUN/'ARCHIVE_REVIEW_FINISHED.json').exists()
 write(out/'PLAN.json',plan)
 with (out/'driver.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(out/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES=''))
 j=dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(out/'PLAN.json'));write(out/'LAUNCH.json',j);print(m,j)
