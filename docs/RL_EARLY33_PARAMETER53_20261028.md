# Direct33／参数53早期loss与下一轮恢复准备（2026-10-28）

Goal active。此前完整交接仍见[RL_RESUME33_PARAMETER53_20261028.md](RL_RESUME33_PARAMETER53_20261028.md)。本轮核远端main `d620fddfed28a31d1ac7ace90484b0a65b8c2bfd`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read，未发现新的RL环境/gate变化。主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`，B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。

## 已完成的新证据

读取各方法当前轮固定前5000条optimizer，保存原始行和SHA256，全部数值metric有限、steps连续。此为回顾性固定前缀诊断，不冒称预登记稳定性窗口；没有新物理或优化更新。完整原53–55窗口保持。

| 方法 | 前1000 critic loss均值 | 第4001–5000均值 | 前5000最大值 |
|---|---:|---:|---:|
| Direct33 | 0.008725863 | 0.008638095 | 0.014879877 |
| Impedance53 | 2.101265608 | 2.111797362 | 13.629007339 |
| Admittance53 | 1.891315976 | 1.661931608 | 27.263952255 |
| VMC53 | 0.659883418 | 0.714773984 | 9.113719940 |

实际已查看`B/runs/early33_53_loss_20261028_v1/loss.png`。Direct平稳；导纳早期loss回落但仍高于52抬升前约1.34，尖峰保留，不判定收敛或全部健康。完整53尚未结束。

## 导纳52末段标签与loss时序

全30个terminal前后1000更新邻域均保留，没有只选成功或失败邻域。`active_short_train_0600`在51/52两轮使用相同MJB，脚本冻结物理有效性条件均为`abort_reason is None and max_external_penetration_m <= 0.0002`，Strict为Task且physical_valid。

- 51：Task/Strict=true/true，最大外部穿透0.188775607mm，距0.2mm门槛尚余0.011224393mm；回合reward15.690052977。
- 52：Task=true、Strict=false，最大外部穿透0.234536373mm，超过门槛0.034536373mm；最深接触对为`office_v5_ball_geom`与`fr3_link6_collision`。回合reward−34.966087179，差值−50.656140156。
- 52在step2179929写终端，terminal成功项−25（51为+25），完整终端reward−28.504752630。该terminal前1000 loss均值1.292099337，其后1000为1.912621715；完整52峰值37.244197845在step2181072。

已逐算核验记录的穿透→physical_valid→Strict标签与完整回合奖励和，绑定rollout/TERMINAL/执行脚本hash。**这是已保存记录与原gate的核验，不是独立重算全部物理接触；邻域重叠且未记录实际抽样replay索引，不能证明该terminal导致loss尖峰。** 不改0.2mm门槛、reward、物理或学习率。

## 下一完整轮次的恢复准备

`B/runtime/prepare34_parameter54_20261028_v1`已保存完整源码/diff/hash/登记；仅准备，不启动训练。原Direct33/参数53及归档review继续，GPU合成守护v2保持运行。

- Direct34 preparation waiter PID1059038；参数54 waiter PID1059039，原进程起始ticks已核验。
- 固定14400秒；绑定原learner与archive monitor身份，要求当前完整archive/review/health成功且原learner退出后才调用check-only。
- 两个prepare脚本唯一启动的子命令均含`--check-only`，静态AST检查通过；只生成PREPARATION_REVIEW，不生成PRELAUNCH批准收据。当前实际34/54 check-only尚未执行，不宣称恢复已通过。
- 后续读`direct_FINISHED.json`/`parameter_FINISHED.json`与FAILURE，查看父完整loss/health后再决定有限续训。没有自动34/54正式launch。

## 保存

小证据`docs/evidence/RL_EARLY33_PARAMETER53_20261028`；完整前5000原始行、图、脚本与准备登记均在共享SSD归档：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_EARLY33_PARAMETER53_20261028_035157/SMALL_EVIDENCE.tar.gz`。19成员逐大小/hash核验，1304817字节，SHA256 `940fb8ea4e7d1886b62bc219270cb24847e581011090041ffa39b606927e1277`。原大checkpoint/replay/raw仍共享SSD，不是HDD/arm1完整备份。
