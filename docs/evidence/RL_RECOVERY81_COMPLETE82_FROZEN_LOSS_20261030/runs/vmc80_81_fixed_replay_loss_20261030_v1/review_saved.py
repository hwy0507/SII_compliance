"""Independent saved arithmetic and replay mapping; no new network forward."""
from pathlib import Path
import hashlib, json, math, os, statistics, time
import numpy as np
import torch
D=Path(__file__).parent
os.sched_setaffinity(0,{3});torch.set_num_threads(1)
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def close(a,b):assert math.isclose(a,b,rel_tol=2e-5,abs_tol=2e-6),(a,b)
plan=read(D/'PLAN.json');review=read(D/'REVIEW.json')
assert review['passed'] and review['batches']==512
assert sha(D/'sample_indices.npy')==review['sample_indices_sha256']
assert sha(D/'BATCHES.jsonl')==review['batches_sha256']
assert sha(D/'frozen_loss.png')==review['plot_sha256']
assert sha(D/'audit.py')==plan['audit_source_sha256']
for v in plan['inputs'].values():assert sha(v['path'])==v['sha256']
ck=torch.load(plan['inputs']['checkpoint']['path'],map_location='cpu',weights_only=False)
anchor=torch.load(plan['inputs']['anchor_checkpoint']['path'],map_location='cpu',weights_only=False)
a=anchor['replay']['arrays'];size=anchor['replay']['size']
for key,value in a.items():np.testing.assert_array_equal(value,ck['replay']['arrays'][key][:size])
indices=np.load(D/'sample_indices.npy',mmap_mode='r',allow_pickle=False)
assert indices.shape==(512,65536)
rows=[json.loads(l) for l in (D/'BATCHES.jsonl').read_text().splitlines()]
assert len(rows)==512 and [r['batch'] for r in rows]==list(range(512))
rng=np.random.default_rng(plan['seed']);rejections=0
with np.load(plan['inputs']['terminal_values']['path'],allow_pickle=False) as z:
    term_indices=z['indices'][:2394].copy();term_q=z['q_after'][:,:2394].astype(float);term_rewards=z['rewards'][:2394].astype(float);term_masks=z['masks'][:,:2394].astype(float)
assert np.array_equal(term_indices,np.flatnonzero(a['dones'][:,0])) and len(term_indices)==2394
np.testing.assert_array_equal(term_masks,a['masks'][term_indices].T)
np.testing.assert_array_equal(term_rewards,a['rewards'][term_indices,0])
max_terminal_error=0.;max_denom_error=0.
for number,row in enumerate(rows):
    while True:
        expected=rng.integers(size,size=65536)
        if np.all(a['masks'][expected].sum(axis=0)>0):break
        rejections+=1
    ix=np.asarray(indices[number]);assert np.array_equal(ix,expected)
    assert hashlib.sha256(ix.tobytes()).hexdigest()==row['sample_indices_sha256']
    masks=a['masks'][ix].T.astype(float);done=a['dones'][ix,0].astype(float)
    weights=masks*(1+127*done)[None,:];den=weights.sum(axis=1)
    assert np.array_equal(den,np.asarray(row['denominators']))
    assert int(done.sum())==row['terminal_draws']
    assert int(((ix>=plan['complete79_replay_size']) & (done==1)).sum())==row['new30_draws']
    assert int((ix==plan['focus_replay_index']).sum())==row['focus_draws']
    assert len(row['target_pair'])==2 and len(set(row['target_pair']))==2 and all(0<=n<5 for n in row['target_pair'])
    term=done==1;pos=np.searchsorted(term_indices,ix[term]);assert np.array_equal(term_indices[pos],ix[term])
    squared=(term_q[:,pos]-term_rewards[pos][None,:])**2
    contribution=float((128*squared*term_masks[:,pos]/den[:,None]).sum())
    close(contribution,row['terminal_contribution']);max_terminal_error=max(max_terminal_error,abs(contribution-row['terminal_contribution']))
    close(math.fsum(n/d for n,d in zip(row['numerators'],row['denominators'])),row['scalar_loss'])
    close(row['scalar_loss'],row['native_loss'])
    close(row['terminal_contribution']+row['nonterminal_contribution'],row['scalar_loss'])
for name in ['first_batch.npz','maximum_batch.npz','first_focus_batch.npz']:
    with np.load(D/name,allow_pickle=False) as z:
        n=int(z['batch']);row=rows[n];ix=z['indices'];assert np.array_equal(ix,indices[n])
        np.testing.assert_array_equal(z['masks'],a['masks'][ix].T)
        np.testing.assert_array_equal(z['dones'],a['dones'][ix,0])
        np.testing.assert_array_equal(z['rewards'],a['rewards'][ix,0])
        np.testing.assert_array_equal(z['target'][z['dones']==1],z['rewards'][z['dones']==1])
        per=[]
        for k in range(5):
            weights=[float(m)*(1+127*float(done)) for m,done in zip(z['masks'][k],z['dones'])]
            num=math.fsum(w*(float(q)-float(target))**2 for w,q,target in zip(weights,z['q'][k],z['target']))
            den=math.fsum(weights);close(num,row['numerators'][k]);close(den,row['denominators'][k]);per.append(num/den)
        close(math.fsum(per),row['native_loss'])
        if name=='maximum_batch.npz':assert row['native_loss']==max(r['native_loss'] for r in rows)
        if name=='first_focus_batch.npz':assert row['focus_draws']>0 and not any(r['focus_draws'] for r in rows[:n])
def quantile(values,p):
    x=sorted(values);a=(len(x)-1)*p;i=int(a);f=a-i
    return x[i]*(1-f)+x[min(i+1,len(x)-1)]*f
for key,values in [('loss',[r['native_loss'] for r in rows]),('focus_present_loss',[r['native_loss'] for r in rows if r['focus_draws']]),('focus_absent_loss',[r['native_loss'] for r in rows if not r['focus_draws']])]:
    stats=review[key];assert stats['count']==len(values)
    close(math.fsum(values)/len(values),stats['mean']);assert min(values)==stats['minimum'] and max(values)==stats['maximum']
    for p,v in zip([.5,.9,.95,.99],stats['quantiles']):close(quantile(values,p),v)
assert rejections+512==review['accepted_sampling_rng_calls']
result=dict(passed=True,time=time.time(),all512_indices_exact_from_independent_rng=True,
    full_mask_acceptance_rejections=rejections,all512_denominators_and_terminal_identity_counts_exact=True,
    all512_terminal_contributions_independently_recomputed_from_prior_cpu_values=True,
    maximum_cpu_vs_gpu_terminal_contribution_difference=max_terminal_error,
    first_maximum_firstfocus_full_scalar_loss_verified=True,all_summary_statistics_independently_verified=True,
    no_new_network_forward=True,new_physics=0,optimizer_updates=0,plot_inspected=False,
    review_sha256=sha(D/'REVIEW.json'),source_sha256=sha(__file__),
    numerical_tolerance=dict(relative=2e-5,absolute=2e-6),
    limitation='All512 terminal components checked against prior independently audited CPU Q values; nonterminal squared-error arithmetic independently checked for saved first/maximum/first-focus batches only. Original train computed every batch loss; no chronological spike replay or convergence assertion.')
with (D/'SAVED_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result),flush=True)
