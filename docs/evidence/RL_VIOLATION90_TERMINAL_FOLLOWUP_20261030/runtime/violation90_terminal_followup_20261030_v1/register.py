from pathlib import Path
import ast,json,time,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation90_fixed87_terminal_followup_20261030_v1';R=B/'runs/parameter_violation_cycle90_20261030_v1';OLD=B/'runs/history89_fixed87_terminal_followup_20261030_v1';RAW=B/'runs/history89_raw_history_extension_20261030_v1';RESTORE=B/'runtime/violation90_frozen_preparation_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
for p in D.glob('*.py'):ast.parse(p.read_text())
old=read(OLD/'REVIEW.json');raw=read(RAW/'REVIEW.json');assert old['passed'] and raw['passed'] and read(RESTORE/'UPDATED_FROZEN_REVIEW.json')['passed'];assert read(OLD/'PLOT_INSPECTION.json')['actual_visual_inspection']
methods={};refs=[]
for m,previous in old['methods'].items():
 p=R/m/'REGISTRATION.json';protocol=read(p);v=protocol['violation_critic_amendment']['binding'];assert v['history_binding']==protocol['history_critic_amendment']['binding'];saved=OLD/(m+'_values.npz');assert sha(saved)==previous['values_sha256']
 rr=raw['methods'][m];assert rr['sidecar']['sha256']==v['sidecar_sha256'] and rr['bits']['sha256']==v['bits_sha256']
 methods[m]=dict(checkpoint=str(B/'runs/parameter_violation_cycle90_archive_20261030_v1'/m/'cycle_00090.pt'),registration=str(p),history_binding=v['history_binding'],violation_binding=v,baseline_values=str(saved),terminal_rows=previous['terminal_rows'],sidecar=rr['sidecar'],bits=rr['bits'])
 refs.extend([ref(p),ref(saved),rr['sidecar'],rr['bits']])
refs.extend(ref(p) for p in [OLD/'REVIEW.json',OLD/'PLOT_INSPECTION.json',RAW/'REVIEW.json',RAW/'SAVED_REVIEW.json',RESTORE/'UPDATED_FROZEN_REVIEW.json',R/'LAUNCH.json',R/'MONITOR_LAUNCH.json',B/'runtime/violation90_online_20261030_v1/SCIENTIFIC_DECISION.json'])
monitor=read(R/'MONITOR_LAUNCH.json');f=Path('/proc',str(monitor['pid']),'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==monitor['proc_start_ticks']
plan=dict(time=time.time(),parent_cycle=89,target_cycle=90,fixed_original_terminal_cycle=87,methods=methods,inputs=refs,previous_followup=str(OLD),restore_runtime=str(RESTORE),restore_sources={p.name:sha(p) for p in RESTORE.glob('*.py')},source_hashes={p.name:sha(p) for p in D.glob('*.py')},complete_review=str(B/'runs/parameter_violation_cycle90_review_20261030_v1'),original_monitor=monitor,wait_deadline_unix=read(R/'LAUNCH.json')['time']+14400,analysis_budget_seconds=1800,device='cuda:0',physical_steps=0,optimizer_updates=0,automatic91=False,limits='All original87 seen terminal rows/all5/original masks, fixed before complete90. Raw bit joins unchanged51 features;52 dimensions do not change row selection. Descriptive87/88/89/90 retention and fitting across the critic amendment; no causal-bit benefit, generalization, policy performance or convergence claim. Full90 includes additional online training so architecture effects are not identified. No offline weights promoted; all regressions retained.')
with (O/'PLAN.json').open('x') as out:json.dump(plan,out,indent=2);out.write('\n')
print({m:v['terminal_rows'] for m,v in methods.items()})
