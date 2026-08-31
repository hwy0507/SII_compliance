# Compliance Control for Dynamic Obstacle Recovery

## FR3 NUS-inspired tabletop benchmark (validated collision-free demo)

The branch also contains a fixed-base Franka FR3 tabletop benchmark under
`nus_fr3_mujoco/`. It implements the NUS-inspired nominal layer as a native
MuJoCo experiment: wrist RGB-D scene belief, task-stage-aware view selection,
candidate arm trajectories, short-horizon replanning, and Panda two-finger
grasp validation.

The latest server-side validation uses a collision-tested side-grasp pose,
an elevated approach corridor, a short pre-grasp settle segment, and a front
placement corridor. It achieved a two-finger grasp and successful placement
while the independently moved dynamic obstacle made zero contact. The full
offline swept-volume audit also reports no static-clutter penetration:

| Metric | Latest result |
| --- | ---: |
| Grasp / placement | `True / True` |
| Placement error | 0.00756 m |
| Dynamic-obstacle contacts | 0 |
| Maximum dynamic-obstacle force | 0 N |
| Active-view accepted / rejected | `7 / 0` |
| Horizon replanning / plan switches | `93 / 1` |
| Static swept-volume collisions | 0 |
| Static near-collisions | 0 |
| Minimum swept-volume clearance | `0.000 m` |

The result is still a deterministic nominal-layer simulation proof-of-concept;
the RGB-D obstacle estimate uses the benchmark proxy and the grasp latch is a
simulation validation aid. Those limitations are documented below and should
not be presented as a real-robot guarantee.

### Latest server artifact

The large GIF and JSON remain on the experiment server, as requested:

```text
GIF:     /home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_perfect_recheck_20260901.gif
Metrics: /home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_perfect_recheck_20260901.json
```

Run the same validation on the server with:

```bash
cd /home/arm1/vmc_mujoco_runtime/nus_fr3_migration
export MUJOCO_GL=egl
export PYTHONPATH=/home/arm1/vmc_mujoco_runtime/nus_fr3_migration
/home/arm1/vmc_mujoco_runtime/.venv/bin/python -m nus_fr3_mujoco.tabletop_demo \
  --model scenes/fr3_office_v36_rgbd_proxy.xml \
  --output outputs/fr3_perfect_recheck_20260901.gif \
  --metrics outputs/fr3_perfect_recheck_20260901.json \
  --fps 10 --dynamic-obstacle
```

The selected route is `approach_center+place_left`. Its key Cartesian
waypoints are:

```text
approach:  target + [0.00, 0.18, 0.30]
pre-grasp: target + [0.00, 0.14, 0.04]
grasp:     target + [0.00, 0.105, 0.00]
```

The target is held at its desk-rest pose only until the closure window, which
prevents pre-contact simulation impulses from sliding the free object away.
Normal contact dynamics resume during closure and the latch validates both
finger contacts before lift.

本项目聚焦一个单独而明确的问题：

```text
高层 whole-body motion / scheduler 给出名义运动指令，
低层控制器在动态障碍物接触发生后实现柔顺让位、恢复与回轨。
```

当前仓库只保留**柔顺控制**主线，不再包含 `grasp overlap`、抓取 critic 或其他抓取学习分支。

## Project Scope

项目由两部分组成：

- `whole-body-motion-control`：上层系统主工程，负责移动抓取流程、scheduler、benchmark 与执行环境。
- `residual_compliance_fetch_server_20260706`：下层柔顺控制研究分支，负责接触后的 compliant recovery / return-to-track。

当前的工程判断是：

```text
方法开发基线：
  residual_compliance_fetch_server_20260706

最终系统集成宿主：
  whole-body-motion-control
```

也就是说，后续算法先在独立小环境里做扎实，再回接到主工程。

## Repository Layout

```text
0709/
  README.md
  code/
    whole-body-motion-control/
    residual_compliance_fetch_server_20260706/
  reports/
    compliance_control/
      future_work.md
```

## Components

### 1. `whole-body-motion-control`

