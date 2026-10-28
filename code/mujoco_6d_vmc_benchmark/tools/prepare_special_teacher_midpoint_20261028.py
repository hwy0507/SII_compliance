"""Review the completed tail controls and register a finite training-only probe.

The two midpoint readouts interpolate the already observed 0.5/1.0 tradeoff.
Five training identities per candidate, fixed before execution; no validation
or office examples enter the probe or any student fit. Office evidence is
reported as previously inspected regression evidence, never an unseen test.
No automatic recollection, fitting, or model selection follows this probe.
"""
import argparse
import copy
from pathlib import Path
import subprocess

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run


def review_tail(tail):
    reg = read(tail/'REGISTRATION.json')
    state = read(tail/'execution.json')
    assert state['status'] == 'complete_pending_review'
    assert state['registration_sha256'] == sha(tail/'REGISTRATION.json')
    assert len(state['episodes']) == reg['maximum_episodes'] == 4
    status = subprocess.check_output(['systemctl', '--user', 'show',
        'sii-special-teacher-tail-repair-v2-20261028.service',
        '-p', 'MainPID', '-p', 'ActiveState'], text=True)
    assert dict(x.split('=', 1) for x in status.splitlines()) == dict(MainPID='0', ActiveState='inactive')
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    rows = []
    for case, row in zip(reg['cases'], state['episodes']):
        assert case['id'] == row['id'] and row['returncode'] == 0
        folder = tail/case['id']
        if case['kind'] == 'scene':
            folder /= case['scene']
            q = read(folder/'DEMONSTRATION_QUALIFICATION.json')
            assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == row['qualification_sha256']
            for name, digest in q['input_hashes'].items():
                assert sha(folder/name) == digest, name
            assert q['input_hashes']['scene.mjb'] == case['expected_model_sha256']
            with np.load(folder/'legacy.npz', allow_pickle=False) as z:
                speed = float(np.max(np.linalg.norm(np.diff(z['object_position'][-10:], axis=0)/.04, axis=1)))
            rows.append(dict(id=case['id'], task=q['task_success'], qualified=q['status'],
                             tail_object_speed_max_mps=speed, original_threshold_mps=.02,
                             qualification_sha256=row['qualification_sha256'],
                             legacy_npz_sha256=sha(folder/'legacy.npz')))
        else:
            a = read(folder/'AUDIT.json')
            assert sha(folder/'AUDIT.json') == row['audit_sha256']
            for name, key in [('rollout.npz', 'trace_sha256'), ('rollout.mjb', 'model_sha256'),
                              ('execution_chain.npz', 'chain_sha256'),
                              ('rollout_metrics/substep_metrics.npz', 'metrics_sha256')]:
                assert sha(folder/name) == a[key], name
            assert a['action_replay_max_abs'] == a['common_filter_replay_max_abs'] == 0
            assert a['full_horizon'] and abs(a['physical_seconds']-55.) < 1e-7
            rows.append(dict(id=case['id'], task=a['task_success'], strict=a['strict_success'],
                             stage=a['stage'], rmse_mm=a['rmse_mm'], peak_torque_nm=a['peak_torque_nm'],
                             audit_sha256=row['audit_sha256']))
    # Compare teacher stability on failed TRAIN identities only. The complete
    # collection review retains validation failures without tuning on them.
    v6 = Path(reg['collection'])
    plan = read(v6/'COLLECTION_PLAN.json')
    v5 = ROOT/'outputs/special_scene_vmc_collection_20261028_v5'
    tail_comparison = []
    for identity in ('ball_01', 'ball_04'):
        assert next(e for e in plan['episodes'] if e['id'] == identity)['split'] == 'train'
        result = dict(id=identity)
        for label, folder in [('v5', v5/identity/'ball'), ('v6', v6/identity/'ball')]:
            with np.load(folder/'legacy.npz', allow_pickle=False) as z:
                result[label] = dict(
                    tail_object_speed_max_mps=float(np.max(np.linalg.norm(np.diff(z['object_position'][-10:], axis=0)/.04, axis=1))),
                    last4s_action_std=np.std(z['action'][-100:], axis=0).tolist(),
                    last4s_force_std=np.std(z['force'][-100:], axis=0).tolist(),
                    legacy_npz_sha256=sha(folder/'legacy.npz'))
        tail_comparison.append(result)
    return dict(schema='sii-teacher-tail-complete-review-v1', reviewed_utc=now(),
                registration_sha256=sha(tail/'REGISTRATION.json'),
                execution_sha256=sha(tail/'execution.json'), rows=rows,
                train_tail_comparison=tail_comparison,
                interpretation='Teacher velocity readout affects both tail stability and office completion. These are completed controlled observations, not proof of stability for all conditions or any student success.')


def prepare(root, tail):
    if root.exists():
        raise FileExistsError(root)
    review = review_tail(tail)
    previous = read(tail/'REGISTRATION.json')
    collection = Path(previous['collection'])
    plan = read(collection/'COLLECTION_PLAN.json')
    factors = ROOT/'outputs/special_teacher_factor_controls_20261028_v1'
    base_config = read(factors/'v1_avg1.json')
    assert base_config['velocity_weight'] == 1. and base_config['pair_average'] is True
    identities = ('rod_00', 'ball_00', 'ball_01', 'ball_04', 'corner_00')
    cases = []
    root.mkdir(parents=True)
    write(root/'PARENT_REVIEW.json', review)
    for average in (False, True):
        label = 'v075_avg'+str(int(average))
        config = copy.deepcopy(base_config)
        config.update(velocity_weight=.75, pair_average=average)
        path = root/(label+'.json')
        write(path, config)
        for identity in identities:
            entry = next(e for e in plan['episodes'] if e['id'] == identity)
            assert entry['split'] == 'train'
            folder = Path(entry['folder'])
            cases.append(dict(id=label+'_'+identity, kind='scene', scene=entry['scene'],
                identity=identity, seed=entry['seed'], scene_parameters=entry['scene_parameters'],
                expected_model_sha256=read(folder/'execution.json')['model_sha256'],
                baseline=str(folder), baseline_execution_sha256=sha(folder/'execution.json'),
                config=str(path), model=None))
    registration = copy.deepcopy(previous)
    registration.update(schema='sii-teacher-midpoint-training-probe-v1', registered_utc=now(),
        parent=str(tail), parent_review_sha256=sha(root/'PARENT_REVIEW.json'),
        parent_execution_sha256=sha(tail/'execution.json'), maximum_episodes=10,
        cases=cases, config_sha256={c['config']:sha(Path(c['config'])) for c in cases},
        selection_rule='Both candidates complete all five training identities. Eligible only when all five qualify under unchanged task/contact/safety and rod pass-before-withdrawal gates; fixed priority v075_avg0 then v075_avg1. If neither eligible, diagnose, do not relabel or launch a full collection.',
        interpretation=__doc__,
        next_step='Review all ten receipts including failures; chosen training-eligible candidate needs a separate office regression check and complete new30 collection before any fitting. No automatic dispatch.')
    registration['source_sha256'] = {name:sha(ROOT/name) for name in previous['source_sha256']}
    registration['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    write(root/'REGISTRATION.json', registration)
    print(root, sha(root/'REGISTRATION.json'), len(cases))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--tail', type=Path)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.run:
        run(args.root.resolve())
    else:
        prepare(args.root.resolve(), args.tail.resolve())
