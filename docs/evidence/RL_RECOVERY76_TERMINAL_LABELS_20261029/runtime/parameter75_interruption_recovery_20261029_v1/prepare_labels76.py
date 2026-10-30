from pathlib import Path
import json,hashlib,ast,difflib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');old=B/'runtime/parameter_task_label_audit75_20261028_v1';out=B/'runs/parameter_recovery76_task_labels_20261029_v1';run=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1'
out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
s=(old/'audit_labels.py').read_text()
new=s.replace("    assert after == before + 1, 'Only consecutive complete cycles'", "    assert (before, after) == (74, 76), 'Recovery comparison74to76, with retained partial75 exposure'")
new=new.replace("BASE / f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1'", "run_path(cycle)").replace("BASE / f'runs/parameter_capacity_pool30_cycle{cycle}_review_20261026_v1'", "review_path(cycle)")
insert="""def run_path(cycle):
    if cycle == 75: raise ValueError('Interrupted75 has no complete labels')
    if cycle == 76: return BASE / 'runs/parameter_partial75_recovery_cycle76_20261029_v1'
    assert cycle == 74
    return BASE / 'runs/parameter_capacity_pool30_cycle74_20261026_v1'


def review_path(cycle):
    if cycle == 76: return BASE / 'runs/parameter_partial75_recovery_cycle76_review_20261029_v1'
    assert cycle == 74
    return BASE / 'runs/parameter_capacity_pool30_cycle74_review_20261026_v1'


"""
new=new.replace('def audit(before, after, output):',insert+'def audit(before, after, output):').replace("limitation='All 90", "limitation='Complete74 to recovery76 spans retained partial75 exposure, not consecutive complete cycles. All 90")
texts={'audit_labels.py':(s,new)}
s=(old/'review_labels75.py').read_text();new=s.replace('full74->75','full74->76 across retained partial75 exposure').replace('parameter_task_label_audit75_20261028_v1',out.name).replace('parameter75_loss_20261028_v1','parameter_recovery76_loss_20261029_v1').replace('FINISHED75.json','LABELS_FINISHED.json').replace('COMPLETE74_75','COMPLETE74_76').replace('[74,75]','[74,76]')
texts['review_labels76.py']=(s,new)
s=(old/'wait75.py').read_text();new=s.replace('original cycle75','recovery cycle76').replace("BASE = HERE.parent.parent", "BASE = HERE.parent.parent").replace("OUT = BASE / 'runs/parameter_task_label_audit75_20261028_v1'",'OUT = HERE').replace('PLAN75.json','PLAN.json').replace("'--after', '75'","'--after', '76'").replace('COMPLETE74_75','COMPLETE74_76').replace('FINISHED75.json','LABELS_FINISHED.json').replace('WAIT75_FAILURE.json','WAIT_FAILURE.json')
end="    (OUT / 'LABELS_FINISHED.json').write_text(json.dumps(dict(completed=True, time=time.time())) + '\\n')"
assert end in new
new=new.replace(end,end+"\n    loss = BASE / 'runs/parameter_recovery76_loss_20261029_v1'\n    while not (loss / 'SAVED_REVIEW.json').exists():\n        assert not (loss / 'WAIT_FAILURE.json').exists()\n        assert time.monotonic() < deadline, 'Saved loss review wait expired'\n        time.sleep(5)\n    subprocess.run([sys.executable, str(HERE / 'review_labels76.py')], check=True)\n    (OUT / 'FINISHED.json').write_text(json.dumps(dict(completed=True, time=time.time())) + '\\n')")
texts['wait.py']=(s,new)
for n,(s,new) in texts.items():
 ast.parse(new);(out/n).write_text(new);(out/(n+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile='original75/'+n,tofile=str(out/n))))
cmd=[str(B/'env/bin/python'),str(out/'audit_labels.py'),'--before','74','--after','76','--output',str(out/'COMPLETE74_76.json')];r=subprocess.run(cmd,capture_output=True,text=True)
assert r.returncode!=0 and 'Incomplete cycle 76' in r.stderr and not (out/'COMPLETE74_76.json').exists()
write(out/'INCOMPLETE76_REJECTION.json',dict(passed=True,time=time.time(),returncode=r.returncode,stderr=r.stderr,no_output=True))
plan=dict(time=time.time(),parent_run=str(run),parent_launch_sha256=sha(run/'LAUNCH.json'),jobs=read(run/'LAUNCH.json')['jobs'],monitor=read(run/'MONITOR_LAUNCH.json'),sources={n:sha(out/n) for n in texts},wait_seconds=14400,cycles=[74,76],retained_partial75_exposure=True,consecutive_complete_cycles=False,new_training=False)
for j in plan['jobs']+[plan['monitor']]:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
write(out/'PLAN.json',plan);write(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),sources=plan['sources'],adaptations='Explicit74/76 path mapping, interrupted75 rejection, retain all180 labels and original gates, wait for independent saved loss cross-check. No science changes.'))
with (out/'driver.log').open('x') as f:child=subprocess.Popen([str(B/'env/bin/python'),str(out/'wait.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1'))
write(out/'LAUNCH.json',dict(pid=child.pid,proc_start_ticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),plan_sha256=sha(out/'PLAN.json')))
print(read(out/'LAUNCH.json'))
