from pathlib import Path
import os,json,time,socket,subprocess,shutil
D=Path(__file__).resolve().parent;B=D.parents[1];S=B/'runtime/census99_continuation_20261031_v1';read=lambda p:json.loads(p.read_text())
assert read(S/'PREFLIGHT_FINISHED.json')['passed'];assert read(S/'CPU_CONSUMER_REVIEW.json')['passed']
maximum=int(Path('/sys/fs/cgroup/memory.max').read_text());current=int(Path('/sys/fs/cgroup/memory.current').read_text());swap=int(Path('/sys/fs/cgroup/memory.swap.current').read_text());assert maximum-current>=128*1024**3 and swap==0
raw=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True);rows=[x.split(', ') for x in raw.strip().splitlines()];assert len(rows)==4 and all(int(x[2])>=12000 and int(x[3])>=50 for x in rows)
guard=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
for j in guard['identities']:
 t=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert t[0]!='Z' and t[19]==j['start']
assert not Path(guard['root'],'STOP').exists();assert set(range(13,52))<=os.sched_getaffinity(0)
free=shutil.disk_usage(B).free;assert free>=40*1024**3
r=dict(passed=True,time=time.time(),host=socket.gethostname(),container_memory_max=maximum,container_memory_current=current,container_swap_current=swap,required_free_container_memory=128*1024**3,required_gpu_free_MiB=12000,gpu_rows=raw.strip().splitlines(),guard=guard,learner_cpu=[13,26,39],samplers_per_method=30,capacity=6000000,allocated_host_only=True,ssd_available_bytes=free)
with (S/'RESOURCE_REVIEW.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print('resource passed',raw.strip())
