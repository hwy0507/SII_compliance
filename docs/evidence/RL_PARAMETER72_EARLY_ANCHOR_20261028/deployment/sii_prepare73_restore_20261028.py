from pathlib import Path
import json,hashlib,ast,re,difflib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runtime/prepare_parameter72_20261028_v1';new=B/'runtime/prepare_parameter73_20261028_v1';new.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
mapping={'00071':'00072','00072':'00073','71':'72','72':'73'};items=[]
for name in ['prepare_parameter72.py','wait_prepare.py','launch_parameter72.py','startup72.py']:
 src=old/name;dst=new/name.replace('72','73');a=src.read_text();protected={};masked=a
 for literal in ['68_70','68-70','71_73','71-73','[71,72,73]']:
  if literal in masked:
   key='__WINDOW_'+chr(65+len(protected))+'__';protected[key]=literal;masked=masked.replace(literal,key)
 def protect(m):
  key='__HASH_'+chr(65+len(protected))+'__';protected[key]=m.group();return key
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,masked);counts={k:len(re.findall(r'(?<!\d)'+k+r'(?!\d)',masked)) for k in mapping}
 s=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],masked);inv={v:k for k,v in mapping.items()}
 assert re.sub(r'(?<!\d)('+'|'.join(inv)+r')(?!\d)',lambda m:inv[m.group()],s)==masked
 for k,v in protected.items():s=s.replace(k,v)
 ast.parse(s);dst.write_text(s);dst.with_name(dst.name+'.diff').write_text(''.join(difflib.unified_diff(a.splitlines(True),s.splitlines(True),fromfile=str(src),tofile=str(dst))))
 items.append(dict(name=dst.name,parent=str(src),parent_sha256=sha(src),sha256=sha(dst),token_coverage=counts,inverse_mapping_exact=True,protected_values=list(protected.values())))
assert sha(new/'wait_prepare.py')==sha(old/'wait_prepare.py')
launcher=(new/'launch_parameter73.py').read_text()
assert "current_window71_73_plan" in launcher and "['cycles']==[71,72,73]" in launcher
assert 'parameter_capacity68_70_reward_stability' in launcher and 'parameter_capacity71_73_reward_stability' in launcher
assert 'parameter_capacity72_73_reward_stability' not in launcher
write(new/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),mapping=mapping,files=items,ast_passed=True,historical68_70_review_preserved=True,current71_73_plan_binding_preserved=True,scientific_threshold_changed=False,automatic_training=False))
write(new/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,files={n:sha(new/n) for n in ['launch_parameter73.py','startup73.py']}))
r=subprocess.run([str(B/'env/bin/python'),str(new/'launch_parameter73.py')],capture_output=True,text=True)
assert r.returncode!=0 and 'DECISION73.json' in r.stderr and 'FileNotFoundError' in r.stderr
assert not (B/'runs/parameter_capacity_pool30_cycle73_20261026_v1').exists()
write(new/'UNREVIEWED_LAUNCH_REJECTION.json',dict(passed=True,time=time.time(),returncode=r.returncode,stderr=r.stderr,no_training_run_created=True))
root=B/'runs/parameter_capacity_pool30_cycle72_20261026_v1'
reg=dict(time=time.time(),jobs=dict(parameter=dict(parent_run=str(root),parent_review=str(B/'runs/parameter_capacity_pool30_cycle72_review_20261026_v1'),parent_launch_sha256=sha(root/'LAUNCH.json'),learners=read(root/'LAUNCH.json')['jobs'],monitor=read(root/'MONITOR_LAUNCH.json'),prepare_source=str(new/'prepare_parameter73.py'),prepare_source_sha256=sha(new/'prepare_parameter73.py'),python=str(B/'env/bin/python'))))
for j in reg['jobs']['parameter']['learners']+[reg['jobs']['parameter']['monitor']]:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
assert not (root/'ARCHIVE_REVIEW_FINISHED.json').exists();write(new/'REGISTRATION.json',reg)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');cmd=[str(B/'env/bin/python'),str(new/'wait_prepare.py'),'parameter']
with (new/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
j=dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),registration_sha256=sha(new/'REGISTRATION.json'),source_sha256=sha(new/'wait_prepare.py'),command=cmd,automatic_training=False)
write(new/'parameter_LAUNCH.json',j);print(json.dumps(j,indent=2))
