"""Build a deterministic, office-style MuJoCo scene around the FR3 model."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ASSETS = """
    <material name="floor_mat" rgba="0.18 0.20 0.22 1"/>
    <material name="wall_mat" rgba="0.72 0.74 0.76 1"/>
    <material name="wood_light" rgba="0.52 0.30 0.14 1"/>
    <material name="wood_edge" rgba="0.30 0.16 0.08 1"/>
    <material name="metal_dark" rgba="0.08 0.09 0.10 1"/>
    <material name="plastic_black" rgba="0.025 0.030 0.035 1"/>
    <material name="screen_glass" rgba="0.025 0.14 0.20 1"/>
    <material name="paper_white" rgba="0.90 0.89 0.84 1"/>
    <material name="book_red" rgba="0.46 0.06 0.045 1"/>
    <material name="book_blue" rgba="0.06 0.18 0.34 1"/>
    <material name="target_orange" rgba="0.90 0.25 0.045 1"/>
    <material name="mug_ceramic" rgba="0.82 0.84 0.82 1"/>
    <material name="clutter_blue" rgba="0.05 0.27 0.58 1"/>
    <material name="clutter_green" rgba="0.16 0.40 0.20 1"/>
    <material name="plant_green" rgba="0.08 0.35 0.12 1"/>
    <material name="pot_terracotta" rgba="0.60 0.20 0.08 1"/>
    <material name="chair_fabric" rgba="0.12 0.16 0.20 1"/>
    <material name="camera_housing" rgba="0.025 0.030 0.035 1"/>
    <material name="off_white" specular="0.5" shininess="0.25" rgba="0.85 0.85 0.83 1"/>
    <mesh name="hand_c" file="{panda_assets}/hand.stl"/>
    <mesh name="hand_0" file="{panda_assets}/hand_0.obj"/>
    <mesh name="hand_1" file="{panda_assets}/hand_1.obj"/>
    <mesh name="hand_2" file="{panda_assets}/hand_2.obj"/>
    <mesh name="hand_3" file="{panda_assets}/hand_3.obj"/>
    <mesh name="hand_4" file="{panda_assets}/hand_4.obj"/>
    <mesh name="finger_0" file="{panda_assets}/finger_0.obj"/>
    <mesh name="finger_1" file="{panda_assets}/finger_1.obj"/>
"""


HAND_DEFAULTS = """
    <default class="fingertip_pad_collision_1">
      <geom type="box" size="0.0085 0.004 0.0085" pos="0 0.0055 0.0445" contype="4" conaffinity="4"/>
    </default>
    <default class="fingertip_pad_collision_2">
      <geom type="box" size="0.003 0.002 0.003" pos="0.0055 0.002 0.05" contype="4" conaffinity="4"/>
    </default>
    <default class="fingertip_pad_collision_3">
      <geom type="box" size="0.003 0.002 0.003" pos="-0.0055 0.002 0.05" contype="4" conaffinity="4"/>
    </default>
    <default class="fingertip_pad_collision_4">
      <geom type="box" size="0.003 0.002 0.0035" pos="0.0055 0.002 0.0395" contype="4" conaffinity="4"/>
    </default>
    <default class="fingertip_pad_collision_5">
      <geom type="box" size="0.003 0.002 0.0035" pos="-0.0055 0.002 0.0395" contype="4" conaffinity="4"/>
    </default>
    <default class="panda_finger">
      <joint axis="0 1 0" type="slide" range="0 0.04" armature="0.1" damping="1"/>
    </default>
