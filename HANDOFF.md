# SII Compliance / Direct ESN 项目交接文档

- 最后更新：2026-08-17（v3，OOD 泛化扫描后更新）
- 用途：供后续 Codex/agent 接手固定 WBC + Direct ESN 柔顺控制实验。
- 当前结论：**随机 reservoir robustness 已解决——正式配方是 stable-reference coverage BC（19+1 expert traces），8/8 reservoir seeds 通过完整 selection gate，held-out fx3 ΔRMSE = −2.207±0.034 mm（deterministic reference 为 −2.397 mm）**。泛化边界已测绘：几何 OOD（未见 timing/height，可行域内）8/8 seeds 全过、ΔRMSE −1.7~−3.0 mm；强度 OOD（stroke > 0.176）为任务物理不可行区（Fixed WBC 也 fail），无 task-level 外推。随机 pool counterfactual DAgger 是净负贡献（8/8 seeds held-out 恶化至 +1.146±0.390 mm），已记录为失败方向 F。v1 的「seed 251 DAgger iter2 通过 gate」是 held-out 扫描选择偏差，已降级为探索性参考。

---

## 1. 项目边界与主线

本项目的主线是 Franka/Panda 机械臂末端 6D 空间柔顺控制。当前实验只针对 end-effector 的六维任务空间，不把 VMC 和 ESN 混成一个算法：

```text
Fixed WBC nominal trajectory / nominal twist
                ↓
        Direct ESN collision-response policy
                ↓
 [WBC slowdown, 6D yielding Cartesian twist]
                ↓
 velocity / acceleration / torque / slew safety adapter
                ↓
             Panda MuJoCo
```

### WBC 的角色

- 只提供 nominal grasp trajectory、nominal end-effector twist 和 measured WBC tracking error。
- WBC 是固定 nominal controller，不观察 rod force、contact normal、obstacle pose 或 future release time。
- 被撞之后，ESN 才是主要柔顺响应策略；WBC 负责 nominal tracking 和偏离后的回归基础。

### ESN 的角色

Direct ESN 输出 7 维 action：

```text
[wbc_slowdown, yield_vx, yield_vy, yield_vz, yield_wx, yield_wy, yield_wz]
```

在线输入固定为 32 维：

```text
q(7), qdot(7), nominal WBC twist(6), WBC pose error(6), WBC twist error(6)
```

禁止进入 online observation 的 privileged fields：

```text
contact_force
contact_normal
contact_duration
signed_distance
obstacle_pose
obstacle_velocity
impactor_type
release_time
```

接触力、接触法向、杆运动、MuJoCo snapshot 等只能用于 offline teacher、counterfactual rollout 或 evaluation trace，不能进入部署 ESN。

### VMC 的边界

VMC 是独立 baseline 线。Direct ESN proposed 线中：

- `ppo_used_in_proposed = false`
- `vmc_used_in_proposed = false`
- 不要把当前方法命名为 ESN+VMC。

---

## 2. 仓库、服务器与运行环境

### 本地

父仓库：

```text
/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709
```

MuJoCo 子项目：

```text
/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark
```

远程仓库：

```text
https://github.com/hwy0507/SII_compliance
```

当前分支：`main`。本次 handoff 写入前的最新相关 commit：

```text
77ddf31  Document repaired Direct ESN reservoir training
9fdc592  Bootstrap reservoir ESNs from stable multi-fixture teacher
9be13e6  Record Direct ESN reservoir training selection failures
ebed73e  Bootstrap Direct ESN training across reservoir seeds
dcd902e  Document multi-fixture Direct ESN training entry
c057378  Aggregate Direct ESN DAgger labels across fixtures
c0cfe81  Add deployable Direct ESN rejoin fade
1c922ac  Constrain Direct ESN DAgger readout updates to parent
bd8f94a  Restrict counterfactual label ramp to pre-contact states
800bc62  Densify counterfactual Direct ESN teacher labels
60c088d  Record exact post-contact benchmark comparison
c39030d  Record exact contact impulse for post-contact benchmark
d675200  Add matched post-contact Direct ESN benchmark
```

本次（2026-08-17 fixture coverage 会话）新增的代码能力：

