# 完整65审查、固定终端对照与第66轮接续

2026-10-28 17:08 UTC，Goal active，尚未整体收敛。实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。Torch `B/env/bin/python`，Direct JAX `B/serl_env/bin/python`。前次准备和固定样本登记见[65早期交接](RL_PARAMETER65_EARLY_ANCHOR_20261028.md)，前次已发布a998343cad916c1758cf33151fa3c330dfe267c8。

## 完整65科学结果

原 `B/runs/parameter_capacity_pool30_cycle65_20261026_v1` 三learner自然完成，均为stopped_at_complete_cycle；不是观察器超时或训练异常。每路30×55秒/41250新增、无abort。完整64的2676648/2677250/2678250行replay所有字段、历史、优化器超参数保留，新reward按冻结interval日志逐步重建误差0，网络/优化器数值有限。batch65536/UTD1/终端权重128/4m append和历史23/47 marker保持，未改门/物理/LR/目标。

|方法|steps / updates|reward均值|Task / Strict（各30）|critic首→末1000|critic均值 / 最大值|
|---|---|---|---|---|---|
|impedance|2717898 / 2712899|-4.029249489|17 / 16|1.729979808→1.794003460|1.689982716 / 22.743158340|
|admittance|2718500 / 2713501|-8.478569768|14 / 14|1.297140518→1.178396711|1.209419590 / 16.899009705|
|vmc|2719500 / 2714501|-2.822722886|17 / 17|1.000113431→0.758601528|0.857225746 / 16.500747681|

完整checkpoint位于 `B/runs/parameter_capacity_pool30_cycle65_archive_20261026_v1/{method}/cycle_00065.pt`：

- impedance SHA256 `45590ee3053ecb778442dc694100f2f2f1f94fe83e08a18440d31c374dc984e2`。
- admittance SHA256 `f82e1c28902b08b75baf8fc9f2ea0408086770bf8f97b92bf9a427bd740e3f7d`。
- vmc SHA256 `1d72af6620ce15dad2cb2996ddae9e9f293a16189d1d91cba8807e79abf34fc2`。

全loss独立标量复算、连续步号/全数值有限与实际loss.png图审通过。I actor25.632912→25.162023持续下降，critic末段尖峰较密；A actor−9.895210→−9.578409持续上升，critic初降后较平、局部33000附近有限尖峰；V actor先降至约−14.23再升到−14.112847，critic末段下降但仍有有限尖峰。有限尖峰不新增失败阈值；actor和reward仍变化，不能宣称整体稳定。

健康诊断 `B/runs/parameter_capacity_pool30_cycle65_review_20261026_v1/health/DIAGNOSIS.json` 完成，实际training_diagnostics.png已查看；长标题右端裁切但轴和数据可读。终端in-bag MAE I.324930287/A.318129445/V.270246892；采样TD MAE.228646014/.252027190/.148394880。网络状态保持，诊断0优化。I alpha末段略升，V总体较低且波动；零终端误差不是停止门。

## 全标签64→65

`B/runs/parameter_task_label_audit65_20261028_v1` COMPLETE64_65/FINISHED65/独立COMPLETE64_65_SAVED_REVIEW通过。全部180保存rollout、90reward对和计数核验，没有Task-only遗漏。

- I long0000由Task/Strict真变假，reward17.427498→−32.994113；物理有效仍真。short0600 Task仍真，穿透.190713768→.214653472mm超过原.2mm而失Strict，reward19.357919→−34.714759。
- A各条件标签不变，Task/Strict14/14；reward−8.512810→−8.478570接近，不能仅两点声称稳定。
- V short0600 Task仍真，穿透.223143468→.192992514mm恢复Strict，reward−34.815386→17.688778。全V reward−4.607564→−2.822723改善，未证明泛化。

原62–64三路未过原描述性5%（I近零保护）、原59–61失败及I56–58/V53–55通过保留。原65–67窗口仍待完整66/67，不能提前pass或移端点。Direct33仅原训练集经验数值收敛且Task/Strict0/0，保持launch34=false。

## 全1944固定VMC终端与全部64新增30对照

`B/runs/vmc65_terminal_anchor_followup_20261028_v1` FINISHED/REVIEW/SAVED_VALUES_REVIEW与实际follow65.png检查完成。全1944固定64 observations/actions/rewards/masks精确，权重/forward RNG保持，health65复现；SSE12834.464224739→6717.641319237（−47.6593553%）。旧贡献.701902540432→.362022514359；用旧denominator的after贡献.367569890027；65新30贡献.002374328243，全1974贡献.364396842603。保存values SHA256 `073a761d55173b83edeaa3e3cb2b4f68ece80d46df99f2b17aaed6878a3722f4`。

原五focus全部保留：

