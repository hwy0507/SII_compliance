"""Zero-physics provenance/gate controls without reading unseen conditions."""
import argparse
import copy
from pathlib import Path
import tempfile
from unittest.mock import patch
import evaluate_contact_yield_unseen108_20261030 as adapter


def check():
 models=[dict(name=f+'_s'+str(s),family=f,seed=s) for f in adapter.development.FAMILIES for s in adapter.development.SEEDS]
 rows=[dict(method=m['name'],condition=s+'_00',task_success=True,strict_success=True,machine_compliant=True) for m in models for s in ('rod','ball','corner')]
 report=dict(status='verified_fixed27_development_diagnosis',no_model_reselection=True,no_final_test_performed=True,rows=rows,independent_replays=[dict(actor_replay_max_abs=0.,filter_replay_max_abs=0.) for _ in rows],task_successes=27,strict_successes=27,failed_ids=[])
 adapter.gate(report,models);rejected=[]
 for name,alter in [('missing_row',lambda r:r['rows'].pop()),('duplicate_row',lambda r:r['rows'].__setitem__(1,copy.deepcopy(r['rows'][0]))),('task_fail',lambda r:r['rows'][0].update(task_success=False)),('strict_fail',lambda r:r['rows'][0].update(strict_success=False)),('machine_fail',lambda r:r['rows'][0].update(machine_compliant=False)),('action_replay',lambda r:r['independent_replays'][0].update(actor_replay_max_abs=.1)),('filter_replay',lambda r:r['independent_replays'][0].update(filter_replay_max_abs=.1)),('reselection',lambda r:r.update(no_model_reselection=False)),('test_access',lambda r:r.update(no_final_test_performed=False)),('failure_hidden',lambda r:r.update(failed_ids=['failed']))]:
  bad=copy.deepcopy(report);alter(bad)
  try:adapter.gate(bad,models)
  except AssertionError:rejected.append(name)
  else:raise AssertionError(name+' accepted')
 with tempfile.TemporaryDirectory(dir=adapter.ROOT/'outputs',prefix='.adapter-control-') as temp:
  root=Path(temp);root.rmdir()
  with patch.object(adapter,'prerequisite',side_effect=AssertionError('not trained')),patch.object(adapter,'read',side_effect=AssertionError('sealed conditions must not open')) as reader:
   try:adapter.register(root)
   except AssertionError as exc:assert str(exc)=='not trained'
   else:raise AssertionError('premature registration accepted')
   assert not root.exists() and reader.call_count==0
  original=adapter.evaluator.check_registration
  with patch.object(adapter.evaluator,'run',side_effect=RuntimeError('synthetic dispatch failure')):
   try:adapter.run(root)
   except RuntimeError:pass
   else:raise AssertionError('dispatch failure swallowed')
   assert adapter.evaluator.check_registration is original
  with patch.object(adapter.evaluator,'review',side_effect=RuntimeError('synthetic review failure')):
   try:adapter.review(root,root/'review.json')
   except RuntimeError:pass
   else:raise AssertionError('review failure swallowed')
   assert adapter.evaluator.check_registration is original
 return dict(status='passed_zero_physics_unseen_adapter_controls',adapter_sha256=adapter.sha(Path(adapter.__file__)),checker_sha256=adapter.sha(Path(__file__)),rejected=rejected,sealed_conditions_not_read_on_premature_register=True,restored_original_registration_checker_after_run_and_review_errors=True,physics_episodes=0,training_updates=0,unseen_inputs_read=False,scope='Synthetic gate/provenance glue only. No registration, real final dispatch, final metric result or model-success claim.')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();adapter.write(a.output,check());print('unseen adapter gate/provenance controls passed; sealed conditions unread')
