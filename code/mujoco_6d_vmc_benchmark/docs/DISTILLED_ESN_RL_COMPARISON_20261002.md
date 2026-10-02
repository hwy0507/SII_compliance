# 最新蒸馏 ESN 与 RL：固定 office 三指标比较（2026-10-02）

GitHub main 核验提交：`14820fac7141fa8779aa56b5ae0ba595ee2ee0a5`。没有一个被正式锁定为最终成功模型的新版 ESN；最新发布批次含13个有效学习模型及24条学生闭环候选/干预。全部失败。
本报告复用已保存的匹配配置回合，新增仿真0；独立重算35条完整回合、19,250,000个原生物理子步。

## 结论与版本身份

- 基础VMC蒸馏 `original_v2`：30.058 mm / 39.210 Nm / 0.370185 m/s，权重SHA256 `97f2c7451db6948c7f5f2d7a2b53dd1083a8e057f9d180620f521a3d8d284747`。
- 它比四个直接动作RL的RMSE都低；峰矩/峰速并非全胜。对RL调导纳RMSE几乎相同；对RL调阻抗RMSE与峰矩较高、峰速略低；对RL调VMC三项均较低。
- context候选29.438 / 37.294 / .382850；推进较远的integral41为76.718 / 38.129 / .398990。
- 最后一组学习候选DAgger-drift为125.970 / 37.615 / .388723，不能把较早original_v2包装成最后训练模型，也不能认为后期优化必然更好。
- Zero及固定阻抗作为参照保留。全部task/strict=false；低指标不等于完成放置。

## 相同配置及核验

同一office-tool-contact-v5、seed2026091751、55s、dt1e-4、MuJoCo3.11.0、25Hz公共策略/4ms伺服。
MJB SHA256 `b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1`。逐回合核对归档二进制模型、fixture、公共arguments和8个公共源码hash
（WBC、规划、场景、gate、指标），策略模式/权重/输出路径/记忆干预区别显式排除。
新ESN与RL运行使用同一参考summary hash；ESN权重逐文件复核，所有原始指标文件另存hash。
RMSE按三维位置误差平方的时间积分开方；峰值使用全部550000子步的真实qfrc_actuator绝对值和手部线速度范数。
从float32归档复算与原统计容差内一致，未用视频抽帧估计。
原ESN在airpig/Python3.11.15运行，RL在Spark/Python3.12运行；没有声称同机逐位复现。
两个host的zero统计30微米量级差异，不用于宣称微小优势。

## 主表：基础蒸馏与全部RL及经典对照

所有行task/strict=false，完整55s。
| Method | RMSE mm | Peak torque Nm | Peak hand speed m/s | Penetration mm | Final stage |
|---|---:|---:|---:|---:|---|
| esn_first_three/esn_original_v2 | 30.058 | 39.210 | 0.370185 | 0.111707 | carry |
| zero | 27.557 | 36.901 | 0.398633 | 0.158694 | carry |
| fixed_admittance | 33.959 | 41.143 | 0.389360 | 0.139791 | carry |
| parameter_admittance | 29.840 | 40.473 | 0.416043 | 0.195404 | carry |
| fixed_impedance | 24.323 | 37.377 | 0.335478 | 0.113233 | carry |
| parameter_impedance | 26.279 | 38.935 | 0.375062 | 0.117540 | carry |
| fixed_vmc | 56.781 | 37.866 | 0.370950 | 0.111872 | carry |
| parameter_vmc | 42.824 | 39.553 | 0.393182 | 0.147240 | carry |
| direct_metric_74001 | 76.758 | 47.090 | 0.310141 | 0.499765 | approach |
| direct_metric_74002 | 535.865 | 70.780 | 0.861965 | 0.161716 | approach |
| direct_office_task_74001 | 197.466 | 37.720 | 0.415320 | 0.125126 | approach |
| direct_office_task_74002 | 574.996 | 76.463 | 1.212784 | 0.127202 | approach |

## 最新发布的全部24条ESN评估

