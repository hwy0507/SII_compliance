# v8第二条件核验与补采接续检查修复

## 01:17 UTC：持续观察与核验共享

00:56:16.645–01:16:16.652UTC共41次确认原1172675/start32623702与后处理1201537/start32942337
同身份active，实际回合物理时间推进，完成25→30/108。最大原服务内存780238848bytes，
全部OOM/oom_kill/swap0。观察器30059自然exit0；第四条件ESN seed2在途，科学作业继续，不重启。
[完整记录](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FROZEN108_VERIFIED_WAIT_0056.json)，
59764bytes，SHA256 `49d32f3eb1a29da04dbd22e72447ab1bb0e20dcdaed6004f0cd76c2c0f1234ad`。

已核共享目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_condition002_direction_20261029_v1/`。
其中SCIENCE.tar.gz是科学79552a67071dedec0e0a5064e74aaf0b2fba8152的五文件包，22870bytes，
SHA256 `39b0ee7e6874137d8863a6556bb6a903f204cc5971a038013d6ce090884cad94`；
逐成员对Git blob/本机一致，另附上述完整观察JSON，两文件暂存和最终大小hash一致。
包不包含在途物理全集或本段补记。远端main01bb3503的另一任务更新已读并安全合并，
两份日志的双方新增和共同历史逐字节保持；有效八球v4的197个绑定源保持、仍未启动。
本轮为新增覆盖诊断及第三条件全审progress，Goal active；主矩阵未修复。

## 01:08 UTC：第三条件全审与训练方向缺口

原评测同身份继续至28/108，第四条件已开始；并非完成或修复。
第三条件`new30_prospective_20261026_acceptance_002`九模型的8,904,000个保存子步、
source/config/checkpoint hash和原actor/filter收据已复核；Task/Strict全部false。
ESN seed1在5.20秒lift发生global penetration abort，其余八条完整55秒。
ESN三seed外部/桌边最大穿透3.621621/.243724/.239524mm，MLP seed2 .526426mm，
这四条机器合规失败；其他五条按现行定义通过，不代表任务完成。MLP seed1无人体接触，舒适NA。
无BOTH回合，SPT仍NA；全矩阵汇总等待现有自动后处理。

[第三条件准确审计](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION002_AUDIT.json)
SHA256 `bbfc5fe7212e93b32a40c68c432917d864cad48835a8b21b3aff58ce7f274a27`。
只读审计日志确认01:07:32–01:07:38UTC完成，CPU4.791秒，无新增物理。
`terminal_stage`扩展字段是旧rollout缺失键而为null，实际阶段用已独立提取的`failure_stage`。

新增[训练方向覆盖报告](NONRL_V8_TRAIN_DIRECTION_COVERAGE_20261029.md)：24条train共12,600帧
均无±Y主导方向，棍推只含±Z参考方向。全部训练观测/动作与物理原件精确一致，六validation未统计，
无测试数据拟合。方向×载荷覆盖缺口为后继补采提供依据，不是修复通过或唯一因果证明。
原108/后处理不重启；有效八球仍v4、未启动。先完成原108审查归档，再推进真实三场景共同数据修复。

## 00:52 UTC续接观察

00:41:17.811–00:51:17.814UTC共21次原1172675/start32623702和后处理1201537/start32942337
同身份active，完成22→24/108，当前worker物理时间真实推进。最大原服务内存824283136bytes/3GiB，
OOM/oom_kill/swap均0。观察器81841自然exit0；00:52:28复核两科学服务仍active，没有重启。
第三条件seed2 ESN/RNN/MLP完整55秒runtime Task/Strict均false，ESN穿透0.243724mm、
MLP0.526426mm；失败保留。第三条件九模型尚未全审，seed3 ESN在途，不把前缀当最终结果。

[完整观察](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FROZEN108_VERIFIED_WAIT_0041.json)
30640bytes/SHA256 `1495a8648a645de777357d57f9adfc6b95269a18c884c4c35e0ad33566ae9ee2`，
已在暂存和最终位置核验大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0041_20261029_v1/V8_FROZEN108_VERIFIED_WAIT_0041.json`。
仅本轮观察，不含在途物理全集。当前磁盘可用约426GiB，评测目录约2.8GiB，不需要清理或重启。
最终报告对无BOTH回合保留SPT=NA的代码路径已只读复核，没有修改冻结指标或源码。
本轮verified wait，上一轮修复/审计为progress；有效八球仍为v4、尚未启动，Goal active。
开工main6fe74b6c/baselinef6e8f8c实际fetch/read；无RL/子agent/服务器计算/删除。

