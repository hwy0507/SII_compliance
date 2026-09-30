# Canonical48/action7 PPO 开发试验

本轮建立与当前 canonical student 相同 **48D 因果观测 / 7D 动作 / 原 panel task、observer、WBC 和 safety** 的 PPO 最小闭环，并先验证桥接代码没有改变零动作物理轨迹。它是按 teacher manifest 重建的 **push 子集开发试验**，不是完整四场景 RL baseline，也不是某篇论文的完整复现；不能与早期 32D legacy pilot 混为一谈。

## 实验入口与证据

- 独立 Gym 桥：`scripts/canonical48_rl_env_20260923.py`。
- 入口：`tools/run_canonical48_ppo_20260923.py`。
- 本轮输出：`outputs/canonical48_ppo_pilot_20260923_r1/`。
- 启动日志：`outputs/canonical48_ppo_pilot_20260923_r1.launch.log`。
- 运行进度：`progress.json`；完成必须以 `COMPLETE.json` 为准，失败写 `FAILED.json`。
- manifest 保存软件版本、全部 scripts/src Python 源文件 hash、所有机器人资源 hash、teacher bank hash、训练配置、数据 split 和选择规则。

本机环境为独立 `.venv-canonical-rl`，MuJoCo 3.11.0（与服务器一致）、PyTorch 2.11.0+cu128、Stable-Baselines3 2.9.0。没有更改已有 controller 文件或旧 RL 环境。

## 数据与重建边界

Teacher manifest SHA256：`8762b865a9bce8f3dd98e3495d71b3ad0e05d900c69e7e878b98b46fbff78847`。

按原 manifest 顺序选取各 split 的第一个 push 样本，未按候选模型表现挑选：

| 用途 | manifest id | 物理 fixture | 接触 focus | rod stroke |
|---|---|---|---|---:|
| train | push_00000 | rod | push_rod_geom | 0.17 m |
| validation | push_00714 | front | push_front_guard | 0 m |

物理参数来自对应历史 `command.json` 和 `rollout.json`；任务使用当前 canonical panel runner。实算完整 manifest 的 physical_fixture、fixture_hash、parameter_group、content_hash 在 train/validation/test 两两交集均为空，共 12 项检查。未打开 test episode 数据，未用 office 训练或选模。只训练一个 rod fixture、验证一个 front fixture不足以证明跨场景泛化。

重建时发现当前 runner 的默认 rod 高度变为 0.60 m，而归档 scene/arguments 都是 0.65 m。独立桥显式增加 `PANEL_CONFIG.rod_height_m=0.65` 恢复已记录值；最终 scene 逐字段和 physical_panels 均必须与归档相等，否则试验报错。错误默认值的首次短试验保留在 `outputs/canonical48_bridge_smoke_20260923/`，未计入正式 pilot。没有历史源码完整快照或模型逐字节一致性证明，不能宣称重放了历史 teacher runtime。每次完整 rollout 的 `historical_config_audit.json` 明确记录该边界。

## 观测、动作、reward 与冻结评估

Actor 和 critic 都只接受原 runner 提供的 48 个值：q7、qdot7、nominal_twist6、pose_error6、twist_error6、estimated_joint_load7、estimated_wrench6、path_direction3。动作是 slowdown `[0,1]` 加六轴 yield `[-1,1]`，**不是直接输出关节力矩**。动作继续通过原控制链的滤波、slew 与安全约束；WBC 仍为 `ScaledReferenceWBC`，nominal、reset、阶段切换等代码保持原入口。

Reward 使用下一 actor 观测中的位置误差、旋转误差、估计力，以及动作幅值/变化惩罚；阶段前进 +0.5，终端 task success +5、invalid physics −5。phase、终端任务标签是 reward supervision，**未拼入 actor 或 value 输入**。评估接触审计也只写入终端 info。Reward 不等于严格物理成功 gate；高 reward 不能代替 gate。

训练仅在线拟合 train 的 VecNormalize，验证时冻结均值/方差/count并检查不变；固定预算最后 checkpoint，无 validation 选模。终端不从 audit 状态构造新的 actor observation，不对该状态 bootstrap。冻结评估重新加载保存的 PPO checkpoint；失败完整保留，不筛除。

本轮超参数：640 transitions；PPO MLP 128×128；n_steps=64、batch_size=64、n_epochs=3、lr=3e−4、gamma=.995、GAE=.95、initial log_std=−2；训练随机种子 20260923，fixture seed 来自归档（800）。24 s 每 episode 为 600 步，因此预算包含一个完整 episode 及第二个 partial；预算结束的 partial 单独保存且不计成完整评估。

