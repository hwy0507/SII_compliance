# MLP384 fixed27 开发闭环：宿主核验与完整复核入口

## 最新宿主快照

2026-10-31 02:55 CST，原协调器 PID2517772 仍由同一用户 scope 运行，execution 已到 22/27，当前 `corner_00__special_rnn_scratch_s2026102802`。完成行 Task 22/22、Strict 19/22；MemoryCurrent 约 0.72 GiB、MemoryMax 3 GiB、swap0，OOM/OOM-kill 均为0。另一路 CPU5 对这22条已完成行的 actor/filter 独立重放误差均为0。快照和所有行指标 hash 见 `docs/evidence/CONTACT_YIELD_MLP384_LIVE_PREFIX_V2_20261031.json`，对应重放见 `docs/evidence/CONTACT_YIELD_MLP384_PREFIX_REPLAY_V3_20261031.json`。这些仍是 train00 开发集中的部分行，不是最终测试。

观察时间：2026-10-30T18:47:33.821999+00:00。只覆盖已完成的 13/27 条 train00 开发回合，不是最终测试结果。

完成前缀 Task 13/13，Strict 10/13。原协调器 PID2517772 的宿主进程和 scope 已实际核验 live；MemoryMax 3 GiB、swap0、OOM/kill0。资源快照不是内核全程峰值。

| 方法 | 棍推 Task/Strict | 峰穿透 mm（三 seed） |
|---|---|---|
| ESN | 3/3；3/3 | 0.065508 / 0.067434 / 0.073104 |
| RNN | 3/3；3/3 | 0.033068 / 0.076847 / 0.095849 |
| MLP384 | 3/3；0/3 | 0.251768 / 0.243292 / 0.222516 |

宽 MLP 的验证动作 MSE 下降12.23%–17.45%，但棍推三个种子均超过冻结0.20 mm门槛；不能把拟合改善解释为闭环安全改善。原宽128 MLP在同rod00为1/3 Strict，新模型为0/3；这是单个已见训练身份的开发诊断，不能推广为未见性能结论。其余回合按原队列完成，保留全部失败，不依据开发结果重选checkpoint。

## 加载器修复与审计边界

v1/v2在首个宽MLP物理步前被旧loader拒绝；v3完成首个宽MLP物理回合后，独立审计子进程又调用旧loader而失败。v4通过隔离worker及独立actor/filter审计使用版本化v2契约loader，已保存失败资格收据。所有attempt保留。

最终全27 reviewer原本仍经legacy loader，新增独立入口 `experiments/review_contact_yield_mlp384_fixed27_20261031.py` 在自身进程绑定同一已审loader，复用原完整review算法。未修改运行中注册source，也不新增物理或optimizer更新。前缀replay输出独立证据，不冒充全27复核。

完整27结束且原execution为complete_development_diagnosis_pending_review后，使用原解释器、CPU6/单线程/3GiB/swap0运行该入口，输出到本run新的REVIEW_WIDE.json。若现有同名输出已存在则拒绝覆盖。

最终108仍封存，Task/Strict/双成功SPT/平均峰矩/人体舒适度/机器合规率的最终比较未完成。开发场景仅有杆/球接触代理，human_comfort=null不能改成100%人体舒适。

## 同步状态

已fetch并读取远端main 9207ff427aa1c90e6e27926dbe86c8a3943e4f0e与baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d UPDATE_LOG；main为另一RL会话新进度，不改其运行。共享服务器连接被自动审批拒绝，已请求具体授权；本轮大产物仅本地，未声称已归档。

证据：`docs/evidence/CONTACT_YIELD_MLP384_FIXED27_PREFIX_20261031.json`，包含完整执行前缀、指标/资格/审计、hash与宿主资源读数。最初生成证据的shell字符串转义错误在运行前SyntaxError，修正后才生成该文件，0训练/物理步。

前缀wide-loader实际重放已通过14条完成轨迹，actor/filter最大误差均0；独立证据为docs/evidence/CONTACT_YIELD_MLP384_PREFIX_REPLAY_20261031.json。该14条是稍后时刻快照，与13条资源/指标前缀分别绑定，不混作同一观察时刻。
