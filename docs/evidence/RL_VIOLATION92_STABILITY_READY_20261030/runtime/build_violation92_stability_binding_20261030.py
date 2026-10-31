from pathlib import Path
import ast,difflib,hashlib,json,time
B=Path(__file__).resolve().parent.parent;D=B/'runtime/violation92_stability_ready_20261030_v1';old=B/'runtime/violation91_stability_preparation_20261030_v1/bind_inputs.py';s=old.read_text();before=s
anchor='def setup():\n';assert s.count(anchor)==1
helper='''def bind_visual_evidence(cycle,review,inspection,loss):
 assert inspection['actual_visual_inspection'] is True
 expected={'loss_plot':review/'loss'/f'loss{cycle}.png','health_plot':review/'health/training_diagnostics.png'}
 items=inspection['plots'];assert len(items)==2
 by_path={Path(x['path']).resolve():x for x in items}
 assert len(by_path)==2 and set(by_path)=={p.resolve() for p in expected.values()}
 for p in expected.values():
  item=by_path[p.resolve()];assert item['inspected'] is True and sha(p)==item['sha256']
 assert sha(expected['loss_plot'])==loss['plot_sha256']
 return {k:ref(p) for k,p in expected.items()}

'''
s=s.replace(anchor,helper+anchor)
a=" assert full['passed'] and loss['passed'] and finished['completed'] and inspection['actual_visual_inspection']\n result={}"
b=" assert full['passed'] and loss['passed'] and finished['completed'] and inspection['actual_visual_inspection']\n visual_refs=bind_visual_evidence(cycle,review,inspection,loss)\n result={}"
assert s.count(a)==1;s=s.replace(a,b)
a="  result[f'{m}:{cycle}']={name:ref(path) for name,path in dict(protocol=run/m/'REGISTRATION.json',review=review/'REVIEW.json',health=review/'health/DIAGNOSIS.json',finished=review/'FINISHED.json',episodes=episodes,optimizer=optimizer).items()}"
b=a+"\n  result[f'{m}:{cycle}'].update(visual_refs,loss_review=ref(review/'loss/REVIEW.json'),plot_inspection=ref(review/'PLOT_INSPECTION.json'),window_plan=ref(S/'PLAN.json'),early_window_failure=ref(S/'EARLY_WINDOW_FAILURE_91.json'))"
assert s.count(a)==1;s=s.replace(a,b)
a=s.index(" if args.check_only:");z=s.index('\n else:\n',a)
s=s[:a]+''' if args.check_only:
  inputs.update(bind_cycle(91,B/'runs/parameter_violation_cycle91_20261030_v1',B/'runs/parameter_violation_cycle91_review_20261030_v1',plan,previous))
  try:bind_cycle(92,B/'runs/parameter_violation_cycle92_20261030_v1',B/'runs/parameter_violation_cycle92_review_20261030_v1',plan,previous)
  except FileNotFoundError:missing=True
  else:raise AssertionError('92 already complete; inspect before changing preparation status')
  original=read(B/'runtime/violation91_completion_20261030_v1/COMPLETE91_BINDING_REVIEW.json');assert original['passed']
  for key,group in original['inputs90_91'].items():
   assert all(inputs[key][k]==v for k,v in group.items())
  early=read(S/'EARLY_WINDOW_FAILURE_91.json');assert early['original_plan_sha256']==sha(S/'PLAN.json') and early['failed_methods']==['impedance','admittance']
  assert sha(early['source_report']['path'])==early['source_report']['sha256']
  put(D/'INPUT90_91_READY_REVIEW.json',dict(passed=True,time=time.time(),inputs90_91=inputs,previous_six_input_groups_exact=True,actual_missing_complete92_rejected=missing,actual_plots_and_loss_receipts_bound=True,original_plan_sha256=sha(S/'PLAN.json'),original_early_failure_sha256=sha(S/'EARLY_WINDOW_FAILURE_91.json'),binding_source_sha256=sha(__file__),physical_steps=0,optimizer_updates=0,statistics_evaluated=False,automatic_training=False));print('Complete90/91 core refs unchanged; plots/loss/plan/failure now bound; actual incomplete92 rejected; no full statistics')''' +s[z:]
s=s.replace("binding_source=ref(Path(__file__)),automatic_training=False", "binding_source=ref(Path(__file__)),original_early_failure=ref(S/'EARLY_WINDOW_FAILURE_91.json'),automatic_training=False")
ast.parse(s);(D/'bind_inputs.py').write_text(s);(D/'bind_inputs.py.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile=str(old),tofile='bind_inputs.py')))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1';plan=dict(time=time.time(),parent_binding=str(old),parent_sha256=sha(old),binding_sha256=sha(D/'bind_inputs.py'),original_plan_sha256=sha(S/'PLAN.json'),audit_sha256=sha(S/'audit.py'),saved_review_sha256=sha(S/'review_saved.py'),original_early_failure_sha256=sha(S/'EARLY_WINDOW_FAILURE_91.json'),scope='Add exact actual health/loss plot bytes, loss review and original plan/failure refs to final input manifest; numerical audit/statistics/thresholds unchanged. Actual complete90/91 plus missing92 refusal only; no automatic window computation or training.')
(D/'BINDING_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n');print('Prepared provenance-only binding update; original statistics unchanged')
