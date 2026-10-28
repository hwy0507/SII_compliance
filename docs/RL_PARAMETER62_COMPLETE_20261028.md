# 完整62审查与准确续训63

2026-10-28 UTC，Goal active。计算主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，仓库 `B/repository/SII_compliance`，Torch `B/env/bin/python`。开工实际查询/fetch/read main `d1b1bf89e5f9a1860f0e64d622355f52e32a2100`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；非RL另一主机原108已31条的等待记录已读并fast-forward保留，无RL协议变化。

## 完整62

`B/runs/parameter_capacity_pool30_cycle62_20261026_v1` 三learner自然完成，各30×55秒、41250新增、无abort。完整审查 `B/runs/parameter_capacity_pool30_cycle62_review_20261026_v1` 已完成：全部61 replay行/历史保留、各新reward按冻结物理区间journal复算误差0，网络/优化器有限；这是保存区间审查，不冒充重新计算原子步物理。

|方法|steps / updates|reward均值|Task / Strict（分母30）|critic首→末1000|critic mean / max|
|---|---|---|---|---|---|
|Impedance|2594148 / 2589149|−5.822771830|17 / 15|2.373413150 → 2.683752962|2.394865868 / 35.179088593|
|Admittance|2594750 / 2589751|−8.573957478|14 / 14|1.354128577 → 1.296581514|1.319113244 / 6.618958473|
|VMC|2595750 / 2590751|−4.613581712|17 / 16|.719143295 → 1.175511562|.837059352 / 32.620281219|

全loss `B/runs/parameter62_loss_20261028_v1` 的保存算术/连续步数/全数值有限/完整回合及配对来源已独立复核，实际loss.png、health图已看并写PLOT_INSPECTION。I critic早期较密尖峰逐渐收缩，35000后再现burst；actor27.649446→26.700612持续下降。A critic较平略降，actor−10.536972→−10.394553后段上升。V约33500 burst后critic均值抬升，actor−14.501490→−14.230126大部分上升、末尾小回落。有限尖峰不另设失败门，也不称稳定收敛。health长标题右端有裁切，数据/轴可读。

health检查固定checkpoint的terminal in-bag MAE为I .421440524、A .199197854、V .317216813；sampled TD MAE .246374284/.218278916/.152123237。A/V sampled Q超过当前soft bound比例各.001074218773，I为0；完整保留，不声称完全校准。诊断无优化、network state不变；非零终端误差不成为新停止门。

精确checkpoint在 `B/runs/parameter_capacity_pool30_cycle62_archive_20261026_v1/{method}/cycle_00062.pt`：

- I SHA256 `b7786592de1486c982f8149063fd2ecdcef82d05e7d3d206c40606a1c507668f`。
- A SHA256 `625e57f57214fb07498738e269b867b446f4f12d5039c06e02a8c94bd5f2e90e`。
- V SHA256 `067cb41496065e47d4f4105575c4c45286640fac449ea9718cc9709f820fd0e2`。

## 完整61→62标签和固定终端

`B/runs/parameter_task_label_audit62_20261028_v1/COMPLETE61_62.json` 全180保存rollout审查完成；新增COMPLETE61_62_SAVED_REVIEW独立核对全部90 reward对、两个周期的成功计数及原Strict/abort配对列表，全部一致，本轮无Task-only遗漏。原MJB/evaluator及.2mm门保持。

- I short0100 Task保持true，穿透.192327926→.200854969mm，physical/Strict失效；long0000 Task/Strict失效，physical保持true。均值较61下降3.392731273。
- A short0200、long0300、long0500 Task/Strict失效；long0900、long0200恢复；physical全部保持true。均值下降1.570919460。
- V short0000 Task保持true，穿透.129352343→.226158827mm，physical/Strict失效。均值下降1.801899724。

`B/runs/vmc62_terminal_anchor_followup_20261028_v1` 全1854旧终端固定输入/动作/reward/mask精确、另30新终端；完整62 CPU前向、权重/RNG不变、health复现、独立保存算术通过。旧SSE **1108.452722069→2550.400600476（增加130.0865476%）**。旧贡献.063514201338→.143899727540；采用旧分母的after .146237131567，新30贡献.234366539225，全1884贡献.378266266764。

