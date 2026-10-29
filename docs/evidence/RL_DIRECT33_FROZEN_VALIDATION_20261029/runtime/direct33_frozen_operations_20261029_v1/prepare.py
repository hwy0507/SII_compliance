from pathlib import Path
import json,time,hashlib,ast,difflib,subprocess,os,socket,shutil
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;O=B/'runs/serl_take33_frozen_full30_20261029_v1';RT=B/'runtime/serl_take33_frozen_full30_20261029_v1';OLD=B/'runs/serl_take29_frozen_full30_20261027_v1';REV=B/'runs/serl_take_cycle33_review_20261027_v1';TRAIN=B/'runs/serl_take_cycle33_20261027_v1';CP=B/'runs/serl_take_cycle33_archive_20261027_v1/direct/cycle_00033.pt'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def replace_once(s,a,z):assert s.count(a)==1,(a,s.count(a));return s.replace(a,z)
O.mkdir();RT.mkdir()
assert read(REV/'FINISHED.json')['completed'] and read(REV/'REVIEW.json')['passed']
assert sha(CP)==read(REV/'REVIEW.json')['methods']['direct']['checkpoint_sha256']=='783eaa7f7b03226915539e41cce313a5faeb4d49a15ae25626bb9762a9f47849'
decpath=B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json';dec=read(decpath);assert dec['direct_numerical_criterion_satisfied'] and not dec['launch34']
for x in dec['evidence'].values():assert sha(x['path'])==x['sha256']
oldplan=read(OLD/'PLAN.json');protocol=read(TRAIN/'REGISTRATION.json');assert protocol['conditions']==oldplan['conditions'] and read(OLD/'REVIEW.json')['passed']
# Register once before any new33 restoration or physical evaluation, acknowledging post-training selection.
plan={k:oldplan[k] for k in ['action_seed','noise_schedule','maximum_episodes','maximum_actions','maximum_physical_substeps','conditions','case_ids','optimizer_updates','replay_writes','training_conditions_only','convergence_claim','capacity_entry_cycle','replay_capacity','quarantined_pending','interrupted25_checkpoint']}
plan.update(time=time.time(),host=socket.gethostname(),cycle=33,checkpoint=ref(CP),training_registration=ref(TRAIN/'REGISTRATION.json'),stage_decision=ref(decpath),comparison_frozen29_plan=ref(OLD/'PLAN.json'),comparison_frozen29_review=ref(OLD/'REVIEW.json'),comparison_frozen29_registration=ref(OLD/'REGISTRATION.json'),selected_as='Latest complete33 retained when Direct numerical training stage was accepted. Post-training checkpoint selection disclosed; all30 training conditions, external action seed and budget fixed before any new33 evaluation. Not a new prospective training convergence window.',learner_cpu=0,physics_cpus=[1,2],review_cpu=3,inference_gpu=0,check_only_timeout_seconds=600,evaluation_review_wait_seconds=21600,automatic_evaluation=False,automatic_training=False,history_requirement='Original complete0..24 and26..33 retained, partial25 exposure and930 quarantined pending preserved. No complete25 invented.',resource_gate='Use released CPU0-3/GPU0; parameter78 training remains13-51/GPU1-3 and guard52-54. Keep synthetic occupancy after all science.',limitation='Single training seed and original external action seed2026102626 on the same30 training conditions. Latest33 frozen validation and descriptive paired29->33 comparison only, not held-out/generalization, new convergence proof or specifiedESN/finalSPT comparison. Do not select finalTref from this partial comparison.')
write(O/'PLAN.json',plan)
freeze=read(OLD/'SOURCE_FREEZE.json');oldrt=Path(freeze['evaluation_runtime']);copied={}
for n,h in freeze['source_hashes'].items():
 p=oldrt/n;assert sha(p)==h,n;(RT/n).write_bytes(p.read_bytes());copied[n]=h
for n,h in protocol['recovery_continuation_stage']['source_hashes'].items():assert sha(RT/n)==h,n
src=(oldrt/'evaluate_serl_recovery_frozen_20261027.py').read_text();new=replace_once(src,'args.expected_cycle != 29','args.expected_cycle != 33');new=replace_once(new,'registered only for complete29','registered only for complete33');name='evaluate_serl33_frozen_20261029.py';(RT/name).write_text(new);ast.parse(new)
assert src.split('    results = []',1)[1]==new.split('    results = []',1)[1]
a=ast.parse(src);z=ast.parse(new)
for fun in ['case_action_seed','seeded_action']:
 assert ast.dump(next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name==fun))==ast.dump(next(n for n in z.body if isinstance(n,ast.FunctionDef) and n.name==fun))
