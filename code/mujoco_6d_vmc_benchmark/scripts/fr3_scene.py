#!/usr/bin/env python3
"""FR3 + Panda Hand scene builder for the compliance benchmark.

The real FR3 shares its wrist flange with the Panda Hand (same hardware on
the target robot), so the scene grafts the Panda hand/finger bodies, tendon,
materials, and finger defaults onto the FR3 arm, converts the FR3 position
actuators to torque motors with the FR3 per-joint force limits, and injects
the same table/target/rod stage the Panda benchmark uses.  Joint ordering,
torque limits, keyframe layout, and control indexing match the Panda scene
one-to-one so the environment needs no per-robot branching.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

# FR3 already defines visual/collision default classes; only the finger and
# fingertip-pad classes (Panda-hand-specific) are grafted.
PANDA_HAND_DEFAULTS = """
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
      <default class="finger">
        <joint axis="0 1 0" type="slide" range="0 0.04" armature="0.1" damping="1"/>
      </default>
"""

# FR3 already defines black/white materials; only off_white is new.
PANDA_MATERIALS = """
    <material name="off_white" specular="0.5" shininess="0.25" rgba="0.85 0.85 0.83 1"/>
"""

PANDA_HAND_ASSETS = """
    <mesh name="hand_c" file="{panda_assets}/hand.stl"/>
    <mesh name="hand_0" file="{panda_assets}/hand_0.obj"/>
    <mesh name="hand_1" file="{panda_assets}/hand_1.obj"/>
    <mesh name="hand_2" file="{panda_assets}/hand_2.obj"/>
    <mesh name="hand_3" file="{panda_assets}/hand_3.obj"/>
    <mesh name="hand_4" file="{panda_assets}/hand_4.obj"/>
    <mesh name="finger_0" file="{panda_assets}/finger_0.obj"/>
    <mesh name="finger_1" file="{panda_assets}/finger_1.obj"/>
"""

PANDA_HAND_BODY = """
                    <body name="hand" pos="0 0 0.107" quat="0.9238795 0 0 -0.3826834">
                      <inertial mass="0.73" pos="-0.01 0 0.03" diaginertia="0.001 0.0025 0.0017"/>
                      <geom mesh="hand_0" material="off_white" class="visual"/>
                      <geom mesh="hand_1" material="black" class="visual"/>
                      <geom mesh="hand_2" material="black" class="visual"/>
                      <geom mesh="hand_3" material="white" class="visual"/>
                      <geom mesh="hand_4" material="off_white" class="visual"/>
                      <geom name="hand_collision" mesh="hand_c" class="collision" contype="4" conaffinity="4"/>
                      <body name="left_finger" pos="0 0 0.0584">
                        <inertial mass="0.015" pos="0 0 0" diaginertia="2.375e-6 2.375e-6 7.5e-7"/>
                        <joint name="finger_joint1" class="finger"/>
                        <geom mesh="finger_0" material="off_white" class="visual"/>
                        <geom mesh="finger_1" material="black" class="visual"/>
                        <geom mesh="finger_0" class="collision"/>
                        <geom class="fingertip_pad_collision_1"/>
                        <geom class="fingertip_pad_collision_2"/>
                        <geom class="fingertip_pad_collision_3"/>
                        <geom class="fingertip_pad_collision_4"/>
                        <geom class="fingertip_pad_collision_5"/>
                      </body>
                      <body name="right_finger" pos="0 0 0.0584" quat="0 0 0 1">
                        <inertial mass="0.015" pos="0 0 0" diaginertia="2.375e-6 2.375e-6 7.5e-7"/>
                        <joint name="finger_joint2" class="finger"/>
                        <geom mesh="finger_0" material="off_white" class="visual"/>
                        <geom mesh="finger_1" material="black" class="visual"/>
                        <geom mesh="finger_0" class="collision"/>
                        <geom class="fingertip_pad_collision_1"/>
                        <geom class="fingertip_pad_collision_2"/>
                        <geom class="fingertip_pad_collision_3"/>
                        <geom class="fingertip_pad_collision_4"/>
                        <geom class="fingertip_pad_collision_5"/>
                      </body>
                    </body>
