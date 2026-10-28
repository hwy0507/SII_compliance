"""Independent scalar reconstruction of every ranked row and aggregate."""
from pathlib import Path
import hashlib
import json
import math
import os
import time
os.sched_setaffinity(0,{53})
import numpy as np
out=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def close(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
r=read(out/'REVIEW.json');p=read(out/'PLAN.json')
assert r['passed'] and r['plan_sha256']==sha(out/'PLAN.json')
assert r['source_sha256']==sha(out/'audit.py') and r['plot_sha256']==sha(out/'ranked_terminals.png')
for item in p['inputs'].values():assert sha(Path(item['path']))==item['sha256']
expected={};before={}
with np.load(p['inputs']['values.npz']['path'],allow_pickle=False) as v:
    for i,index in enumerate(v['indices']):
        reward=float(v['rewards'][i]);terms=[];weighted=[]
        for h in range(5):
            term=float(v['masks'][h,i])*(float(v['q_after'][h,i])-reward)**2
            terms.append(term);weighted.append(128*term/float(v['denominator'][h]))
        old=math.fsum(float(v['masks'][h,i])*(float(v['q_before'][h,i])-reward)**2 for h in range(5)) if i<2004 else None
        expected[int(index)]=(math.fsum(terms),math.fsum(weighted),old,reward,terms)
        if old is not None:before[int(index)]=old
rows=r['all2034_ranked'];assert len(rows)==len(expected)==2034
assert [x['replay_index'] for x in rows]==sorted(expected,key=lambda k:(-expected[k][0],k))
for rank,row in enumerate(rows,1):
    sse,weight,old,reward,terms=expected[row['replay_index']]
    assert row['rank']==rank and row['terminal_reward']==reward
    assert row['old_fixed_row']==(old is not None)
    close(row['sse67'],sse);close(row['contribution67'],weight)
    if old is None:assert row['sse66'] is None
    else:close(row['sse66'],old)
    for a,b in zip(row['per_head_sse'],terms):close(a,b)
total=math.fsum(x[0] for x in expected.values());close(total,r['all2034_sse'])
close(math.fsum(before.values()),r['old2004_sse_before'])
close(math.fsum(expected[k][0] for k in before),r['old2004_sse_after'])
close(math.fsum(x[0] for k,x in expected.items() if k not in before),r['new30_sse'])
close(math.fsum(x[1] for x in expected.values()),r['all2034_contribution'])
for n,share in r['top_shares'].items():close(share,math.fsum(x['sse67'] for x in rows[:int(n)])/total)
assert r['improved_old']==sum(expected[k][0]<v for k,v in before.items())
assert r['worsened_old']==sum(expected[k][0]>v for k,v in before.items())
assert r['unchanged_old']==sum(expected[k][0]==v for k,v in before.items())
prior=read(Path(p['inputs']['REVIEW.json']['path']))
assert [x['replay_index'] for x in r['original_five_focus']]==[x['replay_index'] for x in prior['focus']]
for row in r['original_five_focus']:assert row==rows[row['rank']-1]
result=dict(passed=True,time=time.time(),all2034_rows_independently_recomputed=True,all_aggregates_and_original_five_focus_verified=True,source_sha256=sha(Path(__file__)),review_sha256=sha(out/'REVIEW.json'),new_forward=0,optimizer_updates=0,replay_writes=0,new_physics=0)
with (out/'SAVED_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
