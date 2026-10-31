from pathlib import Path
import json,time,hashlib
import numpy as np
D=Path(__file__).resolve().parent;rd=lambda p:json.loads(p.read_text());r=rd(D/'TERMINAL_DECOMPOSITION.json');plan=rd(D/'DECOMPOSITION_PLAN.json');assert r['passed'];checked={}
for m,v in r['methods'].items():
 p=Path(v['inputs']['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==v['inputs']['sha256']
 with np.load(p) as z:
  ids=z['indices'];before=np.square(z['complete92'].astype(np.float64)-z['rewards'].astype(np.float64)[:,None])*z['masks'];after=np.square(z['complete93'].astype(np.float64)-z['rewards'].astype(np.float64)[:,None])*z['masks'];flags=np.array([int(i) in plan['known_abort_indices'][m] for i in ids])
  for name,sel in [('all',np.ones(len(ids),dtype=bool)),('known_aborts',flags),('other_terminals',~flags)]:
   g=v['groups'][name];assert g['rows']==np.count_nonzero(sel)
   np.testing.assert_array_equal(g['mask_counts'],z['masks'][sel].sum(0))
   for k,x in [('sse92',before),('sse93',after),('delta',after-before)]:np.testing.assert_allclose(g[k],x[sel].sum(0),rtol=1e-11,atol=1e-8)
   for k,x in [('total92',before),('total93',after),('total_delta',after-before)]:np.testing.assert_allclose(g[k],x[sel].sum(),rtol=1e-11,atol=1e-8)
   assert g['regressing_critics']==np.flatnonzero((after-before)[sel].sum(0)>0).tolist()
  delta=(after-before).sum(1);order=np.argsort(delta,kind='stable')
  for label,pos in [('largest_increases',order[-10:][::-1]),('largest_decreases',order[:10])]:
   assert [x['replay_index'] for x in v['ranked'][label]]==ids[pos].tolist()
   for row,j in zip(v['ranked'][label],pos):np.testing.assert_allclose(row['delta'],delta[j],rtol=1e-11,atol=1e-8)
 checked[m]=dict(rows=len(ids),known_aborts=int(flags.sum()),all_saved_group_sums_counts_and_ranked_deltas_checked=True)
with (D/'DECOMPOSITION_SAVED_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=checked,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),f,indent=2);f.write('\n')
print(checked)
