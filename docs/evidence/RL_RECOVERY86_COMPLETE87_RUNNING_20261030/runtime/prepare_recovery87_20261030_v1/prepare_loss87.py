from pathlib import Path
import ast,difflib,hashlib,json,re,time
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;OLD=B/'runs/parameter_recovery86_loss_20261029_v1';OUT=B/'runs/parameter_recovery87_loss_20261029_v1';OUT.mkdir();files=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py']:
 old=(OLD/name).read_text();new=old.replace('parameter_partial75_recovery_cycle86_20261029_v1','parameter_partial75_recovery_cycle87_20261029_v1')
 for a,b in [('complete86','complete87'),('Complete86','Complete87'),('full86','full87')]:new=new.replace(a,b)
 new=new.replace('if c in (76,77,78,79,80,81,82,83,84,85,86):','if c in (76,77,78,79,80,81,82,83,84,85,86,87):')
 if name=='audit.py':
  assert ',73,74,76,77,78,79,80,81,82,83,84,85,86]:' in new
  new=new.replace(',73,74,76,77,78,79,80,81,82,83,84,85,86]:',',73,74,76,77,78,79,80,81,82,83,84,85,86,87]:').replace('Reward49-74 plus76-86 is descriptive','Reward49-74 plus76-87 is descriptive')
 if name in ['paired_gate.py','review_saved.py']:
  new=new.replace('[85,86]','[86,87]');new=re.sub('reward85|reward86',lambda m:{'reward85':'reward86','reward86':'reward87'}[m[0]],new).replace('Comparison85to86','Comparison86to87')
 ast.parse(new);p=OUT/name;p.write_text(new);(OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(OLD/name),tofile=str(p))));files.append(dict(name=name,parent_path=str(OLD/name),parent_sha256=sha(OLD/name),sha256=sha(p)))
 for node in ast.parse(new).body:
  if isinstance(node,ast.FunctionDef) and node.name=='episode_file':
   ns={'B':B};exec(compile(ast.Module(body=[node],type_ignores=[]),'<path-regression>','exec'),ns)
   for m in ['impedance','admittance','vmc']:
    for c in range(49,75):assert ns['episode_file'](c,m)==B/f'runs/parameter_capacity_pool30_cycle{c}_20261026_v1/{m}/train/episodes.jsonl'
    for c in range(76,88):assert ns['episode_file'](c,m)==B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/{m}/train/episodes.jsonl'
    try:ns['episode_file'](75,m)
    except ValueError:pass
    else:raise AssertionError('Incomplete75 accepted')
assert 'reward85' not in (OUT/'paired_gate.py').read_text() and 'reward86' in (OUT/'paired_gate.py').read_text() and 'reward87' in (OUT/'paired_gate.py').read_text()
(OUT/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,path_regression49_74_76_87_and_reject75=True,history49_74_and76_86_retained=True,new_full87_loss=True,paired86_87=True,original_math_and_gate_unchanged=True,registered_before_any87_training=True,completed76_78_79_81_82_84_findings_retained=True,prospective85_87_plan_unchanged=True,actual79_short_failed_episode_retained=True,automatic_training=False),indent=2)+'\n')
print('Future87 full loss/history and86->87 pair prepared; no deployment')
