"""Frozen preterminal/final56 critic comparison on identical terminal rows."""
from pathlib import Path
import hashlib, json, os, sys, time
os.sched_setaffinity(0, {53})
import numpy as np
import torch
torch.set_num_threads(1)
OUT = Path(__file__).resolve().parent
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
plan = read(OUT/'PLAN.json')
for name, expected in plan['sources'].items(): assert sha(OUT/name) == expected
capture = read(OUT/'CAPTURE_REVIEW.json')
assert sha(capture['snapshot']) == capture['snapshot_sha256']
binding = read(OUT/'FINAL_BINDING.json')
for v in binding.values(): assert sha(v['path']) == v['sha256']
registration = read(plan['registration']['path'])
assert sha(plan['registration']['path']) == plan['registration']['sha256']
runtime = Path(registration['runtime']); helper = Path(plan['helper_runtime'])
assert sha(runtime/'RUNTIME.json') == registration['runtime_sha256']
for name, h in read(runtime/'SOURCE_HASHES.json').items(): assert sha(runtime/'source'/name)==h
for name, h in registration['batch_size_stage']['dependency_hashes'].items(): assert sha(helper/name)==h
sys.path[:0] = [str(helper), str(runtime/'source/tools')]
from published_compliance_learner_20261025 import PublishedLearner
from validate_published_finite_check_20261025 import digest
assert sha(helper/'validate_published_finite_check_20261025.py') == plan['digest_helper_sha256']
before = torch.load(capture['snapshot'], map_location='cpu', weights_only=False)
after = torch.load(binding['checkpoint']['path'], map_location='cpu', weights_only=False)
assert after['cycle']==56 and after['boundary']=='complete_condition_cycle' and after['controller']=='vmc'
assert before['steps']==2334000 and before['controller']=='vmc'
a = after['replay']['arrays']; b = before['replay']['arrays']; n = before['replay']['size']
for k,v in b.items(): np.testing.assert_array_equal(v,a[k][:n])
for ck in [before,after]:
    assert ck['replay']['capacity']==4_000_000
    assert ck['replay']['replay_capacity_extension']['capacity']==2_000_000
    assert ck['replay']['replay_capacity_followup']['capacity']==4_000_000
    assert ck['learner']['terminal_loss_weight']==128
    assert ck['learner']['target_pair_reduction']['target']=='mean'
indices=np.flatnonzero(a['dones'][:,0]==1)
old_indices=np.flatnonzero(b['dones'][:,0]==1)
assert len(old_indices)==capture['old_terminal_count']==1674
np.testing.assert_array_equal(indices[:1674],old_indices)
assert len(indices)==1704 and np.all(indices[1674:]>=n)
health=read(binding['health']['path'])['methods']['vmc']
assert health['checkpoint_sha256']==binding['checkpoint']['sha256'] and health['terminal_count']==1704
features=np.concatenate([a['observations'][indices],a['actions'][indices]],axis=1)
obs=torch.as_tensor(a['observations'][indices]); actions=torch.as_tensor(a['actions'][indices])
q=[]
for ck in [before,after]:
    state=ck['learner']
    learner=PublishedLearner(runtime,dimension=7,direct=False,seed=42,device='cpu',algorithm=state['algorithm'],
        **{k:state[k] for k in ['critic_layer_norm','numerical_amendments','critic_clock']})
    agent=learner.learner.agent; agent.load_state_dict(state['agent'])
    digest_before=digest(agent.state_dict()); assert digest_before==digest(state['agent'])
    rng=torch.get_rng_state().clone()
    with torch.no_grad(): values=torch.stack([agent.get_q_value(obs,actions,i,target=False).reshape(-1) for i in range(5)]).numpy()
    assert np.isfinite(values).all() and digest(agent.state_dict())==digest_before and torch.equal(rng,torch.get_rng_state())
    q.append(values)
target=a['rewards'][indices,0]; masks=a['masks'][indices].T.astype(np.float64)
native_abs=np.abs(q[1]-target[None]).astype(np.float64)
assert np.isclose(native_abs.mean(),health['terminal_q_absolute_error']['mean'],rtol=0,atol=1e-9)
assert np.isclose(native_abs[masks.astype(bool)].mean(),health['terminal_q_in_bag_absolute_error']['mean'],rtol=0,atol=1e-9)
denominator=a['masks'].sum(axis=0,dtype=np.float64)+127*masks.sum(axis=1)
squared=[masks*(v.astype(np.float64)-target.astype(np.float64)[None])**2 for v in q]
groups={}
for name,sl in [('old1674',slice(0,1674)),('new30',slice(1674,None)),('all1704',slice(None))]:
    sums=[float(v[:,sl].sum()) for v in squared]
    groups[name]=dict(masked_sse_before=sums[0],masked_sse_after=sums[1],ratio=sums[1]/sums[0],
                     same_final_denominator_contribution_before=float((128*squared[0][:,sl]/denominator[:,None]).sum()),
                     same_final_denominator_contribution_after=float((128*squared[1][:,sl]/denominator[:,None]).sum()))
np.savez_compressed(OUT/'values.npz',indices=indices,features=features,rewards=target,masks=masks,
                    q_before=q[0],q_after=q[1],denominator=denominator)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
for ax,(name,sl) in zip(axes,[('Old1674',slice(0,1674)),('New30',slice(1674,None))]):
    ax.scatter(squared[0][:,sl].sum(axis=0),squared[1][:,sl].sum(axis=0),s=12,alpha=.6)
    lim=max(squared[0][:,sl].sum(axis=0).max(),squared[1][:,sl].sum(axis=0).max())
    ax.plot([0,lim],[0,lim],'--',color='gray');ax.set_title(name+' fixed terminal rows')
    ax.set_xlabel('Masked SSE: preterminal56 critic');ax.set_ylabel('Masked SSE: final56 critic')
fig.savefig(OUT/'comparison.png',dpi=130)
assert sha(capture['snapshot'])==capture['snapshot_sha256']
for v in binding.values(): assert sha(v['path'])==v['sha256']
report=dict(passed=True,time=time.time(),groups=groups,preterminal_steps=before['steps'],final_steps=after['steps'],
            preterminal_replay_prefix_exact=True,weights_and_forward_rng_unchanged=True,
            final_terminal_health_reproduced=True,new_physics=0,optimizer_updates=0,replay_writes=0,
            convergence_claim=False,causal_claim=False,
            values_sha256=sha(OUT/'values.npz'),plot_sha256=sha(OUT/'comparison.png'),
            limitation=plan['limitation'])
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
