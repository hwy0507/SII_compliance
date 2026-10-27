from pathlib import Path
import json,time,os,shutil,subprocess,ast,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def identity(pid):
 q=Path(f'/proc/{pid}');st=(q/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z';return dict(start_ticks=st[19],command=(q/'cmdline').read_bytes().replace(b'\0',b' ').decode())
def start(out,script):
 cmd=[str(B/'env/bin/python'),str(out/script)]
 with (out/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 write(out/'LAUNCH.json',dict(pid=p.pid,time=time.time(),command=cmd,identity=identity(p.pid)));return p.pid
O=B/'runs/parameter48_serl29_transition_20261027_v1';O.mkdir();shutil.copyfile(B/'runs/parameter47_serl28_transition_20261027_v1/observe.py',O/'observe.py')
groups=[]
for name,parents,rpid,review,cpu,nxt in [('parameter48_to49',[359275,359279,359281],359363,'parameter_capacity_pool30_cycle48_review_20261026_v1',13,'parameter_capacity_pool30_cycle49_20261026_v1'),('serl29_to30',[241542],241549,'serl_take_cycle29_review_20261027_v1',0,'serl_take_cycle30_20261027_v1')]:
 ids={str(p):identity(p) for p in parents+[rpid]};assert review in ids[str(rpid)]['command'];groups.append(dict(name=name,parents=parents,review_pid=rpid,review_run=review,cpu=cpu,next_run=nxt,identities=ids))
write(O/'PLAN.json',dict(time=time.time(),groups=groups,budget_seconds=7200,interval_seconds=2,automatic_training=False,action='Move only original read-only review processes to released learnerCPU after all original parents exit; no formal scheduling changes',source_sha256=hashlib.sha256((O/'observe.py').read_bytes()).hexdigest()))
observer=start(O,'observe.py')
P=B/'runs/parameter48_saved_review_20261027_v1';P.mkdir();s=(B/'runs/parameter47_saved_review_20261027_v1/review_saved.py').read_text().replace('cycle47','cycle48').replace("['cycle']==47","['cycle']==48").replace('Original47','Original48').replace('monotonic()+1800','monotonic()+7200');ast.parse(s);(P/'review_saved.py').write_text(s);ppid=start(P,'review_saved.py')
D=B/'runs/serl_take29_saved_review_20261027_v1';D.mkdir();s=(B/'runs/serl_take28_saved_review_20261027_v1/review_saved.py').read_text().replace('cycle28','cycle29').replace("['cycle']==28","['cycle']==29").replace('Original28','Original29').replace("['terminal_count']==840","['terminal_count']==870").replace('monotonic()+1800','monotonic()+7200');ast.parse(s);(D/'review_saved.py').write_text(s);dpid=start(D,'review_saved.py')
print(dict(observer=observer,parameter48_saved=ppid,serl29_saved=dpid))