"""

# FR3 per-joint torque limits (datasheet: joints 1-4 +-87 Nm, 5-7 +-12 Nm).
FR3_TORQUE_LIMITS = (87.0, 87.0, 87.0, 87.0, 12.0, 12.0, 12.0)


def build_fr3_hand_scene_xml(
    menagerie: Path,
    contact_time_constant_s: float,
    rod_height_m: float = 0.540,
    rod_center_x_m: float = 0.55,
    rod_center_y_m: float = 0.0,
    rod_approach_side: str = "negative_y",
    impactor_type: str = "rod",
    target_start_z: float = 0.455,
    board_underside_z: float | None = None,
    lift_board_center_m: tuple[float, float, float] | None = None,
    lift_board_tilt_deg: float | None = None,
) -> str:
    """Return the FR3+Hand torque-actuated benchmark scene XML text.

    ``board_underside_z`` optionally adds the under-table extraction board
    (the Prepose-Sampler style obstacle): a horizontal slab spanning the
    carry corridor (x in [0.24, 0.50]) so the preplanned lift/carry sweeps
    into its underside, while the approach/grasp chimney at x ~ 0.54 stays
    clear and the carry destination (x ~ 0.18) lies beyond the board.
    """

    from run_rod_perturbation_benchmark import impactor_geometry_spec, rod_approach_geometry

    fr3_path = menagerie / "franka_fr3" / "fr3.xml"
    text = fr3_path.read_text()
    fr3_assets = (menagerie / "franka_fr3" / "assets").resolve()
    panda_assets = str((menagerie / "franka_emika_panda" / "assets").resolve())
    text = text.replace('meshdir="assets"', f'meshdir="{fr3_assets}"', 1)

    # 1. graft finger/visual/collision defaults into the FR3 default tree
    anchor_default = "</default>\n\n  <custom>"
    if anchor_default not in text:
        anchor_default = "</default>\n\n  <asset>"
    assert anchor_default in text, "FR3 default block anchor not found"
    text = text.replace(anchor_default, PANDA_HAND_DEFAULTS + anchor_default, 1)

    # 2. materials + hand meshes into the asset section
    anchor_asset = "</asset>"
    assert anchor_asset in text
    text = text.replace(
        anchor_asset,
        PANDA_MATERIALS + PANDA_HAND_ASSETS.format(panda_assets=panda_assets) + anchor_asset,
        1,
    )

    # 3. hand body under the final FR3 link (link8 = flange frame)
    #    The Panda attaches the hand at (0,0,0.107, rot -45deg) from its link6;
    #    FR3's link8 is that same flange, so the identical attach is used.
    hand_attach = re.search(r'(<body name="fr3_link7"[^>]*>)', text)
    assert hand_attach, "fr3_link7 body not found"
    # insert before the closing of link8's body: find its direct closing tag by scanning depth
    start = hand_attach.end()
    depth = 1
    pos = start
    while depth > 0:
        m = re.compile(r"<body\b|</body>").search(text, pos)
        assert m
        if m.group(0) == "</body>":
            depth -= 1
        else:
            depth += 1
        pos = m.end()
    close = text.rindex("</body>", start, pos + len("</body>"))
    text = text[:close] + PANDA_HAND_BODY + text[close:]

    # 4. tendon for the split gripper
    anchor_tendon = "</tendon>"
    if anchor_tendon not in text:
        text = text.replace("</mujoco>", "<tendon></tendon>\n</mujoco>")
    tendon_block = """
    <fixed name="split">
      <joint joint="finger_joint1" coef="0.5"/>
      <joint joint="finger_joint2" coef="0.5"/>
    </fixed>
