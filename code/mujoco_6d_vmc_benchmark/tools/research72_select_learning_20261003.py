"""Choose shared learned variants from completed public development only.

Every seed participates in one family-level decision. The separately selected
learning rates remain fixed. No strict-success eligibility filter or heldout
read; missing episodes fail selection rather than silently shrinking a cohort.
"""
import argparse
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import statistics


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rank_variants(candidates,observations,seeds,conditions):
    groups=defaultdict(list)
    for c in candidates:groups[c['category'],c['variant']].append(c)
    ranked=defaultdict(list)
    for (family,variant),models in groups.items():
        assert len(models)==len(seeds) and {m['seed'] for m in models}==set(seeds)
        rows=[]
        for model in models:
            pairs=[observations[model['name'],condition] for condition in conditions]
            assert all(r['checkpoint_sha256']==model['checkpoint_sha256'] for r in pairs)
            rows.extend(pairs)
        strict=sum(r['strict_success'] for r in rows);task=sum(r['task_success'] for r in rows)
        full=sum(r['full_horizon'] for r in rows)
        penetration=max(max(r['penetration_mm'],r['edge_penetration_mm']) for r in rows)
        rmse=statistics.mean(r['rmse_mm'] for r in rows);torque=statistics.mean(r['peak_torque_nm'] for r in rows)
        ranked[family].append(dict(variant=variant,candidates=sorted(models,key=lambda m:m['seed']),
            score=[-strict,-task,-full,penetration,rmse,torque,variant],task=task,strict=strict,
            full_horizons=full,denominator=len(rows),worst_penetration_mm=penetration,
            mean_rmse_mm=rmse,mean_peak_torque_nm=torque))
    for choices in ranked.values():choices.sort(key=lambda x:x['score'])
    return dict(ranked)


