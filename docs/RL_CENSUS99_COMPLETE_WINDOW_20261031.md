# 第99轮完整审查及原97–99窗口完成 — 2026-10-31

**Goal active，未收敛。原第99轮三训练/归档/四诊断全部正常结束，不能重启这些已完成进程。原97–99窗口三路均未通过5%奖励稳定性检查；阻抗新物理中止与原loss尖峰明确保留。尚无100派发，下一阶段须依据本轮失败诊断独立登记和完整恢复预检。GPU guard继续。**

|方法|新增步|Task / Strict / 30|平均reward|原loss均值 / 最大|
|---|---:|---:|---:|---:|
|impedance|40882|17 / 16|-4.297839897|1.126621 / 22.261616|
|admittance|41250|15 / 14|-8.434798316|1.028893 / 1.626923|
|vmc|41250|17 / 16|-4.601926107|0.751349 / 2.861036|

I为29完整55秒+1中止，A/V各30完整55秒。I `active_long_train_0000`在40.28s/1007动作触发`global_penetration_exceeded_2mm`，较完整回合少368动作；Task/Strict均失，仍留30分母。原记录全局穿透87.091390mm、最坏对凸边/目标物体，外部穿透仅.066886mm，不能混淆。与98同MJB；独立核805600原物理子步、dt5e-5/终止时刻及float32 torque峰值，接触深度本身未原样逐子步记录，未声称独立重建穿透。

完整99旧replay/history/violation精确保留，全部新52/action/reward/30模型按原检查核验；只读诊断前后learner/Adam/RNG不变，逐条奖励误差0。全新增context补充覆盖无尾部排除。原loss全部123382更新的原JSONL/保存数组/独立标量通过，五实际图已检查。I末1000原loss1.386599较首1.106786上升，最高22.261616；actor从约27.54降26.38，明显漂移。A原loss约1.029但旧终端拟合退化，V末段尖峰2.861036；有限值不是健康通过。

固定8803旧终端原mask SSE变化I−15.8621%、A+46.1728%、V−1.3001%；退化行1307/1959/1256均保留，五critic与未mask误差分列。新增90及全部8893终端参考逐条绑定、旧8803预测复现、全learner/Adam/replay/RNG不变。新99 masked SSE为8913.966721/6.094042/2.710804。

阻抗新long0000终端reward−36.681351，五critic仍预测约5.15至5.95，全mask为1，SSE8909.666519占全部新I误差99.9518%；原violation bit0保留。原loss最大点在其终端后30更新；无抽样索引，只有时序关联，不作样本因果解释。A尽管平均reward变化很小，Strict获得short0100/long0200、失short0600/long0500，Task获得long0200、失long0500。V Task/Strict集合不变。全部成功退化/失败保留。

## 原97–99窗口

|方法|97 / 98 / 99 reward均值|相邻相对变化|端点相对变化|原5%检查|
|---|---|---|---|---|
|impedance|-4.200142 / -2.397637 / -4.297840|42.9154% / 79.2532%|2.3261%|失败|
|admittance|-6.807197 / -8.476092 / -8.434798|24.5166% / 0.4872%|23.9100%|失败|
|vmc|-2.870847 / -4.576209 / -4.601926|59.4027% / 0.5620%|60.2986%|失败|

恰九组真实checkpoint/父链/日志/原loss/两核心图绑定通过。原5%/nearzero1/5000bootstrap/seed2026102861与.025/.975区间保持，原始标量及同抽样下独立均值/线性分位数复算通过；bootstrap仅条件组成敏感性，非独立seed或冻结评测。不移窗口到98–100，原94–96失败保持。

发现原锁定audit仍有`current_replay_capacity == 4000000`旧断言，与已登记96→97扩到600万及实际九checkpoint不符。原audit/PLAN/SOURCE_LOCK逐字保留；独立`repair_window_capacity.py`执行时仅把该断言常量改为6000000，并额外检查所有九组原4m历史标记与6m标记。实际97/98六组复现旧断言拒绝、正确检查通过，24损坏容量/标记拒绝；AST证明统计逻辑无变化，执行源码hash/修复收据显式绑定最终报告。不是阈值或窗口放宽，详见`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census99_window_completion_preparation_20261031_v1/CAPACITY_ASSERTION_REPAIR_REVIEW.json`。

## 运行与恢复

完成监视3208.754s/321样本，八原作业均已核成功终态；无重启。GPU保存780样本/3989.636s，min[72, 65, 64, 66]%、低于50[0, 0, 0, 0]、末[78, 71, 79, 71]%。包含保活负载，不是科研吞吐或每瞬时保证；科学结束仍保留`/tmp/sii_gpu_util_guard_20261031_recovery_v1`，勿创建STOP，非开机自启服务。

直接动作分支保持原Direct33数值验收与冻结30 Task/Strict0/0，不追加34；原28最终memory缺口/恢复2已证、指定ESN缺失、最终共同集合Tref/SPT和公平冻结比较仍待。参数下一有限阶段还须按99失败及完整97–99结果决策、准确最新99全state恢复；不以阶段完成/有限loss代替联合收敛。

主机`rltest-1025--a6ed2ff39b3c-cn2p6rygmr`；共享SSD根`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`；三最终checkpoint位于`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle99_archive_20261031_v1/<method>/cycle_00099.pt`，hash见核心REVIEW。全部99审查`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census99_completion_20261031_v1/COMPLETE99_SCIENTIFIC_REVIEW.json`，原窗口`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census97_99_reward_stability_20261031_v1`。

小证据包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS99_COMPLETE_WINDOW_20261031/SMALL_EVIDENCE.tar.gz`，181成员/10776467字节，SHA256`11561cd5e4b77645c49f57577afd0f12a1af9f197665ba347782e572aadbfacf`逐成员回读通过。依赖先前97/98/99启动归档和原共享SSD大checkpoint/replay/raw；HDD配额满，仅254-byte LATEST指针更新，非HDD/arm1全备份。开工mainbddee503/baselinef6e8f8c2实际query/fetch/read，发布见`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS99_COMPLETE_WINDOW_20261031/PUBLICATION.json`。