- `run_direct_esn_mujoco.py`：`--rod-stroke-m / --rod-height-m / --rod-start-time-s / --grasp-time-s`
  fixture override，用于生成参数化 expert traces；summary 写入 `override_fixture`。
- `run_direct_esn_dagger.py`：`--dagger-fixtures "stroke,height,start;..."` 自定义随机化 rod pool，
  `--fixture-indices` 索引该 pool；summary 写入 `dagger_fixture_pool`，每个 archive 记录
  `rollout_fixture`（避免"seed 变了但物理轨迹相同"的假随机化）。
- `evaluate_direct_esn_post_contact.py`：同款 `--rod-stroke-m / --rod-height-m /
  --rod-start-time-s / --grasp-time-s` override，用于 OOD benchmark（结果 JSON 记录
  `override_fixture`），保证 OOD 指标与正式评估同定义。

### 服务器

账号/地址：

```text
arm1@192.168.31.70
```

不要把密码写入代码、日志、README、handoff 或 Git commit。

服务器项目路径：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark
```

服务器 MuJoCo menagerie：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_menagerie
```

服务器 Python runtime：

```bash
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
```

服务器有 MuJoCo 3.x；本地环境没有可直接 import 的 `mujoco`，本地主要跑 `py_compile`、静态 contract tests 和纯 NumPy 单元测试。服务器虚拟环境当前没有安装 `pytest`，完整 MuJoCo smoke 必须直接运行脚本。

---

## 3. 关键代码文件

主控制器：

```text
code/mujoco_6d_vmc_benchmark/scripts/direct_esn_compliance.py
```

主要内容：

- `DirectESNConfig`
- `DirectESNController`
- fixed random leaky ESN reservoir + ridge readout
- 32D deployable input contract
- 7D direct compliance action
- optional `error_aligned_yield`（默认关闭，失败实验分支）
- optional `rejoin_fade_enabled`（默认关闭，尚未证明有效）
- proximal readout fitting：`fit_readout(..., prior_readout=..., prior_weight=...)`

MuJoCo 环境：

```text
code/mujoco_6d_vmc_benchmark/scripts/wbc_velocity_residual_env.py
```

关键约束：

- `observation_mode="direct_esn"` 会 bypass 旧 PPO authority gate、phase projection、predictive WBC modulation 和 energy tank。
- safety adapter 仍限制 joint velocity、acceleration、torque、torque slew。
- `last_action_contact_force`、`last_action_contact_penetration`、`dagger_contact_duration_s` 只用于 offline teacher-side diagnostics。

counterfactual teacher：

```text
code/mujoco_6d_vmc_benchmark/scripts/counterfactual_direct_esn_teacher.py
```

实现方式：

1. 使用 `mujoco.mj_copyData` 保存当前状态的 clone。
2. 在 cloned `MjData` 上比较 zero / slowdown / outward-yield candidates。
3. cost 包含 contact force、impulse、terminal WBC error、torque、action change、secondary contact。
4. teacher 可使用 privileged truth，但只返回 offline label。

DAgger：

```text
code/mujoco_6d_vmc_benchmark/scripts/run_direct_esn_dagger.py
```

支持：

- `--teacher-mode phase|counterfactual`
- `--fixture-indices 0,1,2`
- `--dagger-fixtures "0.176,0.541,1.085;0.176,0.5395,1.062;..."`（自定义随机化 rod pool，替代 default pool）
- `--counterfactual-horizon-steps`
- `--counterfactual-zero-repeat`
- `--counterfactual-nonzero-repeat`
- `--counterfactual-label-dilation-steps`（默认 0；对称 dilation 是失败实验）
- `--prior-readout-weight`（proximal readout update）
- student-visited archive
- multi-fixture aggregate fitting

bootstrap：

```text
code/mujoco_6d_vmc_benchmark/scripts/bootstrap_direct_esn_multifixture.py
```

支持两种来源：

- legacy single phase teacher（不推荐用于随机 reservoir）；
- `--expert-traces ... --no-rod-expert-trace ...`：从稳定 deterministic reference 的 40 ms `bounded_action` trace 做 behavior cloning，当前推荐路径。

