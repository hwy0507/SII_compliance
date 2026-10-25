# 服务器 agent 接手入口：项目背景、RL 训练与五卡并行

2026-10-25。**先读本页，再读 [reward 与训练协议](RL_SPT_TRAINING_HANDOFF_20261025.md)。**
用户要求的是把方案、代码和交接发布到 GitHub，由服务器上的 agent 执行。
本次发布者没有连接服务器、没有检查其实际硬件，也没有启动本轮训练。
服务器地址无须提供给发布者；路径、Python/CUDA 环境和设备编号由接手 agent 在当地确认。

## 项目在做什么

研究 FR3 机械臂在人机交互、外部扰动和接触过程中完成搬运/放置任务的柔顺控制。
目标是人受到的冲击小、机器不超出安全约束、任务完成且尽量快。
MuJoCo 的统一 office 场景包含人体/物体扰动；不能只跟踪参考轨迹而不完成实际任务。

主要方法包括 ESN（固定 reservoir、学习读出，用时序信息产生控制输出）、其他神经网络、
经典阻抗/导纳/VMC，以及本轮四类在线 RL。ESN 使用采集的控制数据学习；本轮 RL 使用
真实仿真交互从头训练，不使用 teacher action、BC 或旧 replay。最终需要在相同未见条件上
比较，**不预设 ESN 优于 RL，也不为了让某个方法获胜而改变指标。**

自 10 月 25 日起，[正式评估标准](EVALUATION_STANDARD_SPT_20261025.md) 已改变：
Task/Strict success rate、**SPT**、峰值广义力矩、实际人体交互期间的舒适力矩合规比例，
另报机器安全违规。SPT 采用成功加权完成时间，SPL 不再是主效率指标。
reward/loss 是学习诊断；低 reward 方差、低力矩或跟踪误差小，都不能替代任务成功。

历史状态见 [真实训练快照](RL_SNAPSHOT_20261025.md)：旧训练只有短末段稳定证据，
不足以认定四方法都已学习收敛；旧图、旧 checkpoint 和旧测试结论不得标成新训练结果。
用户认可 baseline 最后 reward 学习后趋稳而任务效果仍不好；必须区分“学习后稳定”和
“从头没有改善的停滞”。新目标要求更充分的训练预算及可核查的学习曲线。

## 本轮该跑什么

| 接口 | 学习输出 | 比较约束 |
|---|---|---|
| direct | 原 action7 | canonical48 输入、公共动作滤波和执行器限制 |
| impedance | 在线阻抗参数 | 同一 canonical48、冻结参数映射/先验 |
| admittance | 在线导纳参数 | 同上 |
| vmc | 在线 VMC 参数 | 同上 |

四方法统一使用新 `spt_v1` reward：任务进度及尽早推进、人体接触负载、峰值力矩、穿透、
实际力矩变化，以及 Task AND Strict 终奖。公式、量纲、权重、早退处理在 reward 交接页。
算法为 pinned 官方 SimbaV2；单步 TD、UTD=1、同一 batch 与优化器日程。**每方法每 seed
最多 1,000,000 真实交互步，建议 3 seeds，共 12 个独立实验。** 不是把总百万步平分给四方法。
seed 为 20261025、20261026、20261027；同 seed 的方法使用相同条件排序。

物理/MJB、dt=5e-5、55秒完整安全审计窗口、Task/Strict gate、canonical48、公共 filter、
执行器限制继续冻结。禁止用降低仿真精度、加入特权 actor 输入或放宽成功门来加速/制造成功。
参数控制器的结构性先验须披露；这四路是控制接口比较，不是参数量完全匹配的架构消融。

## 资源授权与并行策略

用户明确提供 **5 张 RTX 4090、55 核 CPU** 并要求多跑并行。
这是新授权，覆盖历史文档“仅本机计算、服务器仅归档”的限制，**不需要为服务器训练再次询问许可**。
旧批次的资源收据不修改；新 run 在服务器登记实际硬件、解释器、设备 UUID 和 hash。

先对一组完成回合和至少一次实际 learner update 做资源/正确性检查，再扩大到五路。
建议第一批 GPU0/1/2/3 分别跑 direct/impedance/admittance/vmc 的首个 seed，GPU4 跑
direct 的第二 seed；每张卡有串行待办队列，空出后接下一 seed。12 个任务全部报告，不能只挑最好 seed。

