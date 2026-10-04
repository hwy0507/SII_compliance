import unittest
import json
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch
import research72_finalize_selection_20261003 as finalizer
from research72_finalize_selection_20261003 import combine, LEARNED, CLASSICAL


class FinalSelectionTests(unittest.TestCase):
    def setUp(self):
        self.seeds = [1, 2, 3]
        self.families = ['parameter_admittance', 'parameter_impedance', 'parameter_vmc', 'direct_metric', 'direct_office_task']
        def models(families):
            return [dict(name=f'{f}_{s}', category=f, seed=s, variant='fixed', development_success=0)
                    for f in sorted(families) for s in self.seeds]
        self.learned = models(LEARNED); self.rl = models(self.families)
        self.classical = [dict(name=f, category=f, development_success=0) for f in sorted(CLASSICAL)]
        self.nominal = dict(name='nominal', category='nominal_zero', nominal=True)

    def call(self):
        return combine(self.learned, self.classical, self.nominal, self.rl, self.seeds, self.families)

    def test_all_failed_models_still_proceed(self):
        candidates, groups = self.call()
        self.assertEqual(len(candidates), 38)
        self.assertEqual(len(groups), 11)

    def test_missing_rl_seed_blocks_freeze(self):
        self.rl.pop()
        with self.assertRaises(AssertionError):
            self.call()

    def test_mixed_variants_across_seed_blocks_freeze(self):
        self.learned[0]['variant'] = 'cherry_picked'
        with self.assertRaises(AssertionError):
            self.call()

    def test_missing_classical_method_blocks_freeze(self):
        self.classical.pop()
        with self.assertRaises(AssertionError):
            self.call()

    def test_full_ledger_closes_identical_teacher_without_mutating_collector(self):
        self.full_ledger()

    def test_common_boundary_uses_all_fifteen_earlier_weights_not_latest(self):
        self.full_ledger(boundary=True)

    def test_missing_common_boundary_does_not_fall_back_to_latest(self):
        self.full_ledger(boundary=True, mutation='missing_boundary')

    def test_changed_governor_closure_blocks_all_finalists(self):
        self.full_ledger(boundary=True, mutation='changed_closure')

    def full_ledger(self, boundary=False, mutation=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def write(path, data):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data))
            write(root/'teacher.json', {})
            protocol = dict(teacher_config_sha256=finalizer.sha(root/'teacher.json'),
                budget_caps=dict(training_seeds=self.seeds, rl_families=self.families,
                                 rl_adaptation_steps_per_family_seed=80000))
            write(root/'PROTOCOL.json', protocol); digest = finalizer.sha(root/'PROTOCOL.json')
            for name in ('followup_v1', 'additional_development_v1', 'context_gate_development_v1',
                         'rl_office_adaptation_v1', 'final_rehearsal_v1', 'controller_confirmation_v1'):
                write(root/name/'execution.json', dict(status='complete'))
            write(root/'controller_confirmation_v1/SUMMARY.json', {})
            write(root/'controller_confirmation_v1/SPECIFICATION.json', {})
            teacher_candidate = next(c for c in self.classical if c['category']=='enhanced_teacher')
            teacher_candidate['config'] = {}
            choice = dict(protocol_sha256=digest, candidates=self.classical,
                outcome='one per family selected on all eight development identities',
                screen_spec_sha256=finalizer.sha(root/'controller_confirmation_v1/SPECIFICATION.json'),
                screen_summary_sha256=finalizer.sha(root/'controller_confirmation_v1/SUMMARY.json'))
            write(root/'followup_v1/CONTROLLER_CHOICE.json', choice)
            teacher_path = root/'teacher_refinement_v1/execution.json'
            write(teacher_path, dict(status='complete_skipped_identical_teacher', new_physics_episodes=0,
                selected_teacher=teacher_candidate, choice_sha256=finalizer.sha(root/'followup_v1/CONTROLLER_CHOICE.json')))
            original_teacher_digest = finalizer.sha(teacher_path)
            if boundary:
                write(teacher_path, dict(status='complete',
                    choice_sha256=finalizer.sha(root/'followup_v1/CONTROLLER_CHOICE.json')))
                original_teacher_digest = finalizer.sha(teacher_path)
            write(root/'additional_development_v1/NOMINAL_SPECIFICATION.json',
                  dict(protocol_sha256=digest, candidates=[self.nominal]))
            write(root/'LEARNING.json', dict(protocol_sha256=digest, candidates=self.learned,
                                            development_evidence=[], completion_receipts=[]))
            jobs = [dict(name=r['name'], family=r['category'], seed=r['seed'], controller=None) for r in self.rl]
            rl = root/'rl_office_adaptation_v1'
            write(rl/'SPECIFICATION.json', dict(protocol_sha256=digest, jobs=jobs))
            for index in range(3):
                queue = rl/f'queue_{index}'; rows = []
                for job in jobs[index::3]:
                    parent = queue/job['name']; checkpoint = parent/'initial/checkpoint'
                    execution = parent/'initial/execution.json'
                    write(execution, dict(status='complete', stop_reason='requested',
                        checkpoint_rows=[dict(path=str(checkpoint))]))
                    manifest = parent/'initial_CHECKPOINT.json'
                    write(manifest, dict(checkpoint=str(checkpoint), family=job['family'], seed=job['seed'],
                                         controller=job['controller'], cumulative_physics_steps=5500))
                    rows.append(dict(name=job['name'], latest_manifest=str(manifest),
                        latest_manifest_sha256=finalizer.sha(manifest), segments=[dict(stage='initial',
                            returncode=0, cumulative_steps=5500, execution_sha256=finalizer.sha(execution))]))
                write(queue/'execution.json', dict(status='complete', rows=rows))
            if boundary:
                # Exercise the real boundary/closure readers used after the
                # live queues finish. No model lock or sealed inputs exist.
                from research72_rl_final_boundary_20261004 import AMENDMENT, STAGE
                closures = []; queues = []
                for index in range(3):
                    queue = rl/f'queue_{index}'; queue_path = queue/'execution.json'
                    state = json.loads(queue_path.read_text())
                    for row in state['rows']:
                        parent = queue/row['name']
                        original = json.loads(Path(row['latest_manifest']).read_text())
                        selected_steps = 49336 if original['seed']==3 else 49500
                        actual_steps = selected_steps+1375
                        for stage, steps in ((STAGE, selected_steps), ('cumulative_0071500', actual_steps)):
                            checkpoint = parent/stage/'checkpoint'
                            training = parent/stage/'PROTOCOL.json'
                            write(training, dict(segment_step_limit=49500 if stage==STAGE else 71500,
                                maximum_new_physics_steps=80000))
                            execution = parent/stage/'execution.json'
                            write(execution, dict(status='complete', steps=steps,
                                stop_reason='remaining_budget_less_than_one_full_episode' if stage==STAGE else 'requested_stop',
                                checkpoint_rows=[dict(path=str(checkpoint))]))
                            manifest = parent/(stage+'_CHECKPOINT.json')
                            write(manifest, dict(original, checkpoint=str(checkpoint),
                                cumulative_physics_steps=steps, training_protocol=str(training),
                                training_protocol_sha256=finalizer.sha(training)))
                            row['segments'].append(dict(stage=stage, returncode=0, cumulative_steps=steps,
                                execution_sha256=finalizer.sha(execution)))
                            row.update(latest_manifest=str(manifest), latest_manifest_sha256=finalizer.sha(manifest))
                        chosen = finalizer.selected_boundary(queue, row)
                        closures.append(dict(chosen, actual_total_training_steps=actual_steps,
                                             unused_compatibility_steps=1375))
                    write(queue_path, state)
                    queues.append(dict(path=str(queue_path), sha256=finalizer.sha(queue_path)))
                governor = root/'governor'; governor.mkdir()
                refs = {}
                for key in ('registration', 'forecast', 'governor_source'):
                    path = governor/(key+'.json'); write(path, dict(synthetic_test_only=True))
                    refs[key] = str(path); refs[key+'_sha256'] = finalizer.sha(path)
                write(root/AMENDMENT, dict(protocol_sha256=digest,
                    scope='outcome_independent_common_rl_final_boundary', active_campaign=rl.name,
                    selected_stage=STAGE, selected_step_limit=49500, all_fifteen_models_required=True,
                    selection_uses_rewards_or_task_results=False, sealed_contents_read=False,
                    specification_sha256=finalizer.sha(rl/'SPECIFICATION.json'), output=str(governor), **refs))
                closed = dict(status='complete', amendment_sha256=finalizer.sha(root/AMENDMENT),
                    source_sha256=refs['governor_source_sha256'], models=closures, queue_executions=queues)
                write(governor/'CLOSURE.json', closed)
                write(governor/'execution.json', dict(status='complete', dry_run=False,
                    amendment_sha256=finalizer.sha(root/AMENDMENT), source_sha256=refs['governor_source_sha256'],
                    closure_sha256=finalizer.sha(governor/'CLOSURE.json')))
                if mutation=='missing_boundary':
                    # Keep queue and closure hashes internally consistent so
                    # rejection must come from the absent required stage.
                    path = Path(queues[0]['path']); state = json.loads(path.read_text())
                    state['rows'][0]['segments'] = [s for s in state['rows'][0]['segments'] if s['stage']!=STAGE]
                    write(path, state); queues[0]['sha256'] = finalizer.sha(path)
                    write(governor/'CLOSURE.json', closed)
                    execution = json.loads((governor/'execution.json').read_text())
                    execution['closure_sha256'] = finalizer.sha(governor/'CLOSURE.json')
                    write(governor/'execution.json', execution)
                if mutation=='changed_closure':
                    closed['models'][0]['selected_steps'] = 50875
                    write(governor/'CLOSURE.json', closed)
            output = root/'FINALISTS.json'
            # Checkpoint bytes are tested by the separate final-lock suite.
            # This test exercises real file/receipt/manifest joining only.
            with patch.object(finalizer, 'verify_candidates') as verify, patch.object(sys, 'argv',
                ['select', '--root', str(root), '--learning-selection', str(root/'LEARNING.json'), '--output', str(output)]):
                if mutation:
                    with self.assertRaises(AssertionError):
                        finalizer.main()
                    self.assertFalse(output.exists())
                    verify.assert_not_called()
                    self.assertFalse((root/'sealed').exists())
                    return
                finalizer.main()
            result = json.loads(output.read_text())
            self.assertEqual(len(result['candidates']), 38)
            self.assertEqual(verify.call_count, 1)
            self.assertEqual(finalizer.sha(teacher_path), original_teacher_digest)
            if boundary:
                policies = [c for c in result['candidates'] if c.get('adapted_rl')]
                self.assertEqual(len(policies), 15)
                for policy in policies:
                    selected_steps = 49336 if policy['seed']==3 else 49500
                    self.assertEqual(policy['cumulative_training_steps'], selected_steps)
                    self.assertEqual(policy['total_collected_training_steps'], selected_steps+1375)
                    self.assertEqual(policy['unused_post_selection_training_steps'], 1375)
                    self.assertIn('/'+STAGE+'/', policy['adapted_rl']['checkpoint'])
                    self.assertEqual(policy['variant'], 'office_from_scratch_common_49500_boundary')
                self.assertFalse(output.with_suffix('.teacher_closure.json').exists())
            else:
                closure = json.loads(output.with_suffix('.teacher_closure.json').read_text())
                self.assertEqual(closure['new_physics_episodes'], 0)
                self.assertEqual(closure['original_status'], 'complete_skipped_identical_teacher')
                self.assertTrue(closure['config_verified_identical'])
            self.assertFalse((root/'sealed').exists())


if __name__ == '__main__':
    unittest.main()
