"""Read completed v8 regression rows; no fitting, simulation or model selection.

Ranges use training frames only. Exceeding a marginal range is descriptive,
not causal evidence: closed-loop errors may themselves create novel states.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from audit_special_frozen108_20261028 import verify_episode
from prepare_special_frozen_test_20261028 import manifest, read, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', type=int, default=2)
    args = parser.parse_args()
    assert args.count > 0 and not args.output.exists()
    preparation = args.preparation.resolve()
    plan = read(preparation/'REGISTRATION.json')
    root, training, parent_root = [Path(plan[k]) for k in ('evaluation', 'training', 'source_run')]
    assert manifest(root/'source') == plan['physics_source_sha256']
    state = read(root/'execution.json')
    rows = state['results'][:args.count]
    assert len(rows) == args.count
    lock = read(root/'INPUT_MODEL_LOCK.json')
    assert sha(root/'INPUT_MODEL_LOCK.json') == sha(training/'MODEL_LOCK.json')
    models = {m['name']: m for m in lock['models']}
    parent = read(parent_root/'REGISTRATION.json')
    parent['formal_model_sha256'] = read(parent_root/'PROTOCOL.json')['formal_model_sha256']
    conditions = {c['id']: c for c in read(parent_root/'CONDITIONS.json')['conditions']}
    dataset = training/'data/training_data.npz'
    assert sha(dataset) == lock['training_data_sha256']
    with np.load(dataset, allow_pickle=False) as z:
        train = z['observation'][z['train']].copy()
        assert len(train) == 12600
    columns = list(range(14,17))+list(range(20,23))+list(range(26,29))+list(range(39,48))
    lo, hi = train.min(axis=0), train.max(axis=0)
    results, verified = [], set()
    for row in rows:
        checked = verify_episode(row, models[row['method']], conditions[row['condition']], root,
                                 root/'source', parent, verified)
        run = Path(row['run'])
        audit = read(run/'AUDIT.json')
        with np.load(run/'rollout.npz', allow_pickle=False) as z:
            obs, time, stage, contacts = [z[k].copy() for k in ('observation','time','stage','prior_contact_peak')]
        with np.load(run/'execution_chain.npz', allow_pickle=False) as z:
            action = z['requested_action'].copy()
        assert len(obs) == len(time) == len(action) and np.isfinite(obs).all()
        outside = (obs < lo-1e-12) | (obs > hi+1e-12)
        # Independent scalar recount on all selected columns and frames.
        for k in columns:
            count = sum(float(v) < float(lo[k])-1e-12 or float(v) > float(hi[k])+1e-12 for v in obs[:,k])
            assert count == int(outside[:,k].sum())
        stages = []
        for s in sorted(set(stage.tolist())):
            mask = stage == s
            stages.append(dict(stage=int(s), frames=int(mask.sum()), start_s=float(time[mask][0]),
                end_s=float(time[mask][-1]), selected_any_outside_fraction=float(outside[mask][:,columns].any(axis=1).mean()),
                mean_requested_action=action[mask].mean(axis=0).tolist(),
                peak_abs_requested_action=np.abs(action[mask]).max(axis=0).tolist(),
                estimated_wrench_rms=np.sqrt(np.mean(obs[mask,39:45]**2,axis=0)).tolist()))
        results.append(dict(row=row, independent_saved_evidence_check=checked,
            worst_pair=audit['worst_pair'], stage=audit['stage'],
            actor_replay_max_abs=audit['action_replay_max_abs'],
            filter_replay_max_abs=audit['common_filter_replay_max_abs'],
            frames=len(obs), stages=stages,
            prior_contact_columns=['ball','person_hand','rod','cup','pillar'],
            prior_contact_peaks=contacts.max(axis=0).tolist(),
            prior_contact_limitation='These five channels omit unexpected_edge; zero is not proof of no contact.',
            ranges=[dict(column=k, training_min=float(lo[k]),training_max=float(hi[k]),
                actual_min=float(obs[:,k].min()),actual_max=float(obs[:,k].max()),
                outside_frames=int(outside[:,k].sum()),
                first_outside_s=float(time[np.flatnonzero(outside[:,k])[0]]) if outside[:,k].any() else None)
                for k in columns]))
    assert read(root/'execution.json')['results'][:args.count] == rows
    result = dict(status='completed_prefix_saved_evidence_and_training_range_checked',
        created_utc=datetime.now(timezone.utc).isoformat(), preparation=str(preparation),
        registration_sha256=sha(preparation/'REGISTRATION.json'), dataset_sha256=sha(dataset),
        model_lock_sha256=sha(root/'INPUT_MODEL_LOCK.json'), diagnostic_source_sha256=sha(Path(__file__)),
        episode_auditor_sha256=sha(Path(__file__).with_name('audit_special_frozen108_20261028.py')),
        completed_prefix=args.count, training_frames=len(train), rows=results,
        verified_physics_sources=[dict(path=n,sha256=h) for n,h in sorted(verified)],
        limitations='Completed prefix only, not the complete108 or a method ranking. No new physical rollout, no independent dynamics reintegration. Training marginal ranges are not joint-distribution or causal tests. Test histories excluded from fitting and checkpoint selection.')
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'],rows=args.count)))


if __name__ == '__main__':
    main()
