# Residual Compliance Fetch 进度记录

本文件用于持续记录当前工程完成到哪一步、还存在什么假设、后续可以怎么优化。后面每做一轮实验或改动，都优先更新这里。

## 当前阶段

当前处于：

```text
Phase 1A+: ManiSkill/SAPIEN + Fetch analytic residual demo
```

已经从最早的 2D toy prototype 推进到物理仿真环境：

```text
Fetch 固定底盘 + 固定 torso + 7D arm joint velocity control
```

## 已完成

1. 建立了独立工程目录：

```text
/home/hwy21/桌面/whole_body_manipulation/residual_compliance_fetch
```

2. 完成了第一版物理仿真 demo：

```text
baseline: 只跟踪 nominal arm path
residual: nominal arm path + analytic link-aware residual compliance
```

3. 实现了动态障碍物：

```text
一个红色 kinematic sphere 横穿机械臂路径
```

4. 实现了当前解析式避障机制：

```text
link-obstacle clearance
  -> risk gate
  -> Cartesian avoidance velocity
  -> link Jacobian / DLS 映射到 7D arm residual velocity
  -> nominal tracking softening
  -> velocity smoothing / acceleration limit
```

5. 实现了可视化：

```text
side / front / iso / close / top camera views
```

推荐汇报使用：

```text
--camera-view close
```

6. 当前固定 demo 结果：

```text
baseline:
  collision = true
  success = false
  min_clearance ≈ -0.0029 m

residual:
  collision = false
  success = true
  min_clearance ≈ 0.0145 m
```

7. 新增了 ObstacleProvider 抽象：

```text
TrueStateObstacleProvider
NoisyVisibleObstacleProvider
ContactReflexObstacleProvider placeholder
```

这一步把“物理世界里的真实障碍物”和“控制器能感知到的障碍物”分开了。

8. 新增了随机化评估入口：

```text
scripts/evaluate_randomized_obstacles.py
```

可以随机采样：

```text
障碍物半径
出现时间
速度
横穿位置
高度
```

并批量比较：

```text
baseline vs residual
```

9. 完成了最小 smoke test：

```text
true provider, 1 randomized episode, max_steps=420:
  baseline success = true, collision = false
  residual success = true, collision = false

noisy_visible provider, 1 randomized episode:
  residual success = true, collision = false
  min_clearance 从 true provider 的约 0.122 m 降到约 0.055 m
  mean_jerk 明显增加
```

这说明：

```text
ObstacleProvider 分支能跑通；
感知噪声/可见性丢失会明显影响安全距离和平滑性；
后续需要做统计规模更大的 randomized evaluation。
```

10. 优化了 noisy_visible provider：

```text
visible frame:
  对障碍物位置/速度/半径做 temporal smoothing

short dropout:
  保留上一帧障碍物估计
  confidence 按 memory_decay 衰减

controller:
  residual risk 按 perception confidence 缩放
```

目的：

```text
减少感知噪声和短时遮挡导致的 residual 抖动；
让“看不见一瞬间”不等于“障碍物突然消失”；
为后续点云记忆和力反馈融合做接口铺垫。
```

最小对比结果：

```text
noisy_visible, noise_std=0.02, dropout=0.20, 1 randomized episode

优化前:
  residual success = true
  collision = false
  min_clearance ≈ 0.055 m
  mean_jerk ≈ 0.0406

加入 smoothing + memory 后:
  residual success = true
  collision = false
  min_clearance ≈ 0.084 m
  mean_jerk ≈ 0.0111
```

初步说明：

```text
短时感知记忆可以明显降低 dropout 导致的 residual 抖动；
安全间隙也有所提升；
后续需要用更多 episodes 验证统计显著性。
```

## 当前仍然依赖的假设

1. 机械臂只控制 7D arm joints。

当前没有控制：

```text
base
torso
gripper
```

2. 当前 demo 默认仍然可以使用仿真真值 provider。

也就是：

```text
obstacle_provider = true
```

这适合验证底层控制器，但不能直接等价为真实感知闭环。

3. NoisyVisibleObstacleProvider 只是模拟视觉不完美。

它可以模拟：

```text
位置噪声
偶发看不见 / dropout
短时障碍物记忆
confidence 衰减
```

但还没有真正从 RGB-D / 点云中估计障碍物。

4. ContactReflexObstacleProvider 目前只是占位。

后续如果加入力反馈或接触反馈，应从这里扩展。

5. 随机评估时 max_steps 不能太短。

在一个 smoke test 中，`max_steps=120` 时 residual 绕开后尚未回到目标；默认 `max_steps=420` 可以恢复成功。后续统计时需要同时报告：

```text
success_rate
collision_rate
time/steps_to_recover
```

## 后续优化方向

### 0. 已尝试但未采用的 controller 优化

在 `true provider, 20 randomized episodes` 上尝试过以下 controller 修改：

```text
multi-link residual 加权平均
nominal clearance-rate motion gate
近端/远端 link 分层避障
低风险 residual 快速衰减
```

结果：

```text
原稳定版本 residual:
  success_rate = 0.95
  collision_rate = 0.05

上述组合修改后 residual:
  success_rate = 0.60
  collision_rate = 0.40
```

结论：

```text
这组 controller 修改整体变差，已经撤回。
当前保留的是原稳定 analytic residual controller；
继续保留 noisy_visible 的 temporal smoothing + short-term memory，因为该优化在 noisy smoke test 中有效。
```

这说明下一步不应继续靠手工调 analytic controller，而应转向：

```text
更多 randomized evaluation
expert data collection
BC / PPO 学习 residual
或引入更明确的 contact/force reflex
```

### 1. Force / Contact Reflex

后续可以加入力反馈，作为视觉之外的最后安全防线。

目标逻辑：

```text
视觉看到障碍物:
  提前避让

视觉没看到，但发生接触 / 近接触:
  触发 reflex compliance
  降低 nominal tracking
  沿接触法向退让
```

可能输入：

```text
contact force
contact link name
force direction / contact normal
wrench estimate
joint torque residual
```