matched benchmark：

```text
code/mujoco_6d_vmc_benchmark/scripts/evaluate_direct_esn_post_contact.py
```

报告：

- contact onset / actual release
- scheduled rod release
- exact contact impulse（使用 `contact_impulse_delta_ns`）
- peak deviation
- post-contact RMSE
- post-contact IAE
- actual-release rejoin latency
- scheduled-release rejoin latency
- torque / jerk / recovery jerk

---

## 4. 测试与基本验证

本地最近一次相关测试：

```text
14 passed
```

推荐本地命令：

```bash
cd /Users/hwy/Desktop/个人/科研/SII科研/compliance/0709/code/mujoco_6d_vmc_benchmark
python3 -m py_compile scripts/direct_esn_compliance.py scripts/run_direct_esn_dagger.py scripts/bootstrap_direct_esn_multifixture.py
pytest -q tests/test_direct_esn_compliance.py \
  tests/test_direct_esn_dagger_contract.py \
  tests/test_direct_esn_env_contract.py \
  tests/test_direct_esn_post_contact_contract.py \
  tests/test_direct_esn_bootstrap_contract.py
```

服务器基础 smoke：

```bash
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts
python -m py_compile direct_esn_compliance.py run_direct_esn_dagger.py \
  bootstrap_direct_esn_multifixture.py evaluate_direct_esn_post_contact.py
```

---

## 5. 当前推荐 checkpoint

### Deterministic multi-fixture reference（通过完整 selection gate）

服务器路径：

```text
/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_formal_multifixture_dagger_20260817/seed_20260907/direct_esn_dagger_iteration_03.npz
```

训练池：fixture `0,1,2`。held-out：fixture `3`。配置：

- 3 轮 multi-fixture DAgger
- counterfactual horizon 24 physics steps / 96 ms
- `prior_readout_weight=100`
- `counterfactual_label_dilation_steps=0`
- no-rod archive 保持 neutral

结果：

| Fixture | Split | Fixed WBC RMSE | Direct ESN RMSE | Δ RMSE | Fixed→ESN rejoin |
|---:|---|---:|---:|---:|---:|
| 0 | train | 8.816 mm | **7.775 mm** | **−1.041 mm** | 880 → **800 ms** |
| 1 | train | 11.893 mm | **9.243 mm** | **−2.650 mm** | 960 → **600 ms** |
| 2 | train | 15.537 mm | **12.031 mm** | **−3.506 mm** | 960 → **480 ms** |
| 3 | held-out | 17.901 mm | **15.504 mm** | **−2.397 mm** | 1000 → **640 ms** |

No-rod：task success、hard torque false、mean yielding twist 约 `0.00173 m/s`（复测 `0.00043 m/s`）。

特点：train fixture RMSE / rejoin latency 全面最优；recovery jerk 偏高（fx2 136、fx3 119 m/s³）。

### 随机 reservoir 正式候选（2026-08-17 coverage 会话，8/8 通过完整 gate）

服务器路径（8 个独立 reservoir，全部通过 gate）：

```text
/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817/bootstrap/bootstrap_seed_{13,42,71,137,251,307,512,1009}.npz
```

完整报告：同目录 `EXPERIMENT_REPORT.md`；统计 `multiseed_statistics.json`。

训练方式（stable-reference coverage BC，仅此一步、无 DAgger）：

1. 用 deterministic reference 在 fixture 2 邻域生成 19 条参数化 expert traces
   （stroke {0.170–0.176} × start {1.062–1.108} × height {0.5395–0.5425}，全部 task success，
   无 fixture 3 exact 组合）+ 1 条 no-rod trace；
2. behavior cloning bootstrap（`washout 3 / rod-repeat 4 / neutral-repeat 4`，
   readout MSE ≈ 1.3e-5）。

8-seed 统一协议统计（iteration 不适用；fx3 只报告；Fixed WBC → ESN）：

| 指标 | fx0 (train) | fx1 (train) | fx2 (train) | fx3 (held-out) |
|---|---:|---:|---:|---:|
| Δ post-contact RMSE | −0.982±0.011 | −2.600±0.011 | −3.313±0.015 | **−2.207±0.034** |
| rejoin latency | 0.80±0.00 s | 0.64±0.00 s | 0.52±0.00 s | 0.68±0.00 s |
| recovery jerk | 10±1 | 64±5 | 133±4 | 127±3 |

