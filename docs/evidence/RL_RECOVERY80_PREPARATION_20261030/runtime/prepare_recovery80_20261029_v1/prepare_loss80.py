from pathlib import Path
import ast,json,time,hashlib,re,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_recovery79_loss_20261029_v1';OUT=B/'runs/parameter_recovery80_loss_20261029_v1';OUT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py']:
 s=(OLD/name).read_text();v=s.replace('parameter_partial75_recovery_cycle79_20261029_v1','parameter_partial75_recovery_cycle80_20261029_v1').replace('complete79','complete80').replace('Complete79','Complete80').replace('full79','full80')
 v=v.replace('if c in (76,77,78,79):','if c in (76,77,78,79,80):')
 if name=='audit.py':
  assert ',73,74,76,77,78,79]:' in v;v=v.replace(',73,74,76,77,78,79]:',',73,74,76,77,78,79,80]:').replace('Reward49-74 plus76-79 is descriptive','Reward49-74 plus76-80 is descriptive')
 if name in ['paired_gate.py','review_saved.py']:
  v=v.replace('[78,79]','[79,80]');v=re.sub('reward78|reward79',lambda m:{'reward78':'reward79','reward79':'reward80'}[m[0]],v).replace('Comparison78to79','Comparison79to80')
 ast.parse(v);(OUT/name).write_text(v);(OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(OLD/name),tofile=str(OUT/name))));records.append(dict(name=name,parent_sha256=sha(OLD/name),sha256=sha(OUT/name)))
 for node in ast.parse(v).body:
  if isinstance(node,ast.FunctionDef) and node.name=='episode_file':
   ns={'B':B};exec(compile(ast.Module(body=[node],type_ignores=[]),'<path-regression>','exec'),ns)
   for m in ['impedance','admittance','vmc']:
    for c in range(49,75):assert ns['episode_file'](c,m)==B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl'
    for c in [76,77,78,79,80]:assert ns['episode_file'](c,m)==B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/{m}/train/episodes.jsonl'
    try:ns['episode_file'](75,m)
    except ValueError:pass
    else:raise AssertionError('Incomplete75 accepted')
assert 'reward78' not in (OUT/'paired_gate.py').read_text() and '[78,79]' not in (OUT/'review_saved.py').read_text()
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=records,path_regression49_74_76_80_and_reject75=True,history49_74_and76_79_retained=True,new_full80_loss=True,paired79_80=True,original_math_and_gate_unchanged=True,registered_before_any80_training=True,original_prospective76_78_results_retained=True,prospective79_81_plan_unchanged=True,automatic_training=False),indent=2)+'\n')
print('Future full80 loss sources ready; previous complete histories retained; no80 loss waiter or training')
