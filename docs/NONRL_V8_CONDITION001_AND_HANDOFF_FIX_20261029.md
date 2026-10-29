# v8第二条件核验与补采接续检查修复

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
