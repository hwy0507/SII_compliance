from pathlib import Path
import re,ast,json,hashlib,difflib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runtime/parameter73_completion_observation_driver_20261029_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();items=[]
p=Path('/tmp/sii_bootstrap68_70_independent_20261028.py');a=p.read_text();s=a.replace('parameter_capacity68_70','parameter_capacity71_73').replace('parameter68_70_bootstrap_independent_20261028_v1','parameter71_73_bootstrap_independent_20261029_v1').replace('[68,69,70]','[71,72,73]');q=Path('/tmp/sii_bootstrap71_73_independent_20261029.py');ast.parse(s);assert not q.exists();q.write_text(s);(O/q.name).write_text(s);items.append(dict(source=str(q),sha256=sha(q),parent=str(p),parent_sha256=sha(p),purpose='Independent original71-73 bootstrap, same seed and draws; run only after full report and scalar review'))
p=Path('/tmp/sii_decide_launch73_20261028.py');a=p.read_text();s=a;protected={}
for literal in ['68_70','68-70','71_73','71-73','[71,72,73]']:
 key='__KEEP_'+chr(65+len(protected))+'__';protected[key]=literal;s=s.replace(literal,key)
mapping={'71':'72','72':'73','73':'74','2154':'2184'};s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],s)
for k,v in protected.items():s=s.replace(k,v)
s=s.replace('COMPLETE70_72','COMPLETE71_72')
s=s.replace('parameter73_completion_observation_driver_20261028_v1','parameter73_completion_observation_driver_20261029_v1')
needle="parent=B/'runs/parameter_capacity_pool30_cycle73_20261026_v1'"
block="""window=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
for key,name in [('reward_window71_73','REVIEW.json'),('reward_window71_73_saved','SAVED_ARITHMETIC_REVIEW.json'),('reward_window71_73_plot','PLOT_INSPECTION.json')]:evidence[key]=ref(window/name)
assert read(window/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(window/'PLOT_INSPECTION.json')['actual_image_viewed']
evidence['original71_73_bootstrap_independent']=ref(B/'runtime/parameter71_73_bootstrap_independent_20261029_v1/REVIEW.json')
assert read(Path(evidence['original71_73_bootstrap_independent']['path']))['passed']
future=B/'runs/parameter_capacity74_76_reward_stability_20261029_v1/PLAN.json'
assert sha(future)=='d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703' and read(future)['cycles']==[74,75,76]
evidence['future_window74_76_plan']=ref(future)
"""
assert s.count(needle)==1;s=s.replace(needle,block+needle)
ast.parse(s);q=Path('/tmp/sii_decide_launch74_20261029.py');assert not q.exists();q.write_text(s);(O/q.name).write_text(s);(O/(q.name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True))))
assert ".replace('COMPLETE71_72','COMPLETE72_73')" in s
assert "original71_73_bootstrap_independent" in s and "original68_70_bootstrap_independent" in s
items.append(dict(source=str(q),sha256=sha(q),parent=str(p),parent_sha256=sha(p),purpose='Decision only after actual full73/71-73/restore/plots; bind future74-76 PLAN; original windows preserved'))
(O/'HELPER_PREPARATION_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,files=items,ast_passed=True,no_decision_or_new_training=True),indent=2)+'\n')
print('Prepared independent71-73 bootstrap and guarded74 decision helpers; neither executed')