"""


HAND_BODY = """
      <body name="fr3_hand" pos="0 0 0.107" quat="0.9238795 0 0 -0.3826834">
        <inertial mass="0.73" pos="-0.01 0 0.03" diaginertia="0.001 0.0025 0.0017"/>
        <geom mesh="hand_0" material="off_white" class="visual"/>
        <geom mesh="hand_1" material="black" class="visual"/>
        <geom mesh="hand_2" material="black" class="visual"/>
        <geom mesh="hand_3" material="white" class="visual"/>
        <geom mesh="hand_4" material="off_white" class="visual"/>
        <geom name="fr3_hand_collision" mesh="hand_c" class="collision" contype="4" conaffinity="4"/>
        <!-- Wrist RGB-D sensor: its pose is controlled by the FR3 hand pose. -->
        <geom name="wrist_camera_housing" type="box" pos="0 -0.015 0.055" size="0.040 0.022 0.030"
              material="camera_housing" contype="0" conaffinity="0"/>
        <geom name="wrist_camera_lens" type="cylinder" pos="0 -0.040 0.055" quat="0.707 0.707 0 0"
              size="0.012 0.006" material="screen_glass" contype="0" conaffinity="0"/>
        <!-- MuJoCo cameras look along local -Z. This 180-degree flip makes
             the sensor face the Panda fingers and the tabletop workspace. -->
        <camera name="wrist_rgbd" pos="0 0 0.040" quat="0 1 0 0" fovy="82"/>
        <body name="fr3_left_finger" pos="0 0 0.0584">
          <inertial mass="0.015" pos="0 0 0" diaginertia="2.375e-6 2.375e-6 7.5e-7"/>
          <joint name="fr3_finger_joint1" class="panda_finger"/>
          <geom mesh="finger_0" material="off_white" class="visual"/>
          <geom mesh="finger_1" material="black" class="visual"/>
          <geom name="fr3_left_finger_collision" mesh="finger_0" class="collision"/>
          <geom class="fingertip_pad_collision_1"/>
          <geom class="fingertip_pad_collision_2"/>
          <geom class="fingertip_pad_collision_3"/>
          <geom class="fingertip_pad_collision_4"/>
          <geom class="fingertip_pad_collision_5"/>
        </body>
        <body name="fr3_right_finger" pos="0 0 0.0584" quat="0 0 0 1">
          <inertial mass="0.015" pos="0 0 0" diaginertia="2.375e-6 2.375e-6 7.5e-7"/>
          <joint name="fr3_finger_joint2" class="panda_finger"/>
          <geom mesh="finger_0" material="off_white" class="visual"/>
          <geom mesh="finger_1" material="black" class="visual"/>
          <geom name="fr3_right_finger_collision" mesh="finger_0" class="collision"/>
          <geom class="fingertip_pad_collision_1"/>
          <geom class="fingertip_pad_collision_2"/>
          <geom class="fingertip_pad_collision_3"/>
          <geom class="fingertip_pad_collision_4"/>
          <geom class="fingertip_pad_collision_5"/>
        </body>
      </body>
