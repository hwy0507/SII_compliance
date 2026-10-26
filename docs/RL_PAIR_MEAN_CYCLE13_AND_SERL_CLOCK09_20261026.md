# 2026-10-26 参数target-pair均值对照与cycle13、Direct critic-clock cycle9

原Goal继续active，尚未健康收敛，每卡GPU≥50%仍未达。上一轮完成12与冻结11审查，本轮推进四路正式训练；收尾Direct9已结束且审查完成，三参数13仍在运行。
本报告覆盖 `RL_EXACT_PIPELINE_CYCLE12_AND_SERL_CLOCK_20261026.md` 的“当前无正式learner”状态。
开工fetch/read main d6f48179054e94bb3a35e0785bf908f25cee5165、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d；
旧PID已退出、四卡0%实查后才登记新run，不重启旧作业。无子agent，不干预另一主机非RL。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
物理/MJB/gates/filter/执行器/dt5e-5/30条件/SPT reward不改；大型产物在本集群SSD，HDD只备份小证据，非arm1全量归档。
本轮有明确算法适配，不能称原CHEQ/SERL论文原样复现或等价学习改动。所有正式旧网络/Adam/replay/RNG/history保留，无辅助权重推广。

## 参数有限对照：target pair minimum与mean

背景：完整12终端拟合改善，但A/V Q均值−232.570/−77.636仍负移，末1000 q_loss115.199/98.975。
在准确完整12上比较随机两target critic取minimum与mean，保留相同抽样pair、actor的minimum、
terminal128、有限上界投影、batch32768、UTD1、actorLR与所有旧状态。没有引入未经证明的Q下界。
降低负Q幅度本身不是正确价值估计的证明，均值估计也可能增加过估计。

新 `B/runs/parameter_cycle12_pair_mean_probe_20261026_v2`，三方法各两臂×5000，共30000辅助更新，
0物理、不保存/推广权重。两臂初始完整state直接匹配正式12；相同实际抽样流和RNG，20记录/臂；
父checkpoint/replay不变、预算/有限值/三路完整审查与图通过。原3485636/3485637/3485638全部结束勿重跑。

| 方法 | 终端MAE：min → mean | in-bag MAE：min → mean | absQ p95：min → mean | Q均值：min → mean |
|---|---:|---:|---:|---:|
| I | 1.634716 → 1.795160 | .746939 → .900718 | 67.1511 → 64.4141 | -19.0387 → -14.4787 |
| A | .913353 → .990956 | .395168 → .473410 | 461.1895 → 385.4901 | -227.0487 → -206.8261 |
| V | 1.366905 → 1.392467 | .778813 → .764427 | 281.8863 → 252.1551 | -75.3821 → -60.1933 |

终端拟合并非全面改善；I均值臂Qmax51.185，高于该时刻全局上界48.652，仍有少量预测越界，
投影的是target不是强制所有网络预测满足上界。A/V的uncertainty仍大，不能称CHEQ authority恢复。
因此I保留minimum；仅A/V登记一个有限在线mean周期，检验负偏差和任务行为，不宣称已修复。

入口检查v1暴露foreach恢复的幂等性问题：第二次load检查到已替换的方法而报错，发生于1次辅助更新后，
没有正式影响。原run/runtime/gate.log保留。修正 `published_exact_pipeline_20261026.py`：保存并持续校验原方法，
每次恢复后重新绑定当前参数引用。v2独立pair数学/RNG检查、minimum模式完整一次更新的全部state/metrics/RNG
与原实现逐项相同通过；2次辅助gate更新。总预算为30000+2+失败v1的1次，不能漏记失败检查的更新。
旧已运行的cycle12冻结源码不覆盖。该修正不改变target公式或更新次数。

## 正式参数cycle13：I minimum，A/V mean

`B/runs/parameter_pair_reduction_cycle13_20261026_v1/{method}/train`：

- I3841250，GPU1，CPU13–25，12sampler。
- A3841253，GPU2，CPU26–38，12sampler。
- V3841255，GPU3，CPU39–51，12sampler。

准确父均为 `parameter_exact_pipeline_archive_20261026_v1/{method}/cycle_00012.pt`，SHA见上一交接。
全部旧网络、Adam/moments、replay、RNG、完整history保持。terminal128/上界projection/batch32768/UTD1/
actorLR I/V3e-4、A3e-5不改；I target minimum不变，A/V只改同随机pair的target reduction为mean。
两种actor均仍minimum。执行使用已修复的等价cache/foreach。只一个完整13，无自动14。

