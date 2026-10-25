# Fresh CHEQ 学习启动核验与采样资源优先级

## 结论与范围

新的 reduced-reuse CHEQ 已开始真实在线学习，尚未完成第一个 30 条件周期，不能称为收敛。
本轮将后续资源优先给这个已登记的新阶段：待原两个协调器完整交接后，SAC 在完整周期
边界保存并停止；CHEQ 在完整周期边界保留全部训练状态，采样器由每路 2 个扩为 12 个。
协调器已经启动但仍在等待依赖，**扩容尚未生效**，也没有向任何 learner 发出本轮停止请求。

这次调整不改变 source_train16、batch256、UTD1、gamma=.9995、reward、actor、physics/MJB、
gate、公共 filter、执行器或 dt。六个完整周期是原阶段的总 review 预算，交接后只运行
`6 - 已完成周期数`，不是再增加六周期，更不是总训练目标的步数上限。

## 学习启动证据

CPU 只读核验已结束，没有增加 physics 或 optimizer updates。

- Direct3000、Admittance2000、VMC4000 步的预热 checkpoint 与同 source/seed 的全新构造
  完全匹配，优化器为空。9000 行 replay 的奖励、终止标志和自身 mixing context 与真实
  transition 日志一致。CHEQ actor49/action7；该动作维度在本条证据中仅覆盖这三个接口。
- Direct/VMC 的 6000 步 checkpoint 各有 1001 次 critic 更新。actor、critic ensemble、
  target ensemble 参数均已改变，所有网络参数和日志指标有限；Adam 计数有效，预热
  replay 所有保留字段精确相同。optimizer 日志与更新步序精确匹配。
- Direct 参数变化 L2：actor1.9332、critic10.4196、target8.8988；VMC 为1.7750、9.3059、8.0624。
  这证明代码确实进行了学习，不证明策略质量、value 校准或稳定性。
- Adam actor/alpha 计数1002、critic1001，是原 policy_frequency 实现的实际结果，不伪装
  为三者相同更新次数。

启动检查时新阶段进度：

| 方法 | 真实 transitions | 梯度更新 | 当前周期 | 完成条件 |
|---|---:|---:|---:|---:|
| Direct | 8385 | 3386 | 0 | 6/30 |
| Impedance | 尚等原资源释放 | — | — | — |
| Admittance | 7171 | 2172 | 0 | 4/30 |
| VMC | 8480 | 3481 | 0 | 6/30 |

以上为 `STARTUP_REVIEW.json` 的时点快照，不是停止时步数。早期完整被动回合失败保留，
特别是预热回合不能归因为学习后的控制效果。

## 为什么调整资源

原 SAC 的独立完整周期证据已显示 critic 持续恶化。Admittance/VMC 的 cycle2→3
loss 分别146717→1790203、537785→3062208，terminal MAE3754→13778、11169→23290；
Direct cycle5 和 Impedance cycle3 也没有健康收敛证据。增加 SAC 采样器只加快采样，
并不修复这个问题。保留其当前完整周期和所有状态，把后续算力优先给已选定的新阶段。
这不是 CHEQ 已优于 SAC 的结论，也没有再次改变新阶段的学习超参数。

新配置总共52个 learner/sampler CPU，另留13、53、54用于只读审计、监测和协调：

| 方法 | GPU | learner CPU | sampler CPU（12个） |
|---|---:|---:|---|
| Direct | 0 | 0 | 1–12 |
| Impedance | 1 | 14 | 15–25、52 |
| Admittance | 2 | 26 | 27–38 |
| VMC | 3 | 39 | 40–51 |

并发变化会改变后续采样到达次序和 action RNG 的交织；这是有记录的资源调整，不声称
未来轨迹逐位等价。不得为 GPU 占用而扩大 batch/UTD。当前利用率50%要求仍未完成。最新无辅助训练的60样本/67.41秒窗口，GPU0–3均值
分别11.93%、7.17%、31.72%、3.58%，最小值均0；当时SAC Direct/VMC在周期尾部分别
只剩2/1个采样回合。该实测发生在新扩容前，不能充当扩容后的利用率结果。

## 安全交接与审计

- 新 coordinator **1956030** 先等原 fresh dispatcher1146202 和 SAC coordinator691298
  写出四路已实际更新的结束收据并退出，然后才发出八路完整周期 STOP_REQUESTED。
  通过实际 PID/启动时刻、命令、CPU/GPU、协议 hash 和进度核验，不能绕过尚未启动的 Impedance。
- 每路等其 CHEQ 与 SAC 原进程都正常退出，核对完整30条件（含失败）、FINISHED、checkpoint
  和协议。CHEQ 网络/目标网络/Adam/温度/RNG/replay/history 全状态字节复制到独立父文件，
  使用同一冻结 trainer 恢复。任何失败保留现场，无自动重试或整组强杀。
- 原只读 observer1156327 在等待cycle0、无子进程、无已完成诊断时被明确替换，
  新 observer **1968149** 仍审计原0/1/3/5。它从原run与新run查找真实归档，记录每个方法的
  actual_run；有冲突 checkpoint 则失败。诊断图只覆盖其实际run日志段，不能冒充拼接后的收敛曲线。
- 首次替换 observer 因当前Python无 `os.pidfd_open` 在发信号前失败；保留失败收据，
  核对原观察进程身份后完成唯一替换。训练和新资源协调器均没有因此重复启动。
- 7项守卫测试通过，覆盖预算/完整条件/CPU重叠/等待与身份/冲突归档；实际780源文件、
  24参数文件、30条件及参考计划hash通过。没有修改任何已有冻结runtime。

## 服务器产物与未完成项

实际集群主机：`rltest-1025--a6ed2ff39b3c-s5gnp35dxg`。
SSD根：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。

- `runs/fresh_reduced_reuse_learning_onset_v1/`：预热和更新后只读证据、checkpoint。
- `runs/CHEQ_FRESH_SAMPLING_PRIORITY_V1.json`：独立资源协议。
- `runtime/fresh_sampling_priority_v1/`：冻结协调/审计源码、预检、启动、替换失败和成功收据。
- `runs/cheq_fresh_priority_seed20261025_v1/`：等待中的协调器；之后才产生新learner产物。
- `runs/CHEQ_FRESH_PRIORITY_AUDIT_V1.json`、`runs/fresh_priority_audit_v1/`：替代只读观察。
- 仓库配套JSON保存证据hash、真实启动快照和完整资源协议；大型数据仅保存在上述集群。

资源交接、完整周期科学review、健康收敛、固定策略训练集矩阵、共同 `SPT_empirical` 和
指定ESN的公平比较均未完成。指定ESN checkpoint仍缺，不替换成历史ESN。继续保留所有失败，
不把名义控制的成功或训练内成功作为新策略的独立接受结果。

本轮重新fetch/read远端 main=`a52dfba4486af8d263d5cd0a976c3102482ff249`、
baseline=`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，没有新变更；本地研究提交尚待远端认证解决后发布。