发布的 `run_spt_server_parallel_20261025.py` 实现最多五路、一卡一 learner；每路绑定互不重叠
CPU 集，内含一个单线程 MuJoCo worker。初始每路8 GiB主机内存硬上限、禁swap，启动时对
全部活动作业尚未使用的内存额度作预留并保留4 GiB主机余量。不知道服务器内存容量，故不能
仅凭55核就声称能开满五路。内存不足会保留失败并停新派发，调整登记后重新准备独立 run。
JAX 限定 CUDA_VISIBLE_DEVICES 到 GPU UUID；实际后端不是GPU就报错，不能静默退回CPU。
显存分配比例0.8只是 JAX 分配器设置，**不是总显存硬隔离**；仍须看 nvidia-smi。

并行的是独立算法/seed，不是五卡分布式训练同一策略，也不是单策略多环境采样。
55核不应转成每个 BLAS 55线程：当前小网络和串行物理不一定受益。先记录完整回合的
steps/s、updates/s、物理/学习/写盘时间、峰值RAM/显存、GPU温度和利用率，再比较1路/5路吞吐。
若仍受CPU仿真或写盘限制，接手 agent 可继续实现并登记多采样器/批量推理，核对回合边界、
replay、UTD、真实样本数和确定性审计后扩大并发；不能只删锁开更多重复进程。
五路是本入口初始实现上限，不是用户要求永久限制算力。

本入口每回合保存完整 replay/checkpoint 和物理记录；百万步时不能按小试验的磁盘量估算。
仅约百万条float32 replay本身就约0.4 GB，约727个回合末全部留存会产生大量重复数据。
先用预检实测压缩大小，外推12路总存储和写盘时间，登记归档/保留策略；20 GiB剩余磁盘保护
只是停止派发下限，不表示足够完成百万步。不得删除未归档核验的唯一续训状态或失败证据。

## 当地准备：环境与必需产物

在服务器 checkout 本次 `main`；按根 AGENTS 读两分支更新日志，检查现有服务、进程、
GPU占用和 execution，不能覆盖其他 agent 的作业。现有资源锁只协调同用户、同主机、遵守本入口
的任务；GPU准入也检查其他计算进程。跨用户作业需遵守服务器当地调度器的分配。
需要 Linux cgroup v2 和可用的 `systemd-run --user`；队列跨SSH会话存活应使用当地已有的持久
会话/服务，先确认 user manager 不会随登出终止。不要修改显示驱动/Xorg来运行训练。

使用服务器现有、版本登记的 Python 环境，需要 NumPy、MuJoCo、Gymnasium、JAX CUDA、
Flax、OmegaConf 和 pinned SimbaV2 依赖。不要复制本机虚拟环境路径到服务器、不要静默升级
JAX/Flax；实际 `jax.devices()`、CUDA/驱动/Python与包版本必须写入资源预检报告。

Git 不包含所有历史大产物。接手者在服务器找到/按来源取得下列输入后传给脚本：

| 参数 | 内容与校验 |
|---|---|
| `--parent` | 历史 `rl_tuned_20261015_v4` 的 PROTOCOL、CONDITIONS、teacher.json；只复用环境/条件，不复用旧 reward |
| `--parameter-source` | 该批次 `parameter_fullrange`，含 PRIORS、official_parameter_agent.py 及控制器模块 |
| `--runtime` | 含 v6/、menagerie/、SimbaV2/、simba_reward_20260930/ 的公共运行时 |

原始已知来源为发布者本机 benchmark 的 `outputs/rl_tuned_20261015_v4/` 与
`outputs/baseline_local_rl_20261009/runtime/`，**不是已核验的服务器路径**。
缺输入时先核对当地历史归档；不得伪造下载地址、重新生成不同模型冒充原产物。
关键旧输入 SHA256：

```text
parent/PROTOCOL.json       61d379a9e514d99f59fb5f5262b9e7b0770ee0c8baabb3b413f4d93a746fa9db
parent/CONDITIONS.json     591d2e71a4c0fde428292ed70b479574ea87700eff04ded4826e2de2aee407a4
parent/teacher.json        294c6461957cadcc934616375635c82df4dc99cd2e46f1ec4a4513d9b805f317
parameter/PRIORS.json      36a510b0f700cffa539eab8ef272c6c7d7fabda134b458c149730a8f6592eb37
v6/construction/rollout.mjb 173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11
SimbaV2 Git commit         86899c277cdc697b2b02d827243de1ea93f20a1d
```

准备器只在新快照里重定位 adapter 的 UPSTREAM 路径，并登记前后 hash；不修改历史 adapter，
也不改变算法实现。原有 schema 兼容物理 worker；新增字段明确标识 spt_surrogate_v1。

## 启动入口

