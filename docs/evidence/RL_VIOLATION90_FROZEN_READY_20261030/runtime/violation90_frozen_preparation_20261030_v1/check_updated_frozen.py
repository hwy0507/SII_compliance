"""Finite recorded-input preflight on immutable, actually updated partial90 states."""
from pathlib import Path
import gc, json, os, sys, time, traceback
D = Path(__file__).resolve().parent
B = D.parents[1]
read = lambda p: json.loads(Path(p).read_text())
def put(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
plan = read(D/'PREFLIGHT_PLAN.json')
implementation = read(D/'PREFLIGHT_IMPLEMENTATION.json')
os.sched_setaffinity(0, {plan['cpu']})
os.environ['OMP_NUM_THREADS'] = os.environ['OPENBLAS_NUM_THREADS'] = '1'
sys.path[:0] = [str(D), str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from frozen_helpers import sha, capture_rng, restore_rng, seed_native, ExternalActions, gate
from persisted_history_critic import feature
from persisted_violation_critic import violation_replay_class, KEY as VK
from evaluate_violation90 import validate_architecture
from violation_consumers import restore_learner
from parameter_replay_capacity4m_20261027 import replay_class
from train_published_compliance_20261025 import Replay
from validate_published_finite_check_20261025 import digest
from evaluate_violation90 import validate_recovery
torch.set_num_threads(1)
started = time.monotonic()
try:
    assert sha(__file__) == implementation['script_sha256']
    assert sha(D/'PREFLIGHT_PLAN.json') == implementation['plan_sha256']
    for name, expected in plan['sources'].items():
        assert sha(D/name) == expected, name
    results = {}
    for method, reg in plan['actual_updated_startup_snapshots'].items():
        assert time.monotonic()-started < plan['budget_seconds']
        saved = reg['software_preflight_snapshot']
        assert sha(saved['path']) == saved['sha256']
        ck = torch.load(saved['path'], map_location='cpu', weights_only=False)
        binding = reg['violation_binding']
        assert ck['controller'] == method and ck['steps'] > binding['rows']
        assert sha(reg['training_registration']) == reg['training_registration_sha256']
        protocol = read(reg['training_registration'])
        assert ck['protocol_sha256'] == reg['training_registration_sha256']
        validate_architecture(ck, protocol)
        rejected = False
        try:
            validate_recovery(ck, protocol, 90)
        except AssertionError:
            rejected = True
        assert rejected, 'Actual partial90 incorrectly accepted as a complete90 checkpoint'
        assert ck['boundary'] != 'complete_condition_cycle'
        learner = restore_learner(ck['learner'], binding, Path(reg['runtime']), plan['device'], ck['seed'])
        initial = digest(ck['learner'])
        assert digest(learner.state_dict()) == initial
        replay = violation_replay_class(replay_class(Replay), binding)(binding['action_dimension'], 52, 2026102638)
        replay.load_state_dict(ck['replay'])
        rd = digest(ck['replay'])
        assert digest(replay.state_dict()) == rd
        agent = learner.learner.agent
        learned = {}
        for label, ensemble in [('online', agent.ensemble), ('target', agent.ensemble_targets)]:
            values = [float(q.q_net[0].weight[:,51].abs().max()) for q in ensemble]
            assert all(v > 0 for v in values)
            learned[label+'_bit_weight_absmax'] = values
        for key in ['exp_avg', 'exp_avg_sq']:
            values = [float(learner.learner.q_optimizer.state[q.q_net[0].weight][key][:,51].abs().max()) for q in agent.ensemble]
            assert all(v > 0 for v in values)
            learned[key+'_bit_absmax'] = values
        ep = implementation['episodes'][method]
        assert sha(ep['journal']) == ep['journal_sha256']
        assert sha(ep['terminal']) == ep['terminal_sha256']
        rows = [json.loads(line) for line in Path(ep['journal']).read_text().splitlines()]
        terminal = read(ep['terminal'])
        assert len(rows) == 1375 and rows[0]['interval'] is None
        rng_before = digest(capture_rng(learner))
        gate_review = gate(learner, ck, rows[:3], reg['action_seed'], ep['condition'], digest)
        assert digest(capture_rng(learner)) == rng_before
        outputs, terminal_outputs = [], []
        for native in [True, False]:
            original = capture_rng(learner)
            try:
                if native:
                    seed_native(learner, reg['action_seed'], ep['condition'])
                    learner.reset_episode()
                    call = lambda *args, **kwargs: learner.act(*args, **kwargs)
                else:
                    external = ExternalActions(learner, reg['action_seed'], ep['condition'])
                    external.call(learner.reset_episode)
                    call = lambda *args, **kwargs: external.call(learner.act, *args, **kwargs)
                sequence = []
                for i, row in enumerate(rows):
                    assert time.monotonic()-started < plan['budget_seconds']
                    learner.consume_interval(row['interval'])
                    result = call(row['observation'], step=ck['steps'], deterministic=False)
                    obs = result[0]
                    peak = 0. if row['interval'] is None else row['interval']['external_penetration_peak_m']
                    assert obs.shape == (52,) and obs[49] == np.float32((1375-i)/1375)
                    assert obs[50] == feature(peak) and obs[51] == float(peak > .0002)
                    sequence.append(result)
                learner.consume_interval(terminal['interval'])
                assert learner.episode_actions == learner.history_intervals == {0:1375}
                term_obs = learner.terminal_observation(sequence[-1][0])
                assert term_obs[49] == 0 and term_obs[50] == feature(terminal['interval']['external_penetration_peak_m'])
                assert term_obs[51] == float(terminal['interval']['external_penetration_peak_m'] > .0002)
                terminal_outputs.append(term_obs)
                outputs.append(sequence)
            finally:
                restore_rng(learner, original)
            assert digest(learner.state_dict()) == initial
            assert digest(capture_rng(learner)) == rng_before
        assert digest(outputs[0]) == digest(outputs[1])
        np.testing.assert_array_equal(*terminal_outputs)
        obs = torch.as_tensor(np.stack([r[0] for r in outputs[0]]), device=learner.device)
        bits = obs[:,51].cpu().numpy();assert set(bits.tolist()) == {0.,1.}
        alt = obs.clone()
        alt[:,49:] = 1-alt[:,49:]
        with torch.no_grad():
            assert digest(agent.actor(obs)) == digest(agent.actor(alt))
        assert digest(learner.state_dict()) == initial
        assert digest(capture_rng(learner)) == rng_before
        assert digest(replay.state_dict()) == rd == digest(ck['replay'])
        assert sha(saved['path']) == saved['sha256']
        result = dict(passed=True, snapshot=saved, partial_steps=ck['steps'],
            new_steps=ck['steps']-binding['rows'], learned_bit=learned,
            recorded_case=ep, gate=gate_review, raw_bit_zero_count=int((bits==0).sum()),raw_bit_one_count=int((bits==1).sum()), full1375_native_external_exact=True,
            terminal_history_and_bit_exact=True, actor49_isolation_all1375_exact=True,
            actual_partial_rejected_as_complete90=True, full_learner_restore_unchanged=True,
            full_replay_restore_unchanged=True, global_and_local_rng_unchanged=True,
            full_learner_digest=initial, replay_digest=rd,
            sequence_digest=digest(outputs[0]), native_actions=2757,
            physical_steps=0, optimizer_updates=0, replay_writes=0)
        put(D/(method+'_UPDATED_FROZEN_REVIEW.json'), result)
        results[method] = result
        print('PASSED', method, ck['steps'], flush=True)
        del learner, replay, ck, agent, obs, alt, outputs, sequence, call
        gc.collect()
        torch.cuda.empty_cache()
    put(D/'UPDATED_FROZEN_REVIEW.json', dict(passed=True, methods=results,
        elapsed_s=time.monotonic()-started, maximum_actions=8271,
        physical_steps=0, optimizer_updates=0, replay_writes=0,
        scope='Recorded inputs from89 with updated partial90 weights; no physical performance result or complete90 approval'))
except BaseException as exc:
    put(D/('PREFLIGHT_FAILURE_'+str(time.time_ns())+'.json'),
        dict(error=repr(exc), traceback=traceback.format_exc(), elapsed_s=time.monotonic()-started))
    raise
