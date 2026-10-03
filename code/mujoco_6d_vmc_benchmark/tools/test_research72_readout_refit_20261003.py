"""Synthetic registration/data-lineage checks; no fitting or physical episodes."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research72_train_models_20261003 import context_readout_refit_jobs, main as register_fit
from research72_refit_data_receipt_20261003 import verify, sha


class RefitTests(unittest.TestCase):
    def test_local_register_only_preserves_server_reuse_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def write(name,obj):
                path=root/name;path.write_text(json.dumps(obj));return path
            data=root/'data.npz';data.write_bytes(b'NO FIT, HASH ONLY')
            protocol=write('protocol.json',dict(budget_caps=dict(training_seeds=[1,2,3])))
            metadata=write('metadata.json',dict(all_real_execution=True,protocol_sha256=sha(protocol),
                training_data_sha256=sha(data),lineage=[]))
            reused=[dict(name=f'{family}{seed}',category=family,seed=seed,variant='point',
                         checkpoint=f'/server-only/{family}{seed}/checkpoint.npz',checkpoint_sha256='synthetic')
                    for family in ('ordinary_mlp','ordinary_rnn') for seed in (1,2,3)]
            rates=write('rates.json',dict(protocol_sha256=sha(protocol),data_sha256=sha(data),
                decisions=[dict(family=f,variant='point',selected_learning_rate=1e-5)
                    for f in ('ordinary_mlp','ordinary_rnn','matched_mlp','matched_rnn')],selected_candidates=reused))
            amendment=write('amendment.json',dict(protocol_sha256=sha(protocol),
                scope='fixed_state_context_readout_selected_teacher_refit',new_learning_cap_per_family_seed=60,
                sealed_contents_read=False,learning_rate_selection_sha256=sha(rates)))
            receipt=write('receipt.json',dict(protocol_sha256=sha(protocol),status='complete',
                selected_teacher_verified=True,training_data_sha256=sha(data),dataset_metadata_sha256=sha(metadata)))
            argv=['register','--data',str(data),'--metadata',str(metadata),'--protocol',str(protocol),
                '--output',str(root/'out'),'--context-readout-refit','--amendment',str(amendment),
                '--learning-rate-selection',str(rates),'--refit-data-receipt',str(receipt),'--register-only']
            with patch('sys.argv',argv):register_fit()
            spec=json.loads((root/'out/SPECIFICATION.json').read_text())
            self.assertEqual(len(spec['jobs']),12)
            self.assertEqual(spec['reused_ordinary_candidates'],reused)
            self.assertFalse((root/'out/execution.json').exists())

    def test_all_families_seeds_parents_and_fixed_rates(self):
        rates=dict(decisions=[dict(family=f,variant='point',selected_learning_rate=1e-5)
            for f in ('ordinary_mlp','ordinary_rnn','matched_mlp','matched_rnn')])
        jobs=context_readout_refit_jobs([1,2,3],rates)
        self.assertEqual(len(jobs),18)
        seen=set()
        for job in jobs:
            if 'parent' in job:self.assertIn(job['parent'],seen)
            seen.add(job['name'])
            self.assertNotIn('--leak-gate',job['extra'])
            if job['family'] in ('esn','memoryless'):
                self.assertIn('--state-context-readout',job['extra'])
            else:
                self.assertEqual(job['extra'][job['extra'].index('--learning-rate')+1],'1e-05')
        for family in {j['family'] for j in jobs}:
            self.assertEqual({j['seed'] for j in jobs if j['family']==family},{1,2,3})
        unchanged=context_readout_refit_jobs([1,2,3],rates,include_ordinary=False)
        self.assertEqual(len(unchanged),12)
        self.assertFalse(any(j['family'].startswith('ordinary_') for j in unchanged))

    def fixture(self, reused):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        def write(path,obj):
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj))
        conditions=[dict(id=f'c{i}',role='train' if i<4 else 'imitation_validation' if i<6 else 'development') for i in range(48)]
        if not reused:
            conditions=[dict(id=f'c{i}',role='train' if i<32 else 'imitation_validation') for i in range(40)]
        write(root/'CONDITIONS.json',dict(conditions=conditions))
        write(root/'PROTOCOL.json',dict(condition_file_sha256=sha(root/'CONDITIONS.json')))
        digest=sha(root/'PROTOCOL.json');selected=dict(category='enhanced_teacher',config={'x':1})
        write(root/'followup_v1/execution.json',dict(status='complete'))
        choice=root/'followup_v1/CONTROLLER_CHOICE.json'
        write(choice,dict(protocol_sha256=digest,candidates=[selected]))
        bank=root/('teacher_bank' if reused else 'teacher_refinement_v1/collection')
        data=root/('prepare_learning_v2/demonstrations' if reused else 'teacher_refinement_v1/demonstrations')
        teacher=root/'teacher.json' if reused else bank/'teacher.json';write(teacher,selected['config'])
        write(bank/'execution.json',dict(status='complete'))
        write(data/'execution.json',dict(status='complete'))
        (data/'training_data.npz').write_bytes(b'SYNTHETIC HASH FIXTURE ONLY')
        ledger=[dict(condition_id=c['id'],included=c['role']!='development',qualified=c['role']!='development') for c in conditions]
        write(data/'QUALIFICATION_LEDGER.json',ledger)
        lineage=[dict(condition_id=c['id'],data_role=c['role'],actual_execution_labels=True,
            counterfactual_relabel=False,synthetic=False,task_success=True,strict_success=True)
            for c in conditions if c['role']!='development']
        metadata=dict(protocol_sha256=digest,all_real_execution=True,teacher_config_sha256=sha(teacher),
            training_data_sha256=sha(data/'training_data.npz'),actual_filter_replay_verified=True,
            actual_requested_labels_preserved=True,qualification_ledger_sha256=sha(data/'QUALIFICATION_LEDGER.json'),
            lineage=lineage,training_identities=sum(c['data_role']=='train' for c in lineage),
            validation_identities=sum(c['data_role']=='imitation_validation' for c in lineage))
        write(data/'DATA_COMPLETE.json',metadata)
        write(root/'teacher_refinement_v1/execution.json',dict(
            status='complete_skipped_identical_teacher' if reused else 'complete',
            choice_sha256=sha(choice),selected_teacher=selected,new_physics_episodes=0 if reused else 40,
            dataset_metadata_sha256=sha(data/'DATA_COMPLETE.json')))
        if not reused:write(bank/'TEACHER_SELECTION.json',dict(candidate=selected,choice_sha256=sha(choice)))
        return root,data

    def test_same_teacher_reuses_verified_data_without_fake_collection(self):
        root,_=self.fixture(True);receipt=verify(root)
        self.assertTrue(receipt['reused_original_teacher'])
        self.assertEqual(receipt['qualifying_train_identities'],4)
        self.assertFalse(receipt['sealed_contents_read'])

    def test_changed_teacher_requires_actual_completed_collection(self):
        root,_=self.fixture(False);receipt=verify(root)
        self.assertFalse(receipt['reused_original_teacher'])
        state=root/'teacher_refinement_v1/execution.json';record=json.loads(state.read_text())
        record['status']='collecting';state.write_text(json.dumps(record))
        with self.assertRaises(AssertionError):verify(root)

    def test_dataset_mutation_rejected(self):
        root,data=self.fixture(True);(data/'training_data.npz').write_bytes(b'TAMPERED')
        with self.assertRaises(AssertionError):verify(root)

    def test_open_final_receipt_blocks_refit(self):
        root,_=self.fixture(True);(root/'FINAL_UNSEAL_RECEIPT.json').write_text('{}')
        with self.assertRaises(AssertionError):verify(root)


if __name__=='__main__':unittest.main()
