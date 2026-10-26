from pathlib import Path
import subprocess,json,time,os,hashlib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=B/'runs/batch18_parameter27_mixed_gpu_20261026_v1';out.mkdir();os.sched_setaffinity(0,{52})
pids=[2732254,2286139,2286140,2286141,1749189,1749193]
reg=dict(samples=30,interval_seconds=1,expected_original_pids=pids,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),time=time.time(),scope='Mixed formal18/27 training and frozen16 inference. Short operational observation, not pure-formal throughput or guarantee for every instant; excludes prior transition idle.')
(out/'REGISTRATION.json').write_text(json.dumps(reg,indent=2)+'\n');rows=[];start=time.monotonic()
for i in range(reg['samples']):
 assert all(Path(f'/proc/{p}').exists() for p in pids)
 raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader,nounits'],text=True)
 values={int(r.split(',')[0]):int(r.split(',')[1]) for r in raw.splitlines()};assert set(values)=={0,1,2,3}
 rows.append(dict(time=time.time(),utilization=values))
 if i+1<reg['samples']:time.sleep(1)
result=dict(time=time.time(),elapsed_seconds=time.monotonic()-start,samples=rows,means={i:sum(r['utilization'][i] for r in rows)/len(rows) for i in range(4)},scope=reg['scope'],original_pids_alive_at_every_sample=True)
(out/'PROFILE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='samples'}),flush=True)