No-rod：8/8 task success、无 hard torque、mean yielding twist 0.001057±0.000064 m/s。

特点：与 deterministic reference 水平相当（fx3 −2.207 vs −2.397），但给出跨 reservoir 的
统计稳健性；这是论文随机化 proposed 线的正式方法。**不要对这批模型再跑随机 pool DAgger**
（见失败方向 F）。

探索性参考（不进入正式结果）：seed 251 DAgger iteration 02 曾在 fx3 达到 −3.214 mm、
recovery jerk 75/85，但该 checkpoint 是对 9 个 (seed,iteration) 组合做 held-out 扫描后挑出
的最优，属测试集选择偏差；统一协议（train-only iteration 选择）下所有 DAgger 产物均
不达标。路径 `dagger_seed_251/direct_esn_dagger_iteration_02.npz` 仅作分析用。

### Repair 后随机 reservoir 输出（不选为最终模型）

服务器目录：

```text
/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_reservoir_repair_20260817/
```

seed：`71, 137, 251`。

修复后的 no-rod mean yield 已降到 `0.00080–0.00183 m/s`，但 RMSE 在强碰撞 fixture 2/3 仍有回退：

| Reservoir | Fixture 0 | Fixture 1 | Fixture 2 | Held-out fixture 3 | 判定 |
|---:|---:|---:|---:|---:|---|
| 71 | +0.132 mm | +1.463 mm | +6.369 mm | +3.173 mm | reject |
| 137 | −0.477 mm | −0.106 mm | +2.252 mm | +6.971 mm | reject |
| 251 | −0.242 mm | +0.147 mm | +4.717 mm | +4.822 mm | reject |

不要从该目录直接选模型作为 proposed。

---

## 6. 已验证但失败的方向（不要直接复用）

### A. 旧单 fixture phase-template DAgger

问题：no-rod 自激或 rod response 过度保守。counterfactual teacher 已替代它。

### B. 对称 counterfactual label dilation

问题：把 nonzero residual 扩展到碰撞后状态，会造成持续 residual；出现 task failure、峰值偏离超过 150 mm、无法 stable rejoin。

代码仍保留 `--counterfactual-label-dilation-steps`，但默认值已经恢复为 0。不要直接打开对称 dilation。

### C. error-aligned / canonicalized yield

问题：短期动作方向看似合理，但与原 world-frame teacher 参数化不一致；最终出现约 56.9 mm 峰值偏离和约 985 ms 回归。`error_aligned_yield` 默认关闭，只能作为 opt-in ablation。

### D. rejoin fade

问题：当前 checkpoint 上多种 fade 强度没有改变 benchmark 结果，说明现有误差导数相位判断尚未对 recovery jerk 产生有效作用。默认关闭，不要把它当作已验证改进。

### E. 直接从单一 phase teacher 初始化随机 reservoir

问题：no-rod mean yield 可升到 `0.04–0.10 m/s`，部分 fixture 无稳定 rejoin。必须先做 stable-reference behavior cloning。

### F. 随机 pool counterfactual DAgger（2026-08-17 coverage 会话确认为净负贡献）

设置：coverage BC bootstrap 之后，在 8-fixture 随机化 rod pool（5/8 为 stroke ≥0.174 强碰撞）
上跑 counterfactual DAgger（h24 / nonzero-repeat 8 / dilation 0 / prior 100）。

结果：8/8 reservoir seeds 的 DAgger iter1 在 held-out fx3 恶化（mean +1.146±0.390 mm；
BC-only 对照为 −2.207±0.034 mm）；train fixtures 上亦随 iteration 单调劣化，
train-only 协议下全部 8 个 seed 的 iteration 选择都落在 iter1 且仍不达标。

机理推测：pool 强碰撞占比高 + nonzero 标签 repeat=8 加权，把 readout 拉向过强 yield，
破坏 BC 学到的与 teacher 参数化一致的低误差行为；proximal prior 100 不足以约束。

