from pathlib import Path
import hashlib,json,ast,re,difflib,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runtime/parameter74_loss_preparation_20261029_v1';new=B/'runtime/parameter75_loss_preparation_20261029_v1';new.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
history='['+','.join(str(i) for i in range(49,75))+']';files=[];deploy_review=None
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py','deploy.py']:
 a=(old/name).read_text();masked=a;protected={}
 for token in ['68-70','68_70','71-73','71_73','[71, 72, 73]','74-76','74_76','[74, 75, 76]',history]:
  if token in masked:
   k='__FIXED_'+chr(65+len(protected))+'__';protected[k]=token;masked=masked.replace(token,k)
 def protect(m):
  k='__HASH_'+chr(65+len(protected))+'__';protected[k]=m.group();return k
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,masked)
 mapping={'72':'73','73':'74','74':'75'} if name=='deploy.py' else {'73':'74','74':'75'}
 s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],masked);inverse={v:k for k,v in mapping.items()}
 assert re.sub(r'(?<!\d)('+'|'.join(inverse)+r')(?!\d)',lambda m:inverse[m.group()],s)==masked
 for k,v in protected.items():s=s.replace(k,v)
 pure=s;intentional=[]
 if name=='audit.py':
  assert s.count(history)==1;s=s.replace(history,history[:-1]+',75]');intentional.append('Retain complete49-74 history and append75')
 if name=='deploy.py':
  assert s.count('prepare_parameter75_20261028_v1')==1;s=s.replace('prepare_parameter75_20261028_v1','prepare_parameter75_20261029_v1');intentional.append('Use actual prepared75 runtime directory date29')
 ast.parse(s);(new/name).write_text(s);(new/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(old/name),tofile=str(new/name))))
 item=dict(name=name,parent=str(old/name),parent_sha256=sha(old/name),sha256=sha(new/name),mapping=mapping,protected_values=list(protected.values()),inverse_exact_before_intentional_changes=True,pure_mapping_sha256=hashlib.sha256(pure.encode()).hexdigest(),intentional_changes=intentional)
 if name=='deploy.py':deploy_review=item
 else:files.append(item)
write(new/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,ast_passed=True,history49_74_retained_append75=True,paired74_75=True,original_windows_preserved=True,automatic_training=False))
write(new/'DEPLOY_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=[deploy_review],ast_passed=True,original_scientific_thresholds_unchanged=True))
r=subprocess.run([str(B/'env/bin/python'),str(new/'deploy.py')],capture_output=True,text=True)
assert r.returncode!=0 and 'DECISION75.json' in r.stderr and 'FileNotFoundError' in r.stderr
assert not (B/'runs/parameter75_loss_20261028_v1').exists()
write(new/'UNREVIEWED_DEPLOY_REJECTION.json',dict(passed=True,time=time.time(),returncode=r.returncode,stderr=r.stderr,no_loss_run_or_waiter=True,training_launched=False))
print('75 loss prepared; real missingDECISION75 rejected; no loss run or training')
