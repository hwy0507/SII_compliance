"""Register v3 of the bounded v7 MLP rod teacher-handoff probes."""
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
V2_SCRIPT = ROOT/'experiments/contact_yield_v7_mlp_rod_handoff_20261030_v2.py'
TARGET = ROOT/'outputs/contact_yield_v7_mlp_rod_handoff_20261030_v3'
spec = importlib.util.spec_from_file_location('contact_yield_v7_handoff_v2', V2_SCRIPT)
campaign = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = campaign
spec.loader.exec_module(campaign)
campaign.TARGET = TARGET

_base_check = campaign.check
_base_source_manifest = campaign.source_manifest


def source_manifest():
    manifest = _base_source_manifest()
    path = Path(__file__).resolve()
    manifest[str(path.relative_to(ROOT))] = campaign.sha(path)
    return manifest


campaign.source_manifest = source_manifest


def check(registration):
    assert registration['schema'] == 'sii-contact-yield-v7-mlp-rod-handoff-v3'
    assert registration['python'] == str(EXPECTED_PYTHON)
    assert registration['source_sha256'] == source_manifest()
    translated = dict(registration, schema='sii-contact-yield-v7-mlp-rod-handoff-v2')
    _base_check(translated)


campaign.campaign.check = check


def prepare(root):
    assert root == TARGET.resolve() and not root.exists()
    parent = campaign.prerequisites()
    cases = []
    for identity, scene, family, seed, prefix in campaign.PLAN:
        source_case = next(case for case in parent['cases']
                           if case['condition']['scene'] == scene
                           and case['model']['family'] == family
                           and case['model']['seed'] == seed)
        cases.append(dict(id=identity, scene=scene, student_steps=prefix,
                          model=source_case['model'],
                          condition=source_case['condition'],
                          teacher_reference=source_case['teacher_reference']))
    fit = campaign.FIT
    registration = dict(
        schema='sii-contact-yield-v7-mlp-rod-handoff-v3',
        registered_utc=campaign.campaign.now(), cases=cases,
        maximum_episodes=len(campaign.PLAN), source_sha256=source_manifest(),
        parent_files={name: campaign.sha(campaign.PARENT/name) for name in
                      ('REGISTRATION.json', 'execution.json', 'REVIEW.json')},
        final_execution_sha256=campaign.sha(campaign.FINAL/'execution.json'),
        teacher_config=parent['teacher_config'],
        teacher_config_sha256=parent['teacher_config_sha256'],
        python=str(EXPECTED_PYTHON),
        resources=dict(cpu_affinity=[6], cpu_quota_percent=100,
                       simulators=1, threads=1,
                       memory_max_bytes=3221225472, swap_bytes=0),
        purpose=(
            'Run the four bounded VMC-teacher suffix probes from the exact v7 MLP '
            'seed02/seed03 fixed27 failure checkpoints at 4.48s and 4.60s. This '
            'registration corrects only process affinity launch via taskset -c 6; '
            'no unseen evaluation, reselection, fitting, physics/gate/input/filter/'
            'actuator/dt change, or automatic retry. Preserve every outcome.'))
    registration['v7_fit_files'] = {
        name: campaign.sha(fit/name) for name in (
            'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
            'data/training_data.npz', 'data/DATA_COMPLETE.json')}
    root.mkdir(parents=True)
    campaign.write(root/'REGISTRATION.json', registration)
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
        campaign.campaign.run(root)


if __name__ == '__main__':
    main()
