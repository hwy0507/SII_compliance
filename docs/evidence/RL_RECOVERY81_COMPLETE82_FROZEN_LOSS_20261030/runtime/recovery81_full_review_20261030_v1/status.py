from pathlib import Path
import json,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def read(p):return json.loads(p.read_text())
R=B/'runs/parameter_partial75_recovery_cycle81_20261029_v1'
for m in ['impedance','admittance','vmc']:
 p=R/m/'train/PROGRESS.json';r=read(p);print(m,r['steps'],r['completed_conditions'],r['running'])
for rel in ['runs/parameter_partial75_recovery_cycle81_review_20261029_v1','runs/parameter_recovery81_loss_20261029_v1','runs/parameter_recovery81_task_labels_20261029_v1','runs/vmc_recovery81_terminal_followup_20261029_v1','runs/admittance_recovery81_terminal_followup_20261029_v1','runs/parameter_recovery79_81_reward_stability_20261030_v1','runtime/prepare_recovery82_20261030_v1','runs/vmc80_81_fixed_replay_loss_20261030_v1']:
 p=B/rel;print(p.name,[(n.name,round(time.time()-n.stat().st_mtime,1)) for n in p.glob('*.json') if n.name in ['FINISHED.json','REVIEW.json','SAVED_REVIEW.json','SAVED_ARITHMETIC_REVIEW.json','SAVED_VALUES_REVIEW.json','WAIT_FINISHED.json'] or 'FAILURE' in n.name])
g=read(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl')) if False else json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]);print('GPU', [v['utilization'] for v in g['gpus']],'age',time.time()-g['time'])