若要复活 DAgger（未验证）：标签权重按碰撞强度归一；pool 强度分布匹配 default fixtures；
仅对 student 明显偏离 teacher 的状态打标。在验证前，**不要对 coverage BC 产物再跑随机 pool
DAgger**。

---

## 7. 下一位 agent 的优先级

2026-08-17 v2 更新：随机化 proposed 方法已确定为 coverage BC（8/8 seeds 过 gate，统计见
第 5 节）；随机 pool DAgger 记为失败方向 F。剩余工作按新优先级排列。

### 优先级 1：完善论文主实验（2026-08-17 v4 已完成核心部分）

已产出（`paper_tables/`，服务器与本地 docs 同步）：

1. Table 1 matched benchmark 全指标（Fixed WBC vs BC 8-seed vs reference）；
   Table 2 no-rod neutrality；Table 3 geometry OOD；Table 4 strength OOD 边界；
2. `paper_main_statistics.csv`（机器可读 mean/std）；`paper_main_figure.png`
   （RMSE / rejoin / OOD ΔRMSE 三面板，含 per-seed scatter）；
3. 要点：BC 8-seed 全面优于 Fixed WBC（held-out fx3 RMSE 17.901→15.694±0.034 mm、
   rejoin 1.00→0.68 s）；impulse/peak force/peak torque 与 Fixed WBC 一致（接触瞬时由
   rod 运动学主导）；唯一劣势指标仍是 recovery jerk（126.8±2.9 vs 15.0 m/s³ @fx3）。

剩余（可选）：LaTeX 版主表；VMC / 旧 ESN baseline 若要进主表需在 matched protocol 下
另行评估（当前 evaluate 脚本只内建 fixed_wbc 对照）。

### 优先级 2：扩展泛化评估（2026-08-17 v3 已完成核心部分）

已测（结果见 `EXPERIMENT_REPORT.md` v3 节与 `ood_*/` 数据）：

1. **几何 OOD（阳性）**：可行域内未见 timing（1.130/1.150）/height（0.545）/角点，
   8/8 BC seeds 全部 task success，ΔRMSE −1.7~−3.0 mm，rejoin 0.56–0.68 s（FW 0.96–1.00 s），
   与 in-distribution 无衰减——可直接作论文泛化主张。
2. **强度 OOD（边界清晰）**：stroke 0.178–0.190 为任务物理不可行区（Fixed WBC 也全部
   task fail）；BC seeds 退化分层（bc_71 全程优于 FW；bc_13/307 与 reference 剧烈退化）。
   报告为 generalization boundary，不声称强度外推。

仍可扩展（可选）：其他 impactor 类型 / approach side（`impactor_type`、
`rod_approach_side` 字段已存在）；contact time constant / 摩擦的物理扰动。

### 优先级 3：recovery jerk 压低（未解决）

BC-only 的 fx2/3 recovery jerk（133/127）与 reference（136/119）相当，仍高于 Fixed WBC
（2/15）。可选方向：yield 幅度 rate limit、jerk 显式进 counterfactual cost 的离线标签精修
（不是 DAgger）、rejoin 相位 readout 正则。rejoin fade 仍无效，不要重复。

### 已完成（供参考，不要再做）

- fixture 2/3 coverage expert traces（19+1 条）与参数化基础设施；
- 随机化训练分布（运动学部分）+ 8-reservoir seed 统计；
- selection gate 的实际执行（must 项 + 优先项 + reject 记录），gate 定义：

```text
必须：task success
必须：effective collision
必须：no hard torque limit
必须：no-rod task success
必须：no-rod mean yielding twist < 0.005 m/s
必须：held-out stable rejoin
优先：post-contact RMSE 不高于 Fixed WBC
优先：IAE / rejoin latency 不高于 Fixed WBC
约束：contact impulse 不得恶化超过预设预算
约束：recovery jerk 不得超过绝对安全上限
```

不要仅凭 mean yielding twist、task success 或 contact impulse 单项指标选模型。

---

## 8. 推荐运行命令

### 用稳定 reference 生成参数化 expert traces

