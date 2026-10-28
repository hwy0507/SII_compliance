from pathlib import Path
import json,hashlib,ast,re,difflib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
old=B/'runtime/prepare_parameter70_20261028_v1';new=B/'runtime/prepare_parameter71_20261028_v1'
new.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n')
mapping={'00069':'00070','00070':'00071','69':'70','70':'71'}
extra="""# Require the original68-70 window assessment before any finite71 dispatch.
window=B/'runs/parameter_capacity68_70_reward_stability_20261028_v1'
for key,name in [('reward_window68_70','REVIEW.json'),('reward_window68_70_saved','SAVED_ARITHMETIC_REVIEW.json'),('reward_window68_70_plot','PLOT_INSPECTION.json')]:
 assert key in decision['evidence']
 assert Path(decision['evidence'][key]['path']).resolve()==(window/name).resolve()
assert read(window/'SAVED_ARITHMETIC_REVIEW.json')['passed']
assert read(window/'PLOT_INSPECTION.json')['actual_image_viewed']
"""
items=[]
for name in ['prepare_parameter70.py','wait_prepare.py','launch_parameter70.py','startup70.py']:
 src=old/name;dst=new/name.replace('70','71');a=src.read_text();hashes={}
 def protect(m):
  k='__HASH_'+chr(65+len(hashes))+'__';hashes[k]=m.group();return k
 masked=re.sub(r'\b[0-9a-f]{64}\b',protect,a)
 hits={k:len(re.findall(r'(?<!\d)'+k+r'(?!\d)',masked)) for k in mapping}
 out=re.sub(r'(?<!\d)('+'|'.join(mapping)+r')(?!\d)',lambda m:mapping[m.group()],masked)
 inverse={v:k for k,v in mapping.items()}
 assert re.sub(r'(?<!\d)('+'|'.join(inverse)+r')(?!\d)',lambda m:inverse[m.group()],out)==masked
 for k,v in hashes.items():out=out.replace(k,v)
 pure=out
 if name=='launch_parameter70.py':
  needle="for x in decision['evidence'].values():assert sha(Path(x['path']))==x['sha256']\n"
  assert out.count(needle)==1;out=out.replace(needle,needle+extra)
 ast.parse(out);dst.write_text(out)
 dst.with_name(dst.name+'.diff').write_text(''.join(difflib.unified_diff(a.splitlines(True),out.splitlines(True),fromfile=str(src),tofile=str(dst))))
 items.append(dict(parent=str(src),parent_sha256=sha(src),name=dst.name,sha256=sha(dst),token_coverage=hits,inverse_mapping_exact=True,pure_mapping_sha256=hashlib.sha256(pure.encode()).hexdigest(),explicit_window_enforcement=name=='launch_parameter70.py'))
write(new/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),mapping=mapping,files=items,ast_passed=True,window_enforcement_added=extra,scientific_threshold_changed=False,automatic_training=False))
write(new/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,files={n:sha(new/n) for n in ['launch_parameter71.py','startup71.py']}))
result=subprocess.run([str(B/'env/bin/python'),str(new/'launch_parameter71.py')],capture_output=True,text=True)
assert result.returncode!=0 and 'DECISION71.json' in result.stderr and 'FileNotFoundError' in result.stderr
assert not (B/'runs/parameter_capacity_pool30_cycle71_20261026_v1').exists()
write(new/'UNREVIEWED_LAUNCH_REJECTION.json',dict(passed=True,time=time.time(),returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,no_training_run_created=True))
root=B/'runs/parameter_capacity_pool30_cycle70_20261026_v1'
reg=dict(time=time.time(),jobs=dict(parameter=dict(parent_run=str(root),parent_review=str(B/'runs/parameter_capacity_pool30_cycle70_review_20261026_v1'),parent_launch_sha256=sha(root/'LAUNCH.json'),learners=read(root/'LAUNCH.json')['jobs'],monitor=read(root/'MONITOR_LAUNCH.json'),prepare_source=str(new/'prepare_parameter71.py'),prepare_source_sha256=sha(new/'prepare_parameter71.py'),python=str(B/'env/bin/python'))))
for j in reg['jobs']['parameter']['learners']+[reg['jobs']['parameter']['monitor']]:
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert not (root/'ARCHIVE_REVIEW_FINISHED.json').exists()
write(new/'REGISTRATION.json',reg)
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
cmd=[str(B/'env/bin/python'),str(new/'wait_prepare.py'),'parameter']
with (new/'driver.log').open('xb') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
s=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()
receipt=dict(pid=p.pid,proc_start_ticks=s[19],time=time.time(),registration_sha256=sha(new/'REGISTRATION.json'),source_sha256=sha(new/'wait_prepare.py'),command=cmd,automatic_training=False)
write(new/'parameter_LAUNCH.json',receipt);print(json.dumps(receipt,indent=2))
