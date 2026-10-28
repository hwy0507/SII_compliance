from pathlib import Path
import re,json,ast,difflib,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
mapping={'00069':'00070','00070':'00071','2094':'2124','2124':'2154','69':'70','70':'71'}
def clone(src,dst,checkpoint=None):
 a=src.read_text();hashes={}
 def protect(m):
  k='__HASH_'+chr(65+len(hashes))+'__';hashes[k]=m.group();return k
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,a);counts={k:len(re.findall(r'(?<!\d)'+k+r'(?!\d)',masked)) for k in mapping}
 s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],masked)
 inv={v:k for k,v in mapping.items()};assert re.sub(r'(?<!\d)('+'|'.join(inv)+r')(?!\d)',lambda m:inv[m.group()],s)==masked
 for k,v in hashes.items():s=s.replace(k,v)
 change=None
 if checkpoint:
  pattern=r"assert inputs\[str\(cp\)\]=='([0-9a-f]{64})'";m=re.search(pattern,s);assert m;previous=m.group(1);assert s.count(previous)==1;s=s.replace(previous,checkpoint);change=dict(before=previous,after=checkpoint)
 ast.parse(s);assert not dst.exists();dst.write_text(s);dst.with_name(dst.name+'.diff').write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(src),tofile=str(dst))))
 return dict(name=dst.name,parent=str(src),parent_sha256=sha(src),sha256=sha(dst),mapping=mapping,token_coverage=counts,inverse_exact_before_checkpoint_update=True,protected_sha_literals=len(hashes),checkpoint_hash_change=change)
for method in ['vmc','admittance']:
 old=B/f'runs/{method}70_terminal_anchor_followup_20261028_v1';new=B/f'runs/{method}71_terminal_anchor_followup_20261028_v1';new.mkdir(exist_ok=False)
 checkpoint=json.loads((B/f'runs/parameter_capacity_pool30_cycle70_review_20261026_v1/{method}_REVIEW.json').read_text())['checkpoint_sha256']
 files=[clone(old/n,new/n,checkpoint if n=='capture_anchor.py' else None) for n in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']]
 (new/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,ast_passed=True,historical_focus_preserved=True,old_rows=2124,expected_new_rows=2154,new_training=False),indent=2)+'\n');print(method,'prepared')
old=B/'runtime/parameter_task_label_audit70_20261028_v1';new=B/'runtime/parameter_task_label_audit71_20261028_v1';new.mkdir(exist_ok=False)
(new/'audit_labels.py').write_bytes((old/'audit_labels.py').read_bytes());assert sha(new/'audit_labels.py')==sha(old/'audit_labels.py')
files=[clone(old/'wait70.py',new/'wait71.py'),clone(old/'review_labels70.py',new/'review_labels71.py')]
(new/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,generic_auditor_unchanged=True,auditor_sha256=sha(new/'audit_labels.py'),ast_passed=True,automatic_training=False),indent=2)+'\n')
(B/'runs/parameter_task_label_audit71_20261028_v1').mkdir(exist_ok=False);print('labels71 prepared')
