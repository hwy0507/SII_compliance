from pathlib import Path
import ast, difflib, hashlib, json, re, time
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OLD = B / 'runs/parameter_recovery81_loss_20261029_v1'
OUT = B / 'runs/parameter_recovery82_loss_20261029_v1'
OUT.mkdir(exist_ok=False)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
files = []
for name in ['audit.py', 'paired_gate.py', 'review_saved.py', 'wait.py']:
    old = (OLD / name).read_text()
    new = old.replace('parameter_partial75_recovery_cycle81_20261029_v1', 'parameter_partial75_recovery_cycle82_20261029_v1')
    for before, after in [('complete81', 'complete82'), ('Complete81', 'Complete82'), ('full81', 'full82')]:
        new = new.replace(before, after)
    new = new.replace('if c in (76,77,78,79,80,81):', 'if c in (76,77,78,79,80,81,82):')
    if name == 'audit.py':
        assert ',73,74,76,77,78,79,80,81]:' in new
        new = new.replace(',73,74,76,77,78,79,80,81]:', ',73,74,76,77,78,79,80,81,82]:')
        new = new.replace('Reward49-74 plus76-81 is descriptive', 'Reward49-74 plus76-82 is descriptive')
    if name in ['paired_gate.py', 'review_saved.py']:
        new = new.replace('[80,81]', '[81,82]')
        new = re.sub('reward80|reward81', lambda m: {'reward80': 'reward81', 'reward81': 'reward82'}[m[0]], new)
        new = new.replace('Comparison80to81', 'Comparison81to82')
    ast.parse(new)
    p = OUT / name
    p.write_text(new)
    (OUT / (name + '.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=str(OLD / name), tofile=str(p))))
    files.append(dict(name=name, parent_path=str(OLD / name), parent_sha256=sha(OLD / name), sha256=sha(p)))
    for node in ast.parse(new).body:
        if isinstance(node, ast.FunctionDef) and node.name == 'episode_file':
            ns = {'B': B}
            exec(compile(ast.Module(body=[node], type_ignores=[]), '<path-regression>', 'exec'), ns)
            for method in ['impedance', 'admittance', 'vmc']:
                for cycle in range(49, 75):
                    assert ns['episode_file'](cycle, method) == B / f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1/{method}/train/episodes.jsonl'
                for cycle in range(76, 83):
                    assert ns['episode_file'](cycle, method) == B / f'runs/parameter_partial75_recovery_cycle{cycle}_20261029_v1/{method}/train/episodes.jsonl'
                try: ns['episode_file'](75, method)
                except ValueError: pass
                else: raise AssertionError('Incomplete75 accepted')
assert 'reward80' not in (OUT / 'paired_gate.py').read_text()
(OUT / 'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True, time=time.time(), files=files,
    path_regression49_74_76_82_and_reject75=True, history49_74_and76_81_retained=True,
    new_full82_loss=True, paired81_82=True, original_math_and_gate_unchanged=True,
    registered_before_any82_training=True, original76_78_results_retained=True,
    prospective79_81_plan_unchanged=True, actual79_short_failed_episode_retained=True,
    automatic_training=False), indent=2) + '\n')
print('Future82 loss sources prepared, history and original79 failure retained; not deployed.')
