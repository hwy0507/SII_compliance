# 有限history89实际续训；冻结88继续

2026-10-30 UTC，Goal active。根据完整88的全回放/奖励、loss/health、全90训练配对和固定87终端all5证据，本轮独立登记并实际启动唯一有限89；不是自动无限续训，不是新的history架构修改。完整89、reward稳定、最终loss健康仍待。采用仓库sii-research-sync，无子agent。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；Python `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。上一完整88及冻结启动交接：[RL_COMPLETE88_FROZEN88_20261030.md](RL_COMPLETE88_FROZEN88_20261030.md)。

## 决定及恢复

登记/driver `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_continuation_20261030_v1`；三路活动run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle89_20261030_v1`。`SCIENTIFIC_DECISION.json`绑定完整88审查与实际图、loss/health、固定87终端及87→88全90解释。88平均reward均改善、critic首末1000均值均下降；仍保留A short0900 Task/Strict退化、I critic3及A critic2/3原mask内SSE退化、非零soft-bound诊断、actor漂移与全部loss尖峰。不能把一个周期改善当收敛，也不能把训练变化归因于history修订。

唯一改变是从完整88恢复后再运行一个89周期。每方法全部30条件×最多55s、最多41250新transition与更新；batch65536/UTD1、4m append-only、terminal128、原LR/reward/masks、23/47历史标记、actor49/canonical48、物理/MJB/gates/filter/执行器限制/dt5e-5保持。history critic/replay维度51沿用88，历史列50为preaction累计外部穿透p/(p+0.0002)，clock49；直接恢复已学习历史列及Adam状态，不再次零列迁移、不导入离线拟合权重。

三方法全部完整learner/replay/RNG准确恢复，84个协议/父checkpoint/浮点LR负例拒绝；每方法两次原生batch65536副本更新可精确重复，全state与replay恢复，checkpoint hash不变，总6次可丢弃更新/0physics/0正式更新。生成trainer与实际88 trainer逐字比较，仅原两处migrate_parent恢复改为load_state_dict，其余科学循环相同。`driver.py.diff`已按最终源重新生成。完整新launch gate强制所有证据/hash/原进程身份，训练单次派发，不自动90或Direct34。

## 实际89启动和监视

三路PID `{'impedance': 3433021, 'admittance': 3433022, 'vmc': 3433023}`；GPU1/2/3，learner CPU13/26/39，原每组12核/30物理sampler。新只读消费者 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_review_20261030_v1`。startup对真实新增快照核验原完整88全部51维回放字段、全旧cycles/markers、30MJB、CPU、原优化器超参，以及新current/next历史、观测/clock、动作映射和reward。旧历史列直接对完整88逐位比较；未错误使用87 sidecar长度或再次剥除历史列。

启动审查：`{'impedance': {'total': 3648698, 'added': 1000, 'retained': 3647698, 'reward_error': 0.0}, 'admittance': {'total': 3651000, 'added': 1000, 'retained': 3650000, 'reward_error': 0.0}, 'vmc': {'total': 3653000, 'added': 2000, 'retained': 3651000, 'reward_error': 0.0}}`。三路新reward重构最大误差0，启动快照是部分回合，终端覆盖仍由完整审查负责。实际观察120.042秒/13样本/99原进程身份保持，三方法steps均增加。保存时总steps `{'impedance': 3652305, 'admittance': 3654609, 'vmc': 3655743}`，不等于完整89。

archive监视PID `3433024` 等待原训练在唯一完整周期边界正常结束，最长14400s；静态归档目标 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle89_archive_20261030_v1`，完整审查 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle89_review_20261030_v1`。随后全51维回放/奖励映射、health及全部41250 loss复算自动运行，图生成后必须实际查看。health源码与88逐字相同；loss步号基线用完整88rows（历史87 binding rows+41250），无串联轮号替换。任何失败保留，不自动延长/重跑训练。

## 原冻结88与剩余科学目标

原冻结run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1`，三evaluator/collector/后处理身份保持，未重启。保存进度 `{'impedance': {'completed': 3, 'condition': 'passive_corner_train_0300', 'actions': 600}, 'admittance': {'completed': 3, 'condition': 'passive_corner_train_0300', 'actions': 1000}, 'vmc': {'completed': 3, 'condition': 'passive_corner_train_0300', 'actions': 600}}`。全部30×3训练条件、固定seed2026102638、0更新的完整结果、最终全learner/replay不变、raw审计和82→88全90配对仍待；前两条件失败不隐去。原后处理 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_frozen_postprocess_20261030_v1` 继续按原deadline等待，无新预算。冻结矩阵是开发同seed评测，非独立训练seed或held-out泛化。

原88—90同history统计方案已登记，但仅88完成、89运行、90未派发；完整89先审再明确决定下一有限阶段，不跨架构拼接旧窗口。Direct33数值阶段接受，冻结30 Task/Strict0/0；Direct28中断缺最终内存不变证明仍披露，不为了GPU负载重启Direct。指定ESN缺失、未替代他主机模型。partial75、74—76不可判、79安全中止、旧稳定性失败（含85—87）、半std失败、所有历史软件失败保留。

## GPU与持久化

用户明确要求科学任务全部结束仍继续GPU保载。原v7 supervisor97370/四worker继续，阈值50%、控制目标70%，不随有限训练结束停止，也不创建STOP。此次172样本，各卡最低 `[75, 65, 65, 69]`%、低于50样本 `[0, 0, 0, 0]`，末值 `[80, 93, 93, 94]`%；包含合成守护，不能作为科研吞吐或瞬时保证。历史v7预热0及v6 31/33/44低谷全部保留。当前守护不等于重启后自启服务。

开工及启动前实际query/fetch/read main `aac53b19e38573a5d7dec84f24ffa0d5e80f5620`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关协议变更。小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY89_ONLINE_20261030/SMALL_EVIDENCE.tar.gz`，105成员/154362字节/SHA256 `4fd6d62ed8560cd1bc795ccdf627afcbcb306581affbb3cede560ba033c60cdf`，tar逐成员及Python AST已核；Git index/commit逐字校验、正常push及实际远端确认后另写包外PUBLICATION。大checkpoint/轨迹仍共享SSD，HDD仅原位更新已有254字节LATEST；不是HDD/arm1完整备份。
