# 实际RL完整续训及奖励缓存核验

## 11:00UTC补充：VMC参数与直接task两个seed303训练段

两段分别于10:13:09和10:16:28UTC自然完成。复用371264a原三工具，未改运行中训练或追加物理。
VMC303父5500、实际累计27500步/45002更新；直接task303父5168、累计27159步/44320更新。
父缓存前缀精确保留，新增观测/原始action/终止/非末帧下一观测与真实轨迹一致。

| 训练段 | 新回合 | 新转移 | 子步 | 核验奖励 | 未核验首项 | 短失败 |
|---|---:|---:|---:|---:|---:|---:|
| VMC参数303 | 16 | 22000 | 17600000 | 21984 | 16 | 0 |
| 直接task303 | 16 | 21991 | 17592800 | 21975 | 16 | 1 |

共1759.64模拟秒；原始区间重算误差积分最大差4.16e-17、有界积分6.25e-17，
时长/实际力矩/最大位置误差/过滤action差0。原rtol1e-12、atol1e-13未改变。
直接task303的train009于54.64秒因`global_penetration_exceeded_2mm`终止，未当完整55秒；
两组各16条task/strict均false。这是在线更新策略的训练过程，不能作为最终冻结策略成功率或ESN优势证据。
32首奖励仍因初始potential缺失排除；potential/终止下一观测/逐梯度一致性和收敛未因此得到验证。

Spark原venv_gpu，单线程1GiB/Swap0/CPUQuota100%，服务`sii-r72-continuation-audit-v4`
20.644秒正常退出；物理区间审计11:00:34–11:00:52UTC。0新仿真/actor/梯度/最终条件读取。
服务器arm1@192.168.31.70，目录
`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_completed_continuation_audit_v4/`。
四文件327499字节，与Git证据前缀`RL_CONTINUATION_V4_`逐SHA同字节：

| 文件 | SHA256 |
|---|---|
| `parameter_vmc_2026100303_PREFIX.json` | `e90397bbf184e1d1b5d2d7b37b26bca129a8778ef21e0044f25334447df8eb89` |
| `direct_office_task_2026100303_PREFIX.json` | `48ac689f5499e3071c56c2dfc2e6f4bbdc844a4aef69a1af522f8a6a2f67f4e2` |
| `REWARDS.json` | `1a6f02bf6526fd7be174add2dc28ca9d4106795ad932ec5f67ed98576f1d7674` |
| `INTERVALS.json` | `a643720ed7f01a060bc29682a6732647a323ee9bd2cbb5a627b5bcd3a14ff9f1` |

累计四批审计240回合/276948区间/221558400子步，276708可核验奖励、240首项未核验。
原队列继续；全部15模型共同边界、最终912、独立最终actor和论文结论仍未完成。

## 10:00UTC补充：direct office-task 301 新完成训练段

原队列于09:17:16UTC自然完成该27500上限阶段，实际26746步/43494更新。
未重跑既有审计，复用371264a冻结三工具检查5500父缓存前缀、新增21246转移及16真实回合。
16996800物理子步对应849.84秒；21230个可核验奖励逐值一致，16个未知首奖励仍排除。
误差积分最大差4.16e-17、有界积分3.47e-17；时长/力矩/最大位置误差/过滤action差0。
15条完整55秒，最后train004于24.84秒以`global_penetration_exceeded_2mm`终止；16条task/strict均false。
这是在线更新中的训练回合，不能作为最终冻结策略的0/16测试结果或ESN优势证据。
初始potential、终止下一观测和逐梯度一致性仍未独立核验，完整15模型最终边界尚未完成。

Spark原venv_gpu，单线程、MemoryMax1GiB/Swap0/CPUQuota100%；服务
`sii-r72-continuation-audit-v3`正常退出，10.631秒，0新物理/actor/梯度。
物理区间核验实际10:00:22–10:00:31UTC；未修改训练、场景或最终条件封存。
服务器arm1@192.168.31.70，目录
`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_completed_continuation_audit_v3/`。
三文件共163793字节，Git证据前缀`RL_CONTINUATION_V3_`，传输后逐SHA核验同字节：

| 文件 | SHA256 |
|---|---|
| `PREFIX.json` | `a68fc69ed6fa98303b1f1d19a913013b2d82878820bea18ca10176f90b7c5332` |
| `REWARDS.json` | `f2f52adcb4597f4a7d2e08d4d11104cbbbc6eca8bdd51706c43f28d90d8809cd` |
| `INTERVALS.json` | `992aadb4716a390f48bfcb07d2095f085339920605123ad77d7eb7d38d522ffa` |

合并原两批审计共208回合、232957区间、186365600子步；232749奖励已核验，208首项未核验。
这仍是训练链审计范围，不是最终统一测试的分母。

