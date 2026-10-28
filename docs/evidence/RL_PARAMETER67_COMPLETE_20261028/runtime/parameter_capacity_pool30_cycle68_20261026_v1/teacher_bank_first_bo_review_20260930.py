"""Read-only audit of v10 passive_corner/VMC c03's first actual BO decision.

Independent aggregation from preceding training audits; proposal replay reuses
the frozen optimizer implementation and is expressly not independent GP code.
"""
import argparse
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys

import numpy as np
import scipy


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.run.resolve(), args.output.resolve()
    if output.exists() or root == output or root in output.parents:
        raise ValueError('Require new output directory outside the source run')
    inputs, snapshots = {}, {}

    def read(relative, snapshot=False):
        # Exactly one read of mutable history, then hash and parse those bytes.
        data = (root/relative).read_bytes()
        inputs[relative] = digest(data)
        if snapshot:
            snapshots[relative] = data
        return json.loads(data)

    plan = read('plan.json')
    fixtures = read('fixtures.json')
    assert inputs['fixtures.json'] == plan['fixtures_sha256']
    train = [f for f in fixtures if f['category'] == 'passive_corner' and f['split'] == 'train']
    history_path = 'search/passive_corner/vmc/history.json'
    history_all = read(history_path, snapshot=True)
    prefix = history_all[:3]
    decision_path = 'search/passive_corner/vmc/c03/decision.json'
    decision = read(decision_path, snapshot=True)
    assert len(prefix) == 3 and decision['history_count'] == 3
    assert decision['algorithm'] == 'constrained_gp_bo' and plan['warm_candidates'] == 3
    assert plan['anchor_indices'] == [0, 337, 671]
    aggregate, evidence, models = [], {}, {}
    for index in range(3):
        candidate = f'search/passive_corner/vmc/c{index:02d}'
        prior_decision = read(candidate+'/decision.json')
        x = prior_decision['x']
        assert prior_decision['algorithm'] == 'latin_hypercube'
        rows = []
        for anchor in plan['anchor_indices']:
            relative = candidate+'/'+str(anchor)
            audit = read(relative+'/audit.json')
            request = read(relative+'/request.json')
            assert request['fixture'] == train[anchor]
            assert request['phase'] == 'search' and request['method'] == 'vmc' and request['x'] == x
            assert audit['fixture_id'] == train[anchor]['id'] and audit['split'] == 'train'
            assert audit['method'] == 'vmc'
            model_hash = digest((root/relative/'rollout.mjb').read_bytes())
            inputs[relative+'/rollout.mjb'] = model_hash
            assert model_hash == audit['model_sha256'] == audit['files_sha256']['rollout.mjb']
            assert inputs[relative+'/request.json'] == audit['files_sha256']['request.json']
            # Check matched baseline compiled models using completed metadata;
            # these rows are evidence of pairing, never optimizer observations.
            paired = {}
            for method in ('admittance', 'impedance'):
                peer = f'search/passive_corner/{method}/c{index:02d}/{anchor}/audit.json'
                peer_audit = read(peer)
                assert peer_audit['fixture_id'] == audit['fixture_id']
                assert peer_audit['split'] == 'train'
                assert peer_audit['model_sha256'] == model_hash
                paired[method] = dict(audit_sha256=inputs[peer], model_sha256=peer_audit['model_sha256'])
            if anchor in models:
                assert models[anchor] == model_hash
            models[anchor] = model_hash
            # Failure-label proxy, not a continuous physical residual.
            labels = len(audit['failure_reasons'])
            assert audit['eligible'] == (labels == 0)
            constraint = -1. if labels == 0 else float(labels)
            assert constraint == audit['constraint']
            score = audit['rmse_m']/.05+.3*audit['torque_ratio']+.1*audit['completion_proxy_retreat_s']/55.
            assert abs(score-audit['score']) < 1e-12
            rows.append(dict(anchor=anchor, fixture_id=audit['fixture_id'], split=audit['split'],
                eligible=audit['eligible'], failures=audit['failure_reasons'],
                constraint=constraint, score=score, audit_sha256=inputs[relative+'/audit.json'],
                model_sha256=model_hash, paired_baseline_models=paired))
        successful = sum(row['eligible'] for row in rows)
        failures = len(rows)-successful
        severity = max(max(row['constraint'], 0.) for row in rows)
        proxy = -1. if failures == 0 else failures+.25*severity/(1.+severity)
        summary = dict(x=x, index=index, eligible_count=successful, total=len(rows),
            failed_anchor_count=failures, violation_proxy=severity, constraint=proxy,
            constraint_semantics='failed_anchor_count + 0.25*max_failure_label_count/(1+max_failure_label_count); all feasible=-1; categorical proxy, not physical violation magnitude',
            score=float(np.mean([row['score'] for row in rows])))
        for key, value in summary.items():
            if isinstance(value, float):
                assert abs(value-prefix[index][key]) < 1e-12, key
            else:
                assert value == prefix[index][key], key
        aggregate.append(summary)
        evidence[str(index)] = rows
    source_path = root/'source/tools/teacher_bank_design_20260930.py'
    source_bytes = source_path.read_bytes()
    campaign_hash = digest((root/'source/tools/teacher_bank_campaign_20260930.py').read_bytes())
    assert digest(source_bytes) == plan['sources']['tools/teacher_bank_design_20260930.py']
    assert campaign_hash == plan['sources']['tools/teacher_bank_campaign_20260930.py']
    spec = importlib.util.spec_from_file_location('frozen_bo_design', source_path)
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    category_index, candidate_index = design.CATEGORIES.index('passive_corner'), 3
    seed = design.SEED+category_index*100+candidate_index
    replayed = design.propose(aggregate, seed)
    delta = float(np.max(np.abs(np.asarray(replayed)-decision['x'])))
    unchanged = digest((root/decision_path).read_bytes()) == inputs[decision_path]
    assert unchanged, 'Immutable decision changed during audit'
    result = dict(scope='First actual v10 BO decision only; candidate c03 outcome not evaluated',
        script_sha256=digest(Path(__file__).read_bytes()),
        runtime=dict(python=sys.version, numpy=np.__version__, scipy=scipy.__version__),
        source_sha256=dict(design=digest(source_bytes), campaign=campaign_hash),
        frozen_optimizer_and_campaign_match_plan=True,
        read_bytes_sha256=inputs, history_snapshot_entry_count=len(history_all),
        optimizer_history_prefix=prefix, independently_aggregated_history=aggregate,
        training_evidence=evidence, model_hash_equal_across_candidates_and_methods=True,
        no_validation_inputs=dict(optimizer_only_receives='Three VMC training-anchor candidate summaries and deterministic seed',
            anchors=plan['anchor_indices'], validation_trajectories_read=False,
            note='fixtures.json contains split definitions; only training fixtures select optimizer rows. Baseline audit metadata checked solely for paired model identity.'),
        decision=decision, same_implementation_replay=dict(seed=seed,
            formula='SEED + category_index*100 + candidate_index', category_index=category_index,
            candidate_index=candidate_index, x=replayed, maximum_abs_difference=delta,
            exact_match=replayed == decision['x'],
            caveat='Frozen propose/GP implementation reused, not independent optimizer verification; numerical library mismatch is reported, never corrected'),
        optimizer_regime='feasibility LCB search because zero whole-anchor candidates have constraint<=0',
        constraint_semantics='Discrete failed-anchor count plus bounded failure-label tie-break; not continuous physical safety margins',
        frozen_propose_source=inspect.getsource(design.propose), original_decision_unchanged=unchanged)
    output.mkdir(parents=True)
    for name, data in snapshots.items():
        destination = output/(name.replace('/', '__')+'.snapshot')
        destination.write_bytes(data)
    destination = output/'review.json'
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(destination), sha256=digest(destination.read_bytes()),
                         replay_max_abs=delta, seed=seed)))


if __name__ == '__main__':
    main()
