from pathlib import Path
import json,math,time,hashlib

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def review_paired(root, candidate, plan):
    assert plan['pre_tanh_std_factor']==.5
    for ref in plan['baseline_inputs'].values():assert sha(ref['path'])==ref['sha256']
    baseline=json.loads((Path(plan['baseline_root'])/'REVIEW.json').read_text())
    assert baseline['passed'] and baseline['total_episodes']==candidate['total_episodes']==16
    assert set(baseline['groups'])==set(candidate['groups'])==set(plan['groups'])
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(4,2,figsize=(12,12),constrained_layout=True)
    groups={}
    for i,key in enumerate(plan['groups']):
        old,new=baseline['groups'][key],candidate['groups'][key]
        assert old['checkpoint_sha256']==new['checkpoint_sha256']
        assert old['initial_and_final_learner_digest']==new['initial_and_final_learner_digest']
        assert [r['seed'] for r in old['rows']]==[r['seed'] for r in new['rows']]==plan['action_seeds']
        rows=[]
        for a,b in zip(old['rows'],new['rows']):
            assert a['condition']==b['condition']==plan['groups'][key]['case_ids'][0]
            rows.append(dict(seed=a['seed'],condition=a['condition'],baseline=a,half_std=b,
                reward_delta=b['reward']-a['reward'],task_change=int(b['task'])-int(a['task']),
                strict_change=int(b['strict'])-int(a['strict']),penetration_delta_mm=b['penetration_mm']-a['penetration_mm']))
        delta=math.fsum(r['reward_delta'] for r in rows)/4
        assert math.isclose(delta,new['reward_mean']-old['reward_mean'],abs_tol=1e-12)
        groups[key]=dict(rows=rows,baseline_task=old['task'],half_std_task=new['task'],baseline_strict=old['strict'],half_std_strict=new['strict'],mean_reward_delta=delta,task_gained=sum(r['task_change']>0 for r in rows),task_lost=sum(r['task_change']<0 for r in rows),strict_gained=sum(r['strict_change']>0 for r in rows),strict_lost=sum(r['strict_change']<0 for r in rows),candidate_aborts=[r['seed'] for r in rows if r['half_std']['abort_reason']],serialized_state_equal_sampling_distribution_changed=True)
        for col,metric in enumerate(['reward','penetration_mm']):
            for label,key2 in [('Baseline','baseline'),('Half pre-tanh std','half_std')]:
                axes[i,col].plot(range(4),[r[key2][metric] for r in rows],'o-',label=label)
            axes[i,col].set_title(key+' '+metric);axes[i,col].set_xticks(range(4),[str(s) for s in plan['action_seeds']],rotation=15);axes[i,col].legend(fontsize=8);axes[i,col].grid(alpha=.2)
        axes[i,1].axhline(.2,color='black',linestyle='--')
    fig.suptitle('One paired inference intervention at fixed86; all16 original pairs retained')
    plot=root/'paired_half_std_results.png';fig.savefig(plot,dpi=140);plt.close(fig)
    report=dict(passed=True,time=time.time(),groups=groups,all16_pairs_retained=True,baseline_review_sha256=sha(Path(plan['baseline_root'])/'REVIEW.json'),pre_tanh_std_factor=.5,plot_sha256=sha(plot),new_physics=0,new_optimizer_updates=0,new_network_forward=0,no_automatic_promotion=True,limitations=plan['limits'])
    p=root/'PAIRED_REVIEW.json';p.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    saved=json.loads(p.read_text());assert saved==report
    for key,g in saved['groups'].items():
        assert sum(r['task_change'] for r in g['rows'])==g['half_std_task']-g['baseline_task']
        assert sum(r['strict_change'] for r in g['rows'])==g['half_std_strict']-g['baseline_strict']
        assert math.isclose(math.fsum(r['half_std']['reward'] for r in g['rows'])/4-math.fsum(r['baseline']['reward'] for r in g['rows'])/4,g['mean_reward_delta'],abs_tol=1e-12)
    (root/'PAIRED_SAVED_REVIEW.json').write_text(json.dumps(dict(passed=True,all16_read_back=True,all_endpoint_sums_recomputed=True,review_sha256=sha(p),source_sha256=sha(__file__)),indent=2)+'\n')
    return dict(review_sha256=sha(p),plot_sha256=sha(plot),all16_pairs_retained=True)
