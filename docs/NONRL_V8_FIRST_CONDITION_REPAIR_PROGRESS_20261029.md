# 非RL首条件九模型核验与后继补采检查

本轮增量代码及小证据已逐Git blob、暂存及最终大小/SHA核验共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_condition000_20261029_v1/DELTA_SOURCE_AND_EVIDENCE.tar.gz`。
科学commit `d05a66360c768530d963bce21a0f3a0d2432f993`，4文件/13179bytes，SHA
`6439c0f81de71fba055dcd652396b2cb75dceb9981fe1b2213b6740e4f39c1f8`。
见[收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION000_SHARED_RECEIPT.json)。
包内报告是该科学commit准确版本，不含本段后补说明/合并日志或在途108原轨迹。
这覆盖文末“待同步”快照；依赖源码仍由原完整源码包和Git提供。

**主矩阵尚未修复。** 原108继续，首条件九模型全部Task/Strict失败；本轮完成了该条件
保存证据的独立复核，并补齐真实场景覆盖探针的结果检查入口，没有重新训练或重启仿真。
承接[同教师历史诊断](NONRL_V8_MATCHED_HISTORY_AND_COVERAGE_20261029.md)。

## 已完成的原测试条件000

`sii-special-v8-condition000-audit-20261029.service`在23:36:43UTC正常结束，
核验9回合、8,486,400个保存子步。原源码/配置/checkpoint/MJB、actor及公共filter原重放收据、
子步RMSE/峰速/峰矩/穿透/接触时间/舒适代理/机器合规逐一通过。
这是保存证据及算术复核，不是独立动力学重新积分。

| 模型 | seed末位 | 最终阶段 | 时长(s) | Task/Strict | 峰矩(Nm) | 机器合规 |
|---|---:|---|---:|---|---:|---|
| ESN | 1 | lift，穿透中止 | 4.84 | false/false | 74.967 | false |
| RNN | 1 | approach | 55.00 | false/false | 43.304 | true |
| MLP | 1 | approach | 55.00 | false/false | 36.665 | true |
| ESN | 2 | carry | 55.00 | false/false | 61.172 | false |
| RNN | 2 | carry | 55.00 | false/false | 41.799 | true |
| MLP | 2 | carry | 55.00 | false/false | 52.350 | false |
| ESN | 3 | lift，穿透中止 | 34.48 | false/false | 45.560 | false |
| RNN | 3 | carry | 55.00 | false/false | 38.563 | true |
| MLP | 3 | carry | 55.00 | false/false | 39.465 | true |

三个seed为2026102801/02/03。阶段取各`AUDIT.json.stage`（独立审计的`failure_stage`）；
`rollout.json`没有顶层stage，因此旧审计额外字段`terminal_stage=null`不作为阶段依据。
所有失败仍计入Task/Strict、峰矩、机器合规分母。无BOTH成功回合，SPT为NA；
完整108前不产生全局T_ref或总排名。舒适指标仍是实际人体接触dt上的工程代理，
无接触回合为NA，不能以无接触/低力矩代替任务成功。

[完整审计](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION000_AUDIT.json)
SHA `5359a9af4afbeef87a2796d98d6a57e578ea07beebda8f7304cb70b31a617d00`。
ESN seed3的global穿透中止与外部/edge通道最大0.158459mm属不同通道；机器合规已经
将中止原因计为失败，不因局部通道低于0.2mm漏记该失败，也不修改原gate。

## 修复方向与本轮实现

这批变更包含三个真实特化采集场景及共同数据集的更换，并不只是旧模型的棍推动作微调。
已完成的30条teacher和18条学生开发诊断说明局部行为可实现，但不能保证原测试域覆盖。
此前同成功teacher历史比较已排除“所有误差都是学生先失败以后才产生”的解释：
ESN在teacher的lift/carry也存在大偏差；RNN/MLP首帧即有非教师残差。
训练方向范围窄是具体覆盖缺口，尚不是唯一因果结论。不得用测试轨迹拟合或重新选本批模型。

有效八球开发准备仍为`outputs/nonrl_ball_coverage_probe_20261029_v3`，REG SHA
`2f008162e1ddf774ae578e8f6e4e5e6961f6a5d6aadb510a5742b4bab03457a1`，没有启动。
新增`tools/review_ball_coverage_probe_20261029.py`检查全部八项，不只看参数：

- 绑定登记、teacher、真实执行环境、原资格/源码/轨迹hash、原actor/filter重放。
- 比对保存的canonical48路径方向：接近、带载搬运、返回三个阶段都必须实际到达；
  检查实际搬运目标差是否等于登记位移。缺阶段或方向不符明确记覆盖失败。
- 原任务/接触/安全资格全部保留，即使八项执行结束，也不把失败项算作有效补采。
  零估计载荷但非零上下文的帧数仅作描述，不能替代真实手接触标签。
- 拒绝未开始/不完整probe；结果不自动批准训练，也不替代棍推、厚桌角或最终108。

验证使用已保存的真实train ball00：750帧，接近/搬运/返回分别43/71/491帧，
原搬运位移[.085,.035,0]及三阶段方向均匹配，最大方向误差2.22e-16。
反向carry、缺少carry/return、错误目标位移均正确记失败；NaN拒绝。
实际尚未开始的v3被拒绝且未产生输出。全部v3绑定源码hash保持，新增物理步数0。
这只是reviewer验证，**真实八球正向结果尚不存在**。

## 接续入口

1. 继续原用户级`sii-special-frozen108-v8-20261029.service`，PID1172675/start32623702。
   23:40:56UTC仍active，10/108；第二条件ESN seed1已结束，RNN seed1推进到12.04s/approach。
   MemoryCurrent596717568bytes、Max3GiB、swap0、OOM计数0。第十回合尚未做本轮独立审计，
   不扩展上述9回合审计结论。不要重启或重复派发。
2. 完整108后运行原`audit_special_frozen108_20261028.py`，输出必须是
   `outputs/special_scene_frozen108_20261029_v8/FROZEN108_AUDIT.json`；完成报告/归档。
3. 确认原服务inactive后，按原资源限制执行有效v3的`--run`。结束后调用本轮新reviewer：
   `--root outputs/nonrl_ball_coverage_probe_20261029_v3 --output outputs/nonrl_ball_coverage_probe_20261029_v3/REVIEW.json`。
4. 根据全部实际结果修订三场景共同采集与验证覆盖，再公平重训三家，最后重评原矩阵。
   原12条件已被检查，属于回归条件，不能重新称未见测试集。Goal保持active。

开工实际fetch/read main `80efd331debd8fb4c2320cf04f5d7f86361b0524`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。收尾远端main新增9e4d6c57，已读另一任务的
RL71/72进度；仅保留其文档/证据更新，不操作RL。无子agent、服务器计算、删除。
新代码/审计当前仅本机；共享核验完成后补充准确收据，原在途108原始轨迹不在本轮小证据包中。
