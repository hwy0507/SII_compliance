"""Review original-recovery normalization controls; gate prospective recollection.

Separate version preserves the already archived intent-control reviewer.
"""
import argparse
import copy
import hashlib
from pathlib import Path
import tarfile

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from diagnose_special_scene_regression_20261028 import now
from review_special_teacher_midpoint_20261028 import inactive


def review(root):
    reg, state = read(root/'REGISTRATION.json'), read(root/'execution.json')
    variants = {
        'legacy_parameter_teacher_v1': ('sii-special-teacher-legacy-units-v1-20261029.service',
            'optimize_tool_contact_20261002.py', 'legacy_teacher_office_driver_20261029.py'),
        'intent_scaled_recovery_v1': ('sii-special-intent-recovery-v1-20261029.service',
            'intent_recovery_teacher_20261029.py', 'intent_teacher_office_driver_20261029.py'),
        'intent_scaled_equilibrium_v1': ('sii-special-intent-equilibrium-v1-20261029.service',
            'intent_equilibrium_teacher_20261029.py', 'intent_equilibrium_office_driver_20261029.py'),
    }
    service, extension, driver = variants[reg['teacher_mechanism']]
    service = reg.get('service', service)
    inactive(service)
    assert state['status'] == 'complete_pending_review'
    assert state['registration_sha256'] == sha(root/'REGISTRATION.json')
    assert len(state['episodes']) == len(reg['cases']) == reg['maximum_episodes'] == 6
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    for name, digest in reg['config_sha256'].items():
        assert sha(Path(name)) == digest
    rows = []
    for case, row in zip(reg['cases'], state['episodes']):
        assert case['id'] == row['id'] and row['returncode'] == 0
        folder = root/case['id']
        result = dict(id=case['id'], kind=case['kind'])
        if case['kind'] == 'scene':
            folder /= case['scene']
            q = read(folder/'DEMONSTRATION_QUALIFICATION.json')
            assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == row['qualification_sha256']
            for name, digest in q['input_hashes'].items():
                assert sha(folder/name) == digest
            assert q['input_hashes']['scene.mjb'] == case['expected_model_sha256']
            result.update(status=q['status'], task=q['task_success'], safety=q['safety_valid'],
                          contact=q['scene_contact_valid'], qualification_sha256=row['qualification_sha256'])
            if case['scene'] == 'ball':
                with np.load(folder/'legacy.npz', allow_pickle=False) as trace:
                    result['tail_object_speed_max_mps'] = float(np.linalg.norm(np.diff(trace['object_position'][-10:], axis=0)/.04, axis=1).max())
                result['original_motion_threshold_mps'] = .02
            elif case['scene'] == 'rod':
                result['rod_audit'] = read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
        else:
            audit = read(folder/'AUDIT.json')
            assert sha(folder/'AUDIT.json') == row['audit_sha256']
            for name, key in [('rollout.npz', 'trace_sha256'), ('rollout.mjb', 'model_sha256'),
                              ('execution_chain.npz', 'chain_sha256'), ('rollout_metrics/substep_metrics.npz', 'metrics_sha256')]:
                assert sha(folder/name) == audit[key]
            assert audit['action_replay_max_abs'] == audit['common_filter_replay_max_abs'] == 0.
            assert audit['full_horizon']
            # Prove the actual worker archive contains the executed extension
            # and its driver, not merely files copied beside the evaluator.
            with tarfile.open(folder/'source_overlay.tar.gz') as archive:
                names = archive.getnames()
                for name in (extension, driver):
                    matches = [n for n in names if n.endswith('/'+name)]
                    assert len(matches) == 1
                    digest = hashlib.sha256(archive.extractfile(matches[0]).read()).hexdigest()
                    assert digest == sha(root/'source/tools'/name)
            with np.load(folder/'rollout.npz', allow_pickle=False) as trace, np.load(folder/'teacher_internal.npz', allow_pickle=False) as internal:
                obs = trace['observation'][-250:]
                result.update(last250_pose_error_mean=obs[:,20:26].mean(0).tolist(),
                              last250_recovery_memory_mean=float(internal['recovery_memory'][-250:].mean()),
                              last250_z_action_mean=float(internal['requested_action'][-250:,3].mean()))
            result.update(task=audit['task_success'], strict=audit['strict_success'], stage=audit['stage'],
                          audit_sha256=row['audit_sha256'], action_replay_max_abs=0., filter_replay_max_abs=0.)
        rows.append(result)
    qualified = all(r.get('status') == 'qualified' if r['kind'] == 'scene' else r['task'] and r['strict'] for r in rows)
    result = dict(reviewed_utc=now(), registration_sha256=sha(root/'REGISTRATION.json'),
                  execution_sha256=sha(root/'execution.json'), rows=rows,
                  all_six_qualified=qualified, selection_rule=reg['selection_rule'],
                  limitation='Finite teacher controls only. Office is inspected development regression. No student training, all30 qualification, or repaired108 claim.')
    path = root/'REVIEW.json'
    if path.exists():
        old = read(path)
        assert {k:v for k,v in old.items() if k!='reviewed_utc'} == {k:v for k,v in result.items() if k!='reviewed_utc'}
        return old
    write(path, result)
    return result


