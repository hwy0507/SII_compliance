from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class StepRecord:
    t: float
    q_arm: list[float]
    q_target: list[float]
    qdot_nom: list[float]
    qdot_residual: list[float]
    qdot_cmd: list[float]
    min_clearance: float
    risk: float
    active_link: str | None
    feedback_confidence: float = 1.0
    feedback_source: str = "unknown"
    contact_depth: float = 0.0
    force_proxy_level: float = 0.0
    qvel_tracking_error: float = 0.0
    locked_joint_correction: float = 0.0
    locked_joint_velocity_norm: float = 0.0


@dataclass
class RolloutMetrics:
    mode: str
    goal_tolerance: float
    allowed_penetration: float = 0.025
    records: list[StepRecord] = field(default_factory=list)
    contact_occurred: bool = False
    collision: bool = False
    success: bool = False
    final_arm_error: float = float("inf")

    def add(
        self,
        *,
        t: float,
        q_arm: np.ndarray,
        q_target: np.ndarray,
        qdot_nom: np.ndarray,
        qdot_residual: np.ndarray,
        qdot_cmd: np.ndarray,
        min_clearance: float,
        risk: float,
        active_link: str | None,
        feedback_confidence: float = 1.0,
        feedback_source: str = "unknown",
        contact_depth: float = 0.0,
        force_proxy_level: float = 0.0,
        qvel_tracking_error: float = 0.0,
        locked_joint_correction: float = 0.0,
        locked_joint_velocity_norm: float = 0.0,
    ) -> None:
        self.records.append(
            StepRecord(
                t=float(t),
                q_arm=np.asarray(q_arm).astype(float).tolist(),
                q_target=np.asarray(q_target).astype(float).tolist(),
                qdot_nom=np.asarray(qdot_nom).astype(float).tolist(),
                qdot_residual=np.asarray(qdot_residual).astype(float).tolist(),
                qdot_cmd=np.asarray(qdot_cmd).astype(float).tolist(),
                min_clearance=float(min_clearance),
                risk=float(risk),
                active_link=active_link,
                feedback_confidence=float(feedback_confidence),
                feedback_source=str(feedback_source),
                contact_depth=float(contact_depth),
                force_proxy_level=float(force_proxy_level),
                qvel_tracking_error=float(qvel_tracking_error),
                locked_joint_correction=float(locked_joint_correction),
                locked_joint_velocity_norm=float(locked_joint_velocity_norm),
            )
        )
        if min_clearance <= 0.0:
            self.contact_occurred = True
        if -float(min_clearance) > float(self.allowed_penetration):
            self.collision = True

    @property
    def min_clearance(self) -> float:
        if not self.records:
            return float("inf")
        return float(min(r.min_clearance for r in self.records))

    def finalize(self, final_q: np.ndarray, goal_q: np.ndarray) -> dict[str, Any]:
        self.final_arm_error = float(np.linalg.norm(final_q - goal_q))
        self.success = bool((not self.collision) and self.final_arm_error <= self.goal_tolerance)
        return self.summary()

    def summary(self) -> dict[str, Any]:
        if not self.records:
            return {
                "mode": self.mode,
                "success": False,
                "collision": False,
                "steps": 0,
            }

        commands = np.asarray([r.qdot_cmd for r in self.records], dtype=np.float32)
        residuals = np.asarray([r.qdot_residual for r in self.records], dtype=np.float32)
        jerks = np.zeros((0, commands.shape[1]), dtype=np.float32)
        if len(commands) >= 3:
            jerks = commands[2:] - 2.0 * commands[1:-1] + commands[:-2]
        contact_steps = sum(1 for r in self.records if r.min_clearance <= 0.0)
        contact_compliance_steps = sum(
            1
            for r in self.records
            if str(r.feedback_source).startswith(("contact_compliance", "bc_policy"))
        )
        max_penetration = max(0.0, -float(self.min_clearance))
        force_proxy_steps = sum(1 for r in self.records if r.force_proxy_level > 0.0)
        locked_joint_corrections = np.asarray(
            [r.locked_joint_correction for r in self.records], dtype=np.float32
        )
        locked_joint_velocities = np.asarray(
            [r.locked_joint_velocity_norm for r in self.records], dtype=np.float32
        )
        final_arm_error = float(self.final_arm_error)
        mean_jerk = float(np.linalg.norm(jerks, axis=1).mean()) if len(jerks) else 0.0
        score = 100.0
        if not self.success:
            score -= 35.0
        if self.collision:
            score -= 45.0
        score -= min(35.0, 1500.0 * max_penetration)
        score -= min(15.0, 0.15 * float(contact_steps))
        score -= min(10.0, 80.0 * mean_jerk)
        score -= min(10.0, 50.0 * final_arm_error)
        score = float(np.clip(score, 0.0, 100.0))

        return {
            "mode": self.mode,
            "success": bool(self.success),
            "collision": bool(self.collision),
            "contact_occurred": bool(self.contact_occurred),
            "min_clearance": float(self.min_clearance),
            "max_penetration": float(max_penetration),
            "allowed_penetration": float(self.allowed_penetration),
            "final_arm_error": final_arm_error,
            "mean_command_norm": float(np.linalg.norm(commands, axis=1).mean()),
            "mean_residual_norm": float(np.linalg.norm(residuals, axis=1).mean()),
            "mean_jerk": mean_jerk,
            "steps": int(len(self.records)),
            "elapsed_sim_time": float(self.records[-1].t),
            "max_risk": float(max(r.risk for r in self.records)),
            "mean_feedback_confidence": float(
                np.mean([r.feedback_confidence for r in self.records])
            ),
            "contact_steps": int(contact_steps),
            "contact_compliance_steps": int(contact_compliance_steps),
            "force_proxy_steps": int(force_proxy_steps),
            "max_force_proxy_level": float(max(r.force_proxy_level for r in self.records)),
            "mean_qvel_tracking_error": float(
                np.mean([r.qvel_tracking_error for r in self.records])
            ),
            "max_locked_joint_correction": float(np.max(locked_joint_corrections)),
            "mean_locked_joint_correction": float(np.mean(locked_joint_corrections)),
            "max_locked_joint_velocity_norm": float(np.max(locked_joint_velocities)),
            "compliance_score": score,
        }

    def to_json_dict(self, include_records: bool = False) -> dict[str, Any]:
        out = self.summary()
        if include_records:
            out["records"] = [r.__dict__ for r in self.records]
        return out
