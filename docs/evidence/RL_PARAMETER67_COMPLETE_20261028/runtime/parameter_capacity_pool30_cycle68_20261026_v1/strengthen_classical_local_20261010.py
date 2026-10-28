"""Local finite boundary search after positive controls and contact attribution.

Three families, center + eight factorial boundary candidates each, two shared
development conditions; best two per family complete remaining six identities.
54 screen +36 confirmation episodes maximum; no automatic test-set opening.
"""
import argparse
import itertools
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import classical_acceptance_20261010 as campaign


def candidates(priors):
    result = []
    axes = dict(vmc=(0,1,3), admittance=(0,6,4), impedance=(0,4,2))
    for method, indices in axes.items():
        prior = priors[method]
        center = list(prior['center'])
        vectors = [center]
        for corners in itertools.product((0,1), repeat=3):
            vector = center.copy()
            for index, boundary in zip(indices, corners):
                vector[index] = prior['bounds'][index][boundary]
            vectors.append(vector)
        for i, vector in enumerate(vectors):
            assert all(lo <= x <= hi for x, (lo,hi) in zip(vector, prior['bounds']))
            result.append(dict(name=f'{method}_boundary_{i:02d}', controller=method,
                               parameters=vector, is_historical_selected_center=i==0))
    return result


def prepare(args):
    campaign.prepare(SimpleNamespace(root=args.root, runtime=args.runtime,
        condition='repair_development_000', methods=['vmc','admittance','impedance'], fixtures=['frozen']))
    source = args.root/'source'
    import shutil
    shutil.copy2(__file__, source/'tools'/Path(__file__).name)
    reg = campaign.read(args.root/'REGISTRATION.json')
    conditions = [c for c in campaign.read(args.runtime/'history/CONDITIONS.json')['conditions']
                  if c['role'] == 'development']
    assert len(conditions) == 8 and len({c['id'] for c in conditions}) == 8
    priors = campaign.read(args.root/'parameter/PRIORS.json')['methods']
    choices = candidates(priors)
    reg.update(schema='classical-local-boundary-search-v1', source_hashes=campaign.hashes(source),
        registered_utc=campaign.now(), candidates=choices, conditions=conditions,
        screen_conditions=[c['id'] for c in conditions[:2]],
        confirmation_conditions=[c['id'] for c in conditions[2:]],
        candidate_design='Same 9/family: previous selected center + full 2^3 factorial at original bounds for horizontal stiffness, vertical stiffness/ratio and translational damping ratio/scale. Other coordinates remain center.',
        confirmation_rule='Best two/family by Strict, Task, full horizon, worst/sum actual payload XY target error, worst penetration, sum RMSE, sum peak torque. Complete other6 conditions; combine with screen2. No final access.',
        max_episodes=90, decision='Finite boundary sensitivity study, not proof of global optimum. Review 8-condition confirmation and contact mechanisms before any further search or final freeze.',
        prerequisites=dict(clear_root=str(args.acceptance_root), diagnostic_root=str(args.diagnostic_root)),
        controller_changes='None: exact repaired parameter_v2 laws and original bounds. New selected parameters remain explicit.',
        final_evaluation_started=False, final_test_reads=0)
    reg['jobs'] = [dict(name=c['name']+'__'+d['id'], fixture='frozen',
        controller=c['controller'], candidate=c['name'], parameters=c['parameters'], condition_id=d['id'])
        for d in conditions[:2] for c in choices]
    assert len(reg['jobs']) == 54
    campaign.write(args.root/'REGISTRATION.json', reg)
    print('FINAL_REGISTRATION', campaign.sha(args.root/'REGISTRATION.json'), flush=True)


def run(args):
    reg = campaign.read(args.root/'REGISTRATION.json')
    prereq = reg['prerequisites']
    clear_root = Path(prereq['clear_root'])
    clear = campaign.read(clear_root/'execution.json')
    assert clear['status'] == 'complete' and len(clear['completed']) == 4
    assert all(r['audit']['task_success'] and r['audit']['strict_success'] for r in clear['completed'])
    diag_root = Path(prereq['diagnostic_root'])
    state = dict(status='running', started_utc=campaign.now(), stage='contact_attribution',
                 registration_sha256=campaign.sha(args.root/'REGISTRATION.json'))
    receipt = args.root/'CHAIN_EXECUTION.json'
    campaign.write(receipt, state)
    try:
        previous = campaign.read(diag_root/'execution.json')
        if previous['status'] == 'prepared':
            command = [sys.executable, str(diag_root/'source/tools/classical_acceptance_20261010.py'),
                'run', '--root', str(diag_root), '--runtime', str(args.runtime)]
            subprocess.run(command, check=True)
        else:
            assert previous['status'] == 'complete', 'Preserve interrupted diagnostic, no automatic restart'
        done = campaign.read(diag_root/'execution.json')
        assert done['status'] == 'complete' and len(done['completed']) == 6
        state.update(stage='frozen_world_parameter_search',diagnostic_execution_sha256=campaign.sha(diag_root/'execution.json'))
        campaign.write(receipt, state)
        campaign.run(args)
        state.update(status=campaign.read(args.root/'execution.json')['status'],stage='closed_for_readiness_review')
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc))
        raise
    finally:
        state['ended_utc']=campaign.now()
        campaign.write(receipt,state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run'))
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--acceptance-root',type=Path)
    p.add_argument('--diagnostic-root',type=Path)
    a=p.parse_args()
    a.root=a.root.resolve();a.runtime=a.runtime.resolve()
    if a.mode=='prepare':
        assert a.acceptance_root is not None and a.diagnostic_root is not None
        a.acceptance_root=a.acceptance_root.resolve();a.diagnostic_root=a.diagnostic_root.resolve()
    (prepare if a.mode=='prepare' else run)(a)


if __name__=='__main__':main()
