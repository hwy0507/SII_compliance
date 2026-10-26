# 时钟在线第二周期完整复核

2026-10-26。上一轮实质进展：完成辅助结果复核、启动固定策略矩阵并审查Direct第二周期。
本轮fetch main `6dc2b241215d1898f8e07916153f3e0754dfb3db`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新远端提交。
原四learner和归档/审计、固定策略协调进程均核对live；等待原完整快照，没有重复派发。

## 第二周期（cycle index1）

|方法|累计steps|累计updates|Task/30|Strict/30|本周期平均reward|末1000 Q loss|累计回放终端Q MAE|
|---|---:|---:|---:|---:|---:|---:|---:|
|direct|82500|77501|0|0|-32.920646|19.000493|63.818167|
|impedance|81439|76440|17|16|-4.400356|5.638129|22.994952|
|admittance|82500|77501|12|11|-13.797433|13.131371|53.802093|
|vmc|82500|77501|17|16|-4.573680|26.072100|74.074436|

本周期119个完整55s回合与1个提前中止，所有120回合保留在分母。全部方法被动0/10。
Impedance短期10/9、长期7/7；Admittance短期9/8、长期3/3；VMC短期10/9、长期7/7（Task/Strict）。
Direct失败approach24/align6；其余主要carry，早停Imp属于release。

首→次周期Strict：D0→0、I16→16、A13→11、V16→16。
reward：D−32.788830→−32.920646、I−4.073308→−4.400356、A−10.317198→−13.797433、V−4.607349→−4.573680。
末1000 Q loss四路均增加；Direct/VMC的Q值与actor loss继续漂移，Impedance累计终端MAE约22.88→22.99。
终端MAE来自各快照累计回放的全部终端（首周期30、次周期60），不是固定不变的配对样本；只能作训练诊断。
图已目视复核，不能将低波动/finite权重称为健康收敛，也不能凭两周期宣布算法不适用或时钟修复已失败。

## 实际证据范围

`runs/clock_cycle01_scientific_review_v1/REVIEW.json`：781源码、四checkpoint、120本周期终端/模型/fixture/plan/reward核验。
累计328939条replay的current/next已知时钟和done逐条通过；完整周期中的每条件计数与实际episode steps相符。
原诊断只读且network_state_unchanged；本轮没有新增优化器更新或物理回合用于周期审查。
这是已保存回放/终端/rollout-summary审查，不是在线120回合raw-substep安全重放。采样期间策略变化，不是固定策略acceptance。

## 早停与Strict失败

Impedance `active_long_train_0500` 第314动作、12.56s在release阶段触发`global_penetration_exceeded_2mm`。
保存rollout最大global穿透66.935704mm、external穿透0.0125729mm；两者定义不同，不用低external数值掩盖global失败。
该失败计入Task/Strict分母。独立EARLY_ABORT_REVIEW核验：done1、bootstrap multiplier0、terminal−25、failure_tail−13.111008119。
当前/下一剩余时间分别1062/1375与1061/1375；未用事后知道的提前终止时刻把clock伪设为0。

短期0600的Impedance/Admittance/VMC均Task真Strict假，external穿透分别
0.2292177522/0.2107698118/0.2067260417mm，超过原0.2mm gate，全部保留。

## 新时钟固定策略的首个完整物理审查

原`clock_cycle00_fixed_representatives_v1`矩阵继续；协调2960898、首评估2961606，未重启。
独立`runs/clock_first_fixed_case_review_v1/REVIEW.json`已复算首Direct/passive0000全部110万子步。
learned物理/filter/torque重放通过，同名义模型/fixture/plan/dt；原nominal复用既有独立审查，未新增nominal torque扩展声明。
Task/Strict假、approach失败、完整55s、机器安全违规假，峰值广义力矩39.558577Nm。
实际人接触0s，舒适比例NA，不用静止/无接触给高分。未选择最终Tref。
主动短期也已完整55s Task/Strict假、approach失败，但尚未在本收据中独立完成物理子步复算；长期仍在原进程中。
这只是预选代表矩阵进展，不是最终30条件或指定ESN比较。

## 决策与继续运行

继续原六周期stage，下一统一审计为cycle3/5。四learner1729888/1729892/1729893/1729897，归档1729901、原审计1729905。
本轮只读review工具session39167已正常完成；不要将其结束当作训练停止，勿重启。
不依据两个周期改live reward/gamma/UTD/batch、actor输入、physics/MJB、gate、公共filter、执行器限制或dt。
辅助return拟合已结束，不继续创建重复辅助工作。当前正式GPU50%目标仍未解决；不沿用旧混合高利用率。
目标仍active：健康收敛、最终冻结策略矩阵、SPT_empirical和指定ESN比较未完成。
原始产物仅本集群`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；小型证据见同名JSON，未宣称已传至其他主机。

收尾fetch main新增c3124ba322853c1e561657b58c4204ed2a64a1b6：已读并合并另一airpig主机用户授权旧产物清理/存储解除报告；保留双方UPDATE_LOG追加块。该清理未发生在本集群，不删除或变更当前RL产物，尚无新的指定ESN物理结果。本轮在线报告提交bbc8513，push仍因HTTPS认证失败未发布。
