from pathlib import Path
import ast,json,time,hashlib,re,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_recovery80_loss_20261029_v1';OUT=B/'runs/parameter_recovery81_loss_20261029_v1';OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py']:
 s=(OLD/name).read_text();v=s.replace('parameter_partial75_recovery_cycle80_20261029_v1','parameter_partial75_recovery_cycle81_20261029_v1').replace('complete80','complete81').replace('Complete80','Complete81').replace('full80','full81')
 v=v.replace('if c in (76,77,78,79,80):','if c in (76,77,78,79,80,81):')
 if name=='audit.py':
  assert ',73,74,76,77,78,79,80]:' in v;v=v.replace(',73,74,76,77,78,79,80]:',',73,74,76,77,78,79,80,81]:').replace('Reward49-74 plus76-80 is descriptive','Reward49-74 plus76-81 is descriptive')
 if name in ['paired_gate.py','review_saved.py']:
  v=v.replace('[79,80]','[80,81]');v=re.sub('reward79|reward80',lambda m:{'reward79':'reward80','reward80':'reward81'}[m[0]],v).replace('Comparison79to80','Comparison80to81')
 ast.parse(v);(OUT/name).write_text(v);(OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(OLD/name),tofile=str(OUT/name))));records.append(dict(name=name,parent_sha256=sha(OLD/name),sha256=sha(OUT/name)))
 for node in ast.parse(v).body:
  if isinstance(node,ast.FunctionDef) and node.name=='episode_file':
   ns={'B':B};exec(compile(ast.Module(body=[node],type_ignores=[]),'<path-regression>','exec'),ns)
   for m in ['impedance','admittance','vmc']:
    for c in range(49,75):assert ns['episode_file'](c,m)==B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl'
    for c in [76,77,78,79,80,81]:assert ns['episode_file'](c,m)==B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/{m}/train/episodes.jsonl'
    try:ns['episode_file'](75,m)
    except ValueError:pass
    else:raise AssertionError('Incomplete75 accepted')
assert 'reward79' not in (OUT/'paired_gate.py').read_text() and '[79,80]' not in (OUT/'review_saved.py').read_text()
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=records,path_regression49_74_76_81_and_reject75=True,history49_74_and76_80_retained=True,new_full81_loss=True,paired80_81=True,original_math_and_gate_unchanged=True,registered_before_any81_training=True,original76_78_results_retained=True,prospective79_81_plan_unchanged=True,actual79_short_failed_episode_retained=True,automatic_training=False),indent=2)+'\n')
print('Future81 loss sources prepared, full history/actual79 abort retained; not deployed.')
