"""Prospectively register one finite shared-data readout refit, before any fit."""
import argparse
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
from research72_rl_final_boundary_20261004 import process_info,option,sha
from research72_refit_data_receipt_20261003 import verify
from research72_slot_handoff_20261004 import owners


def read(path):return json.loads(path.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','data-receipt','forecast','parity','fitting-source'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--check-only',action='store_true');a=p.parse_args();root=a.root.resolve()
    target=root/'AMENDMENT_02_CONTEXT_READOUT_REFIT.json'
    assert not target.exists() and not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    protocol=read(root/'PROTOCOL.json');pdigest=sha(root/'PROTOCOL.json');now=datetime.now(timezone.utc)
    assert now<datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    old=read(root/'AMENDMENT_01_CONTEXT_MEMORY.json')
    assert old['protocol_sha256']==pdigest and old['new_learning_cap_per_family_seed']==48
    receipt=read(a.data_receipt);verified=verify(root)
    for key in ('training_data_sha256','dataset_metadata_sha256','teacher_choice_sha256','teacher_execution_sha256'):
        assert receipt[key]==verified[key]
    assert not receipt['reused_original_teacher']
    forecast=read(a.forecast);assert forecast['forecast_only'] and not forecast['final_condition_contents_read']
    assert forecast['optional_episodes_hypothetical']==144
    assert forecast['rl_budget']['all_fifteen_common_boundary']
    assert 0<=(now-datetime.fromisoformat(forecast['snapshot_utc'])).total_seconds()<900
    for path,digest in forecast['inputs'].items():assert sha(path)==digest
    p90=next(row for row in forecast['scenarios'] if row['episode_time_basis']=='p90')
    assert p90['total_ideal_slack_with_optional_and_reserve_hours']>=3
    assert p90['development_ideal_slack_with_optional_hours']>=3
    parity=read(a.parity)
    assert parity['new_fits']==parity['physics_steps']==parity['training_updates']==0
    for path,digest in parity['source_sha256'].items():assert sha(a.fitting_source/path)==digest
    assert len(parity['rows'])==4 and all(row['export_exact'] and row['unused_field_isolation'] and
        row['zero_equilibrium'] and not row['projection_trainable'] and row['max_abs_error']<1e-11 for row in parity['rows'])
    leases=owners(root);queues=[]
    for index in range(3):
        path=root/f'rl_office_adaptation_v2/queue_{index}/execution.json';q=read(path)
        assert q['status']=='running' and any(row['segments'] for row in q['rows'])
        pid=q['simulation_lease']['owner_pid'];info=process_info(pid)
        assert pid in leases and option(info['argv'],'--root')==str(root) and option(info['argv'],'--queue')==str(index)
        queues.append(dict(queue=index,process=info,observed_slot=leases[pid]))
    result=dict(registered_utc=now.isoformat(),scope='fixed_state_context_readout_selected_teacher_refit',
        protocol_sha256=pdigest,previous_learning_cap_per_family_seed=48,new_learning_cap_per_family_seed=60,
        applies_to_all_learning_families=True,sealed_contents_read=False,
        learning_rate_selection_sha256=sha(root/'NEURAL_LR_SELECTION.json'),
        data_receipt=str(a.data_receipt.resolve()),data_receipt_sha256=sha(a.data_receipt),
        training_data_sha256=receipt['training_data_sha256'],training_identities=receipt['qualifying_train_identities'],
        validation_identities=receipt['qualifying_validation_identities'],
        engineering_parity=str(a.parity.resolve()),engineering_parity_sha256=sha(a.parity),
        forecast=str(a.forecast.resolve()),forecast_sha256=sha(a.forecast),observed_rl_queues=queues,
        additional_development_episodes=144,new_models=18,source_sha256=sha(__file__),
        mechanism='128 fixed state-times-current-proprioception readout features, same128 reservoir and18 allowed input fields. No leak gate. ESN learns only3780 readout coefficients. Teacher remains offline.',
        rationale='Earlier parity probe shows the existing readout cannot immediately condition a remembered load on changed current proprioception when current load is zero. Test the fixed readout interaction with actual selected-teacher trajectories. Benefit remains unproven.',
        data='All six imitation families receive the identical selected-teacher20train/5validation data. Original failed attempts and old candidates remain. No synthetic/development/final labels.',
        jobs='Per seed: ESN12 ridge candidates; memoryless12; matched MLP/RNN and ordinary MLP/RNN one4000-update point fit each at earlier fixed validation-selected rates. Three seeds,18models. No further rate/gate/loss search.',
        accounting='Cumulative ESN60 ridge candidates per seed, memoryless36, pooled ordinary+matched MLP/RNN16 each. Count parent fits, failed teacher collection, actual training and development separately; not equal compute.',
        development='All18models on all8 existing development identities. Aggregate all3seeds by unchanged strict/task/horizon/penetration/RMSE/torque/lexical rule. Earlier eligible candidates remain; no successful-only admission or seed selection.',
        resources='Fit locally1thread/MemoryMax3GiB, archive source/data/models onSpark. Development uses the shared four-slot cap; no stable runtime/source changes. Three realRL queues already hold leases.',
        limits='Same environment/input/action/filter/gates/deadlines. Complete final38x24 preserved. Forecast includes maximum2750unused RL steps each and2h reporting; remaining P90 margin>=3h but contention/waits are not guaranteed.',
        interpretation='New data plus readout change is a system variant, not an isolated readout-mechanism ablation. Same-data ESN/memoryless/matched comparisons remain available; no preset winner.')
    if a.check_only:print(json.dumps(dict(eligible=True,models=18,episodes=144,actual_registration=False)));return
    with target.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(registered=str(target),sha256=sha(target),models=18,episodes=144)))


if __name__=='__main__':main()
