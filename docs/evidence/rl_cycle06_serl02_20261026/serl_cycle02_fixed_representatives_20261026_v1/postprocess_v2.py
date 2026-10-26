from pathlib import Path
import os,json,time,subprocess
out=Path(__file__).parent;b=out.parents[1];os.sched_setaffinity(0,{54})
r=json.loads((out/'POSTPROCESS_HANDOFF.json').read_text());reg=json.loads((out/'REGISTRATION.json').read_text())
pid=r['evaluator_retained'];deadline=time.monotonic()+7200
while True:
 p=Path(f'/proc/{pid}/stat')
 if not p.exists():break
 stat=p.read_text().rsplit(')',1)[1].split()
 if stat[0]=='Z' or stat[19]!=r['evaluator_start_ticks']:break
 if time.monotonic()>deadline:raise RuntimeError('Observation timeout; evaluator not stopped')
 time.sleep(5)
result=json.loads((out/'evaluation/RESULTS.json').read_text());assert result['finished'] and len(result['episodes'])==3
assert json.loads((out/'evaluation/POLICY_UNCHANGED.json').read_text())['full_learner_state_unchanged']
rt=b/'runtime/serl_cycle02_fixed_representatives_20261026_v1'
env=dict(os.environ,PYTHONPATH=str(b/'runtime/source_train17_clock/source/tools'),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
for case in reg['case_ids']:
 folder=out/'evaluation'/case
 commands=[('summarize_published_episode_audit_20261025.py',['--method','direct','--case-id',case],'PHYSICS_REVIEW.json'),('replay_published_filter_audit_20261025.py',[],'FILTER_REVIEW.json'),('replay_published_torque_audit_20261025.py',[],'TORQUE_REVIEW.json')]
 for script,extra,name in commands:
  subprocess.run([str(b/'env/bin/python'),str(rt/script),'--episode',str(folder),'--output',str(folder/name)]+extra,check=True,env=env)
(out/'FINISHED.json').write_text(json.dumps({'time':time.time(),'episodes':3,'optimizer_updates':0,'requires_scientific_review':True,'convergence_claim':False})+'\n')
