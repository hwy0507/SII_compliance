# 第96轮全90比较、终端计数与完整95窗口输入

第96轮原三路训练继续；本轮零新增科学训练派发，诊断零physics/optimizer更新。原learner/90sampler/guard没有重启，Goal active；完整96与reward平稳/原loss健康的联合验收仍待。

## 全部90个条件的比较准备

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census96_comparison_20261031_v1/COMPARISON_PLAN.json` 绑定完整95全部review/health/loss/真实图检查、三份96协议、原94–96意向及A早期失败、修正版archive来源。完整95的90条实际rollout成功标签、abort、stage、模型hash、冻结条件和reward分项算术/均值/总数已核验，Task/Strict为I18/17、A15/15、V17/17。96协议相对95只允许post_interruption_continuation变化，census amendment完全相同。

缺真实完整96的检查正确拒绝。唯一等待器PID882729/start198009523，绑定修正版archive PID33045/start197863908，截止1793451215.3429887沿原96启动+14400秒，不延长原截止。完整96 REVIEW/health/loss/FINISHED通过后：interpret96.py覆盖全部90个条件reward与分项、Task/Strict/abort和原抽样/条件估计/actor loss；changed_cases.py核验全部标签变化的原两轮rollout、穿透与模型hash；保存汇总独立复算后生成图。每消费者600秒上限，最终图仍需实际查看。

完整比较尚未运行，不是96结果。两轮估计器相同，原loss健康均读取original_sampled_q_loss；reward分项差值只是算术分解，不是因果证明或固定94–96稳定性结论。

## 终端计数与真实日志绑定

基准为完整95全部8533终端indices/masks（I2845/A2844/V2844），来自 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census96_fixed95_terminal_20261031_v1/reference95`。真实96 first5000的每一步terminal_population与父总数加包含当前步的done累计相等，原日志前缀再次读取字节一致。三路此前缀没有新terminal，不能据此声称真实增长。

缺更新、错步、错计数、漏掉终端增长和错父总数共15损坏输入均被拒绝。核验30份原锁定源码及实际trainer，确认replay.add/cache同步在该步learner.update和optimizer日志之前；这是inclusive累计的代码依据，实际增长仍需done事件。

比较等待器在完整96全90分析后自动执行check_terminal_population.py --complete：全部optimizer行与transition配对，完整96 replay所有done、新done累计、全部旧终端indices/masks、每方法30新终端及32种mask分层存档计数逐项绑定。完整检查尚待原训练完成；在线逐分层tensor未记录，不能冒充已观察其内容。

## 原94–96窗口的完整95输入

复用锁定的binding_rules.py，从validate_registration内抽取原逐组检查AST并逐条确认完全相同，未改变外层九组门槛、窗口、阈值或统计kernel。真实完整95三个组分别绑定protocol/review/health/finished、全部30episodes/41250optimizer、loss与health两张实际图及检查、完整checkpoint，共每组11类来源。三个完整checkpoint均实际加载，census与架构/回放52/4m/counters/完整边界通过。

此前完整94三组检查仍保留；本轮重新hash其全部引用，与真实95父checkpoint/协议/steps链精确相连。`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census96_comparison_20261031_v1/COMPLETE94_95_INPUT_MAP.json` 含六组；原全九组验证器仍明确拒绝“All nine complete input groups required”。尚缺完整96三组，无最终REGISTRATION、bootstrap或稳定性结果。源、原AST提取与结果见EXTRACTED95_GROUP_SOURCE/COMPLETE95_BINDING_REVIEW。

原94–96、5%/nearzero1/5000bootstrap/seed2026102861保持。意向原登记在94启动后首完整回合前，不补造启动前登记。A94→95 reward相对变化19.7689%已违反原5%必要条件；完整95输入通过不改变这项失败。最终仍须九组完整绑定及原统计，不将六组检查冒充全窗口通过。

## 运行证据与后续

101个身份（原3learner、90sampler、5guard，之前修正版archive，原固定8533终端等待器及本轮新增全90等待器）连续600.545s/61样本保持，steps增长{'impedance': 5326, 'admittance': 5341, 'vmc': 5278}。固定终端等待器PID630628/start197966164继续，覆盖全部8533旧终端、all5/original masks、≤94/new95及79/90/92中止和93放置失败；完整96终端比较尚未产生。

原startup/review误写gamma=.9996及其observer失败继续保留，正式训练始终gamma=.9995；独立修正只读消费者后，原训练未重启。本轮适配按Python token处理轮次，浮点常量不变、hash和原94–96窗口保护，修正版archive与cache计划哈希明确绑定。

下一步继续原96，核验真实新terminal增长、完整loss与实际图、全90与固定终端比较，完成原94–96九组绑定/统计。现有append-only4m可容纳96，但完成后I/A/V仅余23488/20000/19000，不能再装完整97；容量另作决定，不覆盖旧数据。无自动97/Direct34。

原physics/MJB/Task/Strict/canonical48/filter/执行器限制/dt5e−5、actor49/critic52、clock/history/rawbit、原LR/reward/masks/terminal128/batch65536/UTD1、census及23/47容量标记不变。中断保全最新96 partial权重/Adam/RNG/replay/journals，另登记续接，不回退95；MuJoCo物理state未保存。

Direct33原数值验收保持，冻结全30 Task/Strict0/0；旧28缺完整memory-invariance证明、恢复2已证，指定ESN缺失，最终独立对比仍待。原90–92以及后续全部失败和非优势结果保持。


## GPU、来源与保存

实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际query/fetch/read main `abedacfb1d72bd0e89dd4ecf78de493cdf8e528a`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，按仓库sii-research-sync保存；原并行非RL工作保留。本轮消费者源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census96_comparison_20261031_v1`，原训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle96_20261031_v1`，固定全部8533终端比较 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census96_fixed95_terminal_20261031_v1`。

独立guard `/tmp/sii_gpu_util_guard_20261031_recovery_v1` 科学结束后仍继续，不创建STOP，非系统重启服务。窗口150样本/758.498s，最低[74, 64, 68, 66]%、低于50[0, 0, 0, 0]、末值[79, 92, 89, 69]%；含synthetic guard，不等于科学吞吐或每瞬时保证，旧主机切换0%记录保留。保存总steps{'impedance': 3957371, 'admittance': 3960861, 'vmc': 3961724}。

小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS96_COMPARISON_20261031/SMALL_EVIDENCE.tar.gz`，64成员/79009字节，SHA256 `65d6d4739b347a5b9222bb699ac3fc12ead097ee8ffd72033b2e48fe05129479`，全部tar成员/AST/JSON核验；原始diff原件保留。大型checkpoint/replay/journals仅共享SSD，HDD配额满仅254字节LATEST原地更新，非HDD/arm1全备份。提交字节与实际远端核验 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS96_COMPARISON_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。