|replay index|SSE64→65|变化|
|---|---|---|
|2050526|4.616749→78.408266|退化|
|2299142|199.500995→178.948025|改善|
|2046571|2.008070→62.917002|退化|
|2423133|4.818018→38.257822|退化|
|2423122|1159.197633→2250.259572|退化|

图中近原点标签部分重叠，精确值保存在REVIEW；全体改善不能替代局部退化，也不建立在线梯度因果。

预登记 `B/runs/vmc65_new64_terminal_followup_20261028_v1` 固定64新增全部30，FINISHED/REVIEW/独立向量SAVED_REVIEW通过，0新前向/物理/优化。SSE6294.889150171→419.908950389，26改善/4退化；贡献.344211032334→.022628746101，after用旧denominator .022975776325。原最大short0600/index2670722 SSE5959.294956349→382.705052265，贡献.325853820059→.020623657389。它是固定64失败样本的Q拟合对照，与65新rollout成功标签不同，不能混淆。保留全部30和全1944/原五focus，不用子集改善替代整体结论。

## 精确恢复与有限66

`B/runtime/prepare_parameter66_20261028_v1` 的三路完整65全state/replay/下一65536 check-only全部exit0；实际科学与图审后DECISION66绑定29项证据。17:02:44 UTC启动一个原配置有限66：

|角色|PID / start ticks|
|---|---|
|I learner|1279033 / 40268104|
|A learner|1279034 / 40268104|
|V learner|1279035 / 40268104|
|archive|1279036 / 40268105|
|startup审查|1279037 / 40268105|
|全66 loss|1286574 / 40270137|

运行目录 `B/runs/parameter_capacity_pool30_cycle66_20261026_v1`，每路30sampler、GPU1/2/3。全66loss `B/runs/parameter66_loss_20261028_v1`，PLAN SHA256 `02e6e93211d3d78ff15f5a5b82141d6d6e319c3339df5767f76243b68cf24431`；完整49–65历史保留追加66、paired65→66，等待7200秒。没有自动67或状态重置。原65–67等待3549846/start39897958继续，PLAN `517dbefb03fe7630530100d658e35e6108528a18af564b01911b2e53a81bd0f0` 不变，输出REVIEW.json，观察到期不等于训练失败。

## GPU与连续观察

`B/runtime/parameter65_verified_wait_1648_20261028_v1` 保存16:47:52–17:01:56共29次真实观测；原learner身份持续核对到自然FINISHED/退出，所有必要审计路径齐全后observer正常结束，无科学重启。同期165条guard min75/67/67/68%、mean79.02424242/80.00606061/80.93333333/80.06060606%，低于50全0，maxgap5.278063秒。即时查询可能与guard采样不同，例如最初GPU0即时74%；均如实保留。

原v5 `/tmp/sii_gpu_util_guard_20261028_v5` 保持：supervisor3256866/start37410686，workers3256867–3256870/start37410690/37410690/37410691/37410693。科学完成后也继续保活；v4 STOP保留、v5 STOP不存在。含合成负载，不等于纯科学吞吐或每瞬时保证；历史09:03全0事件保留。当前不是跨重启服务，操作前检查PID+start ticks。

## 保存与下一步

完整65大checkpoint/replay/raw继续留共享SSD，HDD只重写既有LATEST入口，不能称HDD/arm1全备份。下一步先核实66实际startup前缀、继续全66loss与原65–67窗口，再准备66固定终端/全标签和67仅恢复；完整科学证据之后才决定后续训练。Goal active，无子agent。

17:08实际startup完成且passed：I/A新增1000、V新增2000，全部旧2717898/2718500/2719500行replay逐字段精确、history/optimizer超参数/30sampler/MJB/clock/action保持，新reward重建0。startup1279037已自然退出，不重启。此启动检查无terminal覆盖，不代替完整66审查。

`B/runtime/prepare_parameter66_20261028_v1/SNAPSHOT66.json` 核对原66三learner/归档/全loss/原65–67窗口及五guard身份live；17:08 steps2721215/2721843/2722881，GPU80/94/96/94%，没有训练失败。尚未准备66全终端/全标签/67恢复，不误称已部署。

本次共享SSD小包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER65_COMPLETE_20261028_170801/SMALL_EVIDENCE.tar.gz`，166成员/1781058字节/SHA256 `71e650f2544887757ca306f731445d06820cd058f1aa92331605091c7545c31d`，普通读写/fsync/逐字节、tar成员大小/hash及Python AST通过；[收据](RL_PARAMETER65_COMPLETE_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER65_COMPLETE_20261028/MANIFEST.json)。大产物仍原共享SSD，非HDD/arm1全备份。

开工和收尾实际fetch/read maina998343cad916c1758cf33151fa3c330dfe267c8、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未见新协议变化，另一主机非RL工作完整保留。Goal active，无子agent。
