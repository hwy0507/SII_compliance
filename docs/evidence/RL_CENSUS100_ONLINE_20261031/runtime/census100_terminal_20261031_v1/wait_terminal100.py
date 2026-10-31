from pathlib import Path
import json,time,subprocess,traceback
from terminal100 import O,B,D,read,put,inputs
try:
 p=inputs(read(O/'PLAN.json'));assert read(O/'PREFLIGHT_REVIEW.json')['passed'] and read(O/'PARTIAL_REJECTION_REVIEW.json')['passed'];j=p['original_monitor'];target=Path(p['complete_review'])/'FINISHED.json'
 while not target.exists():
  assert time.time()<p['wait_deadline_unix'] and not (Path(p['run'])/'ARCHIVE_REVIEW_FAILURE.json').exists()
  s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['proc_start_ticks'];time.sleep(15)
 subprocess.run([str(B/'env/bin/python'),str(D/'terminal100.py')],check=True,timeout=1200)
 assert read(O/'REVIEW.json')['passed'];put(O/'FINISHED.json',dict(passed=True,time=time.time(),actual_plot_inspection_pending=True,automatic101=False))
except BaseException as e:put(O/('WAIT_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
