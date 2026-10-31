"""Adapt the audited96 read-only diagnosis; never mutate online97 or launch98."""
from pathlib import Path
import ast, json, hashlib, difflib, re, time

D = Path(__file__).resolve().parent
B = D.parents[1]
OLD = B / 'runtime/census96_new_terminal_diagnosis_20261031_v1'
changes = {'96':'97', '95':'96', '8623':'8713', '8533':'8623', '00096':'00097'}

def adapt(text):
    pattern = '|'.join(sorted(changes, key=len, reverse=True))
    return re.sub(pattern, lambda m: changes[m.group()], text)

review = []
for name in ['build_reference96.py', 'analyze.py', 'review_saved.py']:
    source = (OLD / name).read_text()
    adapted = adapt(source)
    final = adapted
    amendments = []
    if name == 'build_reference96.py':
        old = "assert ep['cycle']==97 and ep['steps']==1375 and ep['full_task_horizon_completed'] and ep['abort_reason'] is None"
        new = "assert ep['cycle']==97 and 0<ep['steps']<=1375;assert ep['total_steps']==t['step'];assert isinstance(ep['full_task_horizon_completed'],bool)"
        assert final.count(old) == 1
        final = final.replace(old, new)
        amendments.append(dict(old=old, new=new, reason='Preserve any actual97 aborted terminal instead of excluding it; original gate labels remain unchanged.'))
    elif name == 'analyze.py':
        old = 'assert len(trans)==1375 and trans[-1]'
        new = "assert 0<len(trans)<=1375 and len(trans)==ep['steps'] and trans[-1]"
        assert final.count(old) == 1
        final = final.replace(old, new)
        amendments.append(dict(old=old, new=new, reason='Keep finite aborted episodes in the diagnostic pair, without changing labels or original gates.'))
    path = D / adapt(name)
    with path.open('x') as f:
        f.write(final)
    ast.parse(final)
    restored = final
    for amendment in reversed(amendments):
        restored = restored.replace(amendment['new'], amendment['old'])
    assert restored == adapted
    (D / (path.name+'.diff')).write_text(''.join(difflib.unified_diff(source.splitlines(True), final.splitlines(True), fromfile=str(OLD/name), tofile=str(path))))
    review.append(dict(source=str(OLD/name), source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                       candidate=str(path), candidate_sha256=hashlib.sha256(final.encode()).hexdigest(),
                       cycle_and_population_identity_mapping=changes, explicit_amendments=amendments,
                       other_arithmetic_and_inference_unchanged=True))
with (D / 'SOURCE_REVIEW.json').open('x') as f:
    json.dump(dict(passed=True, time=time.time(), files=review, physics_steps=0, optimizer_updates=0,
        scope='Identity-only adaptation apart from explicit inclusion of actual finite aborted episodes; no scientific gates changed.'), f, indent=2)
    f.write('\n')
print('Three read-only diagnostic sources prepared')
