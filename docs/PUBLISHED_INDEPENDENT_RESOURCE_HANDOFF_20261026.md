# 按方法独立完成周期并交接采样资源

## 实际改变

取消旧资源交接的“四路新CHEQ都预热并开始更新”统一等待条件，改为各方法独立交接。
这只改变调度依赖，不改变 source_train16、batch256/UTD1、gamma=.9995、reward、物理/MJB、
actor信息、gate、公共filter、执行器或dt，也没有重新开始已经运行的CHEQ。

原v1逻辑在发出STOP前等待两个旧协调器完成。Impedance仍有原SAC需要收尾，之后还需
新CHEQ双worker预热；较快的Direct可能在此期间越过首个周期并进入下一整轮双worker，
导致可避免的额外等待。新协议让当前三路CHEQ立即登记“完整当前周期后停止”，
与同接口SAC分别收尾，二者都退出且完整checkpoint核验通过后立即恢复该方法。

- Direct、Admittance、VMC：完整当前cycle0边界复制全网络、target、Adam、温度、RNG、
  replay和历史；继续剩余五个周期，若实际边界不同则按六周期总预算扣减。
- Impedance：新CHEQ此前确实未启动。只等待原SAC当前完整cycle4释放对应核，随后直接
  用同source/seed/protocol、空replay/全新state、12sampler启动六周期。
- CPU/GPU分配保持原资源登记：D learner0+workers1–12/GPU0，I learner14+15–25/52/GPU1，
  A learner26+27–38/GPU2，V learner39+40–51/GPU3；共52核，13/53/54保留。
- 改变sampler数量会改变未来采样和RNG交织，不声称未来轨迹逐位等价；没有增加原阶段
  总周期预算，也不把六周期完成当作收敛。GPU50%要求仍未达到，当前尚不能评价扩容效果。

## 已执行与尚未执行

旧priority coordinator1956030、fresh dispatcher1146202、SAC coordinator691298均通过
各自COORDINATOR_STOP/DISPATCH_STOP正常退出，实际DISPATCH_STOPPED的已派发方法与登记一致。
它们已经退役，不应重启。旧进程没有触发额外Impedance learner。

新逐方法协调器 **2471936** 已运行，输出 `runs/cheq_fresh_ready_seed20261025_v2`。
它已写入六个新的完整周期停止请求，原Impedance SAC的既有STOP字节hash保持不变。
没有向learner发送进程信号，没有部分回合接续。冻结trainer仅在外层周期边界检查STOP；
内部仍派发当前全部30条件，失败回合保留。

原只读observer1968149在无子进程、无已完成阶段的等待状态被明确替换为 **2472115**，
原0/1/3/5审计仍保留；从原run、旧v1目录和新v2目录定位真实checkpoint。新归档器
**2472286** 从空LAUNCH开始跟随各路实际启动，持续归档至原有限阶段结束。
旧两个early/migration归档器在所有旧learner退出且父状态保存后才通过MONITOR_STOP结束，
没有写入伪造的旧协调器MIGRATION_FINISHED。

启动核验时原七learner均保持PID/启动身份、仍在运行且无FAILURE：

| 方法 | 新CHEQ步数/完成条件 | 对应SAC步数/完成条件 |
|---|---|---|
| Direct | 14431 / 10 | 367540 / 11（cycle8） |
| Impedance | 尚未启动 | 215028 / 20（cycle4） |
| Admittance | 12271 / 8 | 225243 / 27（cycle4） |
| VMC | 13153 / 8 | 242693 / 9（cycle5） |

条件数分母均30，是结束回合数，不是成功数。三路CHEQ均cycle0。
此时新协调器状态为draining_or_resuming_independently、launched为空；
**只证明完整周期收尾已经请求且原训练继续，并不证明恢复或12worker扩容已经完成。**

## 验证和产物

四项新增守卫测试通过：三resume+一fresh组合、缺失/重复parent、CPU/GPU与仍在收尾的
其他方法资源冲突、旧协调器未退役或意外多派发。复用既有完整周期/预算核验函数；
实际七parent命令/启动身份/EXECUTION/STOP及780源码、24参数、30条件/参考计划hash核验。
旧冻结runtime、协议和checkpoint没有修改。新工具及测试文件在UTC跨日至26日前编写，
保留其20261025文件名；本报告按实际整理日期20261026命名。

实际集群主机 `rltest-1025--a6ed2ff39b3c-s5gnp35dxg`，SSD根
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`：

- `runs/CHEQ_FRESH_READY_METHODS_V2.json`：新调度协议，覆盖旧统一等待v1。
- `runtime/fresh_ready_methods_v2/`：冻结协调工具、预检、旧协调器退出/新启动收据。
- `runs/cheq_fresh_ready_seed20261025_v2/`：实际收尾/后续恢复run。
- `runs/CHEQ_FRESH_READY_METHODS_AUDIT_V2.json`、`runs/fresh_ready_methods_audit_v2/`：替代只读观察。

配套JSON记录协议、实际启动核验和证据hash。剩余工作仍是原有限阶段的完整周期科学review、
健康收敛、固定策略训练集矩阵、SPT/接触舒适性和指定ESN比较；指定ESN缺口不变，Goal active。
本轮fetch main a52dfba4486af8d263d5cd0a976c3102482ff249、baseline
f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，远端无新增。
