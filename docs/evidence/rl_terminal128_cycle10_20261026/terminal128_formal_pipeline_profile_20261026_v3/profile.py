from pathlib import Path
import os,json,time,subprocess
os.sched_setaffinity(0,{52})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent
jobs={'direct':(2818100,'serl_pool30_cycle05_06_20261026_v2/direct'),'impedance':(3818446,'parameter_terminal128_cycle10_20261026_v3/impedance/train'),'admittance':(3818448,'parameter_terminal128_cycle10_20261026_v3/admittance/train'),'vmc':(3818450,'parameter_terminal128_cycle10_20261026_v3/vmc/train')}
def proc(pid):
 try:
  s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
  return dict(pid=pid,start=s[19],state=s[0],cpu_s=(int(s[11])+int(s[12]))/os.sysconf('SC_CLK_TCK'))
 except FileNotFoundError:return None
def children(pid):
 try:return [int(x) for x in Path('/proc',str(pid),'task',str(pid),'children').read_text().split()]
 except FileNotFoundError:return []
identities={m:proc(pid) for m,(pid,_) in jobs.items()}
assert all(p is not None and p['state']!='Z' for p in identities.values())
rows=[]
for i in range(60):
 row=dict(time=time.time(),methods={})
 for m,(pid,path) in jobs.items():
  ps=[p for q in [pid]+children(pid) if (p:=proc(q)) is not None]
  progress=json.loads((B/'runs'/path/'PROGRESS.json').read_text())
  row['methods'][m]=dict(processes=ps,progress=progress,original_learner_alive=bool(ps and ps[0]['pid']==pid and ps[0]['start']==identities[m]['start'] and ps[0]['state']!='Z'))
 gpu=subprocess.run(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],check=True,capture_output=True,text=True)
 row['gpus']=[[int(x.strip()) for x in line.split(',')] for line in gpu.stdout.splitlines()];rows.append(row);time.sleep(1)
summary={}
for m,(pid,_) in jobs.items():
 learner_time=worker_time=covered=0.
 for a,z in zip(rows,rows[1:]):
  pa={p['pid']:p for p in a['methods'][m]['processes']};pz={p['pid']:p for p in z['methods'][m]['processes']};elapsed=z['time']-a['time'];covered+=elapsed
  for q in pa.keys()&pz.keys():
   if pa[q]['start']!=pz[q]['start']:continue
   delta=pz[q]['cpu_s']-pa[q]['cpu_s']
   if q==pid:learner_time+=delta
   else:worker_time+=delta
 first,last=rows[0]['methods'][m]['progress'],rows[-1]['methods'][m]['progress']
 summary[m]=dict(transitions_per_s=(last['steps']-first['steps'])/covered,critic_updates_per_s=(last['updates']-first['updates'])/covered,learner_cpu_cores=learner_time/covered,physical_worker_cpu_cores=worker_time/covered,first_progress=first,last_progress=last,original_live_all_samples=all(r['methods'][m]['original_learner_alive'] for r in rows))
report=dict(time=time.time(),duration_s=rows[-1]['time']-rows[0]['time'],summary=summary,gpu_means=[sum(r['gpus'][i][1] for r in rows)/len(rows) for i in range(4)],samples=rows,new_physics=0,optimizer_updates=0,scope='Read-only observation of four existing formal learners; excludes CPU time of workers born/exited entirely between adjacent samples; profiling itself launches no training or physics',convergence_claim=False)
(OUT/'PROFILE.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(summary=summary,gpu_means=report['gpu_means'])),flush=True)
