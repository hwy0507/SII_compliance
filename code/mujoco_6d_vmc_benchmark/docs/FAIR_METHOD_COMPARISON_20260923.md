# 公平 baseline 对比报告（2026-09-23）

本周评价固定为轨迹误差、峰值力矩、峰值速度三个维度，任务与物理有效性作为先决条件。下面先保存历史数据审计，不能将其当成当前 proposed 的正式比较：历史 `direct_esn` 与当前 `proprio48_action7` 学生不是同一个模型版本，原始运行的源码、模型 hash 和完整配置还未找齐。

## 历史诊断表：isolated push（不作为论文主表）

数值是每种方法 30 条 rollout 的均值，包含失败回合；轨迹误差读取 `track_error_rmse_m`，峰值力矩读取 `terminal_info.peak_torque_nm`，峰值速度读取 `ee_speed_peak_mps`。这些是历史 JSON 中的报告值，缺少原始 source/trace 时不能确认其采样率或重算全物理步峰值。速度 P95 作为补充；峰值速度高度一致，可能由共同初始运动或限速主导，尚未由时序数据证明原因。

| method | trajectory RMSE (m) ↓ | peak torque (N·m) ↓ | peak speed (m/s) ↓ | speed P95 (m/s) ↓ | task success | scenario success |
|---|---:|---:|---:|---:|---:|---:|
| ESN（历史 direct_esn） | 0.025344 | 32.080 | 0.082043 | 0.064038 | 30/30 | 7/30 |
| MLP | 0.022445 | 31.825 | 0.082042 | 0.062338 | 30/30 | 0/30 |
| VMC | 0.024790 | 31.144 | 0.082042 | 0.068263 | 30/30 | 0/30 |
| paper-MPC | **0.021736** | **30.859** | 0.082042 | 0.063573 | 30/30 | 0/30 |

相对 ESN 的均值差：MLP 的轨迹 RMSE 低 2.898 mm、峰值力矩低 0.255 N·m；VMC 分别低 0.554 mm、0.937 N·m；paper-MPC 分别低 3.608 mm、1.221 N·m。四种方法的峰值速度差小于 `8×10⁻⁷ m/s`，不能据此声称速度性能存在实质差异；速度 P95 才显示出可见但仍需结合轨迹和 gate 解读的差别。

## 成功判据

历史 `task_success` 与 `scenario_success` 必须分开保存；四种方法前者都是 30/30，后者仅历史 ESN 为 7/30。当前 renderer 的 push 场景门要求接触持续 ≥1.2 s、span ≥1.5 s、duty ≥0.7、位移 ≥30 mm、恢复误差 ≤12 mm、穿透 ≤0.5 mm、无上游误碰并抓起物体，还增加了 full-robot geometry 检查。原始 JSON 缺少这项新检查，不能把当前代码的 gate 定义直接追溯为历史运行定义；也不能把旧 `task_success` 等同于最终办公室抓取—搬运—稳定放置成功。

更关键的是，120 条记录的 push penetration 均超过当前项目的 **0.2 mm** 门槛；四种方法该项通过均为 **0/30**。即使旧 `geometry_valid=True`，也不能进入当前严格物理有效的论文排名。

原始 rollout JSON 没有逐回合 `failure_reasons`、`valid_contact`、`reproducibility_manifest`，缺失不能当成 false 或通过。需要完整原因审计时，应在统一的新 runner 重新运行并保存 failure reasons、penetration 和 contact pair。

从已保存的摘要可重算旧 gate（固定 precontact baseline recovery ≤12 mm、穿透 ≤0.5 mm，其余上述旧接触/位移/抓起门）：120 条均与旧标记完全一致。这只验证摘要内部一致性，不代替重算原始 physics trace。

| 方法 | 位移 ≥30 mm | 恢复 ≤12 mm | 穿透 ≤0.2 mm |
|---|---:|---:|---:|
| 历史 ESN | 21/30 | 16/30 | 0/30 |
| MLP | 26/30 | 0/30 | 0/30 |
| VMC | 23/30 | 7/30 | 0/30 |
| paper-MPC | 23/30 | 2/30 | 0/30 |

其余旧 gate 条件全部通过；`object_placed_on_table` 全部为 false。穿透范围为 ESN 0.3365–0.3844 mm、MLP 0.3192–0.3574 mm、VMC/paper-MPC 0.3347–0.3822 mm。

## 公平性和来源

