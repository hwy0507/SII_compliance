# 接触全子步sidecar：冻结测量与不变性协议

范围仅为补充穿透峰证据、验证测量无干预；不调参、不改验收、不开展步长/CCD扫描、不重训，不覆写原106回合。

## 预先指定小矩阵

复制原固定预算服务器 `source_fixed_budget` 到新的只读源码快照，三个24s回合分别运行contact sidecar OFF/ON，共6条。每条都继续启用原物理子步三指标wrapper，使唯一差异是新增contact读数与落盘。

| 方法 | seed | 用途 | 原穿透门余量 μm |
|---|---:|---|---:|
| VMC | 9403 | 靠近门的通过样例 | +0.607 |
| MLP | 9400 | 靠近门的失败样例 | −0.863 |
| ESN | 9403 | 任务失败且穿透越门样例 | −12.809 |

选择只用于机制诊断，明确是事后选择的诊断样例；不是新的泛化验证或选模数据。保留6条全部结果，不以失败换seed。

运行顺序：先VMC9403 OFF/ON同时运行，最多2worker。逐元素验证原18个rollout数组、contact_samples、physics_states及原物理子步raw数组相同，MJB和原gate、原全部障碍contact统计一致；原OFF与历史同回合也必须一致。若首对有差异则保留原数据并停止余下4条，排查后改新协议版本，不原地修改。首对通过后余下两对最多2worker。启动前核对服务器其他仿真数量，总量不能超过4；等待PPO12结束后再启动。本机不运行模拟。

## 完整接触测量

- 从原 `mj_step` 返回后直接读取live contact，与原在线审计相同的contact快照。机器人geom集合与 `audit_obstacles` 沿用运行环境，排除目标物。所有深度、状态、时间使用float64。
- 每个50μs物理步、每外部障碍保存最大 `max(0,-contact.dist)`、对应geom1/geom2、该对法向力、该障碍接触数、阶段、步前/步后时间。全部物理步分块保存，无稀疏抽样。
- 累计深度≥0.18/0.19/0.20/0.21mm的物理步数、总时长、最长连续段，另按阶段保存。原门始终为最大非目标物穿透<0.2mm，不应用新的容忍区间。
- 每个新障碍最大值、或任一障碍深度≥0.19mm的每一步保存事件：所有相关contact的geom对、dist、contact坐标/法向frame、原求值geom位置/姿态、contact frame下力、solref/solimp、constraint地址。
- 同一事件保存 `mjSTATE_INTEGRATION` 完整步前/步后状态（含qpos/qvel、warmstart、ctrl、外力、mocap等），以及步后qacc、qfrc_constraint、solver_niter和第一island可见迭代统计。状态通过mj_getState复制，不调用forward/collision，不写live model/data。
- 限定原implicitfast积分器。contact几何/力是原该步动力学求值保留的数据，步后qpos已经积分；将时间记成输入/输出区间并保存原求值geom变换，不把二者说成严格同一时刻。solver统计不是经认证的数值误差界。

状态事件分块保存，无“只保留最漂亮峰”的筛选。记录数据缺失、异常和不完整回合，错误不转换成成功。

## 验收与交付

1. 本机仅纯合成数据单元测试：阈值等号、连续时长、deepest pair、目标物排除、完整状态复制、分块保存、错误步长拒绝、hook恢复；不运行mj_step。
2. 服务器启动前冻结完整命令、环境、协议、旧源码hash、新包装器hash、checkpoint hash、预期历史MJB/trace hash。
3. 首对及其余两对都进行ON/OFF/历史三方不变性检查；逐条重算raw contact深度峰及阈值持续，与在线summary及原rollout.json障碍峰完全一致。
4. 独立报告每个原穿透峰的障碍/机器人geom、实际阶段、步时间区间、原门余量、越门累计与最长连续时长、峰时solver/力。只有在获取证据后才能讨论短瞬态与数值计算的区别；本轮不改变原判定。

服务器输出计划为 `outputs/contact_sidecar_20260924_r1/`，新独立driver负责协议准备与顺序队列，最多2worker。

## r2比较器修订（首对结束后，余下回合启动前）

r1首对ON/OFF/历史的所有数值数组精确相同，原gate和panel审计一致，但driver把 `contact.pairs/robot_geoms/robot_bodies` 的无序集合转list顺序视为差异，按协议停止。r1源码、协议、failed标记和两条结果全部保留。r2仅在比较器中排序明确由set序列化的 `pairs/robot_geoms/robot_bodies/other_contacts`，仍逐位比较所有数值及其他序列，不加任何数值容差。

r2独立输出 `outputs/contact_sidecar_20260924_r2/`，复制/校验复用r1已完成首对的全部文件hash，先重新验收首对，再运行原先声明的MLP9400与ESN9403 OFF/ON四条；不重跑首对、不更换诊断样例。sidecar与冻结物理源码不变。启动允许已有最多2个已协调仿真worker，自己的最多2个，总数不超过4。
