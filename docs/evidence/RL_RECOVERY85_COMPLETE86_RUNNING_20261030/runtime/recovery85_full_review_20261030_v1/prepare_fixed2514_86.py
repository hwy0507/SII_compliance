from pathlib import Path
import json,time,hashlib,re,ast,difflib,subprocess,os
B=Path(__file__).resolve().parents[2];D=B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1';R=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1';full=B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1'
def read(p):return json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert read(B/'runtime/recovery86_followups_20261030_v1/FINISHED.json')['passed'];assert not (R/'ARCHIVE_REVIEW_FINISHED.json').exists();assert not (D/'PLAN.json').exists()
launch=read(R/'LAUNCH.json');monitor=read(R/'MONITOR_LAUNCH.json')
for j in launch['jobs']:
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
D.mkdir();inputs={}
for m in ['vmc','admittance']:
 old=B/f'runs/{m}_recovery85_terminal_followup_20261029_v1';new=B/f'runs/{m}_recovery86_terminal_followup_20261029_v1'
 for n in ['anchor84.npz','values.npz','REVIEW.json','SAVED_VALUES_REVIEW.json']:inputs[m+'_prior_'+n]=ref(old/n)
 for n in ['anchor85.npz','ANCHOR_REVIEW.json','ANCHOR_SAVED_REVIEW.json','PLAN.json']:inputs[m+'_current_'+n]=ref(new/n)
prior=B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1';inputs['prior_fixed2514']=ref(prior/'REVIEW.json');inputs['prior_fixed2514_saved']=ref(prior/'SAVED_REVIEW.json')
plan=dict(time=time.time(),parent_run=str(R),parent_review=str(full),methods=['vmc','admittance'],fixed_rows=2514,all_critics=[0,1,2,3,4],checkpoint_cycles=[84,85,86],complete86_rows=2574,monitor=monitor,learners=launch['jobs'],original_deadline_unix=monitor['time']+14400,registered_during86=True,registered_before_complete86=True,inputs=inputs,reason='Extend original fixed2514/all5 cohort through86 after full85 VMC recovery/A regression observed; retain all old rows and all30new84 cohort. Saved-value arithmetic only, no new forward/physics/update or health threshold, no automatic87.',new_physics=0,new_network_forward=0,optimizer_updates=0,automatic_training=False)
put(D/'PLAN.json',plan)
old=B/'runs/recovery82_84_fixed_terminal_critic_followup_20261030_v1/audit.py';s=old.read_text();mapping={'2454':'2514','2484':'2544','2514':'2574','82':'84','83':'85','84':'86'};t=re.sub('2454|2484|2514|82|83|84',lambda m:mapping[m[0]],s)
t=t.replace("plan=read(D/'PLAN.json')","plan=read(D/'PLAN.json')\nassert (B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1/FINISHED.json').exists(),'Complete86 fixed2514 result not ready'")
t=t.replace("percritic=[];rows=[]","cohort=read(B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1/REVIEW.json')['methods'][m]['all30_new84'];condition84={r['index']:r['condition84'] for r in cohort};assert len(condition84)==30\n percritic=[];rows=[]")
t=t.replace("rec=dict(replay_index=int(idx),reward=float(reward[j]),masks=mask[:,j].tolist())","rec=dict(replay_index=int(idx),condition84=condition84.get(int(idx)),cohort='new84' if int(idx) in condition84 else 'before84',reward=float(reward[j]),masks=mask[:,j].tolist())")
t=t.replace("methods[m]=dict(critics=percritic,total_sse=totals,","methods[m]=dict(critics=percritic,total_sse=totals,all30_new84=[r for r in rows if r['cohort']=='new84'],")
ast.parse(t);(D/'audit.py').write_text(t);(D/'audit.py.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile=str(old),tofile=str(D/'audit.py'))))
oldwait=prior/'wait.py';s=oldwait.read_text();t=s.replace('recovery85_terminal','recovery86_terminal').replace('Original85 monitor','Original86 monitor');ast.parse(t);(D/'wait.py').write_text(t);(D/'wait.py.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile=str(oldwait),tofile=str(D/'wait.py'))))
put(D/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),sources=[ref(D/n) for n in ['audit.py','wait.py']],old_source=ref(old),old_wait_source=ref(oldwait),same_fixed2514_three_checkpoints_all5=True,all30new84_retained=True))
p=subprocess.run([str(B/'env/bin/python'),str(D/'audit.py')],capture_output=True,text=True);assert p.returncode!=0 and 'Complete86 fixed2514 result not ready' in p.stderr and not (D/'REVIEW.json').exists();put(D/'INCOMPLETE86_REJECTION.json',dict(passed=True,time=time.time(),exit_code=p.returncode,stderr=p.stderr))
with (D/'driver.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(D/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
put(D/'LAUNCH.json',dict(time=time.time(),pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],source_sha256=ref(D/'wait.py')['sha256'],automatic_training=False));print('Prospective84/85/86 fixed2514 all5 followup registered and waiting; no automatic87')
