# 统一物理子步测量与顺序实验队列

测量模块为新增的 `physics_substep_metrics_20260923.py`，由独立 `run_with_substep_metrics_20260923.py` 包装原runner。未修改canonical仿真、控制或任务源码。它只在进程内包裹环境 `_physics_step` 登记当前episode，并在原 `mujoco.mj_step` 返回后读取测量。

末端位置、速度使用独立scratch MjData，将当前qpos/qvel复制后调用 `mj_kinematics`、`mj_comPos`、`mj_jacBody`，得到更新后 `J(q) qdot`。不对live data调用forward，不进行额外碰撞求解，不修改控制、模型或live状态。实际广义执行器力矩读取 `qfrc_actuator[:7]`，另记录 `actuator_force[:7]`。两者保留的是该step动力学求值结果，通常早于步末更新后的位置/速度；报告不能说它们严格同时。

按同一task stage记录物理步位置误差RMSE（XYZ及3D）、误差/速度/力矩峰值、样本数及阶段时间。任务阶段切换仍遵循原控制流程，测量不改变参考目标。

## 非侵入性验证

3个单元测试通过：scratch速度与独立fresh kinematics一致；采样不改变live qpos/qvel/qacc/warmstart/ctrl/xpos/xmat/qfrc_actuator/actuator_force/cvel/qfrc_bias；分阶段计数、env.close后保存及异常恢复hook正确。

服务器8 s VMC与reference admittance r2各做一对on/off smoke。每对原rollout NPZ的全部18个数组逐元素完全相同；审计各采集160000样本，dt=50 μs。VMC开启/关闭耗时43.83/41.26 s（+6.23%）；导纳43.74/41.02 s（+6.64%）。开销是该smoke环境的观测值，不承诺所有配置相同。证据为 `docs/evidence/classical_20260923/substep_metrics_invariance_smoke.json`。

## CLI与sidecar

```bash
python scripts/run_with_substep_metrics_20260923.py \
  --runner /path/to/original_runner.py --metrics-output /fresh/metrics \
  -- <原runner参数>
```

`--disable-audit`用于精确一致性对照。可选 `--policy-transform module:function` 或 `--teacher-transform module:function` 用于单独标记的因果消融；原基线不设置transform。

- `audit_manifest.json`：原runner参数、源码hash、是否启用、退出异常、wall time、episodes汇总。
- `episode_0/substep_metrics.json`：真实物理步速度峰值、广义执行器力矩峰值、各joint/actuator峰值、全程/分阶段RMSE、时序口径。
- `episode_0/substep_metrics.npz`：每物理步time(float64)、stage(int16)、error/twist/qfrc_actuator/actuator_force(float32)；极值和平方和在线以float64累计。

## 已冻结的执行顺序

1. fixture9301四项机制消融：ESN no-x-yield、ESN raw-action lowpass α=0.25、MLP同低通、VMC同低通。低通保留原安全滤波，并不作为预选获胜控制器。
2. 原始VMC/impedance/admittance/MLP/ESN及reference K300 impedance、K900 impedance、r2 admittance，共8版本×原3物理fixture=24条。与前4项一起进入同一个4-worker队列。
3. 完整28条均无执行错误、测量存在且物理步覆盖24 s后，才顺序启动独立冻结的经典参数开发48回合与同layout新条件验证30回合。选模规则和预算详见 `CLASSICAL_TUNING_PROTOCOL_20260923.md`。

任意时刻最多4个仿真worker，不会重叠执行两个阶段。失败保留原始证据，driver不会将不完整测量交给后续选模。

2026-09-23进展：28条测量/消融全部完成，退出码均为0且审计完整；24条未干预基准的每条18个原NPZ数组与此前对应实验逐元素完全相同。完整无扰动证据为 `docs/evidence/classical_20260923/substep_campaign/full24_invariance.json`，完整新物理测量为同目录 `measured28_final.json`。driver随后自动进入fixed_budget阶段（Unix启动时间1790161459.3168993）；此处不预先声称后续48+30条已完成。

服务器base为 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923`。driver初始PID413277。状态与证据入口：

- `measured_campaign/status.json`、`measured_campaign/queue.json`
- `measured_campaign/measured.log`、`measured_campaign/measured28/`
- `measured_campaign/fixed_budget.log`、`measured_campaign/fixed_budget/`
- 全部完成标记为 `measured_campaign/COMPLETE.json`；不能把仅启动队列视为已完成。
- 隔离源码为 `source_substep_batch/` 与 `source_fixed_budget/`；后者包含冻结协议MD。