第一版可以先用 ManiSkill/SAPIEN contact 信息近似力反馈。

### 2. 点云 ObstacleProvider

实现：

```text
DepthPointCloudObstacleProvider
```

输入：

```text
RGB-D / depth
camera intrinsics
camera pose
robot link poses
```

输出：

```text
link-obstacle distance
link-obstacle direction
confidence
```

这一步能回答“相机没看到会碰撞关节怎么办”的问题。

### 3. 可见性与不确定性

后续需要显式建模：

```text
visible / invisible
confidence
unknown near arm
```

当障碍物不可见但风险区域未知时，控制器应：

```text
降低速度
提高柔顺性
保守执行
```

### 4. Expert Data Collection

用 analytic residual controller 作为专家，采集：

```text
obs:
  q_arm
  qdot_arm
  q_target
  qdot_nom
  link-obstacle distances/directions
  perception confidence
  previous residual

label:
  delta_qdot_residual
```

用于 Behavior Cloning。

### 5. Learned Residual + PPO

学习路线已经确认：

```text
analytic expert
  -> behavior cloning warm start
  -> PPO residual RL fine-tuning
```

PPO reward 需要包含：

```text
goal progress
collision penalty
clearance reward
residual magnitude penalty
smoothness / jerk penalty
path recovery reward
```

### 6. 接回原项目

当前仍是独立 demo。

后续接回：

```text
Visibility-Awared-Mobile-Grasping/grasp_anywhere/envs/maniskill/maniskill_env_mpc.py
```

目标是在原项目执行 `arm_path` 的时候插入：

```text
nominal tracker
  -> residual compliance controller
  -> final arm command
```

### 7. Torso / Whole-Body 扩展

当前只做 7D arm。

后续扩展：

```text
torso + 7D arm
base + torso + arm
```

但建议在 7D arm 版本稳定、有统计结果后再做。

## 推荐下一步

近期优先顺序：

1. 基于 `contact_heavy_strict_500` 构建 BC 数据集。
2. 训练 BC residual policy，作为 PPO warm start。
3. 把 BC policy 接入 ManiSkill rollout，和 analytic controller 做对比。
4. 再进入 PPO fine-tuning。

## 2026-07-04 随机化评估结果更新

本轮已完成 `true` provider 和 `noisy_visible + smoothing + memory` provider 的 20 episode 随机化评估。

### TrueStateObstacleProvider, 20 episodes

```text
baseline:
  success_rate = 0.90
  collision_rate = 0.10
  mean_min_clearance = 0.1346 m
  mean_jerk = 0.0013
  mean_steps = 95.65

residual:
  success_rate = 0.95
  collision_rate = 0.05
  mean_min_clearance = 0.1016 m
  mean_jerk = 0.0093
  mean_steps = 216.95
```

结论：在可以获得障碍物真值状态时，当前 analytic residual controller 已经能把碰撞率从 10% 降到 5%，说明底层绕障机制有效；代价是路径更保守、步骤数和 jerk 增加。

### NoisyVisibleObstacleProvider + memory, 20 episodes

```text
baseline:
  success_rate = 0.90
  collision_rate = 0.10
  mean_min_clearance = 0.1346 m
  mean_jerk = 0.0013
  mean_steps = 95.65

residual:
  success_rate = 0.80
  collision_rate = 0.20
  mean_min_clearance = 0.0536 m
  mean_jerk = 0.0139
  mean_steps = 217.35
  mean_perception_confidence = 0.5188
```

失败样本集中在：

```text
episode 5:  min_clearance = -0.005696 m
episode 11: min_clearance = -0.000764 m
episode 13: min_clearance = -0.000212 m
episode 14: min_clearance = -0.000966 m
```

结论：加入感知噪声和 dropout 后，residual 的成功率下降到 80%，说明当前瓶颈已经从“会不会绕障”转为“感知不确定时如何保持安全裕度”。这些失败多数是毫米级擦碰，不是大幅失控，因此下一步不建议继续手工大改 analytic controller，而应优先做：

```text
1. 回放失败样本，观察碰撞发生在 wrist / forearm / upper-arm 哪个 link。
2. 采集 analytic expert dataset。
3. 训练 BC residual policy 作为 PPO warm start。
4. 增加 contact/force reflex 分支，用作视觉漏检时的最后防线。
```

### Failure replay ep005 近似回放

回放目录：

```text
outputs/failure_replay_ep005
```

本次使用三位小数近似障碍物参数回放，结果为：

```text
baseline:
  success = true
  collision = false
  min_clearance = 0.03149 m

residual:
  success = true
  collision = false
  min_clearance = 0.00484 m
  mean_jerk = 0.0144
  mean_perception_confidence = 0.6184
```

说明：这次没有复现原始 batch 中的碰撞，但 residual 的最小安全距离只有约 4.8 mm，仍属于高风险擦边样本。由于 noisy_visible provider 包含噪声/dropout，且障碍物参数之前被四舍五入，毫米级碰撞结果对随机性和精确参数非常敏感。后续失败回放应使用 `randomized_summary.json` 里的完整浮点参数。

## 2026-07-04 Contact / Force Reflex 兜底实验

本轮新增了显式开关：

```text
--enable-contact-reflex
```

含义：

## 2026-07-04 Contact-Only Strict 500 Episode 结果

本轮使用 contact-heavy 随机障碍物，并且保持严格接触触发：

```text
clearance > 0:
  不触发 residual

contact / penetration / contact memory:
  才允许接触柔顺 residual 与 force proxy 生效
```

输出目录：

```text
outputs/contact_heavy_strict_500
```

关键统计：

```text
baseline:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.824
  mean_max_penetration = 0.007827 m
  mean_contact_steps = 11.288
  mean_jerk = 0.002640
  mean_compliance_score = 83.085

contact_compliance:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.824
  mean_max_penetration = 0.007173 m
  mean_contact_steps = 9.768
  mean_contact_compliance_steps = 13.620
  mean_force_proxy_steps = 7.854
  mean_jerk = 0.004965
  mean_compliance_score = 84.091
```