(D/'evaluator.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),new.splitlines(True),fromfile='frozen29_evaluator',tofile='frozen33_evaluator')))
source=(oldrt/'review_serl29_recovery_frozen_matrix_20261027.py').read_text();review=source
for before,after in [("os.sched_setaffinity(0, {52})","os.sched_setaffinity(0, {3})"),("reg['cycle'] == 29","reg['cycle'] == 33"),("restore['cycle'] == 29","restore['cycle'] == 33"),("==[26,27,28,29]","==list(range(26,34))"),("direct_recovery29_frozen_stochastic","direct_recovery33_frozen_stochastic"),("Frozen recovered complete29","Frozen recovered complete33")]:review=replace_once(review,before,after)
review=replace_once(review,"    samples = sum(r['samples'] for r in rows)","    assert sum(r['actions'] for r in rows) <= 41250\n    samples = sum(r['samples'] for r in rows)")
rname='review_serl33_frozen_matrix_20261029.py';(RT/rname).write_text(review);ast.parse(review);(D/'reviewer.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),review.splitlines(True),fromfile='frozen29_review',tofile='frozen33_review')))
for n in [name,rname]:copied[n]=sha(RT/n)
write(O/'SOURCE_FREEZE.json',dict(time=time.time(),plan=ref(O/'PLAN.json'),parent_source_freeze=ref(OLD/'SOURCE_FREEZE.json'),evaluation_runtime=str(RT),source_hashes=copied,physics_loop_byte_identical=True,external_action_functions_ast_identical=True,original703_sources_byte_exact=True,new_sources=[name,rname],automatic_evaluation=False))
reg={k:plan[k] for k in ['cycle','action_seed','noise_schedule','maximum_episodes','maximum_physical_substeps','physics_cpus','learner_cpu','inference_gpu','optimizer_updates','replay_writes','training_conditions_only','convergence_claim']}
reg.update(evaluation_runtime=str(RT),inputs=dict(plan=ref(O/'PLAN.json'),source_freeze=ref(O/'SOURCE_FREEZE.json'),training_registration=ref(TRAIN/'REGISTRATION.json'),checkpoint=ref(CP),cycle_review=ref(REV/'REVIEW.json'),health_review=ref(REV/'DIAGNOSIS.json'),finished=ref(REV/'FINISHED.json'),stage_decision=ref(decpath),comparison29=ref(OLD/'REVIEW.json')),sources={n:ref(RT/n) for n in copied});write(O/'REGISTRATION.json',reg)
commands=[]
for i,job in enumerate(read(OLD/'COMMANDS.json')['jobs']):
 cmd=list(job['command']);cmd[2]='0-3';cmd[4]=str(RT/name)
 for flag,value in [('--registration',TRAIN/'REGISTRATION.json'),('--checkpoint',CP),('--expected-cycle',33),('--learner-cpu',0),('--physics-cpu',i+1),('--output',O/f'shard{i}')]:cmd[cmd.index(flag)+1]=str(value)
 assert job['case_ids']==plan['case_ids'][i::2];commands.append(dict(command=cmd,case_ids=job['case_ids'],output=str(O/f'shard{i}')))
write(O/'COMMANDS.json',dict(jobs=commands))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
# Physical wrong-cycle rejection occurs before output creation or checkpoint load.
cmd=commands[0]['command'].copy();cmd[cmd.index('--expected-cycle')+1]='29';cmd[cmd.index('--output')+1]=str(O/'WRONG_CYCLE_SHOULD_NOT_EXIST');p=subprocess.run(cmd,capture_output=True,text=True,env=env);assert p.returncode!=0 and 'registered only for complete33' in p.stderr and not (O/'WRONG_CYCLE_SHOULD_NOT_EXIST').exists();write(O/'WRONG_CYCLE_REJECTION.json',dict(passed=True,returncode=p.returncode,stderr=p.stderr,source=ref(RT/name)))
write(O/'STATIC_REVIEW.json',dict(passed=True,time=time.time(),copied_sources=len(freeze['source_hashes']),all_current33_dependency_hashes_exact=True,physical_loop_byte_exact=True,action_seed_and_conditions_match29=True,original_budget_and_gates=True,new_physics=0,optimizer_updates=0,source_manifest=ref(O/'SOURCE_FREEZE.json')))
cmd=commands[0]['command'].copy();cmd[cmd.index('--output')+1]=str(O/'check_only');cmd.append('--check-only')
with (O/'check_only.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(O/'CHECK_ONLY_LAUNCH.json',dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),command=cmd,automatic_physical_evaluation=False));print('Registered exact33 full30 evaluation; check-only launched',p.pid)
