"""Audit newly selected ESN01/MLP01 development cases; no simulation or test."""
import argparse,hashlib,json
from pathlib import Path
from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from review_v9_full_grid_eligibility_20261030 import validate_structure
from audit_special_scene_metrics_v2_20261030 import episode
from run_v9_unseen_matrix_20261030 import replay
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
root=ROOT/'outputs/nonrl_v9_full_grid_eligibility_20261030_v1';raw=(root/'execution.json').read_bytes();state=json.loads(raw);reg=read(root/'REGISTRATION.json');assert state['registration_sha256']==sha(root/'REGISTRATION.json');validate_structure(reg,state,False)
(a.output/'execution.snapshot.json').write_bytes(raw);write(a.output/'REGISTRATION.snapshot.json',reg)
keys={('esn_ridge',2026102801),('mlp_scratch',2026102801)};groups=[g for g in state['groups'] if (g['family'],g['seed']) in keys];assert len(groups)==2 and all(g['selected'] is not None for g in groups)
rows=[]
for g in groups:
 candidate=g['selected'];trial=g['trials'][-1];assert len(trial['cases'])==9 and trial['status']=='development_qualified_all_nine'
 assert sha(Path(candidate['checkpoint']))==candidate['checkpoint_sha256']
 for receipt,reference in zip(trial['cases'],reg['references']):
  folder=Path(receipt['folder']);assert receipt['identity']==reference['identity']
  assert sha(folder/'student_checkpoint.npz')==candidate['checkpoint_sha256']
  assert sha(folder/'DEMONSTRATION_QUALIFICATION.json')==receipt['qualification_sha256']
  q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
  for n,h in q['input_hashes'].items():assert sha(folder/n)==h
  cell=dict(family=g['family'],seed=g['seed'],rank=candidate['validation_rank'],identity=receipt['identity'],folder=str(folder))
  try:
   cell['independent_replay']=replay(folder)
   cell['metrics']=episode(folder,g['family']+'_s'+str(g['seed']),reference['identity'],{'rod':20.,'ball':30.,'corner':13.}[reference['scene']])
   assert all(cell['metrics'][n] for n in ['task_success','strict_success','machine_compliant'])
   cell['audit_status']='passed'
  except Exception as exc:cell.update(audit_status='failed_preserved',error=repr(exc))
  rows.append(cell);write(a.output/'progress.json',dict(completed=len(rows),expected=18,failures=sum(r['audit_status']!='passed' for r in rows)))
assert len(rows)==18
write(a.output/'REVIEW.json',dict(status='new18_development_metric_preflight_passed' if all(r['audit_status']=='passed' for r in rows) else 'failures_preserved',rows=rows,
 execution_snapshot_sha256=hashlib.sha256(raw).hexdigest(),registration_sha256=sha(root/'REGISTRATION.json'),
 source_sha256={str(x):sha(x) for x in [Path(__file__),ROOT/'tools/audit_special_scene_metrics_v2_20261030.py',ROOT/'tools/run_v9_unseen_matrix_20261030.py']},
 physics_integrations=0,final_test_performed=False,spt_computed=False,
 limitations=['Only new18 development cases; prior45 not rerun or counted as new.', 'No partial T_ref/SPT or metric-based reselection.', 'Human comfort NA; proxy not actual human comfort.']))
print(len(rows),sum(r['audit_status']=='passed' for r in rows))