逐 episode 对比：

```text
compliance_score 提升: 314 / 500
compliance_score 变差: 98 / 500
不变: 88 / 500

max_penetration 减小: 300 / 500
max_penetration 变大: 105 / 500
不变: 95 / 500

contact_steps 减少: 339 / 500
contact_steps 增加: 47 / 500
不变: 114 / 500
```

结论：

```text
当前解析式 contact_compliance 已经能统计性降低接触深度和接触持续时间；
但提升幅度仍然有限，且 jerk 明显增加；
部分 episode 会退化，说明继续手调解析公式收益有限。
```

因此下一步切换到：

```text
analytic contact-compliance expert
  -> BC warm start
  -> PPO residual RL fine-tuning
```

已新增脚本：

```text
scripts/build_bc_dataset.py
scripts/train_bc_policy.py
```

BC 输入严格避免使用 pre-contact 视觉距离，主要包含：

```text
q_arm
q_target
q_target - q_arm
qdot_nom
previous qdot_residual
contact_depth
force_proxy_level
qvel_tracking_error
contact_level
contact_flag
active_link one-hot
```

BC label:

```text
qdot_residual
```

当前 BC 只做离线模仿学习，不代表最终算法已经学会闭环控制。训练后还需要：

```text
1. 将 BC checkpoint 接入 rollout。
2. 与 baseline / analytic contact_compliance 做同一组 randomized evaluation。
3. 用 BC checkpoint 初始化 PPO。
```

## 2026-07-04 BC Warm Start 已完成

已从 `contact_heavy_strict_500` 生成离线模仿学习数据集：

```text
data/contact_heavy_strict_500_bc.npz
data/contact_heavy_strict_500_bc.stats.json
```

数据统计：

```text
record files = 500
samples = 60893
observation_dim = 45
action_dim = 7
contact / residual weighted samples = 14891
nonzero_action_ratio = 0.2445
mean_action_norm = 0.0564
max_action_norm = 0.7750
active links:
  none
  elbow_flex_link
  forearm_roll_link
  wrist_flex_link
  wrist_roll_link
```

已训练 BC policy：

```text
runs/bc_contact_policy.pt
runs/bc_contact_policy.history.json
```

训练配置：

```text
MLP hidden = 256, 256
epochs = 80
device = cuda
best_val_loss = 8.96e-05
num_samples = 60893
```

当前结论：

```text
BC 已能离线拟合 analytic contact_compliance expert；
但这只是 open-loop record imitation，不等价于闭环控制成功；
下一步必须把 BC checkpoint 接入 ManiSkill rollout，做 baseline / analytic / BC 三方对比。
```

```text
视觉/感知 provider 仍然可以是 noisy_visible；
但当仿真里任一 tracked arm link 距离障碍物低于 contact_reflex_clearance 时，
系统用仿真真值近似“力反馈/近接触反馈”，临时覆盖视觉估计，
让 residual controller 不再完全依赖 noisy visual estimate。
```

当前默认参数：

```text
contact_reflex_clearance = 0.12 m
contact_reflex_radius_margin = 0.0 m
```

### ep005 标准失败样本

原始 noisy residual：

```text
success = false
collision = true
min_clearance = -0.005696 m
```

近接触 reflex 初版：

```text
contact_reflex_clearance = 0.025 m
contact_reflex_radius_margin = 0.035 m
result: collision worse, min_clearance = -0.043220 m
```

结论：只在很近距离触发，并且人为扩大障碍物半径，会让现有 DLS residual 在近距离阶段产生更差动作，不应采用。

调成更早触发且不扩半径后：

```text
contact_reflex_clearance = 0.08 m
result: success = true, collision = false, min_clearance = 0.001824 m

contact_reflex_clearance = 0.12 m
result: success = true, collision = false, min_clearance = 0.007096 m
```

结论：提前的 near-contact / force-reflex 方向有效，能把 ep005 从碰撞救回；但安全间隙仍偏小。

### noisy_visible + contact-reflex, 20 episodes

输出目录：

```text
outputs/randomized_eval_noisy_contact_reflex_20
```

结果：

```text
baseline:
  success_rate = 0.90
  collision_rate = 0.10
  mean_min_clearance = 0.1346 m

residual + contact-reflex:
  success_rate = 0.95
  collision_rate = 0.05
  mean_min_clearance = 0.0689 m
  mean_jerk = 0.0140
  mean_steps = 216.55
  mean_contact_reflex_steps ~= 22.0
```

相对于上一轮 noisy_visible + memory：

```text
residual success_rate: 0.80 -> 0.95
residual collision_rate: 0.20 -> 0.05
```

说明 contact/force reflex 作为视觉漏检或噪声下的兜底是有价值的。

### 仍然失败的 ep013

ep013 障碍物速度较快：

```text
velocity_y = 0.407 m/s
```

即使把阈值提高到：

```text
contact_reflex_clearance = 0.18 m
```

仍然失败：

```text
residual:
  success = false
  collision = true
  min_clearance ~= -0.0128 m
```

并且该样本中 baseline 原本可以安全通过：

```text
baseline min_clearance ~= 0.0138 m
```

这说明 ep013 的核心问题不是“触发太晚”，而是 residual/avoidance 有时会破坏原本安全的 nominal path。后续不能只继续调阈值，应加入：

```text
1. residual intervention gate：判断 residual 是否真的应该介入；
2. command-level emergency reflex：触发时不仅改 obstacle observation，还能冻结 nominal tracking / 提高撤离速度；
3. BC + PPO 学习：让 policy 学会什么时候让、让多大、什么时候保持 nominal path；
4. safety filter：如果 residual command 预计会降低 clearance，就缩放或拒绝该 residual。
```

## 2026-07-04 任务定义纠正：Contact-Only Compliance

用户重新明确任务边界：

```text
上层已经给出预期轨迹；
底层控制器负责执行轨迹；
障碍物可能完全没有视觉预兆；
机械臂只有在碰到障碍物之后，才能通过力反馈/接触反馈感知到异常；
目标不是提前绕开，而是在接触发生后柔顺退让、滑开、绕过，再回到轨迹/目标。
```

