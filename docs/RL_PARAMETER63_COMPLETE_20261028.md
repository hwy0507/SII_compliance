# 完整63审查、固定终端退化与准确续训64

2026-10-28 UTC，Goal active。计算主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，仓库 `B/repository/SII_compliance`，Torch `B/env/bin/python`。开工实际fetch/read main5f0efa58、baselinef6e8f8c；收尾mainb980c260的非RL教师对照/v6重采更新已读并fast-forward保留，本机冻结RL配置未变。

## 完整63

`B/runs/parameter_capacity_pool30_cycle63_20261026_v1` 三原learner自然结束，各30×55秒、41250新增、无abort。完整归档/审查位于 `B/runs/parameter_capacity_pool30_cycle63_review_20261026_v1`：所有62 replay旧行精确保留，历史与优化器保持，新reward按冻结物理区间journal复算误差0，网络/优化器有限。不是重仿真原子步物理。

|方法|steps / updates|reward均值|Task / Strict（分母30）|critic首→末1000|critic mean / max|
|---|---|---|---|---|---|
|I|2635398 / 2630399|−2.392741760|18 / 17|2.602483042 → 2.312614283|2.422131085 / 42.105827332|
|A|2636000 / 2631001|−13.711200693|12 / 11|1.289616407 → 1.502003641|1.318255592 / 26.354633331|
|V|2637000 / 2632001|−2.856739508|17 / 17|.957334392 → .688026742|.794014416 / 15.718063354|

全loss `B/runs/parameter63_loss_20261028_v1` 的独立保存复算通过：全部数值有限、步数连续、各41250记录/30完整回合、配对来源/模型/evaluator hash一致。实际loss.png和health图已查看并写PLOT_INSPECTION。I critic约2–3波动、15000局部隆起及34000后较密尖峰，actor先略升再持续降26.712457→26.205839；A critic33500附近burst并抬高后段均值，actor−10.384854→−10.114598持续上移；V critic总体下降，actor先降至约−14.53再回升到−14.418246，仍非平坦。有限尖峰不新增失败阈值。

health固定checkpoint terminal in-bag MAE为I .384182405、A .316829588、V .316734334；sampled TD MAE .254053000/.237454444/.157552838。Q超过当前soft bound比例0/.000878906227/.001269531203，非完美校准。I entropy中段下探、alpha短暂抬升再回落，全部有限；诊断0优化、network state不变。health长标题右端裁切，数据/轴可读。非零终端误差不作为新停止门。

完整63 checkpoint在 `B/runs/parameter_capacity_pool30_cycle63_archive_20261026_v1/{method}/cycle_00063.pt`：

- I SHA256 `25abfec6ce636c90b4b03c6cc10d9a5511ca1589dd0817dd2c3319b77352b5b6`。
- A SHA256 `e79ceb72fe5c9669dc9ee97445fa669cda94bf724f213a5cd12da573e6bb7644`。
- V SHA256 `46c3f151864b9e028e747ab5e7a9c84b695ae493f16674eb394e499d5b2b22a6`。

## 全部62→63标签复核

`B/runs/parameter_task_label_audit63_20261028_v1` COMPLETE62_63及新增独立COMPLETE62_63_SAVED_REVIEW核对180保存rollout/90reward对、全部Task/Strict/physical计数、原Strict/abort变化列表通过，本轮无Task-only遗漏。

- I long0000恢复Task/Strict；short0100穿透.200854969→.183909843mm，Task保持true且physical/Strict恢复。均值由−5.822771830回升至−2.392741760。
- A short0100穿透.157312846→.206329078mm，Task保持true但physical/Strict失效。long0200、long0900、short0000、short0900失Task/Strict；long0300、short0200恢复。均值由−8.573957478降至−13.711200693。所有失败保留，原.2mm门不变。
- V short0000穿透.226158827→.118774001mm，Task保持true且physical/Strict恢复；均值由−4.613581712回升至−2.856739508。

## 全1884固定旧终端与新增62全30子集

`B/runs/vmc63_terminal_anchor_followup_20261028_v1` 已完成。旧1884输入/动作/reward/mask精确、全部1914 CPU Q及health复现、权重/RNG不变、独立标量算术通过，实际follow63.png已查看。旧SSE **6702.415584636→9736.928658179（增加45.2749167%）**；旧贡献.378266266764→.541142209332，使用旧分母after .549803996688；新30贡献.002778330818，全1914贡献.543920540150。values.npz SHA `24fbf425d57f9f167bbfd44e76b16a2d8a592e23378b8a158cfd011e79c76825`。

原五focus：2050526 SSE9.808205→146.377992、2299142 82.452507→362.458630、2423133 38.263001→436.588628退化；2046571 12.326942→7.549246、2423122 17.582179→.300759改善。图中另有两个旧样本SSE升至2000以上；原点附近标签重叠，精确身份以REVIEW数值为准。不作在线梯度因果或零误差停止门。

