"""Finite offset-only repair following completed blend-scaling controls.

Same five training identities and disclosed office000; no collection/fitting.
Keep feedback gains, memory and original release; change equilibrium offset
only. Require a complete prior review and new actor arithmetic checks.
"""
import argparse
import copy
import shutil
import subprocess
import sys
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import OLD_TEST, now, run
from intent_equilibrium_teacher_20261029 import VERSION
from review_special_teacher_midpoint_20261028 import inactive


def prepare(root):
    assert not root.exists()
    parent = ROOT/'outputs/special_intent_recovery_20261029_v1'
    inactive('sii-special-intent-recovery-v1-20261029.service')
    reg, state, review = [read(parent/name) for name in ('REGISTRATION.json', 'execution.json', 'REVIEW.json')]
    assert state['status'] == 'complete_pending_review' and len(state['episodes']) == 6
    assert state['registration_sha256'] == sha(parent/'REGISTRATION.json')
    assert review['execution_sha256'] == sha(parent/'execution.json')
    assert not review['all_six_qualified']
    checks_path = ROOT/'outputs/special_intent_equilibrium_preparation_20261029_v1/ACTOR_CHECKS.json'
    checks = read(checks_path)
    assert checks['status'] == 'passed' and checks['synthetic_steps'] == 2700
    for name, digest in checks['source_sha256'].items():
        assert sha(ROOT/'tools'/name) == digest
    config = checks['config']
    assert config['teacher_mechanism'] == VERSION
    # Factory must resolve the exact class used by the copied office driver.
    from run_video_reference_vmc_20261028 import make_actor
    from intent_equilibrium_teacher_20261029 import IntentEquilibriumTeacher
    assert type(make_actor(config)) is IntentEquilibriumTeacher
    root.mkdir(parents=True)
    teacher = root/'teacher_equilibrium.json'
    write(teacher, config)
    shutil.copy2(checks_path, root/'ACTOR_CHECKS.json')
    source = root/'source'
    shutil.copytree(OLD_TEST/'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    originals = {str(p.relative_to(OLD_TEST/'source')):sha(p) for p in (OLD_TEST/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    assert all(sha(source/name) == digest for name, digest in originals.items())
    additions = ('intent_equilibrium_teacher_20261029.py', 'intent_equilibrium_office_driver_20261029.py')
    for name in additions:
        assert not (source/'tools'/name).exists()
        shutil.copy2(ROOT/'tools'/name, source/'tools'/name)
    code = "import sys,json,hashlib,numpy as np;from pathlib import Path;root=Path(sys.argv[1]);sys.path[:0]=[str(root/'scripts'),str(root/'tools')];import intent_equilibrium_teacher_20261029 as m;import optimize_tool_contact_20261002 as o;assert Path(o.__file__).resolve().parent==root/'tools';a=m.IntentEquilibriumTeacher(json.load(open(sys.argv[2])));z=np.load(sys.argv[3]);out=[];[(a.observe(obs),out.append(a.act(obs[39:45]))) for obs in z['observation']];print(hashlib.sha256(np.array(out).tobytes()).hexdigest())"
    trace = ROOT/'outputs/special_teacher_midpoint_office_20261028_v1/office_v075_avg1/rollout.npz'
    digests = [subprocess.check_output([sys.executable, '-c', code, str(folder), str(teacher), str(trace)], text=True).strip() for folder in (ROOT, source)]
    assert digests[0] == digests[1]
    write(root/'SOURCE_COPY_REVIEW.json', dict(original_files=originals, added=list(additions), live_and_copied_replay_sha256=digests))
    cases = copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher), id='equilibrium_'+case.get('identity', 'office000'))
        if case['kind'] == 'office':
            assert case['command'][1].endswith('/intent_teacher_office_driver_20261029.py')
            case['command'][1] = str(source/'tools/intent_equilibrium_office_driver_20261029.py')
    successor = {k:copy.deepcopy(reg[k]) for k in ('old_test', 'old_execution_sha256', 'old_completed', 'model_lock_sha256', 'collection_plan_sha256', 'resources', 'action_contract')}
    hashes = {name:sha(ROOT/name) for name in reg['source_sha256'] if not name.startswith('outputs/')}
    for name in (*additions, 'check_intent_equilibrium_20261029.py', 'review_intent_recovery_controls_20261029.py', Path(__file__).name):
        hashes['tools/'+name] = sha(ROOT/'tools'/name)
    hashes.update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'})
    successor.update(schema='sii-intent-equilibrium-finite-controls-v1', registered_utc=now(),
        maximum_episodes=6, cases=cases, source_sha256=hashes, config_sha256={str(teacher):sha(teacher)},
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'), source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        parent_review_sha256=sha(parent/'REVIEW.json'), teacher_mechanism=VERSION,
        parent_execution_sha256=sha(parent/'execution.json'), interpretation=__doc__,
        selection_rule='All five original training qualifications and office Task/Strict required before new30; retain every failure. No automatic collection, training or validation tuning.')
    write(root/'REGISTRATION.json', successor)
    print(root, sha(root/'REGISTRATION.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    (run if args.run else prepare)(args.root.resolve())
