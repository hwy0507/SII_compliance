from pathlib import Path
import os,json,hashlib,subprocess,time
out=Path(__file__).parent;reg=json.loads((out/'REGISTRATION.json').read_text());b=out.parents[2];os.sched_setaffinity(0,{reg['cpu']});os.nice(19)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(reg['required_review'])==reg['required_review_sha256'];d=json.loads(Path(reg['required_review']).read_text());assert d['passed'] and d['methods'][reg['controller']]['checkpoint_sha256']==reg['checkpoint_sha256']==sha(reg['checkpoint'])
deadline=time.monotonic()+1800
probe=b/'runs/serl_cycle11_batch65536_probe_20261026_v1/INDEPENDENT_REVIEW.json'
while not probe.exists():
 if time.monotonic()>deadline:raise RuntimeError('Probe still not reviewed; inspect original handle')
 time.sleep(2)
assert json.loads(probe.read_text())['passed']
rt=Path(reg['audit_runtime'])
for n,h in reg['source_hashes'].items():assert sha(rt/n)==h
cmd=[str(b/'env/bin/python'),str(rt/'evaluate_pair_parameter_20261026.py'),'--runtime',reg['runtime'],'--registration',reg['training_registration'],'--checkpoint',reg['checkpoint'],'--output',str(out/'evaluation'),'--device',reg['device'],'--learner-cpu',str(reg['cpu']),'--physics-cpu',str(reg['cpu']),'--audit-substeps']
for c in reg['case_ids']:cmd+=['--case-id',c]
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (out/'evaluator.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
(out/'EVALUATOR_LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,command=cmd,time=time.time()),indent=2)+'\n')
if p.wait()!=0:raise RuntimeError('Frozen evaluator failed; preserve evidence')
subprocess.run([str(b/'env/bin/python'),str(out/'review.py')],check=True,env=env)
(out/'FINISHED.json').write_text(json.dumps(dict(time=time.time(),scientific_review_complete=True,convergence_claim=False))+'\n')
