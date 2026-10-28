"""Independent arithmetic and saved-history checks; no physical success claim."""
import argparse
import copy
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from intent_equilibrium_teacher_20261029 import VERSION, IntentEquilibriumTeacher
from intent_recovery_teacher_20261029 import LegacyParameterTeacher


def check():
    cfg = read(ROOT/'outputs/special_teacher_midpoint_20261028_v1/v075_avg1.json')
    rng = np.random.default_rng(2026102902)
    count = 0
    for weight in (0., .75, 1.):
        for horizontal in (0., .5, 1.):
            for command in (0., .006, .03):
                config = dict(cfg, velocity_weight=weight)
                new = IntentEquilibriumTeacher(dict(config, teacher_mechanism=VERSION))
                old = LegacyParameterTeacher(config)
                base_config = copy.deepcopy(config)
                base_config.pop('recovery')
                base = LegacyParameterTeacher(base_config)
                new.recovery_memory = old.recovery_memory = .8
                for _ in range(100):
                    obs = rng.normal(0, .005, 48)
                    obs[45:48] = [horizontal, 0., np.sqrt(1-horizontal**2)]
                    obs[14], obs[26] = command, .03
                    obs[39:45] = [-8., 1., .5, .02, -.01, 0.]
                    for actor in (old, new, base):
                        actor.observe(obs)
                    original, actual, plain = [actor.act(obs[39:45]) for actor in (old, new, base)]
                    for name in ('velocity', 'offset', 'filtered', 'raw_action', 'effective_wrench', 'recovery_memory'):
                        np.testing.assert_array_equal(getattr(new, name), getattr(old, name))
                    np.testing.assert_array_equal(actual[[0,1,2,4,5,6]], original[[0,1,2,4,5,6]])
                    c = config['recovery']
                    intent = np.clip(command/c.get('intent_velocity_mps', .015), 0, 1)*horizontal**2
                    activation = old.recovery_memory*horizontal**2
                    feedback = c['gain_per_s']*obs[22]-obs[16]
                    offset = c['gain_per_s']*c['offset_m']*intent
                    correction = np.clip(feedback+offset, -c['velocity_mps'], c['velocity_mps'])/.32
                    expected = np.clip((1-activation)*plain[3]+activation*correction, -1, 1)
                    np.testing.assert_allclose(actual[3], expected, rtol=0, atol=1e-15)
                    if horizontal == 0 or intent == 1:
                        np.testing.assert_array_equal(actual, original)
                    assert np.isfinite(actual).all() and np.max(np.abs(actual)) <= 1.
                    count += 1
                new.reset()
                assert new.recovery_memory == new.recovery_intent == new.recovery_activation == 0.
    return dict(status='passed', synthetic_steps=count, original_dynamics_and_memory_preserved=True,
                non_z_action_preserved=True, full_intent_and_vertical_exact=True,
                partial_intent_independent_feedback_plus_offset_arithmetic=True,
                reset_finite_bounds=True,
                config=dict(cfg, teacher_mechanism=VERSION),
                source_sha256={name:sha(ROOT/'tools'/name) for name in (
                    'intent_equilibrium_teacher_20261029.py', 'optimize_tool_contact_20261002.py', Path(__file__).name)},
                physical_tested=False, limitation='Mathematical implementation checks, not a closed-loop stability proof. No new physical trials or fitting.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write(args.output, result)
    print(result)
