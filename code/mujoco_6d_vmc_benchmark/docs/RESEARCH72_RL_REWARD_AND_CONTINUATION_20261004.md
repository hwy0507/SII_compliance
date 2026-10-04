# 实际RL完整续训及奖励缓存核验

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
