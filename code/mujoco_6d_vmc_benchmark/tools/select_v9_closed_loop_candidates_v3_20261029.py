"""Finite, common development eligibility screen of already trained candidates.

Wait for all 18 paired diagnoses and their review before registration/dispatch.
Each family/seed gets the same top-three validation-MSE candidates and nine
train/validation closures. No test outcomes, new fitting, or gate relaxation.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time

from catalogue_v9_frozen_candidates_20261029 import build
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now
from prepare_v9_paired_scene_closure_20261029 import (
    COLLECTION, TRAINING, WRAPPER, QUALIFIER, equivalent_physical_worker)
from review_v9_paired_scene_closure_20261029 import review, verify_qualification

PARENT = ROOT/'outputs/nonrl_v9_paired_scene_priority_20261029_v5'
PARENT_UNIT = 'sii-v9-paired-priority-v5-20261029.service'


def properties(unit):
    text = subprocess.check_output(['systemctl', '--user', 'show', unit,
        '-p', 'ActiveState', '-p', 'MainPID', '-p', 'InvocationID'], text=True)
    return dict(line.split('=', 1) for line in text.splitlines())


def require_parent_review():
    state = read(PARENT/'execution.json')
    assert state['status'] == 'complete_pending_review' and len(state['rows']) == 18
    assert properties(PARENT_UNIT)['ActiveState'] == 'inactive'
    destination = PARENT/'REVIEW.json'
    if not destination.exists():
        review(PARENT, destination)
    report = read(destination)
    assert report['status'] == 'complete_development_review' and len(report['rows']) == 18
    assert report['execution_sha256'] == sha(PARENT/'execution.json')
    assert report['registration_sha256'] == sha(PARENT/'REGISTRATION.json')
    assert report['reviewer_sha256'] == sha(ROOT/'tools/review_v9_paired_scene_closure_20261029.py')
    assert all(r['teacher_qualified'] for r in report['rows']), 'Teacher problem requires data repair first'
    return report


def register(root):
    assert not (root/'REGISTRATION.json').exists() and not (root/'execution.json').exists()
    parent_review = require_parent_review()
    assert any(not r['development_qualified'] for r in parent_review['rows']), 'No eligibility defect to repair'
    catalogue = build(TRAINING)
    plan = read(COLLECTION/'COLLECTION_PLAN.json')
    references = []
    for scene in ('rod', 'ball', 'corner'):
        for suffix in ('00', '08', '09'):
            identity = scene+'_'+suffix
            entry = next(e for e in plan['episodes'] if e['id'] == identity)
            assert entry['split'] == ('train' if suffix == '00' else 'validation')
            folder = Path(entry['folder'])
            qualification = verify_qualification(folder, sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
            assert qualification['status'] == 'qualified'
            execution = read(folder/'execution.json')
            for name, digest in read(folder/'SOURCE_HASHES.json').items():
                if name.startswith('scripts/'):
                    assert sha(ROOT/name) == digest, name
            references.append(dict(identity=identity, scene=scene, split=entry['split'],
                seed=entry['seed'], parameters=entry['scene_parameters'], folder=str(folder),
                model_sha256=execution['model_sha256'],
                execution_sha256=sha(folder/'execution.json'),
                qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),
                config_sha256=sha(folder/'teacher.json')))
    sources = list((ROOT/'scripts').glob('*.py'))+list((ROOT/'tools').glob('*.py'))
    registration = dict(schema='sii-v9-common-closed-loop-eligibility-v1', registered_utc=now(),
        parent=str(PARENT), parent_execution_sha256=sha(PARENT/'execution.json'),
        parent_registration_sha256=sha(PARENT/'REGISTRATION.json'),
        parent_review_sha256=sha(PARENT/'REVIEW.json'), catalogue=catalogue,
        candidate_limit_per_family_seed=3, references=references,
        maximum_groups=9, maximum_candidates=27, maximum_candidate_case_checks=243,
        selection='For each family/seed, rank existing 12 candidates by the same six-identity teacher-history validation MSE, tie by id. Inspect at most the first three. Select the first candidate qualified on all nine closures (train00 and both validation08/09 in each of three scenes). Fail a candidate at its first failed closure; retain that full failure. Reuse only exact checkpoint/identity source-bound complete parent closures. If none passes, record null and require further repair; no fallback or final-test dispatch.',
        selection_scope='Development-only revised eligibility rule; no claim of unseen-test success. All families get identical rank cap, eligibility gates and case order. Existing training budgets remain 12 candidates/family/seed; no extra fitting.',
        physical_worker_equivalence=equivalent_physical_worker(), wrapper=WRAPPER, qualifier=QUALIFIER,
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
        resources=dict(cpu=6, simulators=1, threads=1, memory_max_bytes=3221225472, swap_bytes=0),
        unchanged=['training data and checkpoints', 'physical workers and per-identity MJB',
            'canonical48', 'public action filter', 'actuator limits', 'dt=5e-5', 'task and safety gates'])
    write(root/'REGISTRATION.json', registration)


def check_resources():
    group = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (group/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3221225472
    assert (group/'memory.swap.max').read_text().strip() == '0'
    assert os.sched_getaffinity(0) == {6}
    # Some user systemd trees do not delegate the CPU controller. Exact
    # one-core sched affinity still bounds this process and children to one CPU.
    if (group/'cpu.max').exists():
        quota, period = (group/'cpu.max').read_text().split()
        assert quota != 'max' and int(quota) <= int(period)
    assert all(os.environ.get(n) == '1' for n in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))


def check_sources(reg):
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    assert equivalent_physical_worker() == reg['physical_worker_equivalence']
    assert sha(PARENT/'execution.json') == reg['parent_execution_sha256']
    assert sha(PARENT/'REVIEW.json') == reg['parent_review_sha256']


def parent_cache(reg):
    registration = read(PARENT/'REGISTRATION.json')
    state = read(PARENT/'execution.json')
    assert sha(PARENT/'REGISTRATION.json') == reg['parent_registration_sha256']
    cache = {}
    for case, receipt in zip(registration['cases'], state['rows']):
        assert case['id'] == receipt['id'] and receipt['returncode'] == 0
        folder = PARENT/case['id']/case['scene']
        cache[(case['model']['checkpoint_sha256'], case['identity'])] = (folder, receipt['qualification_sha256'])
    return cache


def evaluate(root, reg, candidate, reference, cache):
    check_sources(reg)
    checkpoint = Path(candidate['checkpoint'])
    assert sha(checkpoint) == candidate['checkpoint_sha256']
    assert sha(Path(candidate['metadata'])) == candidate['metadata_sha256']
    teacher = Path(reference['folder'])
    assert sha(teacher/'execution.json') == reference['execution_sha256']
    assert sha(teacher/'teacher.json') == reference['config_sha256']
    key = (candidate['checkpoint_sha256'], reference['identity'])
    if key in cache:
        folder, digest = cache[key]
        reuse = True
    else:
        name = candidate['family']+'_s'+str(candidate['seed'])+'_rank'+str(candidate['validation_rank'])
        output = root/'evaluations'/name/reference['identity']
        output.parent.mkdir(parents=True, exist_ok=True)
        assert not output.exists(), 'Preserve incomplete runs; explicit recovery only'
        env = {k: v for k, v in os.environ.items() if k in
            {'PATH', 'HOME', 'USER', 'LANG', 'LD_LIBRARY_PATH', 'MUJOCO_GL', 'TMPDIR'}}
        env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
            MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),
            VMC_TEACHER_CONFIG=str(teacher/'teacher.json'), VMC_SCENE_SEED=str(reference['seed']),
            VMC_STUDENT_CHECKPOINT=str(checkpoint))
        env.update({k: str(v) for k, v in reference['parameters'].items()})
        with (output.parent/(reference['identity']+'.log')).open('x') as log:
            rc = subprocess.run([sys.executable, str(ROOT/'tools'/WRAPPER), '--output', str(output),
                '--scenes', reference['scene']], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        assert rc == 0, 'Infrastructure failure preserved, no automatic retry'
        folder = output/reference['scene']
        audits = ['audit_video_reference_vmc_20261028.py']
        if reference['scene'] == 'rod':
            audits.append('audit_rod_yield_rejoin_v3_20261028.py')
        audits.append(QUALIFIER)
        for tool in audits:
            with (output/(tool+'.log')).open('x') as log:
                subprocess.run([sys.executable, str(ROOT/'tools'/tool), str(folder)], cwd=ROOT,
                    env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        digest = sha(folder/'DEMONSTRATION_QUALIFICATION.json')
        reuse = False
    qualification = verify_qualification(folder, digest)
    execution = read(folder/'execution.json')
    assert execution['status'] == 'complete' and execution['model_sha256'] == reference['model_sha256']
    assert sha(folder/'student_checkpoint.npz') == candidate['checkpoint_sha256']
    assert execution['filter_config'] == read(teacher/'execution.json')['filter_config']
    for name, value in reference['parameters'].items():
        assert execution['experiment_environment'][name] == str(value)
    return dict(identity=reference['identity'], split=reference['split'], folder=str(folder),
        reused_parent_episode=reuse, qualification_sha256=digest,
        development_qualified=qualification['status'] == 'qualified',
        task_success=qualification['task_success'], safety_valid=qualification['safety_valid'],
        scene_behavior_valid=qualification['scene_contact_valid'])


def run(root):
    check_resources()
    reg = read(root/'REGISTRATION.json')
    assert not (root/'execution.json').exists()
    check_sources(reg)
    cache = parent_cache(reg)
    state = dict(status='running_development_eligibility', started_utc=now(),
        registration_sha256=sha(root/'REGISTRATION.json'), groups=[], selected_models=[])
    write(root/'execution.json', state)
    try:
        for group in reg['catalogue']['groups']:
            row = dict(family=group['family'], seed=group['seed'], trials=[], selected=None)
            state['groups'].append(row)
            for candidate in group['ordered_candidates'][:reg['candidate_limit_per_family_seed']]:
                trial = dict(candidate=candidate, cases=[], status='running')
                row['trials'].append(trial)
                write(root/'execution.json', state)
                for reference in reg['references']:
                    assert sha(root/'REGISTRATION.json') == state['registration_sha256']
                    state['current'] = dict(candidate=candidate['id'], identity=reference['identity'])
                    write(root/'execution.json', state)
                    episode = evaluate(root, reg, candidate, reference, cache)
                    assert sha(root/'REGISTRATION.json') == state['registration_sha256']
                    trial['cases'].append(episode)
                    write(root/'execution.json', state)
                    if not episode['development_qualified']:
                        trial['status'] = 'failed_eligibility_full_episode_preserved'
                        break
                else:
                    assert len(trial['cases']) == 9
                    trial['status'] = 'development_qualified_all_nine'
                    row['selected'] = candidate
                    state['selected_models'].append(dict(name='special_'+candidate['family']+'_s'+str(candidate['seed']),
                        family=candidate['family'], seed=candidate['seed'], validation_mse=candidate['validation_mse'],
                        selected_trial=candidate['id'], checkpoint=candidate['checkpoint'],
                        checkpoint_sha256=candidate['checkpoint_sha256'], metadata=candidate['metadata'],
                        metadata_sha256=candidate['metadata_sha256'], worker_kind='office', config={}))
                    write(root/'execution.json', state)
                    break
            row['status'] = 'selected_development_qualified' if row['selected'] else 'candidate_budget_exhausted_preserved'
            write(root/'execution.json', state)
        state.update(status=('selection_complete_pending_independent_audit' if len(state['selected_models']) == 9
            else 'eligibility_exhausted_preserved'), ended_utc=now())
        # Always preserve null selections and failed trials; never fall back to
        # an unqualified model or call development results final-test success.
        write(root/'DEVELOPMENT_SELECTION.json', dict(status=state['status'], models=state['selected_models'],
            registration_sha256=state['registration_sha256'], final_test_performed=False))
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc), ended_utc=now())
        raise
    finally:
        write(root/'execution.json', state)


def wait_and_run(root):
    assert not root.exists(), 'Never duplicate or silently restart'
    root.mkdir(parents=True)
    with (ROOT/'outputs/.v9-eligibility-coordinator.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        handoff = dict(status='waiting_for_complete_paired_review', started_utc=now(),
            parent=str(PARENT), parent_unit=PARENT_UNIT, maximum_wait_s=10800,
            runner_sha256=sha(Path(__file__)), pending_overlay_sha256={name: sha(ROOT/name) for name in
                ('tools/select_v9_closed_loop_candidates_v3_20261029.py',
                 'tools/catalogue_v9_frozen_candidates_20261029.py')})
        write(root/'HANDOFF.json', handoff)
        deadline = time.monotonic()+10800
        try:
            while time.monotonic() < deadline:
                assert all(sha(ROOT/name) == digest for name, digest in handoff['pending_overlay_sha256'].items())
                state = read(PARENT/'execution.json')
                if state['status'] == 'failed_preserved':
                    raise RuntimeError('Parent failed: review infrastructure before any dispatch')
                if state['status'] == 'complete_pending_review' and properties(PARENT_UNIT)['ActiveState'] == 'inactive':
                    break
                time.sleep(20)
            else:
                raise TimeoutError('Finite wait expired, no dispatch')
            require_parent_review()
            assert all(sha(ROOT/name) == digest for name, digest in handoff['pending_overlay_sha256'].items())
            register(root)
            handoff.update(status='running_registered_eligibility', dispatched_utc=now())
            write(root/'HANDOFF.json', handoff)
            run(root)
            handoff.update(status='finished_pending_scientific_review', ended_utc=now())
        except BaseException as exc:
            handoff.update(status='failed_preserved', error=repr(exc), ended_utc=now())
            raise
        finally:
            write(root/'HANDOFF.json', handoff)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    wait_and_run(args.root.resolve())
