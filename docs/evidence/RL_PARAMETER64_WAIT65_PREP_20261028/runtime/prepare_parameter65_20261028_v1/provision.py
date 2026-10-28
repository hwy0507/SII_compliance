from pathlib import Path
import ast,re,json,hashlib,time,difflib,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runtime/prepare_parameter64_20261028_v1';out=Path(__file__).parent
run=B/'runs/parameter_capacity_pool30_cycle64_20261026_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def transform(s,mp):
 rx=re.compile(r'(?<!\d)('+ '|'.join(mp)+r')(?!\d)')
 return ''.join(x if re.fullmatch(r'[a-f0-9]{64}',x) else rx.sub(lambda m:mp[m[0]],x) for x in re.split(r'([a-f0-9]{64})',s))
mp={'00063':'00064','00064':'00065','63':'64','64':'65'}
helper='''def verified_copy(src, dst):
 src,dst=Path(src),Path(dst)
 data=src.read_bytes()
 assert data==src.read_bytes(), f'Source changed while copying: {src}'
 with dst.open('xb') as stream:
  stream.write(data);stream.flush();os.fsync(stream.fileno())
 assert dst.read_bytes()==data, f'Copied bytes differ: {dst}'
 shutil.copystat(src,dst)
 return str(dst)
'''
rows=[]
for original,target in [('prepare_parameter64.py','prepare_parameter65.py'),('launch_parameter64.py','launch_parameter65.py'),('startup64.py','startup65.py'),('wait_prepare.py','wait_prepare.py')]:
 s=(old/original).read_text();new=transform(s,mp);assert transform(new,{v:k for k,v in mp.items()})==s
 if original.startswith(('prepare_parameter','launch_parameter')):
  marker='def sha(p):';assert new.count(marker)==1;new=new.replace(marker,helper+'\n'+marker)
  new=new.replace("ignore=shutil.ignore_patterns('__pycache__'))", "ignore=shutil.ignore_patterns('__pycache__'), copy_function=verified_copy)")
  new=new.replace('shutil.copyfile(', 'verified_copy(')
 ast.parse(new);assert ('ky26288' in s)==('ky26288' in new)
 assert set(re.findall(r'2026\d{4}',s))==set(re.findall(r'2026\d{4}',new))
 assert re.findall(r'[a-f0-9]{64}',s)==re.findall(r'[a-f0-9]{64}',new)
 (out/target).write_text(new);(out/(target+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=str(old/original),tofile=str(out/target))))
 rows.append(dict(source=str(old/original),source_sha256=sha(old/original),output=str(out/target),output_sha256=sha(out/target),cycle_inverse_exact_before_copy_fix=True))
# Exercise the new buffered-copy implementation on the same original log whose fast-copy failed last turn.
ns={'Path':Path,'os':os,'shutil':__import__('shutil')};exec(helper,ns)
probe=out/'copy_probe';probe.mkdir();source=B/'runs/parameter63_loss_20261028_v1/driver.log';dest=probe/'driver.log';ns['verified_copy'](source,dest);assert source.read_bytes()==dest.read_bytes() and any(dest.read_bytes())
write(out/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,files=rows,mapping=mp,ast_passed=True,dates_owner_opaque_hashes_preserved=True,copy_change='ordinary buffered read/write, fsync, reread exact verification, preserve metadata; source scientific files unchanged',actual_copy_probe=dict(source=ref(source),copy=ref(dest)),learner_changes=False,automatic_training=False))
write(out/'LAUNCH_SOURCE_REVIEW.json',dict(passed=True,files={n:sha(out/n) for n in ['launch_parameter65.py','startup65.py']}))
# An actual unreviewed launch must fail before creating a run or dispatching a process.
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
p=subprocess.run([str(B/'env/bin/python'),str(out/'launch_parameter65.py')],capture_output=True,text=True,env=env)
assert p.returncode!=0 and 'DECISION65.json' in p.stderr and not (B/'runs/parameter_capacity_pool30_cycle65_20261026_v1').exists()
write(out/'UNREVIEWED_LAUNCH_REJECTION.json',dict(time=time.time(),passed=True,returncode=p.returncode,stderr=p.stderr,no_run_created=True,no_training_started=True))
reg=json.loads((old/'REGISTRATION.json').read_text());j=reg['jobs']['parameter'];j.update(parent_run=str(run),parent_review=str(B/'runs/parameter_capacity_pool30_cycle64_review_20261026_v1'),parent_launch_sha256=sha(run/'LAUNCH.json'),learners=json.loads((run/'LAUNCH.json').read_text())['jobs'],monitor=json.loads((run/'MONITOR_LAUNCH.json').read_text()),prepare_source=str(out/'prepare_parameter65.py'),prepare_source_sha256=sha(out/'prepare_parameter65.py'))
reg.update(time=time.time(),automatic_training=False);write(out/'REGISTRATION.json',reg)
for j in reg['jobs']['parameter']['learners']+[reg['jobs']['parameter']['monitor']]:
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert not (run/'ARCHIVE_REVIEW_FINISHED.json').exists()
with (out/'parameter_driver.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(out/'wait_prepare.py'),'parameter'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
job=dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),registration_sha256=sha(out/'REGISTRATION.json'),automatic_training=False);write(out/'parameter_LAUNCH.json',job);print(json.dumps(job,indent=2))