已核验共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_condition001_handoff_20261029_v1/`：

- `SCIENCE.tar.gz`：科学commit `5e755f5147e672d78e84316f62255353789e4484`的9个源码/准确报告/准备/审计文件，
  27227bytes，SHA256 `813282694c2d8a8e591e9f133481d945a6ba8d2f30e8ce23a8e98f300e10e75c`。
- `V8_FROZEN108_VERIFIED_WAIT_0027.json`：30628bytes，SHA256
  `8ef6da35b58b618a42a921829c22fc0d90944aeadc08d0cb814b7593995bbb61`。

科学包逐成员对Git blob/本机核验，两文件暂存与最终大小hash一致，不包含原108轨迹全集或本段后补说明。
十分钟观察00:27:18.782–00:37:18.780UTC共21次确认原1172675/start32623702和后处理1201537/start32942337
身份保持、原服务active且真实物理时间推进，完成19→21；最大原服务内存926273536bytes，OOM/oom_kill/swap全0。
observer27970自然exit0。00:38:39UTC原两个服务仍active、22/108，未因观察结束重启。
第三条件ESN seed2在途窗口记录0.243724mm穿透超限，完整失败按原协议保留，未更改门槛。

本轮完成两件事：核验第二条件九模型的全部保存子步；修复待用补采入口将服务查询错误
当作停止状态的问题。当前评测继续运行，**没有新的物理采集或模型重训，主矩阵未修复**。

## 第二条件九模型

原条件`new30_prospective_20261026_acceptance_001`九回合均完整55秒、无提前abort，
Task/Strict全部false。共9,900,000个保存物理子步的指标算术、source/config/checkpoint/MJB
hash、原actor/filter精确重放收据通过。仅核验此条件，不重启全矩阵后处理。

| 方法 | seed末位 | 最后失败阶段 | 峰值力矩 Nm | 外部/桌边最大穿透 mm |
|---|---:|---|---:|---:|
| ESN | 1 | lift | 73.252 | 0.139479 |
| RNN | 1 | approach | 42.319 | 0.100814 |
| MLP | 1 | approach | 36.665 | 0.036631 |
| ESN | 2 | carry | 60.104 | 0.160713 |
| RNN | 2 | carry | 37.866 | 0.159258 |
| MLP | 2 | carry | 51.602 | 0.351307 |
| ESN | 3 | lift | 60.850 | 0.142894 |
| RNN | 3 | carry | 37.696 | 0.155045 |
| MLP | 3 | carry | 37.370 | 0.147263 |

MLP seed2穿透超过原0.2mm门槛，保留为机器合规失败；其他八回合按当前机器合规定义通过，
不等于Task或Strict成功。MLP seed1未发生人体接触，舒适代理NA，不写100%。
没有BOTH成功回合，SPT为NA；全局T_ref和三方法汇总仍等待完整108。
这些是保存证据/算术复核，不是独立动力学再积分，也不证明真实人体安全。

审计`V8_CONDITION001_AUDIT.json` SHA256
`89b717930911d6690d7b4a1c3ecccaa8504634308846bbb50359a5ecc519d10b`。
实际审计服务`sii-v8-condition001-audit-20261029.service`于00:26:40UTC自然success，
CPU消耗5.261秒，CPU50%/线程1/MemoryMax3GiB/swap0。
原condition000审计完整保留；此次不是新的矩阵排名。

## 已修复的补采入口问题

旧入口以`systemctl --user is-active --quiet ...`的返回码非0判断原服务已停止。
非0也可能来自DBus或服务查询失败，因此该判断不满足“先确认原作业已终止”的要求。
当时原108仍在运行，旧入口尚未启动物理；未据此推断已经发生重复作业。

新入口：

- 准备时查询实际用户服务，绑定原PID1172675/start32623702，并核对其准确命令和准备目录。
- 启动时要求服务明确`LoadState=loaded, ActiveState=inactive, Result=success, MainPID=0`，
  并确认原PID/start身份不存在。查询失败、字段缺失、服务丢失或原进程在服务外仍存活均拒绝。
- 保留完整108、审计和报告hash检查，另绑定原准备hash与审计model-lock。
- 增加实际cgroup CPU上限≤100%检查，原单线程/3GiB/swap0限制保持。
- 原独占probe锁及全局仿真锁保持；没有自动重试、自动拟合或新服务派发。

此修改需要重新登记source hash。**唯一待用版本为v4**：
`outputs/nonrl_ball_coverage_probe_20261029_v4`，REG SHA256
`6b54db811db82c14d309581ecfc4e6df70f795c87c92a52c9a3279e7f8f1b14d`。
v3仍未启动，旧登记与旧launcher完整保留，并新增superseded说明；v1/v2同样不用。
八个case、teacher配置、原物理/门槛/输入/filter/执行器限制、资源预算逐项与v3相同。
登记源清单仅`prepare_ball_coverage_probe_20261029.py`一项变化。

## 检查与实际下一步

`check_ball_coverage_service_guard_20261029.py`通过2个合法终态正例和9个拒绝用例：
active、deactivating、failed、inactive但非success、unit缺失、MainPID非0、原PID身份仍在、
查询异常、返回字段不完整。正例包括PID已不存在和PID已被另一进程复用；后者不等于原进程存活。
这是隔离边界检查，不是声称原108已经完成。

重新运行原静态准备检查：默认task/layout逐元素等价、原阶段gate函数未变、资格检查仅
wrapper文字不同、八方向配置/四非法配置检查通过；原108冻结绑定保持。
**真实v4 --run仍因原108未完成拒绝，未创建execution或物理产物。**

下一步仍为原108自然完成→现有后处理全审/图表→实际查看并归档→v4八球开发控制及完整review。
后续采集与公平重训需要覆盖三场景的载荷、方向、阶段和恢复组合，见
[ESN外推定位](NONRL_V8_READOUT_SUPPORT_DIAGNOSIS_20261029.md)。八球本身不替代三场景目标。
启动命令改用`tools/prepare_ball_coverage_probe_20261029.py --root
outputs/nonrl_ball_coverage_probe_20261029_v4 --run`，必须通过正常单模拟器有界服务执行。
结束后用现有`review_ball_coverage_probe_20261029.py --root ...v4 --output ...v4/REVIEW.json`。
完整正向物理接续与八条资格仍待，不能用软件检查证明修复有效。

开工main `8dec2341602b9cacb78c1ac799307bd99907d433`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`实际fetch/read。上一轮为诊断progress；
本轮补采入口修复及完整条件审计也是progress，原108/后处理继续。无RL/子agent/服务器计算/删除。
新源码/准备/审计目前仅本机，核共享后补准确路径。Goal active，最终六指标与修复尚未完成。
