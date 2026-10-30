from pathlib import Path
import json,time,hashlib,subprocess,socket
D=Path(__file__).parent;B=D.parents[1];O=B/'runs/parameter82_frozen_full30_20261030_v1'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
source=B/'runs/parameter86_frozen_switches_20261030_v1/OBSERVATION_V2_PLAN.json'
ids=json.loads(source.read_text())['identities']
write(D/'PLAN.json',dict(time=time.time(),host=socket.gethostname(),purpose='Observe original frozen82 final episode and full90 review/saved-raw audit/comparison; then independently summarize every paired case and view actual plots. No new physics or training.',identities=ids,identity_source_sha256=sha(source),observer_budget_seconds=1200,interval_s=30,evaluation_plan_sha256=sha(O/'PLAN.json'),all90_cases=True,new_physics=0,new_optimizer_updates=0,automatic_training=False,known_at_registration='I and V finished, A29 cases plus last0900 in progress; selected all original90 not by outcome',remote_main='80e94020d78a3df407541a8c547ff1e9ca56994a',remote_baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d'))
print('PLAN saved')
