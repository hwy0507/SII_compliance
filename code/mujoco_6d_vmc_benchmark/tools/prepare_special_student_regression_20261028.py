"""Prepare18 real-scene closures before the repaired frozen108 comparison.

Each family uses seed2026102801 on training identity00 and validation identity08
in each of the three real scenes. All three seeds still enter the final108.
The completed collection supplies the paired teacher references. Neither this
tool nor its runner trains, selects a checkpoint, or relaxes a task criterion.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from collect_special_scene_actions_20261028 import ROOT, read, sha, write, validate
from diagnose_special_scene_regression_20261028 import OLD_TEST, now, run as run_cases


def prepare(root, collection, training, handoff, service, physics_source):
    if root.exists():
        raise FileExistsError(root)
    plan = validate(collection/'COLLECTION_PLAN.json')
    handoff_plan = read(handoff/'REGISTRATION.json')
    assert Path(handoff_plan['collection']) == collection
    assert Path(handoff_plan['training']) == training
    selected = [r for r in plan['episodes'] if r['id'] in
                {s+'_'+i for s in ('corner', 'rod', 'ball') for i in ('00', '08')}]
    assert len(selected) == 6
    assert {r['split'] for r in selected} == {'train', 'validation'}
    tools = ('prepare_special_student_regression_20261028.py',
             'diagnose_special_scene_regression_20261028.py',
             'run_video_reference_vmc_20261028.py', 'audit_video_reference_vmc_20261028.py',
             'qualify_special_scene_demo_20261028.py', 'audit_rod_yield_rejoin_v3_20261028.py',
             'collect_special_scene_actions_20261028.py', 'optimize_tool_contact_20261002.py',
             'audit_special_scene_fits_20261028.py', 'train_special_scene_models_20261028.py')
    sources = list((ROOT/'scripts').glob('*.py'))+[ROOT/'tools'/name for name in tools]
    root.mkdir(parents=True)
    write(root/'PREPARATION.json', dict(schema='sii-repaired-student-scene-regression-v1',
        registered_utc=now(), collection=str(collection), training=str(training), handoff=str(handoff),
        handoff_service=service, physics_source=str(physics_source),
        physics_source_sha256={str(p.relative_to(physics_source)):sha(p) for p in sorted(physics_source.rglob('*.py'))},
        collection_plan_sha256=sha(collection/'COLLECTION_PLAN.json'),
        handoff_registration_sha256=sha(handoff/'REGISTRATION.json'), identities=selected,
        model_seed=2026102801, families=['esn_ridge', 'rnn_scratch', 'mlp_scratch'],
        maximum_episodes=18, source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},
        purpose='Training00 reproduces the diagnosed failure; validation08 checks the same repair beyond that identity. Fixed chosen models, no fitting or test-based selection. Development gates, not final test Strict. Review all failures before final108.',
        resources=dict(simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0)))
    print(root, sha(root/'PREPARATION.json'))


def run(root):
    prep = read(root/'PREPARATION.json')
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    assert (cg/'memory.max').read_text().strip() != 'max'
    assert int((cg/'memory.max').read_text()) <= 3221225472 and int((cg/'memory.swap.max').read_text()) == 0
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    for name, h in prep['source_sha256'].items():
        assert sha(ROOT/name) == h, name
    frozen = Path(prep['physics_source'])
    assert {str(p.relative_to(frozen)):sha(p) for p in sorted(frozen.rglob('*.py'))} == prep['physics_source_sha256']
    if (root/'REGISTRATION.json').exists() or (root/'FIT_AUDIT.json').exists():
        raise FileExistsError('Preserve existing registration/audit; do not duplicate')
    collection, training, handoff = (Path(prep[k]) for k in ('collection','training','handoff'))
    assert sha(collection/'COLLECTION_PLAN.json') == prep['collection_plan_sha256']
    assert sha(handoff/'REGISTRATION.json') == prep['handoff_registration_sha256']
    assert read(handoff/'execution.json')['status'] == 'fitting_complete_pending_test_review'
    service = dict(line.split('=',1) for line in subprocess.check_output(
        ['systemctl','--user','show',prep['handoff_service'],'-p','ActiveState','-p','Result'],text=True).splitlines())
    assert service == dict(ActiveState='inactive',Result='success')
    assert read(training/'execution.json')['status'] == 'complete'
    assert read(collection/'COLLECTION_PROGRESS.json')['status'] == 'qualified_complete'
    with (root/'fit_audit.log').open('x') as log:
        subprocess.run([sys.executable,str(ROOT/'tools/audit_special_scene_fits_20261028.py'),
            '--root',str(training),'--physics-source',prep['physics_source'],
            '--output',str(root/'FIT_AUDIT.json')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    fit = read(root/'FIT_AUDIT.json')
    assert fit['status'] == 'passed' and fit['model_lock_sha256'] == sha(training/'MODEL_LOCK.json')
    lock = read(training/'MODEL_LOCK.json')
    assert len(lock['models']) == 9
    cases = []
    teacher_refs = {}
    for entry in prep['identities']:
        folder = Path(entry['folder'])
        qualification = read(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert qualification['status'] == 'qualified'
        for name,h in qualification['input_hashes'].items():
            assert sha(folder/name) == h, str(folder/name)
        teacher_refs[entry['id']] = dict(folder=str(folder), qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
        for family in prep['families']:
            model = next(m for m in lock['models'] if m['family']==family and m['seed']==prep['model_seed'])
            cases.append(dict(id=entry['id']+'_'+family, kind='scene', scene=entry['scene'],
                identity=entry['id'], split=entry['split'], seed=entry['seed'],
                scene_parameters=entry['scene_parameters'], baseline=str(folder),
                baseline_execution_sha256=sha(folder/'execution.json'),
                expected_model_sha256=read(folder/'execution.json')['model_sha256'],
                config=str(folder/'teacher.json'), model=model))
    assert len(cases) == prep['maximum_episodes']
    reg = dict(schema='sii-repaired-student-scene-closure-v1',registered_utc=now(),
        preparation_sha256=sha(root/'PREPARATION.json'), fit_audit_sha256=sha(root/'FIT_AUDIT.json'),
        old_execution_sha256=sha(OLD_TEST/'execution.json'), model_lock_sha256=sha(training/'MODEL_LOCK.json'),
        maximum_episodes=len(cases), cases=cases, teacher_references=teacher_refs,
        source_sha256=prep['source_sha256'], config_sha256={c['config']:sha(Path(c['config'])) for c in cases},
        interpretation=prep['purpose'], resources=prep['resources'])
    write(root/'REGISTRATION.json',reg)
    run_cases(root,training=training)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    for name in ('collection','training','handoff','physics-source'):
        p.add_argument('--'+name,type=Path)
    p.add_argument('--handoff-service',default='sii-special-learning-handoff-v3-20261028.service')
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.run:
        run(a.root.resolve())
    else:
        if not all((a.collection,a.training,a.handoff,a.physics_source)):
            p.error('Preparation requires collection, training, handoff and physics-source')
        prepare(a.root.resolve(),a.collection.resolve(),a.training.resolve(),a.handoff.resolve(),
                a.handoff_service,a.physics_source.resolve())
