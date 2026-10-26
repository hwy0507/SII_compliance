# Fresh阶段完整周期结果与剩余资源交接

四路12worker资源交接和首轮统一科学复核已完成，后续正式训练继续。
Direct第二轮仍未出现任务成功；Impedance首轮出现主动条件成功，但被动条件全部失败，
且存在安全失败。当前继续原登记六周期阶段，**尚无充分训练或健康收敛结论**。
两方法此处周期不同，不能用这张训练表作统一预算排名或ESN比较。

| 方法及完整周期 | 累计真实步数 | 累计更新 | Task/Strict，各30 | 完整55秒 |
|---|---:|---:|---:|---:|
| Direct cycle1（第二轮） | 82500 | 77501 | 0/0 | 30 |
| Impedance cycle0（首轮） | 40734 | 35735 | 17/16 | 29 |

Direct首轮/第二轮平均reward分别−32.96638/−33.20797，未见改善，仍按原阶段收集后续证据。
Impedance首轮平均reward−4.32957、标准差26.07573，不能称reward已稳定。
按类别，Impedance被动0/0、主动短期10/9、主动长期7/7（每类10，Task/Strict），
失败和安全违规都留在分母。训练中policy持续变化，不能把这些回合视作固定checkpoint评估。

## 两类安全失败分别保留

- `active_short_train_0600`：Task真、Strict假；球与机器人手部外穿透峰值 **0.2253137mm**，
  超过原 **0.2mm** 门槛。1375个保存的actor区间（代表110万子步）的最大外穿透复算与
  rollout统计精确一致；终端reward项为−25，completion_efficiency为0，没有误发成功奖励。
- `active_long_train_0000`：859actions、**34.36秒**触发原
  `global_penetration_exceeded_2mm` 中止，Task/Strict均假。保存stats中全局穿透峰值
  **87.21165mm**，最坏对为场景凸边与任务物块；外部机器人接触穿透仅0.078858mm。
  全局中止门和外部接触Strict门是不同检查，不能用较低外穿透掩盖全局中止。
  原evaluator在控制循环检查全局峰值；本次不改冻结physics、接触定义或检查频率。

两项都属于真实训练失败，不能以已有阶段进入retreat或低速度/力矩替代最终gate。
本次只核验保存的统计、区间峰值、终端和模型，不声称重新完成原子步安全重放。

## 完整周期核验与继续训练

两组各30个条件集合、终端结果/时长、实际MJB hash及checkpoint replay长度均核验。
Direct完整cycle1 checkpoint SHA256：
`595b10828a0bf8e068d9419bd6612aaf96cf731c24cbcfbe766f33ac33081ca5`。
Impedance完整cycle0 checkpoint SHA256：
`f8f6c209efe360fece16e3ff89f009885f187041b373f293e46f75b5fbe04ce6`。
两路原learner已自动继续下一周期，没有重启或改变学习配置。
原四路完整cycle0/1/3/5只读科学诊断仍由2472115执行，当前等待其他方法的完整首轮。

额外只读观察PID **196372**（工具session4132）等待VMC1146204和Admittance1314547
结束原首轮，再核验原协调2471936自动启动的12worker接续。
它不派发训练、不改STOP或原协议；30分钟deadline只限制这个观察，不停止训练。
原进程仍live时不重启；观察超时也不等同于训练终止。

