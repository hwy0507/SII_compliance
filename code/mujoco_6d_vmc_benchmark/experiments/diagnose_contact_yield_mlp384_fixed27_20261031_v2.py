"""Versioned fixed27 runner after correcting the wide-checkpoint loader route."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

import diagnose_contact_yield_mlp384_fixed27_20261031 as v1

ROOT = v1.ROOT
TARGET = ROOT/'outputs/contact_yield_mlp384_fixed27_20261031_v2'
RUNNER = ROOT/'tools/run_video_reference_coverage_mlp384_20261031.py'
PRIOR = ROOT/'outputs/contact_yield_mlp384_fixed27_20261031_v1'


def run_case(root, case, reg):
    diagnosis = v1.diagnosis
    output = diagnosis.case_folder(root, case).parent
    assert not output.exists(), 'Existing complete or incomplete evidence must not be overwritten'
    output.parent.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k in
           {'PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH', 'MUJOCO_GL', 'TMPDIR'}}
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),
               MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
               VMC_TEACHER_CONFIG=reg['teacher_config'],
               VMC_SCENE_SEED=str(case['condition']['seed']),
               VMC_STUDENT_CHECKPOINT=case['model']['checkpoint'])
    env.update({k: str(value) for k, value in case['condition']['parameters'].items()})
    with (output.parent/(case['id']+'.log')).open('x') as log:
        subprocess.run([sys.executable, str(RUNNER), '--output', str(output),
                        '--scenes', case['condition']['scene']], cwd=ROOT, env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    folder = diagnosis.case_folder(root, case)
    audits = ['audit_video_reference_vmc_20261028.py']
    if case['condition']['scene'] == 'rod':
        audits.append('audit_rod_yield_rejoin_v3_20261028.py')
    audits.append('qualify_ball_coverage_demo_20261029.py')
    for tool in audits:
        with (output/(tool+'.log')).open('x') as log:
            subprocess.run([sys.executable, str(ROOT/'tools'/tool), str(folder)], cwd=ROOT,
                           env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    pairing = diagnosis.check_episode(folder, case, reg)
    row = diagnosis.episode(folder, case['model']['name'], case['condition']['id'],
                            case['expected_duration_s'])
    v1.write(output/'METRICS.json', row)
    return dict(id=case['id'], folder=str(folder), pairing=pairing,
                metrics_sha256=v1.sha(output/'METRICS.json'))


v1.TARGET = TARGET
v1.diagnosis.run_case = run_case


def check(reg):
    assert reg['schema'] == 'sii-contact-yield-mlp384-fixed27-diagnosis-v2'
    assert reg['parent_attempt'] == {
        'registration_sha256': v1.sha(PRIOR/'REGISTRATION.json'),
        'execution_sha256': v1.sha(PRIOR/'execution.json'),
        'status': 'failed_preserved_no_retry',
        'failed_contract': 'proprio48_office_mlp_rnn_v2',
        'physical_steps_for_failed_mlp': 0,
    }
    base = dict(reg)
    base['schema'] = 'sii-contact-yield-mlp384-fixed27-diagnosis-v1'
    base.pop('parent_attempt')
    v1.check(base)
    source = str(Path(__file__).relative_to(ROOT))
    assert reg['source_sha256'][source] == v1.sha(Path(__file__))


def prepare(root):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    v1.prepare(root)
    path = root/'REGISTRATION.json'
    reg = v1.read(path)
    reg['schema'] = 'sii-contact-yield-mlp384-fixed27-diagnosis-v2'
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = v1.sha(Path(__file__))
    reg['parent_attempt'] = {
        'registration_sha256': v1.sha(PRIOR/'REGISTRATION.json'),
        'execution_sha256': v1.sha(PRIOR/'execution.json'),
        'status': 'failed_preserved_no_retry',
        'failed_contract': 'proprio48_office_mlp_rnn_v2',
        'physical_steps_for_failed_mlp': 0,
    }
    v1.write(path, reg)
    check(reg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run', 'review'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.mode == 'prepare':
        prepare(root)
    elif args.mode == 'run':
        v1.diagnosis.check = check
        v1.diagnosis.run(root)
    else:
        v1.diagnosis.check = check
        assert args.output is not None
        v1.diagnosis.review(root, args.output.resolve())


if __name__ == '__main__':
    main()
