# 第64轮前5000审查、全1914固定终端锚点和在途交接

2026-10-28 15:17 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；Torch `B/env/bin/python`。完整63结论、三路checkpoint hash及64精确恢复见[完整63交接](RL_PARAMETER63_COMPLETE_20261028.md)，已发布7357590ea307160597c0236f4decfa529765c0a8。本次继续原64，没有训练重启或科学配置修改。

## 64当前状态

`B/runs/parameter_capacity_pool30_cycle64_20261026_v1` 原I/A/V learner1505861/1505863/1505865及archive1505869，start ticks均39497113。15:16实际steps2651428/2652167/2653353，三路运行中、没有完成或失败；30sampler/路，GPU1/2/3，原reward/gate/物理/LR/终端权重128/batch65536/UTD1/4m append保持。startup1000/1000/2000已审，全部旧replay/optimizer/history/RNG恢复，未自动65。

完整64 loss `B/runs/parameter64_loss_20261028_v1` 原waiter1522440/start39501622继续；原62–64稳定窗口1758711/start38725355继续，原PLAN不变、输出REVIEW.json，目前待64。59–61失败和原I56–58/V53–55通过保留，不按新结果移动端点。Direct33仅原训练集经验数值收敛而Task/Strict0/0，不启动34。

## 固定前5000

`B/runs/parameter64_first5000_20261028_v1` 在原64启动且前缀已可用后登记，只读原optimizer日志。逐字节匹配原5000行、全部数值有限、步号连续、独立标量均值/最大值复算和实际loss.png图审通过。

|方法|critic首1000→末1000|critic最大值|actor首1000→末1000|
|---|---|---|---|
|I|2.383212119→2.237741029|19.714653015|26.189492863→26.175659328|
|A|1.495751109→1.388446475|8.212139130|−10.111025700→−10.120437746|
|V|.741987578→.645007815|8.659723282|−14.400863678→−14.384290198|

I critic有有限尖峰，actor中段微升后小降；A critic轻微下降，actor先降后末段回升；V critic滚动曲线浅U形，局部2700附近有限尖峰，actor末段小幅上升。只描述早期5000，不能替代完整轮次/奖励稳定或收敛结论，不新增尖峰失败阈值。

## 全1914固定终端与全部标签审计

`B/runs/vmc64_terminal_anchor_followup_20261028_v1` 从完整63 checkpoint提取全部1914×57终端输入，indices/reward/mask/Q/denominator与已独立审过的63保存数组精确一致；独立标量SSE9786.920509937361。anchor63.npz SHA256 `0a23517524a72710ae8e46d77ad99f23d726b9cff0727674ee2f9322c250e761`。没有新前向、物理或优化。

等待2178507/start39618553，CPU53/7200秒，PLAN SHA256 `317134860c70a2e4ae68659514e4b6b5073de4a3dac2cec9d4baa4d93c15267a`，绑定真实64 jobs/monitor/sourcehash；等完整64归档且原learner自然退出后才比较1914旧行和30新增终端。原五focus全部保留，零终端误差不是停止门。实际64对照、独立数值复核和图审尚待。

准备期间两个基础设施失败完整保留：过严静态owner检查误要求无基路径的track.py含owner；数字边界映射漏掉零填充cycle_00062.pt，实际读取在模型加载前拒绝，后续缺ANCHOR_REVIEW也拒绝。修正为原文owner存在性保持及显式00062/00063同时映射；原源/失败记录在rejected_padded_mapping，最终逆变换/AST/真实checkpoint hash及全1914提取/复算通过。未影响训练，未掩盖失败。

`B/runs/parameter_task_label_audit64_20261028_v1` 全标签等待2178510/start39618553，CPU53/7200秒，PLAN SHA256 `5d153e4020d19db6f85f84afeb853a0ba02d33764839b264dce7dc38af82635a`。auditor与已验证63版本字节相同，waiter只改63→64阶段；实际未完整64输入调用被拒绝且没有输出。完成后逐全部180rollout/90reward对比较Task/Strict/physical/abort；此时尚无64标签结论。第65轮恢复准备/训练尚未启动。

## GPU和恢复

`B/runtime/parameter64_verified_snapshot_1515_20261028_v1/SNAPSHOT.json` 已核对三learner/归档/全loss/两新审计/原稳定窗口及五guard身份全部live。15:06:16–15:16:20原guard119采样，min74/68/68/63%，mean78.45378151/88.64705882/89.77310924/89.25210084%，低于50全0、maxgap5.242372秒；即时独立GPU79/96/91/95%。包含合成保活、非纯科学吞吐或每瞬时保证，历史0%事件仍保留。

实际v5 `/tmp/sii_gpu_util_guard_20261028_v5`：supervisor3256866/start37410686，worker3256867–3256870/start37410690/37410690/37410691/37410693。用户要求科学完成后也继续运行保活，v5 STOP不存在，v4 STOP保留；该守护目前不是跨重启服务。不要因观察器超时/退出重启训练，所有行动先核对PID+start ticks。

## 保存与下一步

共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER64_EARLY_ANCHOR_20261028_151719/SMALL_EVIDENCE.tar.gz`，49成员/1305865字节/SHA256 `6727f2ebb279d30a79159e5cd7247a0ed5e562d08e19e41f31fd161e434f29a5`，普通读写/fsync/逐字节和tar成员hash、Python AST均通过；[收据](RL_PARAMETER64_EARLY_ANCHOR_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER64_EARLY_ANCHOR_20261028/MANIFEST.json)。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份。HDD配额满只重写既有LATEST入口。

本次接续开工mainb980c260、保存后main7357590e、baselinef6e8f8c实际fetch/read，非RL在途更新完整保留。下一步等待原64完整，核对全loss/health/标签/固定终端及原62–64稳定窗口，实际查看结果图，再决定有限后续；不凭早期loss停止或宣称收敛。Goal active，无子agent。