```bash
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts

REF=/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_formal_multifixture_dagger_20260817/seed_20260907/direct_esn_dagger_iteration_03.npz

# default fixture trace
python run_direct_esn_mujoco.py --controller "$REF" \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 0 --output-summary /tmp/ref_f0.json --output-trace /tmp/ref_f0.npz

# 参数化 override trace（fixture 2 邻域强碰撞覆盖；reference 稳定边界为 stroke ≤ 0.176）
python run_direct_esn_mujoco.py --controller "$REF" \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 2 --rod-stroke-m 0.176 --rod-start-time-s 1.062 \
  --output-summary /tmp/g10.json --output-trace /tmp/g10.npz

python run_direct_esn_mujoco.py --controller "$REF" \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 0 --no-rod --output-summary /tmp/ref_no_rod.json --output-trace /tmp/ref_no_rod.npz
```

本次 coverage 会话的完整 trace 网格与 manifest 见
`/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817/expert_traces/`。

### Stable-reference bootstrap（多 expert trace behavior cloning）

```bash
python bootstrap_direct_esn_multifixture.py \
  --expert-traces ref_f0.npz ref_f1.npz ref_f2.npz g01.npz ... g16.npz \
  --no-rod-expert-trace ref_no_rod.npz \
  --output-model bootstrap_seed_251.npz \
  --output-summary bootstrap_seed_251.json \
  --reservoir-seed 251 \
  --washout-steps 3 --rod-repeat 4 --neutral-repeat 4
```

### 随机化 pool DAgger（失败方向 F，只用于复现负结果，不要用于出新模型）

```bash
POOL="0.160,0.539,1.055;0.165,0.540,1.070;0.170,0.541,1.085;0.176,0.541,1.085;0.176,0.5395,1.062;0.176,0.5425,1.108;0.174,0.541,1.096;0.172,0.5435,1.070"

python run_direct_esn_dagger.py \
  --initial-model bootstrap_seed_251.npz \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --base-rod-trace /home/arm1/vmc_mujoco_runtime/rod_teacher_trace_v3.npz \
  --base-no-rod-trace /home/arm1/vmc_mujoco_runtime/no_rod_fixed_wbc_teacher_v2.npz \
  --output-dir dagger_seed_251 \
  --iterations 3 \
  --fixture-indices 0,1,2,3,4,5,6,7 \
  --dagger-fixtures "$POOL" \
  --teacher-mode counterfactual \
  --counterfactual-horizon-steps 24 \
  --counterfactual-zero-repeat 1 \
  --counterfactual-nonzero-repeat 8 \
  --counterfactual-label-dilation-steps 0 \
  --prior-readout-weight 100
```

8/8 seeds 在此设置下 held-out 恶化（失败方向 F）。正式模型 = bootstrap 产物本身，到此为止。

### Strict matched evaluation

```bash
python evaluate_direct_esn_post_contact.py \
  --controller bootstrap/bootstrap_seed_251.npz \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 3 \
  --output-dir eval_bc_seed_251_fixture_3
```

---

## 9. Git 与文件安全规则

父仓库当前有大量与 compliance 以外项目相关的用户脏改动。后续 agent 必须：

- 只 `git add` 本次确实修改的 Direct ESN 文件和报告；
- 禁止 `git add .`；
- 禁止 `git reset --hard`、`git checkout --`、批量删除或清理其他项目文件；
- 不要提交大模型、`.venv`、大量 MuJoCo outputs；输出保留在服务器并在报告中记录绝对路径；
- 每次重要代码/结果修改都要 commit + `git push origin main`；
- 提交前运行 `git diff --check` 和相关测试；
- 任何失败候选必须记录为 reject，不要覆盖当前 reference checkpoint。

---

## 10. 当前交接一句话

**正式配方 = 稳定 reference 的 fixture 2 邻域 coverage 蒸馏（19+1 expert traces → BC），8/8 随机 reservoir 通过完整 selection gate（held-out −2.207±0.034 mm）；到此为止，不要再叠随机 pool DAgger（失败方向 F）。下一步是论文主实验图表与泛化扩展（OOD 强度 / impactor 变体），以及 recovery jerk 压低。不要回到单一 phase teacher，也不要把 VMC 混入 Direct ESN proposed 线。**
