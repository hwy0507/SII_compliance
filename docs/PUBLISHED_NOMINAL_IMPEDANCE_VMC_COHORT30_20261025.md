# 固定名义 Impedance/VMC 完整训练条件基准（2026-10-25）

原名义矩阵slot1已结束，Impedance、VMC各30条件的结果及物理/filter证据完成复核。固定名义控制器本身已分别达到Task/Strict18/30与17/30；因此RL在训练中得到接近的成功数，不足以证明学习收益。最终必须用冻结RL策略在同条件逐项比较，不能把变化中训练policy的整轮成功数当作固定策略接受结果。

## 完整结果

| 固定控制器 | Task/Strict /30 | 被动Strict /10 | 短期Strict /10 | 长期Strict /10 | 全30回合最大广义力矩 | 机器安全违规 /30 |
|---|---|---:|---:|---:|---:|---:|
| Impedance | 18/18 | 0 | 10 | 8 | 59.2441 Nm | 0 |
| VMC | 17/17 | 0 | 10 | 7 | 48.0088 Nm | 0 |

均完整55秒、1375动作、110万物理子步。失败阶段分别carry12和carry13；被动10例均失败。平均训练代理reward分别−0.45137和−2.84777，不能用于最终方法排名。

| 固定控制器 | 实际人接触回合数 /30 | 人接触总时长 | 接触且力矩合规时长 | 按接触时间汇总合规率 |
|---|---:|---:|---:|---:|
| Impedance | 8 | 130.75935 s | 41.81345 s | 31.9774% |
| VMC | 8 | 97.01005 s | 69.94180 s | 72.0975% |

实际人接触均出现在长期任务。被动/短期无人接触，舒适合规率为NA。阈值仍为工程参考`[43.5]*4+[6]*3 Nm`，人接触起点`>0.05 N`；没有临床舒适性验证。汇总分母含所有回合中的实际接触时长，包括失败回合；不是成功回合筛选或逐回合百分比的简单平均。最大广义力矩统计全回合，不能与接触条件比例混用。

Strict成功回合的完成时间范围：Impedance短期12.96–13.32s、长期15.68–28.92s；VMC短期20.48–33.16s、长期30.24–44.64s。这些范围仅描述成功子集，未完成回合保持失败并留在成功率分母。最终共同Tref/SPT仍未选择，不能据此宣称最终效率排名。此前单个代表条件VMC接触100%不能推广到完整长期条件，当前整组为72.10%。

## 本次复核与边界

新增只读工具`review_published_nominal_completed_20261025.py`，冻结于集群SSD `runtime/nominal_completed_review_v1`。进程3919824完成并退出：60例、6600万既有子步，0新增physics/optimizer更新，未重复任何轨迹。

逐例重新核验物理/filter审计引用的原始文件hash、实际MJB/cohort一致性、零raw action、1375条journal、完整55s/110万子步、reward组件与结果行一致性。由原始实际力矩重新检查幅值界、每80子步内力矩保持、相邻4ms servo输出的slew界，并重新计算峰矩、人接触时长和合规时长，全部通过。原PHYSICAL_AUDIT的filter_replay_verified=false表示该单项审计不覆盖filter；另有FILTER_REPLAY_AUDIT passed=true。本复核读取两种独立收据，不把前者误判为filter失败。

**该较早v4记录没有后续新增的torque投影内部输入。** 因而可核验实际力矩幅值和相邻servo变化率，不能完整重放请求力矩→投影输出，也不能验证第一servo之前未保存的previous torque。报告明确保留这两项限制，不伪造缺失输入。其他固定RL评估拥有更完整投影trace，不因此倒改或重复本批次原物理结果。

名义source06与当前CHEQ source14的parameter/robot资产manifest字节相同，且公共WBC core、audited environment、episode adapter、reward和comparison metrics五个实际源文件hash相同；实际MJB另按60例逐项核验。这是指定文件和输入合同的比较，不宣称两个完整runtime全部相同。

## 持续任务与位置

本轮fetch/read main a52dfba、baseline f6e8f8c，远端未变。原八learner继续，CHEQ11完整审计仍待；原SAC Admittance/VMC cycle3只读observer3759872继续。名义slot0原2210514仍处理Direct/Admittance末尾条件；slot1原2210515已退出勿重启。source16未部署，physics/MJB/gate/actor/filter/执行器/dt不改。

计算主机和哈希见同名JSON。产物在：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/nominal_completed_impedance_vmc_review_v1`，包含REGISTRATION、LAUNCH、results/{impedance,vmc,REVIEW}.json及COMPLETED_REVIEW.json。原轨迹仍位于`runs/nominal_four_interfaces_cohort30_v1`。

后续完整名义矩阵复核应复用本次已完成的两接口验证，不重复仿真。最终训练收敛/优化健康、GPU持续50%、四接口固定策略SPT和指定ESN公平对比仍未完成。
