# 新三场景模型退化：接口修复与教师／学生／场景对照

2026-10-28，Goal active。用户明确要求定位并修复 ESN 的异常退化，而非接受全失败作为主结果。
本页覆盖此前“原108继续等待”的交接指令。旧结果全部保留，不能把未完成矩阵或低力矩当作算法结论。

## 14:29 UTC 更新：完成隔离对照，v6修复采集已启动

十回合诊断已完整结束并逐输入hash核对，见
[完整对照及离线误差](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/COMPLETE_CONTROL_REVIEW.json)。
同一冻结条件000、MJB、命令和gate下：新teacher（velocity_weight=.5，pair_average=true）
55秒仍停在carry，Task/Strict false；历史teacher（1.0、false）55秒到retreat，Task/Strict true，
放置XY误差5.417mm。两者actor/filter replay均0。新teacher RMSE29.283mm比历史38.917mm更低，
却未完成任务，说明不能用更低RMSE或峰矩替代成功。这只证明这个配对条件上的teacher配置退化，
不能扩展为全部12条件的因果结论。

在三个真实训练身份、同0.32动作尺度下：

| 控制器 | 厚桌角00 | 棍推00 | 球撞00 |
| --- | --- | --- | --- |
| 新teacher .5/true | 合格 | 合格 | 合格 |
| 已冻结ESN seed1 | 抓取/放置失败 | 合格 | 合格 |
| 已冻结RNN seed1 | 本轮未测 | 合格 | 本轮未测 |
| 已冻结MLP seed1 | 本轮未测 | 合格 | 本轮未测 |

这里的“合格”是原真实采集任务、保存物理子步审计及接触行为合格，**不是**冻结office测试Strict。
ESN棍推7.92秒越过、9.36秒确认回位，撤棍12.8秒，原行为判据未放宽。
ESN桌角在原0.16采集轨迹上的动作MSE为1.1227906e-6，在修正0.32后的teacher轨迹上为
1.9787818e-3；而棍推/球撞新旧teacher历史的动作误差完全相同（6.7991344e-7、1.4651303e-6）。
这支持桌角接口变化造成分布偏移的判断，不是只凭验证loss断言学好；对学生历史的teacher反事实预测
也存入review，仅作诊断，未执行这些动作、未把它们当作训练数据。

随后完成预登记的另外9回合，补齐velocity_weight∈{.5,1.0}×pair_average∈{false,true}因素对照：

| 速度权重/输入平均 | 棍推00 | 球撞00 | 厚桌角00 |
| --- | --- | --- | --- |
| 1.0 / false（历史） | 合格 | 失败：末态物块运动条件未满足 | 合格 |
| .5 / false | 合格 | 合格 | 合格 |
| 1.0 / true | 合格 | 合格 | 合格 |
| .5 / true（前十回合参考） | 合格 | 合格 | 合格 |

[登记](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/TEACHER_FACTORS_REGISTRATION.json)、
[全部完成收据](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/TEACHER_FACTORS_COMPLETE.json)。
原parent896071已自然退出；原10/新9全部保留，无OOM、无重复模拟器。
完整历史teacher在球撞失败，因此没有整套盲目回退。按恢复历史组件且三场景均合格的开发优先级
1/false→1/true→.5/false→.5/true，选择**1.0/true**：恢复历史速度权重，保留输入平滑。
该选择依据三个真实训练身份；当前12条件已经看过，之后只能称回归比较，不能称unseen。
只有一个身份/场景的对照，不能宣称新30或整个主矩阵已修复。

修复采集v6已于14:29:05 UTC启动，服务`sii-special-collection-v6-20261028.service`，
parent903064；本机单模拟器、单线程、3GiB/swap0。缓存
`code/mujoco_6d_vmc_benchmark/outputs/special_scene_vmc_collection_20261028_v6`。
[计划](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/V6_COLLECTION_PLAN.json)
SHA256 `d20543be6c9d6fb35b9c4cc094269bd7da1a1c7ae6ec68292b22d1100a1ad4ac`。
原30个物理条件、seed、24train/6validation划分逐字段保持；三个场景全部重新执行，统一0.32m/s。
采集器新增开工/回合边界source hash检查，实际正确计划接受、注入错误hash拒绝、未完成因素对照拒绝通过。
首条已实测推进到15物理秒/300000子步，不以该中间值冒充完整成功。**不得改v6登记绑定源码或重复启动。**

