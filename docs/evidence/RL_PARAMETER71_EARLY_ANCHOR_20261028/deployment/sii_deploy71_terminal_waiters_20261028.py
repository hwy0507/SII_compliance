from pathlib import Path
import json,hashlib,time,subprocess,os,re
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
root=B/'runs/parameter_capacity_pool30_cycle71_20261026_v1'
for method in ['vmc','admittance']:
 old=B/f'runs/{method}70_terminal_anchor_followup_20261028_v1';new=B/f'runs/{method}71_terminal_anchor_followup_20261028_v1'
 assert not (new/'PLAN.json').exists() and not (new/'LAUNCH.json').exists()
 p=read(old/'PLAN.json');p['time']=time.time()
 p['parent_run']=str(root);p['parent_review']=str(B/'runs/parameter_capacity_pool30_cycle71_review_20261026_v1')
 p['final_checkpoint']=str(B/f'runs/parameter_capacity_pool30_cycle71_archive_20261026_v1/{method}/cycle_00071.pt')
 p['learners']=read(root/'LAUNCH.json')['jobs'];p['monitor']=read(root/'MONITOR_LAUNCH.json');p['parent_launch_sha256']=sha(root/'LAUNCH.json')
 p['helper_runtime']=str(B/'runtime/parameter_capacity_pool30_cycle71_20261026_v1')
 assert sha(Path(p['helper_runtime'])/'validate_published_finite_check_20261025.py')==p['digest_helper_sha256']
 inputs={}
 for k,v in p['inputs'].items():
  src=Path(v['path']);assert sha(src)==v['sha256']
  if k=='registration':dst=root/method/'REGISTRATION.json'
  elif k.startswith('anchor_'):dst=new/('anchor70.npz' if k=='anchor_values' else src.name)
  elif k.startswith('prior69_'):dst=old/src.name;k=k.replace('69','70')
  else:dst=src
  inputs[k]=dict(path=str(dst),sha256=sha(dst))
 p['inputs']=inputs;p['sources']={n:sha(new/n) for n in p['sources']}
 for k in ['expected_complete70_terminal_rows','registered_during70','registered_before_complete70']:p[k.replace('70','71')]=p.pop(k)
 p['fixed_anchor_rows']=2124;p['expected_complete71_terminal_rows']=2154
 p['limitation']=re.sub(r'(?<!\d)(2094|69|70)(?!\d)',lambda m:{'2094':'2124','69':'70','70':'71'}[m.group()],p['limitation'])
 for j in p['learners']+[p['monitor']]:
  s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
 assert not (root/'ARCHIVE_REVIEW_FINISHED.json').exists()
 for n in ['ANCHOR_REVIEW.json','ANCHOR_SAVED_REVIEW.json']:assert read(new/n)['passed']
 (new/'PLAN.json').write_text(json.dumps(p,indent=2)+'\n')
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 with (new/'driver.log').open('xb') as log:
  proc=subprocess.Popen([str(B/'env/bin/python'),str(new/'wait.py')],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 s=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split()
 receipt=dict(pid=proc.pid,proc_start_ticks=s[19],time=time.time(),plan_sha256=sha(new/'PLAN.json'),command=[str(B/'env/bin/python'),str(new/'wait.py')])
 (new/'LAUNCH.json').write_text(json.dumps(receipt,indent=2)+'\n');print(method,json.dumps(receipt))
