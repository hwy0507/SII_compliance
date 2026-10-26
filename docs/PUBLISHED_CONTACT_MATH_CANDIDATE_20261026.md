# 接触计算独立候选验证与Direct暂时成功复核

正式四路fresh训练继续，未改变运行中的source_train16或训练协议。
本轮完成独立性能候选构建、守卫测试和注册，并启动完整动作记录重放验证；
另外核实Direct后续两轮的暂时成功与退化。两项都不构成收敛或最终方法排名。

## 候选的目的与范围

先前小batch profile显示采样循环开销较高；局部microprobe通过后，本轮新增
`tools/prepare_published_contact_math_20261026.py`，只在不存在的新目录构建候选。
父runtime所有780个source hash先核验，不修改父文件。仅改变三个候选副本：

- `scripts/audited_velocity_env.py`：接触循环绑定geom_bodyid视图；6处已知连续float64三维接触向量范数调用改用等价dot/sqrt。
- `scripts/validate_office_apparatus_v5_20260917.py`：相同数组视图读取，5处接触向量范数调用。
- `tools/published_compliance_episode_20261025.py`：注入evaluator的实际人体接触力范数调用使用同一helper；原注入匹配位置保留。

向量来自np.zeros(3)、np.zeros(6)的前三维或3×3矩阵乘三维向量。没有全局替换norm，
二维位置量、任务门槛表达式、物理步进、接触顺序和力调用不变。接触事件>.05阈值保持，
仅其中范数计算实现改变，必须由数值和完整轨迹证据验证等价。
参数、CHEQ和机器人manifest及其实际文件全部核验；候选副本中三个保护manifest逐字节相同。

3项软件测试通过：随机/特殊float64范数位模式、缺失/多义源匹配拒绝、真实源文件改写范围和重复改写拒绝。
第一次本地构建预检的helper防重复判断误把新调用当成已有定义，候选创建前失败；修复判断后测试通过，
没有失败仿真或改写运行中的源码。候选构建后保持冻结。

## 有限完整验证已启动，尚未完成

集群SSD基址：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/`。

- 父：`runtime/source_train16`；候选：`runtime/contact_math_candidate_v1`。
- 冻结构建器及原有验证器副本：`runtime/contact_math_validation_v1`。
- 注册和输出：`runs/contact_math_validation_v1/REGISTRATION.json`及`results/`。
- 注册SHA256：`84015ef93e79560472d02f3eea38b431010e579c713e5307a725992ff9e28cb1`。
- 候选RUNTIME SHA256：`fd3fa5365c0d1915104eb1b755eb1bea8f561508694b10355aee45f2f18893c5`。

四接口×三类场景首个登记条件，共12个55秒回合，预算1320万新物理子步；0optimizer updates。
参考为已归档完整审计的interim_cheq_cycle03_representatives_v1动作记录。先核验全部参考数据hash，
注册914个输入hash；不重新运行参考、不导入其权重、不视为新方法成绩或最终训练集矩阵。
验证每次观测/区间/潜势精确相同，结束核对MJB、actor journal、terminal和原子步文件字节，
以及rollout/filter/torque数组dtype、shape、bytes。rollout JSON仅允许登记的来源/输出路径变化
与显式robot_parts集合的序列化顺序差异，物理数值和任务结果必须相同。

协调PID2273688、首个child2273849，均绑定预留CPU53、nice10、禁CUDA，单个模拟器串行验证。
原四learner和52核分配不改。启动核验时首例Direct/passive_corner_train_0000已有537次动作前的
观测/区间/潜势通过，实际MJB/adapter/plan/dt与登记一致，父780source再次核验未变。
这是**前缀验证**，当时0/12完整通过；不能宣称整轨迹等价或加速成功。
后续读取原PROGRESS/RESULTS/FAILURE/FINISHED及同一进程身份，不因观察超时重复派发。
任何不一致会保留失败并停止该候选验证；完整通过也不自动切换正式训练，仍需阶段决策与登记。

## Direct第三、第四轮的真实变化

只读核验目录`runs/fresh_direct_cycle23_terminal_review_v1/`，0新增physics/optimizer更新。
两轮各30个终端、模型、fixture、参考计划、dt和完成时长核验，全部完整55秒。

| Direct完整轮次 | 累计真实步数 | Task/Strict，各30 | 平均回合reward |
|---|---:|---:|---:|
| cycle2，第三轮 | 123750 | 2/2 | −29.59422 |
| cycle3，第四轮 | 165000 | 0/0 | −33.25034 |

两个成功都在主动短期：0100在54.040s、0000在54.160s认证最终稳定放置；
终端阶段字段为release，但实际Task/Strict gate均真，不能用阶段名替代gate。
保存1375区间的外穿透峰值与rollout一致且低于原0.2mm，模型/终端一致，成功记录有效。
这是变化中policy的训练回合，未做额外固定checkpoint成功复现或原始子步独立重放。
第四轮随即全部失败，说明成功尚未稳定，不能称已学会或收敛；被动/主动长期在第三轮也仍失败。
第三轮失败carry22/lift5/grasp1；第四轮align12/approach11/lift2/carry5。

原科学审计2472115仍等待四路都完成cycle3，再执行统一诊断，之后继续cycle5；不重复派发。
继续原有限六周期，完整阶段只是复核边界，不是总目标步数上限。若学习不健康，须依照完整
证据另行登记修复/阶段，不以GPU占用率为由恢复大量重复更新。

## 未完成项

完整候选验证、实际整体吞吐改善、GPU50%、充分收敛、固定策略完整训练集矩阵、
最终SPT_empirical/接触舒适审计、指定ESN对照均未完成。没有新增辅助GPU训练。
physics/MJB、gate、actor信息、公共filter、执行器限制、dt及正式reward/batch/UTD未改变。
远端main=a52dfba4486af8d263d5cd0a976c3102482ff249，baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。
GitHub是否发布以实际push结果为准，不能将集群本地提交写成远端已同步。