14:42:08 UTC追加实测：原parent903064/start29580292保持，已完成7/30，rod00–06全部合格、
各20秒/400000物理子步；回位确认7.72–9.72秒，均早于各自12.8–13.0秒撤棍。
正运行rod07，当前已完成资格收据输入hash和绑定源码再核对通过。
[在途进度收据](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/V6_LIVE_RECEIPT.json)。
这7条是teacher示范，不是重训后的ESN或最终测试结果。

旧35失败及前10诊断的完整原始物理、checkpoint、源码、收据共1758文件已打包并逐成员比对，
5923307520字节，SHA256 `6d8a464d96ef8e6e7bd744d3970ec822624fecb06c124b710f862be5d54e6598`。
服务器暂存及最终目录的大小/SHA256均已核验，完整共享路径：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_special_regression_full_20261028_v1/FULL_REGRESSION.tar`。
[共享收据](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/FULL_ARCHIVE_SHARED_RECEIPT.json)。
此完整包不含后9因素对照或在途v6。

后9因素对照（包括球撞失败）的完整物理、源快照、审计，及修复工具/报告/含v6计划的小证据，
另包842936320字节，SHA256 `e1f4a361f12ed6541fed67bffe782130f5fc934d138287e36bfcfc9b2651bffd`，
本机tar逐内容比较和远端暂存/最终核验通过：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_special_teacher_factors_20261028_v1/special_teacher_factors_and_repair_20261028_v1.tar`。
[收据](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/TEACHER_FACTORS_SHARED_RECEIPT.json)。
该包早于随后v6在途收据及报告追加，不含在途v6物理。两包不删除本机或历史产物。

后续先审全部30示范；若任一失败，保留并修复，不删失败条件或直接拟合。
再以新数据按同划分/预算/验证规则/三seed训练ESN ridge、普通RNN、MLP，先检查三个真实场景的
学生闭环是否重现teacher行为，尤其桌角抓取/放置，再重跑完整冻结108和六指标。
teacher配置修正尚未在原office000重新验证，也不能保证覆盖问题消失；仍需完整检验。
Goal active，旧35失败和v5模型均为故障/历史结果，新主矩阵尚未完成。

## 已确认的问题与尚未确认的原因

30条新示范的15750帧标签逐数组核对，均精确等于实际提交给过滤器的教师请求动作，
不是重复过滤后的物理速度；dataset/150个lineage文件hash及30个filter文件核对通过。
但三个场景的实际动作尺度不统一：20条棍推/球撞为0.32m/s，10条厚桌角为0.16m/s。
已完成34条测试的完整filter配置均与棍推的0.32m/s配置相同；桌角唯一配置差异就是该线速度尺度。
最初“全部配置相同”的断言失败与完整差异清单都保留在
[动作契约诊断](evidence/NONRL_SPECIAL_FROZEN108_PREP_20261028/ACTION_CONTRACT_DIAGNOSIS.json)。

来源：`scripts/render_compliance_audited.py`创建桌角环境时没有显式传入线速度尺度，
继承`VelocityResidualSafetyConfig`的0.16默认值。共同filter源码相同并不代表参数相同；
此前只检查AST/hash和各自回放，未充分检查跨场景配置一致性，这项核验已补上。
同样的归一化请求在桌角转换出的目标线速度仅为测试的一半。这是确定的接口不一致，
但尚不能证明它单独导致整个测试矩阵退化，不能据此承诺改一个数字就全部成功。

此外，本次并非只修改棍推动作：训练数据已整体换成三个短特化场景，教师readout也经过开发调整。
先前已发现训练路径方向Y仅覆盖[-.38075,.38075]，当前测试可到-.99028；
这是已观测的覆盖差异，不是闭环失败因果证明。需要用教师直控、同场景学生闭环对照分离原因。

## 已实施的代码修正

- 真实场景wrapper在第一步物理执行前统一到当前测试的0.32m/s线速度尺度、0.6rad/s角速度尺度；
  使用dataclass replace并同步同一个filter配置，保留其他限制、物理模型、gate和任务时长。
- 新采集计划须显式登记动作契约。数据集构建拒绝缺失契约、非教师动作、非0.32m/s数据，
  防止旧混合尺度数据再次悄悄进入新主结果。旧数据文件不改写。
- 增加纯学生诊断入口：同一canonical48观测、同一场景/过滤器/时钟，真实保存checkpoint并独立重放。
  学生诊断不能登记为教师采集，也不能混入教师数据集。

