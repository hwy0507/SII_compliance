# 当前原 ESN 在历史水杯／高柱综合场景中的一次测试

2026-10-13。按用户要求，将当前原 ESN 权重直接用于刚展示的9月28日旧综合环境。
完整55秒：**Task=true，Strict=false**。43.32秒开始释放、44.32秒撤离，最终完成桌面放置；
水杯被碰倒，且穿透与棍推接触覆盖不满足旧场景要求，不能称为完整柔顺验收通过。

## 冻结范围与结果

- checkpoint：`acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7`，
  即原 ESN `readout_refit_esn_2026100301`，不是9月28日旧视频的模型，也不是新数据重训模型。
  128维固定储备池、48D接口、7D动作；不训练、不改权重、无运行时teacher混合。
- 原场景二进制MJB：`586dd7f279dc511983910661b0941846a2a8bb8d8d4afb312907d3634cd5a620`；
  水杯＋高柱＋球＋人手＋棍子，普通桌面目标 `[0.54,0.23,0.425]`，没有新版未知凸边。
  使用当前评估器和名义控制实现加载原二进制；不是对9月28日整个软件运行时的逐位复现。
- seed2026091751、variant0，球2秒发射/1.7m/s，人手3秒启动/0.2m行程，棍9秒启动/
  0.235m行程/6秒hold。沿用该历史场景legacy时序，未采用后来错峰的新版时序。
  实际人手、棍接触时间范围存在重叠；本次不修订它，也不并入当前冻结公平矩阵。
- 55秒、25Hz、1375个动作；base dt=5e-5，前0.2秒沿用原数值细分1.5625e-6；
  共1,224,000物理子步。原输入来源/共同执行器幅值与变化率限制未修改；接触真值仅用于诊断。

| 项目 | 本次结果 |
|---|---:|
| Task / Strict | 通过 / 未通过 |
| 全程3D阶段目标距离RMSE | 217.945 mm |
| 实际广义执行器峰值力矩 | 49.842 Nm |
| 实际末端峰值线速度 | 0.39397 m/s |
| 最大外部穿透 | 0.277821 mm，门槛0.2 mm |
| 水杯最大位移 / 最大倾角 | 142.798 mm / 92.048° |
| 棍子累计有力接触 | 0.029850 s，要求>0.4 s |
| 物块最大抬升 | 139.447 mm |
| 开始释放 / 开始撤离 | 43.32 / 44.32 s |

RMSE由 `physics_substep_metrics` 的 `hand_position - reference.goals[stage]` 按物理时间积分。
旧任务carry指向该阶段终点，途中尚未到达也计入误差；carry阶段31.68秒、RMSE283.827mm。
因此此数字不是“相对一条逐点规划轨迹偏离218mm”，不能直接与新版规划路点实验的RMSE排名。

旧任务Task还检查完整时域、放置保持≥0.5秒、释放时承托、抬升>0.1m、末端撤离到目标15mm内
和夹爪张开>75mm。Strict额外要求有效物理接触、原接触覆盖、杯子稳定和球反弹。
本次Strict失败的三个独立原因：外穿透超限；杯子倾倒/移位且最终无底部承托；棍接触不足。
不是因为缺少新版元数据就判定Strict失败。人手累计接触2.6767秒，球0.00085秒且反弹，
杯接触22.707–24.083秒，柱接触28.401–28.445秒；first-to-last跨度不是累计接触时长。

## 审计、保留失败与视频

- 唯一完整物理回合在 `episode_v2/`。之前 `episode/` 在开始物理步前因
  `No XML model loaded` 退出，保留原失败记录；补上XML导出元数据初始化后仍加载原MJB。
  未按成绩重复尝试，没有额外成功回合筛选。
- 完整回合后的首版审计误读历史JSON不存在的 `placement_destination`，
  `execution.json` 保持 `failed_preserved`。修复仅限审计兼容，单独运行 `--audit-only`，
  `AUDIT_RECOVERY.json` 证明轨迹完整且复核通过，没有重跑物理或改写原execution。
- schedule/observer逐字段一致；原JSON缺少destination/support字段，明确标为无法直接对照，
  不伪造其相等。当前目标与承托记录保留在新JSON中。
- 1375步原始动作、128维状态、裁剪动作、过滤后yield/scale精确重放；
  三项子步指标复算一致，全程有限数值、55秒积分一致。
  独立外穿透子步记录与主统计一致。执行源码tar逐文件hash核验，除明确记录的audit-only修复外
  其余runtime源码未变；复制的checkpoint与原MJBhash一致。
- MP4完整55秒、25fps、1375帧、1920×560三视角，保存状态重渲染，无物理重算。
  全帧解码通过，24秒杯接触与55秒放置后画面已目视检查。
  视频上方的穿透数字是整回合最大值；Task/Strict也为整回合结论，不是逐帧状态。
- 本机单线程、仿真MemoryMax1.5GiB/禁swap，审计与渲染各1GiB。
  为满足内存准入，仅两次有时限冻结原公平比较协调器的派发；独立在途worker正常完成。
  两次lease均已自动thaw，原服务active/running，未重启/重复派发/改变预算。
  服务器仅存储和hash核验，未用于计算。

## 产物与可复现入口

共享目录：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_old_office_transfer_20261013_v1/evidence/`。
发布/核验状态以父目录 `ARCHIVE_VERIFICATION.json` 和本轮 `UPDATE_LOG.md` 为准。

- `episode_v2/`：执行记录、冻结checkpoint、原轨迹、原场景、子步指标、动作链、独立接触、源码tar、审计恢复收据。
- `episode/`：物理开始前的基础设施失败；`PROTOCOL.json`：一回合预算；两份 `DISPATCH_LEASE*.json`：资源交接证据。
- `source/`：新wrapper、lease、实际renderer及本报告；`historical_reference/`：原JSON、MJB、XML。
- `media/replay_threeview.mp4`：`1f6e4cfc1c943755c3f30c83305f4ccaea1600d5e818391b037354eac205f8d1`。
- 原轨迹NPZ：`a122e678ba6ef26e9ce38ef9c9834957c37c5ce7c52eb1ccbbdc6a5224c13468`。
- 子步NPZ：`bb444d48f7276b742bd5d743d38744aef45b3d58b4801886ff534471a8dcb5e6`。

实际命令、Python3.11.15、MuJoCo3.11.0、依赖与源码hash详见execution；实际计算主机airpig。
运行时base commit为 `02e3e289b02a561f1e6c0ac5abddb143612369e0`，未提交wrapper以run源码快照为准。
开工核对main `5a63bd74e94b2a21b4db08160e4eb474eac3ec7b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，期间main由原公平比较作业正常推进至上述base。

已完成：单次冻结权重迁移、审计恢复、完整视频。运行中：既有公平比较。
未完成：此旧布局的多条件/多方法对照与接触质量改善；一回合不能证明泛化成功率或ESN独占优势。
