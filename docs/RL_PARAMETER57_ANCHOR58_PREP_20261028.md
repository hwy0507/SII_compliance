# 参数57固定终端跟踪与58恢复准备

2026-10-28 07:53 UTC，Goal active。原训练和评测继续，未重启。用户明确要求科学工作完成后GPU仍保持运行，独立v4守护继续；其负载不计作科学进展。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮已查询/fetch/read远端main `0073bb1529a0cc22eaa27e0948f89ae13dd01e11`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及更新日志，未出现新的RL科学约束。[完整56与已通过的57实际启动审查](RL_PARAMETER56_COMPLETE_20261028.md)仍为科学结果依据；无子agent。

## 当前真实进度

07:52核验PID和/proc start ticks，三路原57全部live：I3947388/start36800486，A3947389/V3947390/start36800487；archive3947391/start36800487。I/A/V步数2367643/2368319/2369471，各30并行sampler仍运行。各自从完整56新增20995/21069/21221步，尚未完整结束，不能写成完整57通过。

冻结55原I/A/V1869175/1869176/1869177、review1869178（均start36428775）继续，完整条件9/30、10/30、9/30。原90回合计划/seed与零优化约束保持，部分结果不替代最终全90审计。完整57 loss waiter4039965/start36815886、原56–58固定统计788599/start36203076继续，不重置原窗口、阈值或观察截止。

GPUv4 supervisor1629438/start35566457，workers1629439/1629440 start35566468、1629441/1629442 start35566469全部身份相符，STOP不存在。即时79/71/89/96%，包括独立合成保活；不是纯训练吞吐，也不作永久每瞬时保证。守护是当前主机脱离终端的进程，非跨系统重启服务。Direct仍不启动34，数值阶段与Task/Strict0分开披露。

## 新57固定终端只读跟踪

`B/runs/vmc57_terminal_anchor_followup_20261028_v1`，新waiter701140/start36958908，固定7200秒、CPU53，无自动训练。PLAN SHA `3547a5dc155973201de6d18be2a55c046ab248923fea5f82da79d62a6ed3c911`；注册时原57三learner/monitor存活、完整57不存在。计划登记在57训练期间、完整结束前，不称训练前预登记。

以已审计VMC完整56的全部1704终端行为固定锚点，保存的features/reward/mask/q_after/分母均绑定原hash。完整57后验证旧输入、动作、reward、mask逐项一致，对照完整56与57 critic，并保留57新增30终端。两条历史失败index2050526/2299142明确标记，同时保留全部样本，避免只看选中行。

计算旧1704 masked SSE、原分母下的贡献与实际57分母下贡献、新30贡献；独立math.fsum复算已保存数组。CPU冻结前向，检查权重与forward RNG不变、复现完整57健康MAE，零优化/物理/replay写入。不是在线loss、历史minibatch或梯度因果分析，不是新收敛门槛。实际比较、独立数值复核、图像检查均尚待；目前仅源码AST/hash、waiter单处适配逆变换及实际存活检查通过。

## 58仅恢复与派发路径准备

`B/runtime/prepare_parameter58_20261028_v1`，原waiter427130/start36913316，固定14400秒，CPU53。绑定准确57 LAUNCH与原learner/monitor，等待完整57归档、review/health及三learner退出后才check-only；不自动训练。源码同时映射父56→57、新57→58及补零checkpoint路径，逆变换/AST/hash检查通过，旧wait_prepare字节不变。

launch_parameter58.py/startup58.py已准备。缺DECISION58的真实负向调用拒绝，未创建58运行；实际58恢复和训练尚未执行。后续先审完整57 loss/配对/health和新终端跟踪，检查原58恢复结果，再写有限单轮58科学决定，核实际startup。不得把准备成功写成恢复或训练成功。

## 保存及续接

小证据`docs/evidence/RL_PARAMETER57_ANCHOR58_PREP_20261028`，含上述源码/静态检查/负向拒绝/计划/实际PID/当时进度。共享SSD包：`B/repository/RL_PARAMETER57_ANCHOR58_PREP_20261028_075318/SMALL_EVIDENCE.tar.gz`，22成员、15683字节、SHA256 `edcc59029a85fbd686f568ec190bebdb60110c0f9d2e1af03de87ef138e60cf3`，逐成员字节核验。收据[RL_PARAMETER57_ANCHOR58_PREP_20261028_SAVE.json](RL_PARAMETER57_ANCHOR58_PREP_20261028_SAVE.json)。这是本轮准备补充包，依赖前轮完整56证据及共享SSD大checkpoint/replay/raw，非HDD/arm1全备份。

继续原57与冻结55、守护及已有等待任务；未因交接、观察预算或终端中断重启。保持原科学契约，等真实完整结果再作下一步决定。
