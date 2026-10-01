"""Read-only 4 ms contact/behavior telemetry; never supplies actor inputs.

sample() is called after each completed physical substep. Contact forces may
refer to that step's dynamics evaluation, while kinematics are post-step.
No model/data writes or calls to mj_forward occur here.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np


class BehaviorTelemetry:
    def __init__(self, interval_s=.004, metadata=None):
        if interval_s <= 0:
            raise ValueError("interval_s must be positive")
        self.interval_s = float(interval_s)
        self.metadata = dict(metadata or {})
        self.rows = []
        self._elapsed = 0.
        self._start = None
        self._contacts = {}
        self._latest = None
        self._last_time = None

    def sample(self, *, time, dt, hand_position, hand_rotation, hand_twist,
               reference_position, reference_rotation, task_direction,
               route_progress_m=float("nan"), contacts=(), stage=-1,
               object_position=None):
        time, dt = float(time), float(dt)
        if dt <= 0 or (self._last_time is not None and time <= self._last_time):
            raise ValueError("Telemetry requires increasing timestamps and positive dt")
        self._last_time = time
        if self._start is None:
            self._start = time-dt
        hp = np.asarray(hand_position, dtype=float).reshape(3)
        hr = np.asarray(hand_rotation, dtype=float).reshape(3, 3)
        rp = np.asarray(reference_position, dtype=float).reshape(3)
        rr = np.asarray(reference_rotation, dtype=float).reshape(3, 3)
        angle = float(np.arccos(np.clip((np.trace(rr.T @ hr)-1.)/2., -1., 1.)))
        self._latest = dict(
            time=time, hand_position=hp.copy(),
            reference_position=rp.copy(),
            reference_rotation=rr.copy(), hand_rotation=hr.copy(),
            hand_twist=np.asarray(hand_twist, dtype=float).reshape(6).copy(),
            position_error_m=float(np.linalg.norm(hp-rp)),
            rotation_error_rad=angle,
            task_direction=np.asarray(task_direction, dtype=float).reshape(3).copy(),
            route_progress_m=float(route_progress_m), stage=int(stage),
            object_position=(np.full(3, np.nan) if object_position is None else
                             np.asarray(object_position, dtype=float).reshape(3).copy()))
        # Multiple contact points of one obstacle count activity once per substep.
        grouped = {}
        for c in contacts:
            key = str(c["obstacle_id"])
            force = np.asarray(c["force_world"], dtype=float).reshape(3)
            weight = float(np.linalg.norm(force))
            if not np.isfinite(weight) or weight <= .05:
                continue
            normal = np.asarray(c["normal_world"], dtype=float).reshape(3).copy()
            normal /= max(float(np.linalg.norm(normal)), 1e-12)
            if float(normal @ force) < 0:
                normal = -normal
            item = grouped.setdefault(key, dict(force=np.zeros(3), weight=0.,
                normal=np.zeros(3), relative=np.zeros(3), parts=set()))
            item["force"] += force
            item["weight"] += weight
            item["normal"] += weight*normal
            robot = np.asarray(c.get("robot_position", hp), dtype=float).reshape(3)
            obstacle = np.asarray(c["obstacle_position"], dtype=float).reshape(3)
            item["relative"] += weight*(robot-obstacle)
            item["parts"].add(str(c.get("robot_part", "hand")))
        for key, item in grouped.items():
            rec = self._contacts.setdefault(key, dict(duration=0., impulse=0.,
                peak=0., weight=0., normal=np.zeros(3), relative=np.zeros(3),
                parts=set(), first=time-dt, last=time))
            mag = float(np.linalg.norm(item["force"]))
            rec["duration"] += dt
            rec["impulse"] += mag*dt
            rec["peak"] = max(rec["peak"], mag)
            rec["weight"] += item["weight"]*dt
            rec["normal"] += item["normal"]*dt
            rec["relative"] += item["relative"]*dt
            rec["parts"].update(item["parts"])
            rec["last"] = time
        self._elapsed += dt
        if self._elapsed >= self.interval_s-1e-12:
            self._flush()

    def _flush(self):
        if self._latest is None or self._elapsed <= 0:
            return
        row = dict(self._latest, interval_start=self._start, dt=self._elapsed,
                   contacts={})
        for key, rec in self._contacts.items():
            norm = float(np.linalg.norm(rec["normal"]))
            row["contacts"][key] = dict(
                duration=rec["duration"], impulse=rec["impulse"], peak=rec["peak"],
                normal=rec["normal"]/norm if norm > 1e-12 else np.full(3, np.nan),
                relative=rec["relative"]/rec["weight"],
                parts="|".join(sorted(rec["parts"])), first=rec["first"], last=rec["last"])
        self.rows.append(row)
        self._elapsed = 0.
        self._start = None
        self._contacts = {}

    def arrays(self):
        self._flush()
        if not self.rows:
            raise ValueError("No telemetry samples")
        keys = sorted({k for r in self.rows for k in r["contacts"]})
        n, m = len(self.rows), len(keys)
        out = {k: np.asarray([r[k] for r in self.rows]) for k in self.rows[0]
               if k != "contacts"}
        out["obstacle_ids"] = np.asarray(keys, dtype="U128")
        for name in ("duration", "impulse", "peak"):
            out["contact_"+name] = np.zeros((n, m))
        for name in ("normal", "relative"):
            out["contact_"+name] = np.full((n, m, 3), np.nan)
        for name in ("first", "last"):
            out["contact_"+name] = np.full((n, m), np.nan)
        out["contact_parts"] = np.full((n, m), "", dtype="U256")
        for i, row in enumerate(self.rows):
            for j, key in enumerate(keys):
                if key in row["contacts"]:
                    for name, value in row["contacts"][key].items():
                        out["contact_"+name][i, j] = value
        meta = dict(self.metadata, schema="behavior_telemetry_v1",
            interval_target_s=self.interval_s,
            actor_contact_truth=False,
            sampling="all physical substeps accumulated; last post-step kinematics per bin",
            force_semantics="norm of per-obstacle resultant world force; norm-integral impulse",
            relative_semantics="force-time-weighted robot-body center minus obstacle-body center; changing body sets cannot establish slide",
            timestamp_caveat="force dynamics evaluation can precede post-integration kinematics within one physical step")
        out["metadata_json"] = np.asarray(json.dumps(meta, default=str))
        return out

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = self.arrays()
        np.savez_compressed(path, **arrays)
        return dict(path=str(path), samples=len(arrays["time"]),
                    duration_s=float(np.sum(arrays["dt"])),
                    schema="behavior_telemetry_v1",
                    obstacle_ids=arrays["obstacle_ids"].tolist())