评估同时报告 task success 和独立开发 gate：任务成功、无 invalid physics、无 upstream contact、正确 focus 实际接触、所有外部接触最大穿透 ≤0.2 mm。front 的 rod stroke=0，因此不套用 rod release gate。本 gate 不是已经完成论文冻结的正式 test gate。

## 验证与本机资源

在同一恢复配置的当前 runner 上，直接注入全零动作与经 Gym 队列提交全零动作各运行 6.4 s / 160 步，27 个数组逐项完全相等：包含 48D actor observations、7D actions、阶段 metadata、完整 physics_states、contact_samples、原 rollout 数据。证据为 `zero_parity/ZERO_PARITY.json`。此证明针对桥接一致性，不能用来证明历史 teacher 轨迹一致性。

RTX 5080 Laptop GPU（16 GB 显存）已实际用于策略梯度更新。MuJoCo 物理步进在 CPU，128×128 MLP 的计算量很小，因此低 GPU 利用率是预期情况，不为提高显示占用率增加并行环境。

为避免本机 16 GB 内存再次耗尽：单仿真环境、线程1、CPU affinity2核、nice10、CUDA进程配额15%；每次 actor 步及 reset 检查 RSS≤7 GiB、系统可用≥2.5 GiB；45分钟硬时限。执行 PID39497（父 timeout PID39496）只适用于此次运行，不用于下次自动识别。早期160步观测 RSS约2.27 GiB、系统可用9.40 GiB、CUDA已分配约18 MiB。资源守卫不是操作系统 cgroup 的内存硬上限。

## 结果状态

本轮已完整结束，总耗时 **581.44 s（9.69 min）**。Checkpoint 实查 `num_timesteps=640`、`_n_updates=30`，完整训练 episode 为600步且观测/动作全finite，第二个40步 partial单独保留。评估期间 normalization 均值、方差、count保持不变。

| fixture/split | policy | task success | 开发 gate | 最大外部穿透 mm | 峰值外部合力 N | 末端误差 m | episode reward |
|---|---|---|---|---:|---:|---:|---:|
| rod/train | zero | 否 | 否 | 0.150568 | 219.224 | 0.187870 | −11.1149 |
| rod/train | PPO640 | 否 | 否 | 0.104238 | 249.058 | 0.186567 | −15.7449 |
| front/validation | zero | 是 | 是 | 0.000843 | 87.698 | 0.007068 | 3.2267 |
| front/validation | PPO640 | 是 | 是 | 0.002441 | 124.138 | 0.008226 | 3.3141 |

没有证据表明此小预算 PPO 改善了任务成功率：rod 两者失败；front 零动作本已通过，PPO虽然仍通过，峰值合力、穿透和末端误差反而上升。两者都是1/2也不能据此给出“泛化成功率50%”，因为这是各一个开发 fixture、一个模型种子的探索性结果。Reward提高也不代表接触品质改善。

最终进程 RSS2.29 GiB、系统可用9.39 GiB，进程正常结束。PPO checkpoint：`outputs/canonical48_ppo_pilot_20260923_r1/ppo_final.zip`，SHA256 `ce225502656d7deac9d0d605cae3ce8e1b19c9e900c2bdf59402fdd6bec01379`；配套 train-only normalizer 为同目录 `vecnormalize_train_only.pkl`。

额外使用 `tools/audit_canonical48_reconstruction_20260923.py` 审计全部四条评估，15项/条检查全部通过：最终arguments除output/menagerie/model外一致，scene、controller配置、dt、模型nq/nv/nu、CCD、physical_panels、contact_names、初始overlap、lift配置等一致；panel配置仅显式增加恢复高度。`RECONSTRUCTION_AUDIT.json` 仍明确历史raw source为contact45，后经数据转换为canonical48，历史完整WBC/safety/solver配置不可从归档恢复，因此不宣称历史动态等价。

精简证据另存 `docs/evidence/canonical48_20260923/`，包括 COMPLETE、ZERO_PARITY、RECONSTRUCTION_AUDIT 与 manifest。下一阶段需要先审查rod失败接触和训练信号，再扩大 train fixture/四场景覆盖、预算与多 seed；本次小预算结果不支持 RL 与 ESN 的性能排名。

复跑须使用新输出目录（已有目录会拒绝覆盖）：

```bash
/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python tools/run_canonical48_ppo_20260923.py \
  --output outputs/canonical48_ppo_pilot_new_run --steps 640 --device cuda
```

从 benchmark 根目录运行时，项目的独立环境实际路径为 `/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python`；CUDA需要正常设备访问权限。
