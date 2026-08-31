# Compliance Control for Dynamic Obstacle Recovery

## FR3 NUS-inspired tabletop benchmark (three-camera active-perception demo)

The branch also contains a fixed-base Franka FR3 tabletop benchmark under
`nus_fr3_mujoco/`. It implements the NUS-inspired nominal layer as a native
MuJoCo experiment: cooperative fixed-base, root-mounted active-base, and wrist RGB-D scene belief,
task-stage-aware view selection, candidate arm trajectories, short-horizon
replanning, and Panda two-finger grasp validation.

The latest server-side validation uses a collision-tested top-down rod grasp,
an elevated approach corridor, a short pre-grasp settle segment, and a front
placement corridor. The nominal task contains no unconditional `LIFT` segment:
it is `grasp -> carry -> place`. A vertical escape is synthesized only when
the fused RGB-D belief predicts that the current carry horizon is blocked.
The final server run completed the full pick/carry/place task with zero dynamic
obstacle contact:

| Metric | Latest result |
| --- | ---: |
| Grasp / placement | `True / True` |
| Placement error | 0.03658 m |
| Dynamic-obstacle contacts | 0 |
| Maximum dynamic-obstacle force | 0 N |
| Active-base view | fixed mount, changing pan/tilt |
| Horizon replanning / plan switches | `118 / 0` |
| Observation-driven safe holds | `1` |
| Illegal target-contact steps | `0` |
| Three-camera visible steps | `22` |
| Static swept-volume collisions | 0 |
| Static near-collisions | 0 |
| Minimum swept-volume clearance | `0.000 m` |

The result is still a deterministic nominal-layer simulation proof-of-concept;
the RGB-D obstacle estimate uses the benchmark proxy and the grasp latch is a
simulation validation aid. Those limitations are documented below and should
not be presented as a real-robot guarantee.

The current three-camera experiment assigns complementary roles: `base_rgbd`
is a fixed global-alert camera, `active_base_rgbd` is fixed near the FR3 root
with a narrow field of view and actively changes only its orientation for a
left/center/right scan or obstacle focus, and `wrist_rgbd` performs local
end-effector confirmation. The wrist camera now has an independent active
gaze controller: its mount remains attached to the hand, but the local camera
quaternion is recomputed from the current target/obstacle belief each frame;
it no longer stares permanently into the gripper. Their independent RGB-D trackers are fused before
the safety shield; a single anticipatory hold is allowed, and the wrist pose
is not reoriented during the grasp approach, so camera coordination cannot
reintroduce pre-grasp oscillation or a post-event upward fling.

The safety policy no longer contains a fixed `q_lift_ref` response. A visible
obstacle outside the current predicted swept corridor produces no arm action.
Only when the RGB-D-driven short-horizon checker reports that the future
trajectory is blocked may the controller synthesize a collision-gated vertical
escape from the measured current hand pose. In the final run, active-base
first detection was `11.44 s`, the conditional escape began at `12.20 s`, and
the obstacle contact audit remained exactly zero. This keeps active avoidance
causally tied to an actual predicted collision risk and removes the previous
post-event upward pull.

The dynamic-obstacle benchmark timing is separated from the nominal task:
the red box starts outside the RGB-D workspace gate, enters the carry strip
before the carry midpoint, and exits before placement descent. Therefore the
only upward motion visible in the final run is the explicitly labeled
`ACTIVE OBSTACLE LIFT` response.

Placement also has an explicit `SETTLE AT PLACE` stage. The arm now reaches
the refined hand pose, holds it briefly, and only then opens the gripper. This
prevents a GIF frame from showing the rod still suspended near the hand being
mistaken for the final placement result.

The latest server GIF is a 589-frame three-camera layout. The final run
reported `grasp_success=True`, `placement_success=True`, zero dynamic-obstacle
contact steps and zero force, 22 policy steps with all three cameras seeing
the obstacle, and one RGB-D-triggered escape. Placement uses a 0.10 m XY
compliance envelope and a tighter vertical check; the measured release error
was 0.03658 m.

### Latest server artifact

The large GIF and JSON remain on the experiment server, as requested:

```text
GIF:     /home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_rod_active_avoidance_zero_contact_20260831.gif
Metrics: /home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_rod_active_avoidance_zero_contact_20260831.json
```

