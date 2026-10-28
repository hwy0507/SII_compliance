import json
from pathlib import Path
import tempfile
import unittest
from research72_final_transition_20261004 import (
    PREDECESSORS,predecessors,transition,development_names,sha)


class TransitionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'transition';self.out.mkdir()
        self.final=self.root/'final';self.calls=[]

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

    def ready(self):
        for name in PREDECESSORS:self.write(self.root/name/'execution.json',dict(status='complete'))

    def execute(self,label,command,models=38,episodes=912):
        self.calls.append(label)
        if label=='learning_selection':self.write(self.out/'LEARNING_SELECTION.json',{})
        if label=='all_model_selection':self.write(self.out/'FINALISTS.json',{})
        if label=='model_lock':
            self.assertTrue((self.out/'FINALISTS.json').exists())
            self.assertFalse(self.final.exists())
            self.write(self.out/'MODEL_LOCK.json',dict(training_closed=True,
                all_registered_finalists_included=True,candidates=[{}]*models))
        if label=='final_evaluation':
            self.assertEqual(command[-2:],['--lock-sha256',sha(self.out/'MODEL_LOCK.json')])
            self.write(self.final/'execution.json',dict(status='complete',expected=912))
            self.write(self.final/'SUMMARY.json',dict(expected=912,completed=episodes))

    def run_transition(self,execute=None):
        return transition(self.root/'runtime',self.root,self.out,self.final,'python',execute or self.execute)

    def test_real_guard_names_are_loaded_without_physics_import(self):
        names=development_names(Path(__file__).resolve().parents[1])
        self.assertIn('research72_train_rl_20261003.py',names)
        self.assertIn('research72_batch_20261003.py',names)
        self.assertNotIn('research72_final_transition_20261004.py',names)

    def test_watch_is_pending_not_complete(self):
        self.ready();self.write(self.root/'rl_final_boundary_v1/execution.json',dict(status='watching'))
        rows=predecessors(self.root)
        self.assertFalse(all(r['complete'] for r in rows))
        self.assertEqual(sum(r['complete'] for r in rows),len(PREDECESSORS)-1)

    def test_terminal_failure_and_missing_predecessor_block(self):
        self.ready();path=self.root/'context_readout_refit_development_v1/execution.json'
        for status in ('failed_preserved','deadline_no_new_dispatch'):
            self.write(path,dict(status=status))
            with self.assertRaises(AssertionError):predecessors(self.root)
        path.unlink()
        with self.assertRaises(AssertionError):predecessors(self.root)

    def test_all_steps_ordered_and_exact_lock_hash_passed(self):
        result=self.run_transition()
        self.assertEqual(self.calls,['learning_selection','all_model_selection','model_lock','final_evaluation'])
        self.assertEqual(result['model_lock_sha256'],sha(self.out/'MODEL_LOCK.json'))
        self.assertFalse((self.root/'sealed').exists())

    def test_selection_failure_never_locks_or_runs_final(self):
        def fail(label,command):
            self.calls.append(label);raise RuntimeError('missing public episode')
        with self.assertRaises(RuntimeError):self.run_transition(fail)
        self.assertEqual(self.calls,['learning_selection'])
        self.assertFalse((self.out/'MODEL_LOCK.json').exists())
        self.assertFalse(self.final.exists())

    def test_absent_model_blocks_final(self):
        with self.assertRaises(AssertionError):
            self.run_transition(lambda label,command:self.execute(label,command,models=37))
        self.assertEqual(self.calls,['learning_selection','all_model_selection','model_lock'])
        self.assertFalse(self.final.exists())

    def test_missing_final_episode_not_complete(self):
        with self.assertRaises(AssertionError):
            self.run_transition(lambda label,command:self.execute(label,command,episodes=911))
        self.assertTrue((self.final/'SUMMARY.json').exists())

    def test_existing_final_evidence_never_restarted(self):
        self.write(self.root/'FINAL_UNSEAL_RECEIPT.json',{})
        with self.assertRaises(AssertionError):self.run_transition()
        self.assertEqual(self.calls,[])


if __name__=='__main__':unittest.main()
