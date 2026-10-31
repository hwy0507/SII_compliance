"""Frozen complete90 parameter policies on all30 registered training conditions.

One external action seed per method; no optimization or formal replay writes.
Reuse the independently exercised external RNG and native replay implementation
from the completed frozen29 diagnostic, whose source is pinned in registration.
"""
from pathlib import Path
import argparse
import json
import os
import selectors
import subprocess
import sys
import time
from frozen_helpers import (
    sha, write, ExternalActions, gate, review_episode,
)


def validate_architecture(ck, protocol):
    from persisted_history_critic import KEY as HK, marker as hm
    from persisted_violation_critic import KEY as VK, marker as vm
    h = protocol['history_critic_amendment'];v = protocol['violation_critic_amendment'];b = v['binding']
    assert h['first_cycle'] == 88 and v['first_cycle'] == 90 and b['history_binding'] == h['binding']
    assert ck['history_critic_amendment'] == h and ck['violation_critic_amendment'] == v
    assert ck['controller'] == b['method'] and ck['cycle'] == 90 and ck['seed'] == 20261025
    assert b['rows'] < ck['steps'] <= b['rows']+41250
    for key in ['learner','replay']:
        assert ck[key][HK] == hm(h['binding']) and ck[key][VK] == vm(b)
    assert ck['environment_state_saved'] is False
    assert ck['interruption_recovery'] == protocol['interrupted_episode_recovery']
    assert ck['recovery_continuation'] == protocol['post_interruption_continuation']
    assert ck['replay']['size'] == ck['replay']['cursor'] == ck['steps']
    for key in ['observations','next_observations']:
        assert ck['replay']['arrays'][key].shape == (ck['steps'],52)


def validate_recovery(ck, protocol, expected_cycle):
    validate_architecture(ck, protocol)
    assert expected_cycle in (90,)
    assert ck['cycle'] == expected_cycle and ck['boundary'] == 'complete_condition_cycle'
    assert ck['environment_state_saved'] is False
    assert ck['interruption_recovery'] == protocol['interrupted_episode_recovery']
    assert ck['recovery_continuation'] == protocol['post_interruption_continuation']
    stage = protocol['post_interruption_continuation']
    assert stage['parent_cycle'] == expected_cycle - 1 and stage['new_cycle'] == expected_cycle
    assert stage['new_cycles'] == 1 and stage['maximum_new_actions'] == 41250
    assert stage['automatic_followup'] is False and stage['optimizer_settings_changed'] is False
    assert all(c['cycle'] != 75 for c in ck['cycles']) and ck['cycles'][-1]['cycle'] == expected_cycle


