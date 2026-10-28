# v7完整采集与球撞末段稳定性修复

20:31UTC：v8原采集1088910与接续1089228持续active，4/30合格、rod04在途，学习waiting。
先完成三条全部资格输入hash及194个学习绑定源码核验，均一致；没有重复启动。
科学10cebe07与安全合并b5e5fed5已push/远端核验，双方日志新增及共同历史逐字保留。
源码/小证据1178文件6675768bytes/SHAf8a71776已核共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_start_source_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`。
[源码共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_START_SOURCE_SHARED_RECEIPT.json)。
不包含在途v8原始物理/学生；Goal active，全30资格和最终学生主矩阵仍待。

## 20:28 UTC：七项完整通过，v8重采及公平学习接续已启动

完整七项原始物理754文件/688650240bytes已逐成员核验，并在共享暂存和最终目录复核SHA256：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_vertical_damping_controls_20261029_v1/FULL_PROBE.tar`，
SHA `8d32960b10a210afdd35d47030ff41f75dccb8b92f47cbbe31a3435a53c792d2`。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/VERTICAL_DAMPING_SHARED_RECEIPT.json)。
包含完整七项/运行源，不包含在途v8/学生或后来准备代码；旧失败与本地副本未删除。

原七项于20:23:13.547771 UTC自然结束，完整review确认六训练场景全部合格、
office000完整55秒Task/Strict同时通过，末阶段retreat，动作/filter回放误差0。
office RMSE32.732345mm、峰矩44.833782Nm、峰末端速度.363191m/s、外穿透.161989mm。
四球训练尾段速度平方和.06049083598→.01466854611（下降75.7508%），
ball00的RMS仍由.004457升到.006736，保留此退化，不宣称全面更优。
棍00接触4.7444、让位4.84、蹭过7.72、持续回位8.16秒，早于12.80秒撤棍。
[完整七项审查](evidence/NONRL_INTENT_RECOVERY_20261029/VERTICAL_DAMPING_COMPLETE_REVIEW.json)、
[综合回归审计](evidence/NONRL_INTENT_RECOVERY_20261029/VERTICAL_DAMPING_OFFICE_AUDIT.json)。

确认原服务inactive且无模拟器后，登记同一原30条件、seed及24train/6validation的新v8。
`outputs/special_scene_vmc_collection_20261029_v8`，PLAN SHA
`2ed3e2b9d407db4bb8186adbdc7a72d25deafdf3eb873453de62f9d059a4d252`；
唯一`sii-special-collection-v8-20261029.service` parent1088910/start31713076，
20:24:33.257379 UTC启动。20:27已rod00合格、rod01在途，非全30结论。
单模拟器/线程1/CPU100%/3GiB/swap0，物理/MJB/filter/canonical48/执行器/原gate未改。
实际新采集源hash含recollect工具，运行期间不得修改该绑定源。

唯一接续`sii-special-learning-handoff-v8-20261029.service` parent1089228，
20:25:01.506539 UTC启动，REG SHA
`f7086a3fa174579f21bba34ff062b2220a5b1dd0b08fe906ae834b52307d1159`。
全30独立资格通过后才构建`outputs/special_scene_retrain_20261029_v8`，
共同数据/划分、三seed、每家每seed12候选、统一验证requested-action MSE选择规则；
ESN固定储备池+解析ridge，普通RNN/MLP每候选32000更新，共75训练作业/9最终模型。
当前仍等待采集，无新学生结果。v7失败原收据保留，不重启旧服务或复用旧准备。

新18诊断准备`outputs/special_scene_student_closure_20261029_v8` SHA77fedd0e，
新108准备`outputs/special_scene_frozen108_preparation_20261029_v8` SHA173e2abf。
全部重新绑定v8，18/108均未启动。先完成模型审计/真实场景18与失败诊断再派发108，
不按闭环结果重新挑选验证模型、不把office轨迹加入拟合。原12为已检查回归，非unseen。
六指标保持Task、Strict、双成功条件SPT、全回合峰矩均值、接触dt舒适代理、机器合规率。

本次续接实际fetch/read main0a882833、baselinef6e8f8c；独立RL更新与本任务无科学冲突，
不操作RL/服务器计算/子agent。Goal active；教师有限对照修复不等于ESN或主矩阵修复。

