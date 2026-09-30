"""Report semantics: completed files must not conceal early physical aborts."""
import json
import tempfile
import unittest
from pathlib import Path
import report


class HorizonReportTests(unittest.TestCase):
    def test_mixed_horizons_preserve_failures_and_raw_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            rows=[]
            for index,(duration,full,reason,rmse) in enumerate(
                    [(55.,True,None,.3),(20.08,False,"external_penetration",.1)]):
                raw=root/f"raw_{index}.json"
                # Two actual physics resolutions; manifest dt alone is insufficient.
                raw.write_text(json.dumps(dict(metrics=dict(
                    timestep_sample_counts={"0.00005":200000,"0.0001":round((duration-10)/.0001)}))))
                rows.append(dict(case_index=index,position_rmse_3d_m=rmse,
                    peak_torque_nm=40.+index,peak_velocity_mps=.1,
                    strict_success=False,task_success=False,physical_valid=False,
                    placement_complete=False,full_task_horizon_completed=full,
                    execution_complete=full,abort_reason=reason,
                    condition={"duration_s":55.,"physics_dt":.0001},
                    raw_result_json=str(raw)))
            directory=root/"fixed_final"/"metric_seed1";directory.mkdir(parents=True)
            (directory/"SUMMARY.json").write_text(json.dumps(dict(status="complete",
                protocol=dict(duration_s=55.,checkpoint="fixed",manifest_sha256="test"),
                rows=rows)))
            spec=dict(id="metric_seed1",seed=1,mode="metric")
            (root/"CAMPAIGN_PROTOCOL.json").write_text(json.dumps(dict(runs=[spec],steps=10)))
            payload=report.report(root,root/"report")
            seed=payload["per_seed"][0]
            self.assertTrue(seed["evaluation_files_complete"])
            self.assertEqual(seed["episodes"],2)
            self.assertEqual(seed["full_55s_episodes"],1)
            self.assertEqual(seed["early_abort_episodes"],1)
            self.assertEqual(seed["early_termination_episodes"],1)
            self.assertEqual(seed["full_55s_rate"],.5)
            self.assertEqual(seed["actual_substep_duration_s"],[55.,20.08])
            self.assertEqual(seed["rmse_cm"],20.)
            self.assertEqual(seed["comparison_scope"],"mixed_length_failure_diagnostic")
            group=payload["across_seed"][0]
            self.assertEqual(group["total_episodes"],2)
            self.assertEqual(group["full_55s_episodes"],1)
            self.assertEqual(group["early_abort_episodes"],1)
            self.assertEqual(group["full_55s_rate_mean"],.5)
            markdown=(root/"report"/"REPORT.latest.md").read_text()
            self.assertIn("评测文件完备",markdown)
            self.assertIn("混合长度失败诊断",markdown)
            self.assertIn("完整55s/总数",markdown)
            self.assertIn("20.08",markdown)
            self.assertEqual(payload["mixed_length_partitions"],["fixed_final"])

    def test_missing_physical_evidence_remains_unknown(self):
        row=report.episode_execution(
            {"condition":{"duration_s":55.,"physics_dt":.00005},"substep_samples":1100000},
            {"duration_s":55.},[])
        self.assertIsNone(row["actual_substep_duration_s"])
        self.assertIsNone(row["full_task_horizon_completed"])
        self.assertIsNone(row["execution_complete"])
        self.assertIsNone(row["verified_full_55s"])
        self.assertFalse(row["early_abort"])
        self.assertEqual(row["termination_reason"],"unknown")

    def test_full_horizon_flag_conflicting_with_duration_is_flagged(self):
        warnings=[]
        row=report.episode_execution(dict(
            full_task_horizon_completed=True,execution_complete=True,
            metrics=dict(samples=1000,timestep_s=.0001)),
            {"duration_s":55.},warnings)
        self.assertTrue(row["early_termination"])
        self.assertFalse(row["verified_full_55s"])
        self.assertTrue(warnings)


if __name__=="__main__":
    unittest.main(verbosity=2)
