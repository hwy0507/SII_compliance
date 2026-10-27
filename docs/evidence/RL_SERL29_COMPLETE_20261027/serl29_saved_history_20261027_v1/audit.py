from pathlib import Path
import torch,json,hashlib,time,os,math
os.sched_setaffinity(0,{1});torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/serl29_saved_history_20261027_v1';O.mkdir();P=B/'runs/serl_take_cycle29_archive_20261027_v1/direct/cycle_00029.pt';R=B/'runs/serl_take_cycle29_review_20261027_v1/REVIEW.json'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
r=json.loads(R.read_text());assert r['passed'];expected=r['methods']['direct']['checkpoint_sha256'];assert sha(P)==expected
x=torch.load(P,map_location='cpu',weights_only=False,mmap=True);history=x['cycles'];assert [h['cycle'] for h in history]==list(range(25))+[26,27,28,29]
assert x['steps']==1204290 and x['cycle']==29 and x['boundary']=='complete_condition_cycle'
assert history[-1]['reward_mean']==r['methods']['direct']['reward_mean'];assert all(math.isfinite(h['reward_mean']) for h in history)
result=dict(passed=True,time=time.time(),checkpoint_sha256=expected,history=history,first_complete_cycle=history[0],last_complete_cycle=history[-1],first_to_last_mean_delta=history[-1]['reward_mean']-history[0]['reward_mean'],partial25_retained_but_not_invented_as_complete=True,new_physics=0,optimizer_updates=0,convergence_claim=False,scope='Read saved checkpoint history only; algorithms and infrastructure changed across historical stages, so early-to-late difference is descriptive and not an isolated causal comparison. Frozen16-to29 is the original prespecified physical comparison. Task success is reported separately from reward stability.')
(O/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');(O/'audit.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items() if k!='history'},indent=2))
