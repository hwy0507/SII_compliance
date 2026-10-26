# 2026-10-26 参数batch65536第14周期与Direct多步目标第10周期

原Goal active，未健康收敛，每卡GPU≥50%尚未全部达到。本轮完成两个新的有限诊断、完整状态迁移验证，四路正式训练已启动并通过真实1000新增交互的启动审查。当前阶段仍运行，不能将局部loss或有限对照当作收敛。最新运行快照见 `docs/evidence/rl_batch14_multistep10_20261026/LIVE_STATUS.json`。

开工实时fetch/read main `bca5d6662a4426e3e54ea8d53ad2d7a04898ce32`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。上一目标回合只核对文档，按规则判为无进展；本轮重验旧作业结束、四卡0%后推进新实验。无子agent，不干预另一主机非RL。用户补充要求不要让GPU长时间空闲。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。所有大产物、环境和运行源码在本集群SSD；不是arm1共享全量归档。
物理/MJB/gates/filter/执行器/dt5e-5/30条件/SPT reward保持，正式网络/Adam/moments/replay/RNG/history全部保留；没有fresh reset、旧checkpoint回退或辅助权重推广。

## 参数：从完整13比较32768与65536

`B/runs/parameter_cycle13_batch65536_probe_20261026_v1`，三方法两臂各5000，共30000辅助更新；0物理，不保存/推广权重。父为准确完整13，SHA沿用上一交接。必须用 `published_pair_reduction_learner_20261026.py::pair_class` 恢复：I target minimum，A/V target mean，actor仍minimum。terminal128、target上界projection、原actorLR、UTD1保持。

两臂恢复后完整state逐项匹配正式父，初始RNG相同；batch不同，抽样数量及最终sample RNG不同，这是预期，不能宣称相同实际样本流。每臂20记录；独立核验全部预算、有限值、正式父完整digest、原replay不变、持久markers与图通过。

| 方法 | 终端MAE：32768 → 65536 | Q均值：32768 → 65536 | 5000更新耗时：秒 |
|---|---:|---:|---:|
| 阻抗I | 1.650115 → 1.350989 | −16.421789 → −16.416651 | 90.124 → 171.739 |
| 导纳A | .722079 → .668381 | −107.892662 → −108.195488 | 87.681 → 166.646 |
| VMC V | 1.196754 → 1.109237 | 12.463895 → 12.394792 | 88.204 → 167.455 |

较大batch减少了此有限对照的终端误差和部分抖动，但单更新耗时约1.9倍；这改变学习统计，不是等价优化，不证明在线成功率改善。A上一周期的任务退步、V正Q移动及I终端尾部仍需正式结果。
原probe PID1076194/1076196/1076198和review1183654均已结束，勿重复派发填占用。

## 参数正式14：只改batch，全部旧state保留

`B/runs/parameter_batch65536_cycle14_20261026_v1/{method}/train`：

- I PID1254686，GPU1，CPU13–25，12sampler。
- A PID1254688，GPU2，CPU26–38，12sampler。
- V PID1254691，GPU3，CPU39–51，12sampler。

父为 `B/runs/parameter_pair_reduction_archive_20261026_v1/{method}/cycle_00013.pt`，不从probe权重恢复。仅一个完整14，无自动15。
batch65536、UTD1；I minimum/A-V mean，actor minimum、terminal128/projection、actorLR I/V3e-4与A3e-5保持。
新增driver `resume_cheq_batch65536_stage_20261026.py` 严格核验父登记/审查/依赖及所有受保护字段，只允许batch与新阶段记账变化。
原冻结trainer不改：在独立命名空间精确替换一次原batch上限守卫为 `batch_size == 65536, UTD == 1`，保存原/修改后hash及源码。
三路check-only完整learner state和二次恢复均精确相同，拒绝未经登记的batch/UTD/clock/reducer/权重/周期/推广变化，0优化更新。

真实启动各1000新增交互通过：全部原replay前缀/history/优化器配置/三marker、12真实sampler亲和性/MJB、参数输入/当前nextclock/reward重建误差0。
启动审查不是A/V内部动力学逐子步重放；全周期终端与健康审查尚待。
归档PID1286930在 `parameter_batch65536_archive_20261026_v1`，只读协调PID1286970在 `parameter_batch65536_cycle14_review_20261026_v1`；启动审查1286924已结束。后续先核实原handle，不因观察超时重启。

## Direct：精确clock9的1步与32步目标有限对照

`B/runs/serl_cycle09_multistep_probe_20261026_v3`，两臂各2000 outer，即总32000 critic+4000 actor辅助更新；0物理，不保存/推广权重。
精确父 `B/runs/serl_clock_cycle09_archive_20261026_v1/direct/cycle_00009.pt`，SHA `a1a26f285f990ee2308f70a2f178527c2fabfec2b0e6bb1c973e00115981a61d`。
每臂完整learner/Adam/RNG直接匹配正式9，采样同样的32768条历史索引、相同最终抽样RNG；诊断本身不改变完整learner状态。

