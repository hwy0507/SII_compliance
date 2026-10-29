from pathlib import Path
import re,ast,json,time,hashlib,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');p=Path('/tmp/sii_prepare73_restore_20261028.py');q=Path('/tmp/sii_prepare74_restore_20261028.py');a=p.read_text();s=a;protected={}
for literal in ['68_70','68-70','71_73','71-73','[71,72,73]']:
 key='__FIXED_'+chr(65+len(protected))+'__';protected[key]=literal;s=s.replace(literal,key)
mapping={'00071':'00072','00072':'00073','00073':'00074','71':'72','72':'73','73':'74'}
s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],s)
for k,v in protected.items():s=s.replace(k,v)
block="""# Finite74 must bind the completed original71-73 window, not just its PLAN.
completed_window=B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'
for key,name in [('reward_window71_73','REVIEW.json'),('reward_window71_73_saved','SAVED_ARITHMETIC_REVIEW.json'),('reward_window71_73_plot','PLOT_INSPECTION.json')]:
 assert key in decision['evidence']
 assert Path(decision['evidence'][key]['path']).resolve()==(completed_window/name).resolve()
assert read(completed_window/'SAVED_ARITHMETIC_REVIEW.json')['passed']
assert read(completed_window/'PLOT_INSPECTION.json')['actual_image_viewed']
"""
needle=' ast.parse(s);dst.write_text(s);'
inject=" if dst.name=='launch_parameter74.py':\n  target=\"assert read(root/'parameter_FINISHED.json')['prepared']\";assert s.count(target)==1\n  s=s.replace(target,"+repr(block)+"+target)\n  s=s.replace('its complete verdict is still future.','its complete verdict is also required before finite74.')\n ast.parse(s);dst.write_text(s);"
assert s.count(needle)==1;s=s.replace(needle,inject)
s=s.replace('scientific_threshold_changed=False,automatic_training=False','scientific_threshold_changed=False,automatic_training=False,intentional_launcher_requirement="Bind completed original71-73 review, independent arithmetic and actual plot before finite74; restore-only may prepare earlier")') if False else s
# Keep the original review schema and add an explicit description for the intentional launcher change.
s=s.replace('scientific_threshold_changed=False,automatic_training=False)', 'scientific_threshold_changed=False,automatic_training=False,intentional_launcher_requirement="Completed original71-73 review, saved arithmetic and actual plot before finite74; check-only may prepare earlier")')
ast.parse(s);assert not q.exists();q.write_text(s)
o=B/'runtime/parameter73_followups_preparation_20261028_v1';(o/q.name).write_text(s);(o/(q.name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(p),tofile=str(q))))
(o/'RESTORE74_GENERATOR_REVIEW.json').write_text(json.dumps(dict(time=time.time(),ast_passed=True,parent_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(q.read_bytes()).hexdigest(),original71_73_plan_and_completed_review_required_for_launch=True,automatic_training=False),indent=2)+'\n')
print('74 restore preparation generator ready; original71-73 completion required before finite74 dispatch')
