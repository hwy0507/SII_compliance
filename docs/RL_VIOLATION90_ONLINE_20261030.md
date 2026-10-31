# 有限违规位 critic 第90轮实际训练与接续记录

2026-10-30 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；Python `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮从准确完整89的迁移快照，单独登记并实际启动三个方法的有限90。训练尚未收敛；完整90、reward稳定和loss健康仍待。使用仓库 `skills/sii-research-sync/SKILL.md`，无子agent。

## 科学决定与边界

上一交接：[完整89迁移与原生预检](RL_HISTORY89_VIOLATION_PIPELINE_20261030.md)。完整89各30×55s/41250步/无abort，I/A/V Task/Strict为18/17、13/12、17/16；A相对88丢4 Strict与3Task，V丢1 Strict，全部critic末段均值上升。原88→89 A/V相邻reward变化130.492%/63.462%，超过5%必要条件，失败不能被新架构覆盖。

匹配52维零输入对照与因果违规位离线拟合总masked loss改善约53.4%/.83%/1.52%，但Icritic0/Acritic1变差、A/V尖峰仍在。仅据这些有限证据和全部恢复检查，登记一个在线90试验；没有导入离线拟合权重、没有宣称架构最终接受或收敛。完整科学决定与证据hash在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_online_20261030_v1/SCIENTIFIC_DECISION.json`。

新critic/replay52，actor49、canonical48保持；clock49、历史50、违规bit51。bit来自动作前raw累计外穿透严格大于0.0002m；历史仍为p/(p+0.0002)。保留原已学history列、Adam、两种架构marker、完整回放/RNG、23/47容量标记。沿用先计算原51+action点积再加bit贡献的数值布局；不是原先已拒绝的dense插零列布局，也不宣称与离线dense拟合轨迹相同。

每方法唯一30条件×最多55s、最多41250新动作/更新；4m append-only、terminal128、batch65536/UTD1、原LR/reward/masks/Imin+A-Vmean/actor min保持。冻结物理/MJB、Task/Strict、filter、执行器限制、dt5e-5保持。只登记90，无自动91/92或Direct34。

原88—90方案和失败证据全部保留，新增 `runs/parameter_history88_90_reward_stability_20261030_v1/REVISION_BOUNDARY_90.json`。I原同修订三轮窗口未完整，不能将新52维90与旧51维88/89混合。新90—92同修订窗口已在训练前登记，5%/nearzero1/5000 bootstrap/seed2026102861/anchor55不变；这里只是统计方案，不授权91/92训练，未计算不完整全窗口统计。

## 预检、启动与消费者

在线代码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_online_20261030_v1`，run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle90_20261030_v1`，只读消费者 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_review_20261030_v1`。三方法共93个错误协议/父状态/marker/维度/LR负例拒绝；全部准确完整learner/replay恢复，每方法两次batch65536原生clone更新可逐字重复并恢复，共6次已丢弃更新、0预检物理/正式更新。正式trainer以实际89源码为基础，仅增加bit amendment保存及plateau修订起点88→90；逆变换源码逐字相同，interval消费恰一次。历史migration amendment的preparation-only字段描述原迁移来源，新的在线权限和预算由独立90 continuation决定。

第一版注册脚本误引用不存在的重复PLOT_INSPECTION路径，在创建登记前失败；准确失败源码 `register90_initial.py.txt` 和 `REGISTRATION_INPUT_FAILURE.json`保留。删除这项冗余错误引用后注册成功；真正89的图检查仍绑定，不修改已登记计划或科学证据。

三路训练PID `{'impedance': 1096445, 'admittance': 1096447, 'vmc': 1096449}`，GPU1/2/3，learner CPU13/26/39、各30 sampler共享原12核。实际startup对全旧52维回放前缀、双marker、旧cycle history、优化器超参、30MJB/CPU、新current/next52观测/clock/history/raw bit/动作/奖励进行检查。结果 `{'impedance': {'steps': 3689948, 'added': 1000, 'retained': 3688948, 'reward_error': 0.0}, 'admittance': {'steps': 3692250, 'added': 1000, 'retained': 3691250, 'reward_error': 0.0}, 'vmc': {'steps': 3694250, 'added': 2000, 'retained': 3692250, 'reward_error': 0.0}}`。新奖励重构误差0；这是部分回合快照，终端由完整消费者另审。另对这些已保存实际startup快照检查：每方法全部10个online/target critic的bit列、5个在线critic的Adam一/二阶矩均有限且非零；只证明新列实际参与了学习，不代表性能改善。

启动后120.041秒/13观察，99个进程身份保持，三方法步数均增加。保存时总steps `{'impedance': 3693373, 'admittance': 3695763, 'vmc': 3696815}`。archive监视PID `1096452`，最长14400s，等待原唯一完整90边界后归档并运行full review/health/loss。完整检查包含全部新current/next52及terminal raw bit、奖励、旧前缀和30条件。loss步号以完整89 bit binding rows为基准，实际连续长度≤41250，保留abort短回合，不硬写满预算。

health用violation_class(history_class(PublishedLearner))恢复双marker，检查实际90 execution/protocol hash；不拿只允许原89元数据的preparation validator验证已训练90。原unprojected固定minimum-pair TD诊断语义不变，仍不等同线上投影或A/V mean目标。完整90消费者已部署但尚未完成，生成图必须实际查看后才解释结果。

## 原冻结任务与其余目标

原冻结88 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1` 三evaluator/collector/后处理保持原身份和21600s截止，未重启/延长。当前 `{'impedance': {'completed': 25, 'condition': 'active_long_train_0400', 'actions': 1300}, 'admittance': {'completed': 25, 'condition': 'active_long_train_0400', 'actions': 200}, 'vmc': {'completed': 24, 'condition': 'active_long_train_0337', 'actions': 1200}}`，完整90回合结果、全state不变、raw复算及82→88配对仍待。固定seed2026102638，0更新；属于训练条件开发评估，不是held-out泛化或独立训练seed。

Direct33数值阶段接受，冻结33全30 Task/Strict0/0；Direct28缺最终内存不变证明仍披露。指定ESN仍不可用，不替代其他主机模型。partial75、74—76不可判、79安全abort、所有旧稳定性失败/halfstd拒绝和软件失败保留。Goal仍active。

## GPU守护与持久化

按用户明确要求，即使科学任务全部完成也保持GPU保载。原v7 supervisor97370及worker97399–97402继续，阈值50%、目标70%；没有STOP，也不与有限科学任务同停。本轮162样本，各卡最低[78, 68, 66, 68]%，低于50样本[0, 0, 0, 0]，末值[81, 95, 93, 95]%。这些数值包含合成守护，不能称为科学吞吐或所有瞬时保证。原v7预热0及v6低谷31/33/44仍保留；守护不是重启后自动服务。

已实际query/fetch/read main `ef82273834a43c4c37bc8f31c4eeb1cca8889275` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关冻结协议变化。小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION90_ONLINE_20261030/SMALL_EVIDENCE.tar.gz`：136成员/223767字节/SHA256 `477cbcc2ce1028407c662764c6293602849bcd79b73f7845a9e782ad9e560686`，全部tar成员和Python AST已验证；Git index/commit核验、正常push和实际远端确认后另写包外PUBLICATION。大checkpoint/轨迹仍共享SSD，HDD配额满仅原位更新已有254字节指针，不是HDD/arm1完整备份。
