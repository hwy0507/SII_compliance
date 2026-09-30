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
import os as _os
from pathlib import Path

import numpy as np

# FR3 already defines visual/collision default classes; only the finger and
# fingertip-pad classes (Panda-hand-specific) are grafted.
PANDA_HAND_DEFAULTS = """
      <default class="fingertip_pad_collision_1">
        <geom type="box" size="0.0085 0.004 0.014" pos="0 0.0055 0.0445" contype="12" conaffinity="12" rgba="0.05 0.85 0.25 1" friction="3 0.04 0.004"/>
      </default>
      <default class="fingertip_pad_collision_2">
        <geom type="box" size="0.003 0.002 0.003" pos="0.0055 0.002 0.05" contype="12" conaffinity="12" rgba="0.05 0.85 0.25 1" friction="3 0.04 0.004"/>
      </default>
      <default class="fingertip_pad_collision_3">
        <geom type="box" size="0.003 0.002 0.003" pos="-0.0055 0.002 0.05" contype="12" conaffinity="12" rgba="0.05 0.85 0.25 1" friction="3 0.04 0.004"/>
      </default>
      <default class="fingertip_pad_collision_4">
        <geom type="box" size="0.003 0.002 0.0035" pos="0.0055 0.002 0.0395" contype="12" conaffinity="12" rgba="0.05 0.85 0.25 1" friction="3 0.04 0.004"/>
      </default>
      <default class="fingertip_pad_collision_5">
        <geom type="box" size="0.003 0.002 0.0035" pos="-0.0055 0.002 0.0395" contype="12" conaffinity="12" rgba="0.05 0.85 0.25 1" friction="3 0.04 0.004"/>
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
                      <!-- Palm proxy listens on impactor channel 16 while retaining
                           the normal hand channel 1. Finger geoms stay on 12. -->
                      <geom name="hand_collision" mesh="hand_c" class="collision" contype="8" conaffinity="8"/>
                      <geom name="hand_ball_proxy" type="box" pos="0 0 0.035" size="0.038 0.026 0.026" class="collision" contype="1" conaffinity="17"/>
                      <body name="left_finger" pos="0 0 0.0584">
                        <inertial mass="0.015" pos="0 0 0" diaginertia="2.375e-6 2.375e-6 7.5e-7"/>
                        <joint name="finger_joint1" class="finger"/>
                        <geom mesh="finger_0" material="off_white" class="visual"/>
                        <geom mesh="finger_1" material="black" class="visual"/>
                        <geom mesh="finger_0" class="collision" contype="12" conaffinity="12"/>
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
                        <geom mesh="finger_0" class="collision" contype="12" conaffinity="12"/>
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
    lift_board_tilt_axis: str = "x",
    lift_board_yaw_deg: float = 0.0,
    lift_board_size_m: tuple[float, float, float] = (0.18, 0.05, 0.008),
    lift_board_contype: int = 5,
    lift_board_conaffinity: int = 5,
    dual_board_specs: tuple[tuple[str, tuple[float, float, float], float, float,
                                 tuple[float, float, float]], ...] | None = None,
    impactor_mass_kg: float | None = None,
    ball_radius_m: float | None = None,
    rod_slide_damping: float = 2.0,
    rod_driver_kp: float = 5000.0,
    rod_driver_force_limit_n: float = 300.0,
) -> str:
    """Return the FR3+Hand torque-actuated benchmark scene XML text.

    ``board_underside_z`` optionally adds the under-table extraction board
    (the Prepose-Sampler style obstacle): a horizontal slab spanning the
    carry corridor (x in [0.24, 0.50]) so the preplanned lift/carry sweeps
    into its underside, while the approach/grasp chimney at x ~ 0.54 stays
    clear and the carry destination (x ~ 0.18) lies beyond the board.

    The optional rod-drive arguments are physical properties of the external
    apparatus, not policy inputs: a finite-mass body travels on a damped slide
    under a force-limited position servo.  They permit contact-apparatus
    robustness tests without changing the rigid-body/contact mechanism.
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
    hand_body = PANDA_HAND_BODY
    if impactor_type == "ball" and _os.environ.get("THICK_TABLE_SCENE", "0") != "1":
        # Use a convex palm proxy only for the high-speed sphere. The normal
        # rod/board fixtures retain the audited STL palm collision geometry.
        hand_body = hand_body.replace(
            '<geom name="hand_collision" type="box" pos="-0.015 0 0.030" size="0.105 0.065 0.055" margin="0.015" class="collision" contype="1" conaffinity="17"/>',
            '<geom name="hand_collision" type="box" pos="-0.020 0 0.030" size="0.110 0.070 0.060" margin="0.020" class="collision" contype="1" conaffinity="17"/>',
        )
    text = text[:close] + hand_body + text[close:]

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

    # The two finger slides are mechanically coupled in the real parallel
    # gripper.  Keep that coupling in the model so an asymmetric contact does
    # not let one finger remain open while the other closes through the block.
    # This is a bilateral holonomic constraint, not a payload weld: the block
    # is still held only by normal contact and friction.
    finger_sync = (
        '<equality><joint name="finger_sync" joint1="finger_joint1" '
        'joint2="finger_joint2" polycoef="0 1 0 0 0" '
        'solref="0.003 1" solimp="0.9 0.98 0.001 0.5 2"/></equality>'
    )
    text = text.replace("</mujoco>", finger_sync + "</mujoco>", 1)

    # 5. replace the position actuators with torque motors + gripper + rod driver
    torque_actuators = "\n".join(
        f'<motor name="torque_{index}" joint="fr3_joint{index}" ctrllimited="true" '
        f'ctrlrange="{-limit:g} {limit:g}" forcelimited="true" forcerange="{-limit:g} {limit:g}"/>'
        for index, limit in enumerate(FR3_TORQUE_LIMITS, start=1)
    )
    grip_limit = float(_os.environ.get("GRIPPER_FORCE_LIMIT_N", "220"))
    gripper_actuator = (
        f'<position name="gripper" tendon="split" kp="800" ctrllimited="true" '
        f'ctrlrange="0 0.08" forcelimited="true" forcerange="{-grip_limit:g} {grip_limit:g}"/>'
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
    impactor = impactor_geometry_spec(impactor_type, ball_radius_m=ball_radius_m)
    # The FR3 scene reserves bit 16 for finite-mass ball/rod impacts.  The
    # Panda scene keeps its legacy 4/4 hand channel, so this override is
    # deliberately local to the FR3 XML builder.
    if impactor_type in ("ball", "rod"):
        impactor["contype"], impactor["conaffinity"] = "16", ("31" if _os.environ.get("HAPTIC_BALL_FULL_CONTACTS", "0") == "1" else "17")
    if not np.isfinite(rod_slide_damping) or rod_slide_damping < 0.0:
        raise ValueError("rod_slide_damping must be finite and non-negative")
    if not np.isfinite(rod_driver_kp) or rod_driver_kp <= 0.0:
        raise ValueError("rod_driver_kp must be finite and positive")
    if not np.isfinite(rod_driver_force_limit_n) or rod_driver_force_limit_n <= 0.0:
        raise ValueError("rod_driver_force_limit_n must be finite and positive")
    if impactor_mass_kg is not None:
        if not np.isfinite(impactor_mass_kg) or impactor_mass_kg <= 0.0:
            raise ValueError("impactor_mass_kg must be finite and positive when supplied")
        impactor["mass"] = f"{float(impactor_mass_kg):.8g}"
    board_xml = ""
    if board_underside_z is not None and _os.environ.get("THICK_TABLE_SCENE", "0") != "1":
        # Extraction board (Prepose-style): blocks the carry corridor at the
        # nominal carry height; the arm must dip under it and rejoin beyond
        # x < 0.24.  Bits 4/4 collide with the hand (4/4) and the target
        # object (6/7), not with the table (2/2) or the rod (8/4, offstage).
        thickness = 0.03
        board_xml = f"""
      <geom name="extraction_board" type="box" pos="0.52 -0.065 {board_underside_z + 0.5 * thickness:.4f}"
        size="0.08 0.215 {0.5 * thickness:.4f}" contype="4" conaffinity="4"
        rgba="0.55 0.40 0.22 1" friction="0.25 0.02 0.002"
        solref="{contact_time_constant_s:.5f} 1" solimp="0.97 0.995 0.0002 0.5 2"/>
"""
    def board_geom_xml(
        name: str,
        center_m: tuple[float, float, float],
        tilt_deg: float,
        yaw_deg: float,
        half_extents_m: tuple[float, float, float],
        rgba: str,
        lift_board_tilt_axis: str = "x",
        contype: int = 5,
        conaffinity: int = 5,
    ) -> str:
        """Generate one fixed, physical wooden-board collision geom.

        This helper is deliberately shared by the legacy one-board fixture and
        the new dual-phase fixture.  It emits a world-fixed MuJoCo geom rather
        than a mocap body, so neither board can move, teleport, or be exposed
        to the controller during an episode.
        """
        if len(half_extents_m) != 3 or any(float(value) <= 0.0 for value in half_extents_m):
            raise ValueError("board half extents must contain three positive values")
        tilt = float(np.deg2rad(tilt_deg))
        yaw = float(np.deg2rad(yaw_deg))
        cy, sy = np.cos(0.5 * yaw), np.sin(0.5 * yaw)
        ct, st = np.cos(0.5 * tilt), np.sin(0.5 * tilt)
        if lift_board_tilt_axis == "x":
            # Rz(yaw) Rx(tilt): legacy yz-face inclination.
            quat_wxyz = (cy * ct, cy * st, sy * st, sy * ct)
        elif lift_board_tilt_axis == "y":
            # Rz(yaw) Ry(tilt): xz-face inclination, which gives the hand a
            # useful fore-aft surface to rub along during the vertical lift.
            quat_wxyz = (cy * ct, -sy * st, cy * st, sy * ct)
        else:
            raise ValueError("lift_board_tilt_axis must be 'x' or 'y'")
        return f'''
      <geom name="{name}" type="box"
        pos="{center_m[0]:.4f} {center_m[1]:.4f} {center_m[2]:.4f}"
        size="{half_extents_m[0]:.4f} {half_extents_m[1]:.4f} {half_extents_m[2]:.4f}" quat="{quat_wxyz[0]:.6f} {quat_wxyz[1]:.6f} {quat_wxyz[2]:.6f} {quat_wxyz[3]:.6f}"
        contype="{int(contype)}" conaffinity="{int(conaffinity)}" rgba="{rgba}" friction="0.15 0.02 0.002"
        solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
'''

    lift_board_xml = ""
    if lift_board_center_m is not None and lift_board_tilt_deg is not None:
        # Inclined static wooden board across the lift path: the rising arm
        # strikes the tilted face and must slide along the incline (oblique
        # contact normal).  The audited overhead protocol passes 4/4 here so
        # only the hand/finger collision channel can contact the board; the
        # geometry audit independently verifies that upstream FR3 links do
        # not enter the board volume.
        lift_board_xml = board_geom_xml(
            "lift_board", lift_board_center_m, lift_board_tilt_deg,
            lift_board_yaw_deg, lift_board_size_m, "0.62 0.45 0.24 1",
            lift_board_tilt_axis=lift_board_tilt_axis,
            contype=lift_board_contype, conaffinity=lift_board_conaffinity)
    dual_board_xml = ""
    if dual_board_specs is not None:
        seen_names: set[str] = set()
        for name, center_m, tilt_deg, yaw_deg, half_extents_m in dual_board_specs:
            if name not in ("pregrasp_board", "postgrasp_board") or name in seen_names:
                raise ValueError("dual boards must be uniquely named pregrasp_board/postgrasp_board")
            seen_names.add(name)
            color = "0.27 0.58 0.88 1" if name == "pregrasp_board" else "0.84 0.38 0.20 1"
            dual_board_xml += board_geom_xml(
                name, center_m, float(tilt_deg), float(yaw_deg), half_extents_m, color,
                contype=8, conaffinity=8)
    thick_table_xml = ""
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        _tx = float(_os.environ.get("EXT_TABLE_X", "1.00"))
        _ty = float(_os.environ.get("EXT_TABLE_Y", "0.0"))
        _tz = float(_os.environ.get("EXT_TABLE_Z", "0.66"))
        _side_x = float(_os.environ.get("EXT_TABLE_SIDE_X", "0.840"))
        _side_hy = float(_os.environ.get("EXT_TABLE_SIDE_HY", "0.24"))
        _side_hz = float(_os.environ.get("EXT_TABLE_SIDE_HZ", "0.06"))
        _side_y = float(_os.environ.get("EXT_TABLE_SIDE_Y", "0.0"))
        _side_z = float(_os.environ.get("EXT_TABLE_SIDE_Z", "0.573"))
        _side_hx = float(_os.environ.get("EXT_TABLE_SIDE_HX", "0.090"))
        _side_tilt = float(np.deg2rad(float(_os.environ.get("EXT_TABLE_SIDE_TILT_DEG", "0.0"))))
        _side_quat = (float(np.cos(0.5 * _side_tilt)), 0.0, float(np.sin(0.5 * _side_tilt)), 0.0)
        thick_table_xml = f"""
      <body name="pickup_stage" pos="0 0 0">
        <geom name="pickup_pad" type="box" pos="0.54 0 0.38" size="0.09 0.09 0.02"
          contype="2" conaffinity="2" rgba="0.20 0.20 0.22 1"
          friction="1.2 0.02 0.002"/>
      </body>
      <body name="thick_table_structure" pos="0 0 0">
        <geom name="thick_table_top" type="box" pos="{_tx:.3f} {_ty:.3f} {_tz:.3f}"
          size="0.22 0.24 0.035" contype="14" conaffinity="2"
          rgba="0.48 0.32 0.18 1" friction="0.18 0.02 0.002"
          solref="0.008 1" solimp="0.99999 0.999999 0.0000001 0.5 2"/>
        <geom name="table_side" type="box" pos="{_side_x:.3f} {_side_y:.3f} {_side_z:.3f}"
          size="{_side_hx:.3f} {_side_hy:.3f} {_side_hz:.3f}"
          quat="{_side_quat[0]:.6f} {_side_quat[1]:.6f} {_side_quat[2]:.6f} {_side_quat[3]:.6f}"
          contype="8" conaffinity="8" rgba="0.38 0.24 0.12 1"
          friction="0.05 0.01 0.001" margin="0.006" solref="0.00001 1"
          solimp="0.92 0.99 0.001 0.5 2"/>
      </body>
"""

    legacy_table_xml = "" if _os.environ.get("THICK_TABLE_SCENE", "0") == "1" else (
        '      <geom name="table" type="box" pos="0.54 0 0.38" size="0.20 0.20 0.02"\n'
        '        contype="2" conaffinity="2" rgba="0.31 0.22 0.13 1" friction="1.2 0.02 0.002"/>\n'
    )
    push_rod_xml = ""
    if _os.environ.get("PUSH_ROD_SCENE", "0") == "1":
        push_center_x = float(_os.environ.get("PUSH_ROD_CENTER_X", "0.550"))
        push_center_z = float(_os.environ.get("PUSH_ROD_CENTER_Z", "0.530"))
        push_rod_mass = float(_os.environ.get("PUSH_ROD_MASS_KG", "0.30"))
        push_rod_joint_damping = float(
            _os.environ.get("PUSH_ROD_JOINT_DAMPING", "30.0"))
        push_rod_solref_time = float(
            _os.environ.get("PUSH_ROD_SOLREF_TIME_S", "0.00020"))
        push_rod_solimp_min = float(
            _os.environ.get("PUSH_ROD_SOLIMP_MIN", "0.9999"))
        push_rod_solimp_max = float(
            _os.environ.get("PUSH_ROD_SOLIMP_MAX", "0.99999"))
        push_rod_solimp_width = float(
            _os.environ.get("PUSH_ROD_SOLIMP_WIDTH_M", "0.000001"))
        push_rod_driver_kp = float(
            _os.environ.get("PUSH_ROD_DRIVER_KP", "80.0"))
        push_rod_driver_force_limit = float(
            _os.environ.get("PUSH_ROD_DRIVER_FORCE_LIMIT_N", "20.0"))
        if min(push_rod_mass, push_rod_joint_damping, push_rod_solref_time,
               push_rod_solimp_width, push_rod_driver_kp,
               push_rod_driver_force_limit) <= 0.0:
            raise ValueError("push-rod physical parameters must be positive")
        if not 0.0 < push_rod_solimp_min <= push_rod_solimp_max <= 1.0:
            raise ValueError("push-rod solimp bounds must satisfy 0 < min <= max <= 1")
        push_rod_xml = f'''<body name="push_rod_support" pos="{push_center_x:.3f} 0.160 {push_center_z:.3f}">
        <joint name="push_rod_slide" type="slide" axis="0 -1 0" range="0 0.20"
          damping="{push_rod_joint_damping:.8g}" armature="0.02"/>
        <geom name="push_rod_geom" type="cylinder" size="0.018 0.10"
          quat="0.7071068 0.7071068 0 0" mass="{push_rod_mass:.8g}"
          contype="8" conaffinity="15" priority="{int(_os.environ.get('PUSH_ROD_CONTACT_PRIORITY', '0'))}" rgba="0.18 0.70 0.25 1"
          friction="0.65 0.02 0.002" solref="{push_rod_solref_time:.8g} 1"
          solimp="{push_rod_solimp_min:.8g} {push_rod_solimp_max:.8g} {push_rod_solimp_width:.8g} 0.5 2"/>
      </body>'''
    injected = f"""
      <camera name="rod_track" pos="1.18 -1.42 0.86" xyaxes="0.79 0.61 0  -0.17 0.22 0.96"/>
{legacy_table_xml}
      <body name="target_object" pos="0.54 0 {float(_os.environ.get("TARGET_START_Z", target_start_z)):.3f}">
        <freejoint name="target_freejoint"/>
        <geom name="target_object_geom" type="box" size="0.025 0.025 0.025" mass="0.08"
          contype="{4 if _os.environ.get("THICK_TABLE_SCENE", "0") == "1" else 12}" conaffinity="{int(_os.environ.get("TARGET_TABLE_AFFINITY", "14" if _os.environ.get("THICK_TABLE_SCENE", "0") == "1" else "2"))}" rgba="0.96 0.65 0.10 1" friction="2.5 0.02 0.002"
          solref="{contact_time_constant_s:.5f} 1" solimp="0.85 0.95 0.002 0.5 2"/>
      </body>
      <body name="rod_support" pos="{approach.support_position_m[0]:.3f} {approach.support_position_m[1]:.3f} {approach.support_position_m[2]:.3f}">
        <joint name="rod_slide" type="slide" axis="{approach.slide_axis_world[0]:.1f} {approach.slide_axis_world[1]:.1f} {approach.slide_axis_world[2]:.1f}" range="0 0.20" damping="{rod_slide_damping:.8g}"/>
        <geom name="rod_geom" type="{impactor['geom_type']}" size="{impactor['size']}" quat="{impactor.get('quat') or f'{approach.cylinder_quaternion_wxyz[0]:.7f} {approach.cylinder_quaternion_wxyz[1]:.7f} {approach.cylinder_quaternion_wxyz[2]:.7f} {approach.cylinder_quaternion_wxyz[3]:.7f}'}"
          mass="{impactor['mass']}" contype="{impactor.get('contype','16')}" conaffinity="{impactor.get('conaffinity','17')}" rgba="{impactor['rgba']}"
          friction="{impactor['friction']}" solref="{contact_time_constant_s:.5f} {impactor.get('solref_dampratio', '1')}"
          solimp="0.97 0.995 0.0002 0.5 2"/>
      </body>
      {push_rod_xml}
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
    """ + board_xml + lift_board_xml + dual_board_xml + thick_table_xml
    text = text.replace("  </worldbody>", injected + "  </worldbody>", 1)
    rod_driver = (
        f'<position name="rod_driver" joint="rod_slide" kp="{rod_driver_kp:.8g}" '
        f'ctrllimited="true" ctrlrange="0 0.20" forcelimited="true" forcerange="{-rod_driver_force_limit_n:.8g} {rod_driver_force_limit_n:.8g}"/>\n'
    )
    push_driver = (
        f'<position name="push_rod_driver" joint="push_rod_slide" kp="{push_rod_driver_kp:.8g}" '
        'ctrllimited="true" ctrlrange="0 0.12" forcelimited="true" '
        f'forcerange="{-push_rod_driver_force_limit:.8g} {push_rod_driver_force_limit:.8g}"/>\n'
        if _os.environ.get("PUSH_ROD_SCENE", "0") == "1" else ""
    )
    text = text.replace("</actuator>", rod_driver + push_driver + "</actuator>", 1)
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
    lift_board_tilt_axis: str = "x",
    lift_board_yaw_deg: float = 0.0,
    lift_board_size_m: tuple[float, float, float] = (0.18, 0.05, 0.008),
    lift_board_contype: int = 5,
    lift_board_conaffinity: int = 5,
    dual_board_specs: tuple[tuple[str, tuple[float, float, float], float, float,
                                 tuple[float, float, float]], ...] | None = None,
    impactor_mass_kg: float | None = None,
    ball_radius_m: float | None = None,
    rod_slide_damping: float = 2.0,
    rod_driver_kp: float = 5000.0,
    rod_driver_force_limit_n: float = 300.0,
    **_scene_compat_kwargs,
):
    import mujoco

    xml = build_fr3_hand_scene_xml(
        menagerie, contact_time_constant_s, rod_height_m=rod_height_m,
        rod_center_x_m=rod_center_x_m, rod_center_y_m=rod_center_y_m,
        rod_approach_side=rod_approach_side, impactor_type=impactor_type,
        board_underside_z=board_underside_z,
        lift_board_center_m=lift_board_center_m, lift_board_tilt_deg=lift_board_tilt_deg,
        lift_board_tilt_axis=lift_board_tilt_axis,
        lift_board_yaw_deg=lift_board_yaw_deg, lift_board_size_m=lift_board_size_m,
        lift_board_contype=lift_board_contype, lift_board_conaffinity=lift_board_conaffinity,
        dual_board_specs=dual_board_specs,
        impactor_mass_kg=impactor_mass_kg, ball_radius_m=ball_radius_m,
        rod_slide_damping=rod_slide_damping,
        rod_driver_kp=rod_driver_kp, rod_driver_force_limit_n=rod_driver_force_limit_n)
    if _os.environ.get("PUSH_FULL_RIGID_CONTACTS", "0") == "1":
        # Compile the masks into MuJoCo's body-level broadphase caches too.
        # Visual meshes and the ball-only auxiliary proxy remain unchanged.
        from xml.etree import ElementTree as ET
        root = ET.fromstring(xml)
        for body in root.iter("body"):
            name = body.get("name", "")
            if not (name.startswith("fr3_link") or name in {"hand", "left_finger", "right_finger"}):
                continue
            for geom in body.findall("geom"):
                kind = geom.get("class", "")
                if geom.get("name") != "hand_ball_proxy" and (kind == "collision" or kind.startswith("fingertip_pad_collision_")):
                    geom.set("conaffinity", "15")
        xml = ET.tostring(root, encoding="unicode")
    scene_transform = _scene_compat_kwargs.get("scene_transform")
    if scene_transform is not None:
        xml = scene_transform(xml)
        if not isinstance(xml, str):
            raise TypeError("scene_transform must return MJCF text")
    model = mujoco.MjModel.from_xml_string(xml)
    # Collision channel 8 is reserved for the broad wooden-board face.  Keep
    # the board physically coupled to the hand collision proxy while filtering
    # it from upstream arm links and the carried object.  Bit 1 remains
    # enabled so the hand still collides with the target/impactor channels.
    if int(lift_board_contype) & 8:
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    if _os.environ.get("THICK_TABLE_SCENE", "0") == "1":
        hand_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "hand_collision")
        if hand_id >= 0:
            model.geom_contype[hand_id] = int(model.geom_contype[hand_id]) | 8
            model.geom_conaffinity[hand_id] = int(model.geom_conaffinity[hand_id]) | 8
    model.opt.timestep = 0.004
    data = mujoco.MjData(model)
    mujoco.mj_resetDataKeyframe(model, data, 0)
    mujoco.mj_forward(model, data)
    return model, data
