# v7真实场景重采与公平学生评测接续

19:53:42 UTC：原采集15/30合格（10rod+5ball）、ball05在途，原接续waiting，两宿主PID保持。
科学提交797f46ea及安全合并/格式保留至a431b2d0已push并核远端；保留另一任务4c952453全部记录。
合并后双方新增与共同历史逐字核对通过，原始diff证据未改。
源码/小证据1158文件5201198bytes/SHA256 `3e2acc4adf0c91c4d269fa9183e1858b9c8a109d92560b51ce40c94470f096f7`
已核验共享到`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v7_rod_source_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`。
同目录另存a431b2d0版本文，SHA256 `a388ac5b2f431b98a15f43e0fefd1cd4b7c3ae4f1da56f579abfc9a9418950d5`，不含本段后补。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V7_ROD_SHARED_RECEIPT.json)。新30原始物理仍在采集，尚未打包为全数据；Goal active。

19:51 UTC状态更新：原采集13/30合格（全部10rod及ball00–02），ball03在途，学习接续继续waiting。
独立重核已完成13条资格的全部输入hash、194个接续绑定源码以及下方完整棍组10行证据hash均一致；
原两服务同PID active、3GiB/swap0保持。没有重复派发或修改绑定源。
已查出的教师carry卡角问题在固定回归中解除，但学生的模仿误差与场景覆盖仍待新训练/闭环证据，
不能把教师成功提前写成ESN或主评估矩阵修复。

## 19:47 UTC：完整棍推10/10通过，原采集进入球撞

原collector1056282/start31377244与handoff1056692保持实际宿主进程活跃。沙箱内ps没有宿主PID可见性，
再用宿主systemd及ps确认二者仍live，不把命名空间不可见当作进程死亡，不重启。
前轮v7评测准备/覆盖审计属progress。本轮实际fetch/read main6820a1c6、baselinef6e8f8c。

全部10条棍推（8train/2validation）现已完整合格，采集自然进入ball00；训练接续继续waiting。
新增`review_complete_rod_collection_block_20261029.py`逐条复核全部资格输入hash、行为几何审计/source hash、
实际teacher/config、seed、环境参数与登记一致；独立复算撤棍时刻和手接触首时刻，
检查接触≤让位≤蹭过≤回位开始≤回位确认<撤棍，并要求原.08秒保持。
初次未齐10条时实际拒绝且无输出；全10完成后通过。
[完整审查](evidence/NONRL_INTENT_RECOVERY_20261029/V7_COMPLETE_ROD_BLOCK_REVIEW.json)。

| 身份 | 让位 s | 蹭过 s | 回位确认 s | 撤棍前余量 s |
|---|---:|---:|---:|---:|
| rod00 train | 4.84 | 7.80 | 8.88 | 3.92 |
| rod01 train | 5.12 | 10.36 | 10.44 | 2.56 |
| rod02 train | 5.00 | 7.60 | 7.92 | 5.03 |
| rod03 train | 4.92 | 7.60 | 7.68 | 5.17 |
| rod04 train | 4.84 | 7.64 | 7.72 | 5.08 |
| rod05 train | 5.08 | 7.56 | 8.04 | 4.96 |
| rod06 train | 4.92 | 7.64 | 8.28 | 4.62 |
| rod07 train | 5.00 | 7.60 | 7.80 | 5.10 |
| rod08 validation | 4.88 | 7.64 | 7.96 | 4.89 |
| rod09 validation | 5.04 | 7.56 | 7.84 | 5.11 |

这是保存的40ms几何审计、子步接触摘要及事件顺序的完整棍组证据；本轮没有重新积分动力学，
也不是全30、office Task/Strict或学生成功。validation仅核原固定判据，不用结果改教师/条件或选学生。
原8+2/新teacher及所有绑定源保持。球/角剩余20条、全24训练覆盖、所有学生与108仍待。
新增小证据待本轮Git发布，原始在途30仅本机；不重复归档棍组为“完整30”。

19:42:35UTC最新快照：原collector1056282与handoff1056692保持live，7/30已合格、rod07在途，
学习仍waiting；采集cgroup内存714416128bytes，接续8327168bytes。没有重复任务或源更改。

