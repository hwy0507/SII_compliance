"""Read-only comparison of original25 and mixed55 demonstrations.

Recompute available raw telemetry; never infer missing completion/comfort from
positive-only labels. Historical peak torque can be recovered from the original
teacher audit plus the published per-identity selected-minus-original delta.
This is a descriptive dataset audit, not a student or paired teacher experiment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform

import numpy as np

from run_nonrl_spt_matrix_20261025 import completion_time, comfort_and_safety, read, sha


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def summarize(rows):
    complete = all(r['completion_time_s'] is not None for r in rows if r['task'])
    contact = all(r['comfort'] is not None for r in rows)
    duration = sum(r['comfort']['human_contact_duration_s'] for r in rows) if contact else None
    compliant = sum(r['comfort']['human_contact_duration_s'] *
                    (r['comfort']['human_comfort_torque_compliance'] or 0) for r in rows) if contact else None
    return dict(
        episodes=len(rows), task=sum(r['task'] for r in rows),
        strict=sum(r['strict'] for r in rows),
        dual_success=sum(r['task'] and r['strict'] for r in rows),
        peak_torque_mean_nm=float(np.mean([r['peak_torque_nm'] for r in rows])),
        peak_torque_worst_nm=max(r['peak_torque_nm'] for r in rows),
        completion_time_mean_s=(float(np.mean([r['completion_time_s'] for r in rows if r['task']]))
                                if complete and any(r['task'] for r in rows) else None),
        completion_time_min_s=(min(r['completion_time_s'] for r in rows if r['task'])
                               if complete and any(r['task'] for r in rows) else None),
        contact_duration_s=duration,
        comfort_contact_time_weighted=compliant / duration if duration else None,
        machine_safety_violations=sum(r['comfort']['machine_safety_violation'] for r in rows) if contact else None,
        spt_common_55=None,
        missing_completion=sum(r['task'] and r['completion_time_s'] is None for r in rows),
        missing_contact_telemetry=sum(r['comfort'] is None for r in rows),
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    require(not a.output.exists(), 'Output already exists; preserve earlier results')
    bench = Path(__file__).resolve().parents[1]
    repo = bench.parents[1]
    old = bench/'outputs/research72_20261003_1149/demonstrations_refined_v1'
    new = bench/'outputs/teacher_student_15h_20261012_v3'
    evidence = bench/'docs/evidence/research72_20261003'
    receipts = [old/'DATA_COMPLETE.json', old/'QUALIFICATION_LEDGER.json',
                new/'data/DATA_COMPLETE.json', new/'data/QUALIFICATION_LEDGER.json',
                evidence/'TEACHER_BANK_SUMMARY.json', evidence/'TEACHER_TRAIN_PAIRED_DATA_AUDIT.json',
                evidence/'TEACHER_DATA_VALIDATION_COMPARISON.json']
    old_meta, new_meta = read(receipts[0]), read(receipts[2])
    require(sha(old/'training_data.npz') == old_meta['training_data_sha256'], 'Original dataset hash')
    require(sha(new/'data/training_data.npz') == new_meta['training_data_sha256'], 'Mixed dataset hash')
    require(sha(receipts[1]) == old_meta['qualification_ledger_sha256'], 'Original ledger hash')
    with np.load(old/'training_data.npz') as x, np.load(new/'data/training_data.npz') as y:
        require(set(x.files) == set(y.files), 'Dataset fields differ')
        prefix = {k: bool(np.array_equal(x[k], y[k][:len(x[k])])) for k in x.files}
        require(all(prefix.values()), 'Original25 prefix changed')
    initial = {r['name']: r['audit'] for r in read(receipts[4])['rows']}
    paired = {}
    for f, n in [(receipts[5], 32), (receipts[6], 8)]:
        data = read(f)
        require(len(data['paired']) == n, 'Historical paired identity count')
        for r in data['paired']:
            require(r['condition_id'] not in paired, 'Duplicate historical condition')
            paired[r['condition_id']] = r
        recovered = [initial[r['condition_id']]['peak_torque_nm'] +
                     r['selected_minus_initial']['peak_torque_nm'] for r in data['paired']]
        require(np.isclose(np.mean(recovered), data['summaries']['selected']['metrics_all']['peak_torque_nm']['mean'],
                           rtol=0, atol=1e-10), 'Historical reconstructed peak mean mismatch')
    rows = []
    for r in read(receipts[1]):
        cid = r['condition_id']; delta = paired[cid]
        require(r['task_success'] == delta['selected_task'] and r['strict_success'] == delta['selected_strict'],
                'Historical qualification mismatch')
        rows.append(dict(condition=cid, cohort='original', role=r['role'], included=r['included'],
                         task=r['task_success'], strict=r['strict_success'],
                         peak_torque_nm=initial[cid]['peak_torque_nm'] + delta['selected_minus_initial']['peak_torque_nm'],
                         peak_source='historical_audit_plus_published_paired_delta_not_raw_recomputed',
                         completion_time_s=None, comfort=None, raw_path=r['run']))
    require(len(rows) == 40 and sum(r['included'] for r in rows) == 25, 'Original cohort mismatch')
    require(len(new_meta['lineage']) == 55, 'Mixed lineage count')
    lineage = {r['condition_id']: r for r in new_meta['lineage'][25:]}
    hashes = {}
    pending = []
    for r in read(receipts[3]):
        if 'task' not in r:
            pending.append(r)
            continue
        cid = r['condition_id']; run = Path(r['run'])
        audit = read(run/'AUDIT.json'); execution = read(run/'execution.json')
        require(execution['status'] == 'complete', f'Unfinished raw execution: {cid}')
        require(execution['runtime_provenance']['physics_dt_s'] == 5e-5, 'Physics dt changed')
        require(audit['task_success'] == r['task'] and audit['strict_success'] == r['strict'], 'New success mismatch')
        require(audit['full_horizon'] and audit['physical_seconds'] > 54.99, 'Incomplete episode')
        require(audit['action_replay_max_abs'] == 0 and audit['common_filter_replay_max_abs'] == 0,
                'Existing action/filter audit not passed')
        h = {f: sha(run/f) for f in ['AUDIT.json', 'execution.json', 'config.json', 'rollout.json', 'rollout.npz',
                                    'rollout.mjb', 'execution_chain.npz', 'research_substeps.npz',
                                    'rollout_metrics/substep_metrics.npz']}
        require(h['rollout.npz'] == r['trace_sha256'] == audit['trace_sha256'], 'Trace hash')
        require(h['execution_chain.npz'] == audit['chain_sha256'], 'Chain hash')
        require(h['rollout.mjb'] == audit['model_sha256'], 'Model hash')
        require(h['rollout_metrics/substep_metrics.npz'] == audit['metrics_sha256'], 'Substep hash')
        require(h['config.json'] == execution['config_sha256'], 'Config hash')
        if r['included']:
            l = lineage[cid]
            require(h['execution.json'] == l['execution_sha256'] and h['rollout.npz'] == l['sha256']
                    and h['execution_chain.npz'] == l['chain_sha256']
                    and h['config.json'] == l['teacher_config_sha256'], 'Dataset lineage mismatch')
        hashes[cid] = h
        c = comfort_and_safety(run)
        require(c['comfort_threshold_nm'] == [43.5]*4 + [6.0]*3, 'Actuator thresholds changed')
        peak = max(c['peak_torque_by_joint_nm'])
        require(np.isclose(peak, audit['peak_torque_nm'], rtol=0, atol=1e-6), 'Raw peak mismatch')
        t = completion_time(run)
        require(not r['task'] or t is not None, 'Successful completion time unavailable')
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            dt = z['dt']
        with np.load(run/'research_substeps.npz') as z:
            force = z['contact_force_sum'][:, 2]
        require(len(dt) == len(force) == 1100000 and np.allclose(dt, 5e-5, rtol=0, atol=1e-12), 'Substep grid')
        c.update(human_force_peak_n=float(force.max()), human_contact_impulse_ns=float(np.sum(dt[force > .05] * force[force > .05])))
        rows.append(dict(condition=cid, cohort='appended', role=r['role'], included=r['included'],
                         task=r['task'], strict=r['strict'], peak_torque_nm=peak,
                         peak_source='raw_substep_recomputed', completion_time_s=t,
                         comfort=c, raw_path=str(run)))
        print(f'{cid}: peak={peak:.4f}, T={t}, comfort={c["human_comfort_torque_compliance"]}', flush=True)
    groups = dict(original25=[r for r in rows if r['cohort'] == 'original' and r['included']],
                  appended30=[r for r in rows if r['cohort'] == 'appended' and r['included']],
                  mixed55=[r for r in rows if r['included']],
                  original_collection40=[r for r in rows if r['cohort'] == 'original'],
                  appended_collection50=[r for r in rows if r['cohort'] == 'appended'],
                  combined_collection90=rows)
    require([len(v) for v in groups.values()] == [25,30,55,40,50,90] and len(pending) == 30, 'Cohort counts')
    summaries = {k: summarize(v) for k,v in groups.items()}
    # This reference is explicitly local to the newly collected subset, never
    # substituted for the unknown full55 reference or compared against old25.
    subset_ref = min(r['completion_time_s'] for r in groups['appended30'])
    for k in ['appended30', 'appended_collection50']:
        summaries[k]['spt_new_collection_only'] = float(np.mean([
            subset_ref/max(r['completion_time_s'], subset_ref) if r['task'] and r['strict'] else 0.
            for r in groups[k]]))
    result = dict(status='partial_comparison_missing_original_raw', created_utc=datetime.now(timezone.utc).isoformat(),
                  host=platform.node(), simulated_episodes=0, fits=0,
                  original_dataset_sha256=old_meta['training_data_sha256'],
                  mixed_dataset_sha256=new_meta['training_data_sha256'], original_prefix_identical=prefix,
                  input_hashes={str(f.relative_to(repo)): sha(f) for f in receipts},
                  source_hashes={Path(__file__).name:sha(Path(__file__)),
                                 'run_nonrl_spt_matrix_20261025.py':sha(bench/'tools/run_nonrl_spt_matrix_20261025.py')},
                  shared_t_ref_s=None, shared_spt_status='unknown_without_original25_completion_times',
                  new_collection_only_t_ref_s=subset_ref, summaries=summaries, rows=rows,
                  pending_or_unfinished=pending, raw_hashes=hashes,
                  limitations=['Included demonstrations are positive-only; 100% is selection, not generalization.',
                               'Original raw path absent on registered host; local dataset has no raw torque/contact/time.',
                               'Original peaks recovered from historical audited values; not independently recomputed today.',
                               'Full55 SPT/comfort unknown; no missing values are filled using appended subset.',
                               'Teacher configuration and disturbance identities differ; not a paired teacher comparison.',
                               'No students retrained/evaluated; cannot choose training dataset by student effect here.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    print(json.dumps(summaries, indent=2))


if __name__ == '__main__':
    main()
