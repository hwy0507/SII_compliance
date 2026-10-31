# 第92轮前5000 loss审查与固定87终端跟踪登记

2026-10-30 UTC，Goal active，未达到整体reward平稳及loss健康。原第92轮三路训练、唯一归档和原冻结90评测继续；本轮完成固定前5000更新审查，并登记完整92后固定旧终端诊断，没有额外训练周期/新物理派发，不自动93/Direct34。前序：[第92轮实际启动](RL_VIOLATION92_ONLINE_20261030.md)。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际query/fetch/read main `ef2328156111a88c7c8579924523e1543cdd8780`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；沿用 [sii-research-sync](../skills/sii-research-sync/SKILL.md)，无子agent。分析源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_terminal_followup_20261030_v1`，终端诊断run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation92_fixed87_terminal_followup_20261030_v1`。原训练源码/版本/MJB/seed继续由 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_continuation_20261030_v1`、`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle92_20261030_v1/<method>/REGISTRATION.json` 与 `train/EXECUTION.json` 固定；本轮未变更依赖或训练器。

## 固定前5000 loss结果

在读取当前loss值之前沿用固定first5000方案；数据来自每方法optimizer.jsonl最前5000原始完整行，核验完整91真实父steps、连续步号、每步update_index0、所有指标有限及critic非负。保存原字节及NPZ，再用math.fsum独立复算每项首1000、末1000、全5000均值/极值，回读训练文件确认前缀未变。实际六栏图已查看，`prefix5000_v2/PLOT_INSPECTION.json` 固定图hash；原REVIEW内plot_viewed=false是检查前状态，不覆盖后续实际查看收据。

| 方法 | critic首1000→末1000 | critic最大值 | actor首1000→末1000 |
|---|---:|---:|---:|
| impedance | 1.953316400 → 1.872588253 | 20.756031036 | 22.812846191 → 22.922514967 |
| admittance | 1.121138251 → 1.135405753 | 2.490007401 | -7.969905776 → -7.954745052 |
| vmc | 0.747855220 → 0.770664517 | 4.629481792 | -11.295115620 → -11.277514780 |

阻抗critic仍反复出现约12的密集尖峰，最大20.756，actor平滑均值持续上移；其critic前缀末段均值低于首段不能证明健康。导纳critic有较小尖峰和均值起伏，actor前段近似平坦。VMC约第2000次附近出现一组critic尖峰，最大4.629，actor略上移。全部尖峰和退化保留；这只是固定早期窗口，不能推断完整92 reward稳定、loss健康、任务成功或因果改善。

首版prefix92.py在脚本生成时因顺序文本替换把父91 review路径改成了尚未完成的92 review，读取父文件时FileNotFoundError退出1。失败发生在读取任何本轮loss值之前，仅生成空prefix5000目录。原源码、PREFIX_PLAN和空目录保留；PREFIX_FAILURE_AND_FIX记录原因/hash，prefix92_v2.py仅把两处父review路径改回91并使用独立prefix5000_v2输出，原first5000选择与数值方法不变。修复后完成上述核验，原训练未重启或受影响。

## 固定原87全部终端跟踪完整92

继续使用原87全部7813终端：I2605、A2604、V2604；all5 critic、原masks、全部先前87/88/89/90/91预测保持。源来自已完整审计的91跟踪NPZ，原masked SSE/MSE、all-row SSE和分母逐项复算精确，52维保存观测与原51特征和raw preaction>.0002m位重新逐位核验，不替换旧观测。各方法bit分布 `{'impedance': {'0': 2535, '1': 70}, 'admittance': {'0': 2544, '1': 60}, 'vmc': {'0': 2559, '1': 45}}`。真实缺完整92入口已拒绝，当前0新增neural forward/physics/optimizer update。

专用validate_architecture92/validate_recovery92按准确完整91累计步数验证，父91又绑定真实90 steps+实际新增，保留90 I安全中止造成的非整轮行数。原history首次88、violation首次90、双marker、52维current/next、seed/controller/registration、4m cursor/size、continuation及partial75排除保持；原冻结90恢复模块不改。三份实际不可变startup92快照通过架构检查，均拒绝完整轮次边界；27项错误cycle/seed/protocol/controller/旧89步数/cursor/capacity/缺marker/next51测试全部拒绝。没有伪造未来完整92状态来证明恢复。

统计与input hash函数AST与原91相同；实际原生restore、all5 forward以及全learner/replay/RNG检查关键代码保持。新增第六个端点complete92，并保留全部五个旧端点；绘图仅为六组柱调整位置与宽度，数值统计不变。SOURCE_REVIEW和VALIDATOR_REVIEW分别记录源码与实际状态核验。旧91的check路径类型失败与修复保留在历史记录；本次使用已修复的Path读取。

唯一等待器PID `1234380`、start `577686421`，绑定原92 archive463623；等待截止Unix `1793416498.0612915`，即原92 launch+14400s，没有延长原预算。完整92的REVIEW、FINISHED、health、loss全部到齐且checkpoint hash一致后，才读取 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle92_archive_20261030_v1/<method>/cycle_00092.pt`，计算同一批终端all5预测并检查全state/RNG/checkpoint不变。分析预算1800秒；实际图查看另行完成。当前没有92完整终端预测结果。

