from pathlib import Path
import json,time,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1];read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
H=B/'runs/recovery87_history_extension_20261030_v1';V=B/'runs/parameter_history_cycle89_review_20261030_v1';F=B/'runs/history89_violation_bit_paired_fit_20261030_v1';C=B/'runtime/history89_violation_bit_review_20261030_v1'
old=read(H/'REVIEW.json');full=read(V/'REVIEW.json');assert old['passed'] and full['passed'] and read(F/'SAVED_REVIEW.json')['passed']
inputs=[H/n for n in ('REVIEW.json','SAVED_REVIEW.json','FINISHED.json')]+[V/n for n in ('REVIEW.json','FINISHED.json','PLOT_INSPECTION.json')]+[F/n for n in ('PLAN.json','SAVED_REVIEW.json','PLOT_INSPECTION.json')]+[C/'SCIENTIFIC_DECISION.json'];methods={}
for m,a in old['methods'].items():
 reg89=B/f'runs/parameter_history_cycle89_20261030_v1/{m}/REGISTRATION.json';reg88=Path(read(reg89)['post_interruption_continuation']['parent_registration']['path']);cp=B/f'runs/parameter_history_cycle89_archive_20261030_v1/{m}/cycle_00089.pt';assert sha(cp)==full['methods'][m]['checkpoint_sha256']
 methods[m]=dict(prefix_rows=a['total_rows'],checkpoint87=a['checkpoint87'],checkpoint89=ref(cp),sidecar87=a['sidecar'],registrations={'88':ref(reg88),'89':ref(reg89)})
 inputs.extend([reg88,reg89,Path(a['sidecar']['path'])])
for name in ('build.py','review_saved.py','register.py'):ast.parse((D/name).read_text())
plan=dict(time=time.time(),methods=methods,cpu=11,budget_seconds=900,maximum_appended_rows=247500,inputs=[ref(p) for p in inputs],sources={n:sha(D/n) for n in ('build.py','review_saved.py','register.py')},feature='uint8(raw causal cumulative external penetration >0.0002)',current_column='preaction',next_column='postaction',old_data='Exact complete87 raw sidecar; original87 50-dimensional replay prefix equal complete89 first50, all other fields exact; complete89 existing51 history checked for every row',source_cycles=[88,89],new_physics=0,new_network_forward=0,new_optimizer_updates=0,replay_writes=0,architecture52_implemented=False,automatic_training=False,limits='Read-only saved-journal reconstruction and standalone raw/bit arrays. Not independent physical reconstruction, replay migration, final architecture acceptance, or reward improvement. Preserve partial75 and all original failures.')
with (D/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
print('Registered',sha(D/'PLAN.json'))