六份正式journal覆盖400935行、300个episode，每行step/reward/done唯一匹配原replay，按cycle+condition恢复交错流顺序，全部current/next clock与非终端相邻状态精确相等。没有把全局相邻索引当相同episode。
独立重算所有终端前33行及1000随机行，1步派生结果等于原奖励/mask/endpoint；32步在终端截断，不跨episode。

目标为 `sum(gamma**j * reward[j]) + gamma**k * (1-done_at_endpoint) * min_pair_target_Q(endpoint)`；固定gamma=.9995，最多k=32。
保留官方源码1fa2af7496be042e43d36120a7c8d1bfb59、10critic/随机2target/noentropy backup/8critic:1actor。actor仍canonical48，时间仅critic叶；没有未来奖励进入actor。
这是有离策略偏差的历史行为多步目标，没有importance correction，不能当当前策略真实回报或官方原样SERL复现。

| 诊断 | 1步对照 | 32步 |
|---|---:|---:|
| terminal MAE | .559263 | .314708 |
| terminal p95 | 1.008290 | .799384 |
| terminal max | 42.175629 | 12.293819 |
| replay Q均值 | 27.106968 | −20.761347 |
| 固定pair的1步TD MAE | .063595 | .136464 |
| 固定pair的32步TD MAE | 1.588364 | .165193 |

32步早期terminal MAE一度升至约11，随后下降，末尾仍有尾部波动；低1步TD并未证明对照的正Q合理。最终32步拟合改善支持一个有限在线周期，但不证明任务恢复、行为安全或收敛。
独立来源/digest/预算/RNG/有限值审查与图已完成。原probe1200322已结束勿重复。

失败均保留：v1在独立标量回报核验发现向量乘法先用float32再累加，与预期float64求和不同，0更新；v2改为乘法前显式float64后通过回放gate，但启动环境漏 `CUDA_VISIBLE_DEVICES=0` 被严格单GPU守卫拒绝，0更新。v3保持守卫并正确设置环境后完成。
首次独立review误用无JAX的Torch环境，失败日志保留；换既有serl_env重新只读审查通过，没有重跑probe。

## Direct正式10：持久化派生目标与在线成熟回放

`serl_multistep_state_adapter_20261026.py` 新增 `multistep_target_extension`，不改变旧clock结构或任一旧网络/Adam/RNG叶。
原单步replay所有字段保留；另存派生reward/bootstrap/endpoint/length和mature/pending索引，保存并严格恢复这些状态及原replay RNG。每流按32步成熟，短terminal一次性冲刷剩余行；只在mature集合均匀采样。拒绝本有限阶段出现replay容量环绕，不静默损坏跨流索引。
新loader必须同时保留clock和multistep markers，禁止用旧SerlClockLearner/SerlStateLearner恢复而丢失32步规则。driver只接受完整周期父；不把未结束流的partial checkpoint直接作为新物理episode续训。

迁移 `B/runs/serl_multistep_preparation_20261026_v2/REVIEW.json`：

- 剥新learner marker后正式9完整state精确，剥replay派生区后400935原replay、RNG/cursor/capacity全部精确，旧history/steps保持。
- 400935历史派生结果digest匹配独立probe gate。
- 三交错流长度4/35/66，共105在线测试行，覆盖不足32、跨32及终端冲刷；每次加载/采样批与RNG一致，全部派生目标独立标量重建精确。
- 实际batch与probe32步构造一致，缺失/改变marker负守卫通过。两次恢复后的完整下一8:1更新全state/metrics相同。
- gate共16critic+2actor辅助更新，保存前恢复未更新的最初迁移状态，无辅助权重推广。

v1 preparation在独立probe review尚未可用时停止，0更新，错误/源码保留；v2确认review通过后才运行。
prepared9 SHA `6bf4ec143049657f5a071569ce24d22ecca906e1446d23c1e9b6b88be4ccc44f`，路径 `B/runs/serl_multistep_preparation_20261026_v2/prepared_cycle09.pt`。它是正式9的无更新表示扩展，不是候选训练权重。

正式PID1595728，GPU0/learnerCPU0、30sampler共享CPU1–12，`B/runs/serl_multistep_cycle10_20261026_v1/direct`。只一个完整10，无自动11；batch32768、官方8:1与零示范/纠正/旧CHEQ/nominal混合保持。
公共第一动作 `(raw_a0+1)/2`，public0为nominal，增加它减慢WBC。原物理trainer仅通过已登记变换增加显式replay stream id，沿用共享CPU调度，原/修改后源码hash保留。
额外正式check-only从新建learner恢复prepared完整state相同、合同/亲和性负守卫通过。
真实新增1000/8000启动审查：prepared完整旧prefix/history/config、全部新actor48/action7/clock/reward重建0误差、30MJB/30live亲和性；其中178新mature、822pending，全部新派生目标/索引/未成熟排除独立精确通过，无terminal覆盖。
归档PID1621561在 `serl_multistep_cycle10_archive_20261026_v1`；完整10只读协调PID1660936在 `serl_multistep_cycle10_review_20261026_v1`，将核验所有新派生目标、330历史terminal与1/32步TD，完整state只读不变。启动审查1621559已结束。

