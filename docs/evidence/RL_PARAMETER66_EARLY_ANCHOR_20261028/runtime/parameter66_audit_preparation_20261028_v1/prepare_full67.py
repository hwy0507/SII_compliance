from pathlib import Path
import re,ast,json,hashlib,time,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runtime/parameter66_loss_preparation_20261028_v1';out=B/'runtime/parameter67_loss_preparation_20261028_v1';out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def change(s,m):return re.sub('|'.join(re.escape(x) for x in sorted(m,key=len,reverse=True)),lambda x:m[x.group()],s)
rows=[]
for name in ['audit.py','paired_gate.py','review_saved.py','wait.py']:
 p=old/name;s=p.read_text();m={'cycle66_':'cycle67_','complete66':'complete67','Complete66':'Complete67','full66':'full67','Reward49-66':'Reward49-67','reward65':'reward66','reward66':'reward67','[65,66]':'[66,67]'}
 if name=='audit.py':
  h='[49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66]';m[h]=h[:-1]+',67]'
 m={k:v for k,v in m.items() if k in s};t=change(s,m);assert change(t,{v:k for k,v in m.items()})==s;ast.parse(t);assert s.count('0600')==t.count('0600') and s.count('ky26288')==t.count('ky26288') and re.findall(r'2026\d{4}',s)==re.findall(r'2026\d{4}',t)
 (out/name).write_text(t);(out/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile=str(p),tofile=str(out/name))));rows.append(dict(name=name,parent_sha256=sha(p),sha256=sha(out/name),inverse_mapping_verified=True,mapping=m))
(out/'SOURCE_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,files=rows,all49_through66_history_retained=True,appended_cycle67_only=True,condition0600_unchanged=True,ast_passed=True,registered_running_job=False,automatic_training=False,limitation='Static preparation only; no67 loss run/PLAN/waiter. Deploy and bind actual jobs only after complete66 scientific decision and actual67 launch.'),indent=2)+'\n')
p=B/'runtime/prepare_parameter66_20261028_v1/review_labels65.py';s=p.read_text();m={'64':'65','65':'66'};t=re.sub(r'(?<!\d)(64|65)(?!\d)',lambda x:m[x.group()],s);assert re.sub(r'(?<!\d)(65|66)(?!\d)',lambda x:{v:k for k,v in m.items()}[x.group()],t)==s;ast.parse(t);q=B/'runtime/prepare_parameter67_20261028_v1/review_labels66.py';assert not q.exists();q.write_text(t);q.with_suffix('.py.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile=str(p),tofile=str(q))));q.with_suffix('.SOURCE_REVIEW.json').write_text(json.dumps(dict(time=time.time(),passed=True,parent=str(p),parent_sha256=sha(p),sha256=sha(q),inverse_mapping_verified=True,ast_passed=True,actual66_review_pending=True),indent=2)+'\n')
assert not(B/'runs/parameter67_loss_20261028_v1').exists() and not(B/'runs/parameter_capacity_pool30_cycle67_20261026_v1').exists()
print('full67 loss and saved66 labels reviewer prepared; no67 training orloss run')
