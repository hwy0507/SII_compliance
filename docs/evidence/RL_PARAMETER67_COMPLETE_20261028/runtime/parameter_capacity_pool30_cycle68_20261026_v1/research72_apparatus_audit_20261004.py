"""Read the exact public MJB and source identities without running dynamics.

This describes the simulation apparatus, not a biomechanics or safety test.
No MjData, forward pass, integration, actor, or held-out manifest is used.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

import mujoco
import numpy as np


SOURCES = (
    'scripts/fr3_scene.py',
    'scripts/office_complex_scene_v5_20260917.py',
    'scripts/office_contact_scene_20260916.py',
    'scripts/office_task_v4_20260917.py',
    'scripts/planned_hand_corner_20261002.py',
    'scripts/validate_office_apparatus_v5_20260917.py',
    'scripts/wbc_velocity_residual_env.py',
)
MODEL_SHA = 'd4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--execution', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Never overwrite an audit'
    assert mujoco.__version__ == '3.11.0'
    assert sha(args.model) == MODEL_SHA
    record = json.loads(args.execution.read_text())
    assert record['status'] == 'complete'
    provenance = record['runtime_provenance']
    assert provenance['condition_id'] == 'train_000'
    assert provenance['data_role'] == 'train'
    assert provenance['model_sha256'] == MODEL_SHA
    hashes = {name: sha(args.source_root / name) for name in SOURCES}
    assert all(record['source_sha256'][name] == digest for name, digest in hashes.items())
    model = mujoco.MjModel.from_binary_path(str(args.model))
    assert model.opt.timestep == .00005

    def name(kind, index):
        return mujoco.mj_id2name(model, kind, index)

    def rows(count, kind, prefix, fields):
        return [dict(id=i, name=name(kind, i), **{
            field: np.asarray(getattr(model, prefix + field)[i]).tolist()
            for field in fields}) for i in range(count)]

    bodies = rows(model.nbody, mujoco.mjtObj.mjOBJ_BODY, 'body_',
                  ['parentid', 'mass', 'inertia', 'pos', 'quat', 'mocapid', 'jntadr', 'jntnum'])
    joints = rows(model.njnt, mujoco.mjtObj.mjOBJ_JOINT, 'jnt_',
                  ['type', 'bodyid', 'axis', 'range', 'limited', 'stiffness', 'dofadr'])
    for row in joints:
        i = row['dofadr']
        row['first_dof_damping'] = float(model.dof_damping[i])
        row['first_dof_armature'] = float(model.dof_armature[i])
    geoms = rows(model.ngeom, mujoco.mjtObj.mjOBJ_GEOM, 'geom_',
                 ['type', 'bodyid', 'pos', 'quat', 'size', 'contype', 'conaffinity',
                  'condim', 'friction', 'margin', 'gap', 'solref', 'solimp', 'priority'])
    mocap_body_ids = {b['id'] for b in bodies if b['mocapid'] >= 0}
    mocap_geoms = [g for g in geoms if g['bodyid'] in mocap_body_ids]
    geoms = [g for g in geoms if g['contype'] or g['conaffinity']]
    equalities = rows(model.neq, mujoco.mjtObj.mjOBJ_EQUALITY, 'eq_',
                     ['type', 'obj1id', 'obj2id', 'data', 'active0', 'solref', 'solimp'])
    actuators = rows(model.nu, mujoco.mjtObj.mjOBJ_ACTUATOR, 'actuator_',
                    ['trntype', 'trnid', 'ctrlrange', 'forcerange', 'ctrllimited',
                     'forcelimited', 'gainprm', 'biasprm', 'gear'])
    pairs = rows(model.npair, mujoco.mjtObj.mjOBJ_PAIR, 'pair_',
                 ['geom1', 'geom2', 'dim', 'friction', 'solref', 'solimp', 'margin', 'gap'])
    for body_name in ['office_v5_ball', 'target_object', 'office_v5_person',
                      'office_v5_human_hand', 'office_v5_push_rod']:
        assert next(b for b in bodies if b['name'] == body_name)['mocapid'] == -1
    assert not any(e['type'] == int(mujoco.mjtEq.mjEQ_WELD) for e in equalities)
    for joint_name in ['office_v5_ball_free', 'target_freejoint']:
        item = next(j for j in joints if j['name'] == joint_name)
        assert item['type'] == int(mujoco.mjtJoint.mjJNT_FREE)
    trace_hash = sha(args.trace)
    assert trace_hash == record['audit']['trace_sha256']
    with np.load(args.trace, allow_pickle=False) as trace:
        mocap_min = trace['mocap_pos'].min(axis=0).tolist()
        mocap_max = trace['mocap_pos'].max(axis=0).tolist()
        sample_count = len(trace['mocap_pos'])
    result = dict(
        schema='sii-research72-apparatus-readonly-v1',
        created_utc=datetime.now(timezone.utc).isoformat(),
        host=platform.node(), python=sys.executable, numpy=np.__version__,
        mujoco=mujoco.__version__, argv=sys.argv,
        model=str(args.model.resolve()), model_sha256=sha(args.model),
        public_execution=str(args.execution.resolve()), execution_sha256=sha(args.execution),
        trace=str(args.trace.resolve()), trace_sha256=trace_hash,
        saved_mocap_sample_count=sample_count, saved_mocap_pos_min=mocap_min, saved_mocap_pos_max=mocap_max,
        source_root=str(args.source_root.resolve()), source_sha256=hashes,
        audit_source_sha256=sha(__file__),
        threads={k: os.environ.get(k) for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']},
        condition_id='train_000', actor_calls=0, physics_steps=0, heldout_reads=0,
        counts={k: int(getattr(model, k)) for k in ['nq', 'nv', 'nu', 'nbody', 'ngeom', 'njnt', 'neq', 'nmocap', 'npair', 'nexclude']},
        options={k: np.asarray(getattr(model.opt, k)).tolist() for k in
                 ['timestep', 'gravity', 'integrator', 'solver', 'iterations', 'tolerance',
                  'cone', 'impratio', 'disableflags', 'enableflags']},
        arguments=record['arguments'], bodies=bodies, joints=joints,
        collision_geometries=geoms, equalities=equalities, actuators=actuators, explicit_pairs=pairs,
        legacy_mocap_geometries=mocap_geoms,
        checks=dict(exact_model=True, source_matches_public_execution=True,
                    task_apparatus_not_mocap=True, no_weld=True, ball_and_payload_free_joints=True),
        limitations=['No integration, contact-force recomputation, or hardware validation.',
                     'Compiled geometry parameters are not effective combined contact coefficients.',
                     'Drive schedule/control interpretation additionally requires source review.'])
    assert sha(args.model) == MODEL_SHA
    assert sha(args.trace) == trace_hash
    assert all(sha(args.source_root / k) == v for k, v in hashes.items())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(output=str(args.output), sha256=sha(args.output), checks=result['checks'])))


if __name__ == '__main__':
    main()