路径：

```text
code/whole-body-motion-control
```

角色：

- Fetch 移动抓取主工程
- 高层 scheduler 与 benchmark
- ManiSkill / Gazebo / real robot 接口
- 动态障碍场景触发与任务级监测

建议优先阅读：

- `code/whole-body-motion-control/README.md`
- `code/whole-body-motion-control/experiments/run_maniskill_benchmark.py`
- `code/whole-body-motion-control/grasp_anywhere/benchmark/`
- `code/whole-body-motion-control/grasp_anywhere/envs/maniskill/`
- `code/whole-body-motion-control/grasp_anywhere/utils/monitor_core.py`

### 2. `residual_compliance_fetch_server_20260706`

路径：

```text
code/residual_compliance_fetch_server_20260706
```

角色：

- 柔顺控制方法开发基线
- ManiSkill / SAPIEN 中的接触后恢复控制
- baseline / analytic compliance / BC / PPO residual 对比平台

建议优先阅读：

- `code/residual_compliance_fetch_server_20260706/README.md`
- `code/residual_compliance_fetch_server_20260706/docs/progress.md`
- `code/residual_compliance_fetch_server_20260706/src/residual_compliance_fetch/controllers.py`
- `code/residual_compliance_fetch_server_20260706/src/residual_compliance_fetch/ppo_env.py`
- `code/residual_compliance_fetch_server_20260706/scripts/train_ppo_residual.py`

## Current Technical Route

当前采用的路线是：

```text
nominal tracking
  + analytic compliance prior
  + residual RL
  + contact history
  -> compliant recovery and return-to-track
```

关键点不是让 RL 从零输出完整控制，而是：

- 保留名义控制骨架；
- 把学习模块限制在接触后的残差修正；
- 重点解决“碰撞发生后怎么退、怎么稳、怎么回”。

## Integration Plan

后续接入方式建议保持简单清晰：

```text
whole-body-motion-control
  -> 生成 high-level target / nominal motion
  -> 调用 compliance module
  -> 输出 corrected arm command / residual command
  -> 回到主工程执行与评估
```

当前不建议直接在 `whole-body-motion-control` 里从零开发柔顺控制，原因是：

- 耦合大；
- 调 observation / reward / PPO 成本高；
- 容易把 scheduler、perception、planning 的影响和低层控制本身混在一起。

因此，推荐流程是：

1. 在 `residual_compliance_fetch_server_20260706` 中验证方法；
2. 固化 observation / action / reward / metrics；
3. 将成熟接口嵌回 `whole-body-motion-control`；
4. 用主工程 benchmark 和最终 demo 做验证。

## Current Priorities

当前最重要的工作有四项：

1. 把 benchmark 调难，让接触真正发生且恢复过程可测。
2. 把 `contact history` 正式纳入 policy，而不只看当前帧。
3. 保持接口可回接主工程，不做只能在小环境里工作的特例。
4. 提前考虑 sim2real 所需的碰撞几何、接触指标与控制平滑性。

## Next Week Checklist

- [ ] 梳理 `whole-body-motion-control -> compliance module` 的输入输出接口
- [ ] 明确主工程可提供的名义轨迹 / 关节命令格式
- [ ] 在 `residual_compliance_fetch_server_20260706` 中加入固定长度的 `contact history stack`
- [ ] 重新设计更难的 benchmark，提升真实接触比例
- [ ] 统一评估指标：`success_rate`、`collision_rate`、`contact_rate`、`max_penetration`、`final_arm_error`、`mean_jerk`
- [ ] 跑一轮带 `contact history` 的 PPO 短训实验
- [ ] 对比新旧 policy 在恢复质量和轨迹平滑性上的差异
- [ ] 形成一版回接 `whole-body-motion-control` 的接口草案

## Notes

- 本仓库当前是一个**柔顺控制交接包**，不是单体代码仓库。
- 上层系统与下层控制被刻意分开，目的是降低研究迭代成本。
- `reports/compliance_control/future_work.md` 保留了更简短的后续方向摘要。
