# 原108结束后的临时服务回收衔接

主矩阵仍未修复，Goal active。原108/后处理继续，04:18:06 UTC为62/108，
条件006最后一条MLP3在途。本轮修复后继入口的真实生命周期兼容问题，未执行新物理。

## 发现与边界

实际原评测服务为`Type=simple`、`RemainAfterExit=no`、`CollectMode=inactive`，
FragmentPath位于`/run/user/1000/systemd/transient/`。
InvocationID为`1cdbbfde2fba4561902e546b2e03db38`，仍是PID1172675/start32623702。
先前真实完成的`coverage-dataset-check`服务退出后已被回收：LoadState=not-found、
ActiveState=inactive、MainPID=0、InvocationID/ControlGroup为空，ExecMainCode=0、
ExecMainStatus=0、Result=success是查询默认值，**不能作为正常exit0收据**。

旧八球v5只允许loaded/inactive/success，若原评测正常完成后被回收，会被误拒绝。
本轮不改原服务、v5登记或其198绑定源码。新增独立
`tools/prepare_ball_coverage_reclaimed_20261029.py`与唯一后继
`outputs/nonrl_ball_coverage_probe_20261029_v6`，REG SHA256
`c9450ef98e5a6597158a4ace7117ba771cab300eee49cf0ee9314ccfbf2a9e94`。
v5保留为未启动历史，增加superseded说明。v6的198源仅将旧launcher换为新launcher，
八条件、seed、teacher、物理/输入/filter/gate、资源和科学前置完全一致。

## 新守卫

先核原108 execution完整108、全部独立审计通过、REPORT hash及原preparation/model-lock。
之后才检查原服务终态，登记额外绑定boot ID、InvocationID和原cgroup绝对路径。
两种允许状态都要求同boot、原PID/start身份消失、MainPID=0且inactive：

- retained unit：loaded、同InvocationID、Result=success、ExecMainCode=1且ExecMainStatus=0；
  记录`service_exit_zero_verified=true`。
- reclaimed unit：not-found、InvocationID/ControlGroup均为空、**原cgroup路径也不存在**；
  记录`service_exit_zero_verified=false`，只根据已完成的独立科学证据和无原运行实体允许交接。
  不声称已找回原父进程退出码，不能单凭not-found进入此分支。

查询失败、残缺响应、active/deactivating、原PID仍存、旧cgroup仍存、boot变化、
不同invocation、异常exit均拒绝。原单模拟器锁、单CPU/线程、3GiB/禁swap保持。
这不是放宽物理/任务门槛，也不修改在途模型或重启科学作业。

## 验证与交接

`check_ball_reclaimed_handoff_20261029.py`验证3正向状态及14拒绝情形；实际原108未完成时
新run入口拒绝，v5/v6都没有execution.json或物理产物。真实原服务准确InvocationID/PID/start
核验通过。当前只验证软件边界，尚未发生真实完整108终态交接或八球物理运行。
实际新旧launcher差异已逐段审查，旧198源hash保持，全部科学条件逐字段相同。

- [准确登记](evidence/NONRL_INTENT_RECOVERY_20261029/V8_BALL_COVERAGE_V6_REGISTRATION.json)。
- [检查](evidence/NONRL_INTENT_RECOVERY_20261029/V8_RECLAIMED_SERVICE_HANDOFF_CHECK.json)，SHA256
  `cf229242aed087bc051c67c5e7c3b46931ccdc06cde3c9007bbd457321d6318f`。
- 五成员源码/登记/检查/superseded包18669bytes，SHA256
  `306733cd7285769008df1a30278542528fffe984cf9a3ff061dd24ca6cda3d57`，逐成员及暂存/最终核验后共享：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_reclaimed_handoff_20261029_v1/SOURCE_AND_CHECKS.tar.gz`。

下一步：原108完整后处理、实际查看图表并归档后，以单CPU affinity6/数值线程1/3GiB/禁swap
运行`prepare_ball_coverage_reclaimed_20261029.py --root outputs/nonrl_ball_coverage_probe_20261029_v6 --run`。
启动前重新核主机内存和现有作业。不要再启动v5或任何更旧版本。
八球全八review仍使用原`review_ball_coverage_probe_20261029.py`；之后正式三场景采集/资格、
变时长实际train覆盖检查、公平重训和冻结108回归六指标仍待。

本轮开工main `b05249b33858a36f21c420225167a31d172337fa`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`实际fetch/read。上一轮verified wait，
本轮后继守卫修复progress。无RL/子agent/服务器计算/用户数据删除；可选004审计仍未重试。
