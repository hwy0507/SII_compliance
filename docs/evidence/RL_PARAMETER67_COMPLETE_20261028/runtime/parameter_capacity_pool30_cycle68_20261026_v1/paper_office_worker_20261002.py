"""Instrumented local evaluation of the baseline branch's exact frozen v6 MJB.

Only model loading and read-only telemetry differ from the shared worker. No
geometric tuning, task/gate modification or privileged actor input is introduced.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
import optimize_tool_contact_20261002 as worker

V6_SHA = '173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11'
HELDOUT_SHA = 'e9890b9a97ab5f89618a57cf093cb82813e335a1fdfe705ca6ba96c706e322cf'
SENSITIVITY_SHA = 'd9191c98ee76691b449322c6ccfdfbd0522563314730854725309afd2eb1b252'


def evaluation_settings(v6, physics_dt, condition_file=None, condition_id=None):
    if physics_dt not in (.0001,.00005):raise ValueError('Only registered physics resolutions allowed')
    overrides=dict(dt=physics_dt)
    provenance=dict(physics_dt_s=physics_dt,physics_tier='development' if physics_dt==.0001 else 'formal_resolution',
                    geometry_source_sha256=V6_SHA,condition_id=condition_id or 'development_anchor')
    if condition_id is not None:
        condition_sha = worker.sha(condition_file) if condition_file is not None else None
        if condition_sha not in (HELDOUT_SHA, SENSITIVITY_SHA):
            raise ValueError('Exact preregistered heldout file required')
        registered=json.loads(condition_file.read_text())
        condition=next(c for c in registered['conditions'] if c['id']==condition_id)
        overrides.update({k:v for k,v in condition.items() if k!='id'})
        provenance.update(heldout_protocol_sha256=condition_sha,heldout_condition=condition,
                          use='final paired evaluation only, prohibited as training labels or selection feedback')
    elif condition_file is not None:raise ValueError('Condition id required')
    binary=v6/'construction/rollout.mjb'
    assert worker.sha(binary)==V6_SHA
    model=mujoco.MjModel.from_binary_path(str(binary));model.opt.timestep=physics_dt
    buffer=np.empty(mujoco.mj_sizeModel(model),dtype=np.uint8)
    mujoco.mj_saveModel(model,None,buffer)
    expected=hashlib.sha256(buffer.tobytes()).hexdigest()
    if physics_dt==.0001:assert expected==V6_SHA
    provenance['model_sha256']=expected
    return expected,overrides,provenance


def install_binary(v6):
    import fr3_scene
    binary = v6/'construction/rollout.mjb'
    assert worker.sha(binary) == V6_SHA
    protocol = json.loads((v6/'PROTOCOL.json').read_text())
    source = (worker.ROOT/'scripts/fr3_scene.py').read_text()
    needle = '    model = mujoco.MjModel.from_xml_string(xml)'
    assert source.count(needle) == 1
    patch = """    import xml.etree.ElementTree as ET
    v6_root = ET.fromstring(xml)
    v6_edge = v6_root.find(".//geom[@name='office_v5_unexpected_edge']")
    assert v6_edge is not None
    v6_edge.set('pos', V6_POS)
    v6_edge.set('size', V6_SIZE)
    xml = ET.tostring(v6_root, encoding='unicode')