因此，之前实验中的：

```text
contact_reflex_clearance = 0.08 m
contact_reflex_clearance = 0.12 m
```

只能解释为“近距离传感器 / 点云 / 视觉预警”假设下的 proximity proxy，不符合纯 contact-only 任务。它们可以保留为对照实验，但不应作为最终方法。

当前代码默认已改为：

```text
contact_reflex_clearance = 0.0 m
```

含义：

```text
只有 clearance <= 0，即已经接触/发生穿入时，contact reflex 才触发。
```

后续真正要训练/实现的是：

```text
contact event
  -> 降低 nominal tracking stiffness / 冻结继续硬推的轨迹跟踪
  -> 根据接触法向或力方向生成 retreat / slide residual
  -> 接触力下降后逐步恢复 nominal path
```

这也意味着评价指标需要调整：

```text
contact 不再等价于失败；
硬撞、深度穿入、持续大接触力、无法恢复，才算失败。
```

下一步应优先实现：

```text
1. contact-only observation：contact flag, contact normal / force proxy, touched link, penetration depth proxy；
2. command-level compliance reflex：冻结/软化 nominal command，并沿接触法向退让；
3. contact-aware metrics：最大穿入深度、接触持续时间、恢复时间、最终轨迹误差；
4. PPO 训练：policy 学习接触后如何柔顺退让和恢复轨迹。
```

## 2026-07-04 弹性碰撞 / Force Proxy 补充

用户指出真实接触不一定表现为几何穿入，也可能是弹性碰撞、反弹或瞬时冲击。这个判断是正确的，因此 contact-only 版本不能只依赖：

```text
clearance <= 0
```

当前已加入第二类触发信号：

```text
qdot_cmd: 控制器发出的关节速度命令
qvel_arm:  物理步进后的真实关节速度
qvel_tracking_error = ||qdot_cmd - qvel_arm||
```

当速度跟踪误差超过阈值时，将其作为外力/冲击反馈代理：

```text
force_proxy_level > 0
```

对应真实机器人中的：

```text
关节力矩残差
末端/腕部 force-torque impulse
控制器跟踪误差异常
接触导致的速度突变
```

注意：为了避免正常运动误差导致误触发，当前 strict contact-only 版本规定：

```text
force proxy 不能独立触发；
必须已经有几何接触 measured_contact_depth > 0，
或上一周期已有 contact memory，
速度跟踪误差才会被解释为接触后的力/冲击反馈。
```

同时仿真里暂时保留一个 sim-only gate：

```text
force_proxy_max_clearance = 0.035 m
```

含义是：接触记忆释放后，如果简化几何已经离障碍物较远，速度误差不再被解释为接触/冲击反馈。真实机器人上这一步应替换为真实 force/contact detector，而不是视觉距离。

最新 smoke test：

```text
outputs/contact_only_force_proxy_records_v2

baseline:
  contact_occurred = true
  max_penetration = 0.00294 m
  force_proxy_steps = 0

contact_compliance:
  contact_occurred = false by simplified clearance metric
  min_clearance = 0.00257 m
  contact_compliance_steps = 18
  force_proxy_steps = 18
  max_force_proxy_level = 0.114
```

解释：force proxy 在接近接触时触发，控制器提前进入柔顺退让，避免了 baseline 中的轻微几何穿入。这不是视觉预警，而是仿真中对弹性/冲击反馈的近似建模。

## 2026-07-04 Contact-Only 第一组正式实验结果

本轮用户完成三组实验：

```text
outputs/contact_only_demo_close
outputs/contact_only_randomized_20_v2
outputs/contact_only_ep018_demo
```

### 1. 默认 close demo

```text
baseline:
  success = true
  collision = false
  contact_occurred = true
  max_penetration = 0.00294 m
  contact_steps = 3
  force_proxy_steps = 0

contact_compliance:
  success = true
  collision = false
  contact_occurred = false by simplified clearance metric
  max_penetration = 0.0 m
  contact_steps = 0
  contact_compliance_steps = 18
  force_proxy_steps = 18
  max_force_proxy_level = 0.114
```

结论：在默认 demo 中，force proxy 触发了柔顺控制，使 baseline 中的轻微接触/穿入被避免。视觉上能看到手臂在障碍物靠近时有更保守的退让动作。

### 2. 随机 20 组

```text
baseline:
  success_rate = 1.00
  collision_rate = 0.00
  contact_rate = 0.10
  mean_max_penetration = 0.000998 m
  mean_contact_steps = 1.3
  mean_jerk = 0.00131

contact_compliance:
  success_rate = 1.00
  collision_rate = 0.00
  contact_rate = 0.10
  mean_max_penetration = 0.000869 m
  mean_contact_steps = 1.1
  mean_contact_compliance_steps = 1.65
  mean_force_proxy_steps = 1.15
  mean_jerk = 0.00159
```

结论：随机 20 组方向正确，contact_compliance 将平均最大穿入和平均接触步数略微降低；但当前随机采样太温和，只有 10% episode 真的发生接触，因此统计差异不够明显。

### 3. ep018 接触样本

```text
baseline:
  success = true
  collision = false
  contact_occurred = true
  max_penetration = 0.01129 m
  contact_steps = 11

contact_compliance:
  success = true
  collision = false
  contact_occurred = true
  max_penetration = 0.00995 m
  contact_steps = 10
  contact_compliance_steps = 15
  force_proxy_steps = 10
```

主要触发 link：

```text
forearm_roll_link
wrist_flex_link
```

结论：在更明显的接触样本中，contact_compliance 能减少约 1.3 mm 最大穿入并略减接触持续时间，但改善仍偏小。当前 analytic controller 是可用 baseline，还不是最终效果。

### 当前判断

```text
有效性：有，contact-only 机制已跑通，且不会依赖视觉预警。
展示性：默认 demo 有效果，但不够强烈；ep018 更适合展示接触后退让。
统计性：当前随机集太温和，需要构造 contact-heavy benchmark。
下一步：增加专门的 contact-heavy obstacle sampler，并开始为 BC/PPO 采集接触数据。
```

