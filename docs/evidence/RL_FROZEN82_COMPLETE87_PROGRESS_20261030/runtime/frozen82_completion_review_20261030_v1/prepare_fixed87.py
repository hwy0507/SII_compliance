from pathlib import Path
import json,time,hashlib,subprocess,sys,os,difflib,ast
D=Path(__file__).parent;B=D.parents[1];OLD=B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1';O=B/'runs/recovery84_87_fixed_terminal_critic_followup_20261030_v1'
O.mkdir(exist_ok=False)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
root=B/'runs/parameter_partial75_recovery_cycle87_20261029_v1';review=B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1'
assert not (review/'FINISHED.json').exists()
for m in ['impedance','admittance','vmc']:assert not (root/m/'train/FINISHED.json').exists()
s=(OLD/'audit.py').read_text();original=s
s=s.replace("os.sched_setaffinity(0,{3})","os.sched_setaffinity(0,{11})")
s=s.replace('cycle86_review_','cycle87_review_').replace('Complete86 fixed2514','Complete87 fixed2514').replace("new=B/f'runs/{m}_recovery86_","new=B/f'runs/{m}_recovery87_")
s=s.replace("with np.load(new/'anchor85.npz'", "with np.load(new/'anchor86.npz'")
s=s.replace(" np.testing.assert_array_equal(a['masks'],v['masks'][:,:2514]);np.testing.assert_array_equal(a['masks'],anchor['masks'][:,:2514]);np.testing.assert_array_equal(prior['q_after'],v['q_before']);np.testing.assert_array_equal(anchor['q_after'],v['q_before'])", " np.testing.assert_array_equal(a['masks'],v['masks'][:,:2514]);np.testing.assert_array_equal(a['masks'],anchor['masks'][:,:2514]);np.testing.assert_array_equal(anchor['q_after'],v['q_before'])\n with np.load(B/f'runs/{m}_recovery86_terminal_followup_20261029_v1/values.npz',allow_pickle=False) as z:middle={k:z[k].copy() for k in z.files}\n np.testing.assert_array_equal(middle['q_after'],v['q_before']);np.testing.assert_array_equal(prior['q_after'],middle['q_before'])")
s=s.replace("assert len(v['indices'])==2574 and len(v['q_before'][0])==2544", "assert len(v['indices'])==2604 and len(v['q_before'][0])==2574")
s=s.replace("'86':v['q_after'][:,:2514].astype(float)","'86':middle['q_after'][:,:2514].astype(float),'87':v['q_after'][:,:2514].astype(float)")
s=s.replace("rec['delta84_to86']=rec['sse86']-rec['sse84'];percritic.append(rec)","rec['delta84_to86']=rec['sse86']-rec['sse84'];rec['delta86_to87']=rec['sse87']-rec['sse86'];percritic.append(rec)")
s=s.replace('checkpoint86=', 'checkpoint87=').replace('across84/85/86. Registered during86 after full85 degradation known;', 'across84/85/86/87. Registered during87 after full86 VMC improvements and Acritic4 regression known;').replace("for cycle in ['84','85','86']:","for cycle in ['84','85','86','87']:")
assert 'cycle86_review_' not in s and "len(v['indices'])==2604" in s
ast.parse(s);(O/'audit.py').write_text(s);(O/'audit.py.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='fixed84_86',tofile='fixed84_87')))
wait=(OLD/'wait.py').read_text().replace('recovery86_terminal','recovery87_terminal').replace('Original86 monitor','Original87 monitor')
wait=wait.replace(" assert read(D/'REVIEW.json')['passed'] and read(D/'SAVED_REVIEW.json')['passed']"," assert read(D/'REVIEW.json')['passed'] and read(D/'SAVED_REVIEW.json')['passed']\n subprocess.run([sys.executable,str(D/'plot.py')],check=True)\n assert read(D/'PLOT_REVIEW.json')['passed']")
(O/'wait.py').write_text(wait)
plot='''from pathlib import Path
import json,math,time,hashlib,os
os.sched_setaffinity(0,{11})
D=Path(__file__).parent
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=json.loads((D/'REVIEW.json').read_text());assert r['passed']
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for i,m in enumerate(['vmc','admittance']):
 x=r['methods'][m];cycles=[84,85,86,87]
 for c in x['critics']:axes[i,0].plot(cycles,[c['sse'+str(k)] for k in cycles],'o-',label='critic'+str(c['critic']))
 axes[i,0].set(title=m+' fixed2514: all5 critics',ylabel='In-mask squared error sum');axes[i,0].legend()
 axes[i,1].plot(cycles,[x['total_sse'][str(k)] for k in cycles],'o-');axes[i,1].set(title=m+' total over all5',ylabel='In-mask squared error sum')
 for a in axes[i]:a.set_xticks(cycles);a.grid(alpha=.2)
fig.suptitle('Same2514 inputs/actions/rewards/masks across84-87; descriptive only')
fig.savefig(D/'fixed2514_84_87.png',dpi=150);plt.close(fig)
(D/'PLOT_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),plot_sha256=hashlib.sha256((D/'fixed2514_84_87.png').read_bytes()).hexdigest(),all5critics=True,actual_image_viewed=False),indent=2)+'\\n')
'''
ast.parse(plot);(O/'plot.py').write_text(plot)
inputs={k:v for k,v in read(OLD/'PLAN.json')['inputs'].items() if '_current_' not in k}
inputs.update(prior84_86=ref(OLD/'REVIEW.json'),prior84_86_saved=ref(OLD/'SAVED_REVIEW.json'))
for m in ['vmc','admittance']:
 for n in ['anchor86.npz','ANCHOR_REVIEW.json','ANCHOR_SAVED_REVIEW.json','PLAN.json']:inputs[m+'_current_'+n]=ref(B/f'runs/{m}_recovery87_terminal_followup_20261029_v1'/n)
 for n in ['values.npz','REVIEW.json','SAVED_VALUES_REVIEW.json']:inputs[m+'_middle86_'+n]=ref(B/f'runs/{m}_recovery86_terminal_followup_20261029_v1'/n)
monitor=read(root/'MONITOR_LAUNCH.json')
put(O/'PLAN.json',dict(time=time.time(),parent_run=str(root),parent_review=str(review),methods=['vmc','admittance'],fixed_rows=2514,all_critics=[0,1,2,3,4],checkpoint_cycles=[84,85,86,87],complete87_rows=2604,monitor=monitor,learners=read(root/'LAUNCH.json')['jobs'],original_deadline_unix=monitor['time']+14400,registered_before_complete87=True,inputs=inputs,reason='Track preservation of86 VMC improvement and Acritic4 regression on unchanged2514 cohort, all5 critics and all30new84 rows. Entire fixed cohort, no row exclusion, no fresh forwards/physics/updates, no invented health threshold and no automatic88.',new_physics=0,new_network_forward=0,optimizer_updates=0,automatic_training=False))
put(O/'SOURCE_REVIEW.json',dict(passed=True,sources=[ref(O/n) for n in ['audit.py','wait.py','plot.py']],plan=ref(O/'PLAN.json')))
trial=subprocess.run([sys.executable,str(O/'audit.py')],text=True,capture_output=True)
assert trial.returncode!=0 and 'Complete87 fixed2514 result not ready' in trial.stderr
put(O/'INCOMPLETE87_REJECTION.json',dict(passed=True,exit=trial.returncode,stderr=trial.stderr,new_physics=0,new_network_forward=0,optimizer_updates=0))
with (O/'driver.log').open('x') as f:p=subprocess.Popen([sys.executable,str(O/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
put(O/'LAUNCH.json',dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(O/'PLAN.json'),automatic_training=False))
print('Fixed2514/all5 through87 registered and waiting',p.pid,sha(O/'PLAN.json'))
