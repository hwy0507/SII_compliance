from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{53})
import numpy as np
OUT=Path(__file__).resolve().parent
r=json.loads((OUT/'REVIEW.json').read_text())
assert hashlib.sha256((OUT/'values.npz').read_bytes()).hexdigest()==r['values_sha256']
assert hashlib.sha256((OUT/'comparison.png').read_bytes()).hexdigest()==r['plot_sha256']
with np.load(OUT/'values.npz',allow_pickle=False) as x:
    assert len(x['indices'])==1704 and x['features'].shape==(1704,57)
    for name,indices in [('old1674',range(1674)),('new30',range(1674,1704)),('all1704',range(1704))]:
        sse=[];contribution=[]
        for q in [x['q_before'],x['q_after']]:
            terms=[float(x['masks'][i,j])*(float(q[i,j])-float(x['rewards'][j]))**2 for i in range(5) for j in indices]
            pop=[128*float(x['masks'][i,j])*(float(q[i,j])-float(x['rewards'][j]))**2/float(x['denominator'][i]) for i in range(5) for j in indices]
            sse.append(math.fsum(terms));contribution.append(math.fsum(pop))
        v=r['groups'][name]
        for k,value in [('masked_sse_before',sse[0]),('masked_sse_after',sse[1]),('ratio',sse[1]/sse[0]),('same_final_denominator_contribution_before',contribution[0]),('same_final_denominator_contribution_after',contribution[1])]:assert math.isclose(value,v[k],rel_tol=1e-12,abs_tol=1e-12)
(OUT/'SAVED_VALUES_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),all_group_sse_and_fixed_denominator_arithmetic_verified=True,plot_inspected=False,new_physics=0,optimizer_updates=0),indent=2)+'\n')
