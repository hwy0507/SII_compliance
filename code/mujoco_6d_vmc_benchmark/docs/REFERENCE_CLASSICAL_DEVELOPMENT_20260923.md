# 同三组开发fixture的classical参考接口修正

本次保留原15条48D配对结果，另跑两种reference控制器修正。全部24 s结果包含失败回合；8 s smoke只验证接口，不计入下表。开发过程中的K900候选和bug修复均明确分组，不能将选中的开发结果当作未见test。

| 控制器版本 | 有效仿真完成 | task通过 | panel gate通过 | 3D RMSE均值 mm | 回合速度峰值均值 m/s（25Hz） | 回合力矩峰值均值 Nm（4ms command） |
|---|---:|---:|---:|---:|---:|---:|
| 原始raw waypoint impedance | 3/3 | 3/3 | 0/3 | 18.887 | 1.65567 | 87.000 |
| moving-reference impedance K300 | 3/3 | 0/3 | 0/3 | 105.478 | 0.11369 | 33.469 |
| moving-reference impedance K900候选 | 3/3 | 3/3 | 0/3 | 66.010 | 0.12299 | 34.854 |
| 原始velocity-only admittance | 3/3 | 2/3 | 1/3 | 137.220 | 0.13902 | 39.611 |
| reference admittance r1 | 0/3 | 不适用 | 不适用 | 执行错误 | 执行错误 | 执行错误 |
| reference admittance r2 | 3/3 | 2/3 | 1/3 | 125.911 | 0.07999 | 35.488 |

阻抗moving-reference确实降低了完整24 s回合的速度/力矩峰值，不能只归功于8 s smoke。K300的末端误差55.445/55.832/58.520 mm仍超过15 mm task门；三条均已抬起物块且final_stage=3。位置误差限制在6000次更新中触发4487/4507/4510次。K900、Krot45、M1、I0.08、zeta1、nullspace damping2作为单独预声明候选恢复task通过，但9300/9301的杆接触只有0.01635/0.1733 s，不足0.3 s；9302的穿透0.20858 mm超过0.2 mm。因此两个moving-reference版本都还未成为可靠通过所有门的baseline。

导纳r1在8 s smoke正常，但24 s完整运行三个fixture均触发“Observed nominal is not a scalar multiple of the reconstructed WBC”。根因为MuJoCo step后qpos与缓存机器人运动学快照并不处于同一时刻；r2使用与原WBC一致的机器人运动学快照，保留原1e-7检查，不读取接触真值、不修改物理或任务。r2三条24 s完成，无相应运行错误；9300通过panel gate，9301因0.20375 mm穿透失败，9302同时task未完成且0.21080 mm穿透。参数保持K95/Krot4/M0.55/I0.065/zeta1，未为成功放宽门。

本轮不能从所有失败回合的低RMSE判定哪个方法总体更好：原始impedance甚至完全没有杆接触，且参考规则按任务状态切换，较快退出或未完成的阶段会改变全程误差分布。

## 本地证据

- `docs/evidence/classical_20260923/panel48_final.json`：原五方法完整15条；`panel48_traces/`保留全部15份600×48 finite原始NPZ。
- `reference48_final.json` / `reference48_protocol.json`：K300三条完成+导纳r1三条执行错误。`reference48_traces/`含阻抗原始JSON/NPZ和导纳错误日志。
- `reference_k900/`：FINAL_RESULT、protocol及三条原始JSON/NPZ。
- `reference_r2/`：FINAL_RESULT、protocol及三条原始JSON/NPZ、`admittance_reference_state.npz`（每条600×26 finite），可分析offset和action clipping。
- `reference_smoke_final.json`：单独保留，不并入24 s矩阵。
- `server_model_metadata.json`与`server_model_metadata_reference_revisions.json`：运行环境版本及共29份归档MJB的SHA256、大小、远程路径。非smoke每个fixture的9个方法/版本archive hash完全相同。

服务器统一根目录是 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/`。原快照`source_panel48`、`source_reference`与修正快照`source_reference_k900`、`source_reference_r2`分别保留；对应输出`panel_matched48`、`panel_reference48`、`panel_reference_k900_48`、`panel_reference48_r2`互不覆盖。

环境：DGX Spark aarch64，Python3.12.3，MuJoCo3.11.0，numpy2.5.2。速度峰值为25Hz采样，力矩为4ms控制命令峰值而非细物理步actuator观测；后续正式矩阵应对所有方法补同一物理子步审计。
