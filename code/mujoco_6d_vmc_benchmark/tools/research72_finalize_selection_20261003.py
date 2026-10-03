"""Combine public selections and outcome-independent RL boundary checkpoints.

No heldout access. This is a candidate ledger, not the model lock or unseal.
All six learned families, all five RL families and all five deterministic
references are mandatory, including development failures.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import json
from research72_final_lock_20261003 import read, sha, verify_candidates

LEARNED = {'esn', 'memoryless', 'ordinary_mlp', 'ordinary_rnn', 'matched_mlp', 'matched_rnn'}
CLASSICAL = {'enhanced_teacher', 'classical_admittance', 'classical_impedance', 'classical_vmc'}


def combine(learned, controllers, nominal, reinforcement, seeds, rl_families):
    candidates = [*learned, *controllers, nominal, *reinforcement]
    assert len({c['name'] for c in candidates}) == len(candidates)
    assert {c['category'] for c in learned} == LEARNED
    assert {c['category'] for c in controllers} == CLASSICAL and len(controllers) == 4
    assert nominal['category'] == 'nominal_zero' and nominal['nominal'] is True
    assert {c['category'] for c in reinforcement} == set(rl_families)
    groups = []
    for family in sorted(LEARNED | set(rl_families)):
        members = sorted([c for c in candidates if c['category'] == family], key=lambda c: c['seed'])
        assert len(members) == len(seeds) and {c['seed'] for c in members} == set(seeds)
        assert len({c.get('variant') for c in members}) == 1
        groups.append(dict(name=family, names=[c['name'] for c in members]))
    assert len(candidates) == (len(LEARNED)+len(rl_families))*len(seeds)+5
    return candidates, groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'learning-selection', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); root = args.root.resolve(); output = args.output.resolve()
    assert not output.exists()
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    protocol = read(root/'PROTOCOL.json'); digest = sha(root/'PROTOCOL.json')
    seeds = protocol['budget_caps']['training_seeds']; families = protocol['budget_caps']['rl_families']
    learning = read(args.learning_selection)
    assert learning['protocol_sha256'] == digest
    evidence = [*learning['development_evidence'],
                dict(path=str(args.learning_selection.resolve()), sha256=sha(args.learning_selection))]
    completion = list(learning['completion_receipts'])
    for row in evidence:
        assert sha(row['path']) == row['sha256']
    for row in completion:
        assert sha(row['path']) == row['sha256'] and read(row['path'])['status'] == 'complete'
    for name in ('followup_v1', 'additional_development_v1', 'context_gate_development_v1',
                 'rl_office_adaptation_v1', 'final_rehearsal_v1'):
        path = root/name/'execution.json'
        assert read(path)['status'] == 'complete', 'Public predecessor incomplete: '+name
        completion.append(dict(path=str(path), sha256=sha(path)))
    choice_path = root/'followup_v1/CONTROLLER_CHOICE.json'; choice = read(choice_path)
    assert choice['protocol_sha256'] == digest
    assert choice['outcome'] == 'one per family selected on all eight development identities'
    evidence.append(dict(path=str(choice_path), sha256=sha(choice_path)))
    confirmation = root/'controller_confirmation_v1'
    for name, field in (('SPECIFICATION.json', 'screen_spec_sha256'), ('SUMMARY.json', 'screen_summary_sha256')):
        path = confirmation/name; assert sha(path) == choice[field]
        evidence.append(dict(path=str(path), sha256=sha(path)))
    assert read(confirmation/'execution.json')['status'] == 'complete'
    completion.append(dict(path=str(confirmation/'execution.json'), sha256=sha(confirmation/'execution.json')))
    teacher_path = root/'teacher_refinement_v1/execution.json'; teacher = read(teacher_path)
    assert teacher['choice_sha256'] == sha(choice_path)
    skip = teacher['status'] == 'complete_skipped_identical_teacher'
    if skip:
        selected = next(c for c in choice['candidates'] if c['category'] == 'enhanced_teacher')
        assert sha(root/'teacher.json') == protocol['teacher_config_sha256']
        assert teacher['new_physics_episodes'] == 0
        assert teacher['selected_teacher'] == selected and selected['config'] == read(root/'teacher.json')
    else:
        assert teacher['status'] == 'complete'
        completion.append(dict(path=str(teacher_path), sha256=sha(teacher_path)))
    evidence.append(dict(path=str(teacher_path), sha256=sha(teacher_path)))
    nominal_path = root/'additional_development_v1/NOMINAL_SPECIFICATION.json'; nominal = read(nominal_path)
    assert nominal['protocol_sha256'] == digest and len(nominal['candidates']) == 1
    evidence.append(dict(path=str(nominal_path), sha256=sha(nominal_path)))
    rl = root/'rl_office_adaptation_v1'; spec_path = rl/'SPECIFICATION.json'; spec = read(spec_path)
    assert spec['protocol_sha256'] == digest
    jobs = {j['name']: j for j in spec['jobs']}
    assert len(jobs) == len(families)*len(seeds)
    reinforcement = []; seen = set()
    for path in sorted(rl.glob('queue_[0-2]/execution.json')):
        state = read(path); assert state['status'] == 'complete'
        completion.append(dict(path=str(path), sha256=sha(path)))
        for row in state['rows']:
            job = jobs[row['name']]; assert row['name'] not in seen; seen.add(row['name'])
            manifest_path = Path(row['latest_manifest']); manifest = read(manifest_path)
            assert sha(manifest_path) == row['latest_manifest_sha256']
            assert manifest['family'] == job['family'] and manifest['seed'] == job['seed']
            assert manifest['controller'] == job['controller']
            assert 0 < manifest['cumulative_physics_steps'] <= protocol['budget_caps']['rl_adaptation_steps_per_family_seed']
            # Latest completed finite boundary is selected without examining
            # reward, task outcome or any evaluation trajectory.
            latest = row['segments'][-1]
            assert latest['returncode'] == 0 and latest['cumulative_steps'] == manifest['cumulative_physics_steps']
            training_path = path.parent/row['name']/latest['stage']/'execution.json'; training = read(training_path)
            assert sha(training_path) == latest['execution_sha256'] and training['status'] == 'complete'
            assert training['checkpoint_rows'][-1]['path'] == manifest['checkpoint']
            candidate = dict(name='office_rl_'+job['name'], category=job['family'], seed=job['seed'],
                variant='office_from_scratch_latest_completed_boundary', config={},
                cumulative_training_steps=manifest['cumulative_physics_steps'],
                training_stop_reason=training['stop_reason'],
                adapted_rl=dict(checkpoint=manifest['checkpoint'], manifest=str(manifest_path),
                    manifest_sha256=sha(manifest_path), parameter_source=str(rl/'parameter_source'),
                    controller=job['controller']))
            reinforcement.append(candidate)
            evidence.extend(dict(path=str(p), sha256=sha(p)) for p in (manifest_path, training_path))
    assert seen == set(jobs), 'Missing RL models cannot disappear from the matrix'
    evidence.append(dict(path=str(spec_path), sha256=sha(spec_path)))
    candidates, groups = combine(learning['candidates'], choice['candidates'], nominal['candidates'][0],
                                reinforcement, seeds, families)
    verify_candidates(candidates)
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
        protocol_sha256=digest, candidates=candidates, paired_seed_groups=groups,
        selection_uses_only_train_validation_development=True, all_registered_finalists_included=True,
        incomplete_or_failed_training_disclosed=True, development_evidence=evidence,
        completion_receipts=completion, sealed_contents_read=False,
        selection='Shared learned variants and classical configurations from public development; RL latest completed training boundary without outcome ranking; untuned nominal WBC.',
        caveats=['Episode-boundary RL steps can differ below the shared cap; actual steps and stop reasons remain per candidate.',
                 'Any incomplete predecessor or absent model blocks freezing; this tool does not silently drop or invent a replacement.',
                 'Selected candidates may fail development; all remain in the final matrix.',
                 'This file does not freeze runtime or open heldout conditions.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    if skip:
        # The collector's truthful skipped status is immutable. An explicit
        # closure attestation satisfies the final lock's completed-work contract
        # without pretending that forty new trajectories were collected.
        attestation = output.with_suffix('.teacher_closure.json')
        with attestation.open('x') as stream:
            json.dump(dict(status='complete', work='No-op closure of identical-teacher recollection',
                new_physics_episodes=0, original_execution=str(teacher_path), original_status=teacher['status'],
                original_execution_sha256=sha(teacher_path), choice_sha256=sha(choice_path),
                config_verified_identical=True), stream, indent=2); stream.write('\n')
        completion.append(dict(path=str(attestation), sha256=sha(attestation)))
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(dict(models=len(candidates), selection_sha256=sha(output), sealed_contents_read=False)))


if __name__ == '__main__':
    main()
