from pathlib import Path
import ast,shutil,difflib,json,time
B=Path(__file__).resolve().parent.parent;OLD=B/'runtime/violation91_continuation_20261030_v1';D=B/'runtime/violation92_continuation_20261030_v1';D.mkdir()
for p in OLD.glob('*.py'):
 if p.name not in {'driver.py','register91.py','build_driver.py','check_contract.py','run_preflight.py'}:shutil.copyfile(p,D/p.name)
s=(OLD/'driver.py').read_text();before=s
replacements={
 'continuation91 from exact trained90; preserve learned52 and no automatic92':'continuation92 from exact trained91; preserve learned52 and no automatic93',
 'parameter_violation_cycle91_20261030_v1':'parameter_violation_cycle92_20261030_v1',
 'actual90':'actual91','Exact90':'Exact91','learned90':'learned91','trained90':'trained91','trained90':'trained91','Finite91':'Finite92','Complete90':'Complete91','complete90':'complete91','validated_scientific90_driver':'validated_scientific91_driver',
 '(90,91,1,41250,False':'(91,92,1,41250,False',"health['cycle']!=90":"health['cycle']!=91","ck['cycle']!=90":"ck['cycle']!=91","ck['cycles'][-1]['cycle']!=90":"ck['cycles'][-1]['cycle']!=91","'violation91_trainer'":"'violation92_trainer'",'cycle=91,automatic_followup':'cycle=92,automatic_followup'
}
for a,b in replacements.items():s=s.replace(a,b)
a="if n!=v['binding']['rows']+review['new_transitions'] or not 0<review['new_transitions']<=41250:raise ValueError('Actual complete91 rows including abort required')"
b="parent_review=read(previous['post_interruption_continuation']['cycle_review']['path'])['methods'][st['controller']]\n if n!=parent_review['steps']+review['new_transitions'] or not 0<review['new_transitions']<=41250:raise ValueError('Actual complete91 rows from exact complete90 including abort required')"
assert s.count(a)==1;s=s.replace(a,b)
assert "window['cycles']!=[90,91,92]" in s and "plateau_status([c for c in cycles if c['cycle'] >= 90])" in s
ast.parse(s);(D/'driver.py').write_text(s);(D/'driver.py.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile=str(OLD/'driver.py'),tofile='driver92.py')))
s=(OLD/'register91.py').read_text();before=s
# Paths and cycle-specific descriptors only; old window and revision floor stay 90.
for a,b in [('parameter_violation_cycle91_','NEXT_TRAIN_'),('parameter_violation_cycle90_','parameter_violation_cycle91_'),('NEXT_TRAIN_','parameter_violation_cycle92_'),('violation90_completion_','violation91_completion_'),('violation90_fixed87_terminal_','violation91_fixed87_terminal_'),('violation90_online_','violation91_continuation_'),('cycle_00090.pt','cycle_00091.pt'),('full90','full91'),('parent_cycle=90,new_cycle=91','parent_cycle=91,new_cycle=92'),('Finite91','Finite92')]:s=s.replace(a,b)
s=s.replace("'PLOT_INSPECTION.json','ABORT_REVIEW.json'","'PLOT_INSPECTION.json','CHANGED_CASES_REVIEW.json','ADJACENT90_91_REVIEW.json','COMPLETE91_BINDING_REVIEW.json','TERMINAL_SAVED_REVIEW.json'")
s=s.replace("[S/'PLAN.json',B/'runtime/history89_completion_20261030_v1/EARLY_WINDOW_FAILURE.json'","[S/'PLAN.json',S/'EARLY_WINDOW_FAILURE_91.json',B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json',B/'runtime/history89_completion_20261030_v1/EARLY_WINDOW_FAILURE.json'")
a=s.index("put(D/'SCIENTIFIC_DECISION.json'");z=s.index('\nR.mkdir()',a)
reason='Complete91 retained all replay and restored learned52 weights/Adam/RNG exactly; all90 full55 episodes had no abort. I reward and fixed87 masked SSE improved, A reward/Strict and fixed87 masked SSE worsened, V labels/reward remained close and fixed87 masked SSE improved. Critic spikes and actor mean drift remain; I/A original90-92 adjacent5% requirement already failed and cannot be rescued by92. Only two complete online cycles exist after raw violation52 adoption; mixed directions do not yet support changing LR/reward/architecture. Register exactly one additional same-protocol cycle92 from full91 to assess persistence of these changes, obtain the third same52 cycle and complete the originally registered90-92 descriptive analysis (including its retained I/A failures, and V endpoints/loss). This is a bounded learning continuation, not GPU filler or proof of convergence. Full92 and loss/health must be reviewed before any93 decision; no automatic93. Original frozen90 evaluation continues independently. No offline weights promoted, no Direct34, no change to gates or original failed windows.'
s=s[:a]+"put(D/'SCIENTIFIC_DECISION.json',dict(time=time.time(),parent_cycle=91,new_cycle=92,new_cycles=1,maximum_new_actions_per_method=41250,critic_revision='raw_violation52',automatic_followup=False,offline_weights_promoted=False,optimizer_settings_changed=False,reward_physics_changed=False,direct34=False,architecture_final_acceptance=False,convergence_claim=False,original90_92_IA_necessary_condition_failed=True,evidence=[ref(p) for p in required],reason="+repr(reason)+"))"+s[z:]
s=s.replace("abort_review=ref(C/'ABORT_REVIEW.json')","abort_review=ref(B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json')")
s=s.replace('One finite same52 continuation from exact complete90 including I safety abort. Preserve learned history and violation weights/Adam, all replay and RNG, original physics and failed windows; no automatic92.','One finite same52 continuation from exact complete91 with all older90 safety-abort transitions retained. Preserve learned history and violation weights/Adam, all replay and RNG, original physics and failed90-92 necessary condition; no automatic93.')
ast.parse(s);(D/'register92.py').write_text(s);(D/'register92.py.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile=str(OLD/'register91.py'),tofile='register92.py')))
s=(OLD/'check_contract.py').read_text().replace('parameter_violation_cycle91_','parameter_violation_cycle92_').replace('actual90','actual91').replace('finite91','finite92').replace('trained90','trained91').replace("('parent_cycle',89)","('parent_cycle',90)").replace("('new_cycle',92)","('new_cycle',93)").replace("('cycle',89)","('cycle',90)");ast.parse(s);(D/'check_contract.py').write_text(s)
s=(OLD/'run_preflight.py').read_text().replace('parameter_violation_cycle91_','parameter_violation_cycle92_');ast.parse(s);(D/'run_preflight.py').write_text(s)
print('Prepared',D)
