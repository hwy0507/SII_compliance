from pathlib import Path
import json,hashlib,time,os,math,statistics,itertools
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/parameter_capacity_pool30_cycle27_20261026_v1/first5000_loss_audit'
os.sched_setaffinity(0,{52})
reg=json.loads((out/'REGISTRATION.json').read_text());assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==reg['source_sha256']
assert reg['records_per_method']==5000
limit=time.monotonic()+1800
results={}
try:
 for m in ['impedance','admittance','vmc']:
  source=Path(reg['inputs'][m]);parent=reg['parent_steps'][m]
  while True:
   assert time.monotonic()<limit
   assert not (source.parent/'FAILURE.json').exists()
   if source.exists():
    with source.open('rb') as f:raw=list(itertools.islice(f,5000))
    if len(raw)==5000 and all(x.endswith(b'\n') for x in raw):break
   time.sleep(5)
  rows=[json.loads(x) for x in raw]
  assert [r['step'] for r in rows]==list(range(parent+1,parent+5001))
  assert all(math.isfinite(v) for r in rows for v in r.values() if isinstance(v,(float,int)))
  metrics={}
  for k in ['agent_train/q_loss','agent_train/actor_entropy','agent_train/entropy_coefficient']:
   vs=[r[k] for r in rows];metrics[k]=dict(first5000_mean=statistics.mean(vs),last1000_mean=statistics.mean(vs[-1000:]),minimum=min(vs),maximum=max(vs))
  results[m]=dict(source=str(source),prefix_sha256=hashlib.sha256(b''.join(raw)).hexdigest(),first_step=rows[0]['step'],last_step=rows[-1]['step'],records=5000,finite=True,metrics=metrics)
 (out/'REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),methods=results,new_physics=0,optimizer_updates=0,convergence_claim=False,scope='Exactly first5000 new27 optimizer records; last1000 is within this fixed early prefix. Investigates response to26 late loss spikes. Not full-cycle health, reward stability, or causal proof.'),indent=2)+'\n')
except BaseException as error:
 (out/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(error)))+'\n');raise
