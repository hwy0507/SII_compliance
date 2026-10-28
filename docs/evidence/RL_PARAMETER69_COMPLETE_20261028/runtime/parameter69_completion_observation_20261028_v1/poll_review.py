from pathlib import Path
import json,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).resolve().parent
paths={'archive':B/'runs/parameter_capacity_pool30_cycle69_20261026_v1/ARCHIVE_REVIEW_FINISHED.json','loss':B/'runs/parameter69_loss_20261028_v1/FINISHED.json','labels':B/'runs/parameter_task_label_audit69_20261028_v1/FINISHED69.json','vmc_terminal':B/'runs/vmc69_terminal_anchor_followup_20261028_v1/FINISHED.json','admittance_terminal':B/'runs/admittance69_terminal_anchor_followup_20261028_v1/FINISHED.json','restore70':B/'runtime/prepare_parameter70_20261028_v1/parameter_FINISHED.json'}
row=dict(time=time.time(),ready={k:p.exists() for k,p in paths.items()},processes={})
for pid in [3088977,3389722,3373363,3545889,3545890,1085142,3256866,3256867,3256868,3256869,3256870]:
 p=Path(f'/proc/{pid}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else [];row['processes'][str(pid)]=dict(live=bool(s) and s[0]!='Z',start_ticks=s[19] if s else None)
row['review_files']=[p.name for p in (B/'runs/parameter_capacity_pool30_cycle69_review_20261026_v1').glob('*REVIEW.json')]
row['health_exists']=(B/'runs/parameter_capacity_pool30_cycle69_review_20261026_v1/health/DIAGNOSIS.json').exists()
row['failures']=[str(p) for root in [B/'runs/parameter_capacity_pool30_cycle69_20261026_v1',B/'runs/parameter_capacity_pool30_cycle69_review_20261026_v1',B/'runtime/prepare_parameter70_20261028_v1',B/'runs/parameter_task_label_audit69_20261028_v1',B/'runs/vmc69_terminal_anchor_followup_20261028_v1',B/'runs/admittance69_terminal_anchor_followup_20261028_v1'] for p in root.glob('*FAILURE*.json')]
with (OUT/'review_samples.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
print(json.dumps(row));assert not row['failures']
