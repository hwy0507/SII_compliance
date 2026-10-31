"""Finish the original97-99 input map only after actual full99 plot inspection."""
from pathlib import Path
import json,sys,os
D=Path(__file__).resolve().parent;B=D.parents[1];W=B/'runs/parameter_census97_99_reward_stability_20261031_v1'
sys.path.insert(0,str(W));from binding_rules import locked,ref,check_ref,read
os.sched_setaffinity(0,{54});locked(W)
inputs=read(B/'runtime/census99_window_inputs_recovery_20261031_v1/COMPLETE98_INPUT_MAP.json')
assert set(inputs)=={f'{m}:{c}' for m in ['impedance','admittance','vmc'] for c in [97,98]}
for group in inputs.values():
 for r in group.values():check_ref(r)
V=B/'runs/parameter_census_cycle99_review_20261031_v1';R=B/'runs/parameter_census_cycle99_20261031_v1'
assert read(V/'FINISHED.json')['completed'] and read(V/'REVIEW.json')['passed']
assert read(V/'PLOT_INSPECTION.json')['actual_visual_inspection']
assert read(B/'runtime/census99_completion_20261031_v1/COMPLETE99_SCIENTIFIC_REVIEW.json')['passed']
assert read(B/'runtime/census99_completion_20261031_v1/FULL_LOSS_SAVED_REVIEW.json')['passed']
for m in ['impedance','admittance','vmc']:
 paths=dict(protocol=R/m/'REGISTRATION.json',review=V/'REVIEW.json',health=V/'health/DIAGNOSIS.json',finished=V/'FINISHED.json',episodes=R/m/'train/episodes.jsonl',optimizer=R/m/'train/optimizer.jsonl',loss_plot=V/'loss/loss99.png',health_plot=V/'health/training_diagnostics.png',loss_review=V/'loss/REVIEW.json',plot_inspection=V/'PLOT_INSPECTION.json',checkpoint=B/'runs/parameter_census_cycle99_archive_20261031_v1'/m/'cycle_00099.pt')
 inputs[f'{m}:99']={k:ref(p) for k,p in paths.items()}
assert set(inputs)=={f'{m}:{c}' for m in ['impedance','admittance','vmc'] for c in [97,98,99]}
with (D/'COMPLETE97_98_99_INPUT_MAP.json').open('x') as f:json.dump(inputs,f,indent=2);f.write('\n')
print('All nine actual input groups mapped; unchanged original bind_inputs validator still required')