以下变量由服务器 agent 填为当地**真实绝对路径**；这里的占位路径不代表任何服务器已存在。
CPU编号先看 `os.sched_getaffinity(0)`/当地CPU分配，示例用0..19，不假定55核一定编号0..54。

```bash
cd /ACTUAL/CHECKOUT/SII_compliance/code/mujoco_6d_vmc_benchmark
SII_PY=/ACTUAL/VENV/bin/python
SPT_PARENT=/ACTUAL/ARCHIVE/rl_tuned_20261015_v4
SPT_PARAMETER="$SPT_PARENT/parameter_fullrange"
SPT_RUNTIME=/ACTUAL/RUNTIME
SPT_RUN=/ACTUAL/NEW_RUNS/rl_spt_server_20261025_v1

"$SII_PY" tools/prepare_rl_spt_campaign_20261025.py matrix \
  --root "$SPT_RUN" --parent "$SPT_PARENT" --parameter-source "$SPT_PARAMETER" \
  --runtime "$SPT_RUNTIME" --gpu-devices 0,1,2,3,4 \
  --cpu-lanes '0,1,2,3;4,5,6,7;8,9,10,11;12,13,14,15;16,17,18,19' \
  --memory-gib 8 --seeds 20261025,20261026,20261027 --steps 1000000 --dispatch-hours 72

"$SII_PY" tools/run_spt_server_parallel_20261025.py \
  --jobs "$SPT_RUN/PILOT_JOBS.json" --receipt "$SPT_RUN/pilot_batch.json" --dry-run
```

`matrix` 只准备12个独立快照和队列，没有训练；`--dry-run` 只打印。先单独跑首路预检：

```bash
"$SII_PY" tools/prepare_rl_spt_campaign_20261025.py run \
  --root "$SPT_RUN/direct_seed20261025" --family direct --stop-at-step 1375
```

1375步是完整55秒，仍在5000步探索预热内，**不能据此说梯度训练通过**。接着在新的阶段队列中
给此路指定真实已保存 checkpoint，推进到11000步，检查 optimizer 更新、实际GPU后端、原始
telemetry、奖励重放、动作/物理一致性和RAM/显存。不得改变固定百万步优化器日程。

首路通过后，从 PILOT_JOBS 派生新的 JSON 队列，排除已完成首路（不可再启动同一片段），
用新 receipt 跑其余预检，去掉 `--dry-run` 即可。每个队列元素的格式：

```json
{
  "root": "/ACTUAL/NEW_RUNS/rl_spt_server_20261025_v1/impedance_seed20261025",
  "family": "impedance",
  "stop_at_step": 11000,
  "resume_checkpoint": "/ACTUAL/NEW_RUNS/rl_spt_server_20261025_v1/impedance_seed20261025/impedance/segment_0001375/checkpoint_0001375"
}
```

文件最外层是数组。新的从头预检元素不带 resume_checkpoint；续训必须取 execution 中的
真实末 checkpoint，不猜早退情况下的步数。按11k→55k→110k→250k→500k→1M分段，
每阶段新的 jobs JSON 和 receipt，避免把未审查预检自动接成百万步训练。
一旦任务失败/未到段预算，协调器停新派发，收完在途；接手 agent 留下原因、诊断修复后新建
有限续接协议，不能只停在那里不处理，也不能无条件重试覆盖失败。

## 接手者必须交回什么

每路记录实际交互步/更新数/完整回合、checkpoint hash、reward各项、actor/critic loss、
temperature、回合条件和 Task/Strict。画完整历史和按相同条件配对的趋势；注明平滑窗口，
保留原始点、源日志路径/hash，不能只画最后几个好看的回合。
记录每阶段资源实测、并发数和吞吐，而不是用 systemd active 或 GPU 占用冒充训练进展。

训练稳定性按 reward交接页判断，任务差也如实报告；平坦停滞要查实现/探索/尺度，不强行称收敛。
当前正式SPT还缺 gate一致的完成时刻、冻结 T_ref，以及人体舒适阈值标定。训练使用工程代理，
不得据它输出正式SPT/舒适率；最终测试前先补齐评估。旧24条件已看过，不能再次称全新未见组。
四方法训练完成后冻结模型，同新保留组的ESN比较，做独立物理子步、actor/filter和hash审计。
按 AGENTS 更新根日志和进展，提交/push main；大型数据存当地独立run目录，并提供实际地址与hash。

本次代码仅通过本机单元/契约测试和命令预检，**服务器CUDA、五卡并发与新MuJoCo回合尚未实测**。
