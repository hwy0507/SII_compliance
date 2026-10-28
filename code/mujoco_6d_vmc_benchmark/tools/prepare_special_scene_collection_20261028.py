"""Freeze 30 physical initial/drive conditions after three-scene development.

The six validation identities are fixed here, not selected by action loss or
test performance. Development traces are evidence only, never training rows.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from collect_special_scene_actions_20261028 import ALLOWED_PARAMETERS, read, sha, validate


def prepare(root, teacher, references):
    if root.exists():
        raise FileExistsError(root)
    serialized = json.dumps(read(teacher), indent=2, allow_nan=False) + '\n'
    teacher_hash = hashlib.sha256(serialized.encode()).hexdigest()
    evidence, defaults = {}, {}
    for scene, folder in references.items():
        qualification = read(folder/'DEMONSTRATION_QUALIFICATION.json')
        execution = read(folder/'execution.json')
        if qualification['status'] != 'qualified' or execution['scene'] != scene:
            raise ValueError(f'Not qualified: {scene}')
        if execution['teacher_config_sha256'] != teacher_hash:
            raise ValueError('All three reference demonstrations must use the same teacher')
        for name, digest in qualification['input_hashes'].items():
            if sha(folder/name) != digest:
                raise ValueError(f'Stale reference qualification: {scene}/{name}')
        defaults[scene] = {k: v for k,v in execution.get('experiment_environment', {}).items()
                           if k in ALLOWED_PARAMETERS[scene]}
        if scene == 'ball':
            recipe = read(folder/'recipe.json')['arguments']
            for key, argument in [('VMC_BALL_SPEED_MPS','ball_speed'),
                                  ('VMC_BALL_SHIFT_M','shift'),
                                  ('VMC_BALL_HEIGHT_OFFSET_M','ball_height_offset')]:
                defaults[scene][key] = recipe.get(argument, 0.)
        evidence[scene] = dict(folder=str(folder), qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
    if defaults['rod'].get('VMC_ROD_EVENT_STAGE') != 'loaded_lift':
        raise ValueError('Expected qualified loaded-lift rod condition')
    # Prospective local interpolation around the reviewed development point.
    # Validation uses interleaved values, not easier extremes chosen later.
    rod_offsets = [(-.002,-.10), (.002,.10), (-.001,.05), (.001,-.05),
                   (0.,-.10), (0.,.10), (-.002,0.), (.002,0.), (-.001,-.05), (.001,.05)]
    ball_offsets = [(-.2,-.002), (.2,.002), (-.1,.001), (.1,-.001),
                    (0.,-.002), (0.,.002), (-.2,0.), (.2,0.), (-.1,-.001), (.1,.001)]
    entries = []
    for scene in ('rod', 'ball', 'corner'):
        for i in range(10):
            parameters = dict(defaults[scene])
            if scene == 'rod':
                x, delay = rod_offsets[i]
                parameters['VMC_ROD_TARGET_X_M'] = round(float(parameters['VMC_ROD_TARGET_X_M']) + x, 6)
                parameters['VMC_ROD_EVENT_DELAY_S'] = round(float(parameters['VMC_ROD_EVENT_DELAY_S']) + delay, 6)
            elif scene == 'ball':
                speed, shift = ball_offsets[i]
                parameters['VMC_BALL_SPEED_MPS'] = round(float(parameters.get('VMC_BALL_SPEED_MPS',2.4)) + speed, 6)
                parameters['VMC_BALL_SHIFT_M'] = round(float(parameters.get('VMC_BALL_SHIFT_M',.018)) + shift, 6)
            else:
                # Real initial joint-state perturbations, without shifting
                # table collision geometry or changing contact materials.
                parameters['INIT_JOINT_PERTURB_STD_RAD'] = round(.0001 * (i+1), 7)
            identity = f'{scene}_{i:02d}'
            entries.append(dict(id=identity, scene=scene, seed=2026102800+i,
                                split='train' if i < 8 else 'validation',
                                scene_parameters=parameters, folder=str(root/identity/scene)))
    plan = dict(schema='sii-three-real-scenes-collection-plan-v2',
                registered_utc=datetime.now(timezone.utc).isoformat(),
                teacher_config=str(teacher), teacher_file_sha256=sha(teacher), teacher_config_sha256=teacher_hash,
                development_references=evidence, episodes=entries,
                constraints=dict(physics_dt_s=.00005, local_simulators=1, memory_max_bytes=3*1024**3, swap_bytes=0),
                limitations='Local condition variation within the three real scene families; no claim of broad coverage. Development traces excluded. All failures retained; no automatic replacement or test-selected data.')
    root.mkdir(parents=True)
    path = root/'COLLECTION_PLAN.json'
    path.write_text(json.dumps(plan, indent=2, allow_nan=False)+'\n')
    validate(path)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--teacher', type=Path, required=True)
    for scene in ('rod','ball','corner'):
        p.add_argument('--'+scene, type=Path, required=True)
    a=p.parse_args()
    print(prepare(a.output.resolve(),a.teacher.resolve(),{s:getattr(a,s).resolve() for s in ('rod','ball','corner')}))