本轮新登记 `B/runs/vmc63_new62_terminal_followup_20261028_v1`，在63训练期间、完整结果之前固定全部30条新增62终端进行后续对照。PLAN SHA `f2981f0876a37de87723041d57d1b7c78bcb85a6eae39119fb60a6996c58243e`，只读waiter886996/start39357265已自然完成。未完整63实际调用拒绝且未写结果；只等待原17088完成，不重复CPU前向或训练。全1884 before数组/denominator一致，旧30逐行SSE/contribution精确复现，所有30保留。

这30固定旧样本SSE **4152.014984160→316.331301608**，贡献.234366539225→.017583510387，使用旧分母after .017864097017；20改善、10退化。上轮最大short0000/index2588236 SSE3485.716113928→207.046615775，贡献.196767841012→.011509160788；short0100 SSE304.788952→7.776803、short0600 186.420489→46.556463也改善。**该子集改善不能替代全部1884的退化结论。** 无新物理、网络前向、优化或replay写入。

## 准确续训64

`B/runtime/prepare_parameter64_20261028_v1` 三路完整63全state/replay/下一65536恢复检查exit0，实际checkpoint hash与完整63一致。DECISION64绑定上述完整科学证据、原59–61失败/历史通过和原62–64 PLAN；原launcher的reward_window56_58字段保留。奖励仍明显变化、actor/critic未稳定，因此续一个原配置有限64，不重置、不引入辅助权重、不改reward/物理/gate/LR/mask/终端128/batch65536/UTD1/4m append。

**14:54:15 UTC实际启动64**，run `B/runs/parameter_capacity_pool30_cycle64_20261026_v1`：I1505861/A1505863/V1505865及archive1505869的start ticks均39497113；启动审计1505872/start39497114。GPU1/2/3、CPU13–25/26–38/39–51，每路30sampler，仅一轮，不自动65。

完整64 loss已由静态准备源部署到 `B/runs/parameter64_loss_20261028_v1`，绑定实际jobs/sourcehash；waiter1522440/start39501622、CPU54/7200秒，PLAN SHA `49245498c2e145beec881a00f846167aca276583056f2ec5b433e04d0c0d45fc`。全49–63历史保留追加64，完成后独立复算及实际图/全标签审查仍需执行。

原 `B/runs/parameter_capacity62_64_reward_stability_20261028_v1` waiter1758711/start38725355继续，原PLAN SHA `44e0b484fb61c8c640e2e56bfe1ca36b08d96c2098c2c393104ebf9c3713dfc5`不变，现已完整62/63仍待64，不能提前称窗口通过/失败，结果文件为REVIEW而非FINISHED。原59–61失败及I近零保护、I56–58/V53–55历史通过保留；Direct33原经验数值收敛而Task/Strict0/0，不启动34。冻结55/41→55比较不改。

## 等待、GPU和可靠恢复

`B/runtime/parameter63_verified_wait_1429_20261028_v1` 共33真实样本（14:29:53–14:45:57），原身份保持至A/V自然结束；随后三实际FINISHED确认各自完整，观察器exit0，不重启训练。33样本内原guard日志188条：min72/65/66/65%，mean78.55851064/88.60638298/88.56382979/88.23936170%，低于50均0，maxgap5.27849078秒。含合成保活，非每瞬时保证/纯训练吞吐，历史共同0%异常保留。

v5实际 `/tmp/sii_gpu_util_guard_20261028_v5`，五PID3256866–3256870，start37410686/37410690/37410690/37410691/37410693保持；用户要求科学完成后也继续保活，旧v4 STOP不动，当前不是跨重启服务。14:55:45实际64 steps2635887/2636465/2637497，GPU76/94/93/96%，原三learner身份live。

最新小证据见[收据](RL_PARAMETER63_COMPLETE_SAVE_20261028.json)与[清单](evidence/RL_PARAMETER63_COMPLETE_20261028/MANIFEST.json)。大checkpoint/replay/raw仍共享SSD；HDD配额满只重写既有LATEST，不声称HDD/arm1全备份。原64继续，完整结果后完成62–64窗口，再决定后续，Goal active，无子agent。

14:58补充：实际64 startup I/A/V前1000/1000/2000审查通过，全部旧2635398/2636000/2637000 replay行、history、optimizer hyperparameters、30sampler及MJB保持，新reward复算误差0。原learner身份保持，steps2638189/2638805/2639867，GPU79/76/92/95%，非完整64或终端覆盖。

15:07保存补充：首次copyfile产生driver.log同长度全零副本，源日志正常，底层原因未知；原partial和诊断已保留于 `B/runtime/prepare_parameter64_20261028_v1/packaging_failure_v1`。改普通读写/fsync/逐字节回读，全部173成员及归档成员hash/大小和Python AST通过。共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER63_COMPLETE_20261028_150713/SMALL_EVIDENCE.tar.gz`，1384696字节，SHA256 `d735f6c43526b82a19bffa353eaec2942498b02263c83a6378abfc62811b629c`。15:06原64三learner/五guard身份通过，steps2643788/2644407/2645573，GPU74/92/91/93%；接续实际fetch/read mainb980c260/baselinef6e8f8c无变化。
