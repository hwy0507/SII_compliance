from pathlib import Path
import json, hashlib, time, math
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def read(p): return json.loads(p.read_text())
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p): return dict(path=str(p),sha256=sha(p))
def write(p,j):
    assert not p.exists(),p
    p.write_text(json.dumps(j,indent=2)+'\n')
loss=B/'runs/parameter62_loss_20261028_v1'
health=B/'runs/parameter_capacity_pool30_cycle62_review_20261026_v1/health'
terminal=B/'runs/vmc62_terminal_anchor_followup_20261028_v1'
for folder,name,notes in [
 (loss,'loss.png','Actual six-panel image inspected. I critic rolling mean roughly2-3, early dense spikes shrink then late burst after35000; actor declines27.65->26.70. A critic nearlyflat/slightlydown with finite spikes, actor initiallyslightdown then rises especiallylate. V critic burst around33500/rawmax32.62 and late meanrise; actor rises then flattens/slightlydown. No new spike threshold or convergence claim.'),
 (health,'training_diagnostics.png','Actual six-panel image inspected. Episode rewards switch between positive successes and negative failures; I critic fluctuates with later rise, A nearflat, V lateburst. I actor declines; A/V graduallyrise. Entropy stays near targets, alpha varies and V rebounds late. Q nextvalues remain separated by method. Top-right long title clipped at right edge; data and axes readable. No convergence or final ranking.'),
 (terminal,'follow62.png','Actual scatter inspected. Most rows nearorigin, several large worsening rows above diagonal. Focus2299142/2050526/2046571 worsen;2423133/2423122 improve. Two labels nearorigin overlap, numerical identities retained in REVIEW. Fixed1854 totalSSE1108.452722->2550.400600 (130.0865percent increase); no zero-error gate or causal claim.')]:
    write(folder/'PLOT_INSPECTION.json',dict(time=time.time(),plot=ref(folder/name),actual_image_inspected=True,notes=notes,convergence_claim=False))
labeldir=B/'runs/parameter_task_label_audit62_20261028_v1'
labels=read(labeldir/'COMPLETE61_62.json'); paired=read(loss/'PAIRED_GATE_REVIEW.json'); lr=read(loss/'REVIEW.json')
assert labels['passed'] and labels['saved_rollouts_checked']==180 and paired['passed']
summary={}
for m,v in labels['methods'].items():
    rows=v['all30']; assert len(rows)==30
    pairs={x['condition']:x for x in paired['methods'][m]['all30_paired']}
    assert set(pairs)=={x['condition'] for x in rows}
    counts={}
    for i,cycle in enumerate([61,62]):
        r=next(x for x in lr['methods'][m]['reward_history'] if x['cycle']==cycle)
        rewards=[x['cases'][i]['reward'] for x in rows]
        assert math.isclose(sum(rewards)/30,r['reward_mean'],abs_tol=1e-12)
        counts[str(cycle)]={key:sum(x['cases'][i][key] for x in rows) for key in ['task','strict','physical_valid']}
        assert counts[str(cycle)]==v['counts'][str(cycle)]
        assert all(counts[str(cycle)][k]==r[k] for k in ['task','strict'])
        for x in rows: assert x['cases'][i]['reward']==pairs[x['condition']][f'reward{cycle}']
    changed={x['condition'] for x in rows if 'strict' in x['changed_fields'] or 'abort_reason' in x['changed_fields']}
    assert changed=={x['condition'] for x in paired['methods'][m]['changes']}
    taskonly=[x['condition'] for x in rows if 'task' in x['changed_fields'] and 'strict' not in x['changed_fields']]
    assert not taskonly and not v['task_only_changes']
    summary[m]=dict(counts=counts,changes=[dict(condition=x['condition'],fields=x['changed_fields']) for x in rows if x['changed_fields']],task_only_changes=taskonly)
write(labeldir/'COMPLETE61_62_SAVED_REVIEW.json',dict(passed=True,time=time.time(),all90_reward_pairs_and_counts_match=True,strict_abort_changes_match_original=True,methods=summary,source=ref(labeldir/'COMPLETE61_62.json'),new_physics=0,optimizer_updates=0))
parent=read(B/'runs/parameter_capacity_pool30_cycle62_review_20261026_v1/REVIEW.json')
hd=read(health/'DIAGNOSIS.json'); run=B/'runs/parameter_capacity_pool30_cycle63_20261026_v1'
assert parent['passed'] and read(loss/'SAVED_REVIEW.json')['passed'] and read(terminal/'SAVED_VALUES_REVIEW.json')['passed']
for m,v in parent['methods'].items():
    ck=read(run/m/'check_only.log')
    assert ck['passed'] and ck['exact_replay_and_next65536'] and ck['full_learner_state_unchanged']
    assert ck['checkpoint_sha256']==v['checkpoint_sha256']==hd['methods'][m]['checkpoint_sha256']
    assert v['retained_replay_all_fields_exact'] and v['optimizer_and_network_finite'] and v['max_reward_reconstruction_error']==0
    assert hd['methods'][m]['network_state_unchanged']
    fin=read(B/f'runs/parameter_capacity_pool30_cycle62_20261026_v1/{m}/train/FINISHED.json')
    assert fin['status']=='stopped_at_complete_cycle'
assert all(x==0 for x in read(run/'CHECK_ONLY_EXIT_CODES.json').values())
old=read(B/'runtime/prepare_parameter62_20261028_v1/DECISION62.json')
evidence={}
for k,v in old['evidence'].items():
    s=v['path']
    if k.startswith('reward_window') or k=='future_window62_64': pass
    elif k in ['all_labels','all_labels_arithmetic']:
        s=s.replace('parameter_task_label_audit_20261028_v1','parameter_task_label_audit62_20261028_v1').replace('COMPLETE60_61','COMPLETE61_62')
    elif k=='check_only' or k.startswith('restore_'): s=s.replace('cycle62_','cycle63_')
    else:
        s=s.replace('cycle61_','cycle62_').replace('parameter61_loss_','parameter62_loss_').replace('vmc61_terminal_','vmc62_terminal_')
    evidence[k]=ref(Path(s))
assert evidence['future_window62_64']['sha256']=='44e0b484fb61c8c640e2e56bfe1ca36b08d96c2098c2c393104ebf9c3713dfc5'
write(Path(__file__).parent/'DECISION63.json',dict(time=time.time(),passed=True,parent_cycle=62,new_cycle=63,new_cycles=1,plot_inspected=True,convergence_claim=False,evidence=evidence,reason='Complete62 all30x55/41250new/noabort, oldfullreplay retained and rewards reconstructed exactly; finite networks/optimizers. All3 rewards regress: I-5.822772 Task/Strict17/15, A-8.573957 14/14, V-4.613582 17/16. I short0100 and V short0000 cross original.2mm, A2 recoveries/3 losses; no Task-only omissions. I actor continuesdown, V critic lateburst and actor stillmoves, A critic modest improvement retained. V fixed1854SSE rises130.0865percent; first3focus worsen and last2 improve. Health finite with A/V sampledQ above bound fraction.001074 retained; not claimed perfect calibration. No new finite-spike or zero-terminal-error gate. Original59-61 failure and historicalI56-58/V53-55 passes retained, original62-64 pending63/64. Exact62 fullstate/replay/next65536 restore passed for all3. Continue one unchanged finite63 to assess settling, noauto64; no resets/auxiliary weights or configuration changes.',automatic_followup=False,configuration_changed=False,direct34=False))
print(json.dumps(dict(passed=True,labels=summary,decision=str(Path(__file__).parent/'DECISION63.json'))))
