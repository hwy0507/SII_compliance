from pathlib import Path
import json,hashlib,time,sys,math,statistics,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
os.sched_setaffinity(0,{54})
phase=sys.argv[1];assert phase in ['start','end']
O=B/'runtime/parameter71_verified_wait_2248_20261028_v1'/('tail_'+phase);O.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
result={}
for m in ['impedance','admittance','vmc']:
 p=B/f'runs/parameter_capacity_pool30_cycle71_20261026_v1/{m}/train/optimizer.jsonl'
 raw=p.read_bytes();lines=raw.splitlines(keepends=True)
 if not lines[-1].endswith(b'\n'):lines.pop()
 assert len(lines)>=1000
 selected=lines[-1000:];data=b''.join(selected);out=O/(m+'.jsonl');out.write_bytes(data)
 rows=[json.loads(l) for l in selected]
 assert [r['step'] for r in rows]==list(range(rows[0]['step'],rows[-1]['step']+1))
 for r in rows:
  assert all(math.isfinite(float(v)) for v in r.values())
 fields={k:dict(mean=statistics.mean(r[k] for r in rows),minimum=min(r[k] for r in rows),maximum=max(r[k] for r in rows)) for k in rows[0] if k not in ['step','update_index']}
 size=sum(map(len,lines));offset=size-len(data)
 with p.open('rb') as f:f.seek(offset);assert f.read(len(data))==data
 result[m]=dict(source=str(p),source_complete_prefix_bytes=size,source_prefix_sha256=sha(b''.join(lines)),offset=offset,sample_sha256=sha(data),count=len(rows),first_step=rows[0]['step'],last_step=rows[-1]['step'],fields=fields)
report=dict(time=time.time(),phase=phase,methods=result,all_numeric_finite=True,all_steps_contiguous=True,all_source_spans_exact=True,source_sha256=sha(Path(__file__).read_bytes()),registered_after_available=True,convergence_claim=False,limitation='Current latest1000 only; does not replace full71 loss, fixed reward window or health review.')
(O/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
# Re-read saved bytes and independently recompute aggregates with math.fsum.
for m,v in json.loads((O/'REVIEW.json').read_text())['methods'].items():
 raw=(O/(m+'.jsonl')).read_bytes();assert sha(raw)==v['sample_sha256'];rows=[json.loads(l) for l in raw.splitlines()];assert len(rows)==1000
 for k,s in v['fields'].items():
  vals=[r[k] for r in rows];mean=math.fsum(vals)/len(vals)
  assert math.isclose(mean,s['mean'],rel_tol=1e-13,abs_tol=1e-13) and min(vals)==s['minimum'] and max(vals)==s['maximum']
(O/'SAVED_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,saved_bytes_exact=True,all_numeric_fields_finite=True,independent_fsum_arithmetic=True,convergence_claim=False),indent=2)+'\n')
print(json.dumps({m:{k:v['fields'][k] for k in ['agent_train/q_loss','agent_train/actor_loss','agent_train/entropy_coefficient']} for m,v in result.items()},indent=2))
