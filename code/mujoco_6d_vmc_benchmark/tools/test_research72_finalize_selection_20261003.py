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
            output = root/'FINALISTS.json'
            # Checkpoint bytes are tested by the separate final-lock suite.
            # This test exercises real file/receipt/manifest joining only.
            with patch.object(finalizer, 'verify_candidates') as verify, patch.object(sys, 'argv',
                ['select', '--root', str(root), '--learning-selection', str(root/'LEARNING.json'), '--output', str(output)]):
                finalizer.main()
            result = json.loads(output.read_text())
            self.assertEqual(len(result['candidates']), 38)
            self.assertEqual(verify.call_count, 1)
            self.assertEqual(finalizer.sha(teacher_path), original_teacher_digest)
            closure = json.loads(output.with_suffix('.teacher_closure.json').read_text())
            self.assertEqual(closure['new_physics_episodes'], 0)
            self.assertEqual(closure['original_status'], 'complete_skipped_identical_teacher')
            self.assertTrue(closure['config_verified_identical'])
            self.assertFalse((root/'sealed').exists())


if __name__ == '__main__':
    unittest.main()
