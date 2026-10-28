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

## 15:36 UTC补充：原64连续等待、65恢复准备与终端误差集中诊断

本补充覆盖上文“65尚未准备”：现已准备并等待精确恢复检查，但**没有65训练或DECISION65**。开工及收尾实际fetch/read main8086d335f57069d95d66a0266ff7d97b1b50824f、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，无新增协议变化，非RL在途工作完整保留。

`B/runtime/parameter64_verified_wait_1526_20261028_v1` 实际15:25:28–15:35:31的21次观测，原三learner、归档/全loss/终端/标签/原62–64窗口/新65准备及五guard身份全部保持；steps2658374/2659141/2660372→2666135/2666995/2668086严格增长，无完整/失败。600秒有限observer自然exit0，非科学结束，不重启训练。新增ranked对照等待不在此初始观察列表中，另有RANKED_WAITER_EXTRA_SNAPSHOT实际身份核验。

同区间原guard117样本min73/67/62/67%、mean78.64102564/89.14529915/89.29059829/89.59829060%，低于50均0，最大间隔5.290058秒；包含合成保活，非每瞬时保证/纯训练吞吐。科学结束也继续guard；旧0%事件不删除，Direct不启动34。

### 65仅恢复检查及完整loss静态准备

`B/runtime/prepare_parameter65_20261028_v1` 来源为已验证64准备脚本；循环编号/零填充路径同时映射、逆变换/AST/日期/owner/opaque hash保持，原学习配置不变。新waiter2458384/start39669245，REGISTRATION SHA256 `7b76f3a9531d54a009936c9f22dc0c55f3a00dded86f7749f2b659038172d46c`，CPU53/14400秒，绑定原64三learner及归档身份。仅完整64归档/health通过且原learner退出后创建65恢复检查；不自动训练。实际缺DECISION65的launcher调用拒绝且没有建run，收据UNREVIEWED_LAUNCH_REJECTION已保存。完整64科学审查、图审、原62–64窗口及精确恢复后才决定是否继续。

为了避免此前已观测的copyfile同长度全零副本，新65部署基础设施改普通读写/fsync/逐字节回读、copystat保留元数据，拒绝覆盖已有目标；在原parameter63_loss/driver.log实际复制复核通过。它只改新准备/launcher的复制方法，没有改正在运行的64或任何learner/物理源码。原失败副本/诊断仍在prepare64/packaging_failure_v1。首次65真复制尚待父轮完成，不把探针当作完整65恢复通过。

`B/runtime/parameter65_loss_preparation_20261028_v1` 四脚本静态准备通过，全部49–64历史保留并仅追加65；paired64→65，原0600条件/原始门保持。逆变换/AST/实际diff已核验，尚无65 loss运行目录/PLAN/等待进程，须经科学审查且实际65启动后部署绑定。

### 下一个非重叠窗口65–67预登记

`B/runs/parameter_capacity65_67_reward_stability_20261028_v1` 在原64运行、65/66/67均未启动时登记，PLAN SHA256 `517dbefb03fe7630530100d658e35e6108528a18af564b01911b2e53a81bd0f0`。原5%描述性公式、近零1、bootstrap seed2026102855/5000次、anchor55、4m历史23/47和条件/门全保持。只变窗口62–64→65–67，源码逆变换/AST通过；原62–64 PLAN SHA44e0b484未改，仍待完整64，原59–61失败/历史通过保留。尚未启动新窗口waiter；如经完整审查启动65，再启动固定14400秒只读等待。登记不自动授权/派发后续训练，也不是新的停止门。

### 完整63终端误差集中诊断与预登记64后续

`B/runs/vmc63_ranked_terminal_diagnosis_20261028_v1` 对既有63 values.npz的全部1914终端保存值排序，保留全部行/每head masked SSE/贡献；全1914和/排序/唯一性、独立per-head算术通过，0网络前向/物理/优化/replay写入。属于看完63结果后的描述性诊断。

最高两条都来自历史active_short_train_0600，原terminal transition的step/condition/done/float32 reward与保存目标精确、rollout/模型hash/physical和Task/Strict标签一致：

|历史轮次/索引|穿透mm|Task / Strict|SSE62→63|增量|
|---|---|---|---|---|
|59 / 2464220|.2083269549|true / false|4.489379→2238.586046|+2234.096666|
|38 / 1603101|.2038815052|true / false|31.900988→2139.275917|+2107.374929|

两条均略超原.2mm外穿透门，物理无效但无abort。episode累计reward分别−34.677896/−34.634667；真正terminal transition reward约−28.415013/−28.432953，二者不可混淆。第59条增加主要来自in-bag head0/3，第38条主要来自in-bag head3；mask为0的其他正Q未算入误差，原mask不变。

两条增量合计4341.471595，大于全1884旧行净增量3034.513074；剩余1882旧行净变化−1306.958522。两条占全部1914 SSE9786.920510的44.7317617%。这说明此次旧行回归的误差集中，并不证明观测混淆、梯度因果或泛化；不能用剩余样本改善否定原全1884退化。

新增 `B/runs/vmc64_ranked63_terminal_followup_20261028_v1` 在64完整之前锁定全部1914原63排序及上述两个索引。PLAN SHA256 `2da6c78d525d4f6d39a52a55e47bd94bc0c073342a2774e27e22af4c9535f394`；waiter2704977/start39713360、CPU53/7200秒，绑定原64终端对照2178507/start39618553。只读该任务完成后的保存values，不重做前向/训练；全部1914旧数组、SSE/贡献应复现原完整64报告，两个样本不得替代全体或原五focus。真实不完整64调用拒绝且无输出，实际64结果尚待。

### 保存

本补充共享SSD小包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER64_WAIT65_PREP_20261028_153559/SMALL_EVIDENCE.tar.gz`，53成员/221104字节/SHA256 `574fa0e3f560a44bdfe473d21930463513604c608eb9c199f2a86c42af97c175`，普通读写逐字节、tar逐成员大小/hash与Python AST通过；[收据](RL_PARAMETER64_WAIT65_PREP_SAVE_20261028.json)、[清单](evidence/RL_PARAMETER64_WAIT65_PREP_20261028/MANIFEST.json)。大产物仍共享SSD，HDD配额满仅重写既有LATEST，非HDD/arm1全备份。原64和既有审计继续，Goal active，无子agent。
