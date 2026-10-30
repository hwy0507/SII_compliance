"""Bind four bounded teacher-handoff probes to current v7 MLP rod failures."""
import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/contact_yield_recovery_campaign_20261030.py'
PARENT = ROOT/'outputs/contact_yield_recovery_student_development_20261030_v7'
FIT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v7'
FINAL = ROOT/'outputs/contact_yield_final108_handoff_20261030_v1'
TARGET = ROOT/'outputs/contact_yield_v7_mlp_rod_handoff_20261030_v1'
PLAN = (
    ('v7_rod_mlp02_handoff_4p48s', 'rod', 'mlp_scratch', 2026102802, 112),
    ('v7_rod_mlp02_handoff_4p60s', 'rod', 'mlp_scratch', 2026102802, 115),
    ('v7_rod_mlp03_handoff_4p48s', 'rod', 'mlp_scratch', 2026102803, 112),
    ('v7_rod_mlp03_handoff_4p60s', 'rod', 'mlp_scratch', 2026102803, 115),
)

sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_special_scene_actions_20261028 import read, sha, write

spec = importlib.util.spec_from_file_location('contact_yield_recovery_campaign', BASE)
campaign = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = campaign
spec.loader.exec_module(campaign)
campaign.PARENT = PARENT
campaign.FINAL = FINAL
campaign.PLAN = PLAN
campaign.UNITS = (
    'sii-contact-yield-scrape-collection-20261030.service',
    'sii-contact-yield-scrape-training-handoff-20261030.service',
    'sii-contact-yield-student-diagnosis-handoff-20261030.service',
    'sii-contact-yield-final108-handoff-20261030.service',
    'sii-contact-yield-recovery-student-handoff-v1-20261030.service',
    'sii-contact-yield-v6-mlp-rod-refit-v3-20261030.scope',
    'sii-contact-yield-recovery-v7-fixed27-v2-20261030.scope',
)


def prerequisites():
    for unit in campaign.UNITS:
        state = campaign.properties(unit)
        assert state['ActiveState'] == 'inactive' and state.get('MainPID', '0') == '0'
    state = read(PARENT/'execution.json')
    report = read(PARENT/'REVIEW.json')
    assert state['status'] == 'complete_development_diagnosis_pending_review'
    assert len(state['rows']) == 27
    assert report['status'] == 'verified_fixed27_development_diagnosis'
    assert report['registration_sha256'] == sha(PARENT/'REGISTRATION.json')
    assert report['execution_sha256'] == sha(PARENT/'execution.json')
    assert set(report['failed_ids']) == {
        'rod_00__special_mlp_scratch_s2026102802',
        'rod_00__special_mlp_scratch_s2026102803',
    }
    assert report['no_model_reselection'] and report['no_final_test_performed']
    fit = read(FIT/'execution.json')
    lock = read(FIT/'MODEL_LOCK.json')
    audit = read(FIT/'FIT_AUDIT.json')
    assert fit['status'] == 'complete' and lock['status'] == 'frozen'
    assert audit['status'] == 'passed' and len(audit['candidate_jobs']) == 75
    assert len(audit['frozen_actor_replays']) == 9
    assert lock['training_data_sha256'] == sha(FIT/'data/training_data.npz')
    assert fit['model_lock_sha256'] == sha(FIT/'MODEL_LOCK.json')
    final = read(FINAL/'execution.json')
    assert final['status'] == 'development_not_qualified_no_final_dispatch'
    assert final['dispatch_attempted'] is False
    assert not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    return read(PARENT/'REGISTRATION.json')


def source_manifest():
    paths = [Path(__file__).resolve(), BASE.resolve(), campaign.WORKER.resolve(),
             campaign.AUDITOR.resolve()]
    paths += [p for folder in ('scripts', 'tools')
              for p in (ROOT/folder).glob('*.py')]
    return {str(path.relative_to(ROOT)): sha(path)
            for path in sorted(set(paths))}


campaign.prerequisites = prerequisites
campaign.source_manifest = source_manifest
_base_check = campaign.check


def check(reg):
    prerequisites()
    assert reg['schema'] == 'sii-contact-yield-v7-mlp-rod-handoff-v1'
    assert reg['maximum_episodes'] == len(PLAN)
    assert [(c['id'], c['scene'], c['model']['family'],
             c['model']['seed'], c['student_steps']) for c in reg['cases']] == list(PLAN)
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    for name, digest in reg['parent_files'].items():
        assert sha(PARENT/name) == digest, name
    assert sha(FINAL/'execution.json') == reg['final_execution_sha256']
    assert sha(Path(reg['teacher_config'])) == reg['teacher_config_sha256']
    assert reg['python'] == sys.executable
    for case in reg['cases']:
        expected = next(c for c in read(PARENT/'REGISTRATION.json')['cases']
                        if c['condition']['scene'] == case['scene']
                        and c['model']['family'] == case['model']['family']
                        and c['model']['seed'] == case['model']['seed'])
        assert case['model'] == expected['model']
        assert case['condition'] == expected['condition']
        assert case['teacher_reference'] == expected['teacher_reference']
        for key in ('checkpoint', 'metadata'):
            assert sha(Path(case['model'][key])) == case['model'][key+'_sha256']
    expected = {
        name: sha(FIT/name) for name in (
            'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
            'data/training_data.npz', 'data/DATA_COMPLETE.json')}
    assert reg['v7_fit_files'] == expected


campaign.check = check
_base_prepare = campaign.prepare


def prepare(root):
    assert root == TARGET.resolve() and not root.exists()
    parent_registration = prerequisites()
    cases = []
    for identity, scene, family, seed, prefix in PLAN:
        source_case = next(c for c in parent_registration['cases']
                           if c['condition']['scene'] == scene
                           and c['model']['family'] == family
                           and c['model']['seed'] == seed)
        cases.append(dict(id=identity, scene=scene, student_steps=prefix,
                          model=source_case['model'],
                          condition=source_case['condition'],
                          teacher_reference=source_case['teacher_reference']))
    registration = dict(
        schema='sii-contact-yield-v7-mlp-rod-handoff-v1',
        registered_utc=campaign.now(), cases=cases, maximum_episodes=len(PLAN),
        source_sha256=source_manifest(),
        parent_files={name: sha(PARENT/name) for name in
                      ('REGISTRATION.json', 'execution.json', 'REVIEW.json')},
        final_execution_sha256=sha(FINAL/'execution.json'),
        teacher_config=parent_registration['teacher_config'],
        teacher_config_sha256=parent_registration['teacher_config_sha256'],
        python=str(Path(sys.executable).absolute()),
        resources=dict(cpu=6, simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0),
        purpose=(
            'Run four actual VMC-teacher suffix probes from the exact current v7 '
            'MLP seed02/seed03 fixed27 failure checkpoints at 4.48s and 4.60s. '
            'No unseen evaluation, model reselection, fitting, gate/physics/input/'
            'filter/actuator/dt change, or automatic retry. Preserve every outcome; '
            'only independently qualified executed suffixes may be considered by a '
            'separate shared-data decision.'))
    registration['v7_fit_files'] = {
        name: sha(FIT/name) for name in (
            'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
            'data/training_data.npz', 'data/DATA_COMPLETE.json')}
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', registration)
    check(registration)


campaign.prepare = prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    assert root == TARGET.resolve()
    if args.mode == 'prepare':
        prepare(root)
    else:
        campaign.run(root)


if __name__ == '__main__':
    main()
