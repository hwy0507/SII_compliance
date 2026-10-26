"""Final acceptance must reject missing summary coverage, not silently skip it."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_nonrl_new30_20261026 import verify_family_summary


class FinalSummaryAuditTests(unittest.TestCase):
    def setUp(self):
        self.families = ("esn", "rnn", "mlp")
        self.seeds = (1, 2, 3)
        self.keys = ("task_success", "strict_success", "spt_mean", "peak_torque_mean_nm",
                     "human_comfort_torque_compliance_contact_time_weighted", "machine_safety_violation_rate")
        self.methods = {
            f"{family}_s{seed}": {key: 3*seed if key in ("task_success", "strict_success") else seed/4
                                 for key in self.keys}
            for family in self.families for seed in self.seeds}
        self.summary = {family: {key: {"per_seed": [.25, .5, .75], "mean": .5, "sample_sd": .25}
                                for key in self.keys} for family in self.families}

    def check(self, summary):
        verify_family_summary(self.methods, summary, self.families, self.seeds)

    def test_complete_summary_and_real_no_contact_na_are_accepted(self):
        self.check(self.summary)
        key = "human_comfort_torque_compliance_contact_time_weighted"
        self.methods["mlp_s2"][key] = None
        self.summary["mlp"][key] = {"per_seed": [.25, None, .75], "mean": None, "sample_sd": None}
        self.check(self.summary)

    def test_omitted_families_metrics_and_stat_fields_are_rejected(self):
        variants = [{}]
        missing_family = copy.deepcopy(self.summary)
        del missing_family["rnn"]
        variants.append(missing_family)
        missing_metric = copy.deepcopy(self.summary)
        del missing_metric["esn"]["spt_mean"]
        variants.append(missing_metric)
        missing_stat = copy.deepcopy(self.summary)
        del missing_stat["mlp"]["task_success"]["sample_sd"]
        variants.append(missing_stat)
        for summary in variants:
            with self.subTest(summary=summary), self.assertRaises(RuntimeError):
                self.check(summary)

    def test_wrong_seed_order_mean_sd_and_coverage_are_rejected(self):
        for field, value in (("per_seed", [.75, .5, .25]), ("per_seed", [.25, .5]),
                             ("mean", .6), ("sample_sd", .2)):
            summary = copy.deepcopy(self.summary)
            summary["rnn"]["spt_mean"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                self.check(summary)


if __name__ == "__main__":
    unittest.main()
