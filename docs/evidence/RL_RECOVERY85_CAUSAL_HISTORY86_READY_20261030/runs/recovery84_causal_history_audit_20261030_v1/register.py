from pathlib import Path
import json,time,hashlib
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent
source=B/'runtime/source_train17_clock'
hashes=json.loads((source/'SOURCE_HASHES.json').read_text())
refs=[]
for n in ['tools/published_compliance_episode_20261025.py','scripts/validate_office_apparatus_v5_20260917.py','tools/spt_rl_reward_20261025.py']:
 p=source/'source'/n;h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==hashes[n];refs.append(dict(path=str(p),sha256=h))
plan=dict(time=time.time(),cycle=84,methods=['impedance','admittance','vmc'],episodes_per_method=30,actions_per_episode=1375,scope='All90 complete84 saved journals, retrospective source-bound causal availability audit; not preregistered before original data collection.',prior_case_inspected='VMC84 short0600; first over0.0002 preaction at row96/time3.84s already known before this plan.',threshold_m=0.0002,clock_atol_s=1e-6,budget_seconds=600,cpu=53,physics_steps=0,optimizer_updates=0,network_forwards=0,inputs_changed=False,replay_writes=0,source=refs,definition='Row0 cumulative peak0 (no elapsed dynamics). Row i>0 uses only its own interval, delivered before action i; next peak comes from row i+1, except final transition next peak comes from TERMINAL.interval after final action. No terminal information inserted into any preaction row.',checks=['90 complete episodes and exact 1375 rows','raw observations and executed actions bit-exact to saved rollout','cumulative peaks finite nonnegative monotone','elapsed interval clocks match neuron_time','all final cumulative peaks exact to rollout.stats.max_external_penetration_m','Strict implications and Task/physical labels crosscheck; no new gate','derived array reread and independent scalar journal reconstruction'],limitations=['No independent substep penetration telemetry saved; consistency/source audit only','No proof of reconstruction across entire historical replay','No causality of Adam drift or guaranteed fit','No formal history-feature amendment; actor48 unchanged'])
with (D/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
print('Registered',D/'PLAN.json')
