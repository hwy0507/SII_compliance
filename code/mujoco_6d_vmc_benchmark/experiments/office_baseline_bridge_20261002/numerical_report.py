"""Report registered first-impact timestep diagnostics, separate from task results."""
import json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/office_bridge")
def main():
    root=ROOT/"numerical01";rows=[];fig,ax=plt.subplots(3,1,figsize=(10,8),sharex=True,layout="constrained")
    for name in ["dt_1e4","dt_5e5","dt_25e6"]:
        d=root/name;s=json.loads((d/"rollout.json").read_text());dt=s["arguments"]["dt"];contact=s["stats"]["events"]["ball"];derivation=json.loads((d/"MODEL_DERIVATION.json").read_text())
        assert derivation["restored_archive_sha256"]==derivation["original_sha256"]
        assert s["model_sha256"]==derivation["derivative_sha256"]
        raw=np.load(d/"rollout_metrics/substep_metrics.npz");z=np.load(d/"rollout.npz");ball=np.load(d/"rollout_ball_detail.npz")
        i=int(np.argmin(abs(z["time"]-2.4)));assert abs(z["time"][i]-2.4)<1e-8
        values=dict(variant=name,dt_s=dt,duration_s=float(raw["dt"].sum()),ball_peak_n=contact["peak_n"],ball_impulse_ns=contact["impulse_ns"],ball_contact_ms=contact["duration_s"]*1000,
            external_penetration_mm=s["stats"]["max_external_penetration_m"]*1000,position_rmse_mm=s["metrics"]["position_rmse_3d_m"]*1000,
            peak_torque_nm=s["metrics"]["generalized_actuator_torque_peak_nm"],peak_hand_speed_mps=s["metrics"]["linear_speed_peak_mps"],ball_velocity_at_2p4s_mps=z["ball_velocity"][i].tolist(),model_derivation=derivation)
        rows.append(values);label=f'dt={dt:g} s';select=(ball["time"]>=2)&(ball["time"]<=2.35)
        ax[0].plot(ball["time"][select],ball["velocity"][select,1],label=label,lw=1)
        select=(raw["time"]>=2)&(raw["time"]<=2.35)
        ax[1].plot(raw["time"][select],np.linalg.norm(raw["twist"][select,:3],axis=1),lw=1)
        ax[2].plot(raw["time"][select],np.linalg.norm(raw["error"][select],axis=1)*1000,lw=1)
    coarse=np.load(root/"dt_1e4/rollout.npz");full=np.load(ROOT/"transfer01/zero/rollout.npz")
    keys=["qpos","qvel","ctrl","hand","ball","ball_velocity","observation","applied_action"]
    prefix={k:bool(np.array_equal(coarse[k],full[k][:len(coarse[k])])) for k in keys};assert all(prefix.values()),prefix
    for a,label in zip(ax,["Ball y velocity (m/s)","Hand speed (m/s)","Tracking error (mm)"]):a.set_ylabel(label);a.grid(alpha=.2)
    ax[-1].set_xlabel("Physical time (s)");ax[0].legend();fig.suptitle("Nominal office v5: first-impact numerical sensitivity\nOnly physics timestep changes; no full-task or policy-ranking conclusion")
    fig.savefig(root/"timestep_comparison.png",dpi=160);fig.savefig(root/"timestep_comparison.pdf");plt.close(fig)
    base=rows[0];relative=[]
    for r in rows[1:]:relative.append(dict(variant=r["variant"],peak_change_vs_coarse_pct=100*(r["ball_peak_n"]/base["ball_peak_n"]-1),impulse_change_vs_coarse_pct=100*(r["ball_impulse_ns"]/base["ball_impulse_ns"]-1),hand_peak_speed_change_vs_coarse_pct=100*(r["peak_hand_speed_mps"]/base["peak_hand_speed_mps"]-1)))
    result=dict(registration=str(root/"REGISTRATION.json"),rows=rows,coarse_prefix_identical_to_full_zero=prefix,relative_to_coarse=relative,
        limitations=["First 3 s nominal diagnostics only; not full 55 s formal results or evaluation of learned policies at a new timestep.","Only opt.timestep changes, certified by restoring the original model binary hash.","Impulse and post-impact motion may be less sensitive than force maximum; three timesteps do not prove asymptotic convergence or material realism.","No thresholds, geometry or controller parameters selected from these results."])
    (root/"SUMMARY.json").write_text(json.dumps(result,indent=2,allow_nan=False))
    columns=["variant","dt_s","duration_s","ball_peak_n","ball_impulse_ns","ball_contact_ms","external_penetration_mm","position_rmse_mm","peak_torque_nm","peak_hand_speed_mps"]
    with (root/"SUMMARY.csv").open("w") as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows([{k:r[k] for k in columns} for r in rows])
    print(json.dumps(dict(prefix_equal=all(prefix.values()),rows=[{k:r[k] for k in columns} for r in rows],relative=relative),indent=2))
if __name__=="__main__":main()
