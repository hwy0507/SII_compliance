"""Freeze24 learned jobs plus one nominal parity; preparation never runs physics."""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from canonical48_paired_deployment_20260924 import frozen_training, sha
from audit_paired_transitions_20260924 import read, require, exact
from prepare_paired_six_fixture_deployment_20260924 import build_jobs, verify_transition_audit

SEEDS = (20260924, 20260925)
MODES = ('parameter6', 'direct7')
FIXTURES = tuple(range(9400, 9406))
OLD_HASH = 'c417038bcc43c79ed52925cb942a7993b2eeb56595a9b731f92167adaf44b011'
PROTOCOL = 'docs/RL_PAIRED_MULTISEED_DEPLOYMENT_PROTOCOL_20260925.md'
ADDITIONS = (
    'tools/prepare_paired_multiseed_deployment_20260925.py',
    'tools/run_paired_multiseed_deployment_20260925.py',
    'tools/report_paired_multiseed_deployment_20260925.py',
    'tools/prepare_paired_six_fixture_deployment_20260924.py',
    'tools/run_paired_six_fixture_deployment_20260924.py',
    'tools/report_paired_six_fixture_20260924.py',
    'scripts/canonical48_paired_deployment_20260924.py',
    'scripts/run_panel_paired_deployment_20260924.py',
)


def absolute(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts, 'Unambiguous absolute input paths required')
    return path.resolve()


def bind(path, inputs):
    path = absolute(str(path))
    digest = sha(path)
    require(str(path) not in inputs or inputs[str(path)] == digest, 'Conflicting bound file')
    inputs[str(path)] = digest
    return digest


def verify_inputs(evidence, inputs):
    require(bool(evidence.get('input_sha256')), 'Audit lacks bound raw inputs')
    for name, expected in evidence['input_sha256'].items():
        require(bind(name, inputs) == expected, 'Audit input changed: '+name)


def canonical_result(result):
    """Only known set fields and output path; no tolerance or outcome exclusions."""
    result = copy.deepcopy(result)
    result['arguments'].pop('output')
    for key in ('pairs', 'robot_geoms', 'robot_bodies', 'other_contacts'):
        result['contact'][key] = sorted(result['contact'][key], key=lambda x: json.dumps(x, sort_keys=True))
    return result


def nominal_parity(reference, current):
    reference, current = Path(reference), Path(current)
    first = {str(p.relative_to(reference)): p for p in reference.rglob('*.npz')}
    second = {str(p.relative_to(current)): p for p in current.rglob('*.npz')}
    require(set(first) == set(second) and len(first) == 5, 'Nominal raw file contract differs')
    arrays, hashes = {}, {}
    for name in sorted(first):
        for path in (first[name], second[name]): hashes[str(path)] = sha(path)
        with np.load(first[name], allow_pickle=False) as a, np.load(second[name], allow_pickle=False) as b:
            require(set(a.files) == set(b.files), 'Nominal raw keys differ')
            for key in a.files:
                require(a[key].dtype == b[key].dtype and np.array_equal(a[key], b[key]), 'Nominal raw values/dtype differ: '+name+':'+key)
                if a[key].dtype.kind in 'bfciu':
                    require(np.isfinite(a[key]).all() and np.isfinite(b[key]).all(), 'Nonfinite nominal raw')
                else:
                    require(a[key].dtype.kind in 'SU', 'Unexpected nonnumeric nominal field')
                arrays[name+':'+key] = dict(shape=list(a[key].shape), exact=True)
    stems = [p/'rollout/rollout' for p in (reference, current)]
    require(sha(stems[0].with_suffix('.mjb')) == sha(stems[1].with_suffix('.mjb')), 'Nominal MJB drift')
    require(canonical_result(read(stems[0].with_suffix('.json'))) == canonical_result(read(stems[1].with_suffix('.json'))), 'Nominal JSON dynamics differ')
    a, b = [read(p.with_suffix('.paired_deployment.json')) for p in stems]
    require(a['mode'] == b['mode'] == 'nominal_train_vmc' and a['nominal_options'] == b['nominal_options'], 'Nominal metadata/options differ')
    with np.load(current/'rollout/paired_policy_trace.npz', allow_pickle=False) as data:
        require(data['policy_action'].shape == (600, 6) and not np.any(data['policy_action']) and not np.any(data['log_scale']), 'Nominal parity must be full600 zero6 from reset')
    for root in (reference, current):
        for name in ('rollout/rollout.json', 'rollout/rollout.mjb', 'rollout/rollout.paired_deployment.json', 'metrics/episode_0/substep_metrics.json'):
            hashes[str(root/name)] = sha(root/name)
    require(read(reference/'metrics/episode_0/substep_metrics.json') == read(current/'metrics/episode_0/substep_metrics.json'), 'Nominal metric summaries differ')
    return dict(passed=True, arrays=arrays, full600=True, model_mjb_sha256=sha(stems[0].with_suffix('.mjb')), input_sha256=hashes)


