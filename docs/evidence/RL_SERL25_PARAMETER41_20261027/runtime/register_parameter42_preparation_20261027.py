from pathlib import Path
import re,ast,json,time,hashlib,subprocess,os,difflib
b=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');rt=b/'runtime';o=b/'runs/parameter42_preparation_registration_20261027_v1';o.mkdir()
old=json.loads((b/'runs/parameter_capacity_pool30_cycle40_20261026_v1/LAUNCH.json').read_text());launch=json.loads((b/'runs/parameter_capacity_pool30_cycle41_20261026_v1/LAUNCH.json').read_text());mon=json.loads((b/'runs/parameter_capacity_pool30_cycle41_20261026_v1/MONITORS.json').read_text());oldmon=json.loads((b/'runs/parameter_capacity_pool30_cycle40_20261026_v1/MONITORS.json').read_text());pids=[j['pid'] for j in launch['jobs']];assert all(Path(f'/proc/{p}').exists() for p in pids)
pidmap={str(a['pid']):str(c['pid']) for a,c in zip(old['jobs'],launch['jobs'])};pidmap[str(oldmon['review']['pid'])]=str(mon['review']['pid'])
def adapt(s):
 s=re.sub(r'(cycle_000|cycle|Cycle|capacity|parameter|complete|Original|Prepared|before)(40|41)',lambda m:m[1]+str(int(m[2])+1),s)
 s=re.sub(r"(parent_cycle(?:'\])?=|\['cycle'\]==)(40|41)",lambda m:m[1]+str(int(m[2])+1),s)
 s=re.sub(r"('--cycle',')(40|41)(')",lambda m:m[1]+str(int(m[2])+1)+m[3],s)
 return re.sub('|'.join(pidmap),lambda m:pidmap[m[0]],s)
records=[];diff=[]
for name in ['prepare_parameter_capacity41_20261026.py','launch_parameter_capacity41_20261026.py','setup_parameter_capacity41_monitors_20261026.py','wait_prepare_parameter_capacity41_20261026.py','assign_parameter40_review_released_cpu_20261026.py']:
 src=rt/name;dst=rt/adapt(name);assert not dst.exists();s=adapt(src.read_text());ast.parse(s);dst.write_text(s);records.append(dict(path=str(dst),sha256=hashlib.sha256(dst.read_bytes()).hexdigest()));diff.extend(difflib.unified_diff(src.read_text().splitlines(True),s.splitlines(True),fromfile=name,tofile=dst.name))
s=(rt/'prepare_parameter_capacity42_20261026.py').read_text();assert "oldname='parameter_capacity_pool30_cycle41_20261026_v1'" in s and "name='parameter_capacity_pool30_cycle42_20261026_v1'" in s;assert "ck['cycle']==41" in s and "['parent_cycle']==23" in s and 'zip([13,26,39],commands)' in s
s=(rt/'setup_parameter_capacity42_monitors_20261026.py').read_text();assert "replace('cycle41','cycle42')" in s and "replace(\"['cycle']==41\",\"['cycle']==42\")" in s
(o/'SOURCE.diff').write_text(''.join(diff));reg=dict(time=time.time(),parent_cycle=41,next_cycle=42,parent_learners=pids,parent_review=mon['review']['pid'],timeout_seconds=7200,automatic_training=False,files=records,static_checks_passed=True,scope='Preparation only; full41, original39-41 stability and frozen41 plan remain independent. Separate scientific decision required before any42 training.')
(o/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n');procs={};env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
for key,name in [('prepare','wait_prepare_parameter_capacity42_20261026.py'),('released_cpu','assign_parameter41_review_released_cpu_20261026.py')]:
 with (o/(key+'.log')).open('x') as f:p=subprocess.Popen([str(b/'env/bin/python'),str(rt/name)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 procs[key]=dict(pid=p.pid,script=str(rt/name))
reg['processes']=procs;(o/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n');print(procs)
