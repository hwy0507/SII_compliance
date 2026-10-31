# 第94轮全条件比较与终端缓存增长审查准备

原第94轮三路在线训练继续，仍未收敛。本轮没有改训练源码或重启作业。实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`；开工query/fetch/read main `414944fe9b270dfa5664de38f2da96952df365e0`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新RL更新。继续仓库sii-research-sync流程，非RL工作保持。

## 全90条件93→94描述比较

源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census94_comparison_20261031_v1`，COMPARISON_PLAN/WAIT_PLAN绑定真实完整93 review/health/loss/实际图、三份94注册与STABILITY_WINDOW_INTENT。完整93原90 rollout标签/模型hash/冻结条件/逐回合reward分项/全部均值和Task/Strict计数已经复核；完整93 Task/Strict为I17/16、A15/14、V17/16。对真实缺少完整94输入的前置拒绝通过，脚本AST和差异已核验。

唯一等待器PID2051280/start196679638，原archive截止1793438307.1910293；CPU10，每脚本最多600s。完整94归档、回放/health/loss审查结束后，interpret94.py比较全部3×30 reward/分项/Task/Strict/abort/原始抽样loss，changed_cases.py绑定所有Task/Strict变化的两轮rollout摘要、穿透及同一model hash；保存结果独立重算汇总，图须后续实际查看。

94的agent_train/q_loss为条件估计器，原健康口径使用original_sampled_q_loss，93则为其原q_loss，条件估计另列。actor两轮也分别列出。注册比较只允许新增census amendment与单轮接续字段，其余科学协议必须相同；新amendment精确绑定。本消费者无physics/optimizer更新，不改变正式权重，不把两轮描述差当因果改善或首次94–96稳定性证明。**完整94结果尚无**。

## 终端缓存总数对齐

check_terminal_population.py绑定全部旧93终端indices/masks和94注册。原trainer先replay.add/cache.sync再同step update；检查每个更新的terminal_population必须等于旧终端数加包含本步的done累计。first5000三路实际日志逐字回读精确，旧总数2785/2784/2784，新增done均0；15个缺更新/错步/错总数/遗漏终端增长/错父总数损坏输入被拒绝。

完整94后需要运行 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census94_comparison_20261031_v1/check_terminal_population.py --complete`。它要求完整review/checkpoint，严格census-aware元数据校验，全94日志和回放done精确，旧终端indices/masks保持、每方法30终端条件均覆盖、逐步总数匹配，并报告存档32个mask分层总数。**前缀无新终端，不证明真实增长；在线每分层tensor内容未日志化，不能把存档派生分层计数称作在线逐分层观察。**完整检查尚未运行，不改原archive消费者。

## 当前训练与续接

原101身份连续600.436s/61样本保持，三路增长{'impedance': 5185, 'admittance': 5174, 'vmc': 5263}；保存总steps{'impedance': 3870872, 'admittance': 3874369, 'vmc': 3875631}，完成条件{'impedance': 0, 'admittance': 0, 'vmc': 0}。原三正式/90sampler/archive、固定全部8353终端等待器1895688与本轮全90等待器继续。下一步等待完整94，再完成所有实际图/保存算术/真实缓存增长/两种比较，依据结果单独决定95；无自动95或Direct34。

固定94–96统计意向5%/nearzero1/5000bootstrap/seed2026102861保持，登记在94已启动、首完整回合返回前；实际统计输入绑定仍待，95/96仍需各自有限科学审查登记。历史90–92失败、92→93不稳定、I93后续终端退化和所有旧失败保持，原前5000 I16.365尖峰/actor上移不消失。Direct33原数值验收、冻结0/0与旧28证据限制、指定ESN缺失保持；Goal active。

若中断，保全最新94 partial检查点/Adam/RNG/replay/journal，另登记census-aware partial恢复；不回退93或重跑整轮94，物理state未保存。NEXT_REVIEW_NOTES明确后续命令与原作业身份。

## GPU和交接

独立guard `/tmp/sii_gpu_util_guard_20261031_recovery_v1` 保留，科学结束继续，不创建STOP，不是系统重启服务。当前窗口124样本/627.772s，最低[75, 70, 69, 70]%、低于50[0, 0, 0, 0]，末值[78, 95, 92, 95]%；含synthetic guard，不等于科学吞吐或每瞬时保证，旧主机切换0%不抹除。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS94_COMPARISON_20261031/SMALL_EVIDENCE.tar.gz`，38成员/44570字节，SHA256 `7c73f89265538544d87d755418059477d32ffeb99209db3c9812601ce9e19676`，逐成员字节及AST/JSON核验；原始.diff上下文空格保留。提交字节/实际远端收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS94_COMPARISON_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满仅原LATEST254字节原地更新，大checkpoint/replay/raw仍共享SSD，不是HDD/arm1全备份。
