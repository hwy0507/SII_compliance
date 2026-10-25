# Bellman目标候选的可恢复训练准备与随机策略短期结果（2026-10-25）

当前仍未选择或启动下一在线CHEQ阶段。本轮完成的是source_train14候选的可恢复训练实现与真实checkpoint验证；原四路SAC09和固定策略评估继续，source13未部署。

基于前一轮有限配对诊断，候选只把Bellman目标从随机两个target critic的最小值改为全部五个的最小值。Actor仍用原随机pair，NumPy pair抽样保留；actor/critic/target权重、所有Adam moments、alpha、RNG、replay/masks、actor LR3e-5、critic LR3e-4、gamma、batch16384和UTD2均从父9精确保留。候选是算法敏感性试验，不是性能等价补丁或论文原样复现。此前结果只支持受控试验，不证明收敛或在线收益。

实现把目标规则作为checkpoint学习配置保存/恢复；旧checkpoint缺字段时仍使用原pair规则。阶段准备只添加明确的target_count=5并清空跨算法阶段的plateau聚合历史，不清空replay或优化器；原历史仍在父checkpoint。协议校验拒绝未登记规则、重复2→5变更、同时改变actorLR、奖励或受保护来源。dispatcher必须读取与候选规则一致的完整阶段科学review，准备目录里的占位review不是可执行的在线授权登记。

验证：6个阶段测试及8个既有性能续训测试通过。四个真实完整cycle9 checkpoint分别验证旧版完整state精确恢复、候选完整state精确恢复、序列化后恢复，以及恢复后一次更新与已验证离线候选在metrics及完整学习状态上的精确一致；每接口两次辅助更新，共8次。父checkpoint未改，0新physics，无辅助权重保存导入。全部source文件实测匹配manifest；相对source12仅learner adapter、trainer、Bellman helper三文件不同，parameter/robot/published manifests一致，actor输入/公共filter/执行器/physics/MJB/gate/dt未改。

冻结runtime：`BASE/runtime/source_train14`；调度与验证器：`BASE/runtime/bellman_resume_preparation_v1`；证据：`BASE/runs/bellman_resume_preparation_v1`。其中BASE为`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。CANDIDATE_PROTOCOL.json仍标明准备用途、缺最终科学decision；不得自动派发。

Direct固定cycle9随机动作评估继续。三个被动回合Task/Strict均成功；新完成的短期回合Task也是3/3，但Strict仅1/3：

| 动作seed | Task | Strict | 完成时间s | 最大外部穿透mm |
|---|---|---|---:|---:|
| 2026102541 | True | False | 38.04 | 0.212277 |
| 2026102542 | True | True | 12.68 | 0.118590 |
| 2026102543 | True | False | 18.36 | 0.223520 |

原Strict阈值为外部穿透≤0.2mm，与2mm紧急中止条件不同；两个Task成功回合因该原阈值失败，保留失败、不放宽gate。三个短期均完整110万物理子步，但原协调器要在每seed三个条件完成后进行后处理审计，因此目前仍不能称这些新回合已完成全部审计。长期结果及全部审计继续等待实际进程；不挑最好seed、不用随机结果覆盖确定性失败，不据小样本宣称稳定性或收敛。

contact读取候选现8/12完整精确通过，仍未部署；当前cycle9参数矩阵继续Admittance。最终训练收敛、全训练集SPT和指定ESN对比仍未完成。