以下是保留的早期快照，运行状态以上述完整结果为准。

20:19:55 UTC更新：原唯一七项服务1080783保持live，六训练场景全部合格，office55秒回归
运行至25.04秒carry，完整结果待，OOM0。四球训练尾段速度平方和.060490836→.014668546
（−75.75%），但ball00 RMS .004457→.006736退化仍保留；其余01/04/06均下降。
新`recollect_vertical_damping_teacher_20261029.py`仅准备：必须真实完整七项review有资格且
原服务inactive，才登记原30/同split/同gate的v8；实际当前缺review被拒绝且无v8目录。
未启动v8/学生/108，不以六项替代全部七项。

科学提交0f3e2c45已push并核验。完整v7物理归档现已核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v7_full_collection_20261029_v1/FULL_COLLECTION.tar`，
2798858240bytes/SHAfa6eb5b9，包含全部30及ball08失败，覆盖下文上传中旧快照。
同提交源码/小证据1170文件5967224bytes/SHA65673c16及另存报告SHA408786d0已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v7_tail_source_20261029_v1/`。
[完整共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V7_FULL_AND_TAIL_SHARED_RECEIPT.json)。
源码包不含后来recollect准备/本段后补或在途新七项物理；新教师结果仍以完整review为准。

本轮Goal继续，前轮完整棍推审计/发布属于progress。本轮实际查询、fetch并读取main
`2b41371d01cc1b766b6cfccade9311d1f966551a`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。无RL操作、子agent或服务器计算。

## 全30完成，29合格、1失败，未训练学生

原collector1056282/start31377244于2026-10-28 20:04:10.559689 UTC自然结束；
原服务inactive/success。全30真实三场景按原条件、seed、24train+6validation采集完毕：

| 场景 | 合格 | 失败 |
|---|---:|---|
| 带挡板棍推 | 10/10 | 无；全部撤棍前让位—蹭过—持续回位已审 |
| 自由球撞 | 9/10 | validation ball08，原末段速度门失败 |
| 厚桌角 | 10/10 | 无 |

原handoff1056692于20:04:11.913853 UTC以`failed_preserved`退出：
`Original30 incomplete or contains nonqualified demonstrations`，service failed/exit-code，MainPID0。
这是数据资格保护实际生效，不是OOM；不存在`outputs/special_scene_retrain_20261029_v7`，
没有构建该批数据集、拟合或新主矩阵。不重启原采集/接续，不复用v7绑定的18/108准备运行后继数据。
[全30审查](evidence/NONRL_INTENT_RECOVERY_20261029/V7_FULL_COLLECTION_REVIEW.json)、
[接续失败原收据](evidence/NONRL_INTENT_RECOVERY_20261029/V7_FITTING_BLOCKED.json)。

原进程有界观察19:56:26–20:04:26共17次，确认同PID/start真实推进17→30，
最后service inactive而原PID消失；观察自然结束，没有把超时或沙箱可见性当死亡。

## 失败原门复算与训练集同类波动

ball08完整30秒，接触、安全、动作/filter回放均通过；lift=.149360880m，
末9个速度差分最大值`.031113961858026614 m/s`超过原`.02 m/s`，因此grasp_lift/task为false。
不是穿透/执行器违规，也没有把到达stage5当成功。十条ball的原末段lift、motion、
末10位置误差、物理/上游接触/阶段判据逐项复算与原标签完全一致。
独立标量实现再次复算全部10条速度/误差和8条train的尾段RMS，最大速度误差1.74e−18。

只用8条train的最后250速度样本RMS排名：ball04、06、01、00、02、03、07、05。
前三条末10秒RMS分别`.0092294482/.0085790311/.0079571153 m/s`，峰值
`.0373699389/.0307916141/.0245215365 m/s`；最后短窗口都过原门，但不能称整个尾段稳定。
这些训练条件提供控制器修复依据；validation只复算原资格，不用于排名/拟合或参数搜索。

全部8train原actor逐帧精确回放。ball04末段基础/恢复/总z动作标准差分别
`.0123691974/.0158746991/.0189878925`，两种分量都有变化；共变不证明某一项导致振荡。
实际图已目视检查，所有8条训练曲线与训练RMS最高的ball04动作分量均来自本轮保存数据，
无平滑、无假想动力学。`.02`虚线是原末窗口门，不是新全尾段资格门。

