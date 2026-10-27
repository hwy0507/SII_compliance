from pathlib import Path
import subprocess,json,time,os,hashlib
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
r=B/'runs/admittance39_40_terminal_concentration_20261027_v1';s=B/'runtime/admittance39_40_terminal_concentration_20261027_v1'
try:
 for prefix,limit in [('audit',600),('review',120)]:
  script=s/f'{prefix}_admittance39_40_terminal_concentration_20261027.py'
  reg=json.loads((r/'REGISTRATION.json').read_text());expected=reg['source_sha256'] if prefix=='audit' else reg['saved_review_source']['sha256']
  assert hashlib.sha256(script.read_bytes()).hexdigest()==expected
  subprocess.run([str(B/'env/bin/python'),str(script),'--root',str(r)],check=True,timeout=limit,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 (r/'FINISHED.json').write_text(json.dumps(dict(completed=True,time=time.time()))+'\n')
except BaseException as e:
 (r/'COORDINATOR_FAILURE.json').write_text(json.dumps(dict(error=repr(e),time=time.time()))+'\n');raise
