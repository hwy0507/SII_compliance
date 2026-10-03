"""Synthetic regressions for whole-seed selection; no physics or research data."""
import unittest
from research72_select_learning_20261003 import rank_variants


class PairedSelectionTests(unittest.TestCase):
    def setup_rows(self):
        candidates=[];rows={}
        for variant in ('one_lucky_seed','consistent'):
            for seed in (1,2,3):
                name=variant+str(seed)
                candidates.append(dict(name=name,category='esn',variant=variant,seed=seed,checkpoint_sha256=name))
                for condition in ('a','b'):
                    success=(seed==1) if variant=='one_lucky_seed' else condition=='a'
                    rows[name,condition]=dict(checkpoint_sha256=name,strict_success=success,task_success=success,
                        full_horizon=True,penetration_mm=.1,edge_penetration_mm=.1,rmse_mm=10.,peak_torque_nm=20.)
        return candidates,rows

    def test_all_seeds_choose_one_shared_variant(self):
        c,r=self.setup_rows();rank=rank_variants(c,r,[1,2,3],['a','b'])['esn']
        self.assertEqual(rank[0]['variant'],'consistent')
        self.assertEqual([x['seed'] for x in rank[0]['candidates']],[1,2,3])
        self.assertEqual(rank[0]['denominator'],6)

    def test_missing_failed_episode_does_not_shrink_denominator(self):
        c,r=self.setup_rows();del r['one_lucky_seed2','b']
        with self.assertRaises(KeyError):rank_variants(c,r,[1,2,3],['a','b'])

    def test_zero_success_methods_are_still_ranked(self):
        c,r=self.setup_rows()
        for v in r.values():v.update(strict_success=False,task_success=False)
        self.assertEqual(len(rank_variants(c,r,[1,2,3],['a','b'])['esn']),2)


if __name__=='__main__':unittest.main()
