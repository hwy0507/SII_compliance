from pathlib import Path
import json,hashlib,ast,difflib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runs/parameter_recovery76_task_labels_20261029_v1';out=B/'runs/parameter_recovery77_task_labels_20261029_v1';run=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1'
out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
s=(old/'audit_labels.py').read_text()
a=s.index('def run_path(cycle):');b=s.index('def audit(before, after, output):')
new=s[:a]+'''def run_path(cycle):
    assert cycle in (76,77), 'Only completed recovery76/77; interrupted75 excluded'
    return BASE / f'runs/parameter_partial75_recovery_cycle{cycle}_20261029_v1'


def review_path(cycle):
    assert cycle in (76,77), 'Only completed recovery76/77; interrupted75 excluded'
    return BASE / f'runs/parameter_partial75_recovery_cycle{cycle}_review_20261029_v1'


'''+s[b:]
new=new.replace("assert (before, after) == (74, 76), 'Recovery comparison74to76, with retained partial75 exposure'", "assert (before, after) == (76, 77), 'Consecutive complete recovery76/77 only'")
new=new.replace('Complete74 to recovery76 spans retained partial75 exposure, not consecutive complete cycles.', 'Complete recovery76 to complete recovery77; original75 remains interrupted.')
texts={'audit_labels.py':(s,new)}
s=(old/'review_labels76.py').read_text();new=s.replace('full74->76 across retained partial75 exposure','complete recovery76->77').replace('parameter_recovery76_', 'parameter_recovery77_').replace('COMPLETE74_76','COMPLETE76_77').replace('[74,76]','[76,77]');texts['review_labels77.py']=(s,new)
s=(old/'wait.py').read_text();new=s.replace('recovery cycle76','recovery cycle77').replace("'--before', '74', '--after', '76'", "'--before', '76', '--after', '77'").replace('COMPLETE74_76','COMPLETE76_77').replace('parameter_recovery76_loss','parameter_recovery77_loss').replace('review_labels76.py','review_labels77.py');texts['wait.py']=(s,new)
for n,(s,new) in texts.items():
 ast.parse(new);(out/n).write_text(new);(out/(n+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile='recovery76/'+n,tofile=str(out/n))))
cmd=[str(B/'env/bin/python'),str(out/'audit_labels.py'),'--before','76','--after','77','--output',str(out/'COMPLETE76_77.json')];r=subprocess.run(cmd,capture_output=True,text=True)
assert r.returncode!=0 and 'Incomplete cycle 77' in r.stderr and not (out/'COMPLETE76_77.json').exists()
write(out/'INCOMPLETE77_REJECTION.json',dict(passed=True,time=time.time(),returncode=r.returncode,stderr=r.stderr,no_output=True))
plan=dict(time=time.time(),parent_run=str(run),parent_launch_sha256=sha(run/'LAUNCH.json'),jobs=read(run/'LAUNCH.json')['jobs'],monitor=read(run/'MONITOR_LAUNCH.json'),sources={n:sha(out/n) for n in texts},wait_seconds=14400,cycles=[76,77],original75_interrupted=True,consecutive_complete_cycles=True,new_training=False)
for j in plan['jobs']+[plan['monitor']]:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
write(out/'PLAN.json',plan);write(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),sources=plan['sources'],adaptations='Explicit recovery76/77 paths, interrupted75 rejection, original all180 labels and gates, independent saved loss cross-check unchanged. No science changes.'))
with (out/'driver.log').open('x') as f:child=subprocess.Popen([str(B/'env/bin/python'),str(out/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
write(out/'LAUNCH.json',dict(pid=child.pid,proc_start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(out/'PLAN.json')))
print(read(out/'LAUNCH.json'))
