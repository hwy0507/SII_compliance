"""Physical integration smoke: zero canonical action, no network/updates.
A short run validates measurement contracts, not task success.
"""
import argparse
import dataclasses
import json
from pathlib import Path
import numpy as np
from office_env import OfficeEnv
from rewards import IntervalMetrics, OfficeReward, RewardConfig


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--duration",type=float,default=6.4)
    parser.add_argument("--physics-dt",type=float,default=.0001)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    config=RewardConfig(horizon_s=args.duration)
    rewarder=OfficeReward(config)
    env=OfficeEnv(args.output/"episodes",rewarder,duration=args.duration,
                  physics_dt=args.physics_dt,save_substeps=True)
    observations=[];intervals=[];reward_rows=[]
    try:
        observation,info=env.reset(seed=2026093001,options={"variant":-2,"events":"all"})
        phi=info["interval"]["potential"]
        assert info["interval"]["substeps"]==0
        assert observation.shape==(48,)
        observations.append(observation.copy())
        for _ in range(round(args.duration/.04)+1):
            observation,done,info=env.step_raw(np.zeros(7))
            iv=info["interval"]
            assert iv["substeps"]>0
            assert abs(iv["elapsed_s"]-.04)<1e-9
            metric=IntervalMetrics(**{f.name:iv[f.name] for f in dataclasses.fields(IntervalMetrics)})
            result=info.get("evaluation",{})
            success=bool(result.get("strict_success",False)) if done else False
            value,row=rewarder(metric,np.zeros(7),current_potential=phi,
                next_potential=iv["potential"],terminated=done,success=success,
                failure=done and not success,
                terminal_reason=("strict_success" if success else
                                 result.get("abort_reason") or "finite_horizon_timeout") if done else None,
                task_complete_before_interval=iv.get("task_complete_before_interval",False))
            intervals.append(iv);reward_rows.append(row);observations.append(observation.copy())
            phi=iv["potential"]
            if done:break
        else:
            raise AssertionError("Did not terminate within planned horizon")
        metrics=result["metrics"]
        elapsed=sum(iv["elapsed_s"] for iv in intervals)
        expected_error=(metrics["position_rmse_3d_m"]**2*elapsed
                        /(args.duration*config.error_scale_m**2))
        measured=rewarder.error_cost_total
        np.testing.assert_allclose(measured,expected_error,rtol=2e-6,atol=1e-10)
        np.testing.assert_allclose(rewarder.peak_torque_nm_per_joint,
            metrics["generalized_actuator_torque_peak_by_joint_nm"],rtol=2e-6,atol=1e-7)
        assert sum(iv["substeps"] for iv in intervals)==metrics["samples"]
        assert np.isfinite(observations).all()
        summary=dict(status="passed",purpose="short_physical_substep_reward_contract_only",
            seed=2026093001,variant=-2,events="all",duration_requested_s=args.duration,
            duration_executed_s=elapsed,control_intervals=len(intervals),
            physical_substeps=sum(iv["substeps"] for iv in intervals),
            reference="existing stage waypoint",
            error_integral_reward=measured,error_integral_from_evaluator_rmse=expected_error,
            error_integral_relative_difference=abs(measured-expected_error)/max(expected_error,1e-12),
            peak_actual_torque_nm=rewarder.peak_torque_nm_per_joint,
            peak_torque_evaluator_nm=metrics["generalized_actuator_torque_peak_by_joint_nm"],
            peak_torque_squared_increment_sum=sum(x["peak_torque_cost_increment"] for x in reward_rows),
            final_normalized_peak_squared=rewarder.peak_torque_ratio**2,
            final_observation_delta_norm=float(np.linalg.norm(observations[-1]-observations[-2])),
            final_observation_finite=bool(np.isfinite(observations[-1]).all()),
            aborted=result.get("abort_reason"),task_success=result.get("task_success"),
            strict_success=result.get("strict_success"),
            config=config.to_dict())
        (args.output/"VALIDATION.json").write_text(json.dumps(summary,indent=2)+"\n")
        print(json.dumps(summary,indent=2))
    finally:
        env.close()


if __name__=="__main__":
    main()
