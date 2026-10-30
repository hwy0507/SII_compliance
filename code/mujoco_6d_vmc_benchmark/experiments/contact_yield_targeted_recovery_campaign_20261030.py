"""Probe current MLP rod failure states with bounded VMC teacher suffixes."""
import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT/'experiments/contact_yield_recovery_campaign_20261030.py'
PARENT = ROOT/'outputs/contact_yield_recovery_student_development_20261030_v1'
TARGET = ROOT/'outputs/contact_yield_targeted_recovery_20261030_v1'
FINAL = ROOT/'outputs/contact_yield_final108_handoff_20261030_v1'
FIT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v3'
FIT_UNIT = 'sii-contact-yield-recovery-fit-v3-20261030.service'
DIAG_UNIT = 'sii-contact-yield-recovery-student-handoff-v1-20261030.service'
BASE_DIAG_UNIT = 'sii-contact-yield-student-diagnosis-handoff-20261030.service'
FINAL_UNIT = 'sii-contact-yield-final108-handoff-20261030.service'
PLAN = (
    ('rod_mlp01_post_yield_5p2s', 'rod', 'mlp_scratch', 2026102801, 130),
    ('rod_mlp01_late_yield_7s', 'rod', 'mlp_scratch', 2026102801, 175),
    ('rod_mlp03_prepenetration_4p48s', 'rod', 'mlp_scratch', 2026102803, 112),
    ('rod_mlp03_prepenetration_4p60s', 'rod', 'mlp_scratch', 2026102803, 115),
)

sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_special_scene_actions_20261028 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import properties

spec = importlib.util.spec_from_file_location('contact_yield_recovery_base_campaign', BASE_PATH)
campaign = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = campaign
spec.loader.exec_module(campaign)
campaign.PARENT = PARENT
campaign.FINAL = FINAL
campaign.PLAN = tuple((name, scene, family, steps) for name, scene, family, seed, steps in PLAN)
campaign.UNITS = (FIT_UNIT, DIAG_UNIT, BASE_DIAG_UNIT, FINAL_UNIT)


def prerequisites():
    assert all(properties(unit)['ActiveState'] == 'inactive' and
               properties(unit)['MainPID'] == '0' for unit in campaign.UNITS)
    parent = read(PARENT/'execution.json')
    report = read(PARENT/'REVIEW.json')
    assert parent['status'] == 'complete_development_diagnosis_pending_review'
    assert len(parent['rows']) == 27
    assert report['status'] == 'verified_fixed27_development_diagnosis'
    assert report['execution_sha256'] == sha(PARENT/'execution.json')
    assert report['registration_sha256'] == sha(PARENT/'REGISTRATION.json')
    expected_failures = {
        'rod_00__special_mlp_scratch_s2026102801',
        'rod_00__special_mlp_scratch_s2026102803',
    }
    assert set(report['failed_ids']) == expected_failures
    assert report['no_model_reselection'] and report['no_final_test_performed']
    final = read(FINAL/'execution.json')
    assert final['status'] == 'development_not_qualified_no_final_dispatch'
    assert final['dispatch_attempted'] is False
    assert not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    fit = read(FIT/'execution.json')
    lock = read(FIT/'MODEL_LOCK.json')
    assert fit['status'] == 'complete' and lock['status'] == 'frozen'
    assert lock['training_data_sha256'] == fit['dataset_sha256']
    return read(PARENT/'REGISTRATION.json')


def source_manifest():
    paths = [Path(__file__).resolve(), BASE_PATH.resolve(), campaign.WORKER.resolve(),
             campaign.AUDITOR.resolve()]
    paths += [p for folder in ('scripts', 'tools') for p in (ROOT/folder).glob('*.py')]
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))}


def prepare(root):
    assert not root.exists() and root == TARGET
    parent = prerequisites()
    cases = []
    for identity, scene, family, seed, steps in PLAN:
        source = next(case for case in parent['cases']
                      if case['condition']['scene'] == scene
                      and case['model']['family'] == family
                      and case['model']['seed'] == seed)
        cases.append(dict(id=identity, scene=scene, student_steps=steps,
                          model=source['model'], condition=source['condition'],
                          teacher_reference=source['teacher_reference']))
    sources = source_manifest()
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', dict(
        schema='contact-yield-targeted-recovery-development-v1',
        registered_utc=campaign.now(), cases=cases, maximum_episodes=len(cases),
        source_sha256=sources,
        parent_files={name: sha(PARENT/name) for name in
                      ('REGISTRATION.json', 'execution.json', 'REVIEW.json')},
        final_execution_sha256=sha(FINAL/'execution.json'),
        teacher_config=parent['teacher_config'],
        teacher_config_sha256=parent['teacher_config_sha256'],
        python=str(Path(sys.executable).resolve()),
        resources=dict(cpu=6, simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0),
        purpose=('Test whether the unchanged VMC teacher safely completes the current '
                 'MLP01 post-yield state and takes over before the measured MLP03 '
                 '0.2mm penetration onset. Only independently qualified executed '
                 'teacher suffixes may enter a later shared-data refit. No gate, '
                 'physics, actor, filter, executor, dt, model selection, or test change.')))


def check(reg):
    parent = prerequisites()
    assert reg['schema'] == 'contact-yield-targeted-recovery-development-v1'
    assert reg['maximum_episodes'] == len(PLAN) == len(reg['cases'])
    assert reg['source_sha256'] == source_manifest()
    assert reg['parent_files'] == {name: sha(PARENT/name) for name in
                                   ('REGISTRATION.json', 'execution.json', 'REVIEW.json')}
    assert reg['final_execution_sha256'] == sha(FINAL/'execution.json')
    assert reg['teacher_config'] == parent['teacher_config']
    assert sha(Path(reg['teacher_config'])) == reg['teacher_config_sha256']
    for spec, case in zip(PLAN, reg['cases']):
        name, scene, family, seed, steps = spec
        assert (case['id'], case['scene'], case['model']['family'],
                case['model']['seed'], case['student_steps']) == (
                    name, scene, family, seed, steps)
        for field in ('checkpoint', 'metadata'):
            assert sha(Path(case['model'][field])) == case['model'][field+'_sha256']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, default=TARGET)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.mode == 'prepare':
        prepare(root)
    else:
        reg = read(root/'REGISTRATION.json')
        check(reg)
        campaign.prerequisites = prerequisites
        campaign.check = check
        campaign.run(root)


if __name__ == '__main__':
    main()
