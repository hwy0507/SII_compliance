from pathlib import Path
import os,json,hashlib,time
os.sched_setaffinity(0,{54})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/serl_cycle14_initial_actor_gradient_20261026_v3'
reg=json.loads((out/'REGISTRATION.json').read_text());r=json.loads((out/'REVIEW.json').read_text());assert r['passed']
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(reg['checkpoint']['path'])==reg['checkpoint']['sha256']
x=torch.load(reg['checkpoint']['path'],map_location='cpu',weights_only=False);a=x['replay']['arrays'];e=x['replay']['multistep_target_extension'];ids=np.asarray(e['ready']);assert len(ids)==607032 and not e['pending']
current=a['observations'][ids,48];nextclock=a['next_observations'][e['target_endpoints'][ids],48];threshold=np.float32((1375-31)/1375)
source=Path(reg['upstream'])/'serl_launcher/serl_launcher/agents/continuous/sac.py';s=source.read_text();assert 'def temperature_loss_fn' in s and 'batch["next_observations"]' in s
result=dict(time=time.time(),passed=True,checkpoint=reg['checkpoint'],rows=len(ids),current_initial_rows=int(np.sum(current==1)),current_first32_rows=int(np.sum(current>=threshold)),derived_next_initial_rows=int(np.sum(nextclock==1)),derived_next_first32_rows=int(np.sum(nextclock>=threshold)),maximum_derived_next_clock=float(nextclock.max()),earliest_next_action_index=float((1-nextclock.max())*1375),source=dict(path=str(source),sha256=sha(source)),audit_source=dict(path=__file__,sha256=sha(__file__)),new_physics=0,optimizer_updates=0,interpretation='Pinned official temperature_loss_fn obtains actions from _compute_next_actions on batch next_observations. Deployed multistep replay replaces next_observations with the32-step endpoint. Current actor-state and temperature-state coverage therefore differ; all mature replay rows audited here. This is not a bootstrap bug, does not establish causality, and does not change the formal official temperature objective.')
assert result['current_initial_rows']==450 and result['current_first32_rows']==14400
(out/'TEMPERATURE_STATE_COVERAGE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