## 2026-07-04 Contact-Heavy 小范围检查

新增内容：

```text
randomized_contact_heavy_crossing_sphere
--sampler contact_heavy
compliance_score
--include-records
```

同时修正 force proxy 逻辑：

```text
force proxy 不能独立凭 qvel tracking error 触发；
必须已经发生几何接触，或上一周期有 contact memory；
这样满足 strict contact-only 假设。
```

小范围检查输出：

```text
outputs/contact_heavy_strict_smoke_3
```

结果：

```text
baseline:
  success_rate = 1.00
  collision_rate = 0.00
  contact_rate = 0.333
  mean_max_penetration = 0.00333 m
  mean_contact_steps = 6.67
  mean_compliance_score = 90.42

contact_compliance:
  success_rate = 1.00
  collision_rate = 0.00
  contact_rate = 0.333
  mean_max_penetration = 0.00376 m
  mean_contact_steps = 5.33
  mean_contact_compliance_steps = 7.33
  mean_force_proxy_steps = 4.33
  mean_compliance_score = 89.87
```

解释：

```text
1. 小检查流程通过，可以开始采集更大规模数据。
2. 没接触的 episode 中 force_proxy_steps = 0，说明 strict contact-only 约束生效。
3. 3 个 episode 太少，不能判断最终性能。
4. 当前 analytic contact_compliance 在这一小组里分数略低于 baseline，说明它只是初始规则 baseline，后续确实需要 BC/PPO 学习更好的接触后退让策略。
```

## 2026-07-04 Contact-Heavy 500 Episodes 数据采集结果

输出目录：

```text
outputs/contact_heavy_strict_500
```

数据规模：

```text
episodes = 500
sampler = contact_heavy
include_records = true
disk_usage ~= 163 MB
files = 1501
```

总体结果：

```text
baseline:
  success_rate = 1.00
  collision_rate = 0.00
  contact_rate = 0.824
  mean_max_penetration = 0.007827 m
  mean_contact_steps = 11.288
  mean_jerk = 0.002640
  mean_compliance_score = 83.085

contact_compliance:
  success_rate = 1.00
  collision_rate = 0.00
  contact_rate = 0.824
  mean_max_penetration = 0.007173 m
  mean_contact_steps = 9.768
  mean_contact_compliance_steps = 13.620
  mean_force_proxy_steps = 7.854
  mean_jerk = 0.004965
  mean_compliance_score = 84.091
```

接触 episode 内部统计：

```text
contact episodes = 412 / 500

mean_max_penetration:
  baseline = 0.009499 m
  contact_compliance = 0.008705 m
  improvement ~= 0.000794 m

mean_contact_steps:
  baseline = 13.699
  contact_compliance = 11.854
  improvement ~= 1.845 steps

mean_compliance_score:
  baseline = 80.208
  contact_compliance = 81.428
  improvement ~= 1.221
```

逐 episode 对比：

```text
score improved: 314 episodes
score worse:     98 episodes
score unchanged: 88 episodes

penetration reduced: 300 episodes
penetration worse:   105 episodes
unchanged:            95 episodes

contact steps reduced: 339 episodes
contact steps worse:    47 episodes
unchanged:             114 episodes
```

判断：

```text
contact-heavy 数据采集成功；
当前 analytic contact_compliance 在统计上优于 baseline；
但提升幅度较小，且 mean_jerk 增加明显；
部分 episode 中 compliance 反而使穿入或接触持续时间变差；
因此它适合作为 PPO/BC 的初始 baseline 和数据来源，但还不是最终控制器。
```

典型问题：

```text
最高穿入仍在 1.4-1.6 cm 左右；
低分样本多发生在较大半径、高速度障碍物；
regression 样本常见现象是 contact_compliance_steps 很多，但未能有效减少穿入。
```

## 2026-07-04 BC Closed-Loop 接入

已将 BC checkpoint 接入 ManiSkill rollout：

```text
bc_policy mode
```

当前逻辑：

```text
无接触 / 无力反馈 / 无 residual memory:
  residual = 0
  完全跟踪 nominal path

接触或力反馈正在发生:
  调用 BC policy 输出 7D residual qdot

接触释放后:
  不继续让 BC 自由输出
  使用 recovery_decay 对上一帧 residual 做指数衰减
```

这样做的原因：

```text
任务定义是 contact-only；
没有接触时不允许 residual 凭空改变轨迹；
接触释放后需要稳定回到原路径，避免 BC bias 拖慢到达目标。
```

已通过 3 episode smoke test：

```text
outputs/bc_policy_smoke_3_recovery_decay

baseline:
  success_rate = 1.000
  mean_compliance_score = 90.420

contact_compliance:
  success_rate = 1.000
  mean_compliance_score = 89.871

bc_policy:
  success_rate = 1.000
  mean_compliance_score = 89.131
```

解读：

```text
BC 闭环已经能跑通；
但当前 BC 只是 warm start，还没有超过 analytic controller；
下一步需要跑 20/100 episode 统计，并据此决定 PPO reward 和 fine-tuning 方向。
```

推荐下一条命令：

```bash
CUDA_VISIBLE_DEVICES=0 python scripts/evaluate_randomized_obstacles.py \
  --episodes 20 \
  --sampler contact_heavy \
  --render-mode none \
  --bc-checkpoint runs/bc_contact_policy.pt \
  --output-dir outputs/bc_policy_eval_20
```

## 2026-07-05 BC Policy 500 Episodes 正式评估

输出目录：

```text
outputs/bc_policy_eval_500
```

实验配置：

```text
episodes = 500
sampler = contact_heavy
bc_checkpoint = runs/bc_contact_policy.pt
include_records = false
contact_trigger_clearance = 0.0
```

总体结果：

