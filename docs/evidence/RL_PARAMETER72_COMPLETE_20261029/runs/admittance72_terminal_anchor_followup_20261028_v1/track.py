"""Read-only complete72 followup of all2154 fixed71 admittance terminal rows."""
from pathlib import Path
import hashlib,json,os,sys,time
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
OUT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
plan=read(OUT/'PLAN.json');binding=read(OUT/'FINAL_BINDING.json')
for name,h in plan['sources'].items():assert sha(OUT/name)==h
for v in list(plan['inputs'].values())+list(binding.values()):assert sha(v['path'])==v['sha256']
reg=read(plan['inputs']['registration']['path']);runtime=Path(reg['runtime']);helper=Path(plan['helper_runtime'])
assert sha(runtime/'RUNTIME.json')==reg['runtime_sha256']
for name,h in read(runtime/'SOURCE_HASHES.json').items():assert sha(runtime/'source'/name)==h
for name,h in reg['batch_size_stage']['dependency_hashes'].items():assert sha(helper/name)==h
sys.path[:0]=[str(helper),str(runtime/'source/tools')]
from published_compliance_learner_20261025 import PublishedLearner
from validate_published_finite_check_20261025 import digest
assert sha(helper/'validate_published_finite_check_20261025.py')==plan['digest_helper_sha256']
with np.load(plan['inputs']['anchor_values']['path'],allow_pickle=False) as anchor:
    idx,features,rewards,masks,oldq,oldden=[anchor[k].copy() for k in ['indices','features','rewards','masks','q_after','denominator']]
assert len(idx)==2154 and features.shape==(2154,57)
ck=torch.load(binding['checkpoint']['path'],map_location='cpu',weights_only=False)
assert ck['cycle']==72 and ck['boundary']=='complete_condition_cycle' and ck['controller']=='admittance'
a=ck['replay']['arrays'];state=ck['learner'];terminal=np.flatnonzero(a['dones'][:,0]==1)
assert len(terminal)==2184 and np.array_equal(terminal[:2154],idx)
np.testing.assert_array_equal(a['observations'][idx],features[:,:50])
np.testing.assert_array_equal(a['actions'][idx],features[:,50:])
np.testing.assert_array_equal(a['rewards'][idx,0],rewards)
np.testing.assert_array_equal(a['masks'][idx].T,masks)
assert ck['replay']['capacity']==4_000_000 and ck['replay']['replay_capacity_extension']['capacity']==2_000_000 and ck['replay']['replay_capacity_followup']['capacity']==4_000_000
assert state['terminal_loss_weight']==128 and state['target_pair_reduction']['target']=='mean'
learner=PublishedLearner(runtime,dimension=7,direct=False,seed=42,device='cpu',algorithm=state['algorithm'],
    **{k:state[k] for k in ['critic_layer_norm','numerical_amendments','critic_clock']})
agent=learner.learner.agent;agent.load_state_dict(state['agent']);before=digest(agent.state_dict());assert before==digest(state['agent'])
rng=torch.get_rng_state().clone()
with torch.no_grad():
    obs=torch.as_tensor(a['observations'][terminal]);action=torch.as_tensor(a['actions'][terminal])
    q=torch.stack([agent.get_q_value(obs,action,i,target=False).reshape(-1) for i in range(5)]).numpy()
assert np.isfinite(q).all() and digest(agent.state_dict())==before and torch.equal(rng,torch.get_rng_state())
target=a['rewards'][terminal,0];mask=a['masks'][terminal].T.astype(float)
health=read(binding['health']['path'])['methods']['admittance'];assert health['terminal_count']==2184 and health['checkpoint_sha256']==binding['checkpoint']['sha256']
err=np.abs(q-target[None]).astype(float)
assert np.isclose(err.mean(),health['terminal_q_absolute_error']['mean'],rtol=0,atol=1e-9)
assert np.isclose(err[mask.astype(bool)].mean(),health['terminal_q_in_bag_absolute_error']['mean'],rtol=0,atol=1e-9)
den=a['masks'].sum(axis=0,dtype=float)+127*mask.sum(axis=1)
old_sse=masks*(oldq.astype(float)-rewards.astype(float)[None])**2
new_sse=mask*(q.astype(float)-target.astype(float)[None])**2
anchor_review=read(plan['inputs']['anchor_review']['path'])
assert np.isclose(old_sse.sum(),anchor_review['groups']['all2154']['masked_sse_after'],rtol=1e-12,atol=1e-12)
focus=[]
for index in plan['focus_replay_indices']:
    k=int(np.flatnonzero(idx==index)[0])
    focus.append(dict(replay_index=index,reward=float(rewards[k]),masks=masks[:,k].tolist(),q_before=oldq[:,k].tolist(),q_after=q[:,k].tolist(),sse_before=float(old_sse[:,k].sum()),sse_after=float(new_sse[:,k].sum())))
np.savez_compressed(OUT/'values.npz',indices=terminal,rewards=target,masks=mask,q_before=oldq,q_after=q,denominator=den,old_denominator=oldden)
report=dict(passed=True,time=time.time(),fixed_anchor_rows=2154,new_terminal_rows=30,
    original_fixed_observations_actions_rewards_masks_exact=True,
    old2154_sse_before=float(old_sse.sum()),old2154_sse_after=float(new_sse[:,:2154].sum()),
    old2154_sse_ratio=float(new_sse[:,:2154].sum()/old_sse.sum()),
    old2154_contribution_before=float((128*old_sse/oldden[:,None]).sum()),
    old2154_contribution_after=float((128*new_sse[:,:2154]/den[:,None]).sum()),
    old2154_after_using_old_denominator=float((128*new_sse[:,:2154]/oldden[:,None]).sum()),
    new30_contribution=float((128*new_sse[:,2154:]/den[:,None]).sum()),
    all_terminal_contribution=float((128*new_sse/den[:,None]).sum()),focus=focus,
    weights_and_forward_rng_unchanged=True,health72_terminal_values_reproduced=True,
    new_physics=0,optimizer_updates=0,replay_writes=0,convergence_claim=False,causal_claim=False,
    values_sha256=sha(OUT/'values.npz'),limitation=plan['limitation'])
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(6,5),constrained_layout=True)
x=old_sse.sum(axis=0);y=new_sse[:,:2154].sum(axis=0);ax.scatter(x,y,s=12,alpha=.5)
for f in focus:
    k=int(np.flatnonzero(idx==f['replay_index'])[0]);ax.scatter([x[k]],[y[k]],color='red');ax.annotate(str(f['replay_index']),(x[k],y[k]),fontsize=8)
limit=max(x.max(),y.max());ax.plot([0,limit],[0,limit],'--',color='gray')
ax.set_xlabel('Complete71 masked terminal SSE');ax.set_ylabel('Complete72 masked terminal SSE');ax.set_title('All 2154 fixed terminal rows\nOriginal complete66 short0600 focus marked')
fig.savefig(OUT/'follow72.png',dpi=130,bbox_inches='tight');report['plot_sha256']=sha(OUT/'follow72.png')
for v in list(plan['inputs'].values())+list(binding.values()):assert sha(v['path'])==v['sha256']
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