def main(registration, check_only, expected_cycle=90):
    if expected_cycle != 90 and not check_only:
        raise ValueError("Only planned90 may execute physics; validation89 is check-only")
    if expected_cycle not in (90,):
        raise ValueError("Unregistered parent cycle")
    reg = json.loads(registration.read_text())
    os.sched_setaffinity(0, {reg['cpu']})
    os.nice(10)
    import numpy as np
    import torch
    torch.set_num_threads(1)
    root, output = Path(reg['runtime']), registration.parent
    runtime = Path(reg['audit_runtime'])
    for name, expected in reg['source_hashes'].items():
        assert sha(runtime/name) == expected, name
    assert reg['parent_cycle'] == expected_cycle
    assert len(reg['case_ids']) == len(set(reg['case_ids'])) == 30
    assert reg['action_seed'] == 2026102638
    assert sha(reg['checkpoint']) == reg['checkpoint_sha256']
    assert sha(reg['training_registration']) == reg['training_registration_sha256']
    protocol = json.loads(Path(reg['training_registration']).read_text())
    assert protocol['runtime'] == str(root) and sha(root/'RUNTIME.json') == protocol['runtime_sha256']
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        assert sha(root/'source'/name) == expected, name
    assert sha(protocol['reference_plan']) == protocol['reference_plan_sha256']
    assert reg['case_ids'] == [c['id'] for c in protocol['conditions']]
    conditions = {c['id']: c for c in protocol['conditions']}
    for condition in conditions.values():
        assert sha(condition['path']) == condition['sha256']
    review = json.loads(Path(reg['required_review']).read_text())
    assert sha(reg['required_review']) == reg['required_review_sha256'] and review['passed']
    assert review['methods'][reg['controller']]['checkpoint_sha256'] == reg['checkpoint_sha256']
    sys.path[:0] = [str(runtime), str(root/'source/tools')]
    from published_compliance_learner_20261025 import PublishedLearner
    from published_pair_reduction_learner_20261026 import pair_class, marker
    from parameter_replay_capacity_20261026 import MARKER
    from parameter_replay_capacity4m_20261027 import replay_class, MARKER as FOLLOWUP_MARKER
    from train_published_compliance_20261025 import Replay
    from validate_published_finite_check_20261025 import digest
    ck = torch.load(reg['checkpoint'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == expected_cycle and ck['boundary'] == 'complete_condition_cycle'
    assert ck['controller'] == reg['controller'] and ck['protocol_sha256'] == sha(reg['training_registration'])
    validate_recovery(ck, protocol, expected_cycle)
    assert ck['replay']['replay_capacity_extension'] == MARKER
    assert protocol['replay_capacity_stage']['parent_cycle'] == 23
    followup = protocol['replay_capacity_followup_stage']
    assert followup['parent_cycle'] == 47 and followup['marker'] == FOLLOWUP_MARKER
    assert followup['new_capacity'] == 4_000_000 and followup['old_capacity'] == 2_000_000
    assert sha(runtime/'parameter_replay_capacity4m_20261027.py') == followup['helper_sha256']
    assert sha(followup['entry_checkpoint']['path']) == followup['entry_checkpoint']['sha256']
    assert ck['replay']['capacity'] == 4_000_000
    assert ck['replay']['replay_capacity_followup'] == FOLLOWUP_MARKER
    from persisted_history_critic import history_class, marker as history_marker, KEY
    from persisted_violation_critic import violation_class, violation_replay_class
    vb = protocol['violation_critic_amendment']['binding']
    binding = protocol['history_critic_amendment']['binding']
    assert ck['history_critic_amendment'] == protocol['history_critic_amendment']
    assert ck['learner'][KEY] == ck['replay'][KEY] == history_marker(binding)
    replay = violation_replay_class(replay_class(Replay), vb)(ck['replay']['arrays']['actions'].shape[1], 52, 2026102638)
    replay.load_state_dict(ck['replay'])
    replay_digest = digest(replay.state_dict())
    assert replay_digest == digest(ck['replay'])
    reduction = {'impedance': 'minimum', 'admittance': 'mean', 'vmc': 'mean'}[reg['controller']]
    assert ck['learner']['target_pair_reduction'] == marker(reduction)
    dimension = json.loads((root/'parameter/PRIORS.json').read_text())['methods'][reg['controller']]['action_dimension']
    learner = violation_class(history_class(pair_class(PublishedLearner, reduction), binding), vb)(root, dimension=dimension, direct=False,
        seed=ck['seed'], device=reg['device'], algorithm='cheq', critic_layer_norm=True,
        numerical_amendments=True, critic_clock=True)
    learner.load_state_dict(ck['learner'])
    initial = digest(learner.state_dict())
    assert initial == digest(ck['learner'])
    journal = Path(reg['gate_observations'])
    assert sha(journal) == reg['gate_observations_sha256']
    with journal.open() as stream:
        observations = [json.loads(next(stream)) for _ in range(3)]
    result = gate(learner, ck, observations, reg['action_seed'], reg['gate_case_id'], digest)
    result.update(full_replay_restored_exact=True, replay_digest=replay_digest,
                  full_learner_digest=initial, checkpoint_sha256=sha(reg['checkpoint']),
                  replay_capacity=4_000_000, historical_entry_cycle=23, followup_entry_cycle=47, validated_parent_cycle=expected_cycle)
    write(output/('CHECK_ONLY_REVIEW.json' if check_only else 'STARTUP_REVIEW.json'), result)
    if check_only:
        assert digest(replay.state_dict()) == replay_digest
        assert digest(learner.state_dict()) == initial and sha(reg['checkpoint']) == reg['checkpoint_sha256']
        return
    assert json.loads((output/'CHECK_ONLY_REVIEW.json').read_text())['passed']
    launch = json.loads((output.parent/'LAUNCH_AUTHORIZATION.json').read_text())
    assert launch['parent_cycle'] == 90 and launch['registration_hashes'][reg['controller']] == sha(registration)
    assert launch['episodes'] == 90 and launch['maximum_actions'] == 123750 and launch['optimizer_updates'] == 0
    assert not (output/'EVALUATION.json').exists()
    write(output/'EVALUATION.json', dict(registration_sha256=sha(registration),
        checkpoint_sha256=sha(reg['checkpoint']), action_seed=reg['action_seed'], case_ids=reg['case_ids'],
        full_learner_digest=initial, full_replay_digest=replay_digest, expected_episodes=30,
        maximum_actions=41250, maximum_substeps=33000000, optimizer_updates=0,
        scope='Prospectively selected complete90 frozen policy on all30 training conditions, one external action seed; not independent training seeds, held-out tests or final ESN comparison'))
    results = []
    seed = reg['action_seed']
    for case in reg['case_ids']:
        condition = conditions[case]
        assert digest(learner.state_dict()) == initial
        external = ExternalActions(learner, seed, case)
        external.call(learner.reset_episode)
        folder = output/case
        command = ['taskset', '-c', str(reg['cpu']), sys.executable,
            str(runtime/'audit_published_episode_20261025.py'), '--runtime', str(root),
            '--output', str(folder), '--fixture', condition['path'], '--reference-plan',
            protocol['reference_plan'], '--controller', reg['controller'], '--ipc']
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
                   OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MUJOCO_GL='disable')
        with (output/f'{case}.stderr.log').open('x') as log:
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=log, text=True, bufsize=1, env=env)
            write(output/'CURRENT_PHYSICS.json', dict(pid=child.pid, seed=seed, condition=case, time=time.time(), command=command))
            selector = selectors.DefaultSelector()
            selector.register(child.stdout, selectors.EVENT_READ)
            actions = 0
            try:
                while True:
                    if not selector.select(timeout=600):
                        raise TimeoutError('No physics event for600seconds')
                    line = child.stdout.readline()
                    if not line:
                        raise RuntimeError('Physics exited before terminal')
                    event = json.loads(line)
                    if event['kind'] == 'error':
                        raise RuntimeError(event['error'])
                    learner.consume_interval(event['interval'])
                    if event['kind'] == 'terminal':
                        assert event['model_sha256'] == condition['model_sha256']
                        assert child.wait(timeout=60) == 0
                        break
                    assert event['kind'] == 'observation' and actions < 1375
                    if actions == 0:
                        assert sha(folder/'rollout.mjb') == condition['model_sha256']
                    _, _, action, _ = external.call(learner.act, event['observation'],
                                                   step=ck['steps'], deterministic=False)
                    child.stdin.write(json.dumps(dict(action=action.tolist()))+'\n')
                    child.stdin.flush()
                    actions += 1
                    if actions % 100 == 0:
                        write(output/'PROGRESS.json', dict(seed=seed, actions=actions,
                            completed_conditions=len(results), condition=case, physics_pid=child.pid, time=time.time()))
            finally:
                child.stdin.close()
                selector.close()
                try:
                    child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    child.wait(timeout=30)
        assert digest(learner.state_dict()) == initial
        reviewed = review_episode(learner, ck, seed, case, folder, digest)
        assert reviewed['actions'] == actions
        write(output/f'{case}_REVIEW.json', reviewed)
        results.append(reviewed)
        write(output/'RESULTS.json', dict(episodes=results, completed=len(results), expected=30))
    assert digest(learner.state_dict()) == initial
    assert digest(replay.state_dict()) == replay_digest
    assert sha(reg['checkpoint']) == reg['checkpoint_sha256']
    for name, expected in reg['source_hashes'].items():
        assert sha(runtime/name) == expected
    write(output/'FINISHED.json', dict(passed=True, time=time.time(), episodes=30,
        actions=sum(r['actions'] for r in results), substeps=sum(r['physical']['samples'] for r in results),
        task=sum(r['physical']['row']['task_success'] for r in results),
        strict=sum(r['physical']['row']['strict_success'] for r in results),
        full_learner_state_unchanged=True, full_replay_state_unchanged=True,
        initial_learner_digest=initial, final_learner_digest=digest(learner.state_dict()),
        new_optimizer_updates=0, convergence_claim=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--validation-cycle', type=int, choices=[90], default=90)
    args = parser.parse_args()
    try:
        main(args.registration, args.check_only, args.validation_cycle)
    except BaseException as error:
        write(args.registration.parent/('CHECK_ONLY_FAILURE.json' if args.check_only else 'FAILURE.json'),
              dict(time=time.time(), error=repr(error)))
        raise
