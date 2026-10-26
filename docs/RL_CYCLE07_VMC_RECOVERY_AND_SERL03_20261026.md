# 2026-10-26 VMC cycle7失败审查与恢复双target、SERL cycle3及I/A cycle8

原Goal active，训练尚未健康收敛；GPU每卡≥50%仍未满足。本报告覆盖前一交接的实时进度，
不覆盖冻结的物理、MJB、gate、filter、执行器、dt5e-5、30条件或SPT reward。
执行根目录为本集群SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`（B）。
开工main=bca082135c8f8fe2ed82371bcbb67cd4aeddd7cc、baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，
之后读取并快进d9de51c与64ddfef046e9b63e5658329ae0ddc548ab39506f；后两者是另一主机非RL学习曲线/
轨迹归档，未干预其任务或把其模型/条件擅作本集群最终比较。

## 最新完整结果

| 方法 | 完整周期 | 累计transition / critic更新 | Task / Strict，各30 | reward均值 | 终端Q MAE |
|---|---:|---:|---:|---:|---:|
| 官方SERL Direct | 3 | 163214 / 1265720 | 0 / 0 | −34.19838 | 1.00529 |
| Impedance | 8 | 368250 / 363251 | 18 / 17 | −2.27207 | 9.12095 |
| Admittance | 8 | 367250 / 362251 | 13 / 13 | −10.35582 | 3.92555 |
| VMC all5试验 | 7 | 327000 / 322001 | 17 / 16 | −4.60216 | 54.90314 |

各完整周期的全部父replay字段前缀、每条新增reward/done、30条件terminal、fixture/MJB及
参考计划hash核验通过，网络/optimizer有限；每条新reward用冻结SPTReward从interval journal
重建，最大误差0。Direct额外逐条核验canonical48、动作仿射映射、nextstate及零bootstrap。
这些在线周期审查不是原始物理子步的重新独立计算。

Direct3新增40018transition，26个完整55秒回合与4个提前终止，失败保留在分母：
active_long_train_0100 / active_short_train_0900 / active_short_train_0300 / active_long_train_0000，
分别1047/1057/1079/1085动作，均global_penetration_exceeded_2mm、均approach失败。
终端Q MAE2.348→1.005，120条历史终端×10critic误差p95=.419，但max37.28；
抽样TD MAE.02291、Q均值11.405、alpha.00051095。loss大多.001–.01并有尖峰，Q先降再回升。
只读诊断full state/RNG不变，图已看；reward由−33.524回落−34.198，仍0/30，不能凭低TD loss称学会任务。
精确cycle3 checkpoint SHA b72e289704896a8db61558ce587fb6a5b9ece0972d4959e95b05515872cee327。
原521120已进入登记cycle4，没有新派Direct阶段。

I/A cycle8各新增41250、30完整55秒、无abort。I的cycle6/7/8 reward−2.293/−2.349/−2.272，
Strict均17；但terminal MAE2.942→3.649→9.121、末1000 Qloss3.505→13.585，不满足loss健康要求。
A由cycle7 Strict15/reward−6.900回落到13/−10.356，terminal MAE1.951→3.926、末Qloss5.866→29.514；
Q均值从28.23降至−.432。此前降低actor LR的早期改善未持续，不能继续沿用“改善中”结论。
原806847/806849继续已登记cycle9；暂无cycle10及以后部署。
I8 SHA29e64d9b15eba940003a4d66b5da07d45917cab247fa61328daf5f15e58aefe9，
A8 SHAfe90940d6e60bbb58f9b182fbd03c7ebd51944c4d58083d50b5ab87c7d33978f。

## VMC完整all5试验的结果

cycle7全30完整、无abort，新增41250条，reward与cycle6近似；但term MAE16.01（cycle5）→29.32→54.90，
in-bag53.16、out-of-bag61.29，末1000 Qloss394.57。抽样replay Q均值−5.664、范围−1236.47至1426.46，
p95正Q914.45。Q均值降低没有代表校准改善，all5这两周期试验失败，原3419078正常预算结束，不重启。
精确cycle7 SHA aef5f5d6fcd1387edccf08eae97c008a2ea202b11962a4eaf5c438f39e263023。
三参数cycle7统一审查/诊断与原准确归档均已完成；441621/3494331已结束勿重启。
证据B/runs/reviewed_cycle07_audit_20261026_v1，诊断图已目视检查。

进一步核验真实在线mixing context与replay第48索引特征逐条一致：

| 方法 | cycle6平均RL权重 | cycle7平均RL权重 | cycle7处于最低权重0.2的动作比例 |
|---|---:|---:|---:|
| Impedance | .6538 | .5428 | 29.11% |
| Admittance | .4223 | .3445 | 54.47% |
| VMC | .2077 | .20125 | 99.34% |

三参数cycle6/7被动10条件均carry失败；I7短期Task10/Strict9、长期8/8，A7短期9/9、长期6/6，
V7短期10/9、长期7/7。这些是实际行为分布，说明不能用平均reward稳定替代“RL学会了任务”。
没有据此调整CHEQ不确定性阈值，也没有因果证明提高RL权重会改善成功率。
证据B/runs/parameter_cycle07_mixing_review_20261026_v1，0新physics/updates。

## 同一cycle7状态的有限恢复对照

B/runs/vmc_cycle07_target_recovery_probe_20261026_v1，GPU3/CPU54、三臂各5000更新，合计15000，
0新physics，完成即退出，不保存或推广权重。新工具probe_vmc_target_recovery_20261026.py保留
同一完整learner/optimizer/replay/masks/RNG，逐臂恢复digest精确相同，replay抽样流相同，
原checkpoint及CPU replay不变。每250更新记录一次，20点/臂全部有限，图已目视检查。

| 臂 | 终点terminal MAE | in-bag MAE | 抽样Q均值 | 抽样绝对Q p95 | 最后一次Qloss |
|---|---:|---:|---:|---:|---:|
| 保持all5、原LR | 47.250 | 46.811 | −43.005 | 910.227 | 534.345 |
| 恢复随机pair、原LR | 33.045 | 31.676 | 66.121 | 1200.464 | 920.380 |
| 恢复pair、critic LR×.1 | 42.268 | 41.334 | 56.489 | 1112.563 | 815.099 |

初始terminal MAE54.903、in-bag53.159；诊断取4096个非终端普通样本，初始Q均值4.999、绝对Q p95
991.323，和完整健康报告的固定抽样集合不同，不能把两个Q均值直接当作时间变化。
pair终端拟合改善较多，但Q尾部扩大、loss仍异常；降criticLR也没有形成稳定修复。仅据此撤回失败的
all5干预，恢复原pair来继续在线检验，不宣称修复，更不能推广拟合误差最低的辅助权重。

## VMC恢复原target后的真实在线阶段

B/runs/vmc_pair_recovery_cycle08_09_20261026_v1/vmc/train，PID1497979、GPU3、CPU39–51、12sampler，
有限2完整cycle8/9。从真实正式cycle7完整checkpoint继续，仅去掉learner的bellman_target_count5元数据，
恢复原随机双critic target。actor/critic/alpha网络、Adam moments/counters、学习率、replay、随机状态
均逐字段digest保留；没有回退到cycle5，也没有导入任何辅助权重。原actor随机pair保持。
新阶段cycles聚合列表置空，仅避免混合all5阶段的plateau统计；原完整history仍在父checkpoint。
prepared SHA3ea2d211f4634b0c233c5cea92218d8c42d96523f36c96acf7be05a22d131fc3。
原冻结trainer的completed-stage协议、准确parent_cycle7/new_cycles2/原actor LR验证通过。

准备脚本v1在完成checkpoint准备和原trainer校验后，查找了不存在的方法目录LAUNCH.json，
因此在生成命令阶段失败，未启动训练。随后改从原根LAUNCH.json的VMC job读取命令，重新核验源/准备
checkpoint hash后才启动；原失败脚本和日志保留，PREPARATION_RECOVERY.json明确记录修正。
没有重复训练、没有重复准备学习状态，不能把v1说成无错误执行。

实际新增3000transition及3000optimizer更新时，父327000条replay全部字段前缀精确、target2、
原actor/critic optimizer配置、history、网络有限性及12个MJB核验通过。
证据B/runs/vmc_pair_recovery_startup_20261026_v1，0新physics/updates的独立检查。
精确归档1497983在B/runs/vmc_pair_recovery_archive_view_20261026_v1，产物vmc_pair_recovery_archive_20261026_v1；
只读cycle8审查1566165在B/runs/parameter_cycle08_vmc_review_20261026_v1等待，不自动延长预算。
I/A cycle8只读1566163已经完成，产物parameter_cycle08_ia_review_20261026_v1；Direct3只读1210386已完成。

## GPU和实际流水线测量

有限辅助窗口约一分钟，GPU0/1/2/3均值49.85/55.40/46.43/67.48%；前三卡正式，GPU3是VMC恢复对照，
不可称四正式达标。恢复四正式后的独立窗口60.93/26.83/20.55/40.97%，无辅助，I/A进入周期尾部，
仍未满足每卡50%。原始样本分别在vmc_recovery_probe_gpu_monitor_20261026_v1与vmc_pair_recovery_gpu_monitor_20261026_v1。

新增只读60样本流水线profile，实际66.35秒，观察原四PID的CPU消耗、子进程及真实PROGRESS：

| 方法 | transition/s | critic更新/s | learner使用CPU核数 | 物理worker使用CPU核数 | GPU均值 |
|---|---:|---:|---:|---:|---:|
| Direct | 29.34 | 234.74 | .739 | 5.438 | 60.80% |
| Impedance | 3.51 | 3.51 | .117 | 1.231 | 5.18% |
| Admittance | 12.87 | 12.87 | .341 | 4.431 | 16.40% |
| VMC | 32.10 | 32.10 | .770 | 10.322 | 42.68% |

I尾部从2个worker降至1个，A从6降至4；V有12个worker。I/A低占用伴随真实采样吞吐和CPU负载降低，
不是已经结束的learner被误判运行。V的物理采样使用接近分配的12核，简单提高GPU更新负载不能替代
优化真实采样/周期尾部调度。该profile未部署新的调度或更改live参数，0新physics/updates；
CPU统计不含相邻两次采样间完整出生并退出的worker，这是测量范围限制。
证据B/runs/batch32768_live_pipeline_profile_20261026_v1/PROFILE.json，原进程在全部样本中身份一致且live。

后续只读审查已登记并启动等待精确归档：I/A9协调2062385，VMC9协调2062386，Direct4协调2062387，
分别在B/runs/parameter_cycle09_ia_review_20261026_v1、parameter_cycle09_vmc_review_20261026_v1、
serl_cycle04_review_20261026_v1。各以紧邻完整周期为prefix/new-transition父，另核验阶段初始恢复父hash；
只读审查与诊断不派发训练，1小时观察预算超时也不停止或重启原learner。

## 发布和剩余工作

小证据docs/evidence/rl_cycle07_recovery_20261026/SOURCES.json列SSD原路径与SHA，含实际执行源码审阅副本。
大型checkpoint/replay/物理轨迹只在SSD，没有宣称已传arm1或加入旧HDD完整关机快照。
HDD剩余约496MiB，新的备份只放文档/manifest。

原Goal继续active：Direct周期4、I/A周期9、VMC恢复8/9及完整健康/冻结策略审查尚待；
I/A与VMC loss均存在未解决问题，Direct仍未成功。还需实际采样/尾部性能优化、四卡50%、充分收敛、
最终完整冻结比较与指定ESN/SPT。不得把有限对照、低TD loss、状态审计通过或局部reward平稳当最终成功。
