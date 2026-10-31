"""Validate the three real full97 groups using the unchanged locked per-group body.

This produces partial input evidence only. The original all-nine validator must
still reject this map; no window REGISTRATION or statistics are written.
"""
from pathlib import Path
import ast,copy,hashlib,json,os,sys,time,traceback,gc
D=Path(__file__).resolve().parent;B=D.parents[1];W=B/'runs/parameter_census97_99_reward_stability_20261031_v1';V=B/'runs/parameter_census_cycle97_review_20261031_v1';RUN=B/'runs/parameter_census_cycle97_20261031_v1'
os.sched_setaffinity(0,{54});sys.path.insert(0,str(W))
import binding_rules as rules
from bind_inputs import build
rd=rules.read;ref=rules.ref

def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

def main():
 plan=rules.locked(W);source=(W/'binding_rules.py').read_text();tree=ast.parse(source)
 validator=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validate_registration')
 outer=next(x for x in validator.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='m')
 inner=next(x for x in outer.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='c')
 # Exact original per-group statements. No mocked group, changed cycle set, or reduced statistical window.
 body=copy.deepcopy(inner.body)
 fn=ast.parse('def validate_actual_group(reg,m,c,plan,check_checkpoints):\n pass\n').body[0];fn.body=body
 module=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));ns=dict(vars(rules));exec(compile(module,str(W/'binding_rules.py')+':exact_per_group_body','exec'),ns)
 assert ast.dump(fn.body[0],include_attributes=False)==ast.dump(inner.body[0],include_attributes=False)
 assert [ast.dump(x,include_attributes=False) for x in fn.body]==[ast.dump(x,include_attributes=False) for x in inner.body]
 put(D/'EXTRACTED_GROUP_SOURCE.json',dict(source=ref(W/'binding_rules.py'),ast_body_exact=True,statement_count=len(body),scope='Only original per-group checks, outer all-nine gate remains mandatory for final registration.'))
 inputs={}
 for m in rules.METHODS:
  paths=dict(protocol=RUN/m/'REGISTRATION.json',review=V/'REVIEW.json',health=V/'health/DIAGNOSIS.json',finished=V/'FINISHED.json',episodes=RUN/m/'train/episodes.jsonl',optimizer=RUN/m/'train/optimizer.jsonl',loss_plot=V/'loss/loss97.png',health_plot=V/'health/training_diagnostics.png',loss_review=V/'loss/REVIEW.json',plot_inspection=V/'PLOT_INSPECTION.json',checkpoint=B/'runs/parameter_census_cycle97_archive_20261031_v1'/m/'cycle_00097.pt')
  inputs[f'{m}:97']={k:ref(p) for k,p in paths.items()}
 put(D/'COMPLETE97_INPUT_MAP.json',inputs);reg=build(inputs);results={}
 for m in rules.METHODS:
  start=time.time();ns['validate_actual_group'](reg,m,97,plan,True);gc.collect()
  for r in inputs[f'{m}:97'].values():rules.check_ref(r)
  row=rd(V/'REVIEW.json')['methods'][m];results[m]=dict(passed=True,actual_checkpoint_loaded=True,all_original_group_checks=True,rows=row['new_transitions'],steps=row['steps'],task=row['task'],strict=row['strict'],checkpoint_sha256=inputs[f'{m}:97']['checkpoint']['sha256'],seconds=time.time()-start)
  print(m,'actual complete97 binding passed',flush=True)
 try:rules.validate_registration(W,reg,check_checkpoints=True)
 except ValueError as e:
  assert str(e)=='All nine complete input groups required';rejection=str(e)
 else:raise AssertionError('Accepted incomplete three-group window')
 absent={}
 for c in [98,99]:
  p=B/f'runs/parameter_census_cycle{c}_review_20261031_v1/FINISHED.json';assert not p.exists();absent[str(c)]=str(p)
 assert not (W/'REGISTRATION.json').exists() and not (W/'REVIEW.json').exists()
 rules.locked(W)
 put(D/'COMPLETE97_BINDING_REVIEW.json',dict(passed=True,time=time.time(),methods=results,input_map=ref(D/'COMPLETE97_INPUT_MAP.json'),extracted_source=ref(D/'EXTRACTED_GROUP_SOURCE.json'),incomplete_all_nine_rejected=rejection,missing_complete98_99=absent,locked_window=[97,98,99],source_lock=ref(W/'SOURCE_LOCK.json'),statistics_run=False,window_registration_created=False,new_physics=0,optimizer_updates=0,scope='Actual complete97 input integrity only. Full98/99 and original nine-group final binding still required; no reward stability or loss-health acceptance.'))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  put(D/'BINDING_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
