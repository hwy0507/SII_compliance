# 阻抗39保存姿态碰撞检查与Direct26静态准备

2026-10-27 UTC。Goal active，无子agent。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。四正式Direct24/参数40保持运行；本轮没有重新训练、重跑已完成物理回合或修改正式算法/物理/gate/filter/回放。

## 新只读诊断的依据与范围

完整39阻抗long0000原记录在555动作、22.2秒触发global2mm早停，最差pair是office_v5_corner_top / target_object_geom；全局峰值99.575073mm，机器人外部峰值.075943897mm。前轮已核对保存聚合、原executed gate与MJB绑定，本轮进一步检查保存轨迹能否解释这一全局异常。

新run：B/runs/impedance39_saved_collision_20261027_v1；runtime：B/runtime/impedance39_saved_collision_20261027_v1。运行前登记成功38同条件全部1375帧及39全部555帧，10输入hash、同MJB/实际evaluator hash、CPU54/CUDA不可见、120秒上限。原timeout PID1277515已结束，未重启。

实际1930次MuJoCo3.11.0静态mj_forward，读取原25Hz qpos/qvel/ctrl/mocap及时间，不执行mj_step或其他动力学积分；0优化/replay写入。每帧记录指定pair/全局静态contact distance、物块姿态/速度和盒形分离轴间隙。只读输入/source前后hash不变；保存算术审查不调用MuJoCo、不重复前向，验证全部轨迹字段、标量、hash与图，均通过。

## 观察到的结果

| 量 | 完整38 long0000 | 完整39 long0000 |
|---|---:|---:|
| 原Task / Strict | 真 / 真 | 假 / 假 |
| 保存帧 | 1375（55秒） | 555（22.2秒） |
| 原全子步聚合全局峰值mm | .137823 | 99.575073 |
| 保存姿态静态pair峰值mm | .053540 | .067699 |
| 保存姿态pair超过2mm帧数 | 0 | 0 |
| 最大相邻保存帧位移mm | 9.151904 | 34.771378 |
| 保存物块线速度峰值m/s | .241636 | .569342 |
| 保存物块角速度峰值rad/s | 6.052013 | 19.575616 |
| 原retreat台面接触力峰值N | 9.055282 | 5864.176381 |

39最大帧间位移发生于最后22.16→22.20秒：物块移动34.771378mm，保存线速度从约5.45e−12升到.569342m/s；原retreat接触最后记录在22.16115秒。两个完整保存帧序列均没有“分离轴显示分离但静态contact显示穿透”的帧。

**静态姿态检查没有重现原99.575073mm峰值，但不能据此否定原早停或认定引擎错误。** 原极值来自50微秒子步，而姿态每40ms保存一次，中间最多800子步不可见；原高频指标只有机器人误差、twist、执行器力矩等，没有逐子步payload姿态/contact distance。现有证据支持“最后区间有明显运动突变，并伴随原聚合接触力峰值”；无法从这两帧建立准确子步顺序、接触求解根因或策略学习因果关系。

mj_forward使用独立模型/data，不恢复原运行callback/warmstart；不比较重算接触力。保存xpos可能对应积分前状态，而qpos已积分，静态重算与保存物块xpos最大差异38约10.35µm、39约26.08µm，报告保留，未错误要求逐位一致。检查没有改变原失败、reward、gate或正式模型，也不是完整动力学重放。

## Direct26静态准备完成，尚未执行恢复

新登记：B/runs/serl26_static_preparation_20261027_v1。八个脚本/模板已生成并AST与上下文检查通过：prepare/launch/setup/wait四入口，startup/review/coordinator/diagnose四模板；目录B/runtime/serl_capacity26_monitor_templates_20261027_v1。

父25→新26、准确完整父protocol/checkpoint hash守卫、旧/新均2m、历史capacity entry23与batch历史12保持，CPU0不变；完整26预期810终端，原32步目标、全旧raw/derived/history和pending审查保留。模板manifest/source差异已保存，真实launcher调用26 setup，setup仅取26冻结模板。

这仅是静态准备：没有26 waiter、CPU调度或训练进程，也未加载未来完整25父。下一步在真实25启动后登记有界等待和释放CPU调度，完整25审查后执行原check-only，再读科学结果决定有限26；不能把模板通过当成实际全状态恢复通过。正式validated capacity driver/helper没有修改，也未重复前轮容量辅助验证或原百万边界监控。

## 当前工作与限制

Direct24 learner3403962、archive3403966/review3403967；参数40 I691539/A691540/V691541、archive691544/review691545继续。原25准备3448092/调度3448355，41准备715346/调度715347，固定Direct24–26原1470790、参数39–41原3482651均沿用并核验真实存活。完整24/40、固定三轮统计和整体健康收敛尚待，不以本次只读诊断替代。

原Direct1,001,040容量边界、40实际startup、VMC固定1164跟踪39、冻结32全90及纯24/40 GPU窗口均已完成，不重启。本轮无新的GPU负载或重复固定窗口，单次利用率不是持续均值；原纯24/40均值53.5/60.3/58.0333/63.6167%及换轮/存储等待局限保留。

本轮开工真实ls-remote/fetch/read main7d69ac57974888d32f98d208f0097e7ec8f64426、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d；远端非RL97/108不是本机RL或最终ESN/SPT完成。新小证据提交，SSD归档逐成员核验；HDD配额满仅更新既有LATEST指针，非HDD/arm1全checkpoint备份。GitHub HTTPS认证失败状态未解决，不索要凭据或虚构push。
