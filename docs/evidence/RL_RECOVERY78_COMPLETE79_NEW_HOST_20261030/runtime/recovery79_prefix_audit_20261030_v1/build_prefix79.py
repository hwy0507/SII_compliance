from pathlib import Path
import json,time,hashlib,ast,difflib,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runs/parameter_recovery78_first5000_20261029_v1';out=B/'runs/parameter_recovery79_first5000_20261029_v1';out.mkdir(exist_ok=False);root=B/'runs/parameter_partial75_recovery_cycle79_20261029_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
changes={'parameter_partial75_recovery_cycle78_20261029_v1':root.name,"plan['cycle']==78":"plan['cycle']==79",'Descriptive first5000 of recovery78':'Descriptive first5000 of recovery79'}
files=[]
for n in ['audit.py','review_saved.py']:
 s=(old/n).read_text();v=s
 for a,b in changes.items():v=v.replace(a,b)
 back=v
 for a,b in changes.items():back=back.replace(b,a)
 assert back==s;ast.parse(v);(out/n).write_text(v);(out/(n+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True),fromfile=str(old/n),tofile=str(out/n))));files.append(dict(name=n,parent_sha256=sha(old/n),sha256=sha(out/n),inverse_exact=True))
p=read(old/'PLAN.json');p.update(time=time.time(),cycle=79,source_sha256=sha(out/'audit.py'),parent_source_sha256=sha(old/'audit.py'));p['registration']={m:dict(path=str(root/m/'REGISTRATION.json'),sha256=sha(root/m/'REGISTRATION.json')) for m in p['methods']}
(out/'PLAN.json').write_text(json.dumps(p,indent=2)+'\n');(out/'SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),files=files,changes=changes,new_training=False),indent=2)+'\n')
for n in ['audit.py','review_saved.py']:
 with (out/(n+'.log')).open('x') as f:subprocess.run([str(B/'env/bin/python'),str(out/n)],check=True,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
print(json.dumps(read(out/'REVIEW.json')['methods'],indent=2))
