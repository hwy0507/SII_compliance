"""Check development-only model selection after the final model lock exists.

No simulation, learning, model replacement or final outcome inspection. Final
condition identities are read only after validating the complete frozen lock.
"""
import argparse
from datetime import datetime
from pathlib import Path

import numpy as np

from evaluate_baseline_repair_20261008 import validate_candidate, BASELINES
from office_v7_uniform24_20261008 import read, write, sha, now, FAMILIES


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root = a.root.resolve()
    assert not a.output.exists()
    lock = read(root/'FINAL_MODEL_LOCK.json')
    assert lock['status'] == 'frozen'
    assert lock['protocol_sha256'] == sha(root/'PROTOCOL.json')
    assert lock['models_sha256'] == sha(root/'FINAL_MODELS.json')
    for name, digest in lock['source_hashes'].items():
        assert sha(Path(lock['source'])/name) == digest
    final = read(root/'FINAL_MODELS.json')['candidates']
    assert len(final) == 16 and {c['family'] for c in final} == set(FAMILIES)
    for candidate in final:
        validate_candidate(candidate)
    references = read(root/'REFERENCE_MODELS.json')['candidates']
    for candidate in final:
        if candidate['family'] not in BASELINES:
            assert candidate == next(c for c in references if c['family'] == candidate['family'])
    dev = root/'rl_development'
    state = read(dev/'execution.json')
    assert state['status'] == 'complete' and state['completed'] == state['expected'] == 80
    selection = read(root/'RL_SELECTION.json')
    timestamps = [state['ended_utc'], selection['selected_utc'], lock['frozen_utc'],
                  read(root/'final_evaluation/execution.json')['started_utc']]
    assert sorted(map(datetime.fromisoformat, timestamps)) == list(map(datetime.fromisoformat, timestamps))
    dev_ids = {c['id'] for c in read(dev/'CONDITIONS.json')['conditions']}
    assert len(dev_ids) == 8
    summaries = []
    for family, ranked in selection['ranked'].items():
        assert len(ranked) == 2
        reproduced = []
        for entry in ranked:
            c = entry['candidate']
            rows = []
            distances = []
            ids = set()
            for name, digest in entry['receipts'].items():
                receipt = dev/'episodes'/(name+'.execution.json')
                assert sha(receipt) == digest
                row = read(receipt)
                assert row['status'] == 'complete' and row['candidate'] == c['name']
                assert row['family'] == family and row['phase'] == 'development'
                ids.add(row['condition_id'])
                audit = read(dev/'episodes'/name/'AUDIT.json')
                assert sha(dev/'episodes'/name/'AUDIT.json') == row['audit_sha256']
                assert audit == row['audit']
                summary = read(dev/'episodes'/name/'rollout.json')
                np.testing.assert_array_equal(audit['object_final_position'], summary['object_final_position'])
                distances.append(float(np.linalg.norm(np.asarray(audit['object_final_position']) - summary['placement_destination'])))
                rows.append(audit)
            assert len(rows) == 8 and ids == dev_ids
            score = [sum(r['strict_success'] for r in rows), sum(r['task_success'] for r in rows),
                     sum(r['full_horizon'] for r in rows), -max(distances), -sum(distances),
                     sum(max(map(int, r.get('stages', {})), default=0) for r in rows),
                     -max(r['penetration_mm'] for r in rows), -sum(r['rmse_mm'] for r in rows),
                     -sum(r['peak_torque_nm'] for r in rows)]
            np.testing.assert_allclose(score, entry['score'], rtol=0, atol=1e-10)
            reproduced.append((score, c['name']))
            summaries.append(dict(family=family, seed=c['seed'], score=score,
                                  selected=c['name'] == ranked[0]['candidate']['name']))
        assert reproduced == sorted(reproduced, reverse=True)
        assert next(c['name'] for c in final if c['family'] == family) == ranked[0]['candidate']['name']
    protocol = read(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']
    assert sha(root/'sealed/HELDOUT.json') == protocol['sealed_condition_sha256']
    known = read(root/'CONDITIONS.json')['conditions']
    held = read(root/'sealed/HELDOUT.json')['conditions']
    assert len(held) == 24 and all(c['role'] == 'final' for c in held)
    assert not ({c['id'] for c in known} & {c['id'] for c in held})
    import json
    assert not ({json.dumps(c['overrides'], sort_keys=True) for c in known} &
                {json.dumps(c['overrides'], sort_keys=True) for c in held})
    write(a.output, dict(status='passed', created_utc=now(), source_sha256=sha(__file__),
        model_lock_sha256=sha(root/'FINAL_MODEL_LOCK.json'), final_models_sha256=sha(root/'FINAL_MODELS.json'),
        development_execution_sha256=sha(dev/'execution.json'), selection_sha256=sha(root/'RL_SELECTION.json'),
        timeline=timestamps, model_count=16, development_episodes=80, final_conditions=24,
        condition_id_and_exact_override_sets_disjoint=True, unchanged_reference_models=True,
        checkpoint_and_source_hashes_verified=True, development_scores=summaries,
        scope='Reproduced registered development ranks and chronology; no final outcomes read. '
              'Disjoint exact conditions do not establish independent sampling or broad generalization.'))
    print('Passed: 16 model hashes, 80 development ranks, freeze chronology and condition separation', flush=True)


if __name__ == '__main__':
    main()
