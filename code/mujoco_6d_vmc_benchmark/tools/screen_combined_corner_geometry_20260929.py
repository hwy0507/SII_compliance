"""Geometric replay screen only; cannot certify force, safety or task success."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def robot_ids(model):
    result = set()
    for gid in range(model.ngeom):
        body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[gid])) or ''
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid) or ''
        if (body.startswith('fr3_link') or body in {'hand', 'left_finger', 'right_finger'}) and int(model.geom_group[gid]) != 2 and name != 'hand_ball_proxy':
            result.add(gid)
    return result


def screen(xml, trace, candidate, stride):
    root = ET.fromstring(xml)
    name = candidate.get('geom_name', 'office_v5_corner_face')
    corner = root.find('.//geom[@name="' + name + '"]')
    if corner is None:
        corner = ET.SubElement(root.find('worldbody'), 'geom', name=name, type='box',
                               friction='.25 .01 .001', solref='.002 1')
    corner.set('pos', ' '.join(map(str, candidate['position_m'])))
    corner.set('size', ' '.join(map(str, candidate['half_size_m'])))
    # Compile each candidate: changing static geom_pos alone leaves the
    # compiled static collision hierarchy inconsistent with the new geometry.
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    data = mujoco.MjData(model)
    corner_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
    target = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'target_object_geom')
    robot = robot_ids(model)
    result = {}
    for i in range(0, len(trace['time']), stride):
        stage = int(trace['stage'][i])
        if stage > 3:
            continue
        data.qpos[:] = trace['qpos'][i]
        data.qvel[:] = trace['qvel'][i]
        data.mocap_pos[:] = trace['mocap_pos'][i]
        data.mocap_quat[:] = trace['mocap_quat'][i]
        mujoco.mj_forward(model, data)
        for j in range(data.ncon):
            contact = data.contact[j]
            g1, g2 = int(contact.geom1), int(contact.geom2)
            other = g2 if g1 == corner_id else g1 if g2 == corner_id else -1
            if other < 0 or contact.dist > 0:
                continue
            subject = 'target' if other == target else 'robot' if other in robot else None
            if subject is None:
                continue
            phase = 'pre_lift' if stage < 3 else 'lift'
            key = phase + '_' + subject
            time = float(trace['time'][i])
            row = result.setdefault(key, dict(first_s=time, last_s=time, contact_snapshots=0, max_snapshot_overlap_m=0., body_names=[]))
            row['last_s'] = time
            row['contact_snapshots'] += 1
            row['max_snapshot_overlap_m'] = max(row['max_snapshot_overlap_m'], -float(contact.dist))
            body = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[other])) or ''
            if body not in row['body_names']:
                row['body_names'].append(body)
    return dict(candidate=candidate, contacts=result,
                passes_geometric_pre_lift_exclusion=not any(k.startswith('pre_lift_') for k in result),
                has_lift_target_snapshot='lift_target' in result,
                has_lift_robot_snapshot='lift_robot' in result)


def main(a):
    if a.output.exists():
        raise FileExistsError('Preserve existing screen')
    plan = json.loads(a.plan.read_text())
    xml = a.rollout.with_suffix('.xml')
    raw = a.rollout.with_suffix('.npz')
    with np.load(raw, allow_pickle=False) as trace:
        rows = [screen(xml.read_text(), trace, c, a.stride) for c in plan['candidates']]
    result = dict(purpose='read_only_geometry_screen_not_closed_loop',
                  caveat='Geometric overlap snapshots are not forces, continuous contact, safety, or success. Closed-loop rollout is mandatory.',
                  world_xml_sha256=sha(xml), trajectory_sha256=sha(raw), plan_sha256=sha(a.plan),
                  screen_source_sha256=sha(Path(__file__)), snapshot_stride=a.stride, results=rows)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False))
    for r in rows:
        print(r['candidate']['id'], r['passes_geometric_pre_lift_exclusion'], r['contacts'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--rollout', type=Path, required=True)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--stride', type=int, default=1)
    main(p.parse_args())
