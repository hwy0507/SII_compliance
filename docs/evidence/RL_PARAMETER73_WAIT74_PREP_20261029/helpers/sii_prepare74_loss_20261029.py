from pathlib import Path
import hashlib,json,ast,re,difflib,time,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runtime/parameter73_loss_preparation_20261028_v1';new=B/'runtime/parameter74_loss_preparation_20261029_v1';new.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
history='['+','.join(str(i) for i in range(49,74))+']';files=[];deploy_review=None
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py','deploy.py']:
 a=(old/name).read_text();masked=a;protected={}
 for token in ['68-70','68_70','71-73','71_73','[71, 72, 73]',history]:
  if token in masked:
   k='__FIXED_'+chr(65+len(protected))+'__';protected[k]=token;masked=masked.replace(token,k)
 def protect(m):
  k='__HASH_'+chr(65+len(protected))+'__';protected[k]=m.group();return k
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,masked)
 mapping={'71':'72','72':'73','73':'74'} if name=='deploy.py' else {'72':'73','73':'74'}
 s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],masked);inverse={v:k for k,v in mapping.items()}
 assert re.sub(r'(?<!\d)('+'|'.join(inverse)+r')(?!\d)',lambda m:inverse[m.group()],s)==masked
 for k,v in protected.items():s=s.replace(k,v)
 pure=s;intentional=[]
 if name=='audit.py':
  assert s.count(history)==1;s=s.replace(history,history[:-1]+',74]');intentional.append('Retain complete49-73 history and append74; no moved endpoints')
 if name=='deploy.py':
  needle='    assert set(required) <= evidence.keys()'
  assert s.count(needle)==1
  block="""    # Original71-73 must be fully reviewed before any finite74 audit deployment.
    original_window = B / 'runs/parameter_capacity71_73_reward_stability_20261028_v1'
    required += [original_window / name for name in ['REVIEW.json', 'SAVED_ARITHMETIC_REVIEW.json', 'PLOT_INSPECTION.json']]
    assert read(original_window / 'SAVED_ARITHMETIC_REVIEW.json')['passed']
    assert read(original_window / 'PLOT_INSPECTION.json')['actual_image_viewed']
    future_plan_path = B / 'runs/parameter_capacity74_76_reward_stability_20261029_v1/PLAN.json'
    required.append(future_plan_path)
    assert read(future_plan_path)['cycles'] == [74, 75, 76]
    assert sha(future_plan_path) == 'd8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703'
"""
  s=s.replace(needle,block+needle)
  s=s.replace('original71-73 fixed PLAN retained, results pending.', 'original71-73 completed review retained; prospective74-76 PLAN bound, future results pending.')
  intentional.append('Require original71-73 complete review/arithmetic/actual plot and exact prospective74-76 PLAN before deploy; do not require future74-76 results')
 ast.parse(s);(new/name).write_text(s);(new/(name+'.diff')).write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(old/name),tofile=str(new/name))))
 item=dict(name=name,parent=str(old/name),parent_sha256=sha(old/name),sha256=sha(new/name),mapping=mapping,protected_values=list(protected.values()),inverse_exact_before_intentional_changes=True,pure_mapping_sha256=hashlib.sha256(pure.encode()).hexdigest(),intentional_changes=intentional)
 if name=='deploy.py':deploy_review=item
 else:files.append(item)
write(new/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=files,ast_passed=True,history49_73_retained_append74=True,paired73_74=True,original_windows_preserved=True,automatic_training=False))
write(new/'DEPLOY_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),files=[deploy_review],ast_passed=True,original_scientific_thresholds_unchanged=True))
r=subprocess.run([str(B/'env/bin/python'),str(new/'deploy.py')],capture_output=True,text=True)
assert r.returncode!=0 and 'DECISION74.json' in r.stderr and 'FileNotFoundError' in r.stderr
assert not (B/'runs/parameter74_loss_20261028_v1').exists()
write(new/'UNREVIEWED_DEPLOY_REJECTION.json',dict(passed=True,time=time.time(),returncode=r.returncode,stderr=r.stderr,no_loss_run_or_waiter=True,training_launched=False))
print('74 loss prepared; real missingDECISION74 rejected; no loss run or training')