![v7训练球撞末段](evidence/NONRL_INTENT_RECOVERY_20261029/v7_training_ball_tail.png)

[球组审查](evidence/NONRL_INTENT_RECOVERY_20261029/V7_BALL_TAIL_REVIEW.json)、
[实际训练数组](evidence/NONRL_INTENT_RECOVERY_20261029/v7_training_ball_tail.npz)。

## 已启动：唯一七回合垂向阻尼对照

`outputs/special_teacher_vertical_damping_20261029_v1`，工具
`tools/teacher_vertical_damping_control_20261029.py`。只将虚拟z阻尼110→220 Ns/m；
保留x/y/旋转阻尼、刚度/质量、原读出、恢复偏移.03456819977m、intent=.003、公共filter、
canonical48、物理/MJB、执行器和dt5e−5。没有新增恢复机制或场景特判。
较大虚拟阻尼是待检验的训练尾段稳定性假设，不承诺实际速度减半或全闭环稳定。

七项固定为rod00、ball00、ball04、ball06、ball01、corner00、已检查office000。
ball04/06/01由全部8train RMS排名选，ball00和两其他场景保护既有行为；office只是开发回归，
从不进入模仿数据。只有六训练场景原资格和office Task/Strict均通过，且四球训练尾段
速度平方和总量低于原v7对照，才有候选资格。各条件退化也必须报告；不是新最终gate。
没有自动新30/拟合。只有实际完整结果审查后才决定下一步。

独立8000虚拟子步复算最大误差0；两组局部离散谱半径均小于1，静态动作差1.48e−17。
只排除孤立积分/静态映射改变，不证明耦合稳定。
[登记](evidence/NONRL_INTENT_RECOVERY_20261029/VERTICAL_DAMPING_REGISTRATION.json)、
[数值检查](evidence/NONRL_INTENT_RECOVERY_20261029/VERTICAL_DAMPING_ACTOR_CHECKS.json)。

启动前修正模板继承的祖先review/execution hash，明确绑定实际offset父；
源和登记重新hash核验，科学配置/7cases不变，尚无execution时完成。
[修正记录](evidence/NONRL_INTENT_RECOVERY_20261029/VERTICAL_DAMPING_PRELAUNCH_METADATA.json)。
实际REG SHA256 `01d9abbf5f721ce040640edeca6a930fd782b6ac0b19fea7c6895b294344b028`。

唯一service `sii-special-teacher-vertical-damping-v1-20261029.service`，parent1080783/start31622555，
20:09:28.516732 UTC启动，单线程/单模拟器/CPUQuota100%/3GiB/swap0，20:10原进程active，
rod00在途、OOM计数0。不要修改绑定源或再派发同任务。完整后运行原工具`--review`，
不是复用固定六项的旧reviewer。七项通过也不意味着学生/主矩阵完成。

## 学生审查入口与后续

新增`review_repaired_student_closures_20261029.py`读取完整18条的实际来源、配对teacher、
选模锁定/fit audit、物理/场景/seed/filter及源码hash，保留失败；精确重放学生自身动作和教师实际动作，
分开统计学生在teacher历史上的模仿误差、2秒窗口/恢复激活描述分组，以及teacher在学生历史上的反事实误差。
反事实不作为实际物理效果或新训练标签，validation诊断不重选checkpoint。

helper在实际v7 rod00教师及历史ESN/RNN/MLP各500帧学生轨迹上精确复现；独立简易算术/空集NA检查通过。
真实未开始的v7 18入口被拒绝且无REVIEW输出。**完整18正向审查尚未发生**；
历史helper验证不冒充新学生结果。本工具只准备，后继必须重新绑定采集/训练和18计划。

全30旧物理包已本机逐605文件/hash核验：2798858240bytes，SHA256
`fa6eb5b9e3a90f19388c02df0c6b910bc56678a7f73b520665f41d74652c2631`，
包含唯一失败、所有原始子步/轨迹/source/资格。共享上传中，最终核验前不宣称已归档。
新七项仍在本机；不得把当前teacher进度写成ESN、9模型、18或108完成。
