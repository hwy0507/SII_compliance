from pathlib import Path
import json,time
D=Path(__file__).resolve().parent
row=json.loads((D/'WAIT_SAMPLES.jsonl').read_text().splitlines()[-1]);gpu=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);assert time.time()-row['time']<30 and time.time()-gpu['time']<30
print(json.dumps(dict(elapsed=row['elapsed_s'],steps={m:v['steps'] for m,v in row['training'].items()},completed_training_conditions={m:v['completed_conditions'] for m,v in row['training'].items()},frozen={m:v['completed_conditions'] for m,v in row['frozen'].items()},nonlive_count=sum(v in ['absent','reused_pid','Z'] for v in row['states'].values()),learner_finished=row['learner_finished'],review_finished=row['review_finished'],terminal_finished=row['terminal_finished'],failures=row['failures'],gpu=[x['utilization'] for x in gpu['gpus']])))
