# 冻结ESN参数：迁移接口核对

用户明确要求不得通过改ESN参数消除新场景问题。本轮只读核对，checkpoint/储备池/读出/
归一化/输出增益/过滤参数全部保持原值，没有重训或新物理回合。

## 找到的迁移结构问题

上一轮 `transfer_original_esn_old_office_20261013.py` 为保留历史场景配置，显式设
`planned_hand_corner=False`，从而选用旧 `PickPlaceTask`，其carry参考直接指向阶段终点。
原ESN配套部署使用 `PlannedCornerTask`，把 `goals[stage]` 逐次更新为规划路点。
观测构造公式均为 `command.target_position_m - hand_position`，所以字段次序没有错，
但参考的空间尺度和推进机制不同。复用同一个48D接口并不等于完整保持部署接口契约。

已通过原TRAINING_COMPLETE中的数据hash核对真实20训练/5验证轨迹，非扩充后新数据：
`7bb2f7bad7555cc97ca9cc32d43040e91775ce05cdfd32d109a7afbeb1d7e0a0`。

| 来源 | y位置误差绝对最大值 | y特征达到clip上限比例 |
|---|---:|---:|
| 原teacher训练27,500帧 | 16.608 mm | 0% |
| 原teacher验证6,875帧 | 16.327 mm | 0% |
| 原ESN全部8条开发部署 | 各回合15.613–16.730 mm | 均0% |
| 本次旧场景棍推窗口11.48–16.68s | 窗口均值437.677 mm（此格为均值） | 100% |

ESN内部既有定义是 `clip(error/.08,-4,4)`，不是本轮添加。
原训练y特征绝对值最多0.208，本次持续+4，超过训练范围约19倍（特征截断后）；
原始位置误差则约26倍。不能把这个问题简单归因为“ESN见到新物体就失效”。
具体输出放大证据见同日振荡报告：13秒前后的负载×y位置误差项足以把线性读出推向正负饱和。

## 已检查一致的部分

- 同一checkpoint SHA `acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7`。
- 公共评估器、观测器、WBC、速度残差核心、环境执行核心源码hash与原配套评估一致。
  `current_student_policy` 文件仅增加另外两个contract的分发支持；原contract仍走同一ESN实现。
  保存该差异，不把不同文件hash宣称相同。原ESN实现的逐动作/状态重放已有审计。
- action_filter_config逐字段相同：线残差0.32m/s、角残差0.6rad/s、变化率1.2m/s²等均未变化。
- 两个MJB的前7关节名字/qpos/dof索引相同；前7关节damping/frictionloss/armature、
  执行器gain/bias/gear/ctrlrange/forcerange逐值相同，未发现对象自由度增加导致机器人索引错位。
- 同一25Hz控制、同一世界系线/角速度顺序、同一目标减实际误差定义。
  记录的neuron_time是动作前、video/time是动作后40ms；这影响画图对齐，不是额外控制延迟。

## 结论与公平修复边界

有明确的**参考生成层适配不一致**，上一轮把“相同模型＋相同48D接口”当作足够的迁移兼容检查并不充分。
应先保持ESN原参数，核对并恢复其配套的公共参考生成方式在旧几何中的实现。
不能只给actor把误差缩小、置零或偷偷改单位；也不能只为ESN添加独有滤波/恢复策略。
若后续做闭环对照，任务目标/障碍/扰动不变，共同参考定义要对所有方法一致，
且新旧参考实验必须单列，不能用修复后成绩替换原失败。

这尚不是“所有抽动都由迁移代码导致”的因果证明。保持原权重的公共参考对照尚未运行；
如果对齐后仍有振荡，就应保留为现有控制系统的局限，不能再为了这一条结果调ESN。

本轮已完成只读核查、数据范围统计、8条部署对照、源码/执行参数/关节映射核验；
未完成：公共参考修复与冻结权重闭环对照。原公平比较作业继续，不重启。
服务器仅存储：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_transfer_contract_20261013_v1/evidence/`。
归档发布状态以根UPDATE_LOG和父目录ARCHIVE_VERIFICATION.json为准，含脚本、报告、CONTRACT_AUDIT及adapter差异。

开工main `74fcd826741bc0b40bd0f031932f2e1880f26665`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。
使用sii-research-sync，全部分析本机1线程/1GiB/禁swap，原始物理数据未变。
