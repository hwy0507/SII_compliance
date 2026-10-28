"""Three display-only isolated worlds, with the exact new30 demonstration teacher.

These new MJB variants are NOT replacements for the frozen comparison worlds.
Each scene is simulated independently. No result-based tuning or selection.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'outputs/teacher_student_15h_20261012_v3'
RUNTIME = ROOT/'outputs/baseline_local_rl_20261009/runtime'
SCENES = {'passive_corner': 'settle', 'active_short': 'ball', 'active_long': 'rod'}


def worker(out, scene):
    # Use the source that actually collected the newest30 demonstrations.
    sys.path.insert(0, str(PARENT/'source/tools'))
    import paper_office_worker_20261002 as office
    import fr3_scene
    import mujoco
    w = office.worker
    folder = out/scene
    folder.mkdir()
    v6 = RUNTIME/'v6'
    original = v6/'construction/rollout.mjb'
    assert w.sha(original) == office.V6_SHA
    model = mujoco.MjModel.from_binary_path(str(original))
    model.opt.timestep = .00005
    changes = []
    # Keep all names/joints for evaluator compatibility, but remove inactive
    # apparatus from both collision and rendering. No robot geometry is edited.
    for i in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or ''
        inactive = name in ('office_v5_pillar', 'office_v5_pillar_mount', 'office_v5_cup')
        inactive |= (name == 'office_v5_ball_geom' and scene != 'active_short')
        inactive |= name.startswith(('office_v5_person_', 'office_v5_human_'))
        inactive |= name in ('office_v5_upper_arm_geom', 'office_v5_forearm_geom')
        inactive |= (name == 'office_v5_push_rod_geom' and scene != 'active_long')
        inactive |= (scene != 'passive_corner' and name in
                     ('office_v5_corner_face', 'office_v5_unexpected_edge'))
        if inactive:
            assert name.startswith('office_v5_'), 'Never modify robot/payload geometry'
            model.geom_contype[i] = model.geom_conaffinity[i] = 0
            model.geom_rgba[i, 3] = 0
            # Explicit contact pairs can override collision masks; moving the
            # inactive geom outside the workspace also rules those out.
            model.geom_pos[i, 2] -= 10.
            changes.append(name)
    reference = mujoco.MjModel.from_binary_path(str(original))
    retained = [i for i in range(model.ngeom)
                if (mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or '') not in changes]
    import numpy as np
    for field in ('geom_pos', 'geom_contype', 'geom_conaffinity', 'geom_rgba', 'geom_size'):
        np.testing.assert_array_equal(getattr(model, field)[retained], getattr(reference, field)[retained])
    binary = folder/'isolated.mjb'
    mujoco.mj_saveModel(model, str(binary), None)
    choice = json.loads((PARENT/'TEACHER_CHOICE.json').read_text())
    config = folder/'teacher.json'
    w.write(config, choice['selected']['config'])
    executed, _ = office.install_binary(v6)
    assert executed.count(repr(str(original))) == 1
    executed = executed.replace(repr(str(original)), repr(str(binary)))
    exec(compile(executed, 'isolated-display-loader', 'exec'), fr3_scene.__dict__)
    w.EXPECTED_MJB = w.sha(binary)
    w.RUNTIME_ARGUMENT_OVERRIDES = dict(dt=.00005, events=SCENES[scene])
    w.RUNTIME_PROVENANCE = dict(purpose='isolated scene visualization only; not formal evaluation',
        scene=scene, parent_mjb_sha256=w.sha(original), model_sha256=w.sha(binary),
        inactive_geoms=changes, teacher_choice_sha256=w.sha(PARENT/'TEACHER_CHOICE.json'),
        wrapper_sha256=w.sha(Path(__file__)), teacher='new30 teacher_lhs_0; exact frozen source/config')
    w.write(folder/'SCENE.json', w.RUNTIME_PROVENANCE)
    sys.argv = [sys.argv[0], '--reference', str(v6/'esn_original_v2/rollout.json'),
                '--config', str(config), '--output', str(folder/'run'), '--contact-audit']
    w.main()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--worker', choices=SCENES)
    a = p.parse_args()
    out = a.output.resolve()
    if a.worker:
        worker(out, a.worker)
        return
    lock = (ROOT/'outputs/.local-rl-compute.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               MUJOCO_GL='egl', MUJOCO_MENAGERIE_PATH=str(RUNTIME/'menagerie'))
    rows = []
    for scene in SCENES:
        cmd = [sys.executable, str(Path(__file__).resolve()), '--output', str(out), '--worker', scene]
        with (out/(scene+'.log')).open('x') as log:
            rc = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        rows.append(dict(scene=scene, returncode=rc))
        (out/'execution.json').write_text(json.dumps(dict(rows=rows, status='running'), indent=2))
        if rc:
            raise RuntimeError(f'{scene} failed; evidence retained')
    (out/'execution.json').write_text(json.dumps(dict(rows=rows, status='complete'), indent=2))


if __name__ == '__main__':
    main()
