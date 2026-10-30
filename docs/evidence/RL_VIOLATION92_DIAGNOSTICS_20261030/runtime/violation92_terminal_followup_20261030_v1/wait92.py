from pathlib import Path
import json,time,subprocess,traceback,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';R=B/'runs/parameter_violation_cycle92_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
try:
 plan=read(O/'PLAN.json');assert read(O/'PREFLIGHT_REVIEW.json')['passed'];assert sha(Path(__file__))==plan['source_hashes']['wait92.py']
 monitor=read(R/'MONITOR_LAUNCH.json');assert monitor==plan['original_monitor'];deadline=plan['wait_deadline_unix'];target=Path(plan['complete_review'])/'FINISHED.json'
 while not target.exists():
  assert time.time()<deadline and not (R/'ARCHIVE_REVIEW_FAILURE.json').exists()
  stat=Path('/proc',str(monitor['pid']),'stat').read_text().rsplit(')',1)[1].split();assert stat[0]!='Z' and stat[19]==monitor['proc_start_ticks'];time.sleep(15)
 subprocess.run([str(B/'env/bin/python'),str(D/'compare92.py')],check=True,timeout=plan['analysis_budget_seconds']+60)
 assert read(O/'REVIEW.json')['passed'];put(O/'FINISHED.json',dict(passed=True,time=time.time(),actual_plot_inspection_pending=True,automatic93=False))
except BaseException as e:put(O/('WAIT_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
