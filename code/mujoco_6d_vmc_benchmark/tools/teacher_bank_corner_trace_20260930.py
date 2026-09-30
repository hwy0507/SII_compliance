"""Offline XML/NPZ broad-phase analysis; no MuJoCo import or model creation."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from teacher_bank_design_20260930 import sha, write


def rotation(quaternion):
    w, x, y, z = np.asarray(quaternion, dtype=float)/np.linalg.norm(quaternion)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def analyze(folder):
    folder = Path(folder)
    root = ET.parse(folder/'rollout.xml').getroot()
    address = 0
    target_qpos = None
    for element in root.find('worldbody').iter():
        if element.tag in ('joint', 'freejoint'):
            kind = element.get('type', 'free' if element.tag == 'freejoint' else 'hinge')
            if element.get('name') == 'target_freejoint':
                target_qpos = address
            address += 7 if kind == 'free' else 4 if kind == 'ball' else 1
    if target_qpos is None:
        raise ValueError('Target freejoint missing')
    target = root.find(".//geom[@name='target_object_geom']")
    half = np.fromstring(target.get('size'), sep=' ')
    result = dict(source=str(folder), files_sha256={n:sha(folder/n) for n in
        ('rollout.xml', 'rollout.npz', 'rollout.json')}, target_qpos_address=target_qpos,
        purpose='offline_AABB_separation_certificate_not_dynamic_collision_test', stages={})
    with np.load(folder/'rollout.npz', allow_pickle=False) as data:
        quat = data['qpos'][:, target_qpos+3:target_qpos+7]
        extent = np.stack([np.abs(rotation(q)) @ half for q in quat])
        center = data['object_position']
        for stage in (3, 4):
            mask = data['stage'] == stage
            low, high = center[mask]-extent[mask], center[mask]+extent[mask]
            times = data['time'][mask]
            row = dict(time_range=times[[0,-1]].tolist(),
                payload_center_min=center[mask].min(axis=0).tolist(),
                payload_center_max=center[mask].max(axis=0).tolist(),
                payload_aabb_min=low.min(axis=0).tolist(),payload_aabb_max=high.max(axis=0).tolist(),
                hand_min=data['hand'][mask].min(axis=0).tolist(),
                hand_max=data['hand'][mask].max(axis=0).tolist(),obstacles={})
            for geom in root.find('worldbody').findall('geom'):
                if not geom.get('name','').startswith('office_v5_corner'):
                    continue
                pos = np.fromstring(geom.get('pos'), sep=' ')
                size = np.fromstring(geom.get('size'), sep=' ')
                q = np.fromstring(geom.get('quat', '1 0 0 0'), sep=' ')
                ext = np.abs(rotation(q)) @ size
                gap = np.maximum((pos-ext)-high, low-(pos+ext))
                separated = np.max(gap, axis=1)
                i = int(np.argmin(separated))
                row['obstacles'][geom.get('name')] = dict(center=pos.tolist(),half_size=size.tolist(),
                    aabb_min=(pos-ext).tolist(),aabb_max=(pos+ext).tolist(),
                    minimum_axis_separation_m=float(separated[i]),closest_time_s=float(times[i]),
                    closest_signed_xyz_gap_m=gap[i].tolist(),
                    all_saved_frames_disjoint=bool(np.all(separated>0)))
            result['stages'][str(stage)] = row
        # Numeric proposal only: let a corner protrude 3 mm into the nominal
        # payload's left edge around mid-lift. Initial gripper clearance and
        # complete dynamics must be checked separately.
        i = int(np.argmin(abs(data['time']-3.8)))
        payload_low=center[i]-extent[i];payload_high=center[i]+extent[i]
        candidate_half=np.array([.012,.010,.020])
        right_edge=payload_low[0]+.003
        underside=payload_high[2]
        result['unvalidated_mid_lift_candidate']=dict(reference_time_s=float(data['time'][i]),
            face_pos=[float(right_edge-candidate_half[0]),float(center[i,1]),float(underside+candidate_half[2])],
            half_size=candidate_half.tolist(),nominal_edge_intrusion_m=.003,
            caution='No initial geometry, hand clearance or dynamic success verified; do not deploy without preflight.')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise RuntimeError('Preserve previous analysis')
    result=analyze(args.folder);write(args.output,result)
    print(json.dumps(result,indent=2,allow_nan=False))