```text
baseline:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.824
  mean_max_penetration = 0.007827 m
  mean_contact_steps = 11.288
  mean_jerk = 0.002640
  mean_compliance_score = 83.085

contact_compliance:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.824
  mean_max_penetration = 0.007173 m
  mean_contact_steps = 9.768
  mean_jerk = 0.004965
  mean_compliance_score = 84.091

bc_policy:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.824
  mean_max_penetration = 0.007110 m
  mean_contact_steps = 10.122
  mean_jerk = 0.005106
  mean_compliance_score = 84.129
```

只统计发生接触的 episodes：

```text
contact episodes = 412 / 500

baseline:
  mean_max_penetration = 0.009499 m
  mean_contact_steps = 13.699
  mean_compliance_score = 80.208

contact_compliance:
  mean_max_penetration = 0.008705 m
  mean_contact_steps = 11.854
  mean_compliance_score = 81.428

bc_policy:
  mean_max_penetration = 0.008628 m
  mean_contact_steps = 12.284
  mean_compliance_score = 81.475
```

逐 episode 对比：

```text
bc_policy vs contact_compliance:
  score improved = 253
  score worse = 159
  unchanged = 88
  penetration reduced = 267
  penetration worse = 136
  unchanged = 97

bc_policy vs baseline:
  score improved = 319
  score worse = 93
  unchanged = 88
  penetration reduced = 307
  penetration worse = 98
  unchanged = 95
  contact_steps reduced = 300
  contact_steps worse = 54
  unchanged = 146
```

结论：

```text
BC policy 在 500 条闭环评估中稳定，没有 success/collision 退化；
相比 baseline 有明确提升；
相比 analytic contact_compliance 只有很小优势，主要体现在平均穿入略低和 score 略高；
BC 的接触持续时间略长、jerk 略高，说明它还不是最终控制器；
当前 checkpoint 适合作为 PPO warm start。
```

下一步：

```text
进入 PPO fine-tuning。
PPO 的 reward 应重点优化：
  1. 降低 max_penetration；
  2. 缩短 contact_steps；
  3. 限制 jerk / residual 抖动；
  4. 保持 final_arm_error 和 success_rate；
  5. 对 regression episodes 做额外分析，例如 episode 124 和 177。
```

## 2026-07-05 修正：Arm-Only Demo 显式锁住本体

发现问题：

```text
Fetch 在 ManiSkill 的 active joints 不只有 7D arm，还包含：
  root_x_axis_joint
  root_y_axis_joint
  root_z_rotation_joint
  torso_lift_joint
  head_pan_joint
  head_tilt_joint
  gripper fingers
```

之前 demo 虽然只给 arm residual，但没有显式验证 base / torso / head 是否保持不动。用户观察到 GIF 中机器人像是“本体下蹲”，因此原展示不能作为严格 arm-only 结果。

已修正：

```text
DemoConfig.lock_non_arm_joints = True

每个 physics step 后显式恢复：
  root_x_axis_joint
  root_y_axis_joint
  root_z_rotation_joint
  torso_lift_joint
  head_pan_joint
  head_tilt_joint

gripper fingers 不计入 body lock correction，避免把手指开合误认为本体漂移。
```

已新增 metrics：

```text
max_locked_joint_correction
mean_locked_joint_correction
max_locked_joint_velocity_norm
locked_joint_names
```

新的可视化目录：

```text
outputs/bc_policy_visual_ep152_body_locked_close_disappear
```

打开：

```bash
xdg-open outputs/bc_policy_visual_ep152_body_locked_close_disappear/view.html
```

注意：

```text
之前的 bc_policy_eval_500 统计是在未严格锁住 base/torso/head 的旧设置下得到的；
从该修正之后，后续正式评估和 PPO 应基于 body-locked arm-only 设置重新跑。
```

## 2026-07-05 Body-Locked BC Policy 100 Episodes 评估

输出目录：

```text
outputs/bc_policy_body_locked_eval_100
```

实验配置：

```text
episodes = 100
sampler = contact_heavy
lock_non_arm_joints = true
bc_checkpoint = runs/bc_contact_policy.pt
```

总体结果：

```text
baseline:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.810
  mean_max_penetration = 0.005412 m
  mean_contact_steps = 10.38
  mean_jerk = 0.004322
  mean_compliance_score = 86.831

contact_compliance:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.810
  mean_max_penetration = 0.005204 m
  mean_contact_steps = 10.04
  mean_jerk = 0.006888
  mean_compliance_score = 86.939

bc_policy:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.810
  mean_max_penetration = 0.005332 m
  mean_contact_steps = 9.91
  mean_jerk = 0.006744
  mean_compliance_score = 86.802
```

只看发生接触的 episodes：

```text
contact episodes = 81 / 100

baseline:
  mean_max_penetration = 0.006682 m
  mean_contact_steps = 12.815
  mean_compliance_score = 84.553

contact_compliance:
  mean_max_penetration = 0.006425 m
  mean_contact_steps = 12.395
  mean_compliance_score = 84.686

bc_policy:
  mean_max_penetration = 0.006582 m
  mean_contact_steps = 12.235
  mean_compliance_score = 84.517
```

逐 episode 对比：

```text
bc_policy vs contact_compliance:
  score improved = 50
  score worse = 31
  unchanged = 19
  penetration reduced = 42
  penetration worse = 37
  unchanged = 21

bc_policy vs baseline:
  score improved = 39
  score worse = 42
  unchanged = 19
  penetration reduced = 45
  penetration worse = 33
  unchanged = 22
```

结论：

```text
body-locked 后 BC policy 仍然稳定：
  success_rate 没有下降；
  collision_rate 没有上升；
  可以作为 PPO warm start。

但 BC 的平均效果没有超过 analytic contact_compliance：
  mean_score 略低；
  mean_max_penetration 略高；
  contact_steps 略少。

说明旧 BC checkpoint 是在未严格 body-locked 的数据分布上训练的；
修正仿真条件后，最好重新采 body-locked expert dataset，并重训 BC。
```

推荐下一步：

```text
1. 用 body-locked 设置重新采 500 episode expert records；
2. 重新构建 BC dataset；
3. 重新训练 body-locked BC policy；
4. 再用该 checkpoint 作为 PPO 初始化；
5. PPO reward 重点压制 episode 57 / 74 / 56 / 25 这类 regression。
```

