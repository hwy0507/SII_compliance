# 条件终端估计器有限在线94已启动（2026-10-31）

三路从各自完整正式93恢复，新的有限94已实际训练。每方法最多一轮30×55秒/41250新增transition，无自动95、无Direct34。原96次兼容测试权重及任何restart_fixture均未导入；正式学习模型、Adam、RNG与全部旧回放精确继承。Goal active，完整94、reward稳定和原loss健康仍待。

## 科学依据与修改范围

原93仍有loss尖峰和92→93 reward变化，不能宣布收敛。有限冻结target对照中的条件终端全量平均改善全终端masked SSE及原抽样loss均值，但I原最大batch、新93样本分配、旧92中止与V unmasked退化均保留。随后完整native三方法重复/重载、actor-target-温度、增量缓存与全部state验证通过。依据这些具体证据登记一轮在线94，检验动态策略/target和新增物理数据下的行为，不自动扩展预算。

新版本只替换q_losses中终端抽样SSE为完整五位mask分层条件期望，原批次、mask、分母、terminal128、非终端目标、pair与actor/target/温度路径不变；固定状态下期望loss/gradient对应原式，但有限Adam轨迹不同。CensusCache持续包含全部当前终端、只扫描新追加行。模块与通过测试的v2逐字相同，28个运行源码锁定，原辅助模块/物理源码保留。

新checkpoint与execution保存conditional_terminal_amendment和learner版本marker；父只允许准确完整93。旧loader可能丢新规则，归档/审查明确检查marker，CPU诊断用严格完整state恢复并在随机forward后恢复RNG。源码/注册/父状态/有限预算任何漂移拒绝。

`agent_train/q_loss`在94是新条件估计器loss；`agent_train/conditional_terminal_q_loss`明确标注同一值；`agent_train/original_sampled_q_loss`逐步记录原抽样计算。原loss健康判断使用后者，不能用前者平滑来覆盖此前异常。完整loss消费者保存三列原抽样/条件估计/actor，诊断图也使用原抽样loss。4096行额外TD仍为明确标注的未投影固定min-pair诊断，不冒充训练投影/mean目标。

## 预检与实际启动证据

三方法共99个非法登记/父状态反例均拒绝；各自真实65536批次更新两次可精确重复且完整恢复，共6隔离更新、0预检物理。加入marker之外，完整93 learner/Adam/RNG与全回放相等。三路GPU消费者及另行CPU完整state随机推理恢复检查通过。启动gate确认无原93/新94重复进程，核验新主机guard身份后正常派发。

实际启动审查：阻抗/导纳各新增1000、VMC新增2000存档，旧回放所有字段逐元素相等；新current/next52、clock/history/rawbit、raw/mixed action和冻结reward重建误差全部0。每路30个原MJB与30个sampler、原CPU组、actor49/critic52、23/47容量marker、4m append-only、优化器超参和双loss日志通过。该前缀无新terminal，不能代替后续真实终端缓存增长检查。

三learner、90sampler、archive与5guard共99个实际进程身份，连续120.082秒/13样本保持，三路steps分别增长{'impedance': 1087, 'admittance': 1092, 'vmc': 1086}。记录时总steps{'impedance': 3857029, 'admittance': 3860515, 'vmc': 3861566}；仅运行中进度，不是完整94结果。所有科学训练进程继续，不要重启。

| 方法 | 初始正式93 steps | 当前登记新增预算 | GPU | Learner CPU / 采样CPU |
|---|---:|---:|---:|---|
| 阻抗 | 3852762 | ≤41250 | 1 | 13 / 14–25 |
| 导纳 | 3856250 | ≤41250 | 2 | 26 / 27–38 |
| VMC | 3857250 | ≤41250 | 3 | 39 / 40–51 |

唯一LAUNCH在`runs/parameter_census_cycle94_20261031_v1/LAUNCH.json`。实际pid/start均见收据；archive94等待完整94，再核验版本/完整边界和归档hash，运行全journal/replay、strict health与完整loss消费者。完成后仍须实际图查看、保存算术与完整93→94比较，不能仅凭FINISHED当科学完成。

## 稳定性与中断续接

新版本首个候选窗口94–96，沿用原5%、near-zero guard1、5000 bootstrap和seed2026102861。STABILITY_WINDOW_INTENT准确登记于94已启动但尚无任何完整回合结果时，保留当时progress；不是启动前登记。它不授权自动95/96，未来两轮仍各需完整科学审查和单独有限登记，统计输入绑定仍待。旧90–92失败和92→93变化全部保留，不以新窗口覆盖。

若主机再次中断，先保全当前各train/checkpoint_latest.pt与journal。94已产生新的正式更新，不能回退到93或用本driver重跑整轮94；须另登记识别census marker的partial恢复，保留最新已学权重/Adam/RNG/回放和未完成94记录。原MuJoCo物理状态未保存，不声称回合连续恢复。完整94后才改用其正式归档。

原physics/MJB/Task/Strict/canonical48/filter/actuator/dt5e−5、critic52/actor49、clock/history/rawbit、原LR/reward/masks/terminal128/batch65536/UTD1保持。所有历史失败、中止、partial75、不可评74—76、halfstd拒绝、第一版census软件失败均保留；本阶段预检与实际启动未报告科学失败。只读查找路径缺失和startup进程完成瞬间/proc读取缺失已记录，无据此重启。

Direct33原数值验收及冻结30 Task/Strict0/0、旧28内存证明不足及恢复2全state不变结论保持。原冻结90已完成勿重跑，指定ESN仍缺，最终独立比较仍待。无子agent。后续具体审查入口见NEXT_REVIEW_NOTES.md。
