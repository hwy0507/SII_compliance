from pathlib import Path
import json,time,hashlib,ast,re,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_recovery77_loss_20261029_v1';OUT=B/'runs/parameter_recovery78_loss_20261029_v1';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();records=[]
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py']:
 s=(OLD/name).read_text();v=s.replace('parameter_partial75_recovery_cycle77_20261029_v1','parameter_partial75_recovery_cycle78_20261029_v1').replace('complete77','complete78').replace('Complete77','Complete78').replace('full77','full78')
 v=v.replace('if c in (76,77):','if c in (76,77,78):')
 if name=='audit.py':
  assert ',73,74,76,77]:' in v;v=v.replace(',73,74,76,77]:',',73,74,76,77,78]:').replace('Reward49-74 plus76-77 is descriptive','Reward49-74 plus76-78 is descriptive')
 if name in ['paired_gate.py','review_saved.py']:
  v=v.replace('[76,77]','[77,78]');v=re.sub('reward76|reward77',lambda m:{'reward76':'reward77','reward77':'reward78'}[m[0]],v)
  v=v.replace('Comparison76to77','Comparison77to78')
 ast.parse(v);(OUT/name).write_text(v);(OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(OLD/name),tofile=str(OUT/name))));records.append(dict(name=name,parent_sha256=sha(OLD/name),sha256=sha(OUT/name)))
 for node in ast.parse(v).body:
  if isinstance(node,ast.FunctionDef) and node.name=='episode_file':
   ns={'B':B};exec(compile(ast.Module(body=[node],type_ignores=[]),'<path-regression>','exec'),ns)
   for m in ['impedance','admittance','vmc']:
    assert ns['episode_file'](74,m)==B/f'runs/parameter_capacity_pool30_cycle74_20261026_v1/{m}/train/episodes.jsonl'
    for c in [76,77,78]:assert ns['episode_file'](c,m)==B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/{m}/train/episodes.jsonl'
    try:ns['episode_file'](75,m)
    except ValueError:pass
    else:raise AssertionError('Incomplete75 accepted')
assert 'reward76' not in (OUT/'paired_gate.py').read_text() and '[76,77]' not in (OUT/'review_saved.py').read_text()
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=records,path_regression_74_76_77_78_and_reject75=True,history49_74_and76_77_retained=True,new_full78_loss=True,paired77_78=True,original_math_and_gate_unchanged=True,registered_before78_training=True,automatic_training=False),indent=2)+'\n')
print('Full78 loss/paired77-78 sources prepared; no waiter')
