from pathlib import Path
import ast,hashlib,json,time,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=B/'runtime/parameter74_completion_preparation_20261029_v1';D.mkdir(exist_ok=False)
p=Path('/tmp/sii_decide_launch74_20261029.py');q=Path('/tmp/sii_decide_launch75_20261029.py');a=p.read_text();s=a
# Context replacements preserve all fixed scientific windows and their existing reviews.
changes={
"root=B/'runtime/prepare_parameter74_20261028_v1';out=B/'runs/parameter_capacity_pool30_cycle74_20261026_v1'":"root=B/'runtime/prepare_parameter75_20261029_v1';out=B/'runs/parameter_capacity_pool30_cycle75_20261026_v1'",
"old=read(B/'runtime/prepare_parameter73_20261028_v1/DECISION73.json')":"old=read(B/'runtime/prepare_parameter74_20261028_v1/DECISION74.json')",
"p=p.replace('cycle72','cycle73')":"p=p.replace('cycle73','cycle74')",
"p=p.replace('parameter72_loss','parameter73_loss')":"p=p.replace('parameter73_loss','parameter74_loss')",
"p=p.replace('cycle73','cycle74')\n elif key in":"p=p.replace('cycle74','cycle75')\n elif key in",
"p.replace('audit72_','audit73_').replace('COMPLETE71_72','COMPLETE72_73').replace('FINISHED72','FINISHED73')":"p.replace('audit73_','audit74_').replace('COMPLETE72_73','COMPLETE73_74').replace('FINISHED73','FINISHED74')",
"p=p.replace('72_terminal','73_terminal')":"p=p.replace('73_terminal','74_terminal')",
"parent=B/'runs/parameter_capacity_pool30_cycle73_20261026_v1';reviewroot=B/'runs/parameter_capacity_pool30_cycle73_review_20261026_v1'":"parent=B/'runs/parameter_capacity_pool30_cycle74_20261026_v1';reviewroot=B/'runs/parameter_capacity_pool30_cycle74_review_20261026_v1'",
"runs/parameter73_loss_20261028_v1/SAVED_REVIEW.json":"runs/parameter74_loss_20261028_v1/SAVED_REVIEW.json",
"runs/parameter_task_label_audit73_20261028_v1/COMPLETE72_73_SAVED_REVIEW.json":"runs/parameter_task_label_audit74_20261028_v1/COMPLETE73_74_SAVED_REVIEW.json",
"runs/{m}73_terminal_anchor_followup_20261028_v1":"runs/{m}74_terminal_anchor_followup_20261028_v1",
"['fixed_anchor_rows']==2184":"['fixed_anchor_rows']==2214",
"runtime/parameter73_completion_observation_driver_20261029_v1/CONTINUATION_REASON.txt":"runtime/parameter74_completion_preparation_20261029_v1/CONTINUATION_REASON.txt",
"parent_cycle=73,new_cycle=74":"parent_cycle=74,new_cycle=75",
"DECISION74.json":"DECISION75.json",
"Decision74":"Decision75",
"launch_parameter74.py":"launch_parameter75.py"}
# Apply simultaneously, so newly inserted parent decision74 is not remapped to75.
import re
pattern=re.compile('|'.join(re.escape(k) for k in sorted(changes,key=len,reverse=True)))
counts={k:a.count(k) for k in changes};assert all(counts.values()),counts
s=pattern.sub(lambda m:changes[m.group()],a)
# Avoid inheriting the old continuation-reason evidence into the new decision.
needle="  p=p.replace('audit73_','audit74_').replace('COMPLETE72_73','COMPLETE73_74').replace('FINISHED73','FINISHED74')"
assert needle in s
needle=" evidence[key]=ref(Path(p))";assert s.count(needle)==1;s=s.replace(needle," if key=='continuation_reason':continue\n"+needle)
ast.parse(s);assert not q.exists();q.write_text(s);(D/q.name).write_text(s);(D/(q.name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(p),tofile=str(q))))
# Inspect source relationships independently of the rewrite counts.
assert "old=read(B/'runtime/prepare_parameter74_20261028_v1/DECISION74.json')" in s
assert "elif key=='check_only' or key.startswith('restore_'):p=p.replace('cycle74','cycle75')" in s
assert "if key in ['parent_review','health','health_plot']:p=p.replace('cycle73','cycle74')" in s
assert "['cycles']==[71,72,73]" in s and "['cycles']==[74,75,76]" in s
assert "reason_path.read_text()" in s and "parent_cycle=74,new_cycle=75" in s
assert not (D/'CONTINUATION_REASON.txt').exists() and not (B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json').exists()
(D/'SOURCE_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,parent_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),helper_sha256=hashlib.sha256(q.read_bytes()).hexdigest(),context_replacement_counts=counts,ast_passed=True,parent74_restore75_label73_74_terminal2214_checked=True,original71_73_and74_76_preserved=True,reason_not_yet_written=True,helper_not_executed=True,automatic_training=False),indent=2)+'\n');print('75 decision helper prepared only; actual74 full analysis and reason still required')