def check_run(spec, original, inputs):
    seed, mode = spec['seed'], spec['mode']
    require(seed in SEEDS and mode in MODES, 'Undeclared training seed/mode')
    directory = absolute(spec['training_directory'])
    manifest, complete, _ = frozen_training(directory, mode)
    require(manifest['training']['seed'] == seed and complete['seed'] == seed, 'Training seed drift')
    with zipfile.ZipFile(directory/'ppo_final.zip') as archive: model = json.loads(archive.read('data'))
    require(model['seed'] == seed and model['num_timesteps'] == 8192 and model['_n_updates'] == complete['updates'] == 384, 'Wrong final model metadata')
    for name in ('manifest.json', 'COMPLETE.json', 'ppo_final.zip', 'vecnormalize_train_only.pkl'): bind(directory/name, inputs)
    audit_path = absolute(spec['transition_audit'])
    transition = verify_transition_audit(audit_path, directory)
    bind(audit_path, inputs)
    final_path = absolute(spec['final_audit']); final = read(final_path); bind(final_path, inputs)
    require(final['passed'] and final['mode'] == mode and final['seed'] == seed, 'Wrong final independent audit')
    require(final['flat_transition_audit']['sha256'] == sha(audit_path), 'Final and transition audits differ')
    require(final['final_model_metadata'] == dict(num_timesteps=8192, updates=384, seed=seed), 'Final audit model seed/budget differs')
    require(final['frozen_transition_audit'] == read(audit_path), 'Final nested transition evidence differs')
    for name, item in final['final_artifacts'].items():
        require(Path(name).name == name and bind(directory/name, inputs) == item['sha256'], 'Final audited artifact drift')
    require({r['condition'] for r in final['evaluations']} == {'train/zero','train/ppo','validation/zero','validation/ppo'}, 'Missing final evaluation')
    for row in final['evaluations']:
        path = directory/'eval'/row['condition']/'episode_00000/rollout.json'
        require(bind(path, inputs) == row['result_sha256'], 'Final eval result drift')
    zero_path = absolute(spec['zero_parity']); zero = read(zero_path); bind(zero_path, inputs)
    require(zero['passed'] and zero['seed'] == seed and zero['mode'] == mode and zero['reference_seed'] == 20260923, 'Wrong zero parity')
    require(zero['all_zero_episodes_full600'] and zero['same_mode_zero_comparison'], 'Zero evidence is not complete matched-mode parity')
    require(absolute(zero['current_run']) == directory and absolute(zero['reference_run']) == original, 'Zero comparison run mismatch')
    require(set(zero['comparisons']) == {'train', 'validation'} and all(x['passed'] for x in zero['comparisons'].values()), 'Both zero parity splits required')
    verify_inputs(zero, inputs)
    require(str(directory/'manifest.json') in zero['input_sha256'] and str(original/'manifest.json') in zero['input_sha256'], 'Zero parity does not bind both manifests')
    replay_path = absolute(spec['replay']); replay = read(replay_path); bind(replay_path, inputs)
    require(replay['passed'] and replay['samples'] == 600 and replay['mode'] == mode, 'Full600 device replay required')
    require(replay['metadata']['device'] == manifest['device'] == 'cuda', 'Same DGX CUDA deployment required')
    require(replay['metadata']['training_manifest_sha256'] == sha(directory/'manifest.json'), 'Replay manifest mismatch')
    for key in ('checkpoint_sha256', 'normalizer_sha256'):
        require(replay['metadata'][key] == complete[key], 'Replay model mismatch')
    verify_inputs(replay, inputs)
    return manifest, dict(directory=str(directory), device='cuda', manifest_sha256=sha(directory/'manifest.json'),
        checkpoint_sha256=complete['checkpoint_sha256'], normalizer_sha256=complete['normalizer_sha256'],
        transition_audit=transition, transition_audit_path=str(audit_path), final_audit_path=str(final_path),
        zero_parity_path=str(zero_path), replay_path=str(replay_path), replay_sha256=sha(replay_path),
        end_to_end_exact=replay['end_to_end_exact'], seed=seed, mode=mode)


