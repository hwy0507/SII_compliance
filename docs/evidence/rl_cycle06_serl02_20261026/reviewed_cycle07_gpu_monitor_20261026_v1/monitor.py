import subprocess,time,json,os
from pathlib import Path
os.sched_setaffinity(0,{52})
out=Path(__file__).parent
rows=[]
for i in range(60):
 r=subprocess.run(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used','--format=csv,noheader,nounits'],text=True,capture_output=True,check=True)
 rows.append(dict(time=time.time(),gpus=[[int(x.strip()) for x in line.split(',')] for line in r.stdout.splitlines()]))
 time.sleep(1)
report={'samples':rows,'duration_s':rows[-1]['time']-rows[0]['time'],'means':[sum(r['gpus'][i][1] for r in rows)/len(rows) for i in range(4)],'scope':'Four formal learners: SERL cycle3 startup and parameters cycle7 tail; GPU0 also fixed-policy evaluation, no auxiliary training. Includes real stage transition/idle intervals.'}
(out/'GPU_60S.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['means'])
