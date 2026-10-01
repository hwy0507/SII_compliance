"""Office rewards for SimbaV2. Task-only is an Office-specific adaptation.
Reward-only privileged metadata must never enter actor observations.
"""
from dataclasses import asdict, dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class RewardConfig:
    mode: str = "metric"
    error_transform: str = "quadratic"
    gamma: float = 0.995
    horizon_s: float = 55.0
    control_dt_s: float = 0.04
    error_scale_m: float = 0.12
    success_reward: float = 20.0
    failure_penalty: float = 20.0
    progress_weight: float = 5.0
    error_weight: float = 4.0
    torque_peak_weight: float = 8.0
    time_weight: float = 1.0
    smooth_weight: float = 0.0002
    # Declared physical support bound, NOT a cap on actual error.
    max_position_error_m: float = 3.0
    max_actual_torque_ratio: float = 1.0
    action_dim: int = 7

    def validate(self):
        if self.mode not in ("task_only", "office_task", "metric"):
            raise ValueError("mode must be task_only, office_task, or metric")
        if self.error_transform not in ("quadratic", "bounded"):
            raise ValueError("unknown error transform")
        if not 0.0 < self.gamma <= 1.0:
            raise ValueError("gamma must be in (0,1]")
        for name in ("horizon_s", "control_dt_s", "error_scale_m",
                     "max_position_error_m", "max_actual_torque_ratio"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(name + " must be finite and positive")
        for name in ("success_reward", "failure_penalty", "progress_weight",
                     "error_weight", "torque_peak_weight", "time_weight", "smooth_weight"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(name + " must be finite and nonnegative")
        if self.action_dim != 7:
            raise ValueError("Office action contract is normalized action7")
        return self

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class IntervalMetrics:
    """Accumulate EVERY physical substep in an RL interval.
    error_cost = sum(dt / horizon * (norm(p-p_ref)/error_scale)**2).
    peak_torque_ratio = max(abs(qfrc_actuator[j])/env.torque_limits[j]).
    Raw seven per-joint peaks use the same actual actuator signal.
    """
    elapsed_s: float
    error_cost: float
    peak_torque_ratio: float
    peak_torque_nm_per_joint: Sequence[float]
    max_position_error_m: float
    substeps: int
    bounded_error_cost: float | None = None

    def validate(self, cfg):
        values = (self.elapsed_s, self.error_cost, self.peak_torque_ratio,
                  self.max_position_error_m, *self.peak_torque_nm_per_joint)
        if any(not math.isfinite(float(x)) or x < 0 for x in values):
            raise ValueError("interval metrics must be finite and nonnegative")
        if self.elapsed_s <= 0 or self.substeps <= 0:
            raise ValueError("interval must contain physical substeps")
        if len(self.peak_torque_nm_per_joint) != 7:
            raise ValueError("need seven actual actuator torque peaks")
        if self.max_position_error_m > cfg.max_position_error_m + 1e-8:
            raise ValueError("declared error support violated; do not silently clip")
        if self.peak_torque_ratio > cfg.max_actual_torque_ratio + 1e-5:
            raise ValueError("declared torque support violated; audit actuator/limits")
        if cfg.error_transform == "bounded":
            if (self.bounded_error_cost is None or not math.isfinite(self.bounded_error_cost)
                    or not 0 <= self.bounded_error_cost <= self.elapsed_s / cfg.horizon_s + 1e-10):
                raise ValueError("bounded error integral missing or outside [0, elapsed/horizon]")
        max_cost = (self.elapsed_s / cfg.horizon_s
                    * (self.max_position_error_m / cfg.error_scale_m)**2)
        if self.error_cost > max_cost + 1e-8:
            raise ValueError("error integral inconsistent with observed maximum")


class OfficeReward:
    """Requested action is normalized [-1,1]^7 BEFORE common safety/filter.
    Reset previous action zero7 means canonical zero slowdown, zero residual.
    """
    def __init__(self, config=None):
        self.config = (config or RewardConfig()).validate()
        self.reset()

    def reset(self, initial_action=None):
        action = [0., 0., 0., 0., 0., 0., 0.] if initial_action is None else initial_action
        self.previous_action = self._action(action)
        self.elapsed_s = 0.0
        self.peak_torque_ratio = 0.0
        self.peak_torque_nm_per_joint = [0.0] * 7
        self.error_cost_total = 0.0
        self.ended = False

    def _action(self, action):
        result = [float(x) for x in action]
        if len(result) != self.config.action_dim or any(
                not math.isfinite(x) or abs(x) > 1.0 + 1e-6 for x in result):
            raise ValueError("requested action must be normalized finite [-1,1]^7")
        return result

    def _failure_continuation(self):
        """Discounted upper bound of negative costs avoided by early failure.
        Sum gamma*C1+...+gamma**n*Cn analytically, plus remaining peak budget.
        This is conservative, not the unknown true counterfactual return.
        """
        c = self.config
        remaining = max(0.0, c.horizon_s - self.elapsed_s)
        if remaining < 1e-9 or c.mode == "task_only":
            return 0.0
        n_full = int(math.floor(remaining / c.control_dt_s + 1e-9))
        partial = max(0.0, remaining - n_full * c.control_dt_s)
        if partial < 1e-9:
            partial = 0.0
        gsum = (float(n_full) if c.gamma == 1.0 else
                c.gamma * (-math.expm1(n_full * math.log(c.gamma))) / (1.0 - c.gamma))
        error_time_rate = ((c.error_weight * (1.0 if c.error_transform == "bounded" else (c.max_position_error_m / c.error_scale_m)**2)
                            if c.mode == "metric" else 0.) + c.time_weight) / c.horizon_s
        maximum_smooth_cost = c.smooth_weight * 4.0 * c.action_dim if c.mode == "metric" else 0.
        cost = gsum * (error_time_rate * c.control_dt_s + maximum_smooth_cost)
        if partial:
            cost += c.gamma**(n_full + 1) * (
                error_time_rate * partial + maximum_smooth_cost)
        peak_budget = max(0.0, c.max_actual_torque_ratio**2 - self.peak_torque_ratio**2)
        if c.mode == "metric":
            cost += c.gamma * c.torque_peak_weight * peak_budget
        return float(cost)

    def __call__(self, interval, requested_action, *, current_potential,
                 next_potential, terminated=False, success=False, failure=False,
                 terminal_reason=None, task_complete_before_interval=False):
        if self.ended:
            raise RuntimeError("reward called after terminal; reset first")
        c = self.config
        interval.validate(c)
        action = self._action(requested_action)
        if any(not math.isfinite(float(x)) for x in (current_potential, next_potential)):
            raise ValueError("potential must be finite")
        if any(float(x) < -1e-8 or float(x) > 1.0 + 1e-8
               for x in (current_potential, next_potential)):
            raise ValueError("global task potential must be in [0,1]")
        if bool(success) and bool(failure):
            raise ValueError("success and failure are mutually exclusive")
        if terminated and not (success or failure):
            raise ValueError("true terminal must specify success or failure")
        if not terminated and (success or failure or terminal_reason is not None):
            raise ValueError("success/failure/reason requires true terminal")
        if terminated and not terminal_reason:
            raise ValueError("terminal_reason required; finite horizon timeout is terminal")
        previous_peak = self.peak_torque_ratio
        self.peak_torque_ratio = max(previous_peak, float(interval.peak_torque_ratio))
        peak_increment = self.peak_torque_ratio**2 - previous_peak**2
        self.peak_torque_nm_per_joint = [
            max(a, float(b)) for a, b in zip(
                self.peak_torque_nm_per_joint, interval.peak_torque_nm_per_joint)]
        smooth = sum((a - b)**2 for a, b in zip(action, self.previous_action))
        self.previous_action = action
        self.elapsed_s += float(interval.elapsed_s)
        self.error_cost_total += float(interval.error_cost)
        terminal_phi = 0.0 if terminated else float(next_potential)
        potential_reward = c.gamma * terminal_phi - float(current_potential)
        task = (c.success_reward if terminated and success else
                -c.failure_penalty if terminated and failure else 0.0)
        continuation = self._failure_continuation() if terminated and failure else 0.0
        # The successful final interval preceded success, hence is still charged.
        # End immediately once strict success holds; do not simulate extra actions.
        time_cost = (0.0 if task_complete_before_interval else
                     float(interval.elapsed_s) / c.horizon_s)
        terms = dict(
            task=task,
            progress=c.progress_weight * potential_reward if c.mode != "task_only" else 0.0,
            error=-c.error_weight * float(interval.bounded_error_cost if c.error_transform == "bounded" else interval.error_cost) if c.mode == "metric" else 0.0,
            peak_torque=-c.torque_peak_weight * peak_increment if c.mode == "metric" else 0.0,
            time=-c.time_weight * time_cost if c.mode != "task_only" else 0.0,
            smooth=-c.smooth_weight * smooth if c.mode == "metric" else 0.0,
            failure_continuation=-continuation,
        )
        reward = float(sum(terms.values()))
        info = dict(terms, reward=reward, mode=c.mode,
                    error_transform=c.error_transform,
                    bounded_error_cost=interval.bounded_error_cost,
                    error_cost=float(interval.error_cost),
                    error_cost_total=self.error_cost_total,
                    peak_torque_cost_increment=peak_increment,
                    peak_torque_ratio=self.peak_torque_ratio,
                    peak_torque_nm_per_joint=list(self.peak_torque_nm_per_joint),
                    peak_torque_nm=max(self.peak_torque_nm_per_joint),
                    smooth_cost=smooth, current_potential=float(current_potential),
                    next_potential=float(next_potential), effective_next_potential=terminal_phi,
                    elapsed_s=self.elapsed_s, substeps=int(interval.substeps),
                    terminated=bool(terminated), success=bool(success), failure=bool(failure),
                    terminal_reason=terminal_reason, requested_action=action,
                    task_complete_before_interval=bool(task_complete_before_interval),
                    previous_action_reset=[0.,0.,0.,0.,0.,0.,0.])
        self.ended = bool(terminated)
        return reward, info