## 09:14UTC补充：六个新完成续训段，包含38个短失败

复用已核验源码371264a的原审计工具，核查上次未覆盖的六个自然完成27500阶段。
没有重算已有六段、重启训练、追加物理或选择权重；原开发/训练及最终连续监督均保持运行。
实际物理区间审计时间09:13:28–09:14:27UTC，整个串行审计服务耗时67.019秒。
计算主机Spark，使用原venv_gpu解释器；原始大轨迹已在该机，采用单线程、CPUQuota100%、
MemoryMax1GiB/Swap0完成只读核验，避免为此复制百余回合原始物理数据。

| 家族 / seed尾号 | 新回合 | 短失败 | 新转移 | 奖励核验 | 未核验首项 |
|---|---:|---:|---:|---:|---:|
| RL阻抗 / 302 | 16 | 0 | 22000 | 21984 | 16 |
| direct office-task / 302 | 39 | 26 | 20909 | 20870 | 39 |
| RL阻抗 / 301 | 16 | 0 | 22000 | 21984 | 16 |
| RL导纳 / 302 | 16 | 0 | 22000 | 21984 | 16 |
| direct metric / 302 | 27 | 12 | 20798 | 20771 | 27 |
| RL阻抗 / 303 | 16 | 0 | 22000 | 21984 | 16 |
| 合计 | 130 | 38 | 129707 | 129577 | 130 |

各段原5500条父回放前缀逐值保留；新增转移观测/原始策略动作/终止和非末帧下一观测关联全部真实回合，
继承步数、更新计数、checkpoint/源码/训练协议hash核验通过。direct task302实际累计26409步、
direct metric302累计26298步，其余27500步；不将阶段上限当作实际收集数。

103,765,600个物理子步独立分区到129,707个actor区间，共5188.28秒；
时长、力矩/归一化峰值、最大位置误差、执行过滤action的最大差值为0，误差积分及有界积分最大差均
5.55e-17，原比较容差rtol1e-12/atol1e-13未改变。129,577个可核验奖励与冻结公式及float32缓存精确相等。
原日志没有初始potential，每回合首奖励继续明确排除；没有反推它以使结果通过。

38个短回合的原终止原因均为 `global_penetration_exceeded_2mm`。
task302短回合0.36–51.88秒，metric302为0.40–1.68秒；均保留在数据/步数和原训练记录中。
这是正在更新策略的训练过程，不是冻结策略最终成功率；不能以这些短失败宣布直接RL失败或ESN胜出。
审计说明记录链一致，**不证明训练收敛、奖励设计充分、终止下一观测/potential正确、逐梯度一致或接触模型准确**。
原物理gate保持不变，未按这些失败修改场景或RL预算。

