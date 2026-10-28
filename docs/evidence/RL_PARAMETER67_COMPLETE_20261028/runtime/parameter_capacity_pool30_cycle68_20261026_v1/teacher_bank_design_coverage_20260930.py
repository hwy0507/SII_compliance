"""Read-only definition coverage; no validation results, NPZ loading or simulator.

Effective-field projection is an extra diagnostic, never a replacement for the
registered fixture hash. It does not certify physical feasibility or task success.
"""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def function_ast_hash(path, name):
    module = ast.parse(path.read_text())
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == name)
    return hashlib.sha256(ast.dump(function, include_attributes=False).encode()).hexdigest()


def effective(fixture):
    active = dict(fixture['active_physical_parameters'])
    ignored = []
    if fixture['category'] == 'passive_corner':
        ignored.append('corner_placement_rule')  # prose annotation, not read by XML adapter
    if fixture['category'] == 'active_long' and fixture['object_shape'] == 'paddle':
        ignored.append('rod_radius_m')  # paddle branch uses constant box dimensions
    for key in ignored:
        active.pop(key, None)
    return active, ignored


def distribution(values):
    v = np.asarray(values, dtype=float)
    assert np.isfinite(v).all()
    minimum, q05, median, q95, maximum = np.quantile(v, [0, .05, .5, .95, 1])
    return dict(count=len(v), min=float(minimum), p05=float(q05), median=float(median),
                p95=float(q95), max=float(maximum))


