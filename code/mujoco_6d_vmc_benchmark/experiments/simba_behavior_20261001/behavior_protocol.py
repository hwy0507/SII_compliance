"""Development operational definitions, frozen independently of policy results."""
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class BehaviorThresholds:
    position_m: float = .012
    rotation_rad: float = .12
    speed_mps: float = .025
    settle_s: float = .2
    window_s: float = 5.
    sustained_s: float = .4
    tangent_m: float = .01
    progress_m: float = .01
    gap_s: float = .08
    object_floor_z_m: float = .39
    object_lift_m: float = .1

    def to_dict(self):
        return asdict(self)


DEFAULT = BehaviorThresholds()
PROTOCOL_VERSION = "behavior_development_v1_20261001"
SENSITIVITY_FACTORS = (.5, 1., 2.)
# Never infer/drop required objects from whichever contacts happened to occur.
DEFAULT_EVENT_KINDS = {
    "ball": "impact",
    "person_hand": "sustained",
    "rod": "sustained",
    "cup": "sustained",
    "office_v5_pillar": "sustained",
    "office_v5_corner_top": "sustained",
    "office_v5_corner_face": "sustained",
}
