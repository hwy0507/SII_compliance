# 第87轮继续；冻结第86轮固定16回合动作seed诊断已启动

2026-10-30T13:36:21.936023+00:00。Goal active，原第87轮三路训练继续，steps `{'impedance': 3586349, 'admittance': 3588641, 'vmc': 3590297}`；原冻结82和85—87统计继续。GPU守护在科学作业结束后仍保持。本轮新增诊断已实际启动，尚未完成，不是收敛或正式泛化结论。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。已实际查询、fetch并读取main `f7817a1018835facc330ce9e571ba54ff73556de` 和baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。按仓库sii-research-sync执行，无子agent，其他主机非RL成果保留。

## 新诊断的依据与有限预算

先复核已完成的[冻结29多seed实验](RL_PARAMETER31_FROZEN29_SEEDS_20261026.md)：固定29、short0600、全部三方法和四动作seed已有12完整回合，I Task/Strict4/2、A2/2、V4/0；已经证明部分I/A标签在固定权重下仍会变化，不把该认识当作本轮新发现，不重开其旧预算。

本轮使用完整86权重，针对85→86的四个变化组合登记：I short0600 Strict退化、A short0900 Task退化、A long0200 Task恢复、V short0000 Strict恢复。四组×seed2026102633/34/35/36，共16回合，每回合最多55秒/1375动作，总最多22000动作/1760万物理子步，0训练更新。只I short0600与旧29同方法同条件，可描述比较；其余三组为不同条件。选择依据是已知85/86变化，不能当作随机代表全部30条件。

PLAN `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter86_frozen_switches_20261030_v1/PLAN.json`，SHA `42dc5ea17bbcde872335568ca6c02da16f42620500b8a6d31b9021bc43fd8234`；登记时间先于实际派发。固定预算无自动扩展；6小时派发/等待保护从原登记/launch计，不能以等待结束为理由重启。全部seed/失败/中止保留，不挑最好seed，不由4个seed无切换断言稳健或零失败概率。若同组出现标签差异，可证明当前固定86策略对这些动作seed敏感；仍不能分解在线85/86波动的历史因果份额，也不是entropy干预实验。

|作业|方法|条件|CPU|实际evaluator PID|
|---|---|---|---:|---:|
|impedance_short0600|impedance|active_short_train_0600|7|3393179|
|admittance_short0900|admittance|active_short_train_0900|8|3393182|
|admittance_long0200|admittance|active_long_train_0200|9|3393186|
|vmc_short0000|vmc|active_short_train_0000|10|3393188|

全部使用GPU0，原87训练GPU1—3不变；模拟子进程沿用同CPU、单线程。review PID `3393192`，具体start字段见LAUNCH/REVIEW_LAUNCH，重连先核PID身份与FINISHED/FAILURE，禁止重复派发。运行目录 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter86_frozen_switches_20261030_v1`；源码目录 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/parameter86_frozen_switches_20261030_v1`。

## 已通过的检查与仍待项目

四组全部完整checkpoint learner/optimizer/replay/RNG准确恢复通过；4m容量、23/47历史marker、完整86/恢复元数据/模型/原训练注册/required review hash核对。52项设计/恢复元数据负例正确拒绝，另外每组原native-vs-external前三动作逐位一致、同seed一致、异seed动作不同、两个非法seed拒绝。原canonical48 actor/critic50、fixed86 step/native CHEQ mixing、原MJB/dt5e-5/filter/actuator/gate/reward均保持，0优化器更新/0replay追加。

新evaluator复制并复用冻结82的完整4m恢复和冻结29的独立动作重放helper；全部原helper字节一致。实际physics IPC/action while循环AST除了progress字段名一致，独立启动保存审计400行观测/动作有限、48维/5或7维、动作范围、真实MJB、父子PID/start/CPU与注册一致。四组均已实际输出journal，不只check-only。

7个样本/180.012秒的观察中，34个新旧进程身份均live或有合法成功结束证据，原87步数单调；新86最后观察动作 `{'impedance_short0600': 1300, 'admittance_short0900': 1000, 'admittance_long0200': 1000, 'vmc_short0000': 1300}`，当前保存进度 `{'impedance_short0600': 1300, 'admittance_short0900': 1100, 'admittance_long0200': 1100, 'vmc_short0000': 1300}`，尚无完整16回合诊断结论；各作业seed/已完成回合数以保存PROGRESS为准。观察器已自然结束，科学作业继续。首版观察脚本第二个样本因progress/progress87字段名错误停止；原source/FAILURE保留，仅修复汇总脚本并另存V2观察，无科学进程重启。

全部16回合完成后，原review等待器将核验完整动作native replay、physical/filter/torque、原始证据hash、全learner/replay最终不变、checkpoint/source hash、全部seed顺序和预算，生成REVIEW/SAVED_REVIEW/八栏图。需随后实际查看图并复核；目前完整16结果和最终内存不变证明未齐，不得提前写通过。

## 原任务的连续性与未完成项

第86轮完整科学结果仍见[上一交接](RL_RECOVERY86_COMPLETE87_RUNNING_20261030.md)。I/A/V reward−2.408940764/−6.690039706/−2.831541823，Task/Strict18/17、15/15、17/17；A/V旧样本拟合与loss改善，但A critic4回归、I新Strict失败保留，未收敛。本轮没有修改正在运行87的算法或输入。

原87最多每方法41250新增、30×最多55秒、4m append-only/terminal128/batch65536/UTD1及LR/reward/masks/physics/filter/gates不变，PID2291679/80/81、start573936642，所有既有archive/loss/labels/terminal后续继续。全87尚未完成；原85—87 PLAN SHA6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e/seed2026102858/5000bootstrap/nearzero1/5%/anchor55/原4h截止保持，85→86 A/V相邻已超5%，不能靠87追认窗口稳定。完整87后依据所有结果评估单独登记的训练修订，不自动88。

冻结82进度：

- impedance: 完整30，Task/Strict 18/17；全learner/replay最终不变、0更新。
- admittance: 已完成28条件，在途active_long_train_0671，1000动作；最终不变证明待。
- vmc: 已完成29条件，在途active_long_train_0900，800动作；最终不变证明待。

完整90、剩余最终内存不变、root review/55→82比较/独立全savedraw审计与实际图仍待。单actionseed2026102638、开发训练条件，不是泛化。Direct33数值阶段接受、冻结30 Task/Strict0/0，无Direct34；中断28缺最终不变证明仍披露。指定ESN仍缺、不替换他主机模型、不重复追问。partial75/原74—76不可判、76—78/79—81/82—84结论及79真实安全中止保留。历史10,577,448行因果历史重建只证明数据可行性，没有actor输入修订。

## GPU与保存

原v7 supervisor97370/start570509460、workers97399—97402/start570509475继续，adaptive target70%；从上一保存起243样本min `[71, 67, 65, 69]`%、低于50次数 `[0, 0, 0, 0]`，末值 `[81, 96, 92, 93]`%。合成守护计入利用率，不能当科学吞吐或收敛。科学全部结束仍保载；历史v7预热0与v6 GPU0=31/GPU2=33/44低谷保留，采样之间瞬时不保证，不是重启自启服务。

SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY87_FROZEN86_SEEDS_20261030/SMALL_EVIDENCE.tar.gz`，113成员/398074字节，SHA256 `7f18a9cd97da604a51855592f5893f9c1ab569196c8babafc838d6424cacf6ca`。tar成员原字节/源码AST已核，Git index/commit blob另核。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；原HDD LATEST指针保持254字节原位更新。运行中的日志为快照。发布以SSD本包PUBLICATION.json中成功push及随后实际远端核验为准。