"""


def build_scene_xml(model_path: Path, seed: int = 7) -> str:
    """Return a reproducible v0 scene without changing the FR3 kinematic model."""

    _ = seed  # v0 is fixed by design; later versions will randomize a manifest.
    text = model_path.read_text()
    if "name=\"tabletop_v0\"" in text:
        raise ValueError("input already appears to contain tabletop_v0 objects")
    panda_assets = (model_path.parent.parent / "franka_emika_panda" / "assets").resolve()
    text = text.replace('meshdir="assets"', f'meshdir="{model_path.parent.resolve() / "assets"}"', 1)
    asset_anchor = "  </asset>"
    world_anchor = "  </worldbody>"
    if asset_anchor not in text or world_anchor not in text:
        raise ValueError("FR3 XML does not contain expected asset/worldbody sections")

    objects = """
    <!-- NUS-inspired fixed-base tabletop benchmark v0 -->
    <!-- Office shell and a full-size desk. The top surface is z=0.72 m. -->
    <geom name="office_floor" type="plane" pos="0 0 0" size="4 4 0.01" material="floor_mat" contype="1" conaffinity="7"/>
    <geom name="office_back_wall" type="box" pos="0 1.02 1.45" size="2.55 0.035 1.45"
          material="wall_mat" contype="1" conaffinity="7"/>
    <geom name="office_side_wall" type="box" pos="-2.25 0 1.45" size="0.035 1.05 1.45"
          material="wall_mat" contype="1" conaffinity="7"/>
    <geom name="desk_top" type="box" pos="0 0 0.69" size="1.05 0.72 0.03"
          material="wood_light" contype="2" conaffinity="7" friction="0.8 0.08 0.01"/>
    <geom name="desk_front_edge" type="box" pos="0 -0.70 0.675" size="1.05 0.025 0.045"
          material="wood_edge" contype="2" conaffinity="7"/>
    <geom name="desk_rear_edge" type="box" pos="0 0.70 0.675" size="1.05 0.025 0.045"
          material="wood_edge" contype="2" conaffinity="7"/>
    <geom name="desk_leg_left_front" type="box" pos="-0.88 -0.56 0.34" size="0.065 0.065 0.34" material="metal_dark" contype="2" conaffinity="7"/>
    <geom name="desk_leg_right_front" type="box" pos="0.88 -0.56 0.34" size="0.065 0.065 0.34" material="metal_dark" contype="2" conaffinity="7"/>
    <geom name="desk_leg_left_rear" type="box" pos="-0.88 0.56 0.34" size="0.065 0.065 0.34" material="metal_dark" contype="2" conaffinity="7"/>
    <geom name="desk_leg_right_rear" type="box" pos="0.88 0.56 0.34" size="0.065 0.065 0.34" material="metal_dark" contype="2" conaffinity="7"/>
    <geom name="desk_rear_beam" type="box" pos="0 0.55 0.43" size="0.88 0.045 0.045" material="metal_dark" contype="2" conaffinity="7"/>

    <!-- FR3 mounting plate at the rear of the desk. -->
    <geom name="fr3_mount_plate" type="cylinder" pos="-0.18 0.40 0.75" size="0.20 0.035"
          material="metal_dark" contype="2" conaffinity="7"/>
    <geom name="fr3_mount_bolt_1" type="cylinder" pos="-0.31 0.40 0.787" size="0.012 0.006" material="plastic_black" contype="0" conaffinity="0"/>
    <geom name="fr3_mount_bolt_2" type="cylinder" pos="-0.05 0.40 0.787" size="0.012 0.006" material="plastic_black" contype="0" conaffinity="0"/>

    <!-- Left pedestal / drawers. -->
    <geom name="drawer_cabinet" type="box" pos="-0.78 0.28 0.38" size="0.20 0.34 0.35" material="wood_edge" contype="2" conaffinity="7"/>
    <geom name="drawer_1" type="box" pos="-0.78 -0.065 0.55" size="0.18 0.012 0.075" material="wood_light" contype="2" conaffinity="7"/>
    <geom name="drawer_2" type="box" pos="-0.78 -0.065 0.37" size="0.18 0.012 0.075" material="wood_light" contype="2" conaffinity="7"/>
    <geom name="drawer_handle_1" type="box" pos="-0.78 -0.083 0.55" size="0.055 0.008 0.008" material="metal_dark" contype="0" conaffinity="0"/>
    <geom name="drawer_handle_2" type="box" pos="-0.78 -0.083 0.37" size="0.055 0.008 0.008" material="metal_dark" contype="0" conaffinity="0"/>

    <!-- Monitor, stand, keyboard and mouse. -->
    <geom name="monitor_stem" type="cylinder" pos="0.72 0.47 0.89" size="0.025 0.17" material="metal_dark" contype="2" conaffinity="7"/>
    <geom name="monitor_base" type="box" pos="0.72 0.47 0.735" size="0.18 0.10 0.012" material="metal_dark" contype="2" conaffinity="7"/>
    <geom name="monitor_frame" type="box" pos="0.72 0.47 1.08" size="0.40 0.035 0.23" material="plastic_black" contype="2" conaffinity="7"/>
    <geom name="monitor_screen" type="box" pos="0.72 0.425 1.08" size="0.35 0.008 0.18" material="screen_glass" contype="0" conaffinity="0"/>
    <geom name="keyboard" type="box" pos="0.34 0.12 0.75" size="0.25 0.085 0.012" material="plastic_black" contype="2" conaffinity="7"/>
    <geom name="keyboard_surface" type="box" pos="0.34 0.115 0.765" size="0.22 0.065 0.006" material="paper_white" contype="0" conaffinity="0"/>
    <geom name="mouse" type="ellipsoid" pos="0.67 0.12 0.76" size="0.045 0.065 0.022" material="plastic_black" contype="2" conaffinity="7"/>

    <!-- Desk objects provide clutter and occlusion diversity. -->
    <body name="target_object" pos="0.18 -0.283 0.810">
      <freejoint/>
      <geom name="target_object_geom" type="cylinder" size="0.018 0.060"
            material="target_orange" mass="0.18" contype="4" conaffinity="7"
            friction="0.8 0.08 0.01"/>
      <geom name="target_object_cap" type="cylinder" pos="0 0 0.063" size="0.015 0.004" material="metal_dark" contype="0" conaffinity="0"/>
    </body>

    <body name="clutter_notebook_red" pos="-0.08 -0.40 0.755" quat="0.98 0 0 0.20">
      <geom type="box" size="0.14 0.10 0.018" material="book_red" mass="0.25" contype="4" conaffinity="7"/>
      <geom type="box" pos="0 0 0.020" size="0.12 0.085 0.004" material="paper_white" contype="0" conaffinity="0"/>
    </body>
    <body name="clutter_notebook_blue" pos="-0.40 -0.16 0.755" quat="0.99 0 0 -0.12">
      <geom type="box" size="0.12 0.085 0.018" material="book_blue" mass="0.24" contype="4" conaffinity="7"/>
      <geom type="box" pos="0 0 0.020" size="0.10 0.07 0.004" material="paper_white" contype="0" conaffinity="0"/>
    </body>
    <body name="coffee_mug" pos="0.58 -0.28 0.79">
      <geom type="cylinder" size="0.065 0.085" material="mug_ceramic" mass="0.22" contype="4" conaffinity="7"/>
      <geom type="capsule" fromto="0.052 0 0.035 0.115 0 0.035" size="0.012" material="mug_ceramic" contype="4" conaffinity="7"/>
      <geom type="capsule" fromto="0.115 0 0.035 0.115 0 0.085" size="0.012" material="mug_ceramic" contype="4" conaffinity="7"/>
      <geom type="cylinder" pos="0 0 0.086" size="0.054 0.006" material="plastic_black" contype="0" conaffinity="0"/>
    </body>
    <body name="pen_holder" pos="0.68 -0.10 0.82">
      <geom type="cylinder" size="0.065 0.10" material="clutter_blue" mass="0.20" contype="4" conaffinity="7"/>
      <geom type="capsule" fromto="0.78 -0.12 0.86 0.76 -0.10 1.02" size="0.008" material="target_orange" contype="0" conaffinity="0"/>
      <geom type="capsule" fromto="0.82 -0.12 0.86 0.85 -0.10 1.05" size="0.008" material="plant_green" contype="0" conaffinity="0"/>
    </body>
    <body name="desk_plant" pos="-0.60 0.42 0.78">
      <geom type="cylinder" size="0.09 0.10" material="pot_terracotta" mass="0.30" contype="4" conaffinity="7"/>
      <geom type="capsule" fromto="-0.60 0.42 0.84 -0.68 0.43 1.14" size="0.018" material="plant_green" contype="0" conaffinity="0"/>
      <geom type="capsule" fromto="-0.60 0.42 0.88 -0.48 0.42 1.10" size="0.018" material="plant_green" contype="0" conaffinity="0"/>
      <geom type="capsule" fromto="-0.60 0.42 0.92 -0.55 0.34 1.16" size="0.018" material="plant_green" contype="0" conaffinity="0"/>
    </body>

    <body name="loose_paper_stack" pos="0.05 0.24 0.755" quat="0.99 0 0 0.10">
      <geom type="box" size="0.13 0.10 0.018" material="paper_white" mass="0.10" contype="4" conaffinity="7"/>
      <geom type="box" pos="0.02 -0.01 0.022" size="0.11 0.085 0.004" material="paper_white" contype="0" conaffinity="0"/>
    </body>
    <geom name="pencil" type="capsule" fromto="0.10 0.43 0.765 0.38 0.38 0.765" size="0.008" material="target_orange" contype="4" conaffinity="7"/>

    <!-- Office chair in front of the desk, included for scene context. -->
    <body name="office_chair" pos="0 -1.12 0">
      <geom name="chair_seat" type="box" pos="0 0 0.53" size="0.30 0.27 0.06" material="chair_fabric" contype="2" conaffinity="7"/>
      <geom name="chair_back" type="box" pos="0 0.22 0.91" size="0.30 0.06 0.38" material="chair_fabric" contype="2" conaffinity="7"/>
      <geom name="chair_stem" type="cylinder" pos="0 0 0.28" size="0.035 0.25" material="metal_dark" contype="2" conaffinity="7"/>
      <geom name="chair_base" type="box" pos="0 0 0.04" size="0.36 0.06 0.025" material="metal_dark" contype="2" conaffinity="7"/>
      <geom name="chair_base_side" type="box" pos="0 0 0.04" size="0.06 0.32 0.025" material="metal_dark" contype="2" conaffinity="7"/>
      <geom name="chair_wheel_1" type="sphere" pos="-0.31 -0.28 0.03" size="0.045" material="plastic_black" contype="2" conaffinity="7"/>
      <geom name="chair_wheel_2" type="sphere" pos="0.31 -0.28 0.03" size="0.045" material="plastic_black" contype="2" conaffinity="7"/>
      <geom name="chair_wheel_3" type="sphere" pos="-0.31 0.28 0.03" size="0.045" material="plastic_black" contype="2" conaffinity="7"/>
      <geom name="chair_wheel_4" type="sphere" pos="0.31 0.28 0.03" size="0.045" material="plastic_black" contype="2" conaffinity="7"/>
    </body>

    <!-- A cable tray and rear power strip reinforce the office layout. -->
    <geom name="cable_tray" type="box" pos="0 0.61 0.57" size="0.72 0.10 0.035" material="plastic_black" contype="2" conaffinity="7"/>
    <geom name="power_strip" type="box" pos="0.55 0.61 0.76" size="0.23 0.035 0.025" material="plastic_black" contype="2" conaffinity="7"/>

    <!-- External observation interfaces; these are not student observations. -->
    <camera name="office_overview" pos="2.15 -2.85 1.95" mode="targetbody" target="target_object" fovy="58"/>
    <camera name="office_side" pos="2.45 1.85 1.55" mode="targetbody" target="target_object" fovy="62"/>
    <!-- Fixed tabletop RGB-D camera near the FR3 base. -->
    <camera name="base_rgbd" pos="1.25 -1.55 1.55" quat="0.749606 0.567627 0.205509 0.271395" fovy="78"/>
