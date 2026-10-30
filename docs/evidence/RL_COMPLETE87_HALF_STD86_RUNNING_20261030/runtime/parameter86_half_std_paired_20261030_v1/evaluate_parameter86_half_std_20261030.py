"""Finite fixed86 paired intervention: pre-tanh Gaussian sampling std multiplied by0.5.

Same four groups and four external seeds as completed baseline; no updates or replay writes.
Serialized learner state is unchanged; the actor sampling distribution intentionally changes.
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
from half_std_probe import install_probe
from evaluate_parameter29_seeded_switch_20261026 import (
    sha, write, ExternalActions, gate, review_episode,
)


def validate_recovery(ck, protocol, expected_cycle):
    assert expected_cycle == 86
    assert ck['cycle'] == expected_cycle and ck['boundary'] == 'complete_condition_cycle'
    assert ck['environment_state_saved'] is False
    assert ck['interruption_recovery'] == protocol['interrupted_episode_recovery']
    assert ck['recovery_continuation'] == protocol['post_interruption_continuation']
    stage = protocol['post_interruption_continuation']
    assert stage['parent_cycle'] == expected_cycle - 1 and stage['new_cycle'] == expected_cycle
    assert stage['new_cycles'] == 1 and stage['maximum_new_actions'] == 41250
    assert stage['automatic_followup'] is False and stage['optimizer_settings_changed'] is False
    assert all(c['cycle'] != 75 for c in ck['cycles']) and ck['cycles'][-1]['cycle'] == expected_cycle


SEEDS = [2026102633, 2026102634, 2026102635, 2026102636]
GROUPS = {
    'impedance_short0600': ('impedance', 'active_short_train_0600', 7),
    'admittance_short0900': ('admittance', 'active_short_train_0900', 8),
    'admittance_long0200': ('admittance', 'active_long_train_0200', 9),
    'vmc_short0000': ('vmc', 'active_short_train_0000', 10),
}

def validate_design(reg):
    plan_path = Path(reg['plan'])
    assert sha(plan_path) == reg['plan_sha256']
    plan = json.loads(plan_path.read_text())
    assert plan['parent_cycle'] == reg['parent_cycle'] == 86
    assert plan['action_seeds'] == reg['action_seeds'] == SEEDS
    assert plan['episodes'] == 16 and plan['maximum_actions'] == 22000
    assert plan['maximum_substeps'] == 17600000 and plan['optimizer_updates'] == 0
    assert plan['automatic_extension'] is False
    assert set(plan['groups']) == set(GROUPS)
    for key, (method, case, cpu) in GROUPS.items():
        group = plan['groups'][key]
        assert group['controller'] == method and group['case_ids'] == [case] and group['cpu'] == cpu
    entry = plan['groups'][reg['group']]
    for key in ['controller', 'case_ids', 'cpu', 'device', 'checkpoint', 'checkpoint_sha256',
                'training_registration', 'training_registration_sha256', 'required_review',
                'required_review_sha256', 'gate_observations', 'gate_observations_sha256',
                'gate_case_id', 'runtime', 'audit_runtime', 'source_hashes']:
        assert reg[key] == entry[key], key
    assert reg['gate_case_id'] == reg['case_ids'][0]
    assert reg['pre_tanh_std_factor'] == plan['pre_tanh_std_factor'] == .5
    for entry in plan['baseline_inputs'].values():assert sha(entry['path']) == entry['sha256']


def main(registration, check_only, expected_cycle=86):
    if expected_cycle != 86:
        raise ValueError("Only registered complete86 is allowed")
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
    validate_design(reg)
    assert sha(reg['checkpoint']) == reg['checkpoint_sha256']
    assert sha(reg['training_registration']) == reg['training_registration_sha256']
    protocol = json.loads(Path(reg['training_registration']).read_text())
    assert protocol['runtime'] == str(root) and sha(root/'RUNTIME.json') == protocol['runtime_sha256']
    for name, expected in json.loads((root/'SOURCE_HASHES.json').read_text()).items():
        assert sha(root/'source'/name) == expected, name
    assert sha(protocol['reference_plan']) == protocol['reference_plan_sha256']
    assert reg['case_ids'][0] in [c['id'] for c in protocol['conditions']]
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
    replay = replay_class(Replay)(ck['replay']['arrays']['actions'].shape[1], 50, 2026102638)
    replay.load_state_dict(ck['replay'])
    replay_digest = digest(replay.state_dict())
    assert replay_digest == digest(ck['replay'])
    reduction = {'impedance': 'minimum', 'admittance': 'mean', 'vmc': 'mean'}[reg['controller']]
    assert ck['learner']['target_pair_reduction'] == marker(reduction)
    dimension = json.loads((root/'parameter/PRIORS.json').read_text())['methods'][reg['controller']]['action_dimension']
    learner = pair_class(PublishedLearner, reduction)(root, dimension=dimension, direct=False,
        seed=ck['seed'], device=reg['device'], algorithm='cheq', critic_layer_norm=True,
        numerical_amendments=True, critic_clock=True)
    learner.load_state_dict(ck['learner'])
    initial = digest(learner.state_dict())
    assert initial == digest(ck['learner'])
    journal = Path(reg['gate_observations'])
    assert sha(journal) == reg['gate_observations_sha256']
    with journal.open() as stream:
        observations = [json.loads(next(stream))['observation'] for _ in range(3)]
    probe = install_probe(learner, observations, digest)
    write(output/('CHECK_ONLY_PROBE.json' if check_only else 'STARTUP_PROBE.json'), probe)
    result = gate(learner, ck, observations, reg['action_seeds'][0], reg['gate_case_id'], digest)
    result.update(full_replay_restored_exact=True, replay_digest=replay_digest,
                  full_learner_digest=initial, checkpoint_sha256=sha(reg['checkpoint']),
                  replay_capacity=4_000_000, historical_entry_cycle=23, followup_entry_cycle=47, validated_parent_cycle=expected_cycle)
    write(output/('CHECK_ONLY_REVIEW.json' if check_only else 'STARTUP_REVIEW.json'), result)
    if check_only:
        assert digest(replay.state_dict()) == replay_digest
        return
    assert json.loads((output/'CHECK_ONLY_REVIEW.json').read_text())['passed']
    assert not (output/'EVALUATION.json').exists()
    write(output/'EVALUATION.json', dict(registration_sha256=sha(registration),
        checkpoint_sha256=sha(reg['checkpoint']), action_seeds=reg['action_seeds'], case_ids=reg['case_ids'],
        full_learner_digest=initial, full_replay_digest=replay_digest, expected_episodes=4,
        maximum_actions=5500, maximum_substeps=4400000, optimizer_updates=0,
        scope='Paired inference intervention: same fixed86 weights/groups/seeds, pre-tanh Gaussian std factor0.5. Serialized state unchanged but policy sampler intentionally changed. Not a training entropy intervention or convergence claim'))
    results = []
    case = reg['case_ids'][0]
    for seed in reg['action_seeds']:
        condition = conditions[case]
        assert digest(learner.state_dict()) == initial
        external = ExternalActions(learner, seed, case)
        external.call(learner.reset_episode)
        folder = output/f'seed_{seed}'
        command = ['taskset', '-c', str(reg['cpu']), sys.executable,
            str(runtime/'audit_published_episode_20261025.py'), '--runtime', str(root),
            '--output', str(folder), '--fixture', condition['path'], '--reference-plan',
            protocol['reference_plan'], '--controller', reg['controller'], '--ipc']
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
                   OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', MUJOCO_GL='disable')
        with (output/f'seed_{seed}.stderr.log').open('x') as log:
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
                            completed_episodes=len(results), condition=case, physics_pid=child.pid, time=time.time()))
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
        write(output/f'seed_{seed}_REVIEW.json', reviewed)
        results.append(reviewed)
        write(output/'RESULTS.json', dict(episodes=results, completed=len(results), expected=4))
    assert digest(learner.state_dict()) == initial
    assert digest(replay.state_dict()) == replay_digest
    assert sha(reg['checkpoint']) == reg['checkpoint_sha256']
    for name, expected in reg['source_hashes'].items():
        assert sha(runtime/name) == expected
    write(output/'FINISHED.json', dict(passed=True, time=time.time(), episodes=4,
        actions=sum(r['actions'] for r in results), substeps=sum(r['physical']['samples'] for r in results),
        task=sum(r['physical']['row']['task_success'] for r in results),
        strict=sum(r['physical']['row']['strict_success'] for r in results),
        full_learner_state_unchanged=True, full_replay_state_unchanged=True,
        initial_learner_digest=initial, final_learner_digest=digest(learner.state_dict()),
        new_optimizer_updates=0, convergence_claim=False, pre_tanh_std_factor=.5, sampling_distribution_intentionally_changed=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--validation-cycle', type=int, choices=[86], default=86)
    args = parser.parse_args()
    try:
        main(args.registration, args.check_only, args.validation_cycle)
    except BaseException as error:
        write(args.registration.parent/('CHECK_ONLY_FAILURE.json' if args.check_only else 'FAILURE.json'),
              dict(time=time.time(), error=repr(error)))
        raise