本轮科学提交`2187ab1ec7f82af232f9cec7519ca6e6562da35e`已push并核远端。
源码/小证据1155文件5189208bytes逐Git blob及共享暂存/最终hash核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v7_preparation_source_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`，
SHA256 `7045c32f6244b461926d039b9a58bb537e4f2c3e616c409bf7d368934fa5fd48`。
同目录另存该提交版本文，SHA256 `41dfc48d08e2ba6563efc3fbdc47260b50daf21e9419278cd0a733b3eb4aa7a9`，
不含本段后补记录。[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V7_PREPARATION_SHARED_RECEIPT.json)。
非完整仓库/环境/模型备份，不含在途新30或学生结果，无删除。

当前Goal active；前轮已完成教师修复/六项实际对照/原始物理归档及新30派发，属于实际progress。
本轮先核对远端main `9d13fbb923574e3104cbfd69001a88b843d72319`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，原collector与learning handoff仍同PID活跃。
教师修复的完整证据、源码与共享归档见[前序交接](NONRL_TEACHER_VELOCITY_UNITS_20261029.md)。
这里的18/108是新准备，不能误用20261028的v6绑定版本；没有启动任何新评测模拟器。

## 原采集继续：5/30合格，不是全体通过

原`sii-special-collection-v7-20261029.service` parent1056282/start31377244保持，
root`outputs/special_scene_vmc_collection_20261029_v7`、PLAN8e2fc770。19:37:50UTC已完成rod00–04，
均原资格合格，rod05在途；原接续`sii-special-learning-handoff-v7-20261029.service` parent1056692仍waiting。
MemoryMax3GiB/swap0保持，采集RSS对应cgroup约0.78GiB，只有一个模拟器。未重启或改绑定源。

逐条重核已完成前缀的全部qualification输入hash及棍审计，得到：

| 训练身份 | 首次手接触 s | 蹭过 s | 持续回位确认 s | 撤棍开始 s | 最大外穿透 mm |
|---|---:|---:|---:|---:|---:|
| rod00 | 4.73275 | 7.80 | 8.88 | 12.80 | .076057 |
| rod01 | 4.98045 | 10.36 | 10.44 | 13.00 | .033211 |
| rod02 | 4.89395 | 7.60 | 7.92 | 12.95 | .038979 |
| rod03 | 4.80865 | 7.60 | 7.68 | 12.85 | .040371 |
| rod04 | 4.74585 | 7.64 | 7.72 | 12.80 | .060478 |

五条全部原行为检查通过（含让位顺序），未据中间结果改参数。其余25条尚未完整，
任何失败保留且阻止全30数据构建/学生拟合。新30最终原始物理目前仅本机，待完整后单独归档。

## 新准备与真实拒绝检查

`outputs/special_scene_student_closure_20261029_v7/PREPARATION.json` SHA256
`3e7dd2b60b91550a5b9db2fd31ffc05b77743e43c741cc026b4df1d2221e7bc6`。
只使用未来冻结模型seed2026102801，三family各测每场景00训练身份及08验证身份，共18回合；
配对教师来源为实际v7新30。用于诊断拟合/闭环，不能利用结果重选验证模型或称未见测试。
全三seed仍进入108，18不是替代108。[登记](evidence/NONRL_INTENT_RECOVERY_20261029/V7_STUDENT18_PREPARATION.json)。

`outputs/special_scene_frozen108_preparation_20261029_v7/REGISTRATION.json` SHA256
`6650157c71bc7cb53ae9a03291700b42eb105d617cdfa3fc61afdd1d222c048c`。
绑定原12条件/原物理源码、v7训练/接续/18准备，目标`outputs/special_scene_frozen108_20261029_v7`。
静态MJB检查：原归档dt1e−4不改，只按冻结loader在内存设正式dt5e−5，formal SHA
`d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`一致，物理积分0。
实际调用冻结dispatcher提前入口被`Original fitting handoff incomplete`拒绝，未生成execution/评测目录。
[108准备](evidence/NONRL_INTENT_RECOVERY_20261029/V7_FROZEN108_PREPARATION.json)、
[检查收据](evidence/NONRL_INTENT_RECOVERY_20261029/V7_PREPARATION_CHECKS.json)。

全18回合必须完成并审查后才考虑108派发；目前不部署自动108等待器。
原脚本的完整18入口检查并不要求三种学生全部成功，后续需如实审查每家失败，不能挑掉失败或按测试选模型。
模型锁定、导出、fit audit及学生闭环尚未发生，准备检查不能替代它们。

## 训练状态覆盖审计（准备，完整数据待）

新工具`audit_special_training_recovery_coverage_20261029.py`要求真实30条qualified_complete，
逐条核plan/identity/config/资格输入hash后，只重放24条train的canonical观测和requested action。
每条从零状态重置，要求actor精确一致；保存恢复激活、指令/实际路径速度、z误差、反向估计力及
激活>.5的连续长度。6条validation只核来源和资格，不进入这些调参诊断。
.5仅描述性分组，不是新任务门或数据准入条件；边际曝光不证明联合覆盖/学习因果。
当前活跃采集入口已实际拒绝且未写输出；空/离散连续段算术检查通过。完整正向审计待全30结束，
不能把脚本准备称覆盖结论。

后续完整后调用：

```bash
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=scripts:tools \
 /home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python \
 tools/audit_special_training_recovery_coverage_20261029.py \
 --collection outputs/special_scene_vmc_collection_20261029_v7 \
 --output outputs/special_scene_training_coverage_20261029_v7
```

现有学习接续全30合格后才自动构建共同24+6数据/三seed各12候选的解析ridge ESN、普通RNN、MLP；
本审计没有修改其训练参数/数据/验证选择规则。若审计提示覆盖不足，结合实际模仿与学生闭环证据再决定，
不向数据中混入office标签，也不擅自中止稳定的原候选训练。

最终六指标仍为Task/Strict全分母、双满足成功条件SPT（完整108双成功最短时间作T_ref）、
全部回合峰值力矩均值、实际人体接触dt加权舒适代理、机器合规率；无成功/无接触记NA。
当前12已被反复检查，仅作回归，不声称未见泛化。无RL/子agent/服务器计算，Goal未完成。