新增持久marker `target_pair_reduction={version:1,target:minimum或mean,actor:minimum,sampled_targets:2}`。
后续必须通过 `published_pair_reduction_learner_20261026.py::pair_class` 恢复，不能用只识别投影的旧loader
静默丢失新估计器。旧terminal和projection marker也必须保留。
三check-only：除新增marker外完整state逐项相同，二次恢复相同，正负合同守卫通过。
真实启动三路各1000新transition：原完整prefix/history/optimizer配置/新旧markers、12真实亲和性/MJB、
参数输入/clock/nextstate/reward0误差通过，非A/V内部动力学重新仿真。

归档3882892：view `parameter_pair_reduction_archive_20261026_v1_view`，output `parameter_pair_reduction_archive_20261026_v1`。
只读完整13协调4030423：`parameter_pair_reduction_cycle13_review_20261026_v1`，三路health显式齐全。
health仍保留未投影fixed-minimum-pair TD作为校准诊断，明确不等同A/V新mean训练目标。
网络只读诊断加载agent参数，不声称诊断恢复了完整optimizer；全state恢复另由check-only证明。

## Direct正式时钟迁移：全旧状态保留，候选权重不推广

依据上一轮同正式8的clock有限对照：平均终端误差.985 vs1.171，但p95更差、max约43、Q偏差未消失。
本轮只将被检验过的架构适配用于一个有限在线周期，0示范/纠正/旧CHEQ数据/nominal混合。
固定官方commit1fa2af7496be042e43d36120a7c8d1b71f1bfb59；10critic、随机2target、无entropy backup、8critic:1actor、
batch32768、canonical48 actor/action7保持。公共第一通道=(raw_a0+1)/2，public0为nominal，增加它减慢WBC。

`serl_clock_state_adapter_20261026.py` 使用独立state48和clock叶；actor直接读原48连续缓冲，
critic在原55输入GEMM后的首hidden加clock分支。仅新增online/target/六组Adam moment共8个零叶；
全部旧参数/target/Adam counter与moment/行动RNG/local RNG/官方agent RNG精确保留。
`critic_clock_extension` marker持久化；严格loader拒绝缺失/改变marker，旧state必须显式import_original_state迁移。

历史366962×2时钟复用上一轮五正式journal精确审查的不可变数组；只把current/next clock追加到replay末列，
原48列/actions/rewards/dones/replay RNG/cursor/capacity全保持。当前clock=(1375-j)/1375，next=(1374-j)/1375，
早abort同公式；terminal原48仍用最后有效观测，done清零bootstrap，时间列正常推进。不使用未来奖励标签。
每stream在reset时计数0，act后+1，observation读不推进；1375动作边界、stream隔离、越界拒绝检查通过。

迁移v1在扩展尚未加载正式状态的随机初始模板时完整state一致性检查失败，0更新、未产出prepared权重，日志保留。
v2推迟结构扩展到正式state加载之后，严格原gate不变并通过。官方初始step为Python标量，持久化counter有数组表示；
未将这次模板失败当作正式父状态损坏，也未放松真实正式state一致性要求。

`B/runs/serl_clock_formal_preparation_20261026_v2/prepared/REVIEW.json`：
剥除8零叶与marker完整旧learner digest相同；剥除clock列完整旧replay digest相同；旧history/步骤计数原样。
真实act路径的确定性/固定seed随机动作与原actor精确一致；两次从同prepared state恢复后的完整官方8:1更新逐项相同。
这项gate共16critic+2actor辅助更新，保存前恢复最初迁移state，不导入测试更新后的权重。

原正式8 SHA `f3399b01b550d8c3f4cac6b32f8cd49ca57f53beb68275aebbf3fe4d5a1d5b90`。
prepared `B/runs/serl_clock_formal_preparation_20261026_v2/prepared/prepared_cycle08.pt`，SHA
`752480635ecd70000cfdff97b2a50b824e32b0eb0c0cc8a251e14c5dd08d0e18`。
额外正式check-only从新建learner加载prepared，完整state不变/正负协议守卫通过。

## Direct正式cycle9及已出现的早期失败

PID3712508，GPU0，learnerCPU0、30sampler共享CPU1–12，
`B/runs/serl_clock_cycle09_20261026_v1/direct`；仅一个完整9，无自动10。
source adapter/runtime与prepared、原正式8、迁移/probe review hash均在REGISTRATION和SAMPLER_PATCH收据中。
原物理trainer仅替换learner类与既有共享CPU调度，旧base源码/变换后main/hash单列；不能因base元数据仍写48就忽略新clock_stage。

