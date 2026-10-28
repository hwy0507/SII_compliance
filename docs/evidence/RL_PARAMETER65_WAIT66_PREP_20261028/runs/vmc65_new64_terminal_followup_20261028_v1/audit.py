"""Compare all30 fixed new64 terminals after65 using saved CPU Q only."""
from pathlib import Path
import os,json,math,hashlib,time
os.sched_setaffinity(0,{53})
import numpy as np
OUT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def close(x,y):assert math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12),(x,y)
plan=read(OUT/'PLAN.json')
assert sha(__file__)==plan['audit_sha256']
for item in plan['inputs'].values():assert sha(item['path'])==item['sha256']
follow=Path(plan['follow65']);assert read(follow/'FINISHED.json')['completed'] and read(follow/'SAVED_VALUES_REVIEW.json')['passed']
review=read(follow/'REVIEW.json');assert review['fixed_anchor_rows']==1944 and sha(follow/'values.npz')==review['values_sha256']
before=read(plan['inputs']['new64_review']['path']);assert before['passed'] and len(before['all30'])==30
assert read(plan['inputs']['new64_label_review']['path'])['passed']
rows=[]
with np.load(plan['inputs']['values64']['path'],allow_pickle=False) as a,np.load(follow/'values.npz',allow_pickle=False) as v:
    assert len(a['indices'])==1944 and len(v['indices'])==1974
    np.testing.assert_array_equal(a['indices'],v['indices'][:1944])
    np.testing.assert_array_equal(a['rewards'],v['rewards'][:1944])
    np.testing.assert_array_equal(a['masks'],v['masks'][:,:1944])
    np.testing.assert_array_equal(a['q_after'],v['q_before'])
    np.testing.assert_array_equal(a['denominator'],v['old_denominator'])
    assert {int(i) for i in a['indices'][1914:]}=={r['replay_index'] for r in before['all30']}
    for old in before['all30']:
        k=int(np.flatnonzero(v['indices']==old['replay_index'])[0]);assert 1914<=k<1944
        target=float(v['rewards'][k]);mask=[float(x) for x in v['masks'][:,k]]
        oldq=[float(x) for x in v['q_before'][:,k]];newq=[float(x) for x in v['q_after'][:,k]]
        assert oldq==old['q'] and mask==old['masks'] and target==old['terminal_reward']
        s0=[m*(q-target)**2 for m,q in zip(mask,oldq)];s1=[m*(q-target)**2 for m,q in zip(mask,newq)]
        oldcon=math.fsum(128*s/float(d) for s,d in zip(s0,v['old_denominator']))
        newcon=math.fsum(128*s/float(d) for s,d in zip(s1,v['denominator']))
        newoldcon=math.fsum(128*s/float(d) for s,d in zip(s1,v['old_denominator']))
        close(math.fsum(s0),old['sse']);close(oldcon,old['contribution'])
        rows.append(dict(replay_index=old['replay_index'],condition=old['condition'],task64=old['task'],strict64=old['strict'],terminal_reward64=target,sse_before=math.fsum(s0),sse_after=math.fsum(s1),contribution_before=oldcon,contribution_after=newcon,after_using_old_denominator=newoldcon,q_before=oldq,q_after=newq,masks=mask))
    close(math.fsum(x['contribution_before'] for x in rows),before['new30_contribution'])
    assert len(rows)==30 and len({x['condition'] for x in rows})==30
summary=dict(sse_before=math.fsum(x['sse_before'] for x in rows),sse_after=math.fsum(x['sse_after'] for x in rows),contribution_before=math.fsum(x['contribution_before'] for x in rows),contribution_after=math.fsum(x['contribution_after'] for x in rows),after_using_old_denominator=math.fsum(x['after_using_old_denominator'] for x in rows),improved=sum(x['sse_after']<x['sse_before'] for x in rows),worsened=sum(x['sse_after']>x['sse_before'] for x in rows))
result=dict(passed=True,time=time.time(),all30=rows,summary=summary,values65_sha256=sha(follow/'values.npz'),full1944_inputs_exact=True,new_network_forward=0,new_physics=0,optimizer_updates=0,causal_claim=False,convergence_claim=False,scope='Posthoc-selected64 cohort is all30 new64 rows, compared prospectively after65 on fixed64 input/reward/masks. Allrows retained, no sample removal, no new threshold, no online gradient causal claim.')
(OUT/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
