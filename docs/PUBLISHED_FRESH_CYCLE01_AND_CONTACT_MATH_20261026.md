# Fresh第二轮科学复核与接触计算局部性能探针

四路fresh阶段第二轮（cycle1）完整结果已核验，原登记六周期训练继续。
参数方法部分主动条件成功，但四路被动条件仍全部0/10；Direct两轮均0/30。
四路critic loss、Q预测及终端MAE上升，**不能宣称健康收敛或已优于固定名义控制**。

| 方法 | 第二轮末累计真实步数 | 首轮→第二轮 Task/Strict，各30 | 第二轮平均reward | 末1000更新critic loss，首轮→第二轮 | 全replay终端Q MAE，首轮→第二轮 |
|---|---:|---|---:|---|---|
| direct | 82500 | 0/0 → 0/0 | -33.20797 | 9.334 → 25.869 | 36.201 → 72.259 |
| impedance | 81984 | 17/16 → 18/17 | -2.39633 | 8.003 → 53.403 | 36.646 → 81.622 |
| admittance | 82500 | 12/11 → 13/13 | -10.42557 | 11.392 → 79.790 | 51.131 → 115.690 |
| vmc | 82500 | 17/16 → 17/17 | -2.86240 | 7.338 → 49.420 | 52.502 → 104.931 |

四路第二轮各30回合均完整55秒。Impedance累计步数较少来自首轮中止，不删失败补齐步数。
按被动/短期/长期，Task/Strict分别为：Direct 0/0、0/0、0/0；Impedance 0/0、10/9、8/8；
Admittance 0/0、8/8、5/5；VMC 0/0、10/10、7/7，每类分母10。
固定名义完整30条件结果Task/Strict分别18/18、18/18、16/15、17/17，参见此前名义矩阵报告；
当前训练时policy持续变化，不能将以上训练统计与固定名义矩阵直接作正式策略排名。

统计范围已统一：原DIAGNOSIS中Impedance的episodes/ended_episode_returns包含cycle0和1共60回合，
另外三路恢复后日志只含cycle1的30回合。本表显式按cycle==1过滤，Impedance第二轮reward为
−2.396327，不能引用两轮合计−3.362948冒充第二轮。原图保持真实历史范围，未重写旧诊断。
critic loss取各自末1000更新，终端MAE基于两轮累计replay中的60个终端×5个critic；二者不是同分母。

第二轮末in-bag/out-of-bag终端MAE：Direct56.910/137.693、Impedance78.608/94.756、
Admittance97.779/177.976、VMC92.957/140.853。mask=0对应该critic刻意未训练的样本，
样本年龄及不含剩余时间的观测也可能影响误差，不能将全部终端误差归因于发散。
但这些限制同样不能把loss有限、entropy接近目标或reward暂时平坦解释为健康收敛。
当前证据不足以选择新的critic时间输入、奖励或学习协议，未实施这些变更。

Direct第二轮失败阶段approach15、align8、grasp6、carry1；三参数方法主要仍卡在carry。
Impedance短期0600仍Task真/Strict假：球与hand_collision外穿透峰值0.2276335mm，超过原0.2mm。
1375个保存区间峰值复算一致，终端项−25、效率项0。所有失败保留；未改gate。
这次核验不是新增原始物理子步安全审计。

## 核验与产物

核对4份checkpoint的原archive/审计snapshot/诊断副本字节hash、完整周期边界、replay长度、
更新数、training registration、网络有限及诊断未更新网络；120个终端/模型/fixture/plan/dt和
reward分量合计均通过。source_train16的780个源码hash重新核验。诊断六面板图已人工查看。
本次科学复核0新physics、0optimizer updates，原正式训练持续。

服务器基址：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/`。

- `runs/fresh_cycle01_scientific_review_v1/REVIEW.json`：逐方法、逐条件核验及hash。
- 同目录`IMPEDANCE_STRICT_FAILURE.json`：唯一第二轮Task/Strict不一致详情。
- `runs/fresh_ready_methods_audit_v2/fresh_cycle_01/results/`：原诊断、图及完整checkpoint。
- 原审计2472115完成cycle1后继续等待cycle3/5，原训练协调2471936和归档2472286继续。

## 接触计算微基准，不是整体加速结果

新增工具`code/mujoco_6d_vmc_benchmark/tools/probe_published_contact_math_20261026.py`，
登记`runs/CONTACT_MATH_PROBE_V1.json`，冻结副本`runtime/contact_math_probe_v1/`，
结果`runs/contact_math_probe_v1/`。原PID1566953/session9489已完成，不重复执行。

仅测试两项局部候选：缓存model.geom_bodyid数组视图；对连续float64三维向量使用
`float(np.sqrt(value.dot(value)))`。30个真实冻结MJB的269020个几何对比较完全一致，
65536随机、5特殊、8715记录/重建向量的范数结果逐字节一致，模型数组和计时读取中的积分状态未变。
三个Admittance归档轨迹各取6个状态；调用18次mj_forward重建接触，没有mj_step、
新增物理transition或optimizer更新。因此不能称完全没有物理计算，也不能将重建力当作历史求解力。

局部CPU计时的原耗时/候选耗时中位比：geometry3.399倍（2.556–3.480），norm1.460倍
（1.419–1.490）；每次全列表读取的原/新中位耗时分别18.883/5.558µs、79.584/54.413µs。
共享CPU负载、重复缓存读取和限制输入形状使它不能证明完整轨迹等价、整体吞吐或GPU50%达标。
本次只提交可复查探针与证据，**尚未准备或部署完整环境候选**。后续若采用，必须独立构建、
登记并完成全轨迹/动作/子步审计；不能将局部测试直接推广到2D向量、gate或其他dtype/layout。

## 继续工作边界

当前继续原六周期有限阶段并审查cycle3/5；六周期不是总训练上限，也不是自动收敛门槛。
physics/MJB、gate、actor信息、公共filter、执行器限制、dt、live reward/batch/UTD均未改变。
充分训练、固定checkpoint训练集矩阵、最终SPT_empirical/接触舒适审计、指定ESN比较仍未完成。
指定ESN尚缺，不以历史ESN替代。GPU50%未解决；不得用辅助GPU作业掩盖正式训练利用率。
远端main=a52dfba4486af8d263d5cd0a976c3102482ff249，baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。
此文发布前再次核对远端；push认证状态单列，不将本地commit称为GitHub已同步。

新增正式训练60秒窗口（60样本）：GPU0–3平均利用率5.63/5.73/6.15/2.58%，无新辅助GPU任务，
包含正常周期尾部。见同审计目录GPU_60S.json；50%要求仍未满足。
