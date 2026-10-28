"""Check the versioned actor, then register six finite physical controls.

No fitting or validation probing. Office000 is a disclosed development
regression, never unseen evidence or demonstration data.
"""
import argparse
import copy
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import OLD_TEST, now, run
from intent_recovery_teacher_20261029 import VERSION, make_teacher, LegacyParameterTeacher
from review_special_teacher_midpoint_20261028 import inactive


def actor_checks(config):
    original = copy.deepcopy(config)
    original.pop('teacher_mechanism')
    assert type(make_teacher(original)) is LegacyParameterTeacher
    try:
        make_teacher(dict(config, teacher_mechanism='unknown'))
    except ValueError:
        pass
    else:
        raise AssertionError('Unknown actor version accepted')
    rng = np.random.default_rng(2026102901)
    counts = {}
    for weight in (0., .75, 1.):
        for mode in ('full', 'vertical', 'zero', 'partial'):
            cfg = dict(config, velocity_weight=weight)
            legacy_cfg = dict(original, velocity_weight=weight)
            base_cfg = dict(legacy_cfg)
            base_cfg.pop('recovery')
            new, old, base = make_teacher(cfg), make_teacher(legacy_cfg), make_teacher(base_cfg)
            new.recovery_memory = old.recovery_memory = .8
            for _ in range(100):
                obs = rng.normal(0, .005, 48)
                obs[45:48] = [0, 0, 1] if mode == 'vertical' else [1, 0, 0]
                obs[14] = {'full': .03, 'vertical': .03, 'zero': 0., 'partial': .006}[mode]
                obs[26] = .03
                obs[39:45] = [-8., 1., .5, .02, -.01, 0.]
                for actor in (new, old, base):
                    actor.observe(obs)
                a, b, plain = [actor.act(obs[39:45]) for actor in (new, old, base)]
                assert np.isfinite(a).all() and np.max(np.abs(a)) <= 1.
                for name in ('velocity', 'offset', 'raw_action', 'effective_wrench', 'recovery_memory'):
                    np.testing.assert_array_equal(getattr(new, name), getattr(old, name))
                np.testing.assert_array_equal(a[[0, 1, 2, 4, 5, 6]], b[[0, 1, 2, 4, 5, 6]])
                if mode in ('full', 'vertical'):
                    np.testing.assert_array_equal(a, b)
                else:
                    c = cfg['recovery']
                    intent = 0. if mode == 'zero' else .006/c.get('intent_velocity_mps', .015)
                    activation = old.recovery_memory*intent
                    correction = np.clip(c['gain_per_s']*(c['offset_m']+obs[22])-obs[16], -c['velocity_mps'], c['velocity_mps'])/.32
                    np.testing.assert_allclose(a[3], np.clip((1-activation)*plain[3]+activation*correction, -1, 1), rtol=0, atol=1e-15)
            new.reset()
            assert new.recovery_memory == new.recovery_activation == new.recovery_intent == 0.
            counts[str(weight)+'_'+mode] = 100
    folder = ROOT/'outputs/special_teacher_midpoint_office_20261028_v1/office_v075_avg1'
    audit = read(folder/'AUDIT.json')
    assert sha(folder/'rollout.npz') == audit['trace_sha256']
    old, new = make_teacher(original), make_teacher(config)
    old_actions, new_actions = [], []
    with np.load(folder/'rollout.npz', allow_pickle=False) as trace, np.load(folder/'teacher_internal.npz', allow_pickle=False) as internal:
        for obs in trace['observation']:
            old.observe(obs); new.observe(obs)
            old_actions.append(old.act(obs[39:45]))
            new_actions.append(new.act(obs[39:45]))
        np.testing.assert_array_equal(old_actions, internal['requested_action'])
        n = len(old_actions)
    return dict(status='passed', synthetic_steps=counts, legacy_replay_frames=n,
        legacy_replay_max_abs=0., trace_sha256=audit['trace_sha256'],
        counterfactual_only=True,
        last250_old_z_mean=float(np.array(old_actions)[-250:, 3].mean()),
        last250_new_z_mean=float(np.array(new_actions)[-250:, 3].mean()),
        interpretation='Synthetic and same-history checks prove implementation properties only, not closed-loop stability or physical success.')