"""
    text = text.replace("</tendon>", tendon_block + "</tendon>", 1)

    # 5. replace the position actuators with torque motors + gripper + rod driver
    torque_actuators = "\n".join(
        f'<motor name="torque_{index}" joint="fr3_joint{index}" ctrllimited="true" '
        f'ctrlrange="{-limit:g} {limit:g}" forcelimited="true" forcerange="{-limit:g} {limit:g}"/>'
        for index, limit in enumerate(FR3_TORQUE_LIMITS, start=1)
    )
    gripper_actuator = (
        '<position name="gripper" tendon="split" kp="250" ctrllimited="true" '
        'ctrlrange="0 0.04" forcelimited="true" forcerange="-100 100"/>'
    )
    text = re.sub(
        r"<actuator>.*?</actuator>",
        "<actuator>\n" + torque_actuators + "\n" + gripper_actuator + "\n</actuator>",
        text,
        flags=re.DOTALL,
    )

    # 6. rebuild the keyframe with fingers and no ctrl (torque controls start at zero)
    text = re.sub(
        r"<keyframe>.*?</keyframe>",
        '<keyframe>\n    <key name="home" qpos="0 0 0 -1.57079 0 1.57079 -0.7853 0.04 0.04"/>\n  </keyframe>',
        text,
        flags=re.DOTALL,
    )

    # 7. inject the benchmark stage (camera, table, target, rod, markers)
    approach = rod_approach_geometry(rod_approach_side, rod_height_m, rod_center_x_m, rod_center_y_m)
    impactor = impactor_geometry_spec(impactor_type)
    board_xml = ""
    if board_underside_z is not None:
        # Extraction board (Prepose-style): blocks the carry corridor at the
        # nominal carry height; the arm must dip under it and rejoin beyond
        # x < 0.24.  Bits 4/4 collide with the hand (4/4) and the target
        # object (6/7), not with the table (2/2) or the rod (8/4, offstage).
        thickness = 0.03
        board_xml = f"""
      <geom name="extraction_board" type="box" pos="0.37 0 {board_underside_z + 0.5 * thickness:.4f}"
        size="0.13 0.20 {0.5 * thickness:.4f}" contype="4" conaffinity="4"
        rgba="0.55 0.40 0.22 1" friction="0.15 0.02 0.002"
        solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
"""
    lift_board_xml = ""
    if lift_board_center_m is not None and lift_board_tilt_deg is not None:
        # Inclined static wooden board across the lift path: the rising arm
        # strikes the tilted face and must slide along the incline (oblique
        # contact normal).  Contact bits 5/5 collide with the hand (4/4),
        # the FR3 arm links (1/1) and the target object (6/7), matching the
        # dynamic plank impactor bit assignment.
        tilt = float(np.deg2rad(lift_board_tilt_deg))
        # Face normal: the box's +z axis tilted ``tilt`` from -z (pointing
        # down toward the rising arm) about the x axis, so sliding along the
        # face guides the hand sideways in +y toward the board edge.
        quat_wxyz = (np.cos(0.5 * tilt), np.sin(0.5 * tilt), 0.0, 0.0)
        lift_board_xml = f"""
      <geom name="lift_board" type="box"
        pos="{lift_board_center_m[0]:.4f} {lift_board_center_m[1]:.4f} {lift_board_center_m[2]:.4f}"
        size="0.18 0.05 0.008" quat="{quat_wxyz[0]:.6f} {quat_wxyz[1]:.6f} {quat_wxyz[2]:.6f} {quat_wxyz[3]:.6f}"
        contype="5" conaffinity="5" rgba="0.62 0.45 0.24 1" friction="0.25 0.02 0.002"
        solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
