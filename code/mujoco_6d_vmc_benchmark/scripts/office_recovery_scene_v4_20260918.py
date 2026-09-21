"""Shared pick/carry/place reference: level transport, then descent at goal."""
from office_recovery_scene_v3_20260918 import install as install_v3


def install():
    install_v3()
    import office_task_v4_20260917 as task
    class LevelCarryTask(task.PickPlaceTask):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            # Standard task geometry, independent of any obstacle: complete
            # the lift, transport at that height, descend above destination.
            self.goals[4]=self.goals[4].copy();self.goals[4][2]=self.goals[3][2]
            self.goals[7]=self.goals[7].copy();self.goals[7][2]=self.goals[3][2]
    task.PickPlaceTask=LevelCarryTask
