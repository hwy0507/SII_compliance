"""Protect resource handoffs and split-run evidence without starting learners."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from prioritize_published_fresh_sampling_20261025 import jobs_ready, remaining_cycles, validate_allocations, validate_boundary
from audit_published_restart_stages_20261025 import locate_cycle


class FreshPriorityTests(unittest.TestCase):
    def setUp(self):
        methods = ('direct', 'impedance', 'admittance', 'vmc')
        cpus = [list(range(13)), [14]+list(range(15,26))+[52], list(range(26,39)), list(range(39,52))]
        self.plan = dict(total_cycles=6, reserved_cpus=[13,53,54], coordinator_cpu=54,
            allocations={m: dict(cpus=c, workers=12, gpu=i) for i,(m,c) in enumerate(zip(methods,cpus))})
        for role in ('fresh','sac'):
            self.plan[role] = dict(expected_allocations={m: dict(cpus=c[:3]) for m,c in zip(methods,cpus)})

    def test_nonoverlap_and_budget(self):
        validate_allocations(self.plan, set(range(55)))
        state = dict(boundary='complete_condition_cycle', cycle=1, steps=82500,
                     cycles=[dict(cycle=0,steps=41250), dict(cycle=1,steps=82500)])
        self.assertEqual(remaining_cycles(state,6),4)
        state['cycle']=5
        state['cycles']=[dict(cycle=i,steps=(i+1)*41250) for i in range(6)]
        state['steps']=247500
        self.assertEqual(remaining_cycles(state,6),0)

    def test_core_overlap_or_unavailable_rejected(self):
        for cpu in (13,14,55):
            plan=copy.deepcopy(self.plan); plan['allocations']['direct']['cpus'][1]=cpu
            with self.subTest(cpu=cpu), self.assertRaises(ValueError):
                validate_allocations(plan,set(range(55)))

    def test_draining_sibling_overlap_rejected(self):
        self.plan['sac']['expected_allocations']['vmc']['cpus']=[12]
        with self.assertRaisesRegex(ValueError,'draining sibling'):
            validate_allocations(self.plan,set(range(55)))

    def test_partial_or_gapped_history_rejected(self):
        for boundary, cycles in [('partial', [dict(cycle=0,steps=10)]),
                                  ('complete_condition_cycle',[dict(cycle=1,steps=10)])]:
            with self.subTest(boundary=boundary), self.assertRaises(ValueError):
                remaining_cycles(dict(boundary=boundary,cycle=1,steps=10,cycles=cycles),6)

    def test_complete_condition_evidence_includes_failures(self):
        state=dict(boundary='complete_condition_cycle',steps=20,cycle=0,controller='direct',
            protocol_sha256='hash',seed=17,learner=dict(algorithm='cheq'),cycles=[dict(cycle=0,steps=20)])
        finished=dict(steps=20,status='stopped_at_complete_cycle')
        execution=dict(seed=17,algorithm='cheq')
        rows=[dict(cycle=0,condition=c,total_steps=t,strict_success=False) for c,t in [('a',10),('b',20)]]
        validate_boundary(state,finished,execution,'direct','hash',['a','b'],rows)
        with self.assertRaisesRegex(ValueError,'condition set'):
            validate_boundary(state,finished,execution,'direct','hash',['a','b'],[rows[1]])
        with self.assertRaisesRegex(ValueError,'registered complete boundary'):
            validate_boundary(state,finished,execution,'direct','other',['a','b'],rows)

    def test_resolve_real_owner_and_reject_conflicting_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); old=root/'old'; new=root/'new'
            stage=dict(run=str(old),additional_runs=[str(new)],archives=['archive'],cycle=1)
            self.assertIsNone(locate_cycle(stage,'direct'))
            path=new/'archive/direct/cycle_00001.pt'; path.parent.mkdir(parents=True); path.write_bytes(b'new')
            self.assertEqual(locate_cycle(stage,'direct'),(new,path))
            other=old/'archive/direct/cycle_00001.pt'; other.parent.mkdir(parents=True); other.write_bytes(b'conflict')
            with self.assertRaisesRegex(ValueError,'Different checkpoints'):
                locate_cycle(stage,'direct')

    def test_waits_for_live_coordinator_and_rejects_unreceipted_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            spec=dict(run=folder,coordinator_pid=123,coordinator_start_ticks='original',
                      finished_receipt='FINISHED.json')
            with patch('prioritize_published_fresh_sampling_20261025.identity',return_value='original'):
                self.assertIsNone(jobs_ready(spec))
            with patch('prioritize_published_fresh_sampling_20261025.identity',return_value=None):
                with self.assertRaisesRegex(RuntimeError,'without handoff'):
                    jobs_ready(spec)
            with patch('prioritize_published_fresh_sampling_20261025.identity',return_value='reused'):
                with self.assertRaisesRegex(ValueError,'PID reused'):
                    jobs_ready(spec)


if __name__ == '__main__':
    unittest.main()
