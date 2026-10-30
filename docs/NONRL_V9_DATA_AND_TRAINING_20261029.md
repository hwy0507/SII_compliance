# v9方向覆盖修复：30示范完整，公平训练已启动

Goal active，学生主矩阵尚未修复。原v8的Task1/108、Strict0/108结果保留，
本轮完成的是新数据资格/覆盖及实际训练启动，不是新的闭环成功结论。

## 完整采集与数据

原单模拟器于2026-10-29 08:20:36–08:56:14 UTC完成30/30，全部qualified；
棍推、球撞、厚桌角各10条，共12,600,000物理子步。原服务正常exit0，
InvocationID `173a263a95e345f8b6c84f313e017185`，未重新启动或修改208绑定源。

十条棍推都满足手接触→让位→越过→持续回位，回位确认在撤回前1.80–5.19秒。
20条未改变配置的棍/桌角轨迹与v8逐数组完全一致：8,250帧的time、qpos、qvel、ctrl、
mocap_pos、mocap_quat、canonical observation和requested action。该检查验证已保存轨迹，
不是重新积分动力学；新覆盖变化集中在球场景。
[完整检查](evidence/NONRL_INTENT_RECOVERY_20261029/V9_COMPLETED_COLLECTION_REVIEW.json)
SHA256 `4ec639a1ffbb57557ff8bee0ac962823bb0bc4ca1ecbcfb10416e78f233c0f4a`，含检查源码和每条来源。

共享数据15,750帧，24train/6val，分别12,600/3,150帧；各场景8train/2val。
不混入旧综合场景或开发八球轨迹。全部三方法用同一NPZ，SHA256
`120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407`。
训练只读原train分区；六条验证用于相同requested-action MSE选模。

## 实际覆盖变化

沿用原描述性口径：方向分量≥0.8；载荷量为canonical估计wrench按
[8,8,8,1,1,1]缩放后的最大绝对值。0.1是描述性分箱，不是新的物理接触或成功gate。
下表只含8条train球，验证轨迹未纳入分布统计。

| 方向 | v9帧数 | 估计载荷量>0.1帧数 | 估计载荷量≤1e-6帧数 |
|---|---:|---:|---:|
| -X | 1273 | 321 | 829 |
| +X | 1153 | 272 | 763 |
| -Y | 1343 | 205 | 962 |
| +Y | 1096 | 224 | 689 |
| -Z | 296 | 1 | 92 |
| +Z | 839 | 787 | 13 |

v8训练集没有Y主导方向帧；v9补上了两个Y方向在有/无估计载荷区间的示范。
真实物体搬运方向投影72.419–81.091mm、回程75.230–81.482mm，非仅目标指令变化。
这证明该已定位的覆盖空缺有所补充，不证明全部联合状态充分覆盖或学生闭环已修复。

- [train覆盖](evidence/NONRL_INTENT_RECOVERY_20261029/V9_TRAIN_DIRECTION_COVERAGE.json)，SHA `6b4cf5ce6cb4174a18c6961ee4e1f7d1d822dba97b3912d12a9ca1d1bd23f07a`。
- [真实球运动](evidence/NONRL_INTENT_RECOVERY_20261029/V9_TRAIN_BALL_ACTUAL_MOTION.json)，SHA `f8e0c38f1223afaf25bb917e02fcb72ff26cab0de5121553ef8485abe08f6422`。
- [数据身份和分区](evidence/NONRL_INTENT_RECOVERY_20261029/V9_DATA_COMPLETE.json)。

## 有限数据交接与当前训练

新增`tools/prepare_direction_dataset_handoff_20261029.py`，绑定原采集PID1452135、
start_ticks36009362、准确Invocation/boot和计划SHA。只有原retained unit exit0且30条全合格
才运行原builder、train-only覆盖检查和实际球运动描述；不拟合、不跑测试。
2个正常状态及12个错误/不完整状态的拒绝检查通过；真实交接也于08:56:31正常完成。
观察超时明确不等于采集停止；无自动重试、无模型或门槛调整。
登记SHA `76e0834cf30ebfb236edd9263ff465b6c24fa7b56ab1335e22d87db4b2cc67c7`。

08:57:38 UTC已启动`sii-special-direction-fit-v9-20261029.service`，
PID1469962，InvocationID `f22ab353765e49d3a0ddaf7a53ba8e32`。
本机CPU6/数值线程1/MemoryMax3GiB/禁swap；实查内存约1.20GB、OOM/oom_kill/swap0。
根目录`outputs/special_scene_direction_retrain_20261029_v9`。
拟合源码已独立冻结，base commit `69d656d67e60b66107f506400af0d36bc195b4d1`；
逐文件hash是执行来源，不能只凭base commit推断整个工作区干净。

保持原公平预算：ESN/RNN/MLP各3seed、每家每seed12候选，共108候选；
实现为3个ESN网格作业和72个神经候选作业，共75作业。
每个神经候选32,000更新；解析ridge ESN没有优化器更新曲线。
收尾已完成14/75个作业，当前`mlp_scratch_s2026102803_candidate01`推进至3620更新。
冻结拟合输入/源码及14个已完成checkpoint hash均复核一致；未完成全部选模。
训练/验证误差不用于提前宣称泛化或六指标改善，也不与不同旧数据集损失直接作优劣比较。

## 接续要求

先读取原服务、`execution.json`及当前候选`progress.json`，不重复启动或更改运行源。
全部75作业完整结束后，验证模型锁、同数据/曝光/选模、原冻结actor重放；
随后才登记并运行九模型×原12条件的108回归与完整六指标审计。
原12条件已检查过，不是新的未见确认测试。最终图表需实际查看，失败必须保留。
本轮没有新学生闭环结果，Goal保持active。

## 共享归档

30条原始数据604成员包已本地逐成员、源前后核验：2786887680bytes，
SHA256 `9a2f86e143e52ade5c9922877b3c813e9082a037f1a4bcfbd98f507e378e530c`。
暂存及最终共享副本大小/SHA均已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_direction_collection30_20261029_v9/FULL_COLLECTION.tar`。

共享数据及新交接来源另包保存，14成员6978157bytes，SHA256
`5c5221495a6efcde276adde2fb03ff92a40e6cc5d7304521f566ae5bbe26f6bd`，
逐成员/源前后及暂存/最终副本均核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_direction_collection30_20261029_v9/data/SHARED_DATA_AND_REVIEW.tar.gz`。
包含共享NPZ、数据身份/训练登记、终态数据交接/覆盖/实际运动、20场景一致性检查和新增交接源码；
不打包正在写入的拟合状态。两原LOCAL_RECEIPT保留创建时pending字样，不回改历史。

开工实际fetch/read main `69d656d67e60b66107f506400af0d36bc195b4d1`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。上一轮为progress，本轮完整采集、
真实覆盖验证、数据交接与训练启动同为progress。无RL/子agent/服务器计算、用户数据删除，
最终物理/gate/canonical48/filter/执行器与dt保持。