产物目录：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/remaining_fresh_resource_resume_review_v1/`。
包含 `direct_CYCLE_01_REVIEW.json`、`impedance_CYCLE_00_REVIEW.json`、
`IMPEDANCE_STRICT_FAILURE_DETAIL.json`、只读 `observe.py`、EXECUTION及进度收据。
配套仓库JSON引用不可变核验收据和hash，原始checkpoint/运行日志保留集群。

本轮只读复核0新增physics/optimizer updates，原正式训练持续；未修改冻结runtime、
reward/gamma/batch/UTD、physics/MJB、actor信息、公共filter、gate、执行器限制或dt。
GPU50%仍未达到；本轮后续完成的四路扩容GPU测量见下文。
充分训练、固定策略训练集矩阵、最终SPT/接触舒适审计和指定ESN比较仍未完成，Goal active。

## 四路交接完成与统一首轮诊断（同轮后续）

只读观察196372已完成并退出，session4132结束，勿重复启动。
原VMC1146204、Admittance1314547均按完整cycle0正常结束，不应重启。
新VMC **511376**、Admittance **793968** 由原协调自动从各自41250步/36251updates
父checkpoint接续，保留剩余五周期。两路各42250步/37251updates快照已核验：
全部父replay字段及cycle历史精确保留、三个Adam计数连续增长、actor实际改变、
网络/日志有限、更新步数连续；各12个新MJB/fixture/参考plan/dt与48/7/7输入动作核验。
父hash分别 `62d054bafbd296898f7e2f3e3456b384f9486a9329d193c88fa6f18bf3595977` 和
`09b8415f6709615ed45c126c1212c0fd18ec5f55d596bc0b901fae219a1c6843`。
继续使用全state恢复，worker数改变意味着后续采样交织不同，不称未来逐位等价。

新run DISPATCH_FINISHED记录四路已真实更新；这只是资源派发完成，六周期训练仍在运行。
四active PID：D4055508/I3849956/A793968/V511376；每路12sampler，learner+sampler总52核。
原协调2471936、归档2472286和科学审计2472115继续，后者已完成fresh_cycle_00，正在等cycle1。

原审计四路**同一首轮cycle0**的120条件全部核对，复用各自已核验的30终端/MJB收据并核对
checkpoint与实际archive字节hash；reward分量重建/网络不变通过，统一六面板图已目视核对。
119个完整55秒、Impedance一个提前中止，均留分母。

| 首轮方法 | Task/Strict，各30 | 平均回合reward | 末1000 critic loss | 终端Q MAE | in-bag / out-of-bag MAE |
|---|---:|---:|---:|---:|---:|
| Direct | 0/0 | −32.96638 | 9.33414 | 36.20118 | 22.67739 / 92.62802 |
| Impedance | 17/16 | −4.32957 | 8.00295 | 36.64625 | 32.38365 / 55.21902 |
| Admittance | 12/11 | −13.78916 | 11.39242 | 51.13115 | 40.09770 / 95.26498 |
| VMC | 17/16 | −4.57905 | 7.33765 | 52.50248 | 38.08781 / 90.82440 |

四路被动条件均0/10。Admittance短期Task9/Strict8、长期3/3；VMC短期10/9、长期7/7。
VMC和Admittance的Task真/Strict假同为短期0600，保存interval外穿透峰值分别
0.2165552/0.2057225mm，均超过原0.2mm；逐interval复算通过，门槛未放宽。
三参数接口尚未证明学得对被动条件的恢复，也未证明优于固定名义参数。
终端MAE受样本年龄、ensemble mask和隐藏时钟混叠影响；Direct精确抽样研究见
PUBLISHED_FRESH_DIRECT_FIRST_CYCLE_20261026，不能外推其数值到其他方法。

四路均扩容后，新60秒/60样本正式GPU均值为 **6.07/6.80/5.83/5.98%**，最小均0。
无辅助GPU训练；这是已扩容运行中的窗口，包含正常周期阶段差异，不是GPU50%达标。
采样扩容未解决利用不足，需要继续定位当前batch256/UTD1配置的实际吞吐瓶颈；
不为占用率把高重复更新设置重新引入当前live阶段。

新增证据在同产物目录：`vmc_REVIEW.json`、`admittance_REVIEW.json`、`FINISHED.json`、
`FIRST_CYCLE_MATRIX_REVIEW.json`、两个参数Strict失败详情和GPU_60S_ALL_FOUR_12_WORKERS.json。
统一诊断位于 `runs/fresh_ready_methods_audit_v2/fresh_cycle_00/results/`，配套JSON记录hash。
本轮没有改训练源码或配置。下一步继续原阶段、审查后续完整周期与固定策略结果，
不能把首轮完成、资源交接完成或有限loss当成充分收敛。
