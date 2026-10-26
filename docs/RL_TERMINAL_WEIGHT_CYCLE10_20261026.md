# 2026-10-26 终端拟合诊断、参数cycle10与Direct5

Goal仍active。上一轮是实质进展：Direct5/6已启动，I/A9及批量对照完成。本轮进一步完成
VMC9/Direct5审查、两组有限诊断，并已恢复三路参数在线训练。终端拟合改善不等于健康收敛；
四卡正式训练持续≥50%仍未达成。物理/MJB/gates/filter/执行器/dt5e-5/30条件/SPT reward保持。

开工fetch/read main=`236c24f17376aeadf221d03474ae6290cad5e1d3`、
baseline=`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未干预另一主机非RL任务。无子agent。
执行根B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。

## 两个新完整周期

| 方法 | 周期 | 累计steps / critic更新 | Task / Strict，各30 | reward均值 | 终端Q MAE |
|---|---:|---:|---:|---:|---:|
| VMC原pair恢复阶段 | 9 | 409500 / 404501 | 17 / 17 | −2.817421 | 96.200716 |
| 官方SERL Direct | 5 | 244843 / 1918752 | 0 / 0 | −33.469013 | 1.719118 |

V9全30完整55秒、无abort，新增41250；原1497979/归档1497983/只读2062386均结束，勿重启。
父cycle8 replay前缀/原stage父hash、全部新增reward重建0误差、30terminal/MJB与有限网络/
optimizer检查通过。末1000 Q loss1318.913，Q均值539.725、p95=2919.910、最大3292.544；
term MAE从8的51.755升到96.201，不能因reward近似稳定而称健康。pair恢复未修复价值漂移。
SHA=`7e29e027c16215ca9532f0a0bbfa9bfd023586ab6ef5ede4abe60ce822057aa7`。

D5新增40881；29完整55秒，`passive_corner_train_0300` 第1006动作global穿透>2mm提前终止，
approach失败保留在30分母。全新增动作映射/观测/nextstate/reward重建、父203962前缀、30terminal/
MJB通过；这不是原始子步重模拟。180终端×10critic误差p95=3.179、max34.925；抽样Q均值7.011、
TD MAE0.02570、alpha0.0005281。完整网络/optimizer/RNG诊断不变，0更新，图已目视检查。
SHA=`215a0e8274db415e019cac435fc7aea5a78849b6dd7fb2fc1ce8778be956c184`。
原2818100进入登记cycle6，不重复派发；5只读2946490已完成，6只读2946491仍等准确边界。
Direct仍固定官方SERL来源、零示范、无人工纠正/旧CHEQ权重或replay，无nominal mixing。

## 固定学习目标对照：抑制漂移但未修复已有误差

`B/runs/parameter_cycle09_target_drift_probe_20261026_v1`，I/A各两个新臂：仅冻结target更新，
或同时冻结target、actor及温度optimizer step；每臂5000，共20000新辅助critic更新。
完整初始网络/Adam/replay/RNG保留，匹配batch32768、相同实际replay抽样流；复用上轮已完成
I/A各5000的原设置对照，没有重复运行对照。0物理、不存/推广权重。两原PID3269634/3269635均已结束。

| 方法/设置 | 终端MAE | 非终端absQ p95 |
|---|---:|---:|
| I原设置，复用 | 13.088 | 463.294 |
| I固定target | 13.973 | 403.547 |
| I固定target+actor+温度 | 14.326 | 403.322 |
| A原设置，复用 | 7.605 | 160.353 |
| A固定target | 7.282 | 148.566 |
| A固定target+actor+温度 | 7.549 | 148.738 |

独立核对每臂20个记录点、预算、原checkpoint不变，指定冻结组件与Adam状态digest确实不变；
全部新臂的初始full-state digest还直接与正式父state比较一致（PARENT_STATE_AUDIT.json），
不只与另一个实验的初始值比较。图已检查。冻结target阻止Q尾部增长符合预期，但它也固定了
已经有偏的目标；不能把“固定后不再长大”视为价值校准修复，未将该冻结策略用于正式在线训练。

## 终端critic损失权重对照

cycle9终端占replay约0.072%，而critic的长时域Q已严重漂移。新登记
`B/runs/parameter_cycle09_terminal_weight_probe_20261026_v1` 只改变critic回归权重：
终端128、其他1，每个critic按其bootstrap mask及实际总权重归一化。等价公式：

`sum(mask * (1 + 127*done) * squared_TD) / sum(mask * (1 + 127*done))`

该选择把约0.072%终端的总体拟合份额提高到约8.4%，是明确的算法适配；不是等价性能优化，
也不是原作者CHEQ原样。reward、target pair、actor目标、采样序列、batch/UTD、优化器和环境不改。
I/A各一个5000更新的新加权臂，复用原设置对照；VMC准确cycle9首次做原设置/加权各5000。
总20000新辅助更新，外加入口验证2次更新；0物理，不保存或推广任何辅助权重。
三PID3511593/3511594/3511595全部完成，勿重复派发。

| 方法 | 原设置终端MAE → 加权 | 原设置in-bag终端MAE → 加权 | 原设置absQ p95 → 加权 |
|---|---:|---:|---:|
| I | 13.088 → 7.540 | 9.017 → 3.855 | 463.294 → 443.774 |
| A | 7.605 → 1.585 | 7.171 → 0.879 | 160.353 → 160.911 |
| V | 114.529 → 14.891 | 107.262 → 8.242 | 2963.853 → 2987.581 |

三路终端拟合显著改善，但非终端Q尾部仍异常，A/V甚至略高于对照。不能据此宣称全面修复，
不能将加权loss值与原uniform loss直接比较，也不能把历史replay拟合当作在线任务提升。
图与实际数据已核验，全部新臂/对照初始state和实际抽样流一致，原checkpoint/replay不变。
入口验证权重1与原实现的一次更新后**整个learner state逐项完全相同**；非法权重拒绝，
独立三样本有mask的标量例子验证加权分母。该测试共2次辅助更新，不混入正式计数。
本轮两组诊断合计40000新辅助更新+2入口更新，历史I/A对照10000被复用两次但不重复计新工作。

## 已启动参数cycle10：一个完整周期的在线假设检验

正式目录 `B/runs/parameter_terminal128_cycle10_20261026_v3/{method}/train`，从各自准确正式9
直接恢复，保留所有网络/Adam/replay/RNG/历史，**没有导入辅助权重**。只设置终端critic权重128，
原pair target、actor学习率I/V3e-4与A3e-5、batch32768、UTD1保持；各12sampler、原CPU分组。
预算仅一个完整cycle10，不自动延长。目标是检验终端拟合改善能否在在线数据和长期bootstrap中保持，
不是宣称已经找到稳定修复。

| 方法 | 实际learner PID | GPU | CPU |
|---|---:|---:|---|
| I | 3818446 | 1 | 13–25，learner13 |
| A | 3818448 | 2 | 26–38，learner26 |
| V | 3818450 | 3 | 39–51，learner39 |

固定原trainer由独立wrapper装入；只替换PublishedLearner子类与有限阶段protocol gate。
critic train源从冻结作者函数重建并核对原数值修正hash，仅替换masked critic regression一处。
候选函数SHA=`2bb73fcb6ab4050a9ca4200d5cfb066ee366f2306be7ab80c2272de697eb0b22`，
权重另由注册值128绑定；base、helper、driver及注册hash齐全。checkpoint记录
`terminal_loss_weight=128`，后续恢复须使用该wrapper/helper，不能用原loader静默丢弃目标标记。
只读Q诊断可用原网络forward，但训练loss必须标明是终端加权后的值。

三个方法的真实check-only均通过：全部learner/Adam/RNG逐字段一致，仅增加权重标记；
修改batch/UTD/clock/权重/预算或引入辅助权重均拒绝。实际启动第二版只读审查通过：
I新增4000、A/V各新增5000，更新增量逐项一致；父409500/408500/409500条replay全部字段前缀精确，
历史和所有optimizer参数组保留，weight128/pair2/finite网络正确。各12真实子进程亲和性和MJB一致。
全部新增raw action×context到参数控制器输入、canonical48缩放/context/时钟/nextstate、reward/done
核验通过，reward重建误差0。公共7维输出只核验形状/有限/边界，阻抗另核验零运动桥接；
没有独立重模拟导纳/VMC内部状态或原始子步。启动快照没有终端，不能替代完整周期审查。

准确边界归档3818454，view=`parameter_terminal128_archive_view_20261026_v3`，
output=`parameter_terminal128_archive_20261026_v3`。cycle10只读3965208在
`parameter_terminal128_cycle10_review_20261026_v3`，等待三路准确边界并检查父prefix/30terminal/
reward/健康诊断；绘图已显式标记terminal-weight128 q_loss。它不派发下一阶段。

## 预检失败、纠正与保留范围

- v1缺冻结校验依赖，check-only导入时失败，未启动训练。保留FAILURE及原CHECK_ONLY。
- v2补齐依赖后，CPUcheck-only全状态比较发现仅`cuda_rng.1`不同；所有网络/optimizer字段一致。
  原因是CUDA延迟初始化在恢复后重新播种。v3先初始化全部CUDA generator，再恢复保存RNG；
  保留严格逐字段相等守卫，三路最终全部通过。v1/v2从未启动learner，没有重复在线训练。
- v3真实启动第一版审查错误地沿用Direct逻辑，将参数向量与7维公共运动输出比较，阻抗5vs7
  触发失败。两者本来就是不同接口：阻抗参数调节内部力矩，公共运动输出为零。
  保留原审查源码/错误；第二版分别检查参数输入与公共输出契约后通过，没有重启训练或隐去范围限制。

## GPU和后续工作

诊断混合窗口60.55/63.42/59.68/66.77%，后三卡是有限辅助，不当正式在线利用率。
三路恢复后新的纯正式60样本窗口：**56.48/43.85/40.92/40.08%**，无辅助任务。
D/I/A/V吞吐28.09/31.75/30.97/29.47 steps每秒；参数sampler分别使用10.21/10.22/10.19物理核，
四原learner在全部样本存活。每卡持续≥50%仍未达到；不能重复已完成诊断填占用。
Direct30worker也未显示吞吐提升；本轮没有把增加batch/UTD当作占用补丁。

继续原Direct6与参数10并收取审查；重点看非终端Q是否仍漂移、终端校准能否维持、任务reward/
Task/Strict与未加权TD诊断是否改善。若只是加权loss更小，不能作为收敛证据。
最终冻结策略验证/指定ESN与SPT公平比较、健康收敛及持续GPU要求仍未完成。大产物留SSD，
小证据映射见 `docs/evidence/rl_terminal128_cycle10_20261026/SOURCES.json`；不是HDD全量快照，
也未声称已上传arm1。

本轮小文档副本：`/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_TERMINAL128_STATUS_20261026_105937`，仅报告/AGENTS/UPDATE_LOG，非运行产物全备份。
