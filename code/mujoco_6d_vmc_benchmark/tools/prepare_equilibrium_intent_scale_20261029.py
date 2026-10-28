"""One finite intent normalization control after full equilibrium review.

Change the existing intention velocity scale from .015 to .03 m/s. This
reduces the residual lift equilibrium for small nominal path commands while
preserving full-intent behavior above .03 m/s. The same parameter already
governs the existing recovery release term; that coupled effect is explicit.
No physics/filter/gate/input changes and no new labels or fitting.
"""
import argparse
import copy
import shutil
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run
from intent_equilibrium_teacher_20261029 import IntentEquilibriumTeacher
from review_special_teacher_midpoint_20261028 import inactive


def prepare(root):
    assert not root.exists()
    parent = ROOT/'outputs/special_intent_equilibrium_20261029_v1'
    inactive('sii-special-intent-equilibrium-v1-20261029.service')
    reg, state, review = [read(parent/name) for name in ('REGISTRATION.json', 'execution.json', 'REVIEW.json')]
    assert state['status'] == 'complete_pending_review' and len(state['episodes']) == 6
    assert state['registration_sha256'] == sha(parent/'REGISTRATION.json')
    assert review['execution_sha256'] == sha(parent/'execution.json') and not review['all_six_qualified']
    before = read(Path(reg['cases'][0]['config']))
    assert before['recovery'].get('intent_velocity_mps', .015) == .015
    config = copy.deepcopy(before)
    config['recovery']['intent_velocity_mps'] = .03
    a, b = IntentEquilibriumTeacher(before), IntentEquilibriumTeacher(config)
    # Above both intent normalizations, every dynamic update/action must agree.
    obs = np.zeros(48)
    obs[45], obs[14], obs[26], obs[39] = 1., .06, .06, -8.
    for _ in range(200):
        a.observe(obs); b.observe(obs)
        np.testing.assert_array_equal(a.act(obs[39:45]), b.act(obs[39:45]))
        assert a.recovery_memory == b.recovery_memory
    folder = parent/'equilibrium_office000'
    audit = read(folder/'AUDIT.json')
    assert sha(folder/'rollout.npz') == audit['trace_sha256']
    with np.load(folder/'rollout.npz', allow_pickle=False) as trace:
        tail = trace['observation'][-250:]
        path = tail[:,45:47]
        norm = np.linalg.norm(path, axis=1)
        desired = np.sum(tail[:,14:16]*path/np.maximum(norm[:,None], 1e-12), axis=1)
        factors = [np.clip(desired/scale, 0, 1)*np.minimum(1, norm)**2 for scale in (.015, .03)]
        diagnosis = dict(trace_sha256=audit['trace_sha256'], last250_nominal_path_speed_quantiles_mps=np.quantile(desired,[0,.5,.9,1]).tolist(),
            last250_old_intent_mean=float(factors[0].mean()), last250_new_intent_same_history_mean=float(factors[1].mean()),
            interpretation='Small near-goal commands still produce nonzero lift offset. Doubling normalization is a single-field hypothesis; it also changes original memory decay. Counterfactual factors are not new physical trajectories or fitting labels.')
    root.mkdir(parents=True)
    write(root/'DIAGNOSIS.json', diagnosis)
    teacher = root/'teacher_intent030.json'
    write(teacher, config)
    source = root/'source'
    shutil.copytree(parent/'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    originals = {str(p.relative_to(parent/'source')):sha(p) for p in (parent/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    assert all(sha(source/name) == digest for name, digest in originals.items())
    write(root/'SOURCE_COPY_REVIEW.json', dict(files=originals, original_source=str(parent/'source'), full_intent_exact_steps=200))
    cases = copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher), id='intent030_'+case.get('identity', 'office000'))
        if case['kind'] == 'office':
            case['command'][1] = str(source/'tools/intent_equilibrium_office_driver_20261029.py')
    successor = copy.deepcopy(reg)
    for key in ('actor_checks_sha256', 'source_copy_review_sha256'):
        successor.pop(key)
    successor.update(schema='sii-equilibrium-intent030-finite-control-v1', registered_utc=now(),
        service='sii-special-equilibrium-intent030-v1-20261029.service', cases=cases,
        config_sha256={str(teacher):sha(teacher)}, parent_review_sha256=sha(parent/'REVIEW.json'),
        parent_execution_sha256=sha(parent/'execution.json'), interpretation=__doc__,
        changed_parameter=dict(name='recovery.intent_velocity_mps', before=.015, after=.03),
        source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        diagnosis_sha256=sha(root/'DIAGNOSIS.json'),
        selection_rule='One candidate, same six controls. All training qualifications and office Task/Strict required before new30; all failures retained, no automatic collection/fitting.')
    successor['source_sha256'] = {name:sha(ROOT/name) for name in reg['source_sha256'] if not name.startswith('outputs/')}
    successor['source_sha256']['tools/'+Path(__file__).name] = sha(Path(__file__))
    successor['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'})
    write(root/'REGISTRATION.json', successor)
    print(root, sha(root/'REGISTRATION.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    (run if args.run else prepare)(args.root.resolve())
