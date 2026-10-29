# v9 同场景诊断优先的安全边界调度修正

用户要求持续修复 teacher/学习/场景问题。此前将同场景18条开发诊断排在组合office108全部完成之后，会让与根因定位关系较弱的迁移压力测试长期阻塞修复。本轮调整调度顺序，不放宽任何科学门槛，不把未完成回合当作完成。

## 边界协议

1. 原108协调器已有 STOP_REQUESTED 检查，在完整worker、paper_metrics与结果落盘后，下一回合派发前自然写 stopped_at_episode_boundary 并退出。请求时已完成50条，在途回合继续执行。不向worker发停止信号，不改原协调器源码或checkpoint。
2. 原v3等待器按原登记遇到此状态会拒绝派发并退出；它的拒绝收据保留。v3未执行任何student回合，不能把它说成已完成或成功。
3. 首版入口为v4；当前唯一运行入口为 `tools/run_v9_paired_priority_v5_20261029.py`，运行目录 `outputs/nonrl_v9_paired_scene_priority_20261029_v5`，服务 `sii-v9-paired-priority-v5-20261029.service`。必须确认原scope inactive、旧等待器 failed/inactive、原execution为安全边界、全部rows returncode0且逐项对应完整results、有序且不重复，才可复制不可变边界快照并派发。
4. BOUNDARY_HANDOFF.json绑定真实原execution/registration hash、原状态和完成数，列出原108所有未完成格子。原状态不改成complete，失败和轨迹不覆盖。后续以原九模型/冻结条件补齐这些不相交格子，再联合审计原完整集合；不能拿中途子集算最终排名或SPT。
5. 新入口采用原18条train00/validation08案例及同身份合格teacher，由未改的coverage wrapper获取 `outputs/.local-rl-compute.lock`，协调器使用独立 `outputs/.v9-paired-priority-coordinator.lock`；原run的资源检查、物理派发和审计循环AST逐字结构一致，只替换调度前提。单CPU6/线程1/3GiB/禁swap，原物理/最终门/输入/filter/执行器不改。不是未见测试，也不允许据office测试选新参数。

## 前置验证

合成正向边界通过；原scope active、Invocation更换、旧等待器active、父running/failed、未完整worker、结果缺失/错配和重复格子九项拒绝通过。完整原run资源/派发/审计代码在替换前提以外AST相同，18案例登记完成。登记冻结1111个源文件并实际逐hash核验。

本轮只在真实边界与配对结果出现后记录其事实，不把调度修正称为ESN控制表现已修复。原108暂缓后仍是未完成，Goal active。当前服务/边界/进展以相邻 `docs/evidence/nonrl_v9_priority_boundary_20261029_v5/` 收据为准。

## 真实边界与锁冲突修复

原108在51/108完整结果后自然stopped_at_episode_boundary，原scope inactive，原v3按照其完整108前提拒绝派发并failed_preserved；没有student execution。边界原execution SHA1a9053dd1b7ba988d1b39c8be85b494379bc46967e019440332f2351a92b434c，剩余57格逐项保留在BOUNDARY_HANDOFF.json。

我新增的v4协调器曾重复持有wrapper所需全局flock，首case在wrapper第424行获取锁处BlockingIOError、returncode1退出，未创建任何scene execution或trajectory、0物理积分。这是可避免的调度实现错误，v4源码/登记/日志/失败收据完整保留，不回写“成功”。v5只修正协调器锁的所有权，run资源/派发/审计循环AST与v4精确相同，wrapper独占全局仿真锁。v5启动前强制核v4已终止、锁处异常及零物理证据。

v5 PID1672647、Invocation32b84eb9ac2340b7ad71078d0f976db3真实active，MemoryMax3221225472/swap上限0。首rod00 ESN 100000→340000物理子步真实推进；独立进程获取全局仿真锁被拒绝，确认锁修复后仍阻止重复仿真。

首rod00 ESN已经完成400000子步并actor/filter精确回放通过，但task=false、safety=false、scene_contact=false；峰矩45.3241Nm、最大外穿透0.219314mm（阈值0.2mm，失败保留）。同身份teacher原资格通过、task=true、最大穿透0.071541mm。这个train00配对已说明不能仅归因office场景迁移；仍须完成全部18条再作训练/验证侧修复决策，不能从单条宣称所有场景失败或方法排名。此处是开发资格，不冒称正式Strict测试。

## train00 同输入历史诊断

首棍推teacher与两学生初始canonical48观测逐值完全相同、MJB相同，排除本对照的初态/模型不一致。teacher在自己的500帧历史上逐数组重放误差0，两个学生各自actor重放误差0。

ESN在teacher历史上的动作MSE仅2.56526e-6，RNN为3.77224e-6；但ESN真实闭环5.12s开始requested残差饱和，全回合占57.2%，RNN没有饱和。teacher在同一ESN观测历史上的反事实动作与ESN的差异在4.84s超过0.1、5.00s超过0.5；整回合MSE0.321953，而RNN对应历史为7.67933e-5。不同历史的MSE不能当共同输入方法排名，teacher反事实也不证明它能物理纠偏，未作为新训练标签。

RNN rod00真实开发Task/safety/contact均通过；ESN三者失败。这一训练侧证据把下一步重点转向ESN闭环读出/覆盖修复，不再仅以office迁移不匹配解释。全部18结束后按登记审查再定有限修复，未在本轮重拟合或放宽gate。

随后MLP同一rod00也qualified；首组三方法完整，ESN失败而RNN/MLP通过开发资格。18条整体仍在运行，不将该首组外推为最终测试排名。