def matrix_keys(jobs):
    keys = [(j['training_seed'], j['method'], j['fixture']['seed']) for j in jobs]
    wanted = {(seed, mode, f) for seed in SEEDS for mode in MODES for f in FIXTURES}
    wanted.add((SEEDS[0], 'nominal_train_vmc', FIXTURES[0]))
    require(len(keys) == len(set(keys)) == 25 and set(keys) == wanted, 'Require exact25-job multiseed matrix')
    return keys


def prepare(request_path, output):
    request_path = absolute(str(request_path)); request = read(request_path); output = absolute(str(output))
    require(not output.exists(), 'Fresh execution output required')
    inputs = {}; bind(request_path, inputs)
    old_path = absolute(request['old_report']['path'])
    require(request['old_report']['sha256'] == OLD_HASH and bind(old_path, inputs) == OLD_HASH, 'Old18 report is not pinned original artifact')
    old = read(old_path); old_archive = absolute(request['old_archive'])
    require(old['all_new_raw_metrics_recomputed'] and old['all_new_original_gate_components_recomputed'], 'Old18 audit incomplete')
    for name in ('COMPLETE.json', 'FINAL_RESULT.json', 'frozen_plan.json', 'execution_manifest.json'):
        bind(old_archive/name, inputs)
    require(read(old_archive/'COMPLETE.json') == old['complete'] and sha(old_archive/'frozen_plan.json') == old['plan_sha256'], 'Old report/archive mismatch')
    require(not (old_archive/'FAILED.json').exists(), 'Old deployment has failed marker')
    originals = {mode: absolute(request['original_training'][mode]) for mode in MODES}
    original_manifests = {}
    for mode, path in originals.items():
        manifest, _, _ = frozen_training(path, mode)
        require(manifest['training']['seed'] == 20260923, 'Original reference is not seed20260923')
        expected = {r['deployment']['training_manifest_sha256'] for r in old['rows'] if r['method'] == mode}
        require(expected == {bind(path/'manifest.json', inputs)}, 'Old18 trained policy does not bind original manifest')
        original_manifests[mode] = manifest
    specs = request['runs']
    require(len(specs) == 4 and {(x['seed'], x['mode']) for x in specs} == {(s,m) for s in SEEDS for m in MODES}, 'Four predeclared runs required')
    training, manifests = {}, []
    for spec in sorted(specs, key=lambda x:(x['seed'],x['mode'])):
        manifest, record = check_run(spec, originals[spec['mode']], inputs)
        original = original_manifests[spec['mode']]
        require({k:v for k,v in manifest['training'].items() if k!='seed'} == {k:v for k,v in original['training'].items() if k!='seed'}, 'Learning recipe changed beyond seed')
        for field in ('fixture_specs','asset_hashes','runtime','device','nominal_options','reward','adapter'):
            require(manifest[field] == original[field], 'Original paired experiment changed: '+field)
        require(manifest['base_protocol_sha256'] == original['protocol_sha256'], 'Base protocol drift')
        require(len(manifest['source_hashes']) == 165 and len(original['source_hashes']) == 163, 'Expected old163/new165 frozen source manifests')
        require(all(manifest['source_hashes'].get(k) == v for k,v in original['source_hashes'].items()), 'Original163 bytes changed')
        training.setdefault(str(spec['seed']), {})[spec['mode']] = record
        manifests.append(manifest)
    for manifest in manifests[1:]:
        for field in ('source_hashes','protocol_sha256','nominal_options','runtime','fixture_specs','asset_hashes','reward'):
            require(manifest[field] == manifests[0][field], 'New runs not paired: '+field)
    sources = dict(manifests[0]['source_hashes'])
    for name in ADDITIONS:
        actual = sha(ROOT/name)
        require(name not in sources or sources[name] == actual, 'New helper would overwrite frozen source')
        sources[name] = actual
    for name, digest in sources.items():
        require((ROOT/name).resolve().is_relative_to(ROOT) and sha(ROOT/name) == digest, 'Use isolated unchanged165-source deployment snapshot: '+name)
    baseline = absolute(request['baseline_results']['path'])
    require(bind(baseline, inputs) == request['baseline_results']['sha256'], 'Original fixture result aggregate drift')
    rows = sorted([r for r in read(baseline)['rows'] if r.get('candidate',{}).get('family') == 'vmc'], key=lambda r:r['fixture']['seed'])
    require([r['fixture']['seed'] for r in rows] == list(FIXTURES), 'Original six VMC fixture commands required')
    old_vmcs = {(r['method'],r['fixture']['seed']):r for r in old['old_eight_method_rows']}
    for row in rows:
        require(bind(row['result'], inputs) == row['result_sha256'] == old_vmcs[('vmc',row['fixture']['seed'])]['result_sha256'], 'Original fixture result not bound to old report')
        for name,value in read(row['result'])['source_sha256'].items():
            require(sources.get('scripts/'+name) == value, 'Original physics source differs')
    jobs = []
    for seed in SEEDS:
        records = training[str(seed)]
        generated = build_jobs(rows, {m:Path(records[m]['directory']) for m in MODES}, {m:'cuda' for m in MODES}, output/str(seed))
        for job in generated:
            if job['method'] in MODES or (seed == SEEDS[0] and job['fixture']['seed'] == 9400):
                job['training_seed'] = seed; jobs.append(job)
    matrix_keys(jobs)
    # Bind every old nominal file before parity/reuse; no old metric recomputation.
    for fixture in FIXTURES:
        directory = old_archive/'nominal_train_vmc'/str(fixture)
        old_row = next(r for r in old['rows'] if r['method']=='nominal_train_vmc' and r['fixture']['seed']==fixture)
        require(sha(directory/'rollout/rollout.json') == old_row['result_sha256'], 'Old nominal raw/result binding differs')
        original = read(directory/'result.json')
        for name,value in original['artifact_sha256'].items():
            require(bind(directory/name, inputs) == value, 'Old nominal artifact changed')
    return dict(status='prepared_not_started', simulations_started=0, total_new_episodes=25,
        learned_episodes=24, parity_episodes=1, jobs=jobs, training=training, output=str(output),
        old_report=str(old_path), old_report_sha256=OLD_HASH, old_archive=str(old_archive),
        nominal_reference=str(old_archive/'nominal_train_vmc/9400'),
        source_sha256=sources, protocol_sha256=sha(ROOT/PROTOCOL), input_sha256=inputs,
        global_worker_cap=4, first_phase='one nominal parity; then four9400; then remaining20',
        aggregation='six fixtures within each training seed; then distribution over three training seeds',
        request=str(request_path), preconditions_all_passed=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('request','jobs-output','plan-output'): parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    require(not args.plan_output.exists(), 'Fresh plan output required')
    plan = prepare(args.request, args.jobs_output)
    require(not args.plan_output.resolve().is_relative_to(Path(plan['output'])), 'Plan must be outside new execution root')
    args.plan_output.parent.mkdir(parents=True, exist_ok=True)
    with args.plan_output.open('x') as stream: json.dump(plan, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(dict(status=plan['status'], jobs=25, simulations_started=0, plan_sha256=sha(args.plan_output))))


if __name__ == '__main__': main()
