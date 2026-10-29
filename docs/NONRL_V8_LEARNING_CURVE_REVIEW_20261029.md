# 当前 v8 学习曲线与闭环失败的区分

主矩阵尚未修复，Goal active。本轮只核验当前锁定模型的既有学习曲线，不重新拟合或选模。
原108评测继续，2026-10-29 04:42:51 UTC两原服务仍active；随后读取execution为67/108，
条件007的RNN seed2在途。完整审计、八球覆盖对照、正式补采及公平重训仍待完成。

## 当前证据

图来自 `outputs/special_scene_postprocess_20261029_v8/LEARNING_CURVES`，
原绘图收据时间为2026-10-28 23:49:26.806737 UTC。核对九个锁定checkpoint和metadata、
六份实际训练history、数据/登记/model-lock和绘图源码hash；逐点对应原曲线。
两张PNG已经目视检查，未重画、平滑或删除尖峰。六条神经训练均32000 updates，
采用终态checkpoint；六条validation episode是选模集，不是未见测试。
ESN使用解析ridge，没有梯度优化loss曲线。

| 方法/seed末位 | 最终全train动作MSE | 终态validation动作MSE | 最后五个全train记录的相对极差 |
|---|---:|---:|---:|
| RNN1 | 7.254753e-6 | 1.120709e-5 | 2.0544% |
| RNN2 | 6.754794e-6 | 1.095225e-5 | 5.8715% |
| RNN3 | 7.273224e-6 | 1.060905e-5 | 1.9943% |
| MLP1 | 8.982488e-5 | 8.923892e-5 | 1.5990% |
| MLP2 | 8.625908e-5 | 8.189934e-5 | 1.7115% |
| MLP3 | 9.077318e-5 | 8.873214e-5 | 1.4654% |

ESN三个seed的validation MSE分别为3.082290e-5、2.613990e-5、2.585598e-5。
极差采用update≥28800的五个稀疏全train记录，除以其均值；只是描述，不是新增收敛门。
RNN/MLP曲线先下降、末段趋平，但实际冻结训练源码采用cosine学习率，终值为初值的1%，
不是零。实际progress确认RNN1/3末学习率3e-6，RNN2及三MLP为1e-5。
因此末段趋平不能独立证明充分优化、覆盖充分或闭环任务成功。

结合已完成的[读出外推诊断](NONRL_V8_READOUT_SUPPORT_DIAGNOSIS_20261029.md)和
[训练方向检查](NONRL_V8_TRAIN_DIRECTION_COVERAGE_20261029.md)，目前优先验证联合状态覆盖：
现有示范缺少±Y主导方向，ESN在历史成功teacher轨迹上存在严重读出外推；
RNN虽然模仿误差更低，仍有闭环失败。不能把此排名替代Task、Strict、BOTH条件SPT、
峰值力矩、舒适代理、机器合规，也不能据此认定唯一原因或改测试选模。

## 检查失败记录与归档

首次额外检查误用了终态history与导出validation MSE的精确浮点相等，exit1；
实际差异最大1.3552527156068805e-20。改为原绘图程序已有rel_tol=1e-12、abs_tol=0后通过，
原模型、历史、图均未改。首次失败源码及原因随独立检查源码、每模型实际差异一并保留。
正确检查服务自然exit0；实际affinity=[6]、memory.max128MiB、swap.max0，
写报告前memory.peak18579456bytes、memory.events全0。无拟合、预测或物理积分。

[核验JSON](evidence/NONRL_INTENT_RECOVERY_20261029/V8_LEARNING_CURVE_VISUAL_REVIEW.json)：
24835bytes，SHA256 `3dac2976755985b3666acbab3f841bbece0c1894fe1b5ca7ba3d9bef824c3d9b`。
四成员归档含该JSON、两张原PNG和原绘图收据，逐成员字节核对；暂存及最终大小/hash核验通过：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_learning_visual_review_20261029_v1/FIGURES_AND_REVIEW.tar.gz`

441333bytes，SHA256 `ae6e4e4f9025e8a46a616ba9ffe7c57ecbf533c4212b29e0a7720f9ff6d1c4dd`。
服务器仅归档。开工实际fetch/read main ac1735951a011a589f35bf141d703aab087d7245、
baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。

后续严格按[当前交接](NONRL_V8_RECLAIMED_SERVICE_HANDOFF_20261029.md)：原108及后处理完成后
查看完整结果并归档，再执行唯一已登记v6八球开发对照；全八review之后登记真实三场景新30，
资格和实际覆盖检查通过后公平训练三方法，再回归评测。原12条件已被诊断检查，不称未见测试。
未重启原服务，未改绑定源码、物理、输入、filter或gate；可选004审计未重试。