## GPU、吞吐和下一项等价优化

参数14正式、Direct辅助/启动窗口：GPU0–3均值20.45/72.55/76.72/76.33%，GPU0不得计作正式达标。
随后纯四正式窗口 `B/runs/multistep10_batch14_gpu_profile_20261026_v1/PROFILE.json`，60样本、63.92秒，四个原learner全窗口存活、无辅助优化器或冻结评估：

| 方法 | GPU均值 | transitions/s | learner核 | 物理worker核 |
|---|---:|---:|---:|---:|
| Direct10 | 44.53% | 21.213 | .812 | 4.075 |
| I14 | 70.62% | 23.419 | .940 | 7.358 |
| A14 | 73.53% | 25.171 | .995 | 8.526 |
| V14 | 74.87% | 25.312 | .995 | 8.344 |

参数GPU已超过50%，但吞吐低于此前batch32768窗口，不能声称整体提速。Direct仍未达50%，未实现用户全部资源要求。
45秒外部栈采样 `serl_multistep10_live_stack_20261026_v1/capture/SUMMARY.json` 确认原PID持续推进；约20.69%叶在采样dict索引、7.40%在派生nextobs索引，20.18%在JAX array取值。它含idle且非CUDA kernel计时，不把重叠栈比例当精确瓶颈归因。

发现原replay先gather单步reward/nextobs又覆盖，新增候选 `serl_multistep_replay_gather_20261026.py` 仅跳过这两次无用gather。
`B/runs/serl_multistep_gather_microbench_20261026_v1`：28种批次对照全部字段和RNG逐项相同，五轮交替顺序各100次，采样中位耗时11.147→7.600ms，约减少31.8%。0优化更新/0物理，原父replay不变。
追加完整更新gate：从同prepared9分别恢复原/优化采样器和完整learner，下一次官方8:1更新的全state、metrics、采样RNG精确相同；共16critic+2actor辅助更新，无权重保存。**尚未部署到当前10，也未证明在线吞吐改善。** 后续完整边界迁移须保留全部state、验证恢复守卫并登记/实测，不覆盖运行中的冻结源码。

## HDD配额与仓库位置

开工尝试写新脚本触发 `Disk quota exceeded`，产生0字节未提交文件，没有运行该文件。普通df显示底层空间充足，不能识别该4GiB目录配额。
为保留完整仓库并恢复小备份能力，将仓库全部复制到 `B/repository/SII_compliance`，7296文件逐大小与SHA匹配、符号链接目标核验后移除已核验的旧物理副本，原HDD `SII_compliance` 路径保留为指向SSD副本的目录链接。Git历史/原文件全部保留，旧路径仍可用；收据 `B/repository/RELOCATION.json`。
这意味着活动仓库现在依赖SSD；独立小文件备份仍放原HDD backup root，大型产物没有因此得到HDD/arm1全量保护。

## 接续要求

先实查四正式PID、归档和review。它们当前正在完成登记14/10，勿重复派发或回退13/9。收到完整结果后再决定下一阶段，不把有限probe或早期loss作为自动续训依据。
重点审查参数14的全30条件任务与reward是否恢复、Direct10是否出现Task成功及早abort、Q/终端尾部是否稳定；已备齐完整边界只读review，不重启已完成辅助。
当前正式状态必须保留新增marker和派生回放。完整14/10归档一旦存在，后续应使用这些最新正式父，不能继续从本文的旧13/9准备权重重复训练。
持续每卡GPU≥50%、健康收敛、最终冻结比较和ESN/SPT交付均未完成。原Goal保持active。

收尾fetch/read并快进整合远端main `0a6189c5fcdbea8db6c1dcafd34c2ed05693ec33` 的独立非RL第七条件/63回合审查更新，双方记录完整保留，不改变另一主机运行。


## 独立备份的实际范围（收尾更正）

仓库迁移后HDD配额依然受限：未压缩小证据副本和完整压缩包两次写入均失败，不能称HDD完整证据备份已完成。仅删除本次失败的不完整副本，所有源文件、SSD完整压缩包、GitHub提交均保留。
HDD目录 `/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_BATCH14_MULTISTEP10_STATUS_20261026_140709` 中，`ESSENTIAL_BACKUP.tar.gz` 只包含本轮10个新增源码及本报告，包内逐项SHA和整体SHA核验通过，另有 `HANDOFF.md` 与 `BACKUP_RECEIPT.json`。
完整本轮133文件证据包已在SSD `B/repository/RL_BATCH14_MULTISTEP10_29d142e8.tar.gz` 逐项核验，并已发布GitHub提交29d142e；它没有完整复制到HDD。最新交接入口已更新，明确这些范围。大型checkpoint/replay/物理轨迹仍未得到HDD/arm1全量副本。
