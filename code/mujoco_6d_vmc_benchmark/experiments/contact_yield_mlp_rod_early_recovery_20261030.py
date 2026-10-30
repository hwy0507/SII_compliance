"""Probe earlier teacher takeover for the two remaining rod MLP seed failures."""
import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT/'experiments/contact_yield_recovery_campaign_20261030.py'
PARENT = ROOT/'outputs/contact_yield_targeted_student_development_20261030_v2'
TARGET = ROOT/'outputs/contact_yield_mlp_rod_early_recovery_20261030_v1'
FINAL = ROOT/'outputs/contact_yield_final108_handoff_20261030_v1'
FIT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v4'
FIT_HANDOFF = ROOT/'outputs/contact_yield_recovery_training_handoff_20261030_v4'
FIT_SCOPE = 'sii-contact-yield-targeted-refit-v4-20261030.scope'
DIAG_SCOPE = 'sii-contact-yield-targeted-diagnosis-v2-20261030.scope'
FINAL_UNIT = 'sii-contact-yield-final108-handoff-20261030.service'
PLAN = (
    ('rod_mlp01_early_4p48s', 'rod', 'mlp_scratch', 2026102801, 112),
    ('rod_mlp01_early_4p60s', 'rod', 'mlp_scratch', 2026102801, 115),
    ('rod_mlp02_prelimit_4p48s', 'rod', 'mlp_scratch', 2026102802, 112),
    ('rod_mlp02_prelimit_4p60s', 'rod', 'mlp_scratch', 2026102802, 115),
)

sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_special_scene_actions_20261028 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import properties

spec = importlib.util.spec_from_file_location('targeted_rod_base_campaign', BASE_PATH)
campaign = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = campaign
spec.loader.exec_module(campaign)
campaign.PARENT = PARENT
campaign.FINAL = FINAL
campaign.PLAN = tuple((name, scene, family, steps) for name, scene, family, seed, steps in PLAN)
campaign.UNITS = ()


def prerequisites():
    for unit in (FIT_SCOPE, DIAG_SCOPE):
        state = properties(unit)
        assert state['ActiveState'] == 'inactive', (unit, state)
        assert state.get('MainPID', '0') in ('', '0'), (unit, state)
    review = read(PARENT/'REVIEW.json')
    execution = read(PARENT/'execution.json')
    assert review['status'] == 'verified_fixed27_development_diagnosis'
    assert review['execution_sha256'] == sha(PARENT/'execution.json')
    assert review['registration_sha256'] == sha(PARENT/'REGISTRATION.json')
    assert set(review['failed_ids']) == {
        'rod_00__special_mlp_scratch_s2026102801',
        'rod_00__special_mlp_scratch_s2026102802',
        'rod_00__special_mlp_scratch_s2026102803'}
    assert execution['status'] == 'complete_development_diagnosis_pending_review'
    assert len(execution['rows']) == 27
    assert review['no_model_reselection'] and review['no_final_test_performed']
    final = read(FINAL/'execution.json')
    assert final['status'] == 'development_not_qualified_no_final_dispatch'
    assert final['dispatch_attempted'] is False
    assert not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    training = read(FIT/'execution.json')
    lock = read(FIT/'MODEL_LOCK.json')
    audit = read(FIT/'FIT_AUDIT.json')
    assert training['status'] == 'complete' and lock['status'] == 'frozen'
    assert audit['status'] == 'passed' and len(lock['models']) == 9
    assert audit['model_lock_sha256'] == sha(FIT/'MODEL_LOCK.json')
    return read(PARENT/'REGISTRATION.json')


def source_manifest():
    paths = [Path(__file__).resolve(), BASE_PATH.resolve(), campaign.WORKER.resolve(),
             campaign.AUDITOR.resolve()]
    paths += [p for folder in ('scripts', 'tools') for p in (ROOT/folder).glob('*.py')]
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))}


def prepare(root):
    assert root == TARGET and not root.exists()
    parent = prerequisites()
    cases = []
    for identity, scene, family, seed, steps in PLAN:
        case = next(c for c in parent['cases'] if c['condition']['id'] == 'rod_00'
                    and c['model']['family'] == family and c['model']['seed'] == seed)
        cases.append(dict(id=identity, scene=scene, student_steps=steps,
                          model=case['model'], condition=case['condition'],
                          teacher_reference=case['teacher_reference']))
    sources = source_manifest()
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', dict(
        schema='contact-yield-targeted-early-rod-recovery-v1', registered_utc=campaign.now(),
        cases=cases, maximum_episodes=4, source_sha256=sources,
        parent_files={name: sha(PARENT/name) for name in
            ('REGISTRATION.json', 'execution.json', 'REVIEW.json')},
        final_execution_sha256=sha(FINAL/'execution.json'),
        fit_files={name: sha(FIT/name) for name in
            ('execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json')},
        teacher_config=parent['teacher_config'],
        teacher_config_sha256=parent['teacher_config_sha256'],
        python=str(Path(sys.executable).resolve()),
        resources=dict(cpu=6, simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0),
        purpose=('Diagnose whether earlier handoff lets the unchanged teacher resolve the two '
                 'remaining rod MLP development failure modes. Only independently qualified '
                 'executed suffixes may be considered for a later shared refit. No model, '
                 'physics, actor, filter, executor, dt, gate, selection, or test changes.')))


def check(reg):
    prerequisites()
    assert reg['schema'] == 'contact-yield-targeted-early-rod-recovery-v1'
    assert reg['source_sha256'] == source_manifest()
    assert reg['parent_files'] == {name: sha(PARENT/name) for name in
        ('REGISTRATION.json', 'execution.json', 'REVIEW.json')}
    assert reg['final_execution_sha256'] == sha(FINAL/'execution.json')
    assert reg['fit_files'] == {name: sha(FIT/name) for name in
        ('execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json')}
    assert reg['maximum_episodes'] == 4 and len(reg['cases']) == 4
    for spec_case, case in zip(PLAN, reg['cases']):
        identity, scene, family, seed, steps = spec_case
        assert (case['id'], case['scene'], case['model']['family'],
                case['model']['seed'], case['student_steps']) == (
                    identity, scene, family, seed, steps)
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
