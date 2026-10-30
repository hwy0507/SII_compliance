from pathlib import Path
import json,time,hashlib,os,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');run=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
for m in ['vmc','admittance']:
 old=B/f'runs/{m}75_terminal_anchor_followup_20261028_v1';out=B/f'runs/{m}_recovery76_terminal_followup_20261029_v1'
 assert not (out/'PLAN.json').exists() and not (out/'LAUNCH.json').exists()
 for n in ['ANCHOR_REVIEW.json','ANCHOR_SAVED_REVIEW.json']:assert read(out/n)['passed']
 prior=read(old/'PLAN.json');p=dict(time=time.time(),parent_run=str(run),parent_review=str(B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1'),final_checkpoint=str(B/f'runs/parameter_partial75_recovery_cycle76_archive_20261029_v1/{m}/cycle_00076.pt'),learners=read(run/'LAUNCH.json')['jobs'],monitor=read(run/'MONITOR_LAUNCH.json'),parent_launch_sha256=sha(run/'LAUNCH.json'),helper_runtime=prior['helper_runtime'],digest_helper_sha256=prior['digest_helper_sha256'],inputs={k:v for k,v in prior['inputs'].items() if k not in ['registration','anchor_values','anchor_review','anchor_saved_review']},sources={n:sha(out/n) for n in prior['sources']},focus_replay_indices=prior['focus_replay_indices'],fixed_anchor_rows=2244,expected_complete76_terminal_rows=2274,wait_seconds=7200,automatic_training=False,convergence_claim=False,registered_during76=True,registered_before_complete76=True,limitation='Audited retained partial75 versus full recovery76 CPU critic forward on all2244 fixed terminal rows plus allnew30. No complete75 claim. Original focus unchanged, full population and both replay denominators retained; no gradient causality, physics, optimizer or replay mutation, or new convergence threshold.')
 p['inputs'].update(registration=ref(run/m/'REGISTRATION.json'),anchor_values=ref(out/'anchor_partial75.npz'),anchor_review=ref(out/'ANCHOR_REVIEW.json'),anchor_saved_review=ref(out/'ANCHOR_SAVED_REVIEW.json'),anchor_plan=ref(out/'ANCHOR_PLAN.json'))
 for v in p['inputs'].values():assert sha(Path(v['path']))==v['sha256']
 for n,h in p['sources'].items():assert sha(out/n)==h
 for j in p['learners']+[p['monitor']]:
  s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
 assert not (run/'ARCHIVE_REVIEW_FINISHED.json').exists()
 write(out/'PLAN.json',p)
 with (out/'driver.log').open('x') as f:c=subprocess.Popen([str(B/'env/bin/python'),str(out/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 receipt=dict(pid=c.pid,proc_start_ticks=Path(f'/proc/{c.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(out/'PLAN.json'));write(out/'LAUNCH.json',receipt);print(m,json.dumps(receipt))
