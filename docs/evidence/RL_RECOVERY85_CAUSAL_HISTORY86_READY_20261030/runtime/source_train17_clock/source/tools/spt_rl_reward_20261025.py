"""SPT-oriented training surrogate; NOT the final SPT/comfort evaluator.

All four interfaces use identical physical costs. Human contact is column 2
of the archived research channels, never all external contacts. Scales below
are engineering training scales, NOT validated human comfort thresholds.
"""
import math
import numpy as np
from goal_tracking_reward_20261016 import discounted_cost_tail

CONFIG = dict(schema='sii-rl-spt-surrogate-v1', horizon_s=55., control_dt_s=.04,
    gamma=.9995, progress_weight=5., occupancy_weight=4., time_weight=1.,
    comfort_weight=2., contact_force_weight=1., penetration_weight=8.,
    peak_torque_weight=1., slew_weight=.25, comfort_torque_ratio=.5,
    contact_force_scale_n=15., contact_force_onset_n=.05,
    penetration_scale_m=.0002, success_bonus=25., failure_penalty=25.,
    threshold_status='engineering_training_scales_not_human_comfort_calibration',
    success_definition='task_success AND strict_success',
    contact_scope='human_robot_sum_column_2')


def validate_config(config=None):
    cfg = dict(CONFIG if config is None else config)
    if cfg != CONFIG:
        raise ValueError('Changed objective requires a new registered variant and fresh replay')
    return cfg


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Nonfinite reward telemetry')
    return value


def bounded(x):
    x = max(0., finite(x))
    return x / (1. + x)


def contact_integrals(dt, torque, limits, human_force):
    """Integrate coincident human contact and torque at physical substeps.

Returns durations and bounded cost integrals in seconds; ratios use time,
not frame counts. Zero-contact compliance is None, not 100%.
"""
    dt, torque, limits, human_force = (np.asarray(x, dtype=float)
                                      for x in (dt, torque, limits, human_force))
    if (dt.ndim != 1 or not len(dt) or torque.shape != (len(dt), 7)
            or limits.shape != (7,) or human_force.shape != dt.shape
            or not all(np.isfinite(x).all() for x in (dt, torque, limits, human_force))
            or np.any(dt <= 0) or np.any(limits <= 0) or np.any(human_force < 0)):
        raise ValueError('Invalid physical substep arrays')
    active = human_force > CONFIG['contact_force_onset_n']
    ratio = np.max(np.abs(torque)/limits, axis=1)
    excess = np.maximum(0., ratio / CONFIG['comfort_torque_ratio'] - 1.)
    force_excess = np.maximum(0., human_force / CONFIG['contact_force_scale_n'] - 1.)
    duration = float(dt[active].sum())
    compliant = float(dt[active & (excess == 0)].sum())
    return dict(human_contact_s=duration, human_compliant_s=compliant,
        human_compliance_proxy=(compliant/duration if duration else None),
        human_torque_cost_integral_s=float(dt @ (active * excess/(1+excess))),
        human_force_cost_integral_s=float(dt @ (active * force_excess/(1+force_excess))),
        human_force_peak_n=float(human_force.max()),
        human_force_magnitude_integral_ns=float(dt @ human_force),
        human_torque_excess_integral_ratio_s=float(dt @ (active * excess)))


class SPTReward:
    def __init__(self, config=None):
        self.config = validate_config(config)
        self.elapsed_s = 0.
        self.penalty_peaks = dict(penetration=0., peak_torque=0.)
        self.ended = False

    def __call__(self, *, current_potential, next_potential, interval,
                 terminated, task_success, strict_success, failure_reason=None):
        if self.ended:
            raise ValueError('Reward called after terminal')
        cfg = self.config
        dt = finite(interval['elapsed_s'])
        phi, nxt = map(finite, (current_potential, next_potential))
        if not 0 < dt <= cfg['control_dt_s']+1e-7 or not 0 <= phi <= 1 or not 0 <= nxt <= 1:
            raise ValueError('Invalid time/potential')
        elapsed = self.elapsed_s + dt
        if elapsed > cfg['horizon_s']+1e-6 or ((task_success or strict_success) and not terminated):
            raise ValueError('Invalid horizon/terminal labels')
        if strict_success and not task_success:
            raise ValueError('Strict requires Task')
        contact = interval['spt_contact']
        human_s = finite(contact['human_contact_s'])
        compliant_s = finite(contact['human_compliant_s'])
        if not 0 <= compliant_s <= human_s+1e-9 or not 0 <= human_s <= dt+1e-9:
            raise ValueError('Invalid contact denominator')
        costs = [finite(contact[k]) for k in
                 ('human_torque_cost_integral_s', 'human_force_cost_integral_s')]
        if any(x < 0 or x > human_s+1e-9 for x in costs):
            raise ValueError('Invalid contact cost integral')
        peak = finite(interval['peak_torque_ratio'])
        penetration = finite(interval['external_penetration_peak_m'])
        slew = finite(interval['torque_slew_cost'])
        if min(peak, penetration, slew) < 0:
            raise ValueError('Negative physical cost')
        h = cfg['horizon_s']
        terms = dict(progress=cfg['progress_weight']*(cfg['gamma']*(0. if terminated else nxt)-phi),
            occupancy=-cfg['occupancy_weight']*(1.-nxt)*dt/h,
            time=-cfg['time_weight']*dt/h,
            comfort_torque=-cfg['comfort_weight']*costs[0]/h,
            contact_force=-cfg['contact_force_weight']*costs[1]/h,
            torque_slew=-cfg['slew_weight']*min(slew, dt/h))
        current = dict(penetration=bounded(penetration/cfg['penetration_scale_m']),
                       peak_torque=bounded(peak))
        new_peaks = {k:max(current[k], self.penalty_peaks[k]) for k in current}
        for k in current:
            terms[k] = -cfg[k+'_weight']*(new_peaks[k]-self.penalty_peaks[k])
        success = bool(terminated and task_success and strict_success)
        terms['terminal'] = (cfg['success_bonus'] if success else -cfg['failure_penalty']) if terminated else 0.
        terms['failure_tail'] = 0.
        if terminated and not success and elapsed < h-1e-6:
            # An early abort cannot escape the bounded remaining costs.
            weight = sum(cfg[k+'_weight'] for k in ('occupancy','time','comfort','contact_force','slew'))
            terms['failure_tail'] = -discounted_cost_tail(h-elapsed, weight=weight,
                horizon_s=h, control_dt_s=cfg['control_dt_s'], gamma=cfg['gamma'])
            terms['failure_tail'] -= sum(cfg[k+'_weight']*(1.-new_peaks[k]) for k in new_peaks)
        value = sum(terms.values())
        self.elapsed_s, self.ended, self.penalty_peaks = elapsed, bool(terminated), new_peaks
        terms.update(current_potential=phi, next_potential=nxt,
            effective_next_potential=0. if terminated else nxt,
            task_success=bool(task_success), strict_success=bool(strict_success),
            success=success, terminated=bool(terminated), failure_reason=failure_reason,
            elapsed_s=elapsed, final_reward=value)
        return value, terms


def spt_value(*, task_success, strict_success, completion_time_s, reference_time_s):
    """Caller must supply gate-matched completion time, NOT 55 s audit duration."""
    reference = finite(reference_time_s)
    if reference <= 0:
        raise ValueError('Positive registered reference time required')
    if not (task_success and strict_success):
        return 0.
    completion = finite(completion_time_s)
    if completion <= 0:
        raise ValueError('Positive actual completion time required')
    return reference/max(completion, reference)
