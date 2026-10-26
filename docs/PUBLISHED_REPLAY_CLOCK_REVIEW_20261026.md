# Fresh replay时钟核验与接触候选首例完整通过

正式四路训练继续，尚未满足健康收敛和最终比较条件。本轮完成了四份第二轮checkpoint的
独立时钟/回合连续性核验，并复核接触计算候选首个完整55秒回合。没有修改正式训练。

## Replay时钟与输入连续性

读取四份已冻结cycle1 checkpoint，按照global step连接原fresh首轮和12worker恢复后的
transition日志；Impedance两轮本来就在同一run。保存实际消费的日志前缀字节数/hash，
不把仍在追加的整个日志hash当作不可变输入。逐条核对float32 reward、done、mixing context，
以及回合内next_observation与下一条observation、终端next_observation与自身observation。

总计329484条transition、240个完整结束回合全部一致，未发现回合串接或终端索引偏移。
四份checkpoint SHA与原SNAPSHOTS记录相同；观察向量仍是已登记的49维，未增加时钟输入。

时钟数组仅用于后续诊断，和正式replay分开保存：
`current_remaining_fraction=(1375-local_step)/1375`，
`next_remaining_fraction=(1375-local_step-1)/1375`。
依据是预先固定55s horizon与40ms action period，逐回合累计reward elapsed_s也已核验。
这里的reward_terms.elapsed_s是**累计回合时间**，不是单条transition长度。

Impedance首轮active_long_train_0000于859次动作/34.36s提前中止：
其terminal next_remaining_fraction保留516/1375≈0.375273，不因已知未来中止长度强制归零。
终端bootstrap仍由原done处理；重建时钟不编码未来中止时间、成功标志或接触真值。
另239个回合各1375条transition、正常结束时next_remaining_fraction为0。

初次只读v1检查错误地把上述累计elapsed字段当成每步时长，在Direct step3断言失败，
未生成任何时钟数组、未修改正式状态；FAILURE收据及原review.py保留。v2修正核验器后通过。
这是分析脚本错误，不是训练reward clock新发现的缺陷，不能写成修复了正式训练。

## 对“隐藏时钟”解释的限制

对每个终端，在同回合此前最多250条transition中寻找最近输入，使用已有缩放的观测和原始
动作坐标的L∞距离。该计算只描述当前数据，不设通过阈值，也不按距离排列方法优劣。

| 方法 | 核验transition | 终端与非终端完全相同obs / obs+action数，各60终端 | 最近obs距离中位数 | 最近obs+action距离中位数 |
|---|---:|---:|---:|---:|
| direct | 82500 | 0 / 0 | 0.060119 | 0.28785 |
| impedance | 81984 | 0 / 0 | 0.00405787 | 0.174404 |
| admittance | 82500 | 0 / 0 | 0.0178273 | 0.205457 |
| vmc | 82500 | 0 / 0 | 0.000181313 | 0.157122 |

本样本中没有完全相同的终端/非终端输入；部分参数方法的观测距离很小，但原始动作仍有差别。
连续空间中没有精确重复并不能证明Markov充分性，近邻距离也不能证明时间混叠或训练失稳的原因。
因此本轮**没有选择或训练时间条件critic**，没有将增加时间输入当作已证实的修复。
保留数据，为后续基于完整学习证据的独立假设检验提供准确的时钟与索引。
原critic loss/终端误差增大的问题仍存在，不能用时钟解释提前免责，也不能仅以终端MAE非零判失败。

产物基址：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/`。
`runs/fresh_cycle01_clock_review_v2/`含只读review.py、REVIEW.json、四个known_clock.npz；
`runs/fresh_cycle01_clock_review_v1/`保留失败。0新physics/optimizer updates，0新辅助权重。
脚本、数据、checkpoint和日志前缀hash在配套JSON及原REVIEW记录；未修改原replay/actor/learner。

## 接触计算候选首例完整通过

原协调2273688继续执行登记的12例，首例Direct/passive_corner_train_0000已完成55秒：
1375次动作、110万物理子步，Task/Strict均假，与归档参考完全一致，失败结果没有变成成功。
本轮再次只读核验MJB、journal、terminal、audit_substeps字节hash及rollout/filter/torque数组
dtype/shape/bytes，完整rollout结果仅忽略先前登记的来源/路径及显式robot_parts集合顺序差异。
实际candidate adapter、无truth、参考plan和dt5e-5均匹配。原子步对应hash：
`033c76264e5f5699b4ded862af752826b2a36917cdc33820694ffb53493fbdc3`。

收据`runs/contact_math_validation_v1/FIRST_CASE_REVIEW.json`。随后active_short首例也完整55s/110万子步精确通过，第二份收据为同目录SECOND_CASE_REVIEW.json。
原2536553已正常结束，协调自动进入active_long，child2792032继续；勿重复已完成回合。
当前2/12完整通过（合计220万子步）不代表全矩阵、整体加速、GPU50%或可部署；
剩余原登记验证继续，候选没有进入正式训练，未更改physics/MJB、gate、actor信息、公共filter、
执行器限制或dt。原训练reward/batch/UTD也保持。

原四learner和2471936/2472115/2472286继续；完整cycle3/5诊断以原观察进程结果为准。
充分训练、最终固定策略训练集矩阵、SPT_empirical、实际接触舒适审计及指定ESN比较仍未完成。
远端main=a52dfba4486af8d263d5cd0a976c3102482ff249、baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d已fetch/read；
本地commit和GitHub发布状态分别记录。
