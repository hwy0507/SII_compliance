from pathlib import Path
import re,ast,json,time,hashlib,subprocess,os,difflib
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');rt=b/'runtime';o=b/'runs/parameter41_preparation_registration_20261027_v1';o.mkdir()
launch=json.loads((b/'runs/parameter_capacity_pool30_cycle40_20261026_v1/LAUNCH.json').read_text());mon=json.loads((b/'runs/parameter_capacity_pool30_cycle40_20261026_v1/MONITORS.json').read_text());pids=[j['pid'] for j in launch['jobs']];assert len(pids)==3 and all(Path(f'/proc/{p}').exists() for p in pids)
files=['prepare_parameter_capacity40_20261026.py','launch_parameter_capacity40_20261026.py','setup_parameter_capacity40_monitors_20261026.py','wait_prepare_parameter_capacity40_20261026.py','assign_parameter39_review_released_cpu_20261026.py'];pidmap=dict(zip(['3314522','3314523','3314524'],map(str,pids)));pidmap['3314529']=str(mon['review']['pid'])
def adapt(s):
 s=re.sub(r'(cycle_000|cycle|Cycle|capacity|parameter|complete|Original|Prepared|before)(39|40)',lambda m:m[1]+str(int(m[2])+1),s)
 s=re.sub(r"(parent_cycle(?:'\])?=|\['cycle'\]==)(39|40)",lambda m:m[1]+str(int(m[2])+1),s)
 s=re.sub(r"('--cycle',')(39|40)(')",lambda m:m[1]+str(int(m[2])+1)+m[3],s)
 s=re.sub('|'.join(pidmap),lambda m:pidmap[m[0]],s)
 return s
records=[];diffs=[]
for name in files:
 src=rt/name;dst=rt/adapt(name);assert not dst.exists();old=src.read_text();new=adapt(old);ast.parse(new);dst.write_text(new);records.append(dict(path=str(dst),sha256=hashlib.sha256(dst.read_bytes()).hexdigest()));diffs.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=name,tofile=dst.name))
p=(rt/'prepare_parameter_capacity41_20261026.py').read_text();assert "oldname='parameter_capacity_pool30_cycle40_20261026_v1'" in p and "name='parameter_capacity_pool30_cycle41_20261026_v1'" in p
assert "ck['cycle']==40" in p and "parent_cycle']=40" in p and 'parent_cycle=40' in p
assert 'zip([13,26,39],commands)' in p and "['parent_cycle']==23" in p
s=(rt/'setup_parameter_capacity41_monitors_20261026.py').read_text();assert "replace('cycle40','cycle41')" in s and "replace(\"['cycle']==40\",\"['cycle']==41\")" in s
for m in ['impedance','admittance','vmc']:
 reg=json.loads((b/'runs/parameter_capacity_pool30_cycle40_20261026_v1'/m/'REGISTRATION.json').read_text());assert reg['replay_capacity_stage']['parent_cycle']==23
(o/'SOURCE.diff').write_text(''.join(diffs))
reg=dict(time=time.time(),parent_cycle=40,next_cycle=41,parent_learners=pids,parent_review=mon['review']['pid'],timeout_seconds=7200,automatic_training=False,files=records,static_checks_passed=True,replacement='Simultaneous contextual stage replacements; CPU39 and historical capacity entry23 unchanged; no formal training until separate scientific review.')
(o/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n')
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');procs={}
for key,name in [('prepare','wait_prepare_parameter_capacity41_20261026.py'),('released_cpu','assign_parameter40_review_released_cpu_20261026.py')]:
 with (o/(key+'.log')).open('x') as f:pr=subprocess.Popen([str(b/'env/bin/python'),str(rt/name)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 procs[key]=dict(pid=pr.pid,script=str(rt/name))
reg['processes']=procs;(o/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n');print(procs)
