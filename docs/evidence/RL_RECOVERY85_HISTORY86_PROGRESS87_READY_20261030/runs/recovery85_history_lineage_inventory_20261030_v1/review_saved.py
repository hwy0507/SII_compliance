from pathlib import Path
import json,time,math,hashlib,collections
D=Path(__file__).parent;r=json.loads((D/'REVIEW.json').read_text());assert r['passed'] and r['audit_completed'];totals={}
for m,x in r['methods'].items():
 p=Path(x['episode_inventory']['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==x['episode_inventory']['sha256'];eps=[json.loads(l) for l in p.read_text().splitlines()];assert len(eps)==x['episode_cohorts'];by=collections.defaultdict(list)
 for e in eps:by[e['train']].append(e);assert e['journal_exists'] and Path(e['journal']).stat().st_size==e['journal_bytes'];assert not e['terminal_required'] or e['terminal_exists']
 prev=0;total=0
 for node in x['roots']:
  assert node['selected_first_step']==prev+1;prev=node['selected_last_step'];n=node['selected_last_step']-node['selected_first_step']+1
  assert n==node['retained_transitions']==sum(e['transitions'] for e in by[node['train']]);assert node['parsed_log_lines']==n+node['post_checkpoint_tail_rows'];assert node['bad_json_lines']==0 and node['step_discontinuities']==[];total+=n
 assert total==prev==x['retained_transition_rows']==x['expected_complete85_steps'];assert sum(not e['terminal_required'] for e in eps)==x['retained_partial_episode_cohorts'];assert not x['problems']
 for i,node in enumerate(x['chain']):
  p=Path(node['registration']['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==node['registration']['sha256']
  if i:assert node['parent']==x['chain'][i-1]['registration']
 totals[m]=dict(physical_logs=len(x['roots']),retained_steps=total,episodes=len(eps),partial_episodes=x['retained_partial_episode_cohorts'],excluded_post_checkpoint_tails=x['post_checkpoint_tail_rows'])
with (D/'SAVED_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=totals,all_saved_cohort_counts_and_step_intervals_recomputed=True,all_registration_chain_hashes_rechecked=True,not_final_checkpoint_row_equality=True),f,indent=2);f.write('\n')
print(totals)
