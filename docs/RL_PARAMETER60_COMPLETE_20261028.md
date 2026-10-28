# 完整60：保留正向结果和标签变化，准确续训61

2026-10-28 UTC，Goal **active**。原60三路已完整自然退出，完整归档、reward/replay、loss独立算术、health、VMC固定终端和实际图审通过；整体reward稳定且loss无异常的目标尚未证明。继续一个原配置有限61，完成预先登记59–61窗口。无子agent。

实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD
`B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；仓库`B/repository/SII_compliance`，Torch解释器`B/env/bin/python`。
本轮开工实际查询/fetch/read main `a704d4c93275cf08516289de32a03b649053b747` 与 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，原协议不变。前轮完整59及冻结55见[交接](RL_PARAMETER59_FROZEN55_COMPLETE_20261028.md)。

## 完整60结果

`B/runs/parameter_capacity_pool30_cycle60_20261026_v1` 原三learner自然完成；每路30条件×55秒、41250新增、无abort。完整59全部2470398/2471000/2472000行replay字段、history、优化器及4m/历史23与47 marker保留，新reward由冻结实现重算最大误差0，网络/优化器全部有限。

|方法|steps / updates|mean reward|Task / Strict|critic首→末1000|critic mean / max|
|---|---|---:|---|---|---|
|阻抗|2511648 / 2506649|−.628091136|18 / 18|2.341074810 → 1.792392008|2.133043928 / 23.117420197|
|导纳|2512250 / 2507251|−8.555517730|15 / 14|1.619543226 → 1.676395484|1.498329418 / 34.440906525|
|VMC|2513250 / 2508251|−2.855623283|17 / 17|1.192178248 → .880621622|1.051072647 / 16.786970139|

归档 `B/runs/parameter_capacity_pool30_cycle60_archive_20261026_v1/{method}/cycle_00060.pt`：

- impedance SHA256 `c88e6897b7ba62cbcfe2868ed424bfab2bdde6352b82cfdd86d1d8a258541fc0`。
- admittance SHA256 `bf234e3b7e67a5f9c80d31c603fbd35a8de026fa5138315e6bac45b6969006e9`。
- vmc SHA256 `2c3ab84edc6bb4f9f49a8f7fbbe20a15453edeb8a2f477bdf72273b0ab60a1f6`。

完整审查 `B/runs/parameter_capacity_pool30_cycle60_review_20261026_v1`；loss与配对 `B/runs/parameter60_loss_20261028_v1`。全41250更新实际长度、全部数值字段有限、step连续、49–60全部历史及源核验，独立保存算术通过，loss.png实际查看。I critic基线稳定至下降，但actor29.959157→28.925813继续移动；A约34000更新出现后段burst，actor−10.256659→−10.317433后较平；V critic改善，actor−14.150009→−14.608862末段开始变平。有限尖峰本身不新增异常阈值，非零终端误差不作停止门；正向变化完整保留。

## 全条件配对与Task-only补充

I全部Task/Strict标签保持18/18，均值变化−.031138560。原I56–58的reward5%通过保留；59/60近零均值不能静默换分母宣称59–61相对稳定通过。

A mean reward改善5.050777081，但仍是−13.606295→−8.555518的显著平台变化，不能称稳定。short0900和long0200恢复Task/Strict，short0000 Task保持、外穿透.217123555→.145851418mm恢复Strict；原同MJB/evaluator/.2mm门保持。

原paired_gate的`changes`列表仅选Strict变化，完整Task计数和全部30回报一直保留。新增 `TASK_ONLY_CHANGE_REVIEW.json` 补查A short0600：Task false→true，但外穿透.187946116→.235473678mm、physical_valid true→false，Strict两轮均false，reward−34.586351→−34.975550。逐rollout/episode门、原模型和evaluator hash复核，未重仿真。这项任务恢复伴随物理门退化，不能省略。

V short0600 Task保持true，外穿透.208326955→.187235864mm跨原.2mm门恢复Strict，整体17/16→17/17，reward−4.517594→−2.855623。原V53–55 reward通过及后续平台变化均保留。

原59–61稳定窗口由59启动前登记，尚缺61。原5%/nearzero1/5000 bootstrap/seed2026102855/anchor55全部保持，不增加任务成功或零终端误差门，不把当前结果替代原窗口。

## 健康与固定1794终端对照

完整health JSON及实际training_diagnostics.png已读；图右上标题边缘裁切，精确定义以JSON为准。回报图是在线回合完成顺序，不是冻结策略曲线。A/V训练target为mean，诊断TD使用固定min-pair，两者明确区分。

|方法|终端数量|全部终端MAE|in-bag MAE|固定pair未投影TD MAE|sample Q mean|
|---|---:|---:|---:|---:|---:|
|I|1825|.921252443|.319533569|.245894004|−28.168195786|
|A|1824|.854757335|.465177976|.246682112|10.052868823|
|V|1824|.563658246|.252762417|.136757558|14.757708703|

网络状态不变。以上是诊断，不能由有限值或小误差单独推断收敛。

`B/runs/vmc60_terminal_anchor_followup_20261028_v1` 完整对照、独立保存值算术和实际follow60.png审查通过。完整59固定1794×57终端观测/动作/reward/mask精确保持，权重/RNG不变，health60复现，0优化/物理/replay写入。登记在60训练期间，不是训练前。

- 旧1794 masked SSE **9821.147794252→4367.670412362**，下降 **55.52790261%**。
- 旧贡献.581939397522→.254598190300；使用旧分母的末值.258882743141。
- 新30贡献 **.000993234272**，全部终端贡献 **.255591424572**。
- 五个固定focus均改善：2050526 SSE24.127736→3.839032，2299142 37.082465→1.388229，2046571 2.255054→1.043687，58 short0600失败2423133 1175.688107→181.353174，58 short0200成功2423122 1637.752307→1497.642821。最后一项仍较大，全部行保留，不把focus改善当梯度因果。

anchor59 SHA `10da2c3794ef8914dd89029b1da7053bd7ad6fd5c0b79cfb00569501ba6c655f`；values SHA `9ef76ab4a690e66625d4b03f9e0213013a7486b3e352e6e3706f3534f81e98a0`；follow60.png SHA `4d2223c8f93464a12a1c99afa61d710c4efc7bc793b9dabb0ad31935b8e2eac7`。标题完整、近原点标注重叠，实际图已看。

## 有限61已启动

准确60 fulllearner/replay/下一65536恢复三路exit0，检查日志绑定上列完整60 checkpoint。`B/runtime/prepare_parameter61_20261028_v1/DECISION61.json` 绑定完整60/health/loss/独立算术/图、Strict及Task-only配对、固定终端和原稳定窗口。I/V loss改善事实保留，A/V reward仍因标签变化波动，原59–61窗口待61，继续一个原配置有限61，无auto62。

11:40:48 UTC启动 `B/runs/parameter_capacity_pool30_cycle61_20261026_v1`：

|角色|PID|start ticks|
|---|---:|---:|
|阻抗learner|3949762|38336483|
|导纳learner|3949764|38336483|
|VMC learner|3949767|38336484|
|archive|3949770|38336484|
|startup|3949773|38336484|
|完整61 loss等待|3959253|38338911|

GPU1/2/3、CPU13–25/26–38/39–51，每路30sampler。原reward/gates/物理/LR/masks/65536/UTD1/终端权重128/I targetmin与A/V targetmean/actor min/4m append容量及全部历史状态不变。

完整loss等待 `B/runs/parameter61_loss_20261028_v1`，CPU54/7200秒，PLAN SHA `c9183523ca76bb2f9c03cee89744ede62f02cd226b24dbfd44d01c375c96986f`；已绑定真实jobs/source。保留完整49–60并追加61，60→61配对，完成后须review_saved及实际图审，Task-only变化应另外核对，不能只读Strict变化列表。

原59–61统计4067967/start37570184继续。当前不得假称完整61或窗口已完成，不得重复启动61。实际startup已通过：I/A新增1000、V新增2000，旧2511648/2512250/2513250全replay字段/history/optimizer配置保持、30sampler/30MJB和原marker通过、新reward重算0误差。证据 `startup/REVIEW.json`；这与启动前check-only是两项不同核验。11:46原61步数2514897/2515566/2516631，GPU79/96/94/93%，原身份保持。

## 观察退出与GPU守护

只读观察session5024最后输出11:37:33后返回143，原因未确定，未向科学任务发送信号或重启。原60三learner此前均已正常FINISHED；重新核对时archive PID恰已自然退出，实际ARCHIVE_REVIEW_FINISHED证明完成，初次/proc读取缺失已保留记录。其余原终端/61恢复/59–61和五guard均核验live或正常完成。证据 `B/runtime/parameter60_complete_publication_20261028_v1/OBSERVER_EXIT_RECHECK.json`。

GPUv5实际 `/tmp/sii_gpu_util_guard_20261028_v5`，supervisor3256866/start37410686，workers3256867/68 start37410690、3256869/start37410691、3256870/start37410693保持。科学训练结束到新61启动之间仍持续运行，11:38–11:39多次GPU约79/70/71/72%。包含合成守护，不是科学吞吐或每瞬时保证；历史共同0%异常保留。用户要求科学完成后也继续guard；/tmp不是跨系统重启服务，旧v4 STOP保持，禁止恢复v4。

Direct完整33原经验数值收敛结论保持，Task/Strict仍0/0，不启动34；冻结55已完成的原90回合和41→55比较保持，不重跑。

## 保存与下一步

完整60结果、源码/图/独立审查、61恢复/启动/完整loss登记及观察异常记录见[保存收据](RL_PARAMETER60_COMPLETE_SAVE_20261028.json)与 `docs/evidence/RL_PARAMETER60_COMPLETE_20261028/MANIFEST.json`。大checkpoint/replay/raw仍原共享SSD；HDD配额满，只更新既有LATEST入口，不声称HDD/arm1全备份。

继续原61至完整，审全部loss、health、配对和原59–61窗口，保留near-zero保护与全部历史通过/失败。正向诊断不是最终目标完成，Goal仍active。再次接手先查真实PID+start及FINISHED，观察预算结束不代表科学任务终止。

本轮包142成员/1300665字节，SHA256 `2fcfa44f3bac89b37e3b70266d7a9f31272d31393820c280d9a079980a699b52`，逐成员字节/全部Python AST核验。发布前fetch/read mainc72f1427：另一主机非RL观测覆盖诊断与首条件九模型评测均失败，非本机RL结果；已fast-forward完整保留其文件/日志，无科学协议变化。