五focus SSE：2050526 .939564→9.808205、2299142 .149016→82.452507、2046571 1.191591→12.326942退化；2423133 357.964253→38.263001、2423122 47.331503→17.582179改善。实际follow62.png已看；原点附近两标签重叠，数值身份以REVIEW为准。values.npz SHA `21c826dda9cdf10a01912ba7ec7675e67bdd25d4b0a70e1ca4ed8f5ad135221a`。无新物理/优化/replay写入，不作梯度因果或新零误差门。

## 续训63及原稳定性窗口

`B/runtime/prepare_parameter63_20261028_v1` 原check-only自然完成，三路恢复完整62 learner/replay及下一65536采样精确、exit0。新review_and_decide63.py逐项复核上述输入并写DECISION63，保留launcher原reward_window56_58契约，另绑定原完整59–61失败、全62 loss/health/全标签/终端和原62–64 PLAN。三路reward均退化、actor/critic仍变化，因此续一个原配置有限63观察；不重置、不引入辅助权重、不改奖励/物理/gate/LR/mask/终端128/batch65536/UTD1/4m append。

**13:50:29 UTC实际63启动**，`B/runs/parameter_capacity_pool30_cycle63_20261026_v1`：I3732463、A3732464、V3732465，三者start ticks39114601；归档3732466/start39114602，启动审计3732467/start39114603。GPU1/2/3、CPU13–25/26–38/39–51，每路30sampler，只有一轮，不自动64。

完整63 loss由既有静态准备源部署到 `B/runs/parameter63_loss_20261028_v1`，绑定实际LAUNCH jobs及源hash；waiter3741519/start39117327、CPU54/7200秒，PLAN SHA `483c673290a24de71b305d9a7e488f80d7686ce0e85c14ef5c4fda67a150da91`。全49–62历史保留并追加63；完成后仍需独立review_saved和实际图审。

原 `B/runs/parameter_capacity62_64_reward_stability_20261028_v1` waiter1758711/start38725355继续，PLAN SHA `44e0b484fb61c8c640e2e56bfe1ca36b08d96c2098c2c393104ebf9c3713dfc5`不改；现在只完整62，仍待63/64，不能称窗口通过或失败。工具最终写REVIEW而非FINISHED。原59–61未过5%和I近零保护保留；I56–58/V53–55历史通过保留，不换端点。Direct33原经验数值收敛、Task/Strict0/0，不启动34；冻结55及41→55对照不变。

## GPU与可靠接续

原v5 guard实际 `/tmp/sii_gpu_util_guard_20261028_v5` 五进程3256866–3256870，start ticks37410686/37410690/37410690/37410691/37410693均核验live，STOP不存在。旧v4 STOP保持。用户要求科学完成后也继续保活；这是合成负载，不是训练吞吐，不是跨重启服务。

`B/runtime/parameter62_verified_wait_1329_20261028_v1` 20实际观察13:29:32–13:39:05，原learner身份保持到V自然结束；观察器exit0不影响训练。后续三FINISHED及完整归档独立确认，未重启62。另截取原guard日志271样本13:29:36–13:52:39，min70/61/67/65%、mean78.501845/79.350554/79.881919/79.321033%，低于50计数全0、最大间隔5.265177秒。包含合成负载，不能保证每瞬时利用率；历史共同0%异常保留。

最新结果和小证据保存于[收据](RL_PARAMETER62_COMPLETE_SAVE_20261028.json)及[成员清单](evidence/RL_PARAMETER62_COMPLETE_20261028/MANIFEST.json)。大checkpoint/replay/raw仍共享SSD，HDD配额满只重写已有LATEST入口，不声称HDD/arm1完整备份。接手先核验PID与start ticks、实际进度和完成标记，不因观察超时重启。继续63并完成完整loss/health/标签/终端审查，再决定64，Goal保持active。

13:56补充：实际startup三路各1000步已通过，旧2594148/2594750/2595750全部回放行、history、optimizer hyperparameters、30个MJB/30sampler保持，新reward复算误差0；不是终端覆盖或完整63。原learner身份保持，实际steps2597603/2598186/2599115，GPU77/92/93/91%，含保活。

保存核验：131成员/1344615字节小包 `B/repository/RL_PARAMETER62_COMPLETE_20261028_135623/SMALL_EVIDENCE.tar.gz`，SHA256 `ef30758fde03a44350bbfd3a53fe99e9001cd4909c2c5624f065e86386802660`，所有成员逐字节及Python AST通过。