服务器 `arm1@192.168.31.70`，共同根 `/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
结果在 `rl_completed_continuation_audit_v2/`，八文件共1,203,070字节；清单后再次逐内容/大小/完整集合核验通过。
六份 `*_PREFIX.json` 原件在服务器；Git保留下面两审计和清单原字节。

| 文件 | SHA256 |
|---|---|
| `INTERVALS.json` | `0e7fb187eab2dcfb124eb2d126cc41f3300362529b7cb0bc3372a1130d05ac2d` |
| `REWARDS.json` | `df3a1aabdeba954c21052c84c97d68a453faf9266e6ea17da0fc0257cb02ef33` |
| `archive_manifest.json` | `0b16e4a2f7a25de575b7b701113d60b206a00de001e661adc424d1aa3db550c3` |

工具原件：`/home/arm1/sii_shared/SII_compliance/source/371264a8131effa0d593ad585c4ecc60f83ee7f6/code/mujoco_6d_vmc_benchmark/tools/`，
`research72_rl_replay_prefix_20261004.py`逐段执行，`research72_reward_replay_audit_20261004.py`与
`research72_reward_intervals_20261004.py`接收同六个manifest。每份JSON记录实际argv、源hash和输入hash。
源码371264a共3303文件已逐内容/大小/模式/集合核验，tar SHA9cc0dd6f38c4034e453c443251654a472c1e64229a4f40f45fcbe362767423d6。

## 05:51UTC补充：从原始物理子步重算奖励输入

新工具`research72_reward_intervals_20261004.py`补上早先缓存核验的物理输入缺口。
覆盖下表五家族代表段，以及新完成direct_metric301续训段；六段所有62回合都纳入，
包含4个短失败，共82,004个控制区间、65,603,200个原始物理子步、3,280.16s模拟时间。
这些是训练策略不断更新时的记录，不是冻结策略的最终测试结果。

区间由实际actor起止时间与物理时间戳独立划分，不能依赖被检查的区间元数据自行决定边界。
从原始`dt/error/qfrc_actuator`重算时长、误差平方积分、有界误差积分、每关节/归一化峰力矩和最大位置误差；
从归档MJB读取七关节限幅87/87/87/87/12/12/12 Nm。
另核对公共执行链中scale/yield与归一化过滤action7，逐项比较奖励区间保存的实际执行量。
模型、执行、原始轨迹/物理指标/动作链、协议hash及完整/短回合时长均关联原件；不读取最终条件。

- 时长、归一化/逐关节峰力矩、最大误差、过滤动作差值均为0。
- 误差积分最大绝对差`6.94e-17`，有界误差积分`8.33e-17`，来自不同归约顺序；
  固定比较容差rtol`1e-12`、atol`1e-13`，不是修改任何研究gate。
- 完整回合和短尾区间、时间缺口、遗漏终止采样、篡改积分/动作、伪造区间样本数共6项合成回归通过。
  实际Spark单线程/MemoryMax1GiB/CPUQuota100%运行33.16s；新物理、actor、梯度均0。
- **任务potential及初始potential未独立重算，原始物理日志不等于真实接触模型验证。**
  该检查不是重新仿真或完整actor/servo重放；首奖励依然不能宣称全量核验。

直接metric301自然续训至27,336步/22累计回合/44,674更新：5500父前缀逐值不变，
新增21,836转移对应真实18回合。3个短失败分别train009/015/020的39.76/1.04/7.64s，
全部因`global_penetration_exceeded_2mm`终止，仍保留在训练数据、步数与失败记录中。
原task303/train031的41.72s短失败同样纳入物理核算。27,500是阶段上限，不能把实际步数补写为上限。
新段21,818个可核验奖励与冻结公式/缓存精确一致，18个首奖励排除；连同原五段，
累计81,942个奖励已核验、62个首奖励未核验，对应全部82,004个物理区间。
不证明逐梯度优化器一致、收敛、终止下一观测准确或最终任务成功。

服务器`arm1@192.168.31.70`，共同根`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
新两源`reward_intervals_source_v1/`已逐内容/大小/权限核验，tar SHA
`fc4fdbb7145ba401f15a7aa479c3641160904d48b289c5d57b503e0190039f37`。
回放前缀/奖励工具来自已完整核验的
`/home/arm1/sii_shared/SII_compliance/source/19a11c21f6aef4be2801a1e3c192146182a23bad/code/mujoco_6d_vmc_benchmark/tools/`。
结果`reward_intervals_audit_v1/`三文件276,836字节，清单生成后独立逐hash/大小复查通过：

| 结果文件 | SHA256 |
|---|---|
| `INTERVALS.json` | `4772c4f33675529ca1e847ccdc25d27ea2cb06fb6aa83f57d590bef056a09ec7` |
| `DIRECT_METRIC_PREFIX.json` | `982b0b20df34f948fae6b411651ed19a403c3f740492a50919ef9b9182fd81a7` |
| `DIRECT_METRIC_REWARD.json` | `4930b8a690825eb9025e794e7e07424f61a330008fece36e1a4cada221a03211` |
| `archive_manifest.json` | `ddf8c0bea89c62cf4455e01966687002ad7493b178aba07beebe26307477a140` |

物理区间、奖励、清单Git副本同字节；较长前缀原件在服务器按清单查阅。
这六段是五家族代表证据，不是全部15个最终模型；原训练/开发继续，未冻结或开封最终24条件。

## 05:19UTC原始缓存检查

2026-10-04 05:19UTC。以下是训练工程与数据一致性证据，不是最终冻结策略任务成功率。
全部检查不加载learner/actor、不计算梯度、不执行新物理、不读取最终条件；原训练作业保持运行。

## 已自然完成的续训

导纳301与VMC301均已完成`cumulative_0027500`阶段，各累计27,500步/20回合/45,002更新。
相对于父5,500步/4回合/1,002更新，新收集22,000步/16回合，计数与原UTD2及继承关系一致。
独立存档检查通过：完整checkpoint文件hash、协议与原44源文件、prior、RNG可加载、回合边界、
回放容量/维度/终止标记和真实轨迹引用一致。另独立比较所有5,500条父前缀逐值一致，
新增22,000条观测/原始动作/非末帧下一观测/终止逐值关联真实16回合。
原中途16,500步审计保留；本次闭合的是这两个完整27,500阶段，不声称全部15模型已训练完。
未逐梯度重新计算优化器，也未独立核验terminal next observation；最终49,500边界与最终actor审计仍待完成。

## 冻结奖励公式到回放缓存

新只读工具`research72_reward_replay_audit_20261004.py`按每个真实训练协议中记录的SHA加载原冻结rewards.py，
用保存的`RL_INTERVALS.json`、实际公共过滤后action7、原终止task/strict重新计算奖励，与checkpoint回放float32逐值比较。
阻抗原始策略是5D，但其实际公共过滤动作7D仍按原训练实现计算奖励，不改变动作语义。

