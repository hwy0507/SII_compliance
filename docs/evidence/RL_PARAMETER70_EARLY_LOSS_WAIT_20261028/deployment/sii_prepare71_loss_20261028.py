from pathlib import Path
import hashlib,json,ast,re,difflib,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runtime/parameter70_loss_preparation_20261028_v1';new=B/'runtime/parameter71_loss_preparation_20261028_v1';new.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n')
files=[];deploy_review=None
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py','deploy.py']:
 a=(old/name).read_text();masked=a;protected={}
 for token in ['68-70','68_70','[49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70]']:
  if token in masked:
   k='__FIXED_'+chr(65+len(protected))+'__';protected[k]=token;masked=masked.replace(token,k)
 def protect(m):
  k='__HASH_'+chr(65+len(protected))+'__';protected[k]=m.group();return k
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,masked)
 mapping={'68':'69','69':'70','70':'71'} if name=='deploy.py' else {'69':'70','70':'71'}
 # Only deploy's COMPLETE68_69 pair advances68->69. All original68-70 references above are protected.
 s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],masked)
 inverse={v:k for k,v in mapping.items()};assert re.sub(r'(?<!\d)('+'|'.join(inverse)+r')(?!\d)',lambda m:inverse[m.group()],s)==masked
 for k,v in protected.items():s=s.replace(k,v)
 pure=s;intentional=[]
 if name=='audit.py':
  before='[49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70]';after=before[:-1]+',71]';assert s.count(before)==1;s=s.replace(before,after);intentional.append('Retain all49-70 history and append71; no shifting historical cycles')
 if name=='deploy.py':
  needle="    # The original68-70 window is pending71; require its fixed PLAN, not its future verdict.\n"
  assert s.count(needle)==1
  replacement="    # Require the original68-70 completed review before a reviewed71 audit deployment.\n    required += [B / 'runs/parameter_capacity68_70_reward_stability_20261028_v1' / name\n                 for name in ['REVIEW.json', 'SAVED_ARITHMETIC_REVIEW.json', 'PLOT_INSPECTION.json']]\n"
  s=s.replace(needle,replacement)
  s=s.replace('restore and fixed window PLAN must be bound','restore and original68-70 completed review must be bound')
  assert 'original68-70 still pending71.' in s;s=s.replace('original68-70 still pending71.','original68-70 reviewed before71.')
  intentional.append('Require original68-70 complete review, independent arithmetic and actual plot alongside unchanged original65-67; no scientific threshold change')
 ast.parse(s);(new/name).write_text(s);(new/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(old/name),tofile=str(new/name))))
 item=dict(name=name,parent=str(old/name),parent_sha256=sha(old/name),sha256=sha(new/name),mapping=mapping,protected_values=list(protected.values()),inverse_exact_before_intentional_changes=True,pure_mapping_sha256=hashlib.sha256(pure.encode()).hexdigest(),intentional_changes=intentional)
 if name=='deploy.py':deploy_review=item
 else:files.append(item)
write(new/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,ast_passed=True,history49_70_retained_append71=True,paired70_71=True,original68_70_preserved=True,automatic_training=False))
write(new/'DEPLOY_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=[deploy_review],ast_passed=True,original_scientific_thresholds_unchanged=True))
r=subprocess.run([str(B/'env/bin/python'),str(new/'deploy.py')],capture_output=True,text=True)
assert r.returncode!=0 and 'DECISION71.json' in r.stderr and 'FileNotFoundError' in r.stderr
assert not (B/'runs/parameter71_loss_20261028_v1').exists()
write(new/'UNREVIEWED_DEPLOY_REJECTION.json',dict(passed=True,time=time.time(),returncode=r.returncode,stderr=r.stderr,no_loss_run_or_waiter=True,training_launched=False))
print('Four audit sources and guarded deployment prepared; actual missingDECISION71 refused with no output run')