def load_phase(phase,protocol,conditions):
    state=read(phase/'execution.json');assert state['status']=='complete'
    spec=read(phase/'SPECIFICATION.json');summary=read(phase/'SUMMARY.json')
    assert spec['protocol_sha256']==protocol and set(spec['conditions'])==set(conditions)
    assert summary['completed']==summary['expected']==len(spec['candidates'])*len(conditions)
    models={m['name']:m for m in spec['candidates']};independent={};evidence=[]
    for analysis in sorted(phase.glob('queue_*_analysis')):
        receipt=read(analysis/'execution.json');assert receipt['status']=='complete'
        audit=analysis/'INDEPENDENT_AUDIT.json'
        assert sha(audit)==receipt['outputs']['INDEPENDENT_AUDIT.json']
        report=read(audit);assert not report['pending']
        for r in report['rows']:
            key=str(Path(r['run']).resolve());assert key not in independent
            independent[key]=r
        evidence.append(dict(path=str(audit),sha256=sha(audit)))
    assert len(independent)==summary['expected']
    observed={}
    for row in summary['rows']:
        c=models[row['candidate']];run=Path(row['run']);r=independent[str(run.resolve())]
        assert sha(run/'AUDIT.json')==r['audit_sha256']==row['audit_sha256']
        assert r['checkpoint_sha256']==c['checkpoint_sha256']
        assert r['frozen_source_hashes_verified'] and r['actuator_amplitude_and_command_slew_valid']
        assert r['actor_replay_performed'] and r['independent_contact_sidecar_verified']
        key=(c['name'],row['condition_id']);assert key not in observed
        observed[key]=r
    evidence.extend(dict(path=str(phase/n),sha256=sha(phase/n)) for n in ('SUMMARY.json','SPECIFICATION.json'))
    return spec['candidates'],observed,evidence


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();protocol=read(root/'PROTOCOL.json');pdigest=sha(root/'PROTOCOL.json')
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists(),'Selection is closed after final opening'
    conditions=[c['id'] for c in read(root/'CONDITIONS.json')['conditions'] if c['role']=='development']
    assert len(conditions)==8 and sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    rates=read(root/'NEURAL_LR_SELECTION.json');assert rates['protocol_sha256']==pdigest
    amendment=read(root/'AMENDMENT_01_CONTEXT_MEMORY.json');assert amendment['protocol_sha256']==pdigest
    assert amendment['learning_rate_selection_sha256']==sha(root/'NEURAL_LR_SELECTION.json')
    observations={};candidates=[];evidence=[];completion=[]
    for label,phase in [('original',root/'learning_development_v1'),
        ('refinement',root/'additional_development_v1/neural_lr_development'),
        ('context',root/'context_gate_development_v1/development')]:
        models,rows,proof=load_phase(phase,pdigest,conditions)
        assert not set(observations).intersection(rows);observations.update(rows);evidence.extend(proof)
        completion.append(dict(path=str(phase/'execution.json'),sha256=sha(phase/'execution.json')))
        if label=='original':candidates.extend(c for c in models if c['category'] in ('esn','memoryless'))
        if label=='context':candidates.extend(models)
    candidates.extend(rates['selected_candidates'])
    assert len({c['name'] for c in candidates})==len(candidates)==54
    candidate_data={c['name']:rates['data_sha256'] for c in candidates}
    refit_amendment=root/'AMENDMENT_02_CONTEXT_READOUT_REFIT.json'
    extra_count=0
    if refit_amendment.exists():
        extra=read(refit_amendment)
        assert extra['protocol_sha256']==pdigest and extra['new_learning_cap_per_family_seed']==60
        assert extra['scope']=='fixed_state_context_readout_selected_teacher_refit'
        phase=root/'context_readout_refit_development_v1'
        models,rows,proof=load_phase(phase,pdigest,conditions)
        spec=read(phase/'SPECIFICATION.json')
        assert spec['amendment_sha256']==sha(refit_amendment)
        extra_count=18 if spec['ordinary_refit_required'] else 12
        assert len(models)==extra_count and len({c['name'] for c in models})==extra_count
        expected={'esn','memoryless','matched_mlp','matched_rnn'}
        if spec['ordinary_refit_required']:expected|={'ordinary_mlp','ordinary_rnn'}
        else:
            assert spec['data_sha256']==rates['data_sha256']
            reused=spec['reused_ordinary_candidates']
            assert len(reused)==6
            assert all(c in rates['selected_candidates'] for c in reused)
            assert {c['category'] for c in reused}=={'ordinary_mlp','ordinary_rnn'}
        assert {c['category'] for c in models}==expected
        assert not set(observations).intersection(rows)
        observations.update(rows);candidates.extend(models);evidence.extend(proof)
        candidate_data.update({c['name']:spec['data_sha256'] for c in models})
        receipt=spec['refit_data_receipt']
        assert receipt['selected_teacher_verified'] and receipt['training_data_sha256']==spec['data_sha256']
        assert all(sha(e['path'])==e['sha256'] for e in receipt['evidence'])
        evidence.extend(receipt['evidence'])
        evidence.append(dict(path=str(refit_amendment),sha256=sha(refit_amendment)))
        completion.append(dict(path=str(phase/'execution.json'),sha256=sha(phase/'execution.json')))
        assert len({c['name'] for c in candidates})==len(candidates)==54+extra_count
    for c in candidates:
        assert sha(Path(c['checkpoint']))==c['checkpoint_sha256']
        metadata=Path(c['checkpoint']).parent/'TRAINING_COMPLETE.json';training=read(metadata)
        assert training.get('training_data_sha256',training.get('data_sha256'))==candidate_data[c['name']]
        c['training_metadata_sha256']=sha(metadata)
        c['training_data_sha256']=candidate_data[c['name']]
    ranked=rank_variants(candidates,observations,protocol['budget_caps']['training_seeds'],conditions)
    assert set(ranked)=={'esn','memoryless','ordinary_mlp','ordinary_rnn','matched_mlp','matched_rnn'}
    selected=[c for choices in ranked.values() for c in choices[0]['candidates']]
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),protocol_sha256=pdigest,source_sha256=sha(Path(__file__)),
        development_evidence=evidence,completion_receipts=completion,ranked=ranked,candidates=selected,
        learning_rate_selection_sha256=sha(root/'NEURAL_LR_SELECTION.json'),
        amendment_sha256=sha(root/'AMENDMENT_01_CONTEXT_MEMORY.json'),
        paired_seed_groups=[dict(name=family,names=[c['name'] for c in choices[0]['candidates']]) for family,choices in ranked.items()],
        selection='Registered aggregate strict/task/full-horizon counts, worst penetration, mean RMSE/torque and lexical variant across every seed/condition; learning rates already selected by identity validation.',
        caveats=[f'{len(candidates)} eligible frozen weight candidates drawn from{75+extra_count} actually evaluated models; earlier unselected learning rates remain in the exposure ledger.',
            'Optional registered final refit uses the same selected-teacher data for every learning family; selected models may still come from older cohorts. Data generation and architecture changes are not an isolated mechanism ablation.',
            'Family-selected ESN versus family-selected memoryless may use different gates/losses; do not call it an isolated memory ablation.',
            'No heldout data read. Selection is not a final result; all selected seeds proceed even when development success is zero.'])
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(selected_models=len(selected),sha256=sha(a.output))))


if __name__=='__main__':main()
