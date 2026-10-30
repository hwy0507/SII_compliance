"""Register a bounded early-handoff timing bracket for v7 MLP rod failures."""
import argparse
import importlib.util
from pathlib import Path
import sys

EXPECTED_PYTHON = Path('/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python')
if Path(sys.executable).resolve() != EXPECTED_PYTHON.resolve():
    raise SystemExit(f'wrong interpreter: {sys.executable}; expected {EXPECTED_PYTHON}')
import mujoco
if mujoco.__version__ != '3.11.0':
    raise SystemExit(f'wrong MuJoCo version: {mujoco.__version__}; expected 3.11.0')

ROOT = Path(__file__).resolve().parents[1]
V3_SCRIPT = ROOT/'experiments/contact_yield_v7_mlp_rod_handoff_20261030_v3.py'
TARGET = ROOT/'outputs/contact_yield_v7_mlp_rod_handoff_20261030_v4'
PLAN = (
    ('v7_rod_mlp02_handoff_4p20s', 'rod', 'mlp_scratch', 2026102802, 105),
    ('v7_rod_mlp02_handoff_4p32s', 'rod', 'mlp_scratch', 2026102802, 108),
    ('v7_rod_mlp03_handoff_4p20s', 'rod', 'mlp_scratch', 2026102803, 105),
    ('v7_rod_mlp03_handoff_4p32s', 'rod', 'mlp_scratch', 2026102803, 108),
)

spec = importlib.util.spec_from_file_location('contact_yield_v7_handoff_v3', V3_SCRIPT)
campaign = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = campaign
spec.loader.exec_module(campaign)
campaign.TARGET = TARGET
campaign.campaign.PLAN = PLAN

_base_check = campaign.check
_base_source_manifest = campaign.source_manifest


def source_manifest():
    manifest = _base_source_manifest()
    path = Path(__file__).resolve()
    manifest[str(path.relative_to(ROOT))] = campaign.campaign.sha(path)
    return manifest


campaign.source_manifest = source_manifest


def check(registration):
    assert registration['schema'] == 'sii-contact-yield-v7-mlp-rod-handoff-v4'
    assert registration['source_sha256'] == source_manifest()
    translated = dict(registration, schema='sii-contact-yield-v7-mlp-rod-handoff-v3')
    _base_check(translated)


campaign.campaign.campaign.check = check


def prepare(root):
    assert root == TARGET.resolve() and not root.exists()
    parent = campaign.campaign.prerequisites()
    cases = []
    for identity, scene, family, seed, prefix in PLAN:
        source_case = next(case for case in parent['cases']
                           if case['condition']['scene'] == scene
                           and case['model']['family'] == family
                           and case['model']['seed'] == seed)
        cases.append(dict(id=identity, scene=scene, student_steps=prefix,
                          model=source_case['model'],
                          condition=source_case['condition'],
                          teacher_reference=source_case['teacher_reference']))
    fit = campaign.campaign.FIT
    registration = dict(
        schema='sii-contact-yield-v7-mlp-rod-handoff-v4',
        registered_utc=campaign.campaign.campaign.now(), cases=cases,
        maximum_episodes=len(PLAN), source_sha256=source_manifest(),
        parent_files={name: campaign.campaign.sha(campaign.campaign.PARENT/name) for name in
                      ('REGISTRATION.json', 'execution.json', 'REVIEW.json')},
        final_execution_sha256=campaign.campaign.sha(campaign.campaign.FINAL/'execution.json'),
        teacher_config=parent['teacher_config'],
        teacher_config_sha256=parent['teacher_config_sha256'],
        python=str(EXPECTED_PYTHON),
        resources=dict(cpu_affinity=[6], simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0),
        purpose=(
            'Compare the previously authorized v7 MLP rod failure checkpoints with '
            'the same frozen VMC teacher at earlier 4.20s and 4.32s handoff times. '
            'Four serial train-identity episodes only; no test access, fitting, '
            'model reselection, gate/physics/input/filter/actuator/dt change, or retry. '
            'Preserve every result; only qualified actual teacher suffixes may be '
            'considered by a separate data protocol.'))
    registration['v7_fit_files'] = {
        name: campaign.campaign.sha(fit/name) for name in (
            'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
            'data/training_data.npz', 'data/DATA_COMPLETE.json')}
    root.mkdir(parents=True)
    campaign.campaign.write(root/'REGISTRATION.json', registration)
    check(registration)


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
        campaign.campaign.campaign.run(root)


if __name__ == '__main__':
    main()
