# 参数61前5000、全1824终端锚点及后续窗口登记

## 12:17补充：原61继续、全标签复核与GPU实测

本轮开工及收尾真实fetch/read main `d8d1c01f0c47821ab17d6129ed413cb798045cd1`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无协议变化。下文11:59登记继续有效。

新增 `B/runtime/parameter_task_label_audit_20261028_v1/audit_labels.py`：全90条件对/180已保存rollout逐项核对Task、Strict、physical_valid、abort、原.2mm物理门、episode/rollout一致、条件模型与执行evaluator hash；保存全部条件和全部标签变化，特别包含Task变化而Strict未变。只读，无重仿真、优化或原训练脚本改动；是保存标签与物理统计/执行源核验，不是独立子步重算或任务轨迹重放，不新增收敛门。

实际59→60回归 `B/runs/parameter_task_label_audit_20261028_v1/REGRESSION59_60.json` 全180通过；独立与既有报告对照全90 reward及Strict/abort变化均一致，A short0600 Task-only与physical_valid退化精确复现，I/V无Task-only变化。对当前未完整61的真实调用拒绝，未创建结果文件，记录INCOMPLETE61_REJECTION.json。

新等待569099/start38483285已实际核验live，CPU53/7200秒、CUDA禁用；PLAN61 SHA `67c3318b7a53285d2a030ac26df88b4d605150f0432addbbeed009f6043ef4d3`，绑定真实61 learner/archive身份和两个源hash。等原61完整归档/learner自然退出后输出 `COMPLETE60_61.json`、`FINISHED61.json`，失败另记WAIT61_FAILURE.json。尚无完整61结果；不能因观察截止重新启动训练。该补充须纳入未来DECISION62审查，原完整loss/health/59–61统计仍必需。

原61在12:05:47–12:15:50连续21观测，三learner和五guard/五审计等待身份保持，steps2530120/2530977/2532175→2537716/2538679/2539961逐次增长，无完整/失败标记；观察器自然exit0。12:16:43再次原身份live，steps2538547/2539287/2540576、GPU78/92/92/96%。原全61 loss、1824锚点对照、62仅恢复及59–61窗口继续，无auto62，Goal active。

`B/runtime/parameter61_verified_wait_1205_20261028_v1`保存21条进程观测及区间内117条原guard采样。四卡min74/67/63/69%、mean78.75213675/89.38461538/89.07692308/89.24786325%，低于50计数均0，最大采样间隔5.28090453秒。事后实际样本、含合成负载，不代表连续瞬时保证或纯训练吞吐；历史共同0%异常保留。即使科学完成也继续v5保活，不是跨系统重启服务。

[补充保存收据](RL_PARAMETER61_LABEL_WAIT_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER61_LABEL_WAIT_20261028/MANIFEST.json)：13成员/32579字节，`B/repository/RL_PARAMETER61_LABEL_WAIT_20261028_121700/SMALL_EVIDENCE.tar.gz`，SHA256 `008a44c24c129d0522f07f4549e865ff155daac478beba34fa0b106d17bc43cb`，逐字节/所有Python AST核验。大产物仍共享SSD，非HDD/arm1全备份。

2026-10-28 11:59 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；仓库 `B/repository/SII_compliance`，Torch `B/env/bin/python`。完整60科学结果及61真实startup见[上一交接](RL_PARAMETER60_COMPLETE_20261028.md)。本轮实际fetch/read main `72d5d78402061838c1e2a86a3d0c120a6482d63d`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；main新增另一主机非RL108评测10→12/108等待证据，已fast-forward完整保留，无RL协议变化。

## 原61持续运行

`B/runs/parameter_capacity_pool30_cycle61_20261026_v1` 原I3949762/A3949764 start38336483、V3949767/start38336484及archive3949770保持。11:59 steps2525215/2526015/2527201，尚无完整30条件结果。原reward/gates/物理/LR/masks/65536/UTD1/终端权重128/I targetmin、A/V targetmean/actor min/4m append和完整历史状态不变；每路30sampler。无重复启动、无自动62。

完整61 loss等待3959253/start38338911，原59–61稳定窗口等待4067967/start37570184均实际live。完成后审全loss、health、Task和Strict变化、固定终端以及原59–61窗口，不能只读取原paired_gate中仅Strict变化的changes。原I56–58/V53–55通过保持；I59/60近零保护仍按原nearzero1，不改公式以宣称相对稳定。

## 固定前5000结果

`B/runs/parameter61_first5000_20261028_v1` 已逐字节/hash、全字段有限/step连续和独立保存算术复核，loss.png已实际查看，六面板/轴可读。源码逆变换/AST通过；登记在61训练及该前缀存在后，非训练前登记。