## 2026-07-05 Body-Locked Expert Records 500 Episodes 采集结果

输出目录：

```text
outputs/contact_heavy_body_locked_500
```

实验配置：

```text
episodes = 500
sampler = contact_heavy
include_records = true
bc_checkpoint = null
lock_non_arm_joints = true
```

总体结果：

```text
baseline:
  success_rate = 0.998
  collision_rate = 0.002
  contact_rate = 0.788
  mean_max_penetration = 0.006300 m
  mean_contact_steps = 11.302
  mean_jerk = 0.004435
  mean_compliance_score = 85.251

contact_compliance:
  success_rate = 0.996
  collision_rate = 0.004
  contact_rate = 0.788
  mean_max_penetration = 0.005946 m
  mean_contact_steps = 10.238
  mean_jerk = 0.006953
  mean_compliance_score = 85.593
```

只看发生接触的 episodes：

```text
contact episodes = 394 / 500

baseline:
  success_rate = 0.997
  collision_rate = 0.0025
  mean_max_penetration = 0.007995 m
  mean_contact_steps = 14.343
  mean_compliance_score = 82.206

contact_compliance:
  success_rate = 0.995
  collision_rate = 0.0051
  mean_max_penetration = 0.007545 m
  mean_contact_steps = 12.992
  mean_compliance_score = 82.639
```

逐 episode 对比：

```text
contact_compliance vs baseline:
  score improved = 197
  score worse = 196
  unchanged = 107
  penetration reduced = 209
  penetration worse = 155
  unchanged = 136
  contact_steps reduced = 175
  contact_steps worse = 124
  unchanged = 201
```

重要 regression：

```text
episode 206:
  contact_compliance collision = true
  contact_compliance max_penetration = 0.0258 m
  baseline max_penetration = 0.0234 m
  score delta = -53.85

其它明显退化样本包括：
  403, 326, 441, 414, 456, 220, 200, 329, 152
```

结论：

```text
body-locked expert records 已成功采集；
analytic contact_compliance 平均上比 baseline 更柔顺：
  max_penetration 更低；
  contact_steps 更少；
  score 略高。

但它不是完美 expert：
  success_rate / collision_rate 略差于 baseline；
  improved 和 worse episode 数量几乎持平；
  存在少数严重 regression。
```

因此重训 BC 时不应盲目模仿所有 contact_compliance 轨迹。推荐：

```text
1. 先排除 collision / failure 的 expert episodes；
2. 排除 contact_compliance 明显差于 baseline 的 episodes；
3. 或者给 regression episodes 低权重；
4. 再训练 body-locked BC；
5. 用新的 body-locked BC checkpoint 进入 PPO。
```

## 2026-07-05 Filtered Body-Locked BC 数据集与 checkpoint

已修改：

```text
scripts/build_bc_dataset.py
```

新增质量过滤参数：

```text
--exclude-failures
--min-score-delta
--max-penetration-delta
--max-contact-steps-delta
```

本轮采用过滤策略：

```text
--exclude-failures
--min-score-delta 0.0
```

含义：

```text
1. 丢弃 contact_compliance 自己失败或碰撞的 episode；
2. 只模仿 contact_compliance 分数不低于 baseline 的 episode。
```

生成数据：

```text
data/contact_heavy_body_locked_500_filtered_bc.npz
data/contact_heavy_body_locked_500_filtered_bc.stats.json
```

数据统计：

```text
candidate_episodes = 500
kept_episodes = 303
excluded_episodes = 197
excluded_reasons:
  score_delta_too_low = 195
  teacher_failure_or_collision = 2
num_samples = 39602
observation_dim = 45
action_dim = 7
contact_or_residual_weighted_samples = 6607
nonzero_action_ratio = 0.1668
```

已训练新 checkpoint：

```text
runs/bc_body_locked_filtered_policy.pt
runs/bc_body_locked_filtered_policy.history.json
```

训练结果：

```text
epochs = 80
device = cuda
best_val_loss = 2.326e-04
num_samples = 39602
```

下一步：

```text
用 body-locked filtered BC checkpoint 跑 100 episode 评估；
如果稳定且不比 analytic contact_compliance 差，再跑 500 episode；
之后再决定是否进入 PPO。
```

## 2026-07-05 Filtered Body-Locked BC 100 Episodes 评估

输出目录：

```text
outputs/bc_body_locked_filtered_eval_100
```

总体结果：

```text
baseline:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.810
  mean_max_penetration = 0.005412 m
  mean_contact_steps = 10.38
  mean_compliance_score = 86.831

contact_compliance:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.810
  mean_max_penetration = 0.005204 m
  mean_contact_steps = 10.04
  mean_compliance_score = 86.939

filtered_bc_policy:
  success_rate = 1.000
  collision_rate = 0.000
  contact_rate = 0.810
  mean_max_penetration = 0.005542 m
  mean_contact_steps = 10.11
  mean_compliance_score = 86.425
```

只看发生接触的 episodes：

```text
contact episodes = 81 / 100

baseline score = 84.553
contact_compliance score = 84.686
filtered_bc_policy score = 84.052
```

逐 episode 对比：

```text
filtered_bc_policy vs contact_compliance:
  score improved = 37
  score worse = 44
  unchanged = 19
  penetration reduced = 32
  penetration worse = 48
  unchanged = 20

filtered_bc_policy vs baseline:
  score improved = 37
  score worse = 44
  unchanged = 19
  penetration reduced = 47
  penetration worse = 32
  unchanged = 21
```

明显 regression：

```text
episode 38:
  filtered_bc max_penetration = 0.0214 m
  contact_compliance max_penetration = 0.0092 m
  score delta vs contact_compliance = -19.81

episode 57:
  filtered_bc max_penetration = 0.0205 m
  contact_compliance max_penetration = 0.0101 m
  score delta vs contact_compliance = -17.10

episode 12:
  filtered_bc max_penetration = 0.0204 m
  contact_compliance max_penetration = 0.0112 m
  score delta vs contact_compliance = -14.05
```

