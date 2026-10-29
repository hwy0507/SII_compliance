from pathlib import Path
import json,time,hashlib,ast,re,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_recovery76_loss_20261029_v1';OUT=B/'runs/parameter_recovery77_loss_20261029_v1';OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
helper="""def episode_file(c,m):
    if c==75:raise ValueError('Interrupted75 has no complete-cycle reward')
    if c in (76,77):return B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/{m}/train/episodes.jsonl'
    return B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl'
"""
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py']:
 s=(OLD/name).read_text();v=s.replace('parameter_partial75_recovery_cycle76_20261029_v1','parameter_partial75_recovery_cycle77_20261029_v1').replace('complete76','complete77').replace('Complete76','Complete77').replace('full76','full77')
 if name!='wait.py':
  a=v.index('def episode_file(');z=v.index('\ndef sha(',a);v=v[:a]+helper+v[z:]
 if name=='audit.py':
  assert ',73,74,76]:' in v;v=v.replace(',73,74,76]:',',73,74,76,77]:').replace('Reward49-74 plus76 is descriptive','Reward49-74 plus76-77 is descriptive')
 if name in ['paired_gate.py','review_saved.py']:
  v=v.replace('[74,76]','[76,77]');v=re.sub('reward74|reward76',lambda m:{'reward74':'reward76','reward76':'reward77'}[m[0]],v)
  v=v.replace('Comparison74to76 spans retained partial75 exposure; not adjacent complete training cycles.', 'Comparison76to77 covers consecutive complete recovery cycles; retained partial75 exposure remains in both states and historical75 remains incomplete.')
 if name=='wait.py':
  v=v.replace('import json,os,time,subprocess','import json,os,time,subprocess,hashlib')
  v=v.replace("try:\n while True:","try:\n for name,h in plan['sources'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==h\n while True:")
  v=v.replace(" for name in ['audit.py','paired_gate.py']", " for name,h in plan['sources'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==h\n for name in ['audit.py','paired_gate.py']")
 ast.parse(v);(OUT/name).write_text(v);(OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(OLD/name),tofile=str(OUT/name))));records.append(dict(name=name,parent_sha256=sha(OLD/name),sha256=sha(OUT/name)))
 for node in ast.parse(v).body:
  if isinstance(node,ast.FunctionDef) and node.name=='episode_file':
   ns={'B':B};exec(compile(ast.Module(body=[node],type_ignores=[]),'<path-regression>','exec'),ns)
   for m in ['impedance','admittance','vmc']:
    assert ns['episode_file'](74,m)==B/f'runs/parameter_capacity_pool30_cycle74_20261026_v1/{m}/train/episodes.jsonl'
    for c in [76,77]:assert ns['episode_file'](c,m)==B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/{m}/train/episodes.jsonl'
    try:ns['episode_file'](75,m)
    except ValueError:pass
    else:raise AssertionError('Incomplete75 accepted')
assert 'reward74' not in (OUT/'paired_gate.py').read_text() and '[74,76]' not in (OUT/'review_saved.py').read_text()
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=records,path_regression_74_76_77_and_reject75=True,history49_74_and76_retained=True,new_full77_loss=True,paired76_77=True,original_math_and_gate_unchanged=True,registered_before77_training=True,automatic_training=False),indent=2)+'\n')
print('Full77 loss, paired76/77 and saved arithmetic sources prepared; no waiter launched')
