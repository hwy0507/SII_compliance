# 时钟Direct固定策略完整复核与剩余评估并行交接

2026-10-26。开工fetch main `c3124ba322853c1e561657b58c4204ed2a64a1b6`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。
上一Goal轮完成第二周期科学审查和首个固定回合物理审查，属于实质进展。本轮继续原任务，不把阶段结束当收敛。

## 新时钟首周期Direct的三代表条件

`runs/clock_direct_fixed_review_v1/REVIEW.json`完成。冻结checkpoint为cycle0/41250steps，非最新/最终策略。
learned Task/Strict均0/3，同接口nominal均2/3；三个learned均完整55s、approach失败。

|条件|learned峰矩Nm|实际人接触s|舒适比例|nominal任务|nominal完成s|
|---|---:|---:|---|---|---:|
|passive_corner_train_0000|39.558577|0.000000|NA|False|NA|
|active_short_train_0000|37.835064|0.000000|NA|True|24.520000001264524|
|active_long_train_0000|37.835064|0.000000|NA|True|28.800000001264433|

三learned物理/filter/torque独立验证合计330万子步：首110万复用上轮完整审查并重核原始证据hash，本轮新复算后220万。
三个nominal复用旧独立物理/filter审查且重核原始hash；没有重复计作新复算，没有缺失扩展的nominal torque投影声明。
同MJB/fixture/plan/dt，raw48/actor49/critic50/common7；全部4125个确定性决策重放误差0，逐动作clock正确，全部网络参数不变、0updates。

最后10s过滤后平移残差与观察到的名义twist方向余弦约−.99847/−.99892/−.99887，全部采样方向相反。
名义速度约.052m/s、过滤残差约.076m/s；最终窗口平移误差约566/526/529mm。
这描述策略实际行为，未干预动作分量，不作因果失败归因；不能把低力矩、机器安全通过或无接触当任务成功。
无实际人接触的舒适比例全部NA；尚未选择最终Tref，三个失败的SPT对任何合法参考均为0。
此处仅三个预选代表条件，不是完整30条件或ESN比较。

## 只改变评估资源的独立交接

原矩阵协调2960898在等待Impedance evaluator3479276时被单独终止；只终止协调器，未向进程组发信号。
原Impedance evaluator及其物理child保留并核对继续运行；原Direct三回合和全部原始结果保留。
原矩阵目录新增HANDOFF_TO_PARALLEL_V2.json，禁止把旧协调器消失当失败后重启；旧PROGRESS只是交接前快照。
原登记/冻结runtime/模型/策略没有覆盖。后续权威运行状态在`runs/clock_fixed_parallel_v2`。

- Impedance：原3479276继续CPU54；只读接管审计3825230等待其完整三个回合，不重跑。
- Admittance：协调3825231/evaluator3825618，CPU52、GPU2，在新独立目录执行原尚未开始的3条件。
- VMC：协调3825232/evaluator3825634，CPU53、GPU3，同样执行原剩余3条件。
- 有限汇总3996089（CPU54/nice10）等三slot完成后，加原Direct3行，核对四方法×三条件完整且无重复；不新派发或重启physics。

总预算仍为原12×55s，不增加条件或额外回合；并行后尚新派发6回合属于原剩余计划。正式在线CPU0–51/配置不动。
三个预留核承载最多三个评估sampler；原归档/只读诊断也共享这些预留核。调度异步时间可变化，不声称正式训练轨迹逐位不变或已有整体提速证明。
新接管工具`adopt_interim_evaluation_20261026.py`只等原子进程并补完整审计；`aggregate_interim_handoff_20261026.py`只汇总完整行，保留缺失/失败错误。
源码冻结至runtime/clock_fixed_parallel_v2，逐slot登记和根登记包含输入hash，原始登记不重写。

启动复核的第一次断言把learner当作占整个13核组，实际trainer一直只把learner绑定该组首核（0/13/26/39），其余核用于sampler。
失败脚本/收据保留，修正只读核验器后通过，未改变任何训练亲和性。
Admittance/VMC各100动作重放误差0、clock/输入/模型/dt核验；原Imp进程继续live。仅启动验证，完整回合审查未完成。

## 原在线训练与未完成事项

四原learner1729888/1729892/1729893/1729897与归档1729901、审计1729905继续原六周期。
Direct的CYCLES日志已记录cycle2平均reward−33.253961、Strict0/30；该新周期尚未在此报告作完整checkpoint/终端审查，不作收敛结论。
下一统一审计仍cycle3/5。当前充分收敛、完整30条件固定比较、最终SPT与指定ESN比较都未完成；GPU50%仍未解决。
本轮没有更改physics/MJB、gate、actor输入、公共filter、执行器限制、dt或live learner目标/优化设置。
本集群主产物`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；Git仅含源码和小型证据，无其他主机归档声明。
