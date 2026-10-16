"""Prospective train-only cost of remaining measured payload progress.

Uses existing reward-only payload_potential telemetry, never local waypoint
error or additional actor inputs. This is an explicit objective change, unlike
potential-based shaping. Enabled only by an explicit paired-job registration.
"""
import math
from goal_tracking_reward_20261016 import discounted_cost_tail

CONFIG=dict(schema='sii-goal-payload-occupancy-v1',weight=4.,horizon_s=55.,
            control_dt_s=.04,gamma=.9995,
            sample='post_interval_measured_payload_potential',
            interpretation='Dense remaining-progress cost, not potential shaping or a new success label')


def validate_guidance(job, *, controller, reward, reward_variant):
    config=job.get('payload_occupancy_guidance') if job else None
    if config is None:return None
    if config!=CONFIG or controller not in ('impedance','admittance','vmc') or (
            reward!='metric' or reward_variant!='payload_shaping'):
        raise ValueError('Only registered parameter payload-shaping guidance is supported')
    return dict(config)


def check_reward_resume(parent,current):
    if parent.get('payload_occupancy_guidance')!=current.get('payload_occupancy_guidance'):
        raise ValueError('Changed occupancy reward requires fresh paired training or an explicit replay/normalizer rebuild')


def occupancy_terms(potential, interval_s, elapsed_s, *, terminated, success, config):
    if config!=CONFIG:raise ValueError('Unregistered occupancy configuration')
    if not all(math.isfinite(x) for x in (potential,interval_s,elapsed_s)):
        raise ValueError('Nonfinite reward telemetry')
    if (not 0<=potential<=1 or not 0<interval_s<=config['control_dt_s']+1e-7 or
            elapsed_s<interval_s-1e-7 or elapsed_s>config['horizon_s']+1e-7):
        raise ValueError('Invalid potential or interval')
    if success and not terminated:raise ValueError('Success requires terminal evidence')
    cost=config['weight']*(1-potential)*interval_s/config['horizon_s']
    tail=0.
    if terminated and not success:
        tail=discounted_cost_tail(max(0.,config['horizon_s']-elapsed_s),weight=config['weight'],
            horizon_s=config['horizon_s'],control_dt_s=config['control_dt_s'],gamma=config['gamma'])
    return dict(payload_occupancy=-cost,payload_occupancy_failure_continuation=-tail)
