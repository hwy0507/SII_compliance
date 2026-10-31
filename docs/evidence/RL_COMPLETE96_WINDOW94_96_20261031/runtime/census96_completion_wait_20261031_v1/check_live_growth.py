"""Audit a stable live prefix that contains actual newly completed96 episodes."""
from pathlib import Path
import hashlib,json,os,sys,time,copy
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census96_completion_wait_20261031_v1'
C=B/'runtime/census96_comparison_20261031_v1';sys.path.insert(0,str(C))
from check_terminal_population import audit_rows,sha,read
os.sched_setaffinity(0,{54});os.nice(15)
plan=read(C/'CACHE_POPULATION_PLAN.json');assert sha(C/'check_terminal_population.py')==plan['source_sha256']
for p,h in plan['inputs'].items():assert sha(p)==h
def lines(p):
 data=p.read_bytes();data=data[:data.rfind(b'\n')+1];return data.splitlines(keepends=True)
results={}
for method,e in plan['methods'].items():
 run=B/'runs/parameter_census_cycle96_20261031_v1'/method;reg=read(run/'REGISTRATION.json')
 tp=run/'train/transitions.jsonl';up=run/'train/optimizer.jsonl';ep=run/'train/episodes.jsonl'
 tl=lines(tp);ul=lines(up);n=min(len(tl),len(ul));tb=b''.join(tl[:n]);ub=b''.join(ul[:n])
 transitions=[json.loads(x) for x in tl[:n]];updates=[json.loads(x) for x in ul[:n]]
 result=audit_rows(transitions,updates,reg['post_interruption_continuation']['parent_steps'],e['terminal_rows'])
 assert result['new_terminal_rows']>0,'Need actual new terminals, not all-nonterminal prefix'
 episodes=[json.loads(x) for x in lines(ep)];by_condition={x['condition']:x for x in episodes}
 assert len(by_condition)==len(episodes)
 for change in result['changes']:
  episode=by_condition[change['condition']]
  assert episode['cycle']==96 and episode['steps']==1375 and episode['full_task_horizon_completed'] and not episode.get('abort_reason')
 assert len({c['condition'] for c in result['changes']})==result['new_terminal_rows']
 # A corrupted actual new-terminal diagnostic must fail, not just a synthetic done.
 bad=copy.deepcopy(updates);idx=next(i for i,t in enumerate(transitions) if t['done']);bad[idx]['agent_train/terminal_population']-=1
 try:audit_rows(transitions,bad,reg['post_interruption_continuation']['parent_steps'],e['terminal_rows'])
 except ValueError:rejected=True
 else:raise AssertionError('Accepted missed real terminal growth')
 with tp.open('rb') as f:assert f.read(len(tb))==tb
 with up.open('rb') as f:assert f.read(len(ub))==ub
 result.update(prefix_transition_bytes=len(tb),prefix_update_bytes=len(ub),transition_prefix_sha256=hashlib.sha256(tb).hexdigest(),update_prefix_sha256=hashlib.sha256(ub).hexdigest(),transition_path=str(tp),optimizer_path=str(up),completed_episode_conditions_matched=True,actual_growth_corruption_rejected=rejected)
 results[method]=result
report=dict(passed=True,time=time.time(),original_audit_source=dict(path=str(C/'check_terminal_population.py'),sha256=sha(C/'check_terminal_population.py')),methods=results,full96=False,checkpoint_replay_checked=False,online_stratum_tensors_observed=False,physics_steps=0,optimizer_updates=0,scope='All aligned updates in stable live prefixes checked against retained95 count plus inclusive real96 done events; changed conditions matched actual complete episodes. Full96 replay/32strata/health/reward convergence still pending.')
with (O/'LIVE_TERMINAL_GROWTH_REVIEW.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({m:dict(rows=r['rows'],new_terminals=r['new_terminal_rows'],final_population=r['final_population']) for m,r in results.items()}))
