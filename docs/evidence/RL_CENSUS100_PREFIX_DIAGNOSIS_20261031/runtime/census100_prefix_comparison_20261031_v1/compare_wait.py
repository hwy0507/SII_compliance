"""Bounded read-only full100 comparison consumer; never starts training."""
from pathlib import Path
import ast,hashlib,json,os,subprocess,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_census_cycle100_20261031_v1';V=B/'runs/parameter_census_cycle100_review_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def identity(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'));return s[19]
def sources(plan):
 for n,h in plan['source_hashes'].items():assert sha(D/n)==h;ast.parse((D/n).read_text())
 assert sha(D/'COMPARISON_PLAN.json')==plan['comparison_plan_sha256']
 assert sha(D/'CACHE_POPULATION_PLAN.json')==plan['cache_population_plan_sha256']
 for p,h in read(D/'COMPARISON_PLAN.json')['prior_inputs'].items():assert sha(p)==h
 assert plan['original_monitor']==read(T/'MONITOR_LAUNCH.json') and plan['deadline']==min(j['time'] for j in read(T/'LAUNCH.json')['jobs'])+14400
def ready():
 finished=read(V/'FINISHED.json');full=read(V/'REVIEW.json');health=read(V/'health/DIAGNOSIS.json');loss=read(V/'loss/REVIEW.json')
 assert finished['completed'] and full['passed'] and health['cycle']==100 and loss['passed']
 for m in ['impedance','admittance','vmc']:
  x=full['methods'][m];assert 0<x['new_transitions']<=41250 and x['new_transitions']==loss['methods'][m]['rows'];assert x['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256']
 return full
def preflight(plan):
 sources(plan);identity(plan['original_monitor']);assert time.time()<plan['deadline']
 prior=read(B/'runs/parameter_census_cycle99_review_20261031_v1/REVIEW.json');health=read(B/'runs/parameter_census_cycle99_review_20261031_v1/health/DIAGNOSIS.json');assert prior['passed'] and health['cycle']==99
 for m in ['impedance','admittance','vmc']:
  reg=read(T/m/'REGISTRATION.json');assert reg['post_interruption_continuation']['parent_cycle']==99 and reg['post_interruption_continuation']['new_cycle']==100
  assert reg['conditional_terminal_amendment']==read(D/'COMPARISON_PLAN.json')['conditional_amendments'][m]
  cases=[c['id'] for c in reg['conditions']];episodes=[e for e in health['methods'][m]['episodes'] if e['cycle']==99];assert len(cases)==len(episodes)==30 and set(cases)=={e['condition'] for e in episodes};assert prior['methods'][m]['checkpoint_sha256']==reg['post_interruption_continuation']['checkpoint']['sha256']
 try:ready()
 except FileNotFoundError:missing=True
 else:raise AssertionError('Actual complete100 unexpectedly ready; no waiting registration needed')
 put(D/'COMPARISON_PREFLIGHT.json',dict(passed=True,time=time.time(),actual_missing_complete100_rejected=missing,actual_complete99_all90_inputs_bound=True,original_archive_monitor_live=True,source_hashes=plan['source_hashes'],new_physics=0,optimizer_updates=0,new_training=False))
def main(plan):
 sources(plan);assert read(D/'COMPARISON_PREFLIGHT.json')['passed'];os.sched_setaffinity(0,{10})
 while not (V/'FINISHED.json').exists():
  identity(plan['original_monitor']);assert time.time()<plan['deadline'] and not (T/'ARCHIVE_REVIEW_FAILURE.json').exists();time.sleep(15)
 ready();sources(plan)
 for script in ['interpret100.py','changed_cases.py']:
  with (D/(script+'.log')).open('x') as log:subprocess.run([str(B/'env/bin/python'),str(D/script)],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=plan['analysis_budget_seconds'],env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 for n in ['INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','CHANGED_CASES_REVIEW.json']:assert read(D/n)['passed']
 with (D/'population_complete.log').open('x') as log:subprocess.run([str(B/'env/bin/python'),str(D/'check_terminal_population.py'),'--complete'],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=plan['analysis_budget_seconds'],env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 assert read(D/'CACHE_POPULATION_FULL_REVIEW.json')['passed']
 put(D/'COMPARISON_FINISHED.json',dict(passed=True,time=time.time(),actual_plot_inspection_pending=True,automatic101=False,new_physics=0,optimizer_updates=0))
if __name__=='__main__':
 plan=read(D/'WAIT_PLAN.json')
 try:
  if '--preflight' in sys.argv:preflight(plan)
  elif '--launch' in sys.argv:
   sources(plan);assert read(D/'COMPARISON_PREFLIGHT.json')['passed'];identity(plan['original_monitor']);assert time.time()<plan['deadline'] and not (D/'PROCESS.json').exists() and not (V/'FINISHED.json').exists()
   with (D/'wait.log').open('xb') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(Path(__file__))],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   s=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';put(D/'PROCESS.json',dict(pid=p.pid,start=s[19],time=time.time(),deadline=plan['deadline'],source_sha256=sha(__file__)));print('Original100 comparison waiter launched',p.pid)
  else:main(plan)
 except BaseException as e:put(D/('COMPARISON_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
