from pathlib import Path
import json,hashlib,time,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results={}
for m,focus in [('vmc',[2050526,2299142,2046571,2423133,2423122]),('admittance',[2752093])]:
 P=B/f'runs/{m}72_terminal_anchor_followup_20261028_v1';plan=json.loads((P/'PLAN.json').read_text());old=json.loads((B/f'runs/{m}71_terminal_anchor_followup_20261028_v1/PLAN.json').read_text())
 assert plan['fixed_anchor_rows']==2154 and plan['expected_complete72_terminal_rows']==2184
 for n,h in plan['sources'].items():assert sha(P/n)==h
 for ref in plan['inputs'].values():assert sha(Path(ref['path']))==ref['sha256']
 assert 'cycle72' in plan['parent_run'] and 'cycle_00072.pt' in plan['final_checkpoint']
 assert plan['focus_replay_indices']==old['focus_replay_indices']==focus
 tree=ast.parse((P/'track.py').read_text());assert any(isinstance(n,ast.For) and isinstance(n.iter,ast.Subscript) and isinstance(n.iter.value,ast.Name) and n.iter.value.id=='plan' and isinstance(n.iter.slice,ast.Constant) and n.iter.slice.value=='focus_replay_indices' for n in ast.walk(tree))
 results[m]=dict(plan_sha256=sha(P/'PLAN.json'),all_source_and_input_hashes_exact=True,old_rows=2154,expected_complete72_rows=2184,focus_replay_indices=focus,unchanged_from_prior_plan=True,source_reads_plan_focus=True,actual72_paths_verified=True)
out=B/'runtime/parameter72_followups_snapshot_20261028_v1/DEPLOYMENT_STATIC_REVIEW.json';assert not out.exists()
r=dict(passed=True,time=time.time(),methods=results,source_sha256=sha(Path(__file__)),initial_check_failure=dict(error='AssertionError',cause='Temporary pre-save checker incorrectly searched for literal focus list in track.py; actual source reads plan[focus_replay_indices].',scope='Checker assumption only; no scientific source, PLAN, input, training or waiter changed.'),convergence_claim=False)
out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