Run the same validation on the server with:

```bash
cd /home/arm1/vmc_mujoco_runtime/nus_fr3_migration
export MUJOCO_GL=osmesa
export PYTHONPATH=/home/arm1/vmc_mujoco_runtime/nus_fr3_migration
/home/arm1/vmc_mujoco_runtime/.venv/bin/python -m nus_fr3_mujoco.tabletop_demo \
  --model nus_fr3_mujoco/fr3_office_v36_rgbd_proxy.xml \
  --output outputs/fr3_rod_active_avoidance_zero_contact_20260831.gif \
  --metrics outputs/fr3_rod_active_avoidance_zero_contact_20260831.json \
  --fps 6 --dynamic-obstacle --rod-task
```

### Long-rod cooperative-perception benchmark

The `--rod-task` mode changes the target into a horizontal 240 mm rod (24 mm
diameter) and uses a natural top-down pinch: the rod axis is world `+Y`, the
jaw-slide axis is world `X`, and the wrist approaches from above.  The rod is
held at its desk-rest pose through the complete closure window, then released
only after MuJoCo reports simultaneous left- and right-finger contact.  Once
latched, the free-body collision channel is disabled to prevent the broad hand
mesh from producing a false palm penetration; desk support is restored after
release.

Final server run (`fr3_rod_active_avoidance_zero_contact_20260831`):

```text
grasp_success                       True
placement_success                   True
placement_error_m                   0.03658 m
dynamic_obstacle_contact_steps      0
max_dynamic_obstacle_force_n        0.0 N
active_view_accept_count            0
active_view_reject_count            0
dynamic_safety_hold_count           1
replanning_count / plan_switches    118 / 0
illegal_target_contact_steps        0
triple_camera_visible_steps         22
swept_volume_collision_count        0
```

The red obstacle enters the RGB-D workspace before the carry midpoint and
traverses the carry strip leftward. The fused RGB-D state triggers one
anticipatory, collision-gated escape at `12.20 s`; the nominal phase changes
from `CARRY AROUND CLUTTER` to `ACTIVE OBSTACLE LIFT` and then returns to carry
at `13.16 s`. Active-base first detection is `11.44 s`, fused first detection
is `11.28 s`, and all three cameras overlap for `22` policy steps. The
rod-task camera mount is rotated diagonally so the top-down grasp pose does not
point the sensor straight into the desk.
`dynamic_obstacle_min_clearance_m=0.0` is a conservative tangent/degenerate-distance
report; the authoritative contact audit remains zero contacts and zero measured force.

The selected rod route is `approach_left+place_left`. Its key Cartesian
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

For the final visual demonstration, the red dynamic box starts outside the
RGB-D workspace gate at `x=1.20 m`, then follows one continuous leftward path
through `x=0.18 m` to `x=-0.78 m` at `y=-0.30 m`, `z=1.05 m`. The tracker
estimates its motion from the three RGB-D streams, and the safety shield
inserts one `0.60 s` `CONDITIONAL_OBSTACLE_LIFT` at `t=12.20 s` before the
nominal carry route resumes. The authoritative dynamic contact audit reports
zero contact steps and zero measured force.

The camera audit records the actual wrist-camera optical axis, not just the
scheduler label. With the rod-task diagonal wrist-camera mount, the wrist
stream detects the obstacle from `0.36 s` onward during the initial crossing
window, and the two cameras overlap for `24` policy steps. During the later
confirmed-obstacle window, the active focus remains `PREDICTED_OBSTACLE` and
the safety gate accepts all requested reorientations.
After confidence decays and the obstacle leaves the wrist view, the scheduler
falls back to `SWEPT_VOLUME_SEARCH`, which is expected rather than a collision
response.

This validation uses three cooperative RGB-D streams. The fixed `base_rgbd`
camera provides desk-wide early warning, `active_base_rgbd` is fixed near the
FR3 root and scans by changing only its quaternion, and `wrist_rgbd` confirms
the local hand/obstacle relationship. The fused tracker drives one
observation-based conditional lift, with zero rejected active-view actions and
zero dynamic-obstacle contacts. The GIF displays the overview, base RGB/depth,
active-base RGB/depth, and wrist RGB/depth panels together.

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
