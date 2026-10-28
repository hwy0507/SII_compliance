# 参数53完整审查与有限54续训（2026-10-28）

Goal active。当前正式为Direct33和三参数54，旧53均完整退出。GPU守护保持[v4](RL_GPU_GUARD_V4_20261028.md)，已经独立验证VMC退出后GPU3仅守护时最低69%、30样本均≥50%。当前进度需核各run的PROGRESS及/proc，不据旧PID盲目重复启动。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；实际主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本阶段源码基于已发布main `c3d5672622942e4f934ec59e9267abcdf25d99f6`，baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；此前并行场景演示合并仅更新仓库，不改变冻结runtime。

## 完整53结果

三方法全部30个完整55秒/noabort。原archive monitor已完成：独立复制checkpoint并核SHA、全旧replay/history保留、新41250奖励按冻结interval journal重算误差0、优化器/网络有限、双容量marker/entry23/47和4m保持。健康诊断只读network不变，图已实际查看。不是独立重跑全部物理。

| 方法 | steps | updates | mean reward | Task/Strict | critic首→末1000均值 | critic最大 |
|---|---:|---:|---:|---:|---:|---:|
| 阻抗 | 2,223,680 | 2,218,681 | −4.030496866 | 17/16 | 2.101266→3.072625 | 76.325073 |
| 导纳 | 2,223,500 | 2,218,501 | −8.524903781 | 14/14 | 1.891316→1.457763 | 27.263952 |
| VMC | 2,224,500 | 2,219,501 | −4.568304136 | 17/16 | 0.659883→0.833407 | 32.921684 |

loss各41250条，无非有限critic/actor值。导纳本轮逐步回落；阻抗与VMC尾部上升、actor漂移和尖峰保留，不能称全部健康收敛。terminal in-bag MAE I/A/V .603385/.300376/.267938，sampled TD MAE .269495/.222716/.168395；A/V采样Q超过当前alpha全局bound的比例约.000928/.001660，非零如实保留，不把target上界投影等同Q校准。

完整53 checkpoint路径：`B/runs/parameter_capacity_pool30_cycle53_archive_20261026_v1/{impedance,admittance,vmc}/cycle_00053.pt`，SHA分别：

- I `56653f09f342b0c0835224edde1c0672494b703140ade5fb215f3aaf1d1959af`
- A `93330d32ef7e27fea72ff814f5a9c3f91872c63e4f91b8ca03704682ea3ebefc`
- V `8880753064ccfbd949a88de18da3f70ddc72209915cc4ad5661fcd4a7b2104d6`

## 标签变化诊断

52→53全30个条件的配对reward差值保留，所有Strict变化逐一核保存rollout/执行代码/同MJB及原0.2mm穿透门槛。相同short0600条件：I穿透.192759→.205547mm，V .174974→.210618mm，Task均成功但Strict失去；A .234536→.190214mm，恢复Strict。I另丢long0000任务；A另有多个任务成功/失败翻转。这个事实解释回报跳变的组成，不证明某回放样本造成loss尖峰；没有独立重算全部接触，不改gate/reward/physics。

## 54已启动

恢复准备原waiter1059039已完成。三方法准确53全state/所有replay/下一65536与RNG check-only均通过；本轮原配置不变，未导入辅助权重。完整53审查、loss/health图及上述问题审阅后，已登记有限一轮54继续原前瞻53–55窗口，convergence_claim=false。

`B/runs/parameter_capacity_pool30_cycle54_20261026_v1`，I/A/V learner PID2116858/2116859/2116860，GPU1/2/3，CPU分配和30sampler保持。archive/review monitor2116861，实际startup审查2158415；startup最终结果须读`startup/REVIEW.json`，不能以check-only替代实际新增审查。无自动55正式训练。

启动54之前固定登记三方法前5000更新跟踪，`B/runs/parameter54_first5000_20261028_v1`，waiter2158459，固定3600秒，保存完整前缀/hash和critic/actor统计/图；不自动停训，不替代预登记53–55 reward窗口。

Direct33原259795继续，Direct34恢复准备1059038仍等待完整父；原53–55稳定性waiter514418仍按固定窗口运行。科学目标仍未完成。

## 保存

小证据`docs/evidence/RL_PARAMETER53_COMPLETE_20261028`；包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER53_COMPLETE_20261028_041907/SMALL_EVIDENCE.tar.gz`，686057字节，SHA256 `bd132b47c7b7c18811de5e6ebc04413e2588f4245f4b3831366d7a1a77c819db`，19源码/小证据成员逐大小/hash核验并含两张诊断图。大checkpoint/replay/raw继续共享SSD，不是HDD/arm1完整备份。HDD既有LATEST只保存入口。

54实际startup随后已通过：I/A/V新增1000/1000/2000，旧2223680/2223500/2224500条replay全部字段/history保留、原optimizer配置/双容量marker/4m/30MJB/30sampler/动作与clock映射通过，新reward重算误差0；此次首批无终端，不代替完整54审查。最终证据docs/evidence/RL_PARAMETER53_COMPLETE_20261028/stage54/ACTUAL_STARTUP_REVIEW.json，补充包B/repository/RL_PARAMETER53_COMPLETE_20261028_041907/ACTUAL_STARTUP54.tar.gz逐内容核验，SHA256 `981f73e1138eb050d82b20acff42a84e886b1f971d42947734f66340d6e48a8d`。