startup首次脚本错误假设审查时仍有30个live sampler；实际已有6条合法abort结束，因此亲和性数量断言失败。
没有重启训练、原snapshot/源码/日志保留。独立v2按24live+6已结束=30核验，并加入终端reward/clock/占位观测检查。
新增10000transition、80000critic更新通过：prepared完整366962前缀精确、history/官方config不变，
30MJB/实际24live共享亲和性、所有新动作/48观测/当前next时钟/reward重建误差0；其中含6条terminal。

| 失败条件 | 动作数 | reward |
|---|---:|---:|
| passive_corner_train_0100 | 160 | -40.606023 |
| passive_corner_train_0400 | 163 | -40.607220 |
| active_short_train_0671 | 161 | -40.606233 |
| passive_corner_train_0671 | 164 | -40.607577 |
| active_long_train_0337 | 163 | -40.607888 |
| active_short_train_0337 | 162 | -40.607072 |

全部为global penetration>2mm，失败保留；较cycle8更早发生，是明确负面结果，不能称时钟适配有效。
接口/账本检查通过不说明行为安全。尚无完整9结论，原进程继续登记的有限周期。
归档3882888：view `serl_clock_cycle09_archive_20261026_v1_view`，output `serl_clock_cycle09_archive_20261026_v1`。
只读审查4030422：`serl_clock_cycle09_review_20261026_v1`，终端clock与完整旧prepared前缀检查已纳入；
诊断用严格新clock loader并验证完整state一致，不能用原48维loader。

## 纯正式GPU观察与后续

`B/runs/clock9_pair13_gpu_profile_20261026_v1/PROFILE.json`，约63.80秒、60样本，四个正式PID全程存活。
辅助probe/冻结11均已结束，没有用于填占用的额外任务。GPU0–3均值 **49.9333 / 40.6667 / 46.2667 / 40.9333%**，
每卡50%要求仍未满足，不把49.93向上取整冒充达标。
D/I/A/V约23.731/28.998/32.587/30.111 transitions/s；Direct189.850critic updates/s，参数UTD1。
learner约.785/.684/.737/.691核，物理worker约4.478/10.023/9.964/9.964核。
采样/学习流水线仍需优化，不能把辅助窗口代替正式窗口。后续若测试更大batch或更新比，须明确算法统计影响，
从准确完整checkpoint登记、检查健康与吞吐，不能无依据重复旧实验或中途改变当前已登记的单因素阶段。

下一步先收完整13/9，重点检查A/V mean是否缓解负Q而不损害reward/终端拟合，以及Direct早abort是否继续恶化。
不能依据少量terminal拟合改善自动延长；不重置旧状态、不推广辅助权重，不改变物理/SPT/gates。
完整健康收敛、最终冻结比较、完整ESN/SPT与GPU要求仍未完成。
小证据 `docs/evidence/rl_pair13_clock09_20261026/SOURCES.json`；大型checkpoint/物理轨迹仍在B。

收尾读取并快进整合远端main `78c47ae0d2f1f12fd88820ea702aa6149dca29e3` 的非RL第六条件/前54条物理归档更新，保留双方完整记录，不改变其冻结运行。

## 收尾：Direct9已完整审查，时钟适配未修复任务或正Q偏差

原3712508、归档3882888、审查4030422已全部完成，勿重启。当前参数13仍在收尾，尚无Direct10。
Direct9为400935steps / 3167488critic updates，新增33973，Task/Strict0/30，reward均值−33.041089。
24完整55秒，6次160–164动作穿透abort就是上表全部失败；没有排除短失败回合。
所有33973新action/obs/current-nextclock/reward重建0误差、全部30terminal/MJB、完整prepared父prefix/history通过。
严格clock loader恢复完整state精确，诊断learner/Adam/RNG不变；图已目视核对。
300历史terminal×10critic MAE1.713782、p952.236986、max65.252289；Q抽样均值27.636084、max31.106333，
TD MAE.053584、alpha.001395625。相比8的Qmean16.526与terminal max42.604，正偏差和尾部误差恶化。
平均终端MAE略低不能当整体改善，时钟单项适配不是已解决方案。未选择或登记下一算法改动。
准确父归档 `B/runs/serl_clock_cycle09_archive_20261026_v1/direct/cycle_00009.pt`，SHA
`a1a26f285f990ee2308f70a2f178527c2fabfec2b0e6bb1c973e00115981a61d`。
后续必须保留该正式9完整状态及clock marker，不得回退旧8来挑选结果或推广辅助权重。
