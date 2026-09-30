"""Single-environment, no-integration preflight for training-only corner routes.

Never changes frozen scene/evaluator source. Each candidate constructs a fresh
model, runs the unchanged 10-micrometre initial-contact audit, then closes it.
"""
import argparse
import gc
import json
import os
from pathlib import Path
import resource
import sys
import time
import xml.etree.ElementTree as ET

for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ.setdefault('MUJOCO_GL', 'egl')

import numpy as np

from teacher_bank_design_20260930 import sha, write
from teacher_bank_rollout_20260930 import training_xml, numbers

ROOT = Path(__file__).resolve().parents[1]


def routed_training_xml(xml, fixture, route_y=-.08, bridge_z=.510, half_width=.006, face_position=None,
                        face_right_x=None, face_top_z=.535, face_y=-.190):
    """Connect face northward, then eastward into top, avoiding pickup fingers."""
    root = ET.fromstring(training_xml(xml, fixture))
    if fixture['category'] != 'passive_corner':
        return ET.tostring(root, encoding='unicode')
    world = root.find('worldbody')
    for element in list(world):
        if element.get('name', '').startswith('office_v5_corner_training_bridge'):
            world.remove(element)
    face = world.find("geom[@name='office_v5_corner_face']")
    top = world.find("geom[@name='office_v5_corner_top']")
    if face_position is not None:
        # Explicit offline diagnostic override, never edits the source fixture.
        # The final production distribution must register its own placement rule.
        face.set('pos', numbers(face_position))
    if face_right_x is not None:
        size = np.fromstring(face.get('size'), sep=' ')
        yaw = float(fixture['corner_yaw_rad'])
        extent_x = abs(np.cos(yaw))*size[0]+abs(np.sin(yaw))*size[1]
        face.set('pos', numbers([face_right_x-extent_x, face_y, face_top_z-size[2]]))
    pos = np.fromstring(face.get('pos'), sep=' ')
    top_pos = np.fromstring(top.get('pos'), sep=' ')
    top_size = np.fromstring(top.get('size'), sep=' ')
    end_x = float(top_pos[0] - top_size[0] + .004)
    if route_y <= pos[1] or end_x <= pos[0]:
        raise ValueError('Expected north/east corner connection')
    attrs = dict(type='box', contype=face.get('contype', '1'),
                 conaffinity=face.get('conaffinity', '1'), rgba='.50 .32 .18 1',
                 friction=face.get('friction'), solref=face.get('solref', '.002 1'))
    ET.SubElement(world, 'geom', name='office_v5_corner_training_bridge',
        pos=numbers([pos[0], (pos[1] + route_y)/2, bridge_z]),
        size=numbers([half_width, (route_y-pos[1])/2 + half_width, half_width]), **attrs)
    ET.SubElement(world, 'geom', name='office_v5_corner_training_bridge_connector',
        pos=numbers([(pos[0]+end_x)/2, route_y, bridge_z]),
        size=numbers([(end_x-pos[0])/2 + half_width, half_width, half_width]), **attrs)
    return ET.tostring(root, encoding='unicode')


def preflight(fixtures, output, routes, indices, wall_seconds=180.):
    resource.setrlimit(resource.RLIMIT_AS, (3*1024**3, 3*1024**3))
    sys.path.insert(0, str(ROOT/'scripts'))
    import mujoco
    if mujoco.__version__ != '3.11.0':
        raise RuntimeError('Canonical MuJoCo 3.11.0 required')
    import audit_office_complex_scene_v5_20260917 as geometry
    from office_task_v4_20260917 import audit_initial
    from office_complex_scene_v5_20260917 import fixture_flags
    os.environ['MUJOCO_MENAGERIE_PATH'] = str(ROOT/'outputs/canonical_rl_assets_20260923/menagerie')
    selected = [f for f in json.loads(Path(fixtures).read_text())
                if f['category'] == 'passive_corner' and f['split'] == 'train']
    started = time.time()
    report = dict(purpose='initial_geometry_only_no_physics_integration',
        fixtures_path=str(Path(fixtures).resolve()), fixtures_sha256=sha(fixtures),
        source_sha256=sha(__file__), adapter_sha256=sha(Path(__file__).with_name('teacher_bank_rollout_20260930.py')),
        mujoco=mujoco.__version__, python=sys.executable, threads=1, memory_max_bytes=3*1024**3,
        routes=routes, train_indices=indices, rows=[], started=started,
        task_success_verified=False, dynamic_contact_verified=False)
    original = geometry.extend_complex_xml
    try:
        for route in routes:
            for index in indices:
                if time.time()-started > wall_seconds:
                    report['stopped_reason'] = 'preflight_wall_budget'
                    write(output, report)
                    return report
                fixture = selected[index]
                captured = {}
                def adapter(*args, **kwargs):
                    xml = routed_training_xml(original(*args, **kwargs), fixture, **route)
                    captured['xml'] = xml
                    return xml
                geometry.extend_complex_xml = adapter
                row = dict(fixture_id=fixture['id'], fixture_seed=fixture['seed'], route=route)
                env = None
                try:
                    flags = fixture_flags(fixture['seed'], 0, corner_placement=True,
                                          combined_thick_corner_pillar_v4=True)
                    flags.update(duration=55., nominal_speed=.06, ball_speed=fixture['ball_speed_mps'])
                    env, _, _ = geometry.make(flags)
                    audit_initial(env.model, env.data)
                    row.update(passed=True, simulator_time_s=float(env.data.time), ncon=int(env.data.ncon),
                               hand_position_m=env.data.xpos[env._hand_id].tolist())
                except Exception as exc:
                    row.update(passed=False, error_type=type(exc).__name__, error=str(exc))
                finally:
                    if env is not None:
                        env.close()
                    del env
                    gc.collect()
                if 'xml' in captured:
                    import hashlib
                    row['xml_sha256'] = hashlib.sha256(captured['xml'].encode()).hexdigest()
                report['rows'].append(row)
                report['elapsed_s'] = time.time()-started
                write(output, report)
                print(json.dumps(row, allow_nan=False), flush=True)
    finally:
        geometry.extend_complex_xml = original
    report['complete'] = True
    report['passing_routes'] = [route for route in routes
        if all(row['passed'] for row in report['rows'] if row['route'] == route)]
    write(output, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--indices', default='0,1,2,333,666,999')
    parser.add_argument('--routes', default='[{"route_y":-0.08,"bridge_z":0.510,"half_width":0.006}]')
    parser.add_argument('--wall-seconds', type=float, default=180.)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Preserve previous geometry preflight report')
    preflight(args.fixtures, args.output, json.loads(args.routes),
              [int(v) for v in args.indices.split(',')], args.wall_seconds)
