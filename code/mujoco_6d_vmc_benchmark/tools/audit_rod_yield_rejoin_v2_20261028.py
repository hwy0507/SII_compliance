"""Independent saved-state behavior audit; original v1 receipts stay intact.

Require hand contact, geometric crossing and persistent rejoin BEFORE withdrawal
starts. This development criterion is not frozen-test Task/Strict certification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np


def first_hold(time, mask, duration):
    start = None
    for i, ok in enumerate(mask):
        if not ok:
            start = None
        elif start is None:
            start = i
        if start is not None and time[i] - time[start] >= duration - 1e-9:
            return float(time[start]), float(time[i])
    return None, None


def audit(folder):
    legacy = json.loads((folder/'legacy.json').read_text())
    recipe = json.loads((folder/'recipe.json').read_text())['arguments']
    start = float(legacy['fixture_trigger_time_s'])
    retract_start = start + recipe['push_press'] + recipe['push_hold']
    with np.load(folder/'trajectory.npz') as z:
        saved = {k: z[k] for k in z.files}
    with np.load(folder/'legacy.npz') as z:
        target = z['target'].copy()
    time = saved['time']
    model = mujoco.MjModel.from_binary_path(str(folder/'scene.mjb'))
    data = mujoco.MjData(model)
    rod = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'push_rod_geom')
    hand = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'hand')
    if hand < 0:
        hand = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'fr3_hand')
    if rod < 0 or hand < 0:
        raise ValueError('Missing rod/hand geometry')
    hand_bodies = {hand}
    for b in range(hand+1, model.nbody):
        if int(model.body_parentid[b]) in hand_bodies:
            hand_bodies.add(b)
    hand_geoms = [g for g in range(model.ngeom) if int(model.geom_bodyid[g]) in hand_bodies
                  and (model.geom_contype[g] or model.geom_conaffinity[g])]
    body_names = {mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, b) for b in hand_bodies}
    contact = legacy['contact']
    rod_contact = legacy['panel_audit']['contacts']['push_rod_geom']
    first = rod_contact.get('first_s')
    direction = np.asarray(contact.get('contact_path_direction') or [0., 0., -1.], float)
    direction /= max(np.linalg.norm(direction), 1e-12)
    positions, signed, gaps = [], [], []
    for i, t in enumerate(time):
        data.qpos[:] = saved['qpos'][i]
        data.qvel[:] = saved['qvel'][i]
        data.mocap_pos[:] = saved['mocap_pos'][i]
        data.mocap_quat[:] = saved['mocap_quat'][i]
        mujoco.mj_forward(model, data)
        positions.append(data.xpos[hand].copy())
        signed.append(float((data.xpos[hand]-data.geom_xpos[rod]) @ direction))
        gaps.append(min(float(mujoco.mj_geomDistance(model, data, rod, g, .2, None)) for g in hand_geoms))
    positions, signed, gaps = map(np.asarray, (positions, signed, gaps))
    if len(target) != len(time):
        raise ValueError('unaligned trace length')
    error = positions-target
    transverse = error - (error @ direction)[:, None]*direction
    tube_error = np.linalg.norm(transverse, axis=1)
    before = (time >= max(0., (first or start)-.2)) & (time < (first or start))
    baseline = np.median(transverse[before], axis=0) if before.any() else transverse[0]
    excursion = np.linalg.norm(transverse-baseline, axis=1)
    window = (time >= (first or start)) & (time < retract_start)
    peak_i = int(np.argmax(np.where(window, excursion, -1)))
    yield_ids = np.flatnonzero(window & (excursion >= .004))
    yield_time = float(time[yield_ids[0]]) if len(yield_ids) else None
    margin = float(model.geom_size[rod, 0]) + .025
    approach = (time <= (first or start)) & (signed <= -margin)
    driver = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, 'push_rod_driver')
    held = (time >= start+recipe['push_press']) & np.isclose(saved['ctrl'][:,driver],recipe['push_stroke'],rtol=0,atol=1e-8)
    passed = window & held & (signed >= margin) & (gaps >= .002) & bool(approach.any())
    pass_i = np.flatnonzero(passed)
    pass_time = float(time[pass_i[0]]) if len(pass_i) else None
    mask = passed & (time > (yield_time if yield_time is not None else np.inf)) & (tube_error <= .005)
    rejoin, rejoin_end = first_hold(time, mask, .08)
    checks = dict(
        hand_contact=bool(body_names.intersection(rod_contact.get('bodies', []))),
        approached_from_before_rod=bool(approach.any()),
        yielded_before_withdrawal=bool(window.any() and excursion[peak_i] >= .004),
        crossed_rod_while_held=pass_time is not None,
        persistent_rejoin_before_withdrawal=rejoin_end is not None and rejoin_end < retract_start,
        penetration_within_02mm=float(contact['all_external_max_penetration_m']) <= .0002)
    result = dict(schema='rod-yield-rejoin-audit-v2', status='passed' if all(checks.values()) else 'failed_preserved',
        checks=checks, actual_trigger_s=start, retract_start_s=retract_start,
        contact_bodies=rod_contact.get('bodies', []), hand_bodies=sorted(body_names),
        yield_excursion_m=float(excursion[peak_i]), yield_start_s=yield_time, pass_s=pass_time, rejoin_start_s=rejoin,
        rejoin_confirmed_s=rejoin_end, sample_period_s=float(np.median(np.diff(time))),
        criteria=dict(yield_m=.004, rejoin_tube_m=.005, hold_s=.08, gap_m=.002, crossing_margin_m=margin),
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [folder/'trajectory.npz', folder/'scene.mjb', folder/'legacy.json', folder/'recipe.json', Path(__file__)]},
        limitations='Development criterion, 40ms geometry samples plus substep contact summary. No integration or independent physics replay; not frozen-test Task/Strict.')
    path = folder/'ROD_YIELD_REJOIN_AUDIT_V2.json'
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path)
    print(json.dumps(audit(p.parse_args().folder.resolve()),indent=2))
