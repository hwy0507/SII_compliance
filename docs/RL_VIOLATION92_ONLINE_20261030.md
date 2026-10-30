# 完整91精确恢复；同52协议有限92实际训练

2026-10-30 UTC。Goal active，尚未达到全部方法reward平稳及loss健康。本轮根据完整91证据单独登记并启动第92轮；每方法只新增一轮、30×55s、最多41,250新transition，不自动93。原第90轮冻结评测及其唯一后处理继续。前序结果：[完整91](RL_COMPLETE91_20261030.md)。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际query/fetch/read main `3a4a5e35ae9b129faede482131cd6dfa470e2346` 和baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，遵循 [sii-research-sync](../skills/sii-research-sync/SKILL.md)，无子agent。新运行源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_continuation_20261030_v1`；消费者 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_review_20261030_v1`；训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle92_20261030_v1`。解释器/库版本、seed、源/MJB hash沿各实际REGISTRATION和EXECUTION，无变更依赖或模型。完整父快照 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle91_archive_20261030_v1/<method>/cycle_00091.pt`。

## 科学决定与验收边界

完整91各30完整55s、0abort，Task/Strict I18/17、A14/13、V17/17。相对90，I reward与固定87终端masked SSE改善，A reward/Strict与终端masked SSE退化，V reward/标签接近且masked SSE改善；loss仍有尖峰、I尾部升高、actor均值漂移。这些混合方向发生在raw violation52启用后的前两个完整在线周期，尚不足以支持再改LR、奖励或架构。选择从所有已学91权重/Adam/replay/RNG再接续一个相同协议的有限92，观察改善/退化是否持续，并补齐原90–92描述性分析所需第三端点。

原90→91 I42.5116%、A20.8292%已违反原5%相邻必要条件，92不能修复这个事实。原PLAN、EARLY_WINDOW_FAILURE_91和全部旧失败保持；不能通过换窗口或删除中止来宣布收敛。V首相邻.09648%仅未违反该条件，仍需完整92/首尾/第二相邻及loss健康证据。当前没有完整92或完整窗口统计。新启动不等于收敛，也不是因GPU占用而无限延长训练。完整92 review/loss/health审查后才能决定下一有限阶段。

## 恢复、接口与启动验证

driver只更新准确完整父91/新92边界与证据绑定；trainer_registered.py与实际91逐字相同。历史plateau修订floor仍90，history首次88、violation首次90；interval消费一次、两架构marker不变。准确父steps I3770950/A3773750/V3774750，用前轮真实steps+实际新增绑定，保留90 I安全中止后的真实行数；不从原89迁移绑定直接加一个周期推算91。

三方法各36负例、共108拒绝通过，覆盖错误周期/partial/seed/steps、预算/自动后续/协议改写、架构marker缺失、旧51维current/next、cursor/capacity/优化器计数及LR。实际batch65536每方法两次可丢弃原生clone更新，共6次；相同batch重复metrics与完整state精确，之后learner及replay RNG恢复，0正式更新/physics，未推广clone权重。原已学history/violation及Adam均保留。

实际startup三路新增步数 `{'impedance': 1000, 'admittance': 1000, 'vmc': 2000}`。全部旧回放52列及其他字段逐位精确保留；新增current/next原始bit、连续history、clock、raw→mixed动作及reward逐条核验，最大reward重建误差 `{'impedance': 0.0, 'admittance': 0.0, 'vmc': 0.0}`。每方法30冻结MJB、30sampler与原CPU配置通过。仅根据原interval journal重建reward，不声称独立动力学重跑。

实际启动后观察 `120.039`秒，99个原进程身份、13样本通过，三路steps增长。保存时steps `{'impedance': 3775686, 'admittance': 3778467, 'vmc': 3779579}`。完整91父state和实际正式INITIAL_STATE_REVIEW分别核验，不能用check-only替代真实启动。

原critic/replay52、actor49/canonical48信息、clock49/history50/rawbit51、terminal128、batch65536、UTD1、原LR/reward/masks、append-only4m replay及23/47历史marker、Adam/RNG不改。冻结物理/MJB、Task/Strict门、filter、执行器限制与dt5e-5不改；所有历史安全中止、partial75、74–76不可评估、halfstd否决和软件失败保留。

startup/full review/archive/loss消费者绑定新92，loss首步为I3770951/A3773751/V3774751，上限分别3812200/3815000/3816000；health算法与91逐字相同。完整结果由唯一archive消费者等待正常FINISHED后复制和hash核验，再执行全回放/所有新reward、health和全loss审计。该消费者有限等待14400秒，不会自动启动93；新完整图仍须实际查看。

## 持续运行与后续

保持本轮三训练进程及唯一archive/review/health/loss消费者；preflight、startup及两分钟observer已经正常完成，不重跑。具体命令、PID/start ticks在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle92_20261030_v1/LAUNCH.json`、MONITOR/STARTUP/OBSERVER_LAUNCH。首先读取这些实际进程与结果，避免重复派发。

原冻结90 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1`，evaluator283421/283428/283430、collector283433及postprocessor292743仍存活，保存完成数 `{'impedance': 14, 'admittance': 14, 'vmc': 13}`。原seed2026102638、0updates、全90及raw/88→90配对仍待；保持原launch+21600秒截止，不延长、不重复派发。本轮未新增冻结91/92。

Direct33数值收敛已接受；冻结33全30 Task/Strict0/0、旧28动作精确但最终内存证明缺失、恢复后2条完整不变性通过均保留。不把任务成功增加为数值收敛要求，不为占用训练Direct34。指定ESN仍缺，不重复询问或替用其他主机模型。接续完整92/原冻结90，原90–92统计在真实输入齐全后按原方案计算，保留已知I/A失败；Goal active。

## GPU与保存

原guard supervisor97370、workers97399–97402持续运行，用户明确要求科研完成后仍保载。threshold50%、target70%、min duty.7、CPU4–6；不创建STOP。守护当前并非重启自启服务。

从本轮科学登记起141样本、跨度713.275秒，四卡最低[77, 66, 67, 68]%、低于50次数[0, 0, 0, 0]，末值[82, 91, 97, 95]%。包含合成保载，不等于纯科研吞吐或每瞬时保证；历史warmup0与旧低谷记录保持。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_ONLINE_20261030/SMALL_EVIDENCE.tar.gz`，122成员、175289字节、SHA256 `276394df3f4e14b4b14feb878628756d5ffadab1d66bfc2495f8314fdaf6baab`，逐tar成员/AST核验。清单 `docs/evidence/RL_VIOLATION92_ONLINE_20261030/MANIFEST.json`；收据 [RL_VIOLATION92_ONLINE_20261030_SAVE.json](RL_VIOLATION92_ONLINE_20261030_SAVE.json)。Git index/commit逐字核验和正常push/实际远端确认记入包外 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_ONLINE_20261030/PUBLICATION.json` 与 `GIT_BYTES_REVIEW.json`。大checkpoint/replay/raw保留共享SSD；HDD配额满，仅原位更新254字节LATEST指针，非HDD/arm1全备份。
