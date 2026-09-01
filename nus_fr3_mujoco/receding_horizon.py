"""Short-horizon execution supervision for the FR3 tabletop planner."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .collision_checker import FR3SweptVolumeChecker, SweptVolumeReport


@dataclass(frozen=True)
class HorizonDecision:
    time_s: float
    phase: str
    active_plan: str
    selected_plan: str
    switched: bool
    trigger_reason: str
    report: SweptVolumeReport


class RecedingHorizonSupervisor:
    """Recheck and, when necessary, switch the remaining trajectory online."""

    def __init__(
        self,
        candidates: list,
        checker: FR3SweptVolumeChecker,
        *,
        initial_plan: str | None = None,
        initial_q: np.ndarray | None = None,
        horizon_s: float = 0.6,
        check_period_s: float = 0.2,
        sample_dt_s: float = 0.06,
        replan_clearance_m: float | None = None,
        switch_cooldown_s: float = 0.8,
        blend_duration_s: float = 0.30,
    ) -> None:
        if not candidates:
            raise ValueError("at least one candidate plan is required")
        if horizon_s <= 0.0 or check_period_s <= 0.0 or sample_dt_s <= 0.0:
            raise ValueError("horizon, check period, and sample dt must be positive")
        if replan_clearance_m is not None and replan_clearance_m < 0.0:
            raise ValueError("replan_clearance_m must be non-negative or None")
        if switch_cooldown_s < 0.0 or blend_duration_s < 0.0:
            raise ValueError("clearance, cooldown, and blend durations must be non-negative")
        self.candidates = list(candidates)
        self.checker = checker
        self.initial_q = np.zeros(7, dtype=np.float64) if initial_q is None else np.asarray(initial_q, dtype=np.float64).copy()
        if self.initial_q.shape != (7,) or not np.all(np.isfinite(self.initial_q)):
            raise ValueError("initial_q must be a finite seven-vector")
        self.horizon_s = float(horizon_s)
        self.check_period_s = float(check_period_s)
        self.sample_dt_s = float(sample_dt_s)
        self.replan_clearance_m = None if replan_clearance_m is None else float(replan_clearance_m)
        self.switch_cooldown_s = float(switch_cooldown_s)
        self.blend_duration_s = float(blend_duration_s)
        self.active_plan = self.candidates[0].name if initial_plan is None else initial_plan
        self._candidate_by_name(self.active_plan)
        self.next_check_time_s = -np.inf
        self.check_count = 0
        self.switch_count = 0
        self.decisions: list[HorizonDecision] = []
        self.last_switch_time_s = -np.inf
        self.blend_start_time_s = -np.inf
        self.blend_from_q = np.zeros(7, dtype=np.float64)
        self.anchor_time_s = -np.inf
        self.anchor_q = self.initial_q.copy()
        self.anchor_segment_index = 0

    def update(self, q_current: np.ndarray, time_s: float) -> HorizonDecision | None:
        """Inspect the future window when the 0.2 s supervisor timer expires."""

        time_s = float(time_s)
        if time_s + 1.0e-9 < self.next_check_time_s:
            return None
        q_current = np.asarray(q_current, dtype=np.float64)
        if q_current.shape != (7,) or not np.all(np.isfinite(q_current)):
            raise ValueError("q_current must be a finite seven-vector")

        active = self._candidate_by_name(self.active_plan)
        active_report = self._check_candidate(active, q_current, time_s)
        selected = active
        trigger_reason = "periodic_safe_recheck"
        clearance_triggered = self.replan_clearance_m is not None and active_report.min_clearance_m < self.replan_clearance_m
        if active_report.collision_count > 0 or clearance_triggered:
            trigger_reason = "collision_in_horizon" if active_report.collision_count > 0 else "clearance_below_threshold"
            reports = [(active, active_report)]
            for candidate in self._compatible_candidates(active, time_s):
                if candidate.name == active.name:
                    continue
                reports.append((candidate, self._check_candidate(candidate, q_current, time_s)))
            best_candidate, best_report = min(reports, key=self._ranking_key)
            can_switch = time_s - self.last_switch_time_s >= self.switch_cooldown_s
            if can_switch and self._ranking_key((best_candidate, best_report)) < self._ranking_key((active, active_report)):
                selected, active_report = best_candidate, best_report
                self.switch_count += 1
                switched = True
                self.last_switch_time_s = time_s
                self.blend_start_time_s = time_s
                self.blend_from_q = q_current.copy()
                self.anchor_time_s = time_s
                self.anchor_q = q_current.copy()
                self.anchor_segment_index = self._segment_index_at(selected.segments, time_s)
            else:
                switched = False
        else:
            switched = False

        previous_plan = self.active_plan
        self.active_plan = selected.name
        self.check_count += 1
        self.next_check_time_s = time_s + self.check_period_s
        phase = self._phase_at(selected.segments, time_s)
        decision = HorizonDecision(
            time_s=time_s,
            phase=phase,
            active_plan=previous_plan,
            selected_plan=selected.name,
            switched=switched,
            trigger_reason=trigger_reason,
            report=active_report,
        )
        self.decisions.append(decision)
        return decision

    def plan_segments(self):
        return list(self._candidate_by_name(self.active_plan).segments)

    def reference(self, q_current: np.ndarray, time_s: float) -> tuple[np.ndarray, float, str]:
        """Return a continuous reference for the active plan at global time."""

        q_current = np.asarray(q_current, dtype=np.float64)
        segments = self.plan_segments()
        if np.isfinite(self.anchor_time_s) and time_s >= self.anchor_time_s:
            return self._anchored_reference(segments, time_s)
        return self._absolute_reference(segments, time_s, self.initial_q)

    @staticmethod
    def _absolute_reference(segments: list, time_s: float, q_start: np.ndarray) -> tuple[np.ndarray, float, str]:
        elapsed = 0.0
        previous = np.asarray(q_start, dtype=np.float64).copy()
        for segment in segments:
            duration = float(segment.duration_s)
            if time_s < elapsed + duration - 1.0e-9:
                ratio = np.clip((time_s - elapsed) / max(duration, 1.0e-9), 0.0, 1.0)
                smooth = ratio * ratio * (3.0 - 2.0 * ratio)
                q_ref = (1.0 - smooth) * previous + smooth * np.asarray(segment.q, dtype=np.float64)
                return q_ref, segment.gripper_m, segment.phase
            elapsed += duration
            previous = np.asarray(segment.q, dtype=np.float64).copy()
        final = segments[-1]
        return np.asarray(final.q, dtype=np.float64).copy(), final.gripper_m, final.phase

    def _anchored_reference(self, segments: list, time_s: float) -> tuple[np.ndarray, float, str]:
        """Follow a switched candidate from the measured q at switch time."""

        index = min(self.anchor_segment_index, len(segments) - 1)
        segment = segments[index]
        remaining = max(self._segment_end_time(segments, index) - self.anchor_time_s, 1.0e-6)
        elapsed = float(time_s - self.anchor_time_s)
        if elapsed < remaining:
            ratio = np.clip(elapsed / remaining, 0.0, 1.0)
            smooth = ratio * ratio * (3.0 - 2.0 * ratio)
            q_ref = (1.0 - smooth) * self.anchor_q + smooth * np.asarray(segment.q, dtype=np.float64)
            return q_ref, segment.gripper_m, segment.phase

        previous = np.asarray(segment.q, dtype=np.float64).copy()
        elapsed_after = elapsed - remaining
        for next_segment in segments[index + 1 :]:
            duration = float(next_segment.duration_s)
            if elapsed_after < duration:
                ratio = np.clip(elapsed_after / max(duration, 1.0e-9), 0.0, 1.0)
                smooth = ratio * ratio * (3.0 - 2.0 * ratio)
                q_ref = (1.0 - smooth) * previous + smooth * np.asarray(next_segment.q, dtype=np.float64)
                return q_ref, next_segment.gripper_m, next_segment.phase
            elapsed_after -= duration
            previous = np.asarray(next_segment.q, dtype=np.float64).copy()
        final = segments[-1]
        return np.asarray(final.q, dtype=np.float64).copy(), final.gripper_m, final.phase

    def _check_candidate(self, candidate, q_current: np.ndarray, time_s: float) -> SweptVolumeReport:
        segments = self._future_segments(candidate.segments, q_current, time_s)
        if not segments:
            # At the terminal time there is no future segment left. Still
            # evaluate the current configuration so the supervisor has a
            # well-defined final decision and the checker receives [N, 7].
            q_samples = np.asarray(q_current, dtype=np.float64).reshape(1, 7)
            time_samples = np.zeros(1, dtype=np.float64)
            return self.checker.check_trajectory(q_samples, time_samples, max_events=16)
        q_samples, time_samples = self.checker.interpolate_segments(
            segments, q_current, sample_dt_s=self.sample_dt_s
        )
        # ``interpolate_segments`` returns times local to the horizon.  The
        # obstacle predictor is defined in the episode's absolute clock.
        return self.checker.check_trajectory(
            q_samples,
            time_samples + float(time_s),
            max_events=16,
        )

    def _future_segments(self, segments: list, q_current: np.ndarray, time_s: float) -> list:
        remaining = self.horizon_s
        elapsed = 0.0
        previous = np.asarray(q_current, dtype=np.float64).copy()
        result = []
        for segment in segments:
            duration = float(segment.duration_s)
            if time_s >= elapsed + duration - 1.0e-9:
                elapsed += duration
                previous = np.asarray(segment.q, dtype=np.float64).copy()
                continue
            offset = max(0.0, time_s - elapsed)
            local_duration = min(duration - offset, remaining)
            if local_duration > 1.0e-9:
                result.append(type(segment)(local_duration, np.asarray(segment.q).copy(), segment.gripper_m, segment.phase))
                remaining -= local_duration
            elapsed += duration
            previous = np.asarray(segment.q, dtype=np.float64).copy()
            if remaining <= 1.0e-9:
                break
        return result

    @staticmethod
    def _ranking_key(item: tuple) -> tuple:
        candidate, report = item
        return (
            report.collision_count > 0,
            report.near_collision_count,
            -report.min_clearance_m,
            candidate.path_length_rad,
        )

    def _candidate_by_name(self, name: str):
        for candidate in self.candidates:
            if candidate.name == name:
                return candidate
        raise KeyError(f"unknown candidate plan: {name}")

    def _compatible_candidates(self, active, time_s: float) -> list:
        """Keep replanning within the task stage already reached.

        Before pre-grasp, a different approach corridor is still valid. Once
        the hand commits to grasping, switching approach would replay an old
        stage and can invalidate the gripper state. After that point only the
        place corridor may change.
        """

        phase = self._phase_at(active.segments, time_s)
        active_approach = active.name.split("+", 1)[0]
        # Once the hand starts descending into the placement corridor, keep
        # the already selected place waypoint fixed.  Switching between place
        # candidates during this short release window changes the measured
        # hand/object transform and can turn a valid grasp into a placement
        # miss.  Replanning remains available during carry, before descent.
        if phase in {
            "PRE-GRASP HIGH",
            "PRE-GRASP",
            "DESCEND",
            "SETTLE AT GRASP",
            "CLOSE GRIPPER",
            "LIFT",
            # Carry-level obstacle reactions are synthesized from the current
            # RGB-D belief by the local collision-gated shield. Switching to
            # a different precomputed IK branch here caused repeated route
            # flips and large non-task joint excursions.
            "CARRY AROUND CLUTTER",
            "PLACE DESCEND",
            "RELEASE",
            "RETRACT AFTER RELEASE",
            "RETURN HOME",
        }:
            return [active]
        if phase == "APPROACH ABOVE CLUTTER":
            # Replanning may change the approach corridor, but it must not
            # silently change the task's destination.  The previous logic
            # ranked all approach/place combinations together; a collision
            # warning near the base could therefore switch between different
            # placement suffixes. The arm would still move safely, but the
            # final placement audit would be compared against a different
            # target than the one selected at task start. Keep the place
            # suffix fixed for the whole episode and only vary the pre-grasp
            # approach branch.
            active_place = active.name.split("+", 1)[1] if "+" in active.name else None
            if active_place is None:
                return list(self.candidates)
            compatible = [
                candidate
                for candidate in self.candidates
                if "+" in candidate.name and candidate.name.split("+", 1)[1] == active_place
            ]
            return compatible or list(self.candidates)
        return [
            candidate
            for candidate in self.candidates
            if candidate.name.split("+", 1)[0] == active_approach
        ]

    @staticmethod
    def _phase_at(segments: list, time_s: float) -> str:
        elapsed = 0.0
        for segment in segments:
            elapsed += float(segment.duration_s)
            if time_s <= elapsed:
                return segment.phase
        return segments[-1].phase

    @staticmethod
    def _segment_index_at(segments: list, time_s: float) -> int:
        elapsed = 0.0
        for index, segment in enumerate(segments):
            elapsed += float(segment.duration_s)
            if time_s <= elapsed:
                return index
        return len(segments) - 1

    @staticmethod
    def _segment_end_time(segments: list, index: int) -> float:
        return float(sum(float(segment.duration_s) for segment in segments[: index + 1]))
