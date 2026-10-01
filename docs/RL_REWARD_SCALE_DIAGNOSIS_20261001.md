# RL 奖励尺度与抓取失败诊断（2026-10-01）

本审计是主结果之后的实现诊断，不是修复成功或因果消融声明。
主实验原始记录及frozen_main_01不变。读取main=ba84ed8、baseline=140f71a。

## 行为与交付判断

用户视频 /Users/hwy/Downloads/replay_threeview.mp4 为23s、1920×560。
实际核看0/4/10/16/22s画面，叠字Pure ESN ridge-v1 (development)、office-v5，
对应仿真约0.04/9.64/24.04/38.44/52.84s，能看到夹起、搬运及后续释放/撤离，task=True。
视频尚未绑定本轮固定ESN checkpoint，不能混用两者数值。
当前RL在最终测试没有可靠抓取，不符合用户要求的可用论文baseline；
修改success名称不能补救行为失败。负结果可记录，但不能替代充分训练的证据。

## 奖励尺度缺陷

两组共享terminal_task(+20/-20)、势函数差分和时间成本。
metric额外加入平方跟踪误差、归一化峰矩增量、请求动作差分成本。
峰值末端速度只报告，未被直接作为峰速目标优化。

提前失败补偿还随reward改变。metric按剩余时间始终达到3m误差上界计算：
4*(3/.12)^2=2500。它是保守支持上界，不是真实反事实成本。
“提前失败不能逃避未来负成本”的测试通过，不代表该尺度适合有限预算学习。

排除warmup与跨5000步回合，metric30次提前失败的补偿范围-177.73至-1809.77；
三个seed各自中位数-1787.20、-1730.34、-1262.50。
office18次补偿范围-0.715至-0.054。完整metric回合误差成本也可达-403.29。

| seed | office_task最终normalizer分母 | metric最终normalizer分母 |
|---|---:|---:|
|61001|5.6175|366.0475|
|61002|4.9274|365.8561|
|61003|5.6073|363.8715|

官方normalizer使用max(return标准差,历史绝对return峰值/5)，极端惩罚会持续影响尺度。
相同+20在以上最终尺度下约为3.56–4.06 versus0.0546–0.0550。
这是观测到的数值失衡，不证明唯一因果；SAC温度也会自适应，不能仅凭分母断言固定熵支配。

## 动作与抓取阶段

audit_reward_scale.py实际扫描六路全部control_audit，比较step0–4999与95000–99999。
warmup两个奖励配对seed动作与阶段计数一致，动作确实送入公共执行接口。

| 组/seed | warmup请求动作分量RMS | 末5k请求动作分量RMS | 末5k过滤后平移残差RMS m/s |
|---|---:|---:|---:|
|office/61001|.02011|.38202|.12673|
|office/61002|.01995|.64000|.26924|
|office/61003|.02004|.52636|.20480|
|metric/61001|.02011|.52217|.22129|
|metric/61002|.01995|.62913|.26627|
|metric/61003|.02004|.46006|.11813|

这是训练随机策略动作，不是确定性测试的实际末端速度。warmup平移残差约.0111m/s，
曾访问lift/carry/release/retreat；训练后任务组部分回合也到过grasp后阶段，
但最终测试策略未保留稳定抓取。metric学习后226个结束回合均approach/align。
阶段覆盖本身不是实际夹持成功证据。

公共PickPlaceTask要求位置误差<12mm、姿态误差<.12rad、实际速度<.025m/s连续.2s，
才会切换阶段；stage<2时夹爪保持打开，grasp阶段才命令闭合。
请求残差RMS不能与实际速度阈值直接等同，但表明学习后的大幅扰动。
需要进一步用确定性轨迹ready日志检验原因，不能放宽gate或强制闭爪冒充算法改进。

## 修复准入与接续

1. 优先校正新增指标成本/提前失败补偿相对于任务的尺度，保留全部旧失败记录。
   若采用有界训练成本，必须明确与未经裁剪的真实RMSE/峰矩/峰速不同。
2. 同轨迹验证metric等于task加声明成本；验证极端提前失败、折扣和有限时长；
   不允许旧replay/normalizer被悄悄改reward后续训。
3. 先验证确定性策略能够接近、停稳、实际夹起并搬运，再讨论接触后的柔顺指标。
   rc0、阶段覆盖和较低RMSE均不能替代此门槛。
4. 新训练只在独立冻结版本进行，明确是观察主结果后的开发实验。
   不改环境、物理gate、actor输入、执行器或旧实验。
5. 运行中的entropy_diagnostic_02只改熵，没有修复上述reward缺陷，结果须单列。

证据JSON：
/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/REWARD_SCALE_AUDIT.json
审计源码：
/home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/audit_reward_scale.py

当前没有修复后学习效果结论，不能称已经获得可靠RL baseline。
