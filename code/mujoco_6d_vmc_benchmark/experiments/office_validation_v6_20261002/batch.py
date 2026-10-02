"""Bounded foreground evaluation queue; no scheduled or recurring work."""
import concurrent.futures,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
SOURCE=Path(__file__).resolve().parent
protocol=json.loads((ROOT/'PROTOCOL.json').read_text())
def run(item):
    ident,extra=item
    command=['systemd-run','--user','--scope','--quiet','-p','MemoryMax=3G',sys.executable,str(SOURCE/'evaluate.py'),'--id',ident]+extra
    t=time.time()
    with (ROOT/(ident+'.log')).open('x') as log:
        p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ)
    result=dict(id=ident,returncode=p.returncode,elapsed_s=time.time()-t,command=command)
    print(json.dumps(result),flush=True)
    return result
def main():
    items=[('clear_zero',['--clear'])]+[(x['id'],[]) for x in protocol['cases']]
    # Start an ESN early for prompt interface validation, without using its result to alter the queue.
    items.insert(2,items.pop(next(i for i,x in enumerate(items) if x[0]=='esn_original_v2')))
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,x) for x in items]
        for f in concurrent.futures.as_completed(futures):
            rows.append(f.result())
            (ROOT/'BATCH.json').write_text(json.dumps(dict(rows=rows,pending=len(items)-len(rows)),indent=2))
    assert all(x['returncode']==0 for x in rows), 'Failures preserved; inspect execution records'
if __name__=='__main__':main()

