# v8第四条件完整九模型审计

原回归条件`new30_prospective_20261026_acceptance_003`九模型已经全部完成；
**Task/Strict均未通过，当前主矩阵尚未修复。** 这是单条件结果，不是完整108汇总或新模型选择依据。
原评测已正常接续第五条件，没有重启、改模型或放宽门槛。

## 完整结果与失败

原保存子步共8,887,200个，全部指标算术、source/config/checkpoint/MJB hash以及
原actor/filter精确重放收据已核验。ESN seed1在4.36秒lift阶段触发
`global_penetration_exceeded_2mm`，其余八回合完整55秒。没有BOTH成功回合，条件SPT为NA，
不填0或凭低误差计算完成速度。完整矩阵T_ref继续等待原自动后处理。

| 方法 | seed末位 | 最后失败阶段 | 峰值力矩 Nm | 外部/桌边最大穿透 mm | 接触期间舒适代理 | 机器合规 |
|---|---:|---|---:|---:|---:|---|
| ESN | 1 | lift，4.36s abort | 75.556 | 2.993203 | NA | 失败 |
| RNN | 1 | approach | 42.592 | 0.095701 | 100% | 通过 |
| MLP | 1 | approach | 36.665 | 0.036295 | NA | 通过 |
| ESN | 2 | lift | 54.738 | 0.164629 | 95.612% | 通过 |
| RNN | 2 | carry | 38.780 | 0.162702 | 100% | 通过 |
| MLP | 2 | carry | 52.014 | 0.621955 | 100% | 失败 |
| ESN | 3 | lift | 52.911 | 0.223435 | 0% | 失败 |
| RNN | 3 | carry | 38.632 | 0.155740 | 100% | 通过 |
| MLP | 3 | carry | 49.484 | 0.615215 | 100% | 失败 |

ESN1/MLP1没有人体接触，舒适代理NA；ESN3接触时长4.55895秒，原阈值下力矩合规比例确为0。
RNN1虽然该代理为100%，人体接触仅0.02975秒，且任务未完成；不能写作已验证的人机安全。
其他100%亦仅表示原工程代理通过，不抵消穿透或任务失败。机器合规按原0.2mm等定义，
不将五条机器合规通过误称为Task或Strict成功。

三ESN在本条件仍分别停于抬升或提前终止；RNN/MLP的seed1停于接近、其余停于搬运。
这与此前已观察的覆盖/闭环问题一致，但本次没有新增因果消融，不据此改变选模或训练标签。
下一步仍依照[方向覆盖诊断](NONRL_V8_TRAIN_DIRECTION_COVERAGE_20261029.md)和
[当前接续](NONRL_V8_CONDITION001_AND_HANDOFF_FIX_20261029.md)：完整108审查归档后，
运行有效八球v4，再据实际结果修三真实场景共同数据并公平重训。此处不宣称修复成功。

## 执行及证据

- 审计服务`sii-v8-condition003-audit-20261029.service`，本机只读，配置CPU50%、数值线程1、
  MemoryMax3GiB、swap0；日志确认01:52:49–01:52:55UTC完成，CPU5.049秒。
- [准确审计](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION003_AUDIT.json)，
  SHA256 `aa1ead018cbbc25384a6804a51bb291a5cd32b007a01dc6cd2dee1231ba6e4d2`。
  审计是保存数据复算、hash与原重放收据核验，不是独立动力学再积分。
- [原边界观察](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION003_BOUNDARY_WAIT.json)：
  01:39:19.273–01:51:49.304UTC共26次，34→36/108；原1172675/start32623702和后处理
  1201537/start32942337均loaded/active，最高772517888bytes，OOM/oom_kill/swap0。
  本轮读取正确rollout.progress.json，物理时间真实推进。观察71124在第四条件完整后自然exit0，
  原科学服务继续，无重启。
- 开工实际fetch/read main `f7fde7a3ffa09b9241a2facfcdcfe5c96ec29e63`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。上一轮verified wait，本轮完成整组审计属progress。

新审计与观察暂本机，核验共享后补路径。Goal active；无RL、子agent、服务器计算或删除。