def fields(f):
    values = {'payload_mass_kg': f['payload_mass_kg']}
    category = f['category']
    if category == 'passive_corner':
        values.update({key:f[key] for key in ('corner_right_x_m','corner_center_y_m',
            'corner_bottom_z_m','corner_friction')})
        values['corner_yaw_deg'] = float(np.rad2deg(f['corner_yaw_rad']))
    else:
        values['start_s'] = f['start_s']
        values['relative_horizontal_yaw_deg'] = float(np.rad2deg(f['yaw_rad']))
        angle = np.rad2deg(f['yaw_rad'])+(90. if category == 'active_short' else 180. if f['apparatus'] == 'person' else 0.)
        values['world_push_heading_deg_unwrapped'] = float(angle)
        values['push_axis_vertical_component'] = f['axis'][2]
        if category == 'active_short':
            values.update({key:f[key] for key in ('ball_speed_mps','ball_mass_kg','ball_radius_m')})
            values['initial_momentum_proxy_kg_mps'] = f['ball_mass_kg']*f['ball_speed_mps']
            values['initial_kinetic_energy_proxy_j'] = .5*f['ball_mass_kg']*f['ball_speed_mps']**2
            for j, axis in enumerate('xyz'):
                values['launch_'+axis+'_m'] = f['launch_position_m'][j]
        else:
            values.update({key:f[key] for key in ('press_s','hold_s','retract_s','stroke_m','drive_limit_n')})
            values['stroke_over_press_speed_proxy_mps'] = f['stroke_m']/f['press_s']
            values['retract_start_s'] = f['start_s']+f['press_s']+f['hold_s']
            if f['apparatus'] == 'rod':
                values['rod_mass_kg'] = f['rod_mass_kg']
                if f['object_shape'] == 'rod': values['rod_radius_m'] = f['rod_radius_m']
            for j, axis in enumerate('xyz'):
                values['nominal_aim_'+axis+'_m'] = f['target_nominal_m'][j]
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--preflight-dir', required=True, type=Path)
    parser.add_argument('--preflight-source-run', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root, output = args.run.resolve(), args.output.resolve()
    if output.exists() or root == output or root in output.parents:
        raise ValueError('New output directory outside immutable run required')
    plan = json.loads((root/'plan.json').read_text())
    fixtures = json.loads((root/'fixtures.json').read_text())
    assert sha(root/'fixtures.json') == plan['fixtures_sha256']
    sources = {name:dict(expected=value, actual=sha(root/'source'/name)) for name,value in plan['sources'].items()}
    assert all(v['expected'] == v['actual'] for v in sources.values())
    counts, apparatus_counts = Counter(), Counter()
    groups = defaultdict(lambda: defaultdict(list))
    registered, projected, records = defaultdict(list), defaultdict(list), []
    unused = Counter()
    for fixture in fixtures:
        registered_hash = digest(fixture['active_physical_parameters'])
        assert registered_hash == fixture['physical_config_sha256']
        assert all(fixture[key] == value for key,value in fixture['active_physical_parameters'].items())
        projection, ignored = effective(fixture)
        projected_hash = digest(projection)
        key = (fixture['category'], fixture['split'], fixture['object_shape'])
        counts[key] += 1
        if fixture['category'] == 'active_long': apparatus_counts[(fixture['split'],fixture['apparatus'])] += 1
        for name, value in fields(fixture).items(): groups[key][name].append(value)
        entry = dict(id=fixture['id'], split=fixture['split'], seed=fixture['seed'], category=fixture['category'],
            registered_hash=registered_hash, effective_projection_hash=projected_hash,
            ignored_registered_fields=ignored)
        records.append(entry); registered[registered_hash].append(entry); projected[projected_hash].append(entry)
        unused.update(ignored)
    def duplicates(mapping):
        return [[v['id'] for v in rows] for rows in mapping.values() if len(rows)>1]
    overlap = [[v['id'] for v in rows] for rows in projected.values()
               if {v['split'] for v in rows} == {'train','validation'}]
    adapter = root/'source/tools/teacher_bank_rollout_20260930.py'
    prior_adapter = args.preflight_source_run/'source/tools/teacher_bank_rollout_20260930.py'
    preflights = []
    for category in plan['categories']:
        path = args.preflight_dir/('v8_'+category+'.json')
        value = json.loads(path.read_text())
        preflights.append(dict(path=str(path.resolve()), sha256=sha(path), category=category,
            fixture_hash_matches_v10=value['fixtures_sha256'] == plan['fixtures_sha256'],
            saved_adapter_hash_matches_prior_source=value['adapter_sha256'] == sha(prior_adapter),
            full_adapter_hash_matches_v10=value['adapter_sha256'] == sha(adapter),
            training_xml_ast_equal_v8_v10=function_ast_hash(prior_adapter,'training_xml') == function_ast_hash(adapter,'training_xml'),
            training_xml_ast_sha256=function_ast_hash(adapter,'training_xml'),
            train_indices=value['train_indices'], rows=value['rows'],
            purpose=value['purpose'], task_success_verified=value['task_success_verified'],
            dynamic_contact_verified=value['dynamic_contact_verified']))
    identity_path = root/'fixture_model_identity.json'
    identities = json.loads(identity_path.read_text())
    result = dict(scope='Definition coverage only; no validation results read and no dynamics executed',
        run=str(root), script_sha256=sha(Path(__file__)),
        plan_sha256=sha(root/'plan.json'), fixtures_sha256=sha(root/'fixtures.json'), sources=sources,
        definition_count=len(fixtures), split_counts=dict(Counter(f['split'] for f in fixtures)),
        category_split_shape_counts=[dict(category=c, split=s, shape=o, count=n)for (c,s,o),n in sorted(counts.items())],
        active_long_apparatus_counts=[dict(split=s, apparatus=a, count=n)for (s,a),n in sorted(apparatus_counts.items())],
        unique_ids=len({f['id'] for f in fixtures}), unique_seeds=len({f['seed'] for f in fixtures}),
        registered_unique_physical_hashes=len(registered), registered_duplicate_groups=duplicates(registered),
        effective_projection_unique_hashes=len(projected), effective_projection_duplicate_groups=duplicates(projected),
        effective_projection_train_validation_exact_overlap=overlap,
        ignored_registered_field_counts=dict(unused),
        effective_projection_caveat='Additional consumed-field diagnostic only; original hashes unchanged. Drops descriptive corner_placement_rule and unused paddle rod_radius_m. This is not a compiled-MuJoCo-model hash or a dynamics validity certificate; numeric near-duplicates are not ruled out.',
        parameter_distributions=[dict(category=c, split=s, shape=o,
            parameters={name:distribution(vals) for name,vals in values.items()}) for (c,s,o),values in sorted(groups.items())],
        sampling_scope=dict(horizontal_only=True, vertical_axis_component=0.,
            active_relative_yaw_domain_rad=[-.6,.6], passive_corner_yaw_domain_rad=[-.25,.25],
            short_launch_time_domain_s=[2.,12.], short_speed_domain_mps=[1.,2.2],
            short_mass_domain_kg=[.08,.28], short_radius_domain_m=[.025,.045],
            long_press_domain_s=[1.,2.5], long_hold_domain_s=[2.,8.], long_stroke_domain_m=[.15,.23],
            person_drive_limit_domain_n=[45.,90.], rod_drive_limit_domain_n=[8.,18.],
            caveat='Drive caps, momentum and energy are input-strength proxies, not measured impact/contact force. Passive corner has no independently varied hit schedule or drive force; contact timing/force emerge from motion, geometry and controller.'),
        per_fixture_hash_inventory=records, prior_preflight=preflights,
        v10_compiled_model_identity_metadata=dict(sha256=sha(identity_path), count=len(identities),
            fixture_ids=sorted(identities), caveat='Previously recorded model identity for search anchors only, not 3300 compiled or successful environments'),
        outcome_claims=dict(valid_dynamic_trajectories_count='not_measured_by_this_audit',
            heldout_success='not_read', all_definitions_dynamic_validity_verified=False))
    output.mkdir(parents=True)
    (output/'coverage.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    lines = ['# Frozen v10 design coverage (definitions only)', '',
        f'Defined: {len(fixtures)} = train {result["split_counts"]["train"]} + validation {result["split_counts"]["validation"]}. No validation outcomes read.', '',
        '| Category | Split | Shape | Count |', '|---|---|---|---:|']
    lines += [f'| {c} | {s} | {o} | {n} |'for (c,s,o),n in sorted(counts.items())]
    lines += ['',f'Registered unique physical hashes: {len(registered)}; effective-field projection unique hashes: {len(projected)}; exact train/validation overlaps: {len(overlap)}.',
        '', 'The projection is diagnostic and preserves original fixtures/hashes. Paddle radius is registered but not consumed (fixed box); corner_placement_rule is descriptive text. Other category-unused random fields are already excluded from registered active_physical_parameters.',
        '', 'Active yaw is horizontal ±34.38° around the nominal direction; person actual push is -axis, rod is +axis, ball heading is 90°+yaw. No vertical impact-angle sweep. Passive corner yaw is ±14.32°; its timing and force are emergent, not independently sampled.',
        '', 'Ball input ranges: start 2–12 s, speed 1–2.2 m/s, mass 0.08–0.28 kg, radius 0.025–0.045 m. Long push: press 1–2.5 s, hold 2–8 s, stroke 0.15–0.23 m, cap 45–90 N (person) or 8–18 N (rod). These are design domains, with realized min/5th/median/95th/max per split and shape in coverage.json. Force caps, initial momentum/energy are not measured impact forces.',
        '', 'Prior v8 production preflight: 6 train indices per category, 18 t=0 initial checks; fixture hash and training_xml AST match v10, but full adapter hash differs. They remain prior initial-geometry checks, not fresh v10 dynamics verification. v10 model-identity metadata currently covers '+str(len(identities))+' search anchors only.',
        '', '3300 distinct definitions do not establish 3300 feasible contacts, valid executions, successful tasks or usable teacher trajectories. No such outcome claim is made.',
        '', 'Script SHA256: `'+result['script_sha256']+'`', 'Fixtures SHA256: `'+result['fixtures_sha256']+'`']
    (output/'coverage.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(output=str(output), definitions=len(fixtures), registered_unique=len(registered),
                         effective_unique=len(projected), exact_split_overlap=len(overlap), sha256=sha(output/'coverage.json'))))


if __name__ == '__main__': main()
