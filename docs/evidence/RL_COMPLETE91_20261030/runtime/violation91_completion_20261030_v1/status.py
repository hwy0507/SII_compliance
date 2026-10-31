from pathlib import Path
import json,time,subprocess
D=Path(__file__).resolve().parent;B=D.parents[1];p=D/'OBSERVATIONS.jsonl';x=json.loads(p.read_text().splitlines()[-1]);base={'impedance':3729700,'admittance':3732500,'vmc':3733500}
print(json.dumps(dict(time=time.time(),sample_age=time.time()-x['time'],elapsed=x['elapsed_s'],training={m:dict(added=v['progress']['steps']-base[m],completed=v['progress']['completed_conditions'],alive=v['alive']) for m,v in x['training'].items()},frozen={m:v['completed_conditions'] for m,v in x['frozen'].items()},reviews_ready=x['complete_reviews_ready'],archive_alive=x['archive_alive'],terminal_waiter_alive=x['terminal_waiter_alive'],watch_failure=(D/'WATCH_FAILURE.json').exists())))
print(subprocess.check_output(['nvidia-smi','--query-gpu=index,utilization.gpu','--format=csv,noheader']).decode().strip())
