"""Independent complete frozen report arithmetic and all-condition41/55 pairing."""
from pathlib import Path
import json,hashlib,math,time,os,argparse
os.sched_setaffinity(0,{54})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=Path(__file__).parent
ROOTS={41:B/'runs/parameter41_frozen_full30_20261027_v1',55:B/'runs/parameter55_frozen_full30_20261028_v1'}
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def near(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-10),(a,b)
def audit(cycle):
 root=ROOTS[cycle];report=read(root/'REVIEW.json');plan=read(root/'PLAN.json');assert report['passed'] and report['total_episodes']==90
 assert plan['action_seed']==2026102638 and plan['parent_cycle']==cycle
 assert len(plan['case_ids'])==len(set(plan['case_ids']))==30
 assert sha(root/'frozen_full30_results.png')==report['plot_sha256']
 for path,h in report['inputs'].items():assert sha(Path(path))==h
 verified={};sources={};models={};total_actions=0;total_substeps=0
 for method,v in report['methods'].items():
  folder=root/method;reg=read(folder/'REGISTRATION.json');done=read(folder/'FINISHED.json');stored=read(folder/'RESULTS.json')
  assert done['passed'] and done['full_learner_state_unchanged'] and done['full_replay_state_unchanged'] and done['new_optimizer_updates']==0
  assert done['initial_learner_digest']==done['final_learner_digest']==v['initial_and_final_learner_digest']
  assert sha(Path(reg['checkpoint']))==reg['checkpoint_sha256']==v['checkpoint_sha256']
  assert reg['case_ids']==plan['case_ids'] and reg['action_seed']==plan['action_seed']
  assert len(stored['episodes'])==len(v['episodes'])==stored['completed']==stored['expected']==30
  by={e['condition']:e for e in v['episodes']};assert set(by)==set(plan['case_ids']);methods_models={};methods_sources={}
  for case,original in zip(plan['case_ids'],stored['episodes']):
   reviewed=read(folder/f'{case}_REVIEW.json');assert reviewed==original and reviewed['passed'];e=by[case];roll=read(folder/case/'rollout.json');row=reviewed['physical']['row']
   assert reviewed['condition']==case and reviewed['action_seed']==e['seed']==plan['action_seed'];assert reviewed['full_learner_state_unchanged'] and reviewed['new_optimizer_updates']==0
   assert reviewed['native_stochastic_parameter_action_max_error']<=1e-7 and reviewed['filter']['passed'] and reviewed['torque']['passed']
   # Large raw arrays were checked by original physical/filter/torque audits;
   # independently bind their small rollout/model/evaluator evidence here.
   for key in ['rollout.json','rollout.mjb']:assert sha(folder/case/key)==reviewed['physical']['evidence_sha256'][key]
   physical=roll['abort_reason'] is None and roll['stats']['max_external_penetration_m']<=.0002
   assert physical==roll['physical_valid'];assert bool(roll['task_success'] and physical)==roll['strict_success']==e['strict']==row['strict_success']
   assert roll['task_success']==e['task']==row['task_success'] and roll['abort_reason']==e['abort_reason']==row['abort_reason']
   near(1000*roll['stats']['max_external_penetration_m'],e['penetration_mm']);near(reviewed['reward'],e['reward'])
   assert e['actions']==reviewed['actions'];assert e['substeps']==reviewed['physical']['samples'];assert e['full_horizon']==row['full_horizon']
   for key in ['machine_safety_violation','human_contact_s','human_compliance_ratio','peak_torque_nm_per_joint','completion_time_s']:assert e[key]==row[key]
   methods_models[case]=sha(folder/case/'rollout.mjb');src=folder/case/'executed_evaluator.py.txt';methods_sources[case]=sha(src)
   assert "stats['max_external_penetration_m']<=.0002" in src.read_text()
  rewards=[e['reward'] for e in by.values()];peaks=[e['penetration_mm'] for e in by.values()]
  near(math.fsum(rewards)/30,v['mean_reward']);assert [min(rewards),max(rewards)]==v['reward_range'];assert [min(peaks),max(peaks)]==v['penetration_range_mm']
  for label,key in [('task','task'),('strict','strict'),('machine_safety_violation_count','machine_safety_violation'),('full_horizon_count','full_horizon')]:assert sum(e[key] for e in by.values())==v[label]
  actions=sum(e['actions'] for e in by.values());substeps=sum(e['substeps'] for e in by.values());assert actions==done['actions']<=41250 and substeps==done['substeps']<=33000000
  total_actions+=actions;total_substeps+=substeps;verified[method]=by;models[method]=methods_models;sources[method]=methods_sources
 assert total_actions==report['total_actions']<=123750 and total_substeps==report['total_substeps']<=99000000
 return dict(report=ref(root/'REVIEW.json'),plan=ref(root/'PLAN.json'),total_actions=total_actions,total_substeps=total_substeps,methods=verified,models=models,evaluators=sources)

