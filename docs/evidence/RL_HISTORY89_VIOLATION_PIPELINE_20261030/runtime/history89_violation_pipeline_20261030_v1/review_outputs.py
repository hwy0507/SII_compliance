from pathlib import Path
import json,time,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/history89_violation_pipeline_preflight_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
plan=read(O/'POSTPROCESS_PLAN.json');assert sha(Path(__file__))==plan['source_sha256'];assert read(O/'RUN_REVIEW.json')['passed'];mig=read(O/'MIGRATION_REVIEW.json');assert mig['passed'];health=read(O/'health/DIAGNOSIS.json');previous=read(B/'runs/parameter_history_cycle89_review_20261030_v1/health/DIAGNOSIS.json');results={}
fields=('terminal_reward','terminal_q_predictions','terminal_q_absolute_error','terminal_q_in_bag_absolute_error','terminal_q_out_of_bag_absolute_error','terminal_by_restart_origin','terminal_success_bonus_samples','sampled_q_values','sampled_td_absolute_error')
for m,r in mig['methods'].items():
 f=read(O/'frozen'/m/'CHECK_ONLY_REVIEW.json');assert f['passed'] and f['full_replay_restored_exact'] and f['validated_parent_cycle']==89 and f['replay_capacity']==4_000_000 and f['historical_entry_cycle']==23 and f['followup_entry_cycle']==47
 assert f['checkpoint_sha256']==r['checkpoint_sha256']==sha(Path(r['checkpoint_path']))
 assert not (O/'frozen'/m/'EVALUATION.json').exists()
 a=health['methods'][m];old=previous['methods'][m];assert a['checkpoint_sha256']==r['checkpoint_sha256'];compared=[]
 for k in fields:
  if k in old:assert a[k]==old[k],(m,k,a[k],old[k]);compared.append(k)
 assert a['steps']==old['steps'] and a['updates']==old['updates'] and a['terminal_count']==old['terminal_count']
 results[m]=dict(passed=True,actual_evaluator_check_only_passed=True,physical_evaluation_absent=True,full_health_diagnostic_passed=True,old89_health_fields_exact=compared,clone_native_updates=r['clone_native_updates'],negative_rejections=len(r['negative_rejections']),checkpoint_sha256=r['checkpoint_sha256'])
with (O/'FINAL_REVIEW.json').open('x') as f:json.dump(dict(time=time.time(),passed=True,methods=results,formal_updates=0,physics_steps=0,clone_native_updates=6,training90=False,health_scope='Original descriptive unprojected pair-minimum diagnostic retained; not convergence gate or target-estimator reproduction'),f,indent=2);f.write('\n')
print(json.dumps(results))
