"""Policy-independent time parameterization of the unchanged old carry line.

The waypoint-only adapter returns zero reference velocity even while advancing
its target. Here arc-length progress and feedforward are generated together.
Robot pose governs progress; no load, contact, event or policy signal is used.
"""
import numpy as np
from old_office_waypoint_reference_20261013 import LocalCarryReference
from office_task_v4_20260917 import PickPlaceTask, DT
from run_benchmark import so3_log


class ContinuousCarryReference(LocalCarryReference):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        delta = self.original_goals[4] - self.original_goals[3]
        self.length = float(np.linalg.norm(delta))
        if self.length <= 1e-8:
            raise ValueError('Carry line must be nondegenerate')
        self.tangent = delta / self.length
        self.arc = 0.
        self.reference_velocity = np.zeros(3)
        self.progress_records = []

    def update(self, q, dq, pos, rot, twist, wrench):
        self.reference_velocity[:] = 0.
        if self.index != 4:
            return PickPlaceTask.update(self, q, dq, pos, rot, twist, wrench)
        projected = float(np.dot(pos-self.original_goals[3], self.tangent))
        lateral = pos-self.original_goals[3]-projected*self.tangent
        if self.arc < self.length:
            # Reuse existing nominal speed, arrival and lateral-rejoin scales;
            # no fitting to a rollout, and no free-running event timer.
            can_progress = (np.linalg.norm(lateral) < .08 and
                            np.linalg.norm(so3_log(self.rotation@rot.T)) < .12)
            next_arc = min(self.length, self.arc+.06*DT,
                           max(self.arc, projected+.012)) if can_progress else self.arc
            self.reference_velocity = (next_arc-self.arc)/DT*self.tangent
            self.arc = next_arc
            self.goals[4] = self.original_goals[3]+self.arc*self.tangent
            if self.arc == self.length:
                self.goals[4] = self.original_goals[4].copy()
            self.path_direction = self.tangent.copy()
            self.carry_cursor = min(len(self.carry_route)-1,
                int(self.arc/self.length*(len(self.carry_route)-1)))
            self.ready = 0.
            self.progress_records.append([self.arc, projected, *self.reference_velocity])
            return False
        # Preserve final arrival/dwell, carry-load tracking and all release gates.
        return PickPlaceTask.update(self, q, dq, pos, rot, twist, wrench)

    def sample(self, unused=None):
        pos, rot, _, angular = super().sample(unused)
        return pos, rot, self.reference_velocity.copy() if self.index == 4 else np.zeros(3), angular

    def metadata(self):
        value = super().metadata()
        value.update(kind='pose-governed continuous old carry line with consistent feedforward',
                     nominal_speed_mps=.06, maximum_reference_lead_m=.012,
                     control_dt=DT, arc_m=self.arc, length_m=self.length,
                     progress_records=self.progress_records,
                     progression='monotone arc, <=60mm/s, <=12mm ahead of projected pose; lateral/orientation gates retained',
                     caveat='New common reference design; not an exact restoration of the original waypoint planner')
        return value
