"""Migration guards tested without starting physics, learners or processes."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from continue_published_performance_20261025 import validate_boundary, validate_resources


class SamplerReallocationTests(unittest.TestCase):
    def setUp(self):
        methods = ['direct', 'impedance', 'admittance', 'vmc']
        self.jobs = [dict(controller=m, pid=100+i, gpu=i, cpus=[i*13+10, i*13+11, i*13+12])
                     for i, m in enumerate(methods)]
        self.identities = {m: str(400+i) for i, m in enumerate(methods)}
        self.executions = {j['controller']: dict(algorithm='sac', device='cuda:'+str(j['gpu']),
                                               cpus=j['cpus'], seed=17) for j in self.jobs}
        self.resource = dict(reserved_cpus=[0, 13, 14, 26, 39, 54],
            allocations={m: dict(cpus=[i*13+10]+list(range(i*13+1, i*13+10)),
                                  workers=9, gpu=i) for i, m in enumerate(methods)},
            parent_identities={j['controller']: dict(pid=j['pid'],
                start_ticks=self.identities[j['controller']]) for j in self.jobs})
        self.resource['allocations']['impedance']['cpus'] = [23]+list(range(15, 23))+[24]

    def validate(self):
        return validate_resources(self.resource, self.jobs, self.executions,
                                  self.identities, set(range(55)), 54)

    def test_valid_resource_only_move(self):
        self.assertEqual(self.validate()['direct']['workers'], 9)

    def test_reserved_or_other_new_allocation_rejected(self):
        for cpu in (0, 15):
            with self.subTest(cpu=cpu):
                original = copy.deepcopy(self.resource)
                self.resource['allocations']['direct']['cpus'][1] = cpu
                with self.assertRaisesRegex(ValueError, 'overlap'):
                    self.validate()
                self.resource = original

    def test_still_draining_sibling_rejected(self):
        self.resource['allocations']['direct']['cpus'][1] = 25
        with self.assertRaisesRegex(ValueError, 'draining sibling'):
            self.validate()

    def test_stale_pid_unknown_controller_and_gpu_rejected(self):
        original = copy.deepcopy(self.resource)
        self.resource['parent_identities']['direct']['start_ticks'] = 'old'
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.validate()
        self.resource = copy.deepcopy(original)
        self.resource['allocations']['unknown'] = self.resource['allocations'].pop('direct')
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            self.validate()
        self.resource = original
        self.resource['allocations']['direct']['gpu'] = 3
        with self.assertRaisesRegex(ValueError, 'device'):
            self.validate()

    def test_duplicate_cpu_or_wrong_worker_count_rejected(self):
        self.resource['allocations']['direct']['workers'] = 8
        with self.assertRaisesRegex(ValueError, 'allocation'):
            self.validate()
        self.resource['allocations']['direct']['workers'] = 9
        self.resource['allocations']['direct']['cpus'][1] = 10
        with self.assertRaisesRegex(ValueError, 'allocation'):
            self.validate()

    def test_resume_only_complete_matching_boundary(self):
        state = dict(boundary='complete_condition_cycle', steps=41250, cycle=3,
                     controller='direct', protocol_sha256='same', seed=17,
                     learner=dict(algorithm='sac'), cycles=[dict(cycle=3, steps=41250)])
        args = (dict(steps=41250), self.executions['direct'], 'direct', 'same')
        validate_boundary(state, *args)
        for key, value in [('boundary', 'periodic'), ('steps', 41249), ('cycle', 4),
                           ('protocol_sha256', 'other'), ('controller', 'vmc'), ('seed', 18)]:
            changed = copy.deepcopy(state); changed[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'complete-cycle'):
                validate_boundary(changed, *args)


if __name__ == '__main__':
    unittest.main()
