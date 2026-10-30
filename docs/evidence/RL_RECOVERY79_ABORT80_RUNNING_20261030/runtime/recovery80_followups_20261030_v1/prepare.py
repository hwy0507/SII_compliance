from pathlib import Path
import json,hashlib,time,os,sys,subprocess,re,ast,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle80_20261029_v1';REV=B/'runs/parameter_partial75_recovery_cycle80_review_20261029_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def adapt(s):return re.sub('2334|2364|78|79',lambda m:{'2334':'2364','2364':'2394','78':'79','79':'80'}[m[0]],s)
def copy_sources(old,out,mapping):
 sources={};diffs=[]
 for before,after in mapping.items():
  p=old/before;src=p.read_text();new=adapt(src);ast.parse(new);(out/after).write_text(new);sources[after]=sha(out/after)
  (out/(after+'.diff')).write_text(''.join(difflib.unified_diff(src.splitlines(True),new.splitlines(True),fromfile=str(p),tofile=str(out/after))))
  diffs.append(dict(parent=ref(p),adapted=ref(out/after)))
 write(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=diffs,adaptation='Only78->79,79->80,2334->2364,2364->2394 cycle/path/count literals simultaneously. Original gate/arithmetic unchanged.',new_physics=0,optimizer_updates=0))
 return sources
jobs=read(RUN/'LAUNCH.json')['jobs'];monitor=read(RUN/'MONITOR_LAUNCH.json')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='')
def launch(out):
 with (out/'driver.log').open('x') as f:p=subprocess.Popen([sys.executable,str(out/'wait.py')],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 write(out/'LAUNCH.json',dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(out/'PLAN.json'),automatic_training=False))
try:
 old=B/'runs/parameter_recovery79_task_labels_20261029_v1';out=B/'runs/parameter_recovery80_task_labels_20261029_v1';out.mkdir()
 sources=copy_sources(old,out,{'audit_labels.py':'audit_labels.py','review_labels79.py':'review_labels80.py','wait.py':'wait.py'})
 plan=read(old/'PLAN.json');plan.update(time=time.time(),parent_run=str(RUN),parent_launch_sha256=sha(RUN/'LAUNCH.json'),jobs=jobs,monitor=monitor,sources=sources,cycles=[79,80]);write(out/'PLAN.json',plan)
 p=subprocess.run([sys.executable,str(out/'audit_labels.py'),'--before','79','--after','80','--output',str(out/'SHOULD_NOT_EXIST.json')],capture_output=True,text=True,env=env);assert p.returncode!=0 and 'Incomplete cycle 80' in p.stderr and not (out/'SHOULD_NOT_EXIST.json').exists();write(out/'INCOMPLETE80_REJECTION.json',dict(passed=True,returncode=p.returncode,stderr=p.stderr,source=ref(out/'audit_labels.py')));launch(out)
 for m in ['vmc','admittance']:
  old=B/f'runs/{m}_recovery79_terminal_followup_20261029_v1';out=B/f'runs/{m}_recovery80_terminal_followup_20261029_v1';out.mkdir()
  sources=copy_sources(old,out,{n:n for n in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']})
  ap=read(old/'ANCHOR_PLAN.json');ap.update(time=time.time(),sources={n:sources[n] for n in ['capture_anchor.py','review_anchor.py']})
  ap['inputs']={k:ref(p) for k,p in dict(prior_review=old/'REVIEW.json',prior_saved_review=old/'SAVED_VALUES_REVIEW.json',prior_binding=old/'FINAL_BINDING.json',prior_values=old/'values.npz',checkpoint=B/f'runs/parameter_partial75_recovery_cycle79_archive_20261029_v1/{m}/cycle_00079.pt',complete_review=B/'runs/parameter_partial75_recovery_cycle79_review_20261029_v1/REVIEW.json').items()}
  # Preserve any descriptive anchor metadata but update the exact current boundary.
  for k,v in list(ap.items()):
   if isinstance(v,str):ap[k]=adapt(v)
   elif isinstance(v,int) and v==2334:ap[k]=2364
  write(out/'ANCHOR_PLAN.json',ap)
  for n in ['capture_anchor.py','review_anchor.py']:subprocess.run([sys.executable,str(out/n)],check=True,env=env)
  plan=read(old/'PLAN.json');plan.pop('expected_complete79_terminal_rows');plan.update(time=time.time(),parent_run=str(RUN),parent_review=str(REV),final_checkpoint=str(B/f'runs/parameter_partial75_recovery_cycle80_archive_20261029_v1/{m}/cycle_00080.pt'),learners=jobs,monitor=monitor,parent_launch_sha256=sha(RUN/'LAUNCH.json'),sources=sources,fixed_anchor_rows=2364,expected_complete80_terminal_rows=2394,registered_during80=True,registered_before_complete80=True,limitation=adapt(plan['limitation']))
  plan.pop('registered_during79');plan.pop('registered_before_complete79')
  inp=plan['inputs'];inp.update({k:ref(p) for k,p in dict(anchor_values=out/'anchor79.npz',anchor_review=out/'ANCHOR_REVIEW.json',anchor_saved_review=out/'ANCHOR_SAVED_REVIEW.json',anchor_plan=out/'ANCHOR_PLAN.json',source_review=out/'SOURCE_REVIEW.json',registration=RUN/m/'REGISTRATION.json',prior79_review=old/'REVIEW.json',prior79_saved_review=old/'SAVED_VALUES_REVIEW.json').items()})
  write(out/'PLAN.json',plan);assert not (RUN/'ARCHIVE_REVIEW_FINISHED.json').exists();launch(out)
 write(D/'FINISHED.json',dict(passed=True,time=time.time(),labels80_waiting=True,vmc80_waiting=True,admittance80_waiting=True,new_network_forward=0,new_physics=0,optimizer_updates=0,convergence_claim=False))
except BaseException as e:write(D/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