结论：

```text
filtered BC 没有成功提升；
虽然 success/collision 仍稳定，但平均 score 低于 baseline 和 contact_compliance；
硬过滤导致训练集从 500 episodes 降到 303 episodes，可能丢失了困难接触场景的覆盖；
因此不建议用 runs/bc_body_locked_filtered_policy.pt 直接进入 PPO。
```

下一步建议：

```text
不要硬过滤掉坏 episode；
改为保留困难场景，但对坏老师 action 降权，或者让 PPO 在这些场景里自己探索；
更推荐先训练 unfiltered body-locked BC 作为 warm start，再 PPO。
```

## 2026-07-05 Strict Penetration Threshold 100 Episodes

输出目录：

```text
outputs/contact_heavy_body_locked_strict_pen_100
```

实验配置：

```text
episodes = 100
sampler = contact_heavy
allowed_penetration = 0.010 m
bc_checkpoint = null
```

总体结果：

```text
baseline:
  success_rate = 0.820
  collision_rate = 0.180
  contact_rate = 0.810
  mean_max_penetration = 0.005412 m
  mean_contact_steps = 10.38
  mean_compliance_score = 73.895

contact_compliance:
  success_rate = 0.800
  collision_rate = 0.200
  contact_rate = 0.810
  mean_max_penetration = 0.005204 m
  mean_contact_steps = 10.04
  mean_compliance_score = 72.072
```

只看发生接触的 episodes：

```text
contact episodes = 81 / 100

baseline:
  success_rate = 0.778
  collision_rate = 0.222
  mean_max_penetration = 0.006682 m
  mean_contact_steps = 12.815
  mean_compliance_score = 68.583

contact_compliance:
  success_rate = 0.753
  collision_rate = 0.247
  mean_max_penetration = 0.006425 m
  mean_contact_steps = 12.395
  mean_compliance_score = 66.332
```

逐 episode 对比：

```text
contact_compliance vs baseline:
  score improved = 27
  score worse = 37
  unchanged = 36
  penetration reduced = 46
  penetration worse = 33
  unchanged = 21
  contact_steps reduced = 26
  contact_steps worse = 25
  unchanged = 49
```

关键现象：

```text
allowed_penetration 从 2.5 cm 收紧到 1.0 cm 后，
baseline 成功率从接近 1.0 降到 0.82，
说明之前 baseline 确实被宽松阈值高估。

但 analytic contact_compliance 并没有因此显著胜出：
平均穿入和接触步数略好，
但 collision_rate 反而略高，
score 低于 baseline。
```

典型 regression：

```text
episode 61:
  baseline max_penetration = 0.0086 m, no collision
  contact_compliance max_penetration = 0.0135 m, collision

episode 77:
  baseline max_penetration = 0.0091 m, no collision
  contact_compliance max_penetration = 0.0126 m, collision

episode 2:
  baseline max_penetration = 0.0099 m, no collision
  contact_compliance max_penetration = 0.0111 m, collision
```

典型 gain：

```text
episode 80:
  baseline max_penetration = 0.0224 m, collision
  contact_compliance max_penetration = 0.0069 m, no collision
```

结论：

```text
1 cm safety threshold 更合理，能暴露 baseline 的硬撞风险；
但当前 analytic contact_compliance 不是稳定强 teacher；
后续 PPO reward 应直接围绕 1 cm safety threshold 优化；
BC 只能作为 warm start，不能作为最终策略依据。
```

## 2026-07-05 Unfiltered Body-Locked BC + Strict Penetration 100 Episodes

输出目录：

```text
outputs/bc_body_locked_unfiltered_strict_pen_100
```

实验配置：

```text
episodes = 100
sampler = contact_heavy
allowed_penetration = 0.010 m
bc_checkpoint = runs/bc_body_locked_unfiltered_policy.pt
```

总体结果：

```text
baseline:
  success_rate = 0.820
  collision_rate = 0.180
  mean_max_penetration = 0.005412 m
  mean_contact_steps = 10.38
  mean_compliance_score = 73.895

contact_compliance:
  success_rate = 0.800
  collision_rate = 0.200
  mean_max_penetration = 0.005204 m
  mean_contact_steps = 10.04
  mean_compliance_score = 72.072

unfiltered_bc_policy:
  success_rate = 0.800
  collision_rate = 0.200
  mean_max_penetration = 0.005524 m
  mean_contact_steps = 10.15
  mean_compliance_score = 72.065
```

只看发生接触的 episodes：

```text
contact episodes = 81 / 100

baseline:
  success_rate = 0.778
  collision_rate = 0.222
  mean_max_penetration = 0.006682 m
  mean_contact_steps = 12.815
  mean_compliance_score = 68.583

contact_compliance:
  success_rate = 0.753
  collision_rate = 0.247
  mean_max_penetration = 0.006425 m
  mean_contact_steps = 12.395
  mean_compliance_score = 66.332

unfiltered_bc_policy:
  success_rate = 0.753
  collision_rate = 0.247
  mean_max_penetration = 0.006819 m
  mean_contact_steps = 12.531
  mean_compliance_score = 66.323
```

逐 episode 对比：

```text
unfiltered_bc_policy vs baseline:
  score improved = 33
  score worse = 33
  unchanged = 34
  penetration reduced = 48
  penetration worse = 30
  unchanged = 22

unfiltered_bc_policy vs contact_compliance:
  score improved = 36
  score worse = 27
  unchanged = 37
  penetration reduced = 48
  penetration worse = 31
  unchanged = 21
```

关键现象：

```text
unfiltered BC 与 analytic contact_compliance 基本打平；
二者都没有在 1 cm safety threshold 下超过 baseline；
BC 有一些 rescue case，例如 57 / 80 / 84；
但也有严重 regression，例如 47 / 61 / 77 / 83 / 2。
```

结论：

```text
当前 BC 不适合作为最终结果；
但可作为 PPO warm start，因为它能复现 contact reflex 大致行为；
真正性能提升需要 PPO 直接优化 1 cm safety reward，而不是继续依赖 imitation。
```
