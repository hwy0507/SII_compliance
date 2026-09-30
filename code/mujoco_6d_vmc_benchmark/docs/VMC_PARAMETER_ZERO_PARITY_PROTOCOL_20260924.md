# RL调参接口：同训练fixture零参数闭环一致性协议

本协议在两条物理回合前固定。目的仅验证新参数接口在从reset始终输入六维零时，与原名义VMC控制等价；不是训练模型或闭环性能改进试验，不使用验证条件选择K/D。

## 条件与两条job

仅使用teacher manifest的首个train push fixture `push_00000`，对应 `vmc_auto_search_20260920/trials/r0000_rod_04` 的原command及rollout。完整CORE_VMC_CONFIG逐项沿用，尤其显式六维stiffness_6d/damping_6d，不依赖CLI或SixDVirtualDynamics缺省值；rod_height按归档scene恢复0.65m，duration24s，seed800，push触发approach，其他参数全部沿用。机器人模型资源为服务器原menagerie。

| job | actor/controller路径 | 参数请求 | 输出 |
|---|---|---|---|
| nominal_vmc | 原panel runner，不带model，CoreTeacher直接计算 | 原显式固定K/D | 原action7 |
| zero_parameter | 独立loader→Canonical48VMCTuning | 从reset全程zero6 | 参数VMC产生action7 |

**zero6参数不等于zero7执行动作**。零参数控制器始终使用原wrench39:45，保留VMC滤波/offset/velocity状态；不改变task、reset、observer、WBC、safety或物理子步。Actor输入仅48D，无特权字段。

新adapter已要求完整显式K/D，最终冻结SHA256：`7f2cb469ed3c548f3b769be7a649b3ba21c3f921f5a31e4c3285db717376c5ea`。此前默认空options与CoreTeacher CLI fallback不等价，已由主agent修正并通过8项测试；本次使用完整config，不受该边界影响。最后一次变更仅澄清raw SI48和小offset线性化阻尼比语义，发生于本次快照/仿真启动前。

## 预声明等价白名单

必须逐元素完全相同的rollout NPZ字段：time、observation、action、teacher_force、stage、position、target、force、twist、object_position、torque、cup_shift、cup_tilt、slide_memory、cup_position、ball_position、ball_velocity。

唯一不要求A/B同名逐值相同的NPZ字段是teacher_action：A为expert真实输出；B的mixture0 policy分支固定记录zeros。必须额外验证 **A.teacher_action==B.action** 且 **B.teacher_action全0**，不能忽略真正执行的action差异。

另外必须满足：

- 两条600步/24s、observation48、执行action7；B参数记录600×6，request/logscale始终0，K/D每一步精确等于完整名义配置，记录action与原rollout相同。
- physics_states.npz所有字段、contact_samples.npz所有字段逐元素完全一致；model MJB SHA256一致。
- 结果JSON除controller、teacher_called、arguments外所有字段完全相同；arguments差异只允许output和model。A teacher_called=true，B=false；teacher.slide两者为0。
- 若任何真正动态字段不同，保存FAILED及所有原始记录，不在结果出来后扩大排除列表来强行通过。若安全提前结束，也保留但不称完成24s接口证明。

独立driver `scripts/run_vmc_parameter_parity_20260924.py` 在启动前写protocol.json及两条完整argv/env、snapshot源文件hash。独立只读source由已验证的panel source复制，新增loader、driver和已批准的新adapter；不改原物理控制脚本。两条最多2worker，与另一个agent最多2worker的contact sidecar并行，总数≤4。本机不启动仿真，避免和正在进行的潜势reward训练冲突。

服务器计划根：`outputs/vmc_parameter_parity_20260924_r1/`，结果子目录 `parity/`。完成后只有在上述预声明检验全部通过时写COMPLETE；不能把名义VMC任务本身成功/失败与“两个实现控制等价”混淆。此步骤通过也仍不代表调参RL训练完成。

启动后review发现driver的array_equal对浮点用了equal_nan=True。保持已运行snapshot不变、不中断重跑；最终验收补独立 `tools/audit_vmc_parameter_parity_20260924.py`，对全部NPZ数值数组先检查isfinite再严格array_equal。任何共同NaN/Inf都不算接口有效，最终结论必须同时具备 `FINITE_EXACT_AUDIT.json passed=true`，不能仅引用primary COMPLETE。

## 实际结果与独立审计（2026-09-24）

两条物理回合均完成24s/600步，task和accepted_panel_demo均true。主driver在最后JSON比较写入FAILED，原文件和只读source完整保留，未伪造COMPLETE也未重跑物理。差异精确限于contact.pairs两条接触对、contact.robot_bodies两个body的列表顺序反转，所有数值相同。原runner第232–235行将pairs/robot_geoms/robot_bodies/other_contacts初始化为set，第34行clean将set直接迭代为list，所以跨进程列表顺序不代表接触时间顺序或物理变化。

独立审计仅将上述四个明确set语义字段排序后比较，其他JSON动态字段继续严格相等；实际顺序有差异的只有pairs和robot_bodies。52个NPZ数值数组全部有限；全部rollout、physics_states、contact_samples数组依预声明规则逐元素完全一致；600×6参数请求/logscale全0、K/D全程精确等于名义配置。MJB共同SHA256为`9f220b70f721aba1cec9c86d53fc2e2ec748736034a47a8a9c44951684492288`。

本地完整归档 `outputs/vmc_parameter_parity_archive_20260924_r1/parity/`；其中`FINITE_EXACT_AUDIT.json passed=true`明确记录`primary_status=FAILED`及原FAILED哈希。结论是：有限原始数值与接触集合语义等价性独立审计通过，primary的严格JSON列表比较失败。本次支持零参数接口退化到名义VMC，不支持任何RL调参性能提升结论。
