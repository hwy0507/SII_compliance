from pathlib import Path
import re,json,ast,difflib,hashlib,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
mapping={'00068':'00069','00069':'00070','2064':'2094','2094':'2124','68':'69','69':'70'}
def transform(s):
 hashes={}
 def protect(m):
  key='__PROTECTED_HASH_'+chr(65+len(hashes))+'__';hashes[key]=m.group();return key
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,s)
 pattern=r'(?<!\d)('+ '|'.join(mapping)+r')(?!\d)'
 hits={k:len(re.findall(r'(?<!\d)'+k+r'(?!\d)',masked)) for k in mapping}
 out=re.sub(pattern,lambda m:mapping[m.group()],masked)
 inv={v:k for k,v in mapping.items()}
 back=re.sub(r'(?<!\d)('+'|'.join(inv)+r')(?!\d)',lambda m:inv[m.group()],out);assert back==masked
 for k,v in hashes.items():out=out.replace(k,v)
 return out,hits,len(hashes)
def clone(src,dst,cp_hash=None):
 a=src.read_text();out,hits,protected=transform(a);changed=None
 if cp_hash:
  pattern=r"assert inputs\[str\(cp\)\]=='([0-9a-f]{64})'";m=re.search(pattern,out);assert m;old=m.group(1);assert out.count(old)==1;out=out.replace(old,cp_hash);changed=dict(before=old,after=cp_hash)
 ast.parse(out);assert not dst.exists();dst.write_text(out);dst.with_name(dst.name+'.diff').write_text(''.join(difflib.unified_diff(a.splitlines(True),out.splitlines(True),fromfile=str(src),tofile=str(dst))))
 return dict(name=dst.name,parent=str(src),parent_sha256=sha(src),sha256=sha(dst),mapping=mapping,token_coverage=hits,inverse_exact_before_explicit_checkpoint_hash=True,protected_sha_literals=protected,checkpoint_hash_change=changed)
for method in ['vmc','admittance']:
 old=B/f'runs/{method}69_terminal_anchor_followup_20261028_v1';new=B/f'runs/{method}70_terminal_anchor_followup_20261028_v1';new.mkdir(exist_ok=False)
 checkpoint=json.loads((B/f'runs/parameter_capacity_pool30_cycle69_review_20261026_v1/{method}_REVIEW.json').read_text())['checkpoint_sha256'];items=[]
 for name in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']:
  items.append(clone(old/name,new/name,checkpoint if name=='capture_anchor.py' else None))
 (new/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=items,ast_passed=True,historical_focus_preserved=True,old_rows=2094,expected_new_rows=2124,new_training=False),indent=2)+'\n')
 print(method,'prepared',new)
old=B/'runtime/parameter_task_label_audit69_20261028_v1';new=B/'runtime/parameter_task_label_audit70_20261028_v1';new.mkdir(exist_ok=False)
(new/'audit_labels.py').write_bytes((old/'audit_labels.py').read_bytes());assert sha(new/'audit_labels.py')==sha(old/'audit_labels.py')
items=[clone(old/'wait69.py',new/'wait70.py'),clone(B/'runtime/prepare_parameter70_20261028_v1/review_labels69.py',new/'review_labels70.py')]
(new/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=items,generic_auditor_unchanged=True,auditor_sha256=sha(new/'audit_labels.py'),ast_passed=True,automatic_training=False),indent=2)+'\n')
(B/'runs/parameter_task_label_audit70_20261028_v1').mkdir(exist_ok=False)
print('labels70 prepared')