|方法|critic首→末1000|mean / max|actor首→末1000|
|---|---|---|---|
|I|2.360355904 → 2.192203325|2.181532169 / 22.443210602|28.900656687 → 28.821281771|
|A|1.845287362 → 1.695530824|1.764684529 / 27.032014847|−10.324837983 → −10.372588073|
|V|.811884367 → 1.005566544|.916754947 / 23.409801483|−14.611507569 → −14.642100290|

I有约3000–3500局部隆起，A总体略降且早期尖峰，V约1700及4700附近burst、滚动均值升高；actor小幅漂移后较平。只描述固定前缀，不称整轮收敛，有限尖峰本身不新增失败阈值。

## 完整60全1824固定终端锚点

`B/runs/vmc61_terminal_anchor_followup_20261028_v1` 已提取完整60全部1824×57终端输入并独立逐数组/标量复算，masked SSE4384.706013434719。anchor60.npz SHA256 `7ba98a5d1e93c51da77604f0c5388e92a03881215d661d1e622c7cb6856a237b`。复用已核验60 CPU预测，无新前向/优化/物理；checkpoint60 V SHA `2c3ab84edc6bb4f9f49a8f7fbbe20a15453edeb8a2f477bdf72273b0ab60a1f6`。

新waiter345459/start38443452已实际live，CPU53/7200秒、CUDA禁用。PLAN SHA `03e610971addb0a8dc29d083198a7f42d1713f36d94dfbe420f7bc309e6c7353`，绑定真实61 learners和独立MONITOR_LAUNCH记录、registration、锚点及审查、前60结果与原58 focus。61完整审查/原learner自然退出后才冻结CPU前向，1824旧+30新=1854行；五focus2050526/2299142/2046571/2423133/2423122保持，全部行参加、旧/当前分母分列，权重/RNG不变。训练期间登记，非训练前；实际61对照待完成，无新停止门或梯度因果主张。

最初源码适配因checkpoint SHA内含60使逆变换校验失败，未写源码、随后capture缺文件exit2；保护不透明SHA后逆变换/AST通过。PLAN首次组装误从LAUNCH取monitor触发KeyError，未写PLAN/启动；改读取实际MONITOR_LAUNCH后核验真实PID/start并启动。两项准备失败原记录保留，未影响科学进程。

## 62恢复检查与62–64未来窗口

`B/runtime/prepare_parameter62_20261028_v1` 源码61→62（含补零周期）逆变换/AST通过、waiter原字节不变；缺DECISION62的实际启动调用拒绝。等待156458/start38409347实际live、CPU53/14400秒，登记SHA `d674295d90cf3038f7cd02345fbd50a44fe297b8d2782389ab96ad26b4111dc8`，只在完整61审查/自然退出后执行恢复check-only，不自动训练62。未来DECISION62除保留原reward_window56_58字段外，还必须审查并绑定完整原59–61结果。

`B/runs/parameter_capacity62_64_reward_stability_20261028_v1` 已在62/63/64均未启动前登记下一连续非重叠窗口，PLAN SHA `44e0b484fb61c8c640e2e56bfe1ca36b08d96c2098c2c393104ebf9c3713dfc5`。三个源逆变换/AST通过；原seed2026102855/5000 bootstrap/5%/nearzero1/anchor55/4m marker保持。原59–61完整报告必须保留。尚未启动waiter：待62经科学审查真正启动后单独记录并启动原14400秒等待，以覆盖62–64；不改不可变PLAN，不据未完成结果提前启动训练。

## GPU与保存

GPUv5实际 `/tmp/sii_gpu_util_guard_20261028_v5`，supervisor3256866/start37410686、worker3256867/68 start37410690、3256869/start37410691、3256870/start37410693全部核验live，v5 STOP不存在；旧v4 STOP保留，禁止恢复v4。11:59即时GPU79/97/94/94%。用户明确要求科学完成后也继续保活，包含合成负载、不能当训练吞吐，也不保证每瞬时均超过50%；历史共同0%异常保留。该守护脱离终端但不是跨系统重启服务。

Direct33原经验数值收敛/Task Strict0/0结论保持，不启动34。冻结55完整90回合及41→55全180报告比较已完成，不重跑。

[保存收据](RL_PARAMETER61_EARLY_ANCHOR_SAVE_20261028.json)、[成员清单](evidence/RL_PARAMETER61_EARLY_ANCHOR_20261028/MANIFEST.json)：56成员/1287568字节小包 `B/repository/RL_PARAMETER61_EARLY_ANCHOR_20261028_115930/SMALL_EVIDENCE.tar.gz`，SHA256 `81427c3d126715b5d2c2332aae94a96940c1b6995e5eacaa80fcdd813c14bfbd`，逐成员字节/全部Python AST通过。大checkpoint/replay/raw仍原共享SSD，HDD配额满仅改既有LATEST入口，非HDD/arm1全备份。此次包不含完整61结果。

接手核对PID与start ticks及实际FINISHED；观察器超时/退出不是科学任务结束，不因此重启。继续原61，待完整后做上述审查再决定62，Goal active。
