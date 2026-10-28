"""Independent reachability, rate, energy, and old-map compatibility checks."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parameter-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(root/'scripts'), str(args.parameter_source)]
    from baseline_fullrange_controllers_20261009 import ParameterShield, full_range_target
    from baseline_repair_controllers_20261008 import ParameterShield as OldShield
    priors = json.loads((args.parameter_source/'PRIORS.json').read_text())['methods']
    rng = np.random.default_rng(2026100901)
    report = {}
    for method, prior in priors.items():
        center = np.asarray(prior['center']); bounds = np.asarray(prior['bounds']); n = len(center)
        for action, expected in ((-np.ones(n), bounds[:, 0]), (np.zeros(n), center), (np.ones(n), bounds[:, 1])):
            np.testing.assert_allclose(full_range_target(action, center, bounds), expected, rtol=1e-14)
        for sign in (-1., 1.):
            shield = ParameterShield(method, prior)
            for _ in range(300):
                shield.update(np.full(n, sign), np.zeros(6), np.zeros(6))
            np.testing.assert_allclose(shield.theta, bounds[:, int(sign > 0)], rtol=1e-12)
        shield, old = ParameterShield(method, prior), OldShield(method, prior)
        compatibility_error = 0.
        for _ in range(300):
            # Both maps request the same physical target in their common range.
            old_action = rng.uniform(-.6, .6, n)
            target = np.clip(center * np.exp(old_action * prior['action_log_span']), bounds[:, 0], bounds[:, 1])
            log_ratio = np.log(target / center)
            spans = np.where(log_ratio >= 0, np.log(bounds[:, 1] / center), np.log(center / bounds[:, 0]))
            action = np.divide(log_ratio, spans, out=np.zeros(n), where=spans != 0)
            offset, velocity = rng.normal(0, .01, 6), rng.normal(0, .015, 6)
            new_theta = shield.update(action, offset, velocity)
            old_theta = old.update(old_action, offset, velocity)
            compatibility_error = max(compatibility_error, float(np.max(abs(new_theta-old_theta))))
            np.testing.assert_allclose(new_theta, old_theta, rtol=2e-11, atol=1e-11)
            np.testing.assert_allclose(shield.energy, old.energy, atol=1e-10)
        shield = ParameterShield(method, prior); tank_limited = 0
        for _ in range(1000):
            before, energy = shield.theta.copy(), shield.energy
            offset, velocity = rng.normal(0, .08, 6), rng.normal(0, .03, 6)
            shield.update(rng.uniform(-1, 1, n), offset, velocity)
            record = shield.records[-1]
            assert np.all(shield.theta >= bounds[:, 0]-1e-10) and np.all(shield.theta <= bounds[:, 1]+1e-10)
            assert np.max(abs(np.log(shield.theta/before))) <= prior['max_log_rate_per_s']*.04+1e-12
            assert shield.minimum-1e-10 <= shield.energy <= shield.maximum+1e-10
            added = shield.energy_at(shield.theta, offset, velocity)-shield.energy_at(before, offset, velocity)
            assert added <= energy+record['recharge_j']-shield.minimum+1e-9
            tank_limited += int(record['energy_scale'] < .99999)
        assert tank_limited > 0, 'Energy limiter not exercised'
        report[method] = dict(endpoints_reachable_at_zero_storage=True, unchanged_log_rate=True,
            tank_limited_steps=tank_limited, compatibility_max_abs=compatibility_error,
            old_reachable_low=np.maximum(bounds[:, 0], center/2).tolist(),
            old_reachable_high=np.minimum(bounds[:, 1], center*2).tolist(),
            full_low=bounds[:, 0].tolist(), full_high=bounds[:, 1].tolist())
    result = dict(status='passed', physics_steps=0, methods=report,
        limitation='Parameter-space coverage and local tank only; not closed-loop success or global passivity')
    with args.output.open('x') as file:
        json.dump(result, file, indent=2, allow_nan=False); file.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
