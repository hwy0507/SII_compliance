"""Full legal-range parameter actions, preserving the existing rate/tank limits.

This is a separately named baseline variant. Historical factor-two mapping and
all its results remain intact. Zero still requests the fixed controller centre.
No actor field, physical scene, nominal planner, or actuator limit is changed.
"""
import numpy as np
import baseline_repair_controllers_20261008 as repaired


def full_range_target(action, center, bounds):
    action, center, bounds = (np.asarray(x, dtype=float) for x in (action, center, bounds))
    if (center.ndim != 1 or action.shape != center.shape or bounds.shape != (len(center), 2)
            or not all(np.isfinite(x).all() for x in (action, center, bounds))
            or np.any(np.abs(action) > 1.000001) or np.any(bounds <= 0)
            or np.any(bounds[:, 0] >= bounds[:, 1])
            or np.any(center < bounds[:, 0]) or np.any(center > bounds[:, 1])):
        raise ValueError('Finite bounded action and positive ordered bounds containing centre required')
    action = np.clip(action, -1., 1.)
    span = np.where(action >= 0, np.log(bounds[:, 1] / center), np.log(center / bounds[:, 0]))
    target = np.exp(np.log(center) + action * span)
    return np.clip(target, bounds[:, 0], bounds[:, 1])


class ParameterShield(repaired.ParameterShield):
    def update(self, action, offset, velocity, dt=.04):
        offset, velocity = np.asarray(offset, float), np.asarray(velocity, float)
        if (offset.shape != (6,) or velocity.shape != (6,)
                or not np.isfinite(offset).all() or not np.isfinite(velocity).all()
                or not np.isfinite(dt) or dt <= 0):
            raise ValueError('Finite storage state and positive dt required')
        requested_target = full_range_target(action, self.center, self.bounds)
        old = self.theta.copy()
        rate = float(self.prior['max_log_rate_per_s'])
        if not np.isfinite(rate) or rate <= 0:
            raise ValueError('Positive finite log rate required')
        target = np.exp(np.log(old) + np.clip(np.log(requested_target / old), -rate * dt, rate * dt))
        target = np.clip(target, self.bounds[:, 0], self.bounds[:, 1])
        before = self.energy
        _, _, damping = repaired.vectors(self.method, old)
        recharge = min(self.maximum - self.energy, .2 * float(np.sum(damping * velocity**2)) * dt)
        self.energy += recharge
        available = self.energy - self.minimum
        u0 = self.energy_at(old, offset, velocity)

        def candidate(alpha):
            return np.exp(np.log(old) + alpha * (np.log(target) - np.log(old)))

        def cost(alpha):
            return self.energy_at(candidate(alpha), offset, velocity) - u0

        requested, alpha = cost(1.), 1.
        if requested > available:
            lo, hi = 0., 1.
            for _ in range(45):
                mid = (lo + hi) / 2
                if cost(mid) <= available:
                    lo = mid
                else:
                    hi = mid
            alpha = lo
        self.theta = candidate(alpha)
        change = self.energy_at(self.theta, offset, velocity) - u0
        debit = max(change, 0.)
        credit = min(max(-change, 0.), self.maximum - (self.energy - debit))
        self.energy = self.energy - debit + credit
        if not self.minimum - 1e-10 <= self.energy <= self.maximum + 1e-10:
            raise RuntimeError('Parameter energy budget violated')
        self.records.append(dict(raw_action=np.asarray(action).tolist(), previous_parameters=old.tolist(),
            unrestricted_parameters=requested_target.tolist(), requested_parameters=target.tolist(),
            applied_parameters=self.theta.tolist(), energy_before_j=before, recharge_j=recharge,
            requested_storage_change_j=requested, applied_storage_change_j=change, debit_j=debit,
            credit_j=credit, energy_after_j=self.energy, energy_scale=alpha,
            offset=offset.tolist(), velocity=velocity.tolist(),
            mapping='piecewise_log_full_bounds_center_zero_v1'))
        return self.theta


class ParameterController(repaired.ParameterController):
    def __init__(self, env, method, prior):
        super().__init__(env, method, prior)
        self.shield = ParameterShield(method, prior)
        self.apply(self.shield.theta)

    def save(self, out):
        report = super().save(out)
        report.update(parameter_action_mapping='piecewise_log_full_bounds_center_zero_v1',
                      previous_mapping='center_times_exp(action*log(2))')
        repaired.Path(out, 'CONTROLLER_FULLRANGE.json').write_text(
            repaired.json.dumps(report, indent=2, allow_nan=False) + '\n')
        return report


vectors = repaired.vectors