这是已见旧终端拟合与保留诊断，不是安全、策略性能、泛化或收敛门槛。完整91 masked SSE相对90 I改善32.96%、A退化25.48%、V改善60.72%及所有单critic退化仍保留。第92轮自身新终端由原全回放health审查负责。

## 持续运行与未完成项

原92三learner463617/463619/463621、90个sampler、archive463623、冻结90原三evaluator/collector/postprocessor、guard及新等待器经过180.071秒、19样本、105个身份检查，三路steps增长。保存累计steps `{'impedance': 3782554, 'admittance': 3785355, 'vmc': 3786584}`；冻结90完成 `{'impedance': 15, 'admittance': 16, 'vmc': 15}`，每方法总30。原startup/启动observer已正常完成，不重跑；本轮观察完成后也不重启。

继续原92每方法30×55秒/最多41250新transition和唯一归档消费者；完整92 reward/全loss/health/固定87跟踪仍待。原90冻结seed2026102638、全90/0updates及raw/88→90配对仍待，保持原21600秒截止，不重复或延长。没有新冻结91/92任务。

原90–92窗口I/A在90→91已经违反5%相邻必要条件，仍保留原PLAN及EARLY_WINDOW_FAILURE_91；92不能消除该失败。V仅一个相邻未违反，仍待完整第三端点/首尾与第二相邻及loss健康判断。原5%/nearzero1/bootstrap设置不改，当前没有完整窗口统计，不更换窗口隐去失败。

原物理/MJB、Task/Strict、filter、执行器、dt5e-5、actor49/canonical48、critic/replay52、clock49/history50/rawbit51、4m历史23/47 marker、terminal128、batch65536、UTD1、原LR/reward/masks、已学权重/Adam/RNG保持；没有离线权重晋升。partial75、74–76不可判、79/90安全中止、halfstd否决、旧失败窗口及所有软件失败保留。Direct33原数值验收保持，冻结33全30 Task/Strict0/0、旧28最终内存证明缺失与恢复后2条完整不变性通过保持；不额外训练Direct34。指定ESN仍缺，不重复询问或用其他主机模型替代。

## GPU与保存

原GPU guard97370、97399–97402持续，用户要求科研结束也保载；threshold50%、target70%、min duty.7、CPU4–6，不创建STOP。本轮70样本最低[79, 65, 68, 67]%、低于50次数[0, 0, 0, 0]、末值[81, 97, 90, 93]%。包含合成保载，不等于科学吞吐或每瞬时保证；旧低值保留，当前守护不是重启自启服务。

共享SSD证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_DIAGNOSTICS_20261030/SMALL_EVIDENCE.tar.gz`，61成员、1460255字节、SHA256 `c4c7f829b34ec4c8fd9a79428f815cf6937683860fb473d536c382d68c340f9d`，全部tar成员及Python AST核验。清单 `docs/evidence/RL_VIOLATION92_DIAGNOSTICS_20261030/MANIFEST.json`，收据 [RL_VIOLATION92_DIAGNOSTICS_20261030_SAVE.json](RL_VIOLATION92_DIAGNOSTICS_20261030_SAVE.json)。Git index/commit逐字核验及正常push/真实远端确认记入包外 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_DIAGNOSTICS_20261030/GIT_BYTES_REVIEW.json` 和 `PUBLICATION.json`。大checkpoint/replay/raw仍共享SSD，HDD配额已满，仅原位更新254字节LATEST指针，不是HDD/arm1全备份。Goal active。