已检查四文件语法、冻结dataclass替换、实际动作转换到0.32、三类真实checkpoint适配器输出。
真实调用新dataset builder读取旧v5计划会拒绝且不创建输出。完整修复物理效果尚待对照，未宣称通过。

## 原评测在安全边界停止，完整保留

原`special_scene_frozen108_readout05_20261028_v1`使用已存在的`STOP_REQUESTED`协议，
在第35回合及其指标后处理结束后自然停止，`execution.status=stopped_at_episode_boundary`，
35条results、无在途条目；原772606/791378进程均退出。没有kill worker或改冻结模型/条件。
上层handoff检测“不足108”而自然记录`failed_preserved`，不是OOM/意外崩溃，也不是完整比较。
原35回合原始数据仍在本机，之前完整训练/采集已归档；这35回合的全部物理归档仍待。
[安全边界与新服务实测](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/REPAIR_BOUNDARY_RECEIPT.json)
也保留原观察器21个样本：33→35，最后原进程消失且明确停止状态。

## 已登记并实际运行的十回合对照

本机benchmark缓存：`code/mujoco_6d_vmc_benchmark/outputs/special_scene_regression_controls_20261028_v2`。
服务`sii-special-regression-controls-v2-20261028.service`，parent883961/start29348650；
首个worker883963/start29348654，13:51:51 UTC已13.04物理秒、carry，3GiB/swap0/OOM0。
[完整登记](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/DIAGNOSTIC_REGISTRATION.json)
SHA256 `73e8b6b6e95476398869c4e5192ca5f79a82e763a25fa54d67e4f73b195d6184`。

1. 新教师、历史教师分别直接控制同一当前测试条件000，冻结原MJB/gate/dt5e-5。
2. 各在corner00、rod00、ball00训练身份上运行新教师和现有ESN seed2026102801，
   所有场景同0.32m/s，共六回合；条件/seed/MJB与原采集一致。
3. RNN、MLP同一seed各在rod00运行一回合，避免只检查ESN。

这是十回合有限诊断，不是调参搜索、最终矩阵或新的独立测试。旧测试已看过，
不能再叫unseen；不把测试轨迹作为训练示范。所有任务失败照常保存，只有基础设施异常才停止本诊断队列。
最初v1缺少`MUJOCO_MENAGERIE_PATH`，在物理开始前FileNotFoundError退出，原失败目录/日志保留；
补齐原评测环境变量后独立登记v2，未覆盖或重试原目录。

## 后续必须完成

第一项实际对照已完成：新教师在当前条件000跑满55秒，Task/Strict均false，终态carry，
无abort；RMSE29.283021mm，峰矩38.164642Nm，最大外部/edge穿透.140178/.081284mm。
原actor/filter重放误差0。[原完整审计收据](evidence/NONRL_SPECIAL_REGRESSION_REPAIR_20261028/NEW_TEACHER_OFFICE_CONTROL_AUDIT.json)
SHA256 `34ce849b929782b6b4f56e0cd688ea042db13f1c63efb5858cd1f0d4164fe18d`。
这证明至少该测试条件下新教师本身不能完成任务，不能只归因学生没学好；
尚非完整对照或全部测试结论。历史教师对照13:56:43自然接续，原服务继续。

源码/原35停止状态/诊断登记/动作契约差异等13文件小包逐成员字节、远端暂存与最终hash核验，
76718字节，SHA256 `b7f13b26b6864bbe5d4e4f404c169a72f83e07020134cb6be2ef9ad5d179ed8e`：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_special_regression_repair_20261028_v1/nonrl_special_regression_repair_20261028_v1.tar.gz`。
包内报告为第一项对照完成之前版本；后追加的教师审计见Git，原物理全归档仍待。
本轮开工main d1b1bf89、收尾main80553b71/baselinef6e8f8c已实际fetch/read，独立RL更新fast-forward保留。

核对每个对照的真实完整回合和保存子步。若教师在当前测试失败，先隔离教师设计和任务迁移；
若教师通过但同场景学生失败，检查模仿误差、闭环分布和模型学习；若同场景均好而跨场景失败，
在三个真实场景内增加任务方向/阶段覆盖，不回到旧综合场景采动作。
修复后的数据重新登记，三类方法使用相同划分、预算和验证规则重训，再独立运行完整冻结108及六指标审计。
不得把本次35条失败或十回合诊断当成最终结果；保留旧数据、模型、失败及全部版本。
还需实际图表、contact补充、完整物理归档、更新主结果入口与逐项完成审查，之后才可完成Goal。
