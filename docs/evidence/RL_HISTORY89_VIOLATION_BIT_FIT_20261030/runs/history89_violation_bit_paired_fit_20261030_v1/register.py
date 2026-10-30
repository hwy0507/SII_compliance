from pathlib import Path
import ast,json,hashlib,time,socket,subprocess
D=Path(__file__).resolve().parent;B=D.parents[1]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
V=B/'runs/parameter_history_cycle89_review_20261030_v1';F=B/'runs/history89_fixed87_terminal_followup_20261030_v1';C=B/'runtime/history89_completion_20261030_v1';H=B/'runs/recovery87_history_extension_20261030_v1'
full=read(V/'REVIEW.json');assert full['passed'] and read(F/'REVIEW.json')['passed'] and read(C/'BOUNDARY_AND_CONTRIBUTORS_REVIEW.json')['passed']
for folder in (V,F):assert read(folder/'PLOT_INSPECTION.json')['actual_visual_inspection']
previous=read(F/'PLAN.json');hist=read(H/'REVIEW.json');inputs=[V/'REVIEW.json',V/'FINISHED.json',V/'health/DIAGNOSIS.json',V/'loss/REVIEW.json',V/'PLOT_INSPECTION.json',F/'REVIEW.json',F/'FINISHED.json',F/'PLOT_INSPECTION.json',H/'REVIEW.json',C/'BOUNDARY_AND_CONTRIBUTORS_REVIEW.json',C/'FIXED87_SSE_CONTRIBUTORS.json',C/'EARLY_WINDOW_FAILURE.json'];methods={}
for m in ('impedance','admittance','vmc'):
 p=previous['methods'][m];cp=Path(p['checkpoint']);assert sha(cp)==full['methods'][m]['checkpoint_sha256']
 reg=Path(p['registration']);values=F/(m+'_values.npz');side=Path(hist['methods'][m]['sidecar']['path']);assert sha(values)==read(F/'REVIEW.json')['methods'][m]['values_sha256'] and sha(side)==hist['methods'][m]['sidecar']['sha256']
 methods[m]=dict(checkpoint=ref(cp),registration=ref(reg),values=ref(values),sidecar=ref(side),binding=p['binding'],terminal_rows=p['terminal_rows']);inputs.extend([reg,values,side])
for name in ('fit.py','review_saved.py'):ast.parse((D/name).read_text())
plan=dict(time=time.time(),host=socket.gethostname(),git_parent=subprocess.check_output(['git','rev-parse','HEAD'],cwd=B/'repository/SII_compliance',text=True).strip(),cpu=11,device='cuda:1',budget_seconds=900,updates_per_arm=500,maximum_cloned_q_optimizer_steps=3000,initial_q_atol=1e-4,methods=methods,inputs=[ref(p) for p in inputs],restore_runtime=previous['restore_runtime'],restore_sources=previous['restore_sources'],sources={name:sha(D/name) for name in ('fit.py','review_saved.py','register.py')},feature='float(raw_preaction_cumulative_external_penetration_m >0.0002)',feature_index=51,critic_input_dimension=52,control='Same expanded52 architecture, appended input always zero',intervention='Same expanded52 architecture, appended causal violation bit',old_weights_adam='Preserved exactly including learned history column50 and all step counters; inserted column51 and corresponding moments zero in both arms',loss='Sum of original-mask terminal MSE for all5 critics over every original87 terminal, full batch per update. No bootstrap; terminal128 cancels because all rows terminal.',actor_alpha_target_updates=0,physics_steps=0,no_weight_promotion=True,automatic90=False,primary_comparison='Final step500 masked loss and all5 SSE; all methods/curves retained; no selected intermediate checkpoint',scientific_motivation='Complete89 Icritic3 regression on fixed87 samples just over penetration boundary; investigate known discontinuity representation with matched capacity. A/V and all critics retained.',limits='Development in-sample fitting of previously trained-on fixed87 terminals. Does not establish online reward improvement, held-out generalization, causal explanation of policy failures, final architecture acceptance, convergence, or authorization to promote weights. No modification of physical gates, actor inputs, LR, reward or original checkpoints.')
with (D/'PLAN.json').open('x') as f:json.dump(plan,f,indent=2,allow_nan=False);f.write('\n')
print('Registered',sha(D/'PLAN.json'))