"""
    default_anchor = "  </default>\n\n  <asset>"
    if default_anchor not in text:
        raise ValueError("FR3 default section anchor not found")
    text = text.replace(default_anchor, HAND_DEFAULTS + default_anchor, 1)
    text = text.replace(asset_anchor, ASSETS.format(panda_assets=panda_assets) + asset_anchor, 1)

    # The Menagerie FR3 uses position actuators by default.  The nominal
    # controller and later compliance residual both require torque control.
    limits = {index: limit for index, limit in enumerate((87, 87, 87, 87, 12, 12, 12), start=1)}

    def replace_arm_actuator(match: re.Match[str]) -> str:
        index = int(match.group(1))
        limit = limits[index]
        return (
            f'<motor name="fr3_joint{index}" joint="fr3_joint{index}" '
            f'ctrllimited="true" ctrlrange="{-limit} {limit}"/>'
        )

    text, actuator_count = re.subn(
        r'<position class="fr3" name="fr3_joint([1-7])" joint="fr3_joint\1"[^>]*/>',
        replace_arm_actuator,
        text,
    )
    if actuator_count != 7:
        raise ValueError(f"expected seven FR3 position actuators, found {actuator_count}")

    # Attach a collision-aware two-finger hand to the flange body.
    link7 = '<body name="fr3_link7" pos="0.088 0 0" quat="1 1 0 0">'
    start = text.find(link7)
    if start < 0:
        raise ValueError("fr3_link7 body not found")
    close = text.find("</body>", start + len(link7))
    if close < 0:
        raise ValueError("fr3_link7 closing body not found")
    text = text[:close] + HAND_BODY + text[close:]

    actuator_anchor = "  </actuator>"
    text = text.replace(
        actuator_anchor,
        '    <position name="fr3_gripper" tendon="fr3_gripper_tendon" kp="800" ctrlrange="0 0.04"/>'
        + actuator_anchor,
        1,
    )
    text = text.replace(
        "</mujoco>",
        """
  <tendon>
    <fixed name="fr3_gripper_tendon">
      <joint joint="fr3_finger_joint1" coef="0.5"/>
      <joint joint="fr3_finger_joint2" coef="0.5"/>
    </fixed>
  </tendon>
  <equality>
    <joint joint1="fr3_finger_joint1" joint2="fr3_finger_joint2" solimp="0.95 0.99 0.001" solref="0.005 1"/>
    <weld name="target_grasp_weld" body1="fr3_hand" body2="target_object" active="false" solimp="0.95 0.99 0.001" solref="0.005 1"/>
  </equality>
</mujoco>""",
        1,
    )
    # The FR3 base is mounted on the rear-left section of the desk, not on the floor.
    text = text.replace(
        '<body name="base" childclass="fr3">',
        '<body name="base" childclass="fr3" pos="-0.18 0.40 0.75">',
        1,
    )
    text = text.replace(world_anchor, objects + world_anchor, 1)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    output = build_scene_xml(args.model, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output)
    print(f"wrote tabletop scene: {args.output}")


if __name__ == "__main__":
    main()
