# 精确完整90接续有限91；原冻结90继续

2026-10-30 UTC，Goal active。完整90 review/loss/health、全部89→90对照及固定87终端诊断已审；本轮单独登记并启动同52修订的有限91，不自动92，不启动Direct34。原冻结90评测/collector/postprocessor保持原身份运行，最终全90/raw/88→90配对仍待。前序[完整90与冻结90](RL_COMPLETE90_FROZEN90_20261030.md)。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。实际query/fetch/read main `697d2d5b4cf14ae6e545e5479c5a547547542b47` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关科学协议变化；采用sii-research-sync，无子agent。新driver及登记源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation91_continuation_20261030_v1`，消费者 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation91_review_20261030_v1`，实际训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle91_20261030_v1`。完整父checkpoint均来自 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle90_archive_20261030_v1/<method>/cycle_00090.pt`，不回退原89迁移快照、不重新初始化。

科学依据：90 critic尾部均值下降，但I后段尖峰/actor漂移；固定旧终端总masked SSE I改善83.45%、A退化9.70%、V退化146.79%，全部critic退化保留。A/V在线标签恢复部分成功，而I long0000在35.08s发生全局物体/角台穿透安全中止，外部bit0并不覆盖该事件。该混合证据未证明收敛或架构全面有效；单独再运行一个同52/原目标周期，以检查改善和退化的持续性，减少再次改变算法造成的解释混淆。原失败/安全门不修改，无离线权重晋升。完整91审查前不得自动92；90—92统计预登记本身不授权训练。

新driver恢复准确已学90，不再调用只接受迁移89的validate_migrated。注册元数据只变有限continuation，所有科学/历史协议与实际90相同；trainer_registered.py与实际90源码逐字相同，interval消费一次、plateau修订floor仍90、两架构持久字段保留。完整parent的learner/replay/RNG/optimizer/history精确恢复，真实I rows3729700、A3732500、V3733500；I40752新步及安全中止保留，不假定它有41250。两marker、52维、4m append、23/47历史容量、原clock/history/bit、全历史cycles及partial75排除保持。

三方法各36负例，共108拒绝：周期/预算/自动后续/超参/协议变更、错误父身份/partial/seed/steps、缺marker、51维旧current/next、cursor/capacity/优化器计数及错误violation amendment。全部真实父通过；实际batch65536各2次可丢弃clone更新，共6次，重复metrics/完整state精确，随后learner/replay RNG原状态恢复，0正式更新/物理、无clone权重推广。保存check-only精确digest及正式启动INITIAL_STATE_REVIEW。

新startup/full review/health/loss/archive消费者沿原实现。health91算法与health90逐字相同；loss首步由准确完整90 review.steps绑定，I3729701/A3732501/V3733501开始，避免以原89 binding或假定完整41250算错中止后的边界。新archive只消费完整91，保留全部终端/原masks、实际中止长度；完整loss/health仍待。

实际启动全旧回放所有52列/其他字段逐位保留，三方法startup新增 `{'impedance': 1000, 'admittance': 1000, 'vmc': 2000}`；新current/next raw bit、连续history、clock、action和reward逐条核验，reward最大误差 `{'impedance': 0.0, 'admittance': 0.0, 'vmc': 0.0}`。每方法30冻结MJB/30sampler/learner原CPU组、batch65536/UTD1/terminal128/原LR、4m markers与历史保持。120秒观察实际 `120.129s`、99身份、13样本通过，总steps `{'impedance': 3734112, 'admittance': 3736866, 'vmc': 3737781}`。

固定物理/MJB/Task/Strict/filter/执行器/dt5e−5、actor49/canonical48不变。每方法仅30×55s/最多41250新transition，critic/replay52、clock49/history50/rawbit51不变；同修订window只有完整90，尚无完整91/92，未跑缺失窗口统计。91早期进度不是reward稳定/loss健康结论。旧88—90失败、partial75、74—76不可判、79/90安全中止、半std拒绝、全部软件失败保持。

原冻结90仍 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1`，evaluator283421/283428/283430、collector283433、postprocessor292743保持原身份；保存完成数 `{'impedance': 2, 'admittance': 2, 'vmc': 2}`，不重启、不扩展原21600s截止。Direct原数值阶段已接受，冻结33全30 Task/Strict0/0和原28最终内存证明缺失保持；指定ESN仍缺，不替用其他主机模型。

原GPU guard97370及97399–97402继续，科研完成后仍保载。本轮135采样/683.6s，最低[69, 68, 69, 65]%、低于50[0, 0, 0, 0]、末值[74, 91, 97, 94]%；含合成负载，不等于科学吞吐或每瞬时保证。历史v7 warmup0/v6低谷保留，非重启自启服务。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION91_ONLINE_20261030/SMALL_EVIDENCE.tar.gz`，122成员/169741字节/SHA256 `922a8c7353854b1e96de848686be1ceb0dfdfa35f00dcb748090c3e44d09c7ca`，逐tar成员/AST核验。Git index/commit逐字及正常push/实际远端确认后写包外PUBLICATION。大checkpoint/raw仍共享SSD；HDD仅原位254字节指针，非HDD/arm1全备份。

接续：保持原91、唯一archive/完整review/health/loss消费者及原冻结90；完整91与90→91差异到齐后再决定下一有限阶段，并继续原90—92稳定性方案的实际输入绑定，不把新阶段启动当作收敛。
