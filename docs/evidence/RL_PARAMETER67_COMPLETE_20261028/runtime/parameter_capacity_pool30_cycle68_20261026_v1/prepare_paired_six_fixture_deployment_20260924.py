"""Prepare a frozen18-job plan after model/replay audits; NEVER launches a job."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from canonical48_paired_deployment_20260924 import frozen_training, sha


def audit_directory(raw, original_run, training):
    path, origin = Path(raw), Path(original_run)
    if '..' in path.parts or not origin.is_absolute():
        raise ValueError('Ambiguous audit path or path traversal')
    if path.is_absolute():
        relative = path.relative_to(origin)
    else:
        # An audit may save a cwd-relative run while its top-level run is absolute.
        # Bind its entire run-prefix as an exact suffix of the original run path.
        matches = []
        for index, part in enumerate(path.parts):
            if part not in ('train','eval') or index==0:
                continue
            prefix = path.parts[:index]
            if len(prefix)<=len(origin.parts) and origin.parts[-len(prefix):]==prefix:
                matches.append(Path(*path.parts[index:]))
        if len(matches)!=1:
            raise ValueError('Cannot uniquely map original audit episode path')
        relative = matches[0]
    if not relative.parts or relative.parts[0] not in ('train','eval'):
        raise ValueError('Audit episode is not a train/eval episode')
    target = (training/relative).resolve()
    if not target.is_relative_to(training.resolve()):
        raise ValueError('Audit episode escapes current training directory')
    return target


def verify_transition_audit(path, training):
    audit = json.loads(path.read_text())
    manifest = json.loads((training/'manifest.json').read_text())
    if not audit['passed'] or audit['manifest_sha256'] != sha(training/'manifest.json'):
        raise ValueError('Independent transition audit missing or manifest mismatch')
    if audit['training_transitions'] != 8192:
        raise ValueError('Wrong transition audit budget')
    sb3 = audit['sb3_received_rewards']
    if not sb3 or sb3['transitions'] != 8192 or not sb3['all_float32_conversions_exact']:
        raise ValueError('Missing independent8192-step SB3 conversion proof')
    paths, counted, empty_hashes = set(), 0, {}
    for episode in audit['episodes']:
        directory = audit_directory(episode['directory'],audit['run'],training)
        if directory in paths:
            raise ValueError('Duplicate audited episode')
        paths.add(directory)
        if episode['transitions'] == 0:
            if not episode.get('empty_reset'):
                raise ValueError('Unexplained empty audit episode')
            if (directory/'transitions.jsonl').read_text().strip():
                raise ValueError('Audited empty episode became nonempty')
            empty_hashes[str(directory/'transitions.jsonl')] = sha(directory/'transitions.jsonl')
            continue
        if episode['mode'] != manifest['mode']:
            raise ValueError('Audited episode is another policy branch')
        if not all(key in episode['hashes'] for key in ('transitions.jsonl','transitions.npz','actor_trace.npz','transition_contract.json')):
            raise ValueError('Incomplete episode hashes')
        for name, expected in episode['hashes'].items():
            if Path(name).name!=name or sha(directory/name) != expected:
                raise ValueError('Audited episode file drift/path escape')
        if directory.relative_to(training.resolve()).parts[0] == 'train':
            counted += episode['transitions']
    actual = {p.parent.resolve() for p in training.rglob('transitions.jsonl')}
    if paths != actual or counted != 8192:
        raise ValueError('Independent audit does not cover all original episodes')
    received = [json.loads(line) for line in (training/'sb3_received_rewards.jsonl').read_text().splitlines()]
    journal = [json.loads(line) for p in sorted((training/'train').rglob('transitions.jsonl')) for line in p.read_text().splitlines()]
    if len(received) != 8192 or len(journal) != 8192:
        raise ValueError('Original SB3/Gym logs do not contain8192 transitions')
    import numpy as np
    for i, (entry, row) in enumerate(zip(received,journal)):
        if entry['step'] != i+1 or entry['done'] != row['terminated'] or entry['gym_float64'] != row['reward'] or entry['sb3_float32'] != float(np.float32(row['reward'])) or entry['reward_terms'] != row['reward_terms']:
            raise ValueError('SB3 received-reward evidence drift')
    return dict(audit_sha256=sha(path),manifest_sha256=audit['manifest_sha256'],training_transitions=8192,
        sb3_received_rewards_sha256=sha(training/'sb3_received_rewards.jsonl'),all_episode_hashes_verified=True,
        episodes=len(paths),audit_tool_sha256=audit.get('audit_tool_sha256'),original_audit_run=audit['run'],
        empty_journal_hashes_bound_at_prepare=empty_hashes)


def build_jobs(rows, training, devices, output):
    jobs = []
    for row in rows:
        for mode in ('parameter6','direct7','nominal_train_vmc'):
            branch = 'parameter6' if mode == 'nominal_train_vmc' else mode
            seed = row['fixture']['seed']
            job = output/mode/str(seed)
            stem = job/'rollout/rollout'
            original = row['command']
            params = list(original[original.index('--')+1:])
            if '--model' in params:
                raise ValueError('Use original VMC command, not student command')
            params[params.index('--output')+1] = str(stem)
            params.extend(['--paired-mode',mode,'--training-directory',str(training[branch]),
                           '--deployment-device',devices[branch]])
            environment = dict(row['environment'],PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py'))
            jobs.append(dict(method=mode,fixture=row['fixture'],job=str(job),result=str(stem.with_suffix('.json')),
                command=[sys.executable,str(ROOT/'scripts/run_with_substep_metrics_20260923.py'),
                    '--runner',str(ROOT/'scripts/run_panel_paired_deployment_20260924.py'),
                    '--metrics-output',str(job/'metrics'),'--',*params],
                environment=environment,expected_mjb_sha256=row['model_mjb_sha256'],
                reference_result=row['result'],reference_result_sha256=row['result_sha256'],
                adapter_nominal_source=str(training['parameter6']/'manifest.json') if mode!='direct7' else None))
    return jobs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-results',type=Path,required=True)
    p.add_argument('--parameter-training',type=Path,required=True)
    p.add_argument('--direct-training',type=Path,required=True)
    p.add_argument('--parameter-replay',type=Path,required=True)
    p.add_argument('--direct-replay',type=Path,required=True)
    p.add_argument('--parameter-transition-audit',type=Path,required=True)
    p.add_argument('--direct-transition-audit',type=Path,required=True)
    p.add_argument('--jobs-output',type=Path,required=True)
    p.add_argument('--plan-output',type=Path,required=True)
    args = p.parse_args()
    training = dict(parameter6=args.parameter_training.resolve(),direct7=args.direct_training.resolve())
    replays = dict(parameter6=args.parameter_replay,direct7=args.direct_replay)
    audits = dict(parameter6=args.parameter_transition_audit,direct7=args.direct_transition_audit)
    devices, records, manifests = {}, {}, {}
    inputs = {str(args.baseline_results):sha(args.baseline_results)}
    for mode in training:
        manifest, complete, _ = frozen_training(training[mode],mode)
        for name, expected in manifest['source_hashes'].items():
            source=(ROOT/name).resolve()
            if not source.is_relative_to(ROOT) or sha(source)!=expected:
                raise ValueError('Full training source differs from deployment ROOT; use isolated frozen training snapshot plus new deployment files: '+name)
        audit_evidence = verify_transition_audit(audits[mode],training[mode])
        replay = json.loads(replays[mode].read_text())
        if not replay['passed'] or replay['samples']!=600 or replay['mode']!=mode:
            raise ValueError('Full600-frame deployment replay required')
        for key in ('checkpoint_sha256','normalizer_sha256'):
            if replay['metadata'][key] != complete[key]:
                raise ValueError('Replay belongs to another frozen model')
        if replay['metadata']['training_manifest_sha256'] != sha(training[mode]/'manifest.json'):
            raise ValueError('Replay training manifest drift')
        for path, value in replay['input_sha256'].items():
            if sha(path) != value:
                raise ValueError('Replay input/source drift: '+path)
        devices[mode] = replay['metadata']['device']
        records[mode] = dict(directory=str(training[mode]),checkpoint_sha256=complete['checkpoint_sha256'],
            normalizer_sha256=complete['normalizer_sha256'],manifest_sha256=sha(training[mode]/'manifest.json'),
            replay_sha256=sha(replays[mode]),device=devices[mode],end_to_end_exact=replay['end_to_end_exact'])
        records[mode]['transition_audit'] = audit_evidence
        manifests[mode] = manifest
        inputs[str(replays[mode])] = sha(replays[mode])
        inputs[str(audits[mode])] = sha(audits[mode])
    for field in ('training','fixture_specs','source_hashes','asset_hashes','reward','nominal_options','runtime','protocol_sha256'):
        if manifests['parameter6'][field]!=manifests['direct7'][field]:
            raise ValueError('Paired training protocol mismatch: '+field)
    all_rows = json.loads(args.baseline_results.read_text())['rows']
    rows = sorted([r for r in all_rows if r.get('candidate',{}).get('family')=='vmc'],key=lambda r:r['fixture']['seed'])
    if [r['fixture']['seed'] for r in rows] != list(range(9400,9406)):
        raise ValueError('Require exact original six fixture commands')
    for row in rows:
        if sha(row['result'])!=row['result_sha256']:
            raise ValueError('Original fixture evidence hash drift')
        result = json.loads(Path(row['result']).read_text())
        for name, expected in result['source_sha256'].items():
            if sha(ROOT/'scripts'/name) != expected:
                raise ValueError('Original deployment physics/source drift: '+name)
    protocol = ROOT/'docs/RL_PAIRED_SIX_FIXTURE_DEPLOYMENT_PROTOCOL_20260924.md'
    files = ('scripts/canonical48_paired_deployment_20260924.py','scripts/run_panel_paired_deployment_20260924.py',
        'tools/audit_paired_deployment_replay_20260924.py','tools/prepare_paired_six_fixture_deployment_20260924.py',
        'tools/run_paired_six_fixture_deployment_20260924.py','tools/audit_paired_transitions_20260924.py',
        'scripts/canonical48_vmc_tuning_20260924.py','scripts/run_vmc_6d_constrained_push_20260918.py',
        'scripts/run_panel_push_20260920.py','scripts/run_primitive_teacher_v7_20260917.py',
        'scripts/run_with_substep_metrics_20260923.py','scripts/physics_substep_metrics_20260923.py')
    combined_sources=dict(manifests['parameter6']['source_hashes'])
    for name in files:
        actual=sha(ROOT/name)
        if name in combined_sources and combined_sources[name]!=actual:
            raise ValueError('Cannot override frozen source hash: '+name)
        combined_sources[name]=actual
    plan = dict(status='prepared_not_started',jobs=build_jobs(rows,training,devices,args.jobs_output.resolve()),
        training=records,protocol_sha256=sha(protocol),input_sha256=inputs,
        source_sha256=combined_sources,full_training_source_file_count=len(manifests['parameter6']['source_hashes']),simulations_started=0,
        total_new_episodes=18,global_worker_cap=4,launch_requires_coordinator_resource_check=True,
        nominal_control='zero6 with full training options, not original fixture-VMC and not zero7',
        zero7_reuse='Only after actual new per-fixture MJB, common runtime/source/config and original archive checks; not assumed by this plan',
        preflight='First parameter6/direct7/nominal_train_vmc at9400; verify all raw policy traces, model/physics before remaining15',
        invalid_physics='Retain genuine safety early termination; do not confuse with execution error or retry selectively')
    args.plan_output.parent.mkdir(parents=True,exist_ok=True)
    with args.plan_output.open('x') as stream:
        json.dump(plan,stream,indent=2,allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=plan['status'],jobs=len(plan['jobs']),simulations_started=0)))


if __name__ == '__main__':
    main()
