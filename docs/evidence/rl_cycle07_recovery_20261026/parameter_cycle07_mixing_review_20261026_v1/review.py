from pathlib import Path
import json,hashlib,os,time,collections
os.sched_setaffinity(0,{52})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent
results={}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for method in ['impedance','admittance','vmc']:
 run=B/'runs/clock_parameter_reviewed_cycle06_07_20261026_v1'/method/'train'
 cp=B/'runs/reviewed_continuation_cycle_archive_20261026_v1'/method/'cycle_00007.pt'
 x=torch.load(cp,map_location='cpu',weights_only=False)
 rows=[json.loads(s) for s in (run/'transitions.jsonl').read_text().splitlines()]
 episodes=[json.loads(s) for s in (run/'episodes.jsonl').read_text().splitlines()]
 summary={}
 for cycle in [6,7]:
  ts=[r for r in rows if r['cycle']==cycle];es=[r for r in episodes if r['cycle']==cycle]
  context=np.array([r['context'] for r in ts]);idx=np.array([r['step']-1 for r in ts])
  np.testing.assert_array_equal(context.astype(np.float32),x['replay']['arrays']['observations'][idx,48])
  assert len(ts)==41250 and len(es)==30 and np.all((context>=.2-1e-7)&(context<=1.+1e-7))
  cats={}
  for cat in ['passive_corner','active_short','active_long']:
   group=[r for r in es if r['category']==cat]
   cats[cat]=dict(conditions=len(group),task=sum(r['task_success'] for r in group),strict=sum(r['strict_success'] for r in group),mean_reward=float(np.mean([r['reward'] for r in group])),failure_stages=dict(collections.Counter(r['final_task_stage'] for r in group if not r['strict_success'])))
  summary[cycle]=dict(transitions=len(ts),mean_rl_weight=float(context.mean()),at_minimum_fraction=float(np.mean(np.isclose(context,.2,rtol=0,atol=1e-7))),above_half_fraction=float(np.mean(context>.5)),at_full_fraction=float(np.mean(context>1.-1e-7)),categories=cats)
 results[method]=dict(checkpoint_sha256=sha(cp),cycles=summary)
 del x,rows,episodes
report=dict(time=time.time(),methods=results,passed=True,new_physics=0,optimizer_updates=0,limitation='Actual online mixing weights checked against replay feature48; descriptive association, not a causal intervention or proof that changing uncertainty thresholds would improve tasks.',convergence_claim=False)
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