def prepare(root):
    assert not root.exists()
    parent = ROOT/'outputs/special_recovery_release005_20261029_v1'
    inactive('sii-special-recovery-release005-v1-20261029.service')
    reg, state = read(parent/'REGISTRATION.json'), read(parent/'execution.json')
    assert state['status'] == 'complete_pending_review' and len(state['episodes']) == 6
    assert state['registration_sha256'] == sha(parent/'REGISTRATION.json')
    cfg = read(ROOT/'outputs/special_teacher_midpoint_20261028_v1/v075_avg1.json')
    assert cfg['velocity_weight'] == .75 and cfg['pair_average'] is True
    assert cfg['recovery']['release_s'] == 1.257675717389726
    cfg['teacher_mechanism'] = VERSION
    checked = actor_checks(cfg)
    root.mkdir(parents=True)
    write(root/'ACTOR_CHECKS.json', checked)
    teacher = root/'teacher_intent_v1.json'
    write(teacher, cfg)
    source = root/'source'
    shutil.copytree(OLD_TEST/'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    original_hashes = {str(p.relative_to(OLD_TEST/'source')):sha(p) for p in (OLD_TEST/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    assert all(sha(source/name) == digest for name, digest in original_hashes.items())
    extensions = ('intent_recovery_teacher_20261029.py', 'intent_teacher_office_driver_20261029.py')
    for name in extensions:
        assert not (source/'tools'/name).exists()
        shutil.copy2(ROOT/'tools'/name, source/'tools'/name)
    # Independent interpreter import must resolve the copied classes, not the
    # live root teacher. Check both real saved history and synthetic semantics.
    check_code = "import sys;from pathlib import Path;root=Path(sys.argv[1]);sys.path[:0]=[str(root/'scripts'),str(root/'tools')];import intent_recovery_teacher_20261029 as m;assert Path(m.LegacyParameterTeacher.__module__.replace('.','/')).name=='optimize_tool_contact_20261002';import optimize_tool_contact_20261002 as o;assert Path(o.__file__).resolve().parent==root/'tools';import json,numpy as np;cfg=json.load(open(sys.argv[2]));a=m.make_teacher(cfg);z=np.load(sys.argv[3]);out=[];[(a.observe(obs),out.append(a.act(obs[39:45]))) for obs in z['observation']];print(__import__('hashlib').sha256(np.array(out).tobytes()).hexdigest())"
    trace = ROOT/'outputs/special_teacher_midpoint_office_20261028_v1/office_v075_avg1/rollout.npz'
    copied_digest = subprocess.check_output([sys.executable, '-c', check_code, str(source), str(teacher), str(trace)], text=True).strip()
    root_digest = subprocess.check_output([sys.executable, '-c', check_code, str(ROOT), str(teacher), str(trace)], text=True).strip()
    assert copied_digest == root_digest
    write(root/'SOURCE_COPY_REVIEW.json', dict(original_files=original_hashes, added=list(extensions), copied_actor_replay_sha256=copied_digest, live_actor_replay_sha256=root_digest))
    cases = copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher), id='intent_'+case.get('identity', 'office000'))
        if case['kind'] == 'office':
            assert case['command'][1].endswith('/baseline_repair_worker_20261008.py')
            case['command'][1] = str(source/'tools/intent_teacher_office_driver_20261029.py')
    successor = {k:copy.deepcopy(reg[k]) for k in ('old_test', 'old_execution_sha256', 'old_completed', 'model_lock_sha256', 'collection_plan_sha256', 'resources', 'action_contract')}
    hashes = {name:sha(ROOT/name) for name in reg['source_sha256']}
    hashes.update({str(Path('tools')/name):sha(ROOT/'tools'/name) for name in (*extensions, Path(__file__).name)})
    hashes.update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*') if p.is_file()})
    successor.update(schema='sii-intent-recovery-finite-controls-v1', registered_utc=now(),
        maximum_episodes=6, cases=cases, source_sha256=hashes,
        config_sha256={str(teacher):sha(teacher)}, actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),
        source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'),
        failed_parent=str(parent), failed_parent_execution_sha256=sha(parent/'execution.json'),
        teacher_mechanism=VERSION, interpretation=__doc__,
        change='Original .75/averaged teacher and original release_s; only recovery blend multiplied by existing canonical horizontal command intent.',
        selection_rule='All five unchanged training qualifications and original office Task/Strict must pass before separately registered new30. Failures retained. No validation tuning, automatic fitting or unseen claim.')
    write(root/'REGISTRATION.json', successor)
    print(root, sha(root/'REGISTRATION.json'), checked)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    (run if args.run else prepare)(args.root.resolve())
