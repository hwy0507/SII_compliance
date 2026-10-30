from pathlib import Path
import json,ast,hashlib,time,subprocess,os,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/serl_take33_frozen_remaining2_20261030_v2';O=B/'runs/serl_take33_frozen_combined_review_20261030_v3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def read(p):return json.loads(Path(p).read_text())
assert (OLD/'COMBINED_REVIEW_FAILURE.json').exists() and not (OLD/'combined_audits').exists()
for j in read(OLD/'LAUNCH.json')['jobs']:assert read(Path(j['output'])/'POLICY_UNCHANGED.json')['full_learner_state_unchanged']
O.mkdir(exist_ok=False)
for n in ['PLAN.json','LAUNCH.json','REPLAY_LAUNCH.json']:(O/n).write_bytes((OLD/n).read_bytes())
(O/'saved28_replay').symlink_to(OLD/'saved28_replay',target_is_directory=True)
replacements={OLD.name:O.name}
s=(D/'review_combined_v2.py').read_text();v=s.replace(OLD.name,O.name).replace('json.loads(p.read_text())','json.loads(Path(p).read_text())');ast.parse(v);review=D/'review_combined_v3.py';review.write_text(v);(D/'review_combined_v3.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True))))
# The sole helper repair accepts both Path and str; exercise actual input before launch.
assert read(str(O/'PLAN.json'))==read(O/'PLAN.json')
p=read(OLD/'COMBINED_REVIEW_PLAN.json');p.update(time=time.time());p['sources'][0]=ref(review);p['inputs']=[ref(O/n) for n in ['PLAN.json','LAUNCH.json','REPLAY_LAUNCH.json']];put(O/'COMBINED_REVIEW_PLAN.json',p)
for src,dst in [('compare_recovered.py','compare_recovered_v3.py'),('wait_compare_recovered.py','wait_compare_recovered_v3.py')]:
 s=(D/src).read_text();v=s.replace(OLD.name,O.name).replace("D/'compare_recovered.py'","D/'compare_recovered_v3.py'");ast.parse(v);(D/dst).write_text(v)
p=read(OLD/'COMPARISON_PLAN.json');p.update(time=time.time(),source_sha256=sha(D/'compare_recovered_v3.py'),waiter_sha256=sha(D/'wait_compare_recovered_v3.py'));p['inputs']['recovered_plan']=ref(O/'PLAN.json');p['inputs']['combined_review_plan']=ref(O/'COMBINED_REVIEW_PLAN.json');put(O/'COMPARISON_PLAN.json',p)
put(O/'READONLY_REPAIR_REVIEW.json',dict(passed=True,time=time.time(),prior_failure=ref(OLD/'COMBINED_REVIEW_FAILURE.json'),prior_comparison_failure=ref(OLD/'COMPARISON_FAILURE.json'),reason='Normalize read helper argument with Path; previous failure before per-episode audits. All completed original28 and new2 physics plus saved28 action replay reused, no scientific restart.',path_str_control=True,source=ref(review),new_physics=0,new_updates=0))
for name,script,log in [('COMBINED_REVIEW_LAUNCH.json',review,'combined_review.log'),('COMPARISON_LAUNCH.json',D/'wait_compare_recovered_v3.py','compare.log')]:
 with (O/log).open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(script)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 put(O/name,dict(pid=p.pid,start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),source=ref(script)));print(name,p.pid)