def recollect(root, output):
    result = review(root)
    assert result['all_six_qualified'], 'Finite teacher controls failed; no new collection or fitting'
    assert not output.exists()
    previous = ROOT/'outputs/special_scene_vmc_collection_20261028_v6'
    old = read(previous/'COLLECTION_PLAN.json')
    assert read(previous/'COLLECTION_PROGRESS.json')['status'] == 'finished_with_nonqualified_demonstrations'
    reg = read(root/'REGISTRATION.json')
    teacher = Path(reg['cases'][0]['config'])
    references = {}
    for scene in ('rod', 'ball', 'corner'):
        case = next(c for c in reg['cases'] if c.get('identity') == scene+'_00')
        folder = root/case['id']/scene
        references[scene] = dict(folder=str(folder), qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
    plan = copy.deepcopy(old)
    plan.update(registered_utc=now(), teacher_config=str(teacher), teacher_file_sha256=sha(teacher), teacher_config_sha256=sha(teacher),
                development_references=references,
                supersedes=dict(previous_plan_sha256=sha(previous/'COLLECTION_PLAN.json'), previous_progress_sha256=sha(previous/'COLLECTION_PROGRESS.json'),
                    teacher_control_review_sha256=sha(root/'REVIEW.json'),
                    rationale='Original v6 recovery, velocity weight1 and averaged input with matched teacher normalization. Same30 physical identities/seeds/split/gates; all prior failures retained. Inspected office regression disclosed and excluded from imitation labels.'))
    plan['source_sha256'] = {name:sha(ROOT/name) for name in old['source_sha256']}
    for name in ('intent_recovery_teacher_20261029.py', 'intent_equilibrium_teacher_20261029.py', Path(__file__).name):
        plan['source_sha256']['tools/'+name] = sha(ROOT/'tools'/name)
    for original, new in zip(old['episodes'], plan['episodes']):
        new['folder'] = str(output/new['id']/new['scene'])
        assert {k:v for k,v in original.items() if k!='folder'} == {k:v for k,v in new.items() if k!='folder'}
    output.mkdir(parents=True)
    write(output/'COLLECTION_PLAN.json', plan)
    validate(output/'COLLECTION_PLAN.json')
    print(output, sha(output/'COLLECTION_PLAN.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--collection-output', type=Path)
    args = parser.parse_args()
    if args.collection_output:
        recollect(args.root.resolve(), args.collection_output.resolve())
    else:
        result = review(args.root.resolve())
        print('all_six_qualified', result['all_six_qualified'])
        for row in result['rows']:
            print({k:v for k,v in row.items() if k not in ('rod_audit',)})
