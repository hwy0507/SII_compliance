# FR3 NUS tabletop benchmark — next handoff

日期：2026-08-30

## 当前代码状态

- Git 分支：`codex/fr3-nus-mujoco-progress`
- 最新提交：见仓库最新分支提交（最终无碰撞候选轨迹 + 抓取前目标固定）
- 远端仓库：<https://github.com/hwy0507/SII_compliance/tree/codex/fr3-nus-mujoco-progress>
- 服务器源码：`/home/arm1/vmc_mujoco_runtime/nus_fr3_migration/nus_fr3_mujoco/`
- 服务器实验输出：`/home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/`

## 已完成

- 保留经过验证的 Panda 侧向抓取姿态；
- 动态障碍物已从抓取阶段移到搬运阶段：`10.4 / 11.2 / 13.0 s`；
- PRE-GRASP、DESCEND、CLOSE、LIFT 阶段冻结候选切换，避免抓取过程中切换到旧轨迹；
- GIF/JSON/缓存均只保存在服务器，没有加入 Git；
- 本地目标 worktree 干净，远端分支已推送。

## 最近实验结论

- `fr3_carry_pose_test5.json`：曾实现抓取和放置成功，但动态障碍仍有接触，静态 keyboard swept-volume 仍有穿透；
- `fr3_carry_pose_test15.json`：尝试高位清键盘后，抓取失败，不能作为最终结果；
- `fr3_carry_pose_test16.json`：拆分高位预抓取和最终抓取后仍未解决目标倾倒；
- 因此下一次必须重新运行最新 commit，不能把 test15/test16 当作最终性能结果。

## 2026-09-01 基线复核

服务器运行 `fr3_final_recheck_20260901.json` 的结果：

```text
grasp_success                  True
placement_success              True
placement_error_m              0.05968 m
dynamic_obstacle_contact_steps 11
max_dynamic_obstacle_force_n   263.80 N
active_view_accept_count       7
active_view_reject_count       0
plan_switch_count              1
replanning_count               93
swept_volume collision_count   212
swept_volume min_clearance_m   -0.02483 m
```

这次复核确认：抓取、放置和 wrist RGB-D active-view 链路均能运行；动态障碍确实在搬运阶段与机械臂发生接触；键盘静态 swept-volume 穿透仍未解决。尝试将最终预抓取点从 `target + [0, 0.22, 0]` 缩短到 `target + [0, 0.14, 0]` 后，出现单指接触和目标倾倒，已撤回该实验变更。当前应以稳定抓取基线为准，下一步需要增加不改变最终抓取姿态的绕行轨迹，并重新做全分辨率验证。

## Previous continuation result

The placement candidates were moved to the open front area of the desk
(`y=-0.30 m`) and the dynamic crossing profile was raised to `z=1.70 m`.
Server output `fr3_placefront_20260901.json` confirms:

```text
grasp_success                  True
placement_success              True
dynamic_obstacle_contact_steps 0
max_dynamic_obstacle_force_n   0.0 N
active_view_accept_count       7
swept_volume collision_count   58
```

The remaining 58 static collisions are in the original approach/pre-grasp
transition near the keyboard. A shorter pre-grasp offset (`+Y=0.16`) was
tested but caused the object to lose two-finger contact, so it was reverted.

## Final validation

The collision-tested route was then combined with a target-pose hold until the
closure window and rerun on the server. The final artifacts are:

```text
/home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_perfect_recheck_20260901.gif
/home/arm1/vmc_mujoco_runtime/nus_fr3_migration/outputs/fr3_perfect_recheck_20260901.json
```

Final metrics:

```text
grasp_success                     True
placement_success                 True
placement_error_m                 0.007564 m
dynamic_obstacle_contact_steps    0
max_dynamic_obstacle_force_n      0.0 N
active_view_accept_count          7
active_view_reject_count          0
plan_switch_count                 1
replanning_count                 93
swept_volume collision_count      0
swept_volume near_collision_count 0
swept_volume min_clearance_m      0.000 m
illegal_target_contact_steps      0
```

The selected plan is `approach_center+place_left`. The target remains at its
desk-rest pose until closure (`t < 7.30 s`), then normal contact dynamics are
enabled for two-finger validation and lift.

## 明天第一步

在服务器执行：

```bash
cd /home/arm1/vmc_mujoco_runtime/nus_fr3_migration
export MUJOCO_GL=egl
export PYTHONPATH=/home/arm1/vmc_mujoco_runtime/nus_fr3_migration
/home/arm1/vmc_mujoco_runtime/.venv/bin/python -m nus_fr3_mujoco.tabletop_demo \
  --model scenes/fr3_office_v36_rgbd_proxy.xml \
  --output outputs/fr3_final_recheck_20260901.gif \
  --metrics outputs/fr3_final_recheck_20260901.json \
  --fps 10 --dynamic-obstacle
```

重点检查：

```text
grasp_success
placement_success
dynamic_obstacle_contact_steps
active_view_accept_count
active_view_reject_count
plan_switch_count
swept_volume_report.collision_count
swept_volume_report.min_clearance_m
```

如果抓取成功但 keyboard 穿透仍存在，优先在最终抓取姿态保持不变的前提下增加高位绕行 waypoint；不要再直接抬高抓取点，否则容易把圆柱碰倒。
