"""Report tests use synthetic metadata/arrays, not simulated performance."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from report_campaign import aggregate_groups, average, report

CASE = dict(id="fixture0", seed=111, variant=0, ball_speed=1.7,
            person_stroke=.2, rod_stroke=.235, events="all")


def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj))


def campaign(root, rl=False):
    specs = [dict(id="metric_seed61001", reward="metric", seed=61001)] if rl else []
    write(root/"PROTOCOL.json", dict(runs=specs, duration_s=55., evaluation_dt=27.5,
                                     evaluation_manifest_sha256="manifest"))
    write(root/"COMMON_BUDGET.json", dict(step=10000))


def add_run(root, name="esn", *, method="esn", model=b"same-model",
            duration=55., seed=111, norm_changed=False, train_seed=61001,
            success=None):
    folder = root/"evaluation"/name
    raw_path = folder/"case_000"/"rollout.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    mjb = raw_path.with_suffix(".mjb")
    mjb.write_bytes(model)
    digest = hashlib.sha256(model).hexdigest()
    arrays = raw_path.parent/"rollout_metrics"/"substep_metrics.npz"
    arrays.parent.mkdir()
    np.savez_compressed(arrays, time=np.array([duration/2, duration]),
                        dt=np.array([duration/2, duration/2]))
    metrics = dict(position_rmse_3d_m=.02, generalized_actuator_torque_peak_nm=40.,
                   linear_speed_peak_mps=.1, samples=2)
    raw = dict(arguments=dict(CASE, seed=seed, dt=27.5, duration=55.),
               metrics=metrics, physical_valid=True, placement_complete=False,
               task_success=False, strict_success=False,
               full_task_horizon_completed=duration==55.,
               execution_complete=duration==55.,
               abort_reason=None if duration==55. else "test_abort",
               contact_required=["ball","cup"], contact_coverage_valid=False,
               model_sha256=digest)
    write(raw_path, raw)
    behavior = dict(compliant_progress_success=success,
                    strict_compliant_progress_success=success,
                    required_contacts=["ball","cup"],
                    event_results=[dict(obstacle_id="ball",status="unknown"),
                                   dict(obstacle_id="cup",status="not_exposed")])
    if method=="rl":
        ck = root/name/"checkpoint_step_0010000"
        write(ck/"official_agent_state.json", dict(config=dict(seed=train_seed)))
        ch = {"official_agent_state.json":hashlib.sha256((ck/"official_agent_state.json").read_bytes()).hexdigest()}
    else:
        ck = root/"model.npz"
        ck.write_bytes(b"checkpoint")
        ch = {str(ck):hashlib.sha256(ck.read_bytes()).hexdigest()}
    write(folder/"PROTOCOL.json", dict(method=method, checkpoint=str(ck),
        checkpoint_sha256=ch,manifest_sha256="manifest",cases=[CASE],
        duration_s=55.,physics_dt=27.5))
    row = dict(case=CASE,raw_result=str(raw_path),behavior=behavior,metrics=metrics,
               model_sha256=digest)
    write(folder/"SUMMARY.json",dict(status="complete",method=method,rows=[row],
        normalizers_before={"count":4} if method=="rl" else None,
        normalizers_after={"count":5 if norm_changed else 4} if method=="rl" else None))
    return raw_path


class ReportTests(unittest.TestCase):
    def test_nonexistent_campaign_is_not_created(self):
        with tempfile.TemporaryDirectory() as td:
            missing=Path(td)/"future_campaign"
            with self.assertRaises(FileNotFoundError):
                report(missing)
            self.assertFalse(missing.exists())

    def test_seed_means_not_pooled_episodes(self):
        runs=[]
        for seed, values in [(1,[1.]),(2,[2.,2.]),(3,[3.,3.,3.])]:
            ep=[dict(rmse_cm=x,peak_torque_nm=40.,peak_velocity_mps=.1) for x in values]
            runs.append(dict(group="metric",training_seed=seed,episodes=ep,status="complete",
                             case_count_matches=True,mean_all_observed=average(ep)))
        g=next(g for g in aggregate_groups(runs) if g["group"]=="metric")
        self.assertAlmostEqual(g["metrics"]["rmse_cm"]["mean"],2.)
        self.assertAlmostEqual(g["metrics"]["rmse_cm"]["seed_sd"],1.)

    def test_esn_has_condition_not_seed_sd(self):
        ep=[dict(rmse_cm=x,peak_torque_nm=40.,peak_velocity_mps=.1) for x in (1.,3.)]
        runs=[dict(group="esn",training_seed=None,episodes=ep,status="complete",
                   case_count_matches=True,mean_all_observed=average(ep))]
        g=next(g for g in aggregate_groups(runs) if g["group"]=="esn")
        self.assertIsNone(g["metrics"]["rmse_cm"]["seed_sd"])
        self.assertAlmostEqual(g["metrics"]["rmse_cm"]["condition_sd"],np.sqrt(2))

    def test_empty_partial_is_pending_not_zero(self):
        with tempfile.TemporaryDirectory() as td:
            result=report(Path(td))
            self.assertEqual(result["status"],"partial")
            self.assertFalse(result["comparable_full55_matrix"])
            self.assertIsNone(result["groups"][0]["metrics"]["rmse_cm"]["mean"])
            self.assertTrue((Path(td)/"report/REPORT.md").is_file())

    def test_model_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign(root)
            add_run(root,"esn",model=b"one")
            add_run(root,"hybrid",method="hybrid",model=b"two")
            result=report(root)
            self.assertTrue(any("MJB hash mismatch" in x["message"] for x in result["audits"]["errors"]))
            self.assertFalse(result["comparable_full55_matrix"])

    def test_actual_seed_mismatch_not_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign(root)
            add_run(root,seed=222)
            result=report(root)
            self.assertTrue(any("seed differs" in x["message"] for x in result["audits"]["errors"]))

    def test_early_abort_kept_and_duration_verified(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign(root);add_run(root,duration=27.5)
            result=report(root)
            early=result["early_or_unverified_horizon"]
            self.assertEqual(len(early),1)
            self.assertEqual(early[0]["actual_duration_s"],27.5)
            self.assertEqual(early[0]["rmse_cm"],2.)
            self.assertFalse(result["comparable_full55_matrix"])

    def test_changed_normalizer_and_training_seed_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign(root,rl=True)
            add_run(root,"metric_seed61001",method="rl",norm_changed=True,train_seed=61002)
            result=report(root)
            messages=[e["message"] for e in result["audits"]["errors"]]
            self.assertTrue(any("normalizer" in x for x in messages))
            self.assertTrue(any("training seed" in x for x in messages))

    def test_unknown_exposure_and_placement_kept_separate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign(root);add_run(root,success=None)
            result=report(root)
            g=next(x for x in result["groups"] if x["group"]=="esn")
            self.assertEqual(g["counts"]["compliant_progress_success"]["unknown"],1)
            self.assertEqual(g["counts"]["placement_success"]["false"],1)
            self.assertEqual(g["counts"]["event_status_counts"]["not_exposed"],1)
            self.assertEqual(g["counts"]["physical_valid"]["true"],1)
            self.assertEqual(g["counts"]["full55"]["true"],1)

    def test_false_claimed_full_duration_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign(root);rawpath=add_run(root,duration=27.5)
            raw=json.loads(rawpath.read_text())
            raw["full_task_horizon_completed"]=True;raw["execution_complete"]=True
            write(rawpath,raw)
            result=report(root)
            self.assertTrue(any("claimed full horizon" in e["message"] for e in result["audits"]["errors"]))


if __name__=="__main__":
    unittest.main()
