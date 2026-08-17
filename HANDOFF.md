# SII Compliance / Direct ESN 项目交接文档

最后更新：2026-08-17  
用途：供后续 Codex/agent 接手固定 WBC + Direct ESN 柔顺控制实验。  
当前结论：multi-fixture deterministic reference 已经可以工作；随机 reservoir 的 robustness 仍未解决，不能直接把随机 checkpoint 当成论文 proposed model。

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

### Deterministic multi-fixture reference（目前唯一通过完整 selection gate 的模型）

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

No-rod：task success、hard torque false、mean yielding twist 约 `0.00173 m/s`。

这是当前最值得继续使用的研究 reference，但还不是最终 paper checkpoint；recovery jerk 仍比 Fixed WBC 高，随机 reservoir robustness 也未解决。

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

---

## 7. 下一位 agent 的优先级

### 优先级 1：补强 fixture 2/3 的 teacher coverage

当前随机 reservoir 和 deterministic reference 的差异集中在强碰撞 fixture 2/3。下一步应：

1. 对 fixture 2/3 增加多个 impact timing、stroke、height 和 rod speed 的 expert traces。
2. 仍保持 fixture 3 的真正 held-out timing/geometry，不要把验证 fixture 的 exact trace 混回训练。
3. 对每个 candidate 同时优化 post-contact RMSE、IAE、actual-release rejoin 和 recovery jerk。
4. 在 bootstrap 阶段直接 reject：no-rod yield 超限、无 stable rejoin、RMSE 恶化超过容许预算的 reservoir。

### 优先级 2：建立真正的随机化训练分布

当前 fixture 模型基本确定性；只改变 rollout `seed` 不会得到独立 ESN。需要至少改变：

- reservoir initialization seed；
- rod start time / stroke / height / velocity；
- contact time constant 或物理质量/摩擦的有限范围；
- 最好记录每个随机化配置，避免“seed”名义上变化但物理轨迹完全相同。

### 优先级 3：定义正式 selection gate

建议 gate：

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

### 优先级 4：正式多 seed 统计

只有在每个 reservoir 都通过 bootstrap-stage gate 后，才做多 seed aggregate。当前 deterministic reference 和随机 reservoir repair 的结果必须分开报告。

---

## 8. 推荐运行命令

### 用稳定 reference 生成 expert traces

```bash
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts

REF=/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_formal_multifixture_dagger_20260817/seed_20260907/direct_esn_dagger_iteration_03.npz

python run_direct_esn_mujoco.py --controller "$REF" \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 0 --output-summary /tmp/ref_f0.json --output-trace /tmp/ref_f0.npz

python run_direct_esn_mujoco.py --controller "$REF" \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 0 --no-rod --output-summary /tmp/ref_no_rod.json --output-trace /tmp/ref_no_rod.npz
```

### Stable-reference bootstrap

```bash
python bootstrap_direct_esn_multifixture.py \
  --expert-traces ref_f0.npz ref_f1.npz ref_f2.npz \
  --no-rod-expert-trace ref_no_rod.npz \
  --output-model bootstrap_seed_71.npz \
  --output-summary bootstrap_seed_71.json \
  --reservoir-seed 71 \
  --washout-steps 3 --rod-repeat 4 --neutral-repeat 4
```

### Multi-fixture DAgger

```bash
python run_direct_esn_dagger.py \
  --initial-model bootstrap_seed_71.npz \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --base-rod-trace /home/arm1/vmc_mujoco_runtime/rod_teacher_trace_v3.npz \
  --base-no-rod-trace /home/arm1/vmc_mujoco_runtime/no_rod_fixed_wbc_teacher_v2.npz \
  --output-dir formal_run_seed_71 \
  --iterations 3 \
  --fixture-indices 0,1,2 \
  --teacher-mode counterfactual \
  --counterfactual-horizon-steps 24 \
  --counterfactual-zero-repeat 1 \
  --counterfactual-nonzero-repeat 8 \
  --counterfactual-label-dilation-steps 0 \
  --prior-readout-weight 100
```

### Strict matched evaluation

```bash
python evaluate_direct_esn_post_contact.py \
  --controller formal_run_seed_71/direct_esn_dagger_iteration_03.npz \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 3 \
  --output-dir formal_run_seed_71/eval_fixture_3
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

**当前最可靠主线是：稳定 reference 行为蒸馏 → multi-fixture counterfactual/proximal DAgger → fixture 2/3 强碰撞 teacher coverage → 随机 reservoir selection；不要回到单一 phase teacher，也不要把 VMC 混入 Direct ESN proposed 线。**