"""
    injected = f"""
      <camera name="rod_track" pos="1.18 -1.42 0.86" xyaxes="0.79 0.61 0  -0.17 0.22 0.96"/>
      <geom name="table" type="box" pos="0.54 0 0.38" size="0.20 0.20 0.02"
        contype="2" conaffinity="2" rgba="0.31 0.22 0.13 1" friction="1.2 0.02 0.002"/>
      <body name="target_object" pos="0.54 0 {target_start_z:.3f}">
        <freejoint name="target_freejoint"/>
        <geom name="target_object_geom" type="box" size="0.025 0.025 0.025" mass="0.08"
          contype="6" conaffinity="7" rgba="0.96 0.65 0.10 1" friction="1.5 0.02 0.002"
          solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
      </body>
      <body name="rod_support" pos="{approach.support_position_m[0]:.3f} {approach.support_position_m[1]:.3f} {approach.support_position_m[2]:.3f}">
        <joint name="rod_slide" type="slide" axis="{approach.slide_axis_world[0]:.1f} {approach.slide_axis_world[1]:.1f} {approach.slide_axis_world[2]:.1f}" range="0 0.20" damping="2.0"/>
        <geom name="rod_geom" type="{impactor['geom_type']}" size="{impactor['size']}" quat="{impactor.get('quat') or f'{approach.cylinder_quaternion_wxyz[0]:.7f} {approach.cylinder_quaternion_wxyz[1]:.7f} {approach.cylinder_quaternion_wxyz[2]:.7f} {approach.cylinder_quaternion_wxyz[3]:.7f}'}"
          mass="{impactor['mass']}" contype="{impactor.get('contype','8')}" conaffinity="{impactor.get('conaffinity','4')}" rgba="{impactor['rgba']}"
          friction="{impactor['friction']}" solref="{contact_time_constant_s:.5f} 1"
          solimp="0.85 0.95 0.002 0.5 2"/>
      </body>
      <body name="moving_obstacle" mocap="true" pos="0 0 1">
        <geom name="moving_obstacle_geom" type="sphere" size="0.040" mass="0" contype="4" conaffinity="4"
          rgba="0.85 0.12 0.12 0.92" friction="0.9 0.05 0.02"
          solref="{contact_time_constant_s:.5f} 1" solimp="0.75 0.90 0.006 0.5 2"/>
      </body>
      <body name="nominal_marker" mocap="true" pos="0 0 1">
        <geom type="sphere" size="0.025" contype="0" conaffinity="0" rgba="0.10 0.35 1.0 0.95"/>
      </body>
      <body name="actual_marker" mocap="true" pos="0 0 1">
        <geom type="sphere" size="0.024" contype="0" conaffinity="0" rgba="1.0 0.05 0.68 0.98"/>
      </body>
    """ + board_xml + lift_board_xml
    text = text.replace("  </worldbody>", injected + "  </worldbody>", 1)
    rod_driver = (
        '<position name="rod_driver" joint="rod_slide" kp="5000" '
        'ctrllimited="true" ctrlrange="0 0.20" forcelimited="true" forcerange="-300 300"/>\n'
    )
    text = text.replace("</actuator>", rod_driver + "</actuator>", 1)
    return text


def make_fr3_hand_model(
    menagerie: Path,
    contact_time_constant_s: float = 0.015,
    rod_height_m: float = 0.540,
    rod_center_x_m: float = 0.55,
    rod_center_y_m: float = 0.0,
    rod_approach_side: str = "negative_y",
    impactor_type: str = "rod",
    board_underside_z: float | None = None,
    lift_board_center_m: tuple[float, float, float] | None = None,
    lift_board_tilt_deg: float | None = None,
):
    import mujoco

    xml = build_fr3_hand_scene_xml(
        menagerie, contact_time_constant_s, rod_height_m=rod_height_m,
        rod_center_x_m=rod_center_x_m, rod_center_y_m=rod_center_y_m,
        rod_approach_side=rod_approach_side, impactor_type=impactor_type,
        board_underside_z=board_underside_z,
        lift_board_center_m=lift_board_center_m, lift_board_tilt_deg=lift_board_tilt_deg)
    model = mujoco.MjModel.from_xml_string(xml)
    model.opt.timestep = 0.004
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    return model, data
