"""Synthetic complete selection ledger, no actual model fitting or simulation.

Exercise JSON-string receipt paths and all72 candidates through the real
selector, including mandatory extra-cohort completeness and tamper rejection.
These files are test fixtures, never evidence for any real candidate.
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import research72_select_learning_20261003 as selector


class RefitSelectionTests(unittest.TestCase):
    def fixture(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        def write(path, data):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))

        conditions = [f'dev{i}' for i in range(8)]; seeds = [1, 2, 3]
        write(root/'CONDITIONS.json', dict(conditions=[dict(id=c, role='development') for c in conditions]))
        write(root/'PROTOCOL.json', dict(condition_file_sha256=selector.sha(root/'CONDITIONS.json'),
            budget_caps=dict(training_seeds=seeds)))
        digest = selector.sha(root/'PROTOCOL.json')
        phases = {}

        def phase(label, path, variants, data):
            models = []; rows = []; audits = []
            for family, variant in variants:
                for seed in seeds:
                    name = f'{label}_{family}_{variant}_{seed}'
                    cp = root/'models'/name/'checkpoint.npz'
                    cp.parent.mkdir(parents=True); cp.write_bytes(b'SYNTHETIC HASH FIXTURE, NOT WEIGHTS')
                    write(cp.parent/'TRAINING_COMPLETE.json', dict(training_data_sha256=data))
                    candidate = dict(name=name, category=family, variant=label+'_'+variant, seed=seed,
                        checkpoint=str(cp), checkpoint_sha256=selector.sha(cp))
                    models.append(candidate)
                    for condition in conditions:
                        run = path/'queue_0'/(name+'__'+condition)
                        write(run/'AUDIT.json', dict(synthetic=True))
                        audit_sha = selector.sha(run/'AUDIT.json')
                        rows.append(dict(candidate=name, run=str(run), condition_id=condition,
                            audit_sha256=audit_sha))
                        audits.append(dict(run=str(run), audit_sha256=audit_sha,
                            checkpoint_sha256=candidate['checkpoint_sha256'],
                            frozen_source_hashes_verified=True, actuator_amplitude_and_command_slew_valid=True,
                            actor_replay_performed=True, independent_contact_sidecar_verified=True,
                            strict_success=False, task_success=False, full_horizon=True,
                            penetration_mm=.3, edge_penetration_mm=.1, rmse_mm=40., peak_torque_nm=50.))
            write(path/'SPECIFICATION.json', dict(protocol_sha256=digest, conditions=conditions,
                candidates=models, data_sha256=data))
            write(path/'execution.json', dict(status='complete'))
            write(path/'SUMMARY.json', dict(completed=len(rows), expected=len(rows), rows=rows))
            proof = path/'queue_0_analysis/INDEPENDENT_AUDIT.json'
            write(proof, dict(pending=[], rows=audits))
            write(proof.parent/'execution.json', dict(status='complete',
                outputs={'INDEPENDENT_AUDIT.json': selector.sha(proof)}))
            phases[label] = path
            return models

        phase('original', root/'learning_development_v1',
            [(f, v) for f in ('esn', 'memoryless') for v in ('point', 'temporal')], 'old-data')
        rates = phase('refinement', root/'additional_development_v1/neural_lr_development',
            [(f, v) for f in ('ordinary_mlp', 'ordinary_rnn', 'matched_mlp') for v in ('point', 'temporal')]
            + [('matched_rnn', 'point')], 'old-data')
        phase('context', root/'context_gate_development_v1/development',
            [(f, v) for f in ('esn', 'matched_mlp', 'matched_rnn') for v in ('point', 'temporal')]
            + [('memoryless', 'point')], 'old-data')
        write(root/'NEURAL_LR_SELECTION.json', dict(protocol_sha256=digest,
            data_sha256='old-data', selected_candidates=rates))
        write(root/'AMENDMENT_01_CONTEXT_MEMORY.json', dict(protocol_sha256=digest,
            learning_rate_selection_sha256=selector.sha(root/'NEURAL_LR_SELECTION.json')))
        amendment = root/'AMENDMENT_02_CONTEXT_READOUT_REFIT.json'
        write(amendment, dict(protocol_sha256=digest, new_learning_cap_per_family_seed=60,
            scope='fixed_state_context_readout_selected_teacher_refit'))
        path = root/'context_readout_refit_development_v1'
        phase('refit', path, [(f, 'point') for f in
            ('esn', 'memoryless', 'ordinary_mlp', 'ordinary_rnn', 'matched_mlp', 'matched_rnn')], 'new-data')
        teacher = root/'TEACHER_RECEIPT.json'; write(teacher, dict(synthetic=True, status='complete'))
        spec = json.loads((path/'SPECIFICATION.json').read_text())
        spec.update(amendment_sha256=selector.sha(amendment), ordinary_refit_required=True,
            refit_data_receipt=dict(selected_teacher_verified=True, training_data_sha256='new-data',
                evidence=[dict(path=str(teacher), sha256=selector.sha(teacher))]))
        write(path/'SPECIFICATION.json', spec)
        return root, phases, teacher

    def invoke(self, root):
        output = root/'SELECTED.json'
        with patch('sys.argv', ['select', '--root', str(root), '--output', str(output)]):
            selector.main()
        return json.loads(output.read_text())

    def test_all_72_candidates_and_string_receipts_without_success_filter(self):
        root, _, teacher = self.fixture(); result = self.invoke(root)
        self.assertEqual(len(result['candidates']), 18)
        self.assertEqual(sum(len(r['candidates']) for variants in result['ranked'].values() for r in variants), 72)
        self.assertIn(dict(path=str(teacher), sha256=selector.sha(teacher)), result['development_evidence'])
        self.assertTrue(all(r['strict']==r['task']==0 for variants in result['ranked'].values() for r in variants))
        self.assertFalse((root/'FINAL_UNSEAL_RECEIPT.json').exists())

    def test_changed_teacher_receipt_blocks_selection(self):
        root, _, teacher = self.fixture(); teacher.write_text('{"tampered":true}')
        with self.assertRaises(AssertionError): self.invoke(root)
        self.assertFalse((root/'SELECTED.json').exists())

    def test_missing_extra_episode_blocks_selection(self):
        root, phases, _ = self.fixture()
        path = phases['refit']/'SUMMARY.json'
        summary = json.loads(path.read_text()); summary['completed'] -= 1
        summary['rows'].pop(); path.write_text(json.dumps(summary))
        with self.assertRaises(AssertionError): self.invoke(root)
        self.assertFalse((root/'SELECTED.json').exists())


if __name__ == '__main__': unittest.main()
