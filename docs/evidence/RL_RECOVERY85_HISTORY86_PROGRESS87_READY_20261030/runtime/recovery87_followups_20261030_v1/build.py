from pathlib import Path
import json,time,hashlib,ast,re,subprocess,difflib
D=Path(__file__).parent;B=D.parents[1];old=B/'runtime/recovery86_followups_20261030_v1/prepare.py';src=old.read_text();mapping={'2544':'2574','2574':'2604','2514':'2544','85':'86','86':'87','84':'85'}
new=re.sub('2514|2544|2574|84|85|86',lambda m:mapping[m[0]],src);ast.parse(new);p=D/'prepare.py';p.write_text(new);(D/'prepare.py.diff').write_text(''.join(difflib.unified_diff(src.splitlines(True),new.splitlines(True),fromfile=str(old),tofile=str(p))))
a=[n.value for n in ast.walk(ast.parse(src)) if isinstance(n,ast.Constant) and type(n.value) in (int,float)];b=[n.value for n in ast.walk(ast.parse(new)) if isinstance(n,ast.Constant) and type(n.value) in (int,float)];assert [int(mapping[str(v)]) if str(v) in mapping else v for v in a]==b
q=subprocess.run([str(B/'env/bin/python'),str(p)],capture_output=True,text=True);assert q.returncode!=0 and 'cycle87_20261029_v1/LAUNCH.json' in q.stderr
r=dict(passed=True,time=time.time(),parent_source_sha256=hashlib.sha256(src.encode()).hexdigest(),source_sha256=hashlib.sha256(new.encode()).hexdigest(),all_numeric_ast_only_cycles_counts_advanced=True,missing_actual87_launch_rejected=True,stderr=q.stderr,expected86_anchor_rows=2574,expected87_rows=2604,deployed=False,automatic_training=False)
with (D/'PREPARATION_REVIEW.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print('87 labels/terminal followups prepared, not deployed')
