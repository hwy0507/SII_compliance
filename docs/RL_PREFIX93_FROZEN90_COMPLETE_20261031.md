# 第93轮前5000与固定终端后续；冻结90全部评测审查完成（2026-10-31）

原第93轮持续训练，固定前5000 loss仍有尖峰，尚未收敛。全部8263固定92终端后续已登记、真实partial93与缺完整93拒绝检查通过，唯一有限等待器已启动；它只在原完整93归档审查通过后执行零更新诊断，无自动94/Direct34。

原冻结90全部90评测、完整learner/replay不变、全部98391200原始子步审计和88→90配对已完成，实际结果图已查看。所有原冻结evaluator/collector/postprocessor正常结束，勿重启；训练93和固定终端等待器继续。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。实际query/fetch/read main `1560926989409e993acac62c0a851d84965e71ba`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，遵循仓库sii-research-sync，无子agent。当前源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_terminal_followup_20261031_v1`，后续结果 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation93_fixed92_terminal_followup_20261031_v1`，固定前缀 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_terminal_followup_20261031_v1/prefix5000_v2`；原训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle93_20261031_v1`、完整归档消费者 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_review_20261031_v1`。seed、版本、源/MJB和checkpoint hash保留原登记。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。

## 固定前5000

在读取loss值前固定三路各前5000真实更新；按完整92实际父steps3811512/3815000/3816000逐步号检查，update_index均0，原optimizer前缀字节精确。全部字段有限、critic非负，保存NPZ逐字段与原前缀精确，math.fsum独立复核首末1000/全5000均值与极值；实际六栏图已查看并SHA绑定。

| 方法 | critic首1000→末1000 | critic最大 | actor首1000→末1000 |
|---|---:|---:|---:|
| impedance | 1.416558465 → 1.376016963 | 15.037960052 | 23.551574396 → 23.725260735 |
| admittance | 1.080119397 → 1.091731934 | 2.379390001 | -7.746069259 → -7.742651768 |
| vmc | 0.762983690 → 0.803952441 | 2.837953329 | -10.992060356 → -10.965264070 |

I仍有密集尖峰、actor均值上移；A中段critic抬升/尖峰、actor局部近似平稳；V间歇尖峰且末1000均值高于首1000。仅早期prefix，不能代替完整reward/loss稳定性或因果改善。完整92原结论和全部失败窗口保持。

首版prefix脚本的文本替换误把父92 review路径改成不存在的93 review，FileNotFoundError发生在读取optimizer前缀前。原source、原PLAN和空输出目录保留；v2仅修正两个父路径并使用新输出目录，失败/修复hash和diff已保存。未改变训练、模型或研究协议，不隐藏该软件失败。

## 固定92后续

精确绑定完整92全部8263终端：I2755/A2754/V2754，原observations52/actions/rewards/masks及全部五critic预测不变，包括79/90/92中止。原保存masked/all-row SSE算术预检通过；真实缺完整93被拒绝。三份不可变startup93 checkpoint实际验证准确父steps、双架构marker、完整52维及4m/23/47历史标记；全部实际partial均拒绝作complete，27个错误metadata/partial边界反例拒绝。此阶段0新physics、0optimizer update、0新neural forward。

新比较器在真实完整93后要求完整review/health/loss一致、精确checkpoint SHA、complete_condition_cycle、完整93周期历史；固定92的全部终端索引/current52/actions/reward/masks与新回放前缀逐位核对，再恢复完整learner/Adam/RNG计算all5。计算前后完整learner/replay/RNG及磁盘checkpoint不变验证；保存全行92/93预测，独立保存算术审查和图，保留每critic退化及三条中止变化，不以挑选子集替代全队列。这些后续计算尚未执行，不声称已有93终端结果。

唯一等待器PID `1461907`，原archive monitor729497/start578235463绑定，截止 `1793422944.4276955`（原monitor启动+14400秒），不延长；原完整93归档后诊断预算1800秒，保存算术300秒。实际图仍需完成后查看。固定队列是解释loss的诊断，不追加为数值收敛门槛，也不证明策略安全/泛化。

## 在途与约束

本轮连续300.158秒/31样本，原100个训练/archive/固定终端等待/90sampler/guard身份保持，三路steps增长；保存steps `{'impedance': 3826498, 'admittance': 3829977, 'vmc': 3830985}`。冻结90进程按原PID/start核对，正常结束以各完整收据确认，动态正常结束记录 `[{'kind': 'evaluator', 'pid': 283421, 'receipt': '/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1/impedance/FINISHED.json', 'sha256': 'eb15c612acb767c4a3cf2fb768435eaa8d65d5fe4745c9a37e4183630516eb1c'}, {'kind': 'evaluator', 'pid': 283428, 'receipt': '/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1/admittance/FINISHED.json', 'sha256': 'ffe5e0ae7862159adc8cb41e826ed5ba7bfcd2b5503f2a84703c23feda62941c'}, {'kind': 'evaluator', 'pid': 283430, 'receipt': '/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1/vmc/FINISHED.json', 'sha256': 'a702f97387969f145b647d83489e7473b24cdf2de388b4e05ecc9011813de38a'}, {'kind': 'collector', 'pid': 283433, 'receipt': '/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1/REVIEW.json', 'sha256': '3c0a37a0adf318fdd8464684e4ef735d82e92fe25f0e4615af1d4fccacc53591'}, {'kind': 'postprocessor', 'pid': 292743, 'receipt': '/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_frozen_postprocess_20261030_v1/FINISHED.json', 'sha256': 'a6b029a943538749a1fcd4d220e4ed55c039fe4c0d09b64adb3bfc4027cdeece'}]`。冻结完成 `{'impedance': 30, 'admittance': 30, 'vmc': 30}`；原evaluator/collector/postprocessor全结束且收据核验。原阻抗冻结30中29完整+1在614动作/24.56秒安全中止保持，不能写成全30成功。

## 冻结90全部结果

同原30训练条件、外部动作seed2026102638：I/A/V Task分别17/15/17、Strict16/15/16，mean reward分别−4.332399381/−6.792978865/−4.576672118；机器安全违规回合数2/0/1。I有29完整回合，A/V各30完整；全部122989动作、98391200子步，0optimizer updates，完整learner/replay最终内存证明通过。

原raw auditor按全部90条件核对实际原始hash、dt5e−5、逐关节峰矩、实际人体接触分母、工程阈值下合规时长、外部穿透及原reward公式，最大reward重建误差2.842170943e−14。原动作/filter/torque审查收据保持；这是保存轨迹审计，不是独立动力学重跑，也没有在evaluator退出后再计算一次已释放内存digest。最终保存summary与全部raw审计行、配对结果逐组复核，实际图SHA绑定。

与冻结88配对：I mean reward−1.958963614，long0000失去Task/Strict并安全中止；A mean+.076426122但Task16→15、Strict15→15，long0900获Task/Strict、short0600获Strict、short0900与long0300失去Task/Strict；V mean−1.705101673，Task17→17、Strict17→16，short0600失去Strict。全90配对与失败保留，不只报告净计数。I short0600外部穿透.219463635mm，V同条件.200654869mm，均超过原.2mm门；I long0000全局目标物体/台面安全中止，external .111942929mm，不能因external低于门而抹去全局失败。

原训练条件单一外部动作seed的描述性配对包含额外训练曝光和critic修订，不是独立训练seed、未见条件、因果改善或最终SPT/指定ESN比较；工程人体阈值不能声称已验证人体舒适性。完整93及固定92终端对照仍待，原90–92稳定性失败不被这些评测覆盖。

原critic/replay52、actor49/canonical48信息、clock49/history50/bit51及已学权重、Adam/RNG、双marker、append-only4m replay与23/47历史marker保持；terminal128、batch65536、UTD1、原LR/reward/masks、30×55秒/最多41250每方法原预算不变。冻结physics/MJB、Task/Strict gate、filter/执行器/dt5e−5不变，无离线权重推广或自动94。原90–92 I/A失败、V reward-only通过及所有历史失败保留。

Direct33原数值验收与冻结全30 Task/Strict0/0、旧28缺最终内存证明/恢复2完整不变保持，不追加Task成功为数值收敛要求、不为占用训练34。指定ESN仍缺，不替换其他主机模型。partial75、不可评74–76、79/90/92安全中止、halfstd拒绝、全部软件失败保持。Goal active。

原guard97370/97399–97402继续，threshold50/target70/min duty.7，科学完成仍保活，非重启服务。本轮162样本/818.856秒，最低[68, 68, 66, 63]%、低于50次数[0, 0, 0, 0]、末值[73, 70, 73, 97]%。含synthetic guard，不等于科学吞吐或每瞬时保证，旧低谷保留。

共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PREFIX93_FROZEN90_COMPLETE_20261031/SMALL_EVIDENCE.tar.gz`：211成员/3631770字节，SHA256 `efeba11d8ac06c94ae2b0d972d45e10e1c8223119e0aff625e697088ffa14889`，逐tar成员字节/AST核验；manifest在 `docs/evidence/RL_PREFIX93_FROZEN90_COMPLETE_20261031/MANIFEST.json`，index/commit逐字和实际远端push收据在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PREFIX93_FROZEN90_COMPLETE_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。大checkpoint/replay/raw仍SSD，HDD配额满，仅现有254字节LATEST原地更新并回读，非HDD/arm1全备份。