""".replace('V6_POS', repr(' '.join(map(str, protocol['edge_position_m'])))).replace(
        'V6_SIZE', repr(' '.join(map(str, protocol['edge_half_size_m']))))
    replacement = patch+needle+'\n    model = mujoco.MjModel.from_binary_path('+repr(str(binary))+')'
    executed = source.replace(needle, replacement)
    exec(compile(executed, str(Path(fr3_scene.__file__))+'[archived-v6-loader]', 'exec'), fr3_scene.__dict__)
    return executed, protocol


def instrument(output):
    parent = worker.evaluator.EpisodeMetrics
    class ResearchMetrics(parent):
        def __init__(self, env, *args, **kwargs):
            super().__init__(env, *args, **kwargs)
            self.research = dict(hand_position=np.empty((self.capacity, 3), np.float32),
                                 payload_position=np.empty((self.capacity, 3), np.float32),
                                 reference_position=np.empty((self.capacity, 3), np.float32),
                                 dq=np.empty((self.capacity, 7), np.float32),
                                 external_penetration_m=np.zeros(self.capacity, np.float64),
                                 edge_penetration_m=np.zeros(self.capacity, np.float64),
                                 route_cursor=np.empty(self.capacity, np.int16),
                                 contact_force_sum=np.zeros((self.capacity, 6), np.float32))
            self.robot = set(env._push_audit_robot_geom_ids)
            self.payload = env._target_body_id
            self.names = [mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, i) or ''
                          for i in range(env.model.ngeom)]
        def sample(self):
            super().sample()
            i = self.count-1
            env = self.env; m, d = env.model, env.data
            task = env.reference
            self.research['hand_position'][i] = self.scratch.xpos[env._hand_id]
            self.research['payload_position'][i] = self.scratch.xpos[self.payload]
            self.research['reference_position'][i] = task.goals[task.index]
            self.research['dq'][i] = d.qvel[:7]
            self.research['route_cursor'][i] = getattr(task, 'cursors', {}).get(task.index, -1)
            for k, contact in enumerate(d.contact):
                g1, g2 = int(contact.geom1), int(contact.geom2)
                robot_contact = (g1 in self.robot) != (g2 in self.robot)
                external = robot_contact and m.geom_bodyid[g1] != self.payload and m.geom_bodyid[g2] != self.payload
                edge = ('office_v5_unexpected_edge' in (self.names[g1], self.names[g2]) and
                        (robot_contact or m.geom_bodyid[g1] == self.payload or m.geom_bodyid[g2] == self.payload))
                if not (external or edge):
                    continue
                wrench = np.zeros(6)
                mujoco.mj_contactForce(m, d, k, wrench)
                force = float(np.linalg.norm(wrench[:3]))
                if external:
                    self.research['external_penetration_m'][i] = max(self.research['external_penetration_m'][i], -float(contact.dist))
                    self.research['contact_force_sum'][i, 0] += force
                    other = self.names[g2 if g1 in self.robot else g1]
                    group = (1 if 'ball' in other else 2 if ('human' in other or 'person' in other)
                             else 3 if 'push_rod' in other else 5 if 'pillar' in other else None)
                    if group is not None:
                        self.research['contact_force_sum'][i, group] += force
                if edge:
                    self.research['edge_penetration_m'][i] = max(self.research['edge_penetration_m'][i], -float(contact.dist))
                    self.research['contact_force_sum'][i, 4] += force
        def save(self, directory):
            result = super().save(directory)
            np.savez_compressed(output/'research_substeps.npz',
                                **{k: v[:self.count] for k, v in self.research.items()})
            worker.write(output/'research_channels.json', dict(
                source_sha256=worker.sha(Path(__file__)),
                force_columns=['external_robot_sum', 'ball_robot_sum', 'human_robot_sum',
                               'rod_robot_sum', 'edge_robot_or_payload_sum', 'pillar_robot_sum'],
                force_semantics='Sum of contact force magnitudes, not net resultant; live completed mj_step force evaluation',
                position_semantics='Post-integration scratch kinematics, same sampling as native physical metrics',
                actor_access=False, sample_count=self.count,
                telemetry_sha256=worker.sha(output/'research_substeps.npz')))
            return result
    worker.evaluator.EpisodeMetrics = ResearchMetrics


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--v6-input', type=Path, required=True)
    p.add_argument('--physics-dt',type=float,default=.0001)
    p.add_argument('--condition-file',type=Path)
    p.add_argument('--condition-id')
    a, rest = p.parse_known_args()
    output = Path(rest[rest.index('--output')+1]).resolve()
    v6 = a.v6_input.resolve()
    executed, protocol = install_binary(v6)
    expected,overrides,tier=evaluation_settings(v6,a.physics_dt,a.condition_file,a.condition_id)
    worker.EXPECTED_MJB = expected
    worker.RUNTIME_ARGUMENT_OVERRIDES=overrides
    worker.EXTRA_SOURCE_FILES = [Path(__file__)]
    worker.RUNTIME_PROVENANCE = dict(world='office-validation-v6', **tier,
        archived_model=str(v6/'construction/rollout.mjb'), upstream_protocol_sha256=worker.sha(v6/'PROTOCOL.json'),
        executed_constructor_sha256=hashlib.sha256(executed.encode()).hexdigest(),
        upstream_baseline='ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6', wrapper_argv=sys.argv.copy())
    instrument(output)
    sys.argv = [sys.argv[0], *rest]
    try:
        worker.main()
    finally:
        if output.exists():
            (output/'executed_fr3_scene.py.txt').write_text(executed)


if __name__ == '__main__':
    main()