def main():
 args=argparse.ArgumentParser();args.add_argument('--preflight41',action='store_true');a=args.parse_args()
 if a.preflight41:
  result=audit(41);(OUT/'PREFLIGHT41.json').write_text(json.dumps(dict(passed=True,time=time.time(),cycle41_only=True,result=result,source_sha256=sha(Path(__file__)),actual55_review_completed=False),indent=2)+'\n');print('Complete frozen41 independent arithmetic and gates passed; no55 claim.');return
 reg=read(OUT/'PLAN.json');assert sha(Path(__file__))==reg['sources']['review_compare.py']
 before,after=audit(41),audit(55);plans=[read(ROOTS[c]/'PLAN.json') for c in [41,55]]
 for key in ['controllers','case_ids','conditions','action_seed','maximum_actions','maximum_substeps','maximum_episode_seconds','runtime']:assert plans[0][key]==plans[1][key],key
 limits=read(ROOTS[55]/'COMPARISON_LIMITATIONS.json');assert limits['baseline_replay_capacity']==2000000 and limits['evaluation_replay_capacity']==4000000
 methods={}
 for method in plans[0]['controllers']:
  pairs=[]
  for case in plans[0]['case_ids']:
   x=before['methods'][method][case];y=after['methods'][method][case]
   assert before['models'][method][case]==after['models'][method][case]
   assert before['evaluators'][method][case]==after['evaluators'][method][case]
   pairs.append(dict(condition=case,before41=x,after55=y,reward_delta=y['reward']-x['reward'],task_changed=x['task']!=y['task'],strict_changed=x['strict']!=y['strict']))
  methods[method]=dict(all30=pairs,mean_reward_delta=math.fsum(p['reward_delta'] for p in pairs)/30,task41=sum(p['before41']['task'] for p in pairs),task55=sum(p['after55']['task'] for p in pairs),strict41=sum(p['before41']['strict'] for p in pairs),strict55=sum(p['after55']['strict'] for p in pairs),recovered_strict=[p['condition'] for p in pairs if not p['before41']['strict'] and p['after55']['strict']],lost_strict=[p['condition'] for p in pairs if p['before41']['strict'] and not p['after55']['strict']])
 report=dict(passed=True,time=time.time(),methods=methods,before41=before,after55=after,comparison_limitations=limits,source_sha256=sha(Path(__file__)),new_physics=0,optimizer_updates=0,convergence_claim=False,plot_inspected=False,limitation='Complete90 each, same original30 training conditions/action seed/MJB/executed evaluator. Full report scalar/gate/source checks; original raw-substep/filter/torque audits retained, not independent physical resimulation. Replay2m vs4m and training exposure differ; no isolated capacity causality, generalization, seed robustness, or final ESN comparison.')
 (OUT/'REVIEW.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps({m:{k:v for k,v in r.items() if k!='all30'} for m,r in methods.items()},indent=2))
if __name__=='__main__':main()
