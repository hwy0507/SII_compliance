from pathlib import Path
import json,time,socket,subprocess
B=Path(__file__).resolve().parents[2];D=B/'runtime/census97_continuation_20261031_v1'
def read(p):return json.loads(p.read_text())
maximum=int(Path('/sys/fs/cgroup/memory.max').read_text());current=int(Path('/sys/fs/cgroup/memory.current').read_text());swap=int(Path('/sys/fs/cgroup/memory.swap.current').read_text());assert maximum-current>128*1024**3 and swap==0
rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).splitlines();assert len(rows)==4 and all(int(row.split(',')[2])>12000 for row in rows)
g=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');assert not (Path(g['root'])/'STOP').exists()
for j in g['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
x=dict(passed=True,time=time.time(),host=socket.gethostname(),container_memory_max=maximum,container_memory_current=current,container_swap_current=swap,required_free_container_memory=128*1024**3,required_gpu_free_MiB=12000,gpu_rows=rows,guard=g,learner_cpu=[13,26,39],samplers_per_method=30,capacity=6000000,allocated_host_only=True)
with (D/'RESOURCE_REVIEW.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x))