**日志没有保存每回合初始potential，因此每回合第一个奖励明确排除。**
初始potential仅影响首个progress项，不改变已核对冻结rewarder中的峰值、累计时间和前一步动作状态；
重放仍执行首区间以正确初始化这些状态，但不把首奖励当已核验值，也不反推它来通过验证。
后续每个区间及终止项均比较；四项合成回归覆盖首项排除且状态继续、成功/失败终止、后续奖励篡改、缺区间拒绝。

| 真实模型/训练段 | 原始策略维度 | 奖励模式 | 新转移 | 奖励核验 | 排除首项 |
|---|---:|---|---:|---:|---:|
| 导纳301，续训到27500 | 7 | metric | 22000 | 21984 | 16 |
| VMC301，续训到27500 | 7 | metric | 22000 | 21984 | 16 |
| 阻抗301，首段 | 5 | metric | 5500 | 5496 | 4 |
| 直接metric301，首段 | 7 | metric | 5500 | 5496 | 4 |
| 直接office_task303，首段 | 7 | office_task | 5168 | 5164 | 4 |
| 合计 | — | — | 60168 | 60124 | 44 |

60,124条可核验奖励逐值一致；44条未知首奖励保留为未核验，不称全奖励覆盖。
office_task303的train031原短失败41.72s也保留，其task惩罚−20，剩余负成本补偿−0.2224180869，终止potential置0，与缓存一致。
这覆盖五RL家族的代表段，不是全部15模型。奖励区间的误差/力矩统计在此作为保存输入使用，
**本审计没有独立从物理子步重算这些区间**，也不证明奖励设计最优、已收敛或柔顺任务成功。
报告中的checked return/term sums排除了首奖励，不能当完整回合收益。

## 归档与当前进度

服务器`arm1@192.168.31.70`，本轮根`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
只读工具与测试两文件在`reward_replay_source_v1/`完整内容/大小/模式核验，
tar SHA `4d304639183d6c490899961a8393ca4e264bd738a0d77ec137ec9c5ae6a6625e`。
checkpoint哈希、存档和前缀审计工具使用精确Git源码
`/home/arm1/sii_shared/SII_compliance/source/2000768fbd0b4dd2edef709854e6b444b98335a0/code/mujoco_6d_vmc_benchmark/tools/`。
Spark单线程/CPUQuota100%/MemoryMax1GiB/Swap0，未更改训练runtime、奖励、条件或预算。

结果目录`rl_completed_continuation_audit_v1/`五文件共315,828字节，生成清单后再次独立核验全部内容/大小。
清单SHA `33014cf06562a26ac02b4528e9ab6ac45bae1b857b386e70a70f79d78aa3c397`，Git同字节。

| 原件 | SHA256 |
|---|---|
| `SAVED_STATE.json` | `684abfebffec268da40f6bfd71c92edc468de15d6f372ffbccfd8ce5c74fea4a` |
| `ADMITTANCE301.json` | `e13c3e4c22f58bd05c41eb78c2fe196afe5673a6884737a19e6630cc04c25155` |
| `VMC301.json` | `c30cf9975c91a9dc8eccf17ab05956c6c75530b5e2a347946e0602f62f6cd6d4` |
| `REWARD_REPLAY.json` | `3f9be038acba95ba52c3482d038c246d9be583d78452d9868d58d27f4650c60b` |
| `REWARD_REPLAY_BASELINE_TYPES.json` | `2734f2ed1648a560dcbf79f2f7c2fe1dbd00c3c3bb9e87bba9444ee064e0d3be` |

Git保留存档、两份奖励核验和完整清单；较长前缀原件由清单引用共享服务器。
05:19成本快照：120拟合完成，RL140,438真实交互/154,400更新；旧context25/168、增强网络17/168、新refit2/144。
三RL服务PID2428446/47/48和评估队列均经/proc核验存活；三服务memory.events的oom/oom_kill均0，达到内存上限的计数不冒充OOM。
剩余开发理想23.488–24.595h、最终912物理22.824–23.942h，2h报告后余量3.632–5.857h，仍非完成保证。
`BUDGET_FORECAST_20261004_0520.json` SHA `7c4709023889cf34387cd711025f2137bc6d492ce65167fe22025b8a123ad795`，Git原字节；
输入快照SHA `eca5424abf87938bd946c0acf04240b5419e55bd636f5e5eedb9516594fa7561`，实际时间以JSON为准。
本轮未增加训练或物理工作，24最终保持封存；完整开发、全部RL共同边界、最终冻结/912评估与可投稿结论仍未完成。
