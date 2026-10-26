# 四接口 critic 时钟在线阶段（2026-10-26）

本轮从辅助拟合转入真实在线学习。四个独立learner已启动并越过5000 warmup；每路一张RTX4090、12个物理采样器，合计48个采样器。
不是充分收敛结果，不宣称时钟是通用修复，不修改原六轮训练或其失败记录。Goal继续active。

## 选择依据及负面证据

十二个跨周期critic进程全部正常结束：四接口×三独立初始化×两臂×50k，共120万辅助更新、0新physics、0actor更新。
复核24臂、1200诊断点、配对初始函数/采样/hash与曲线；没有推广其权重。
cycle0参与本次critic拟合，cycle1不参与；父actor/alpha此前见过cycle1，不能称完整未见条件或数据评估。

| 方法 | 无时钟cycle1终端MAE | 有时钟cycle1终端MAE | 改善seed数 |
|---|---:|---:|---:|
| direct | 81.322 | 49.061 | 3/3 |
| impedance | 57.908 | 87.011 | 0/3 |
| admittance | 183.942 | 44.849 | 3/3 |
| vmc | 160.909 | 99.770 | 2/3 |

Impedance三seed全部变差；VMC一个seed变差。Direct/Admittance虽相对改善，末段误差仍反弹。
全回放拟合此前四方法三seed均改善，跨周期对照却没有通用改善；不能把实现可用或图线稳定当科学成功。
已目视核验 `withheld_cycle_clock_diagnosis.png`。首次review脚本的partition标签替换误改配置key，读取阶段KeyError后修正；未重新训练或改实验数据。

选择**独立有限在线假设检验**：给critic提供已知剩余时长，让新回放持续覆盖全部条件；不选择性保留offline有利接口。
这是CHEQ-core适配，非reward-only原论文复现：actor直接网络输入49不变，但clock影响critic不确定性、CHEQ mixing和actor自身context。
已发表方法锚点仍为 IFAC2025 polishing-CHEQ，上游SHA `1a3c1fee3332848068afdb127c4fa33eee420418`，不是新算法优越性结论。

## 完整预检和性能候选

四接口各一个完整55s预检全部完成；全部Task/Strict真，但属于fresh bounded warmup/0updates，不能称学习成功。
逐条核验1375条replay的当前/下一时钟、终端done关闭bootstrap、原48维缩放与mixing context、raw-action混合、1375条reward、MJB/fixture/plan/dt。
每路actor49、critic50，target/online时钟新列仍零，optimizer为空，证明没有偷偷导入辅助拟合。
早停859动作保留516/1375的验证在既有四接口单元检查中通过，未把早停未来长度作为输入。

contact_math候选完整12×55s重放已独立复核1320万子步：MJB/终端/区间/子步字节相同，rollout/filter/torque数组逐值相同。
只按登记规则规范化来源路径和robot_parts集合顺序；其余数值/观测/任务/安全相同。
该验证不证明整段训练提速，也不证明策略改善。

新冻结runtime `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/source_train17_clock` 合并两个独立已验证候选：5个critic-clock相关文件+3个contact-math性能文件。
对照source16共8文件差异；保留其他源码、参数控制器、上游CHEQ、机器人资产manifest和实际内容。
physics/MJB、reward、Task/Strict gate、公共filter、执行器限制和dt不变。没有修改任何旧冻结runtime。

## 在线阶段登记与实际更新

登记 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/clock_online_control_v1/REGISTRATION.json`，完整决策 `SCIENTIFIC_DECISION.json`；同名JSON报告包含全文与SHA256。
从全新actor/critic/target/optimizer/temperature/RNG与空replay开始，不恢复预检或辅助权重。
每路6个完整30条件周期（被动/短期/长期各10），最多247500动作；合计最多7.92亿dt5e-5物理子步，55s/1375动作。
这是有限派发阶段，不是总任务步数上限或收敛判据。保留原gamma.9995、batch256、UTD1、lr3e-4、5critics、random-two target和数值修正。

四learner PID1729888/1729892/1729893/1729897，分别CPU0–12/13–25/26–38/39–51；每路12sampler+1learner。
归档1729901使用CPU52；只读周期诊断1729905使用CPU53；既有固定矩阵继续CPU54，总55核quota。
归档完整周期checkpoint，诊断周期0/1/3/5；未达到cycle时等待同一原进程，不超时重启。

四路独立6000-step快照均核验：每路1001updates、actor权重相对fresh已变化、5个critic时钟列均已学习、所有replay行时钟与逐条件动作次数精确对应。
真实模型、fixture、参考规划、dt和输入维度核验；完整optimizer/replay状态存在。不是只看PID存在宣称训练。
报告生成时进度（后续继续增长）：

| 方法 | steps | updates |
|---|---:|---:|
| direct | 14817 | 9818 |
| impedance | 13827 | 8828 |
| admittance | 14091 | 9092 |
| vmc | 13849 | 8850 |

尚无完整新周期结果，不能评估reward改善或收敛。后续必须结合周期reward、terminal校准、Q/loss漂移与冻结策略评估；保留Impedance跨周期变差的风险。

## GPU实测限制

辅助拟合结束后，正式在线阶段约60秒平均GPU0–3利用率 **6.27/5.87/6.27/6.47%**，最低0/2/0/0%，50%要求尚未达到。
测量窗口内四路都在真实更新；GPU3还含既有固定策略推理。48个CPU物理采样器推进不等于4卡满负载。
没有用辅助拟合的98–99%数字冒充在线吞吐，也没有为占用率改变live UTD/batch/physics。
此前profile指向物理采样/等待动作瓶颈；本轮只确认当前利用率，未声称新的全局因果或整体加速结论。

## 旧固定策略代表条件补充

周期3的Impedance/Admittance各三代表完整固定策略复核，learned和同接口nominal均Task/Strict2/3；被动都carry失败。
两方法共重新计算1320万归档子步（learned+nominal），learned物理/filter/torque复核通过，nominal物理/filter通过；不声称缺失扩展的nominal torque投影重放。
Impedance长期完成20.48s对nominal20.52s、峰矩51.228对52.256Nm，但实际接触舒适比例12.61%对24.07%，不能称全面改善。
Admittance短期40.80对45.28s、长期38.48对42.48s；长期实际接触两者100%阈下，峰矩51.202对54.165Nm；短期峰矩55.025对53.934Nm。
无实际人接触的被动/短期舒适比例均NA。只属三个预选条件，非最终30条件或ESN比较；不选择最终共同Tref。
VMC固定矩阵仍在途（原协调3148346），不重复启动。

## 保存与后续

实际主机 `rltest-1025--a6ed2ff39b3c-s5gnp35dxg`，主产物在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；源码snapshot、原始轨迹、checkpoint留SSD，Git仅存报告和必要小型证据。
fetch核对main64fe259、baseline f6e8f8c；未出现新的指定最终ESN。另一非RL会话的8条件/56回合计划不能替代此处30条件公平比较。
下一步继续这四路真实训练和周期0诊断，不因辅助任务结束创建无限诊断循环。收敛、最终冻结策略矩阵、SPT_empirical及指定ESN比较仍未完成。

收尾同步main6dc2b24：已读取并合并非RL示范链审计及存储受阻交接（30条原始链重放通过、25条未读）。这些是远端报告，未在本服务器重复原始数据审计。另一非RL Goal等待存储/归档授权，此处四路RL仍实际运行，不能混为本Goal受阻。在线阶段报告提交d81e531。
