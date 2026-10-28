"""Export strictly train-only VMC label references from a SHA-pinned locked review.

No training, rollout, raw copying, gate adjustment, or independent dynamics replay.
Legacy esn_label_eligible alone is never sufficient: old validation flags may be true.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path, PurePosixPath
import platform
import resource
import sys
import zipfile

from teacher_bank_spark_collection_20260930 import verify_locked_review, sha


RAW_CONTRACT = {
    'rollout.npz': ['observation', 'neuron_time'],
    'teacher_internal.npz': ['request'],
    'execution_chain.npz': ['request', 'filtered_action', 'yield_twist', 'wbc_scale'],
    'rollout_metrics/substep_metrics.npz': ['time', 'dt', 'qfrc_actuator', 'actuator_force'],
}
SUCCESS_KEYS = ('eligible', 'task', 'strict', 'contact', 'esn_label_eligible')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def safe_relative(value):
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe relative path')
    return str(path)


def success_signature(audit):
    # Missing or non-boolean fields are not silently converted to success.
    values = [audit.get(key) for key in SUCCESS_KEYS] + [audit.get('exposure', {}).get('passed')]
    if any(type(value) is not bool for value in values):
        return None
    return values


def parameter_eligibility(request, execution, audit, fixtures, selected, config, plan_sha, source_sha):
    """Bind identity independently of outcome, so failures participate in dedup."""
    reasons = []
    fixture = request.get('fixture', {})
    if fixture.get('split') != 'train' or audit.get('split') != 'train':
        reasons.append('not_train_even_if_legacy_label_flag_true')
    if request.get('method') != 'vmc' or audit.get('method') != 'vmc':
        reasons.append('not_vmc')
    if request.get('phase') not in ('search', 'collection'):
        reasons.append('not_search_or_collection')
    if fixture.get('id') not in fixtures or fixtures.get(fixture.get('id')) != fixture:
        reasons.append('fixture_not_exact_original_train_manifest_entry')
    if audit.get('fixture_id') != fixture.get('id'):
        reasons.append('audit_fixture_mismatch')
    if request.get('x') != selected['x'] or request.get('teacher') != config:
        reasons.append('not_locked_coordinates_and_config')
    if execution.get('status') != 'completed' or execution.get('returncode') != 0:
        reasons.append('not_completed_rc0')
    if request.get('plan_sha256') != plan_sha or execution.get('plan_sha256') != plan_sha:
        reasons.append('plan_binding_mismatch')
    if audit.get('audit_source_sha256') != source_sha:
        reasons.append('audit_source_binding_mismatch')
    return reasons


def deduplicate(records):
    """Fix provenance precedence before outcome; contradictory complete outcomes quarantine."""
    grouped = {}
    for record in records:
        grouped.setdefault(record['identity_sha256'], []).append(record)
    chosen, excluded, quarantined = [], [], []
    for identity, group in sorted(grouped.items()):
        group.sort(key=lambda row: (row['priority'], row['folder']))
        models = {row.get('model_sha256') for row in group}
        if len(models) != 1 or None in models or any(row.get('model_sha256') != row.get('expected_model_sha256') for row in group):
            quarantined.append(dict(identity_sha256=identity, fixture_id=group[0]['fixture_id'],
                reason='different_or_unbound_compiled_model_for_same_fixture_and_parameters',
                attempts=[dict(folder=row['folder'], model_sha256=row.get('model_sha256'),
                               expected_model_sha256=row.get('expected_model_sha256')) for row in group]))
            continue
        signatures = {json.dumps(row['success_signature']) for row in group}
        if len(signatures) != 1 or group[0]['success_signature'] is None:
            quarantined.append(dict(identity_sha256=identity, fixture_id=group[0]['fixture_id'],
                reason='contradictory_or_invalid_complete_success_labels',
                attempts=[dict(folder=row['folder'], success_signature=row['success_signature']) for row in group]))
            continue
        first = group[0]
        if not all(first['success_signature']) or first['failure_reasons']:
            excluded.extend(dict(folder=row['folder'], reasons=['locked_identity_failed_gates'],
                failure_reasons=row['failure_reasons']) for row in group)
            continue
        chosen.append(first)
        excluded.extend(dict(folder=row['folder'], reasons=['duplicate_identity_not_extra_sample'],
            representative=first['folder']) for row in group[1:])
    return chosen, excluded, quarantined


def export(run, review_path, review_sha, metadata, output):
    run, metadata, output = Path(run).resolve(), Path(metadata).resolve(), Path(output).resolve()
    review_path = Path(review_path).resolve()
    if any(output.is_relative_to(tree) for tree in (run, metadata, review_path.parent)):
        raise ValueError('Output must be outside the original run and immutable review/snapshot trees')
    if output.exists():
        raise FileExistsError('Use a new output path; never replace evidence')
    review, plan, bank = verify_locked_review(review_path, review_sha, metadata)
    if Path(review['original_run']).resolve() != run:
        raise ValueError('Raw run differs from SHA-pinned reviewed run')
    pins = review['metadata_sha256']
    def pinned(name):
        name = safe_relative(name)
        if name not in pins or sha(metadata / name) != pins[name]:
            raise ValueError('Missing or altered pinned metadata: ' + name)
        return json.loads((metadata / name).read_text())
    for prefix, mapping in (('source', plan['sources']), ('source_inputs', plan['source_inputs'])):
        for name, expected in mapping.items():
            if sha(run / prefix / safe_relative(name)) != expected:
                raise ValueError('Runtime source/input differs from reviewed plan: ' + name)
    train = [f for f in pinned('fixtures.json') if f['split'] == 'train']
    fixtures = {f['id']: f for f in train}
    if len(fixtures) != len(train):
        raise ValueError('Duplicate train fixture identities in original manifest')
    plan_sha = pins['plan.json']
    if sha(run / 'plan.json') != plan_sha:
        raise ValueError('Original run plan differs from pinned snapshot')
    model_identity = pinned('fixture_model_identity.json')
    source_sha = plan['sources']['tools/teacher_bank_rollout_20260930.py']
    records, excluded, quarantined = [], [], []
    for name in sorted(pins):
        if not name.endswith('/request.json'):
            continue
        folder = name.rsplit('/', 1)[0]
        request = pinned(name)
        fixture = request.get('fixture', {})
        # Exclude validation before loading any of its raw trajectory files.
        if fixture.get('split') != 'train' or request.get('phase') not in ('search', 'collection'):
            excluded.append(dict(folder=folder, reasons=['not_train_search_or_collection'],
                split=fixture.get('split'), phase=request.get('phase')))
            continue
        if request.get('method') != 'vmc':
            excluded.append(dict(folder=folder, reasons=['not_vmc']))
            continue
        category = fixture.get('category')
        key = f'{category}/vmc'
        if key not in bank:
            excluded.append(dict(folder=folder, reasons=['unknown_category']))
            continue
        selected = bank[key][0]
        config = review['closeout']['reconstructed_groups'][key]['selected_controller_config']
        expected_search = f'search/{category}/vmc/c{selected["index"]:02d}/'
        if request['phase'] == 'search' and not folder.startswith(expected_search):
            excluded.append(dict(folder=folder, reasons=['not_original_selected_search_candidate']))
            continue
        required = ['execution.json', 'audit.json', 'archive_manifest.json']
        if any(f'{folder}/{part}' not in pins for part in required):
            excluded.append(dict(folder=folder, reasons=['incomplete_snapshot_metadata']))
            continue
        execution, audit, archive = (pinned(f'{folder}/{part}') for part in required)
        reasons = parameter_eligibility(request, execution, audit, fixtures, selected, config, plan_sha, source_sha)
        if reasons:
            excluded.append(dict(folder=folder, reasons=reasons, failure_reasons=audit.get('failure_reasons', [])))
            continue
        expected_model = model_identity.get(fixture['id'], {}).get('model_sha256')
        identity = dict(fixture_id=fixture['id'], fixture=fixture, x=selected['x'], config=config,
                        plan_sha256=plan_sha, sources=plan['sources'], source_inputs=plan['source_inputs'],
                        expected_model_sha256=expected_model)
        identity_sha = digest(identity)
        # Both snapshot and original audit/request/execution bytes must match the sealed archive.
        for part in ('request.json', 'audit.json', 'execution.json'):
            expected = pins[f'{folder}/{part}']
            if archive.get(part) != expected or sha(run / folder / part) != expected:
                reasons.append('raw_metadata_archive_hash_mismatch:' + part)
        if audit.get('files_sha256', {}).get('request.json') != pins[name]:
            reasons.append('audit_request_hash_mismatch')
        if reasons:
            quarantined.append(dict(folder=folder, fixture_id=fixture['id'], identity_sha256=identity_sha, reasons=reasons))
            continue
        records.append(dict(folder=folder, fixture_id=fixture['id'], category=category,
            identity_sha256=identity_sha, model_sha256=audit.get('model_sha256'), expected_model_sha256=expected_model,
            priority=0 if request['phase'] == 'search' else 1,
            phase=request['phase'], success_signature=success_signature(audit),
            failure_reasons=audit.get('failure_reasons', []), audit=audit, archive=archive,
            metadata_hashes={part:pins[f'{folder}/{part}'] for part in ('request.json', 'execution.json', 'audit.json', 'archive_manifest.json')},
            config=config, x=selected['x'], seed=fixture['seed'], physical_config_sha256=fixture['physical_config_sha256']))
    chosen, duplicates, conflicts = deduplicate(records)
    excluded.extend(duplicates)
    quarantined.extend(conflicts)
    accepted = {category: [] for category in plan['categories']}
    blocked_identities = {row['identity_sha256'] for row in quarantined if 'identity_sha256' in row}
    for row in chosen:
        folder = row['folder']
        if row['identity_sha256'] in blocked_identities:
            excluded.append(dict(folder=folder, reasons=['same_identity_has_quarantined_provenance']))
            continue
        raw_hashes, errors = {}, []
        for filename, columns in RAW_CONTRACT.items():
            expected = row['archive'].get(filename)
            if not expected or expected != row['audit'].get('files_sha256', {}).get(filename):
                errors.append('missing_or_conflicting_raw_hash:' + filename)
                continue
            path = run / folder / filename
            if not path.is_file() or sha(path) != expected:
                errors.append('raw_hash_mismatch:' + filename)
                continue
            try:
                with zipfile.ZipFile(path) as archive:
                    members = set(archive.namelist())
                if any(column + '.npy' not in members for column in columns):
                    errors.append('raw_column_missing:' + filename)
            except zipfile.BadZipFile:
                errors.append('invalid_npz:' + filename)
            raw_hashes[filename] = expected
        model = run / folder / 'rollout.mjb'
        if (row['archive'].get('rollout.mjb') != row['model_sha256']
                or row['audit'].get('files_sha256', {}).get('rollout.mjb') != row['model_sha256']
                or not model.is_file() or sha(model) != row['model_sha256']):
            errors.append('actual_compiled_model_hash_mismatch')
        else:
            raw_hashes['rollout.mjb'] = row['model_sha256']
        receipt_name = f'archive_receipts/{folder}/receipt.json'
        server = f'{plan["server"]}:{plan["remote"].rstrip("/")}/{folder}'
        if receipt_name not in pins:
            errors.append('missing_pinned_server_archive_receipt')
        else:
            receipt = pinned(receipt_name)
            if receipt.get('verified_path') != server:
                errors.append('receipt_server_path_mismatch')
        if errors:
            quarantined.append(dict(identity_sha256=row['identity_sha256'], fixture_id=row['fixture_id'],
                folder=folder, reasons=errors, no_fallback_to_other_duplicate=True))
            continue
        item = {key:row[key] for key in ('folder','fixture_id','identity_sha256','model_sha256','phase','x','config','seed','physical_config_sha256','metadata_hashes')}
        item.update(server_raw_directory=server, server_raw_files={name:server+'/'+name for name in raw_hashes},
            raw_files_sha256=raw_hashes, server_receipt_sha256=pins[receipt_name],
            archive_verification='SHA-pinned existing verified receipt; exporter does not rehash live server files',
            qualification='Original saved gates and provenance verified; no independent raw dynamics replay')
        accepted[row['category']].append(item)
    result = dict(schema=1, purpose=__doc__, reviewed_run=str(run), review_sha256=review_sha,
        generated_at_utc=datetime.now(timezone.utc).isoformat(), invocation_argv=sys.argv,
        invocation_arguments=dict(run=str(run), review=str(review_path), review_sha=review_sha, metadata=str(metadata), output=str(output)),
        runtime=dict(host=platform.node(), architecture=platform.machine(), python=platform.python_version(),
            executable=sys.executable, versions={name:importlib.metadata.version(name) for name in ('numpy','scipy','mujoco')},
            peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        script_sha256=sha(__file__), review_helper_sha256=sha(Path(__file__).with_name('teacher_bank_spark_collection_20260930.py')),
        metadata_snapshot=str(metadata), plan_sha256=plan_sha, fixture_manifest_sha256=pins['fixtures.json'],
        bank_sha256=pins['teacher_bank.json'], sources=plan['sources'], source_inputs=plan['source_inputs'],
        source_and_input_hashes_verified=True, categories=accepted,
        unique_count_by_category={key:len(value) for key,value in accepted.items()},
        unique_total=sum(map(len, accepted.values())), excluded=excluded, quarantined=quarantined,
        reference_only=True, training_started=False, raw_copied=False, independent_raw_replay=False,
        label_semantics=dict(raw_request='teacher_internal.npz request: original unfiltered action7; execution_chain.npz request must remain distinct.',
            filtered_action='execution_chain.npz filtered_action: action7 after shared action filtering; candidate distillation target, not actual motor torque.',
            actual_execution='execution_chain.npz yield_twist/wbc_scale record servo inputs; rollout_metrics/substep_metrics.npz qfrc_actuator and actuator_force record physical-substep generalized/actuator effort. These are not action7 labels.',
            actor_input='rollout.npz observation canonical48D only; do not add stage, contact truth, fixture parameters, or event times to the learner.'),
        limitations=['Only pinned snapshot attempts are considered; new later attempts require a new terminal review and output.',
            'Legacy label flag may be true for validation; split and exact original train membership are mandatory.',
            'Identical fixture+fixed-parameter repeats do not add independent samples; conflicting success flags quarantine the identity.',
            'Full deterministic NPZ duplicate equality is handled separately; this manifest does not claim it.',
            'No ESN or MuJoCo run is performed. Development dt is retained from the source plan.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'review', 'metadata', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--review-sha', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    report = export(args.run, args.review, args.review_sha, args.metadata, args.output)
    print(json.dumps(dict(unique=report['unique_count_by_category'], excluded=len(report['excluded']),
        quarantine=len(report['quarantined']), output=str(args.output), sha256=sha(args.output))))


if __name__ == '__main__':
    main()
