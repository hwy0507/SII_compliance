"""Complete a 2x2 teacher readout control on real training-scene identities.

The (0.5, True) reference is the completed regression diagnostic. The other
three settings are run in all three identical scenes at the common 0.32
action scale. No office/test trajectory is used for fitting or selection.
"""
import argparse
import copy
from pathlib import Path

from collect_special_scene_actions_20261028 import read, sha, write
from diagnose_special_scene_regression_20261028 import ROOT, now, run


def prepare(root, reference):
    if root.exists():
        raise FileExistsError(root)
    state = read(reference/'execution.json')
    original = read(reference/'REGISTRATION.json')
    assert state['status'] == 'complete_pending_review'
    assert len(state['episodes']) == original['maximum_episodes'] == 10
    assert state['registration_sha256'] == sha(reference/'REGISTRATION.json')
    config = read(reference/'teacher_new.json')
    assert config['velocity_weight'] == .5 and config['pair_average'] is True
    old = read(reference/'teacher_historical.json')
    reduced = {k: v for k, v in config.items() if k not in ('velocity_weight', 'pair_average')}
    assert reduced == old, 'Other teacher changes require a new design'
    # Require and bind the complete controls, including failed students.
    for receipt in state['episodes']:
        folder = reference/receipt['id']
        if 'audit' in receipt:
            assert sha(folder/'AUDIT.json') == receipt['audit_sha256']
        else:
            scene = receipt['qualification']['scene']
            assert sha(folder/scene/'DEMONSTRATION_QUALIFICATION.json') == receipt['qualification_sha256']
    for scene in ('rod', 'ball', 'corner'):
        receipt = next(r for r in state['episodes'] if r['id'] == scene+'_teacher')
        assert receipt['qualification']['status'] == 'qualified'
    root.mkdir(parents=True)
    cases = []
    configs = {}
    for velocity, average in ((1., False), (.5, False), (1., True)):
        label = f'v{velocity:g}_avg{int(average)}'
        path = root/(label+'.json')
        write(path, dict(reduced, velocity_weight=velocity, pair_average=average))
        configs[str(path)] = sha(path)
        for scene in ('rod', 'ball', 'corner'):
            case = copy.deepcopy(next(c for c in original['cases'] if c['id'] == scene+'_teacher'))
            case.update(id=label+'_'+scene, config=str(path), model=None)
            cases.append(case)
    reg = copy.deepcopy(original)
    reg.update(schema='sii-special-teacher-factor-control-v1', registered_utc=now(),
               reference=str(reference), reference_execution_sha256=sha(reference/'execution.json'),
               reference_registration_sha256=sha(reference/'REGISTRATION.json'),
               cases=cases, config_sha256=configs, maximum_episodes=9,
               factors=dict(velocity_weight=[.5, 1.], pair_average=[False, True]),
               interpretation='Three new teacher settings plus the completed (0.5,True) reference; identical real training-scene identities and common action scale. Separate paired velocity/averaging contrasts. No test-based selection, no fitting.',
               next_step='Review all nine receipts including failures; preserve rod pass-before-withdrawal and all three scene qualifications. Choose development settings only using these real training scenes, then register complete recollection and fair training.')
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    write(root/'REGISTRATION.json', reg)
    print(root, sha(root/'REGISTRATION.json'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--reference', type=Path)
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    if a.run:
        run(a.root.resolve())
    else:
        prepare(a.root.resolve(), a.reference.resolve())