- 原始目录：`server:/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_matrix_random_20260902/push`。
- 本地只读副本：`outputs/fair_push_comparison_20260923/`。
- 聚合脚本：[aggregate_fair_comparison_20260923.py](../tools/aggregate_fair_comparison_20260923.py)。
- 主结果：[comparison.json](../outputs/fair_push_comparison_20260923/comparison.json)；逐回合结果：[per_rollout.csv](../outputs/fair_push_comparison_20260923/per_rollout.csv)。
- 已验证：四种方法 seed 集合均为 `20264101..20264130`，配对的 `terminal_info.fixture`、record duration、grasp time、已记录的三个 push gain 字段和 rod stroke 相同。
- 但 `terminal_info.fixture.rod_stroke_m` 恒为 0.16 m，而顶层的实际配置 stroke 随条件变化为 0.078894–0.091898 m；该 fixture 对象不能代表完整实际场景。另外四种方法的 terminal 都写 `controller_family=direct_esn`、`observation_mode=direct_esn`、`uses_vmc=false`（包括 VMC 和 MPC），因此这些历史标签不能独立证明控制链身份。
- 未验证：原始控制周期、完整名义参考、完整安全配置、模型/源码 hash、训练/选模 split。当前仓库源码 hash 不能冒充历史运行 hash。
- 同目录的 `guarded_protocol.json` 是另一批 9 条 panel 条件，不能作为本表的 provenance。聚合器明确记录这项不匹配，不据此声称 office 未参与选择。
- 聚合器为每份原始 JSON 保存 SHA-256，并拒绝重复 seed、方法之间缺失 seed、错误 protocol 和非有限指标。

复算命令：

```bash
cd /home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark
/home/airpig/桌面/hwy/compliance_control/.venv-rl/bin/python tools/aggregate_fair_comparison_20260923.py \
  --input outputs/fair_push_comparison_20260923 \
  --output outputs/fair_push_comparison_20260923
```

## impedance / admittance 的位置

当前 impedance/admittance 结果来自另一套 v7 primitive 开发矩阵：24 条 rollout（2 控制器 × 4 fixture × 3 variant），不是上面 30 条统一 push fixture。因此暂不把它们并入主表，否则会把不同场景、不同 reference 和不同 gate 混在一起。

该开发矩阵的严格通过数为：Cartesian impedance `6/12`，Cartesian admittance `2/12`；详情见 [CLASSICAL_BASELINES_20260923.md](CLASSICAL_BASELINES_20260923.md)。admittance 当前把虚拟 offset 用于内部弹簧反馈，却没有把 offset 转换成独立的 WBC reference，这可能造成与名义反馈竞争，需要对照实验才能确定其对失败的贡献。新矩阵应在当前 panel runner 中同时运行 classical、VMC 和当前冻结 ESN/MLP，不再将新数据拼接进旧 30 条表。

## 当前可下的结论

历史表中 ESN 的轨迹 RMSE 和峰值力矩都更高，其旧 scenario 标记为 7/30，三个对照为 0/30。但全部回合都未满足当前 0.2 mm 穿透门槛，模型身份和运行 provenance 也未完全确认，因此不能形成当前 proposed 优于/劣于 baseline 的正式结论。impedance/admittance 目前仍是独立开发诊断。

## 新实验固定的比较规则

1. 同一场景/物体质量/初始状态/名义参考/时钟/solver/夹持 gate；只替换控制器。impedance 使用力矩后端，应明确它是 controller-family 对照，并验证相同实际力矩限幅和 slew，不声称内部伺服完全相同。
2. 同一基础开发 split 上选参数；冻结后所有方法跑同一物理 fixture 列表。仅改变随机 seed 不算增加物理覆盖；学习方法另报训练 seed，不能将 30 个评估 seed 当作 30 次独立训练。
3. 主指标：全任务位置 RMSE、全任务最大绝对关节力矩、末端线速度峰值；逐回合峰值先算，再报均值/标准差/最坏值。另报接触/恢复阶段 RMSE、速度 P95 和未完成任务，避免低速停滞或过硬跟踪获虚假优势。
4. 每回合完整保留，先报告任务成功率和物理通过率，再看三维 Pareto 权衡。失败、提前终止或无有效接触不得静默删除；不同完成时长的 RMSE 明示统计时长。
5. 主物理门包括 penetration ≤0.2 mm、无上游误碰、真实有效接触、有限状态和硬力矩限幅。不得为了某种方法通过而放宽 gate；力/力矩异常大的通过回合另列诊断。
6. 保存 argv、完整配置、模型/源码/XML hashes、原始 trace 和采样周期；报告采样速度峰值与物理步峰值的差别。新矩阵正式跑之前冻结协议，开发 smoke 不作为 test。
