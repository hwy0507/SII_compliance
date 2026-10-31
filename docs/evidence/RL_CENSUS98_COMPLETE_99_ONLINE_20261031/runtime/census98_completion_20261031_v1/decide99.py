from pathlib import Path
import json,hashlib,time,math
D=Path(__file__).resolve().parent;B=D.parents[1];read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
S=D/'COMPLETE98_SCIENTIFIC_REVIEW.json';r=read(S);assert r['passed'] and read(D/'COMPLETION_REVIEW.json')['all_complete']
W=B/'runs/parameter_census97_99_reward_stability_20261031_v1';plan=read(W/'PLAN.json');assert plan['cycles']==[97,98,99] and plan['relative_limit']==.05 and plan['near_zero_guard']==1
for name,key in [('audit.py','source_sha256'),('review_saved.py','review_source_sha256')]:assert sha(W/name)==plan[key]
facts={};early={}
for m,x in r['methods'].items():
 means=[]
 for c in [97,98]:
  p=B/f'runs/parameter_census_cycle{c}_20261031_v1/{m}/train/episodes.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];assert len(rows)==30
  value=math.fsum(a['reward'] for a in rows)/30;expected=read(B/f'runs/parameter_census_cycle{c}_review_20261031_v1/REVIEW.json')['methods'][m]['reward_mean'];assert abs(value-expected)<1e-12;means.append(value)
 assert min(map(abs,means))>=1
 relative=abs(means[1]-means[0])/abs(means[0]);assert relative>.05
 early[m]=dict(means97_98=means,adjacent_relative_change=relative,limit=.05,necessary_five_percent_condition_passed=False)
 facts[m]=dict(checkpoint_sha256=x['training']['checkpoint_sha256'],steps=x['training']['steps'],reward_mean=x['training']['reward_mean'],reward_delta_from97=x['reward_change'],original_loss=x['loss']['agent_train/original_sampled_q_loss'],old_terminal_masked_sse_change=x['fixed97_terminal_groups']['all']['relative_change'],new98_terminal_masked_sse=x['new98_terminal_diagnosis']['total_new98_masked_sse'],task_gained=x['task_gained'],task_lost=x['task_lost'],strict_gained=x['strict_gained'],strict_lost=x['strict_lost'])
put(D/'WINDOW97_99_NECESSARY_CONDITION_98.json',dict(time=time.time(),passed=True,methods=early,window=[97,98,99],final_window_statistics_run=False,cycle99_missing=True,convergence_claim=False,scope='Independent complete97/98 episode means and original adjacent5% necessary condition. All three already exceed5%; final nine-input/99/bootstrap audit still pending. No shifted window.'))
evidence=[S,D/'FULL_LOSS_SAVED_REVIEW.json',D/'FULL_CONTEXT_REVIEW.json',D/'COMPLETION_REVIEW.json',D/'WINDOW97_99_NECESSARY_CONDITION_98.json',B/'runs/census98_new_terminal_diagnosis_20261031_v1/DIAGNOSIS.json',B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',B/'runs/parameter_census94_96_reward_stability_20261031_v1/REVIEW.json']
result=dict(time=time.time(),passed=True,decision='prepare_and_register_one_finite99_from_exact_complete98',parent_cycle=98,new_cycle=99,new_cycles=1,maximum_new_actions_per_method=41250,actual99_restore=False,online99_launched=False,automatic100=False,direct34=False,convergence_claim=False,optimizer_settings_changed=False,reward_physics_changed=False,capacity_unchanged=6000000,original_third_capacity_stage_must_be_preserved=True,offline_weights_promoted=False,facts=facts,evidence=[dict(path=str(p),sha256=sha(p)) for p in evidence],reason='Complete98 state/logs/arrays/scalars/all90 labels/old8713 and new90 terminals/full context/all5 plots verified. New terminal fitting error reduced but I sampled Q drifts up, A/V original-loss late spikes and actor drift persist; V old masked error worsens and A/V Strict regress. Complete one finite unchanged stage99 from exact latest98 to continue adaptation and finish originally fixed97–99 observation, whose97→98 adjacent5% necessary condition already fails for all methods. No success claim, threshold relaxation/window shift/automatic100. Actual full-state/native/CPU/resource/protocol/launch gates remain mandatory.',required_before_launch=['separate99 scientific registration and source manifest','complete98 exact learner/Adam/replay/RNG restore and two repeated65536 native updates per method, restore original state','120 corrupt contract rejections and CPU consumers','resource and original97–99 protocol checks','all98 original scientific jobs complete, separate99 launch gate'])
put(D/'NEXT_FINITE_DECISION.json',result);print(json.dumps(early,indent=2))
