# WBC-aware ESN：训练前数据与接口协议（v0）

## 这一阶段解决什么问题

在 ESN 真正开始学习以前，必须先锁定两个边界：

1. **数据边界**：ESN 的 readout、reservoir 超参数和 safety 选择只能使用独立的 WBC-aware train/validation fixture pool；已经冻结的 V2/V3/V4 不能用于这些选择。
2. **信息边界**：部署时 ESN 只知道机械臂自身状态与 WBC 的当前任务速度；它不知道“棍子是否碰到”“力有多大”“从哪里撞来”“何时撤走”。

这避免了 ESN 在仿真中偷偷使用传感器外的答案，也避免测试集被当作调参集。

## 数据划分

`scripts/screen_esn_wbc_train_validation.py` 用固定的 `vmc_gated` selector 对候选物理场景进行有效碰撞筛选；`scripts/assemble_esn_wbc_fixture_pool.py` 只会在 reference source、selector 和 gate 全部一致时合并筛选轮次。实际通过集在 [esn_wbc_train_validation_fixture_pool.json](esn_wbc_train_validation_fixture_pool.json)，原始筛选轮次保留在同一目录，便于审计。

| split | 新 rod start 时刻（s） | 用途 |
|---|---:|---|
| train | 11 个有效 fixture | 生成 teacher/offline labels，拟合 ESN readout |
| validation | 11 个有效 fixture | 选择 reservoir、ridge、teacher 目标和安全 envelope |
| test | 空 | 不在这个脚本中创建；最终只使用冻结的 WBC-aware V4 ladder |

首轮候选时刻为 train `0.930, 1.180 s`、validation `0.955, 1.205 s`；其中两个 `+x` 晚期 fixture 未形成有效碰撞而被 gate 剔除。随后只针对这个缺口追加了新的、未出现在历史 V2/V3/V4/PPO 记录中的 `+x` 早期时刻（train `0.900, 0.915 s`，validation `0.920, 0.945 s`），四个均通过。最终每个 split 都包含五个 rod approach 方向：`-x` 2、`+x` 3、`-y` 2、`+y` 2、`-z` 2。

所有候选时刻都不与记录在案的 V2/V3/V4、V4 pilot/holdout 或既有 PPO fixture timing 重合。它们复用已物理验证的五种 rod approach geometry（`-x,+x,-y,+y,-z`），但和既有 fixture 不是同一个“geometry + timing”的实例。`+z` 仍未满足稳定 rejoin gate，因此不被声称为 sign-complete 方向覆盖。

每个候选都要满足相同的有效碰撞/任务 gate：有限数值、rod–hand contact、峰力至少 15 N、冲量至少 0.45 N·s、稳定 5 mm/80 ms rejoin、抓起和持有物块、无 hard torque limit，且配对 no-rod run 也完成任务。筛选 controller 只决定该物理 fixture 能否使用，不能当 ESN teacher，也不能作为方法排名依据。

推荐服务器命令（生成结果必须先审查再纳入 Git）：

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark
MUJOCO_GL=egl /home/arm1/vmc_mujoco_runtime/.venv/bin/python scripts/screen_esn_wbc_train_validation.py \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir /tmp/esn_wbc_screen \
  --output-manifest /tmp/esn_wbc_train_validation_manifest.json
```

## ESN student 的部署输入

每个 ESN update（建议 25 Hz）输入恰为 20 维：

\[
o_t^{stu}=[q_t\;(7),\;\dot q_t\;(7),\;\dot x_t^{WBC}\;(6)].
\]

ESN reservoir 还保留自己的上一时刻 **已截断** 7 维 action，作为内部 feedback。它不是环境真值，也不是接触标签。输入由 `scripts/esn_compliance.py` 中的 `ESNObservation` 和 `encode_student_observation` 明确定义。

下列量一律不允许成为 student 输入：rod/contact flag、rod force、rod state、obstacle 的 pose/velocity/geometry、collision normal、future release time、fixture ID。它们可以只在离线 teacher 或评估诊断中使用，并且记录为 privileged-only。

## 行为与安全边界

ESN 绝不直接输出 7 个电机力矩。它输出 7 个无量纲 residual：

\[
a_t=[\Delta \log \kappa_x,\ldots,\Delta \log \kappa_{yaw},\Delta \log d_{recovery}].
\]

动作先截断至 `[-1,1]`，再经过：正值 stiffness/drive envelope、log-space action-rate limit、已有 torque feasibility scaling 和 torque slew limiter。若配置为 `vmc_energy`，冻结的 energy-budget safety shield 仍然在这一层之后工作。也就是说，ESN 调节的是“六个虚拟弹簧 + 回归 drive”，而不是替代 WBC、接触模型或底层 torque safety。

## 审计与正式训练的门槛

在运行训练前必须确认：

- 服务器筛选实际获得非空 train 和 validation split，且各方向/冲量分布没有退化；
- 生成的 manifest 里 `reference_source` 是 `fixed_panda_wbc`；
- ESN trace 同时记录 raw action、bounded action、projected kappa/drive 和 downstream safety projection；
- readout/hyperparameter 只依赖该 manifest 的 train/validation；
- V4 WBC-aware ladder 不被读取，直到全部选择冻结后进行一次最终比较。

这个阶段已经完成物理 fixture 筛选，但**尚未训练 ESN**；22 个通过 fixture 只能证明训练/验证输入场景有效，不能证明 ESN 或任何学习方法优于 VMC-gated、impedance 或 rigid baseline。
