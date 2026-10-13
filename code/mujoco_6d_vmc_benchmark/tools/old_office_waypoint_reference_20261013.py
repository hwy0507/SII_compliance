"""Policy-independent local carry references for the archived desk task.

Preserve the old geometric segment, orientation, endpoint and stage gates.
Use the existing planner's 1 cm densification and waypoint arrival rule.
No contact, obstacle, event clock, neural state or action is consulted.
"""
import numpy as np
from office_task_v4_20260917 import PickPlaceTask
from planned_hand_corner_20261002 import densify
from run_benchmark import so3_log


class LocalCarryReference(PickPlaceTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_goals = [g.copy() for g in self.goals]
        self.carry_route = densify([self.goals[3], self.goals[4]], spacing=.01)
        self.carry_cursor = 0
        self.goals[4] = self.carry_route[0].copy()

    def update(self, q, dq, pos, rot, twist, wrench):
        if self.index == 4 and self.carry_cursor < len(self.carry_route)-1:
            # Same arrival test as original deployed PlannedCornerTask,
            # including its already-enabled lateral rejoin rule.
            reached = np.linalg.norm(pos-self.goals[4]) < .012
            if self.carry_cursor > 0:
                tangent = self.carry_route[self.carry_cursor]-self.carry_route[self.carry_cursor-1]
                length = np.linalg.norm(tangent)
                if length > 1e-8:
                    error = pos-self.goals[4]
                    forward = float(np.dot(error,tangent/length))
                    lateral = error-forward*tangent/length
                    reached = reached or (forward >= 0 and np.linalg.norm(lateral) < .08)
            if (reached and
                    np.linalg.norm(so3_log(self.rotation@rot.T)) < .12):
                previous = self.goals[4].copy()
                self.carry_cursor += 1
                self.goals[4] = self.carry_route[self.carry_cursor].copy()
                self.previous_goal = previous
                delta = self.goals[4]-previous
                self.path_direction = delta/max(np.linalg.norm(delta),1e-8)
            self.ready = 0.
            return False
        # Includes unchanged final carry arrival dwell, load-transfer and release gates.
        return super().update(q,dq,pos,rot,twist,wrench)

    def metadata(self):
        return dict(kind='policy-independent local carry reference', spacing_m=.01,
            arrival_position_m=.012, arrival_orientation_rad=.12,
            allow_lateral_rejoin=True, lateral_rejoin_radius_m=.08,
            original_goals=self.original_goals, carry_route=self.carry_route,
            destination=self.destination, final_cursor=self.carry_cursor,
            stages_other_than_carry_unchanged=True, physical_world_unchanged=True,
            actor_observation_formula_unchanged=True, reference_shared_by_wbc_and_actor=True,
            collision_aware_planning=False, contact_or_event_input=False)