这是候选/干预表，不能当24个独立seed计算成功率。完整保留穿透超限与后期退化。
| Method | RMSE mm | Peak torque Nm | Peak hand speed m/s | Penetration mm | Final stage |
|---|---:|---:|---:|---:|---|
| esn_context_pair/esn_recovery_fast | 29.525 | 37.205 | 0.380968 | 0.128249 | carry |
| esn_context_pair/esn_recovery_long | 32.410 | 38.568 | 0.412502 | 0.190008 | carry |
| esn_context_pair/esn_reference_context | 29.438 | 37.294 | 0.382850 | 0.132814 | carry |
| esn_dagger_pair/esn_dagger_base | 153.759 | 37.061 | 0.374631 | 0.107625 | carry |
| esn_dagger_pair/esn_dagger_drift | 125.970 | 37.615 | 0.388723 | 0.139328 | carry |
| esn_final_pair/esn_final47_fixed | 56.656 | 40.702 | 0.402018 | 0.164717 | lift |
| esn_final_pair/esn_final47_gated | 137.349 | 36.489 | 0.398852 | 0.158803 | lift |
| esn_first_three/esn_coupled_abs | 71.273 | 37.088 | 0.368719 | 0.105663 | carry |
| esn_first_three/esn_coupled_signed | 72.095 | 37.439 | 0.386171 | 0.134387 | carry |
| esn_first_three/esn_original_v2 | 30.058 | 39.210 | 0.370185 | 0.111707 | carry |
| esn_progress_pair/esn_integral41 | 76.718 | 38.129 | 0.398990 | 0.158926 | carry |
| esn_progress_pair/esn_progress44_fixed | 200.110 | 37.455 | 0.373198 | 0.115353 | carry |
| esn_progress_pair/esn_progress44_gated | 57.720 | 36.713 | 0.416762 | 0.199552 | carry |
| final_gain/gain050 | 35.238 | 36.743 | 0.398836 | 0.158911 | carry |
| final_gain/gain075 | 69.836 | 36.667 | 0.422531 | 0.211843 | carry |
| final_gain/reset_each_observation | 27.324 | 37.876 | 0.424088 | 0.215557 | carry |
| readout_grid/rot015 | 82.821 | 38.645 | 0.415720 | 0.195834 | carry |
| readout_grid/rot040 | 71.900 | 37.659 | 0.408019 | 0.177531 | carry |
| readout_grid/xy025 | 96.396 | 36.782 | 0.379658 | 0.126094 | carry |
| readout_grid/xy025_z090_rot040 | 107.197 | 37.471 | 0.374582 | 0.118341 | carry |
| readout_grid/xy025_z110_rot015 | 123.411 | 38.562 | 0.394097 | 0.147492 | carry |
| readout_grid/z090_rot015 | 80.218 | 37.545 | 0.406565 | 0.175391 | carry |
| readout_grid/z110 | 100.641 | 36.833 | 0.406696 | 0.176171 | carry |
| readout_grid/z110_rot040 | 120.812 | 37.663 | 0.413502 | 0.189672 | carry |

## 比较边界

- Single fixed office development condition, 55 s, dt=1e-4; not formal dt=5e-5 or an independent generalization test.
- ESN was optimized on this office condition; RL weights were trained on four primitive scenes and transferred unchanged. Training exposure, optimization budgets and test familiarity are unequal.
- ESN simulation host airpig (Python 3.11.15); RL host Spark (Python 3.12). MuJoCo 3.11.0 and archived MJB agree. This is a matched-configuration archival comparison, not a bitwise same-host rerun.
- All 35 episodes fail task and strict. Low RMSE or low peak speed can coexist with stalled progress.
- 24 ESN evaluations are different candidates, calibrations and interventions, not 24 independent seeds; retain all instead of choosing a winner by a single metric.
- original_v2 is the base VMC-distilled ESN in the latest batch, not the last trained checkpoint. dagger_drift is the later trained variant; final_gain and reset are subsequent interventions.
- ESN architecture is a 128-unit reservoir plus 128-unit nonlinear readout and skip connection; it is not a classical linear-readout-only ESN.
- RMSE uses the common evaluator's evolving nominal task reference. Policies can change task progress, so this is not error against an externally fixed time trajectory.
- All peaks use all 550000 native substeps. Torque is actual qfrc_actuator maximum absolute value; speed is hand linear norm, not joint speed or action magnitude.

## 复算与产物

实际分析在Spark，未改变任何checkpoint、场景或已有结果。
服务器：`arm1@192.168.31.70:/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/esn_rl_comparison_20261002/`
包含COMPARISON.json/CSV、VERIFICATION.json、comparison.png/PDF及浏览页。
ESN原始数据：`/home/arm1/sii_shared/SII_compliance/runs/main/vmc_esn_four_hour_20261002_090155/evidence`；RL原始数据：`/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/office_bridge/transfer01`。
运行：`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python code/mujoco_6d_vmc_benchmark/experiments/office_baseline_bridge_20261002/compare_distilled_esn.py`。
