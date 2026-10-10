# 15小时 baseline 修正窗口收口

授权窗口：2026-10-09 21:21 至 2026-10-10 12:21（Asia/Shanghai）。计算仅在本机 airpig；每路3 GiB、禁 swap、数值线程1，服务器只做文件存储与校验。

预算保护于12:21:00.016 CST冻结旧协调器，向两个已运行训练主进程发送既有的回合边界停止信号；12:25:35 CST确认两个worker都已退出，之后才终止冻结协调器。没有派发110k之后的新节点。

## 收口结果

|接续段|实际交互|完整新增训练回合|Task|Strict|状态|
|---|---:|---:|---:|---:|---|
|direct office_task 55k|54,146|33|0|0|完整节点|
|direct office_task 110k|108,458|40|6|2|预算停止后保存|
|parameter impedance 55k|55,000|32|0|0|完整节点|
|parameter impedance 110k|104,500|36|0|0|预算停止后保存|

直接动作110k的6/40是训练身份中的Task计数；调阻抗收口为0/36。它们没有经过8个固定development身份的同节点重评，因此不能写成最终成功率，也不能直接与proposed ESN比较。55k节点的其余五个配置仍全部Task/Strict 0/8；全七配置的55k开发矩阵在收口前已完成。

## 学习机制审计

四格离线信用分配试验均完成12,002次更新、0新物理步、0 held-out/final读取：原奖励/任务安全分开奖励分别配单步/n-step=25。任务安全候选对外穿透仍使用原0.2 mm阈值，只把训练奖励拆开；actor仍canonical48，不使用接触真值、teacher或BC。它是off-policy学习消融，不能替代闭环baseline。

5.4万步直接动作critic只读诊断未修改checkpoint：replay Q与历史行为回报差值均值约6.54，终止样本Q差值均值约0.257；这是价值学习诊断，不足以单独归因失败。四格试验仍需独立closed-loop development和至少多seed确认，才可决定是否纳入baseline论文表。

## 结论与未完成项

本窗口完成本机RL有限接续、进程边界保护、物理/动作/源hash审计和奖励机制修正候选；没有获得可直接用于最终公平排名的RL策略。经典控制器充分恢复、RL多seed、所有新checkpoint的8条件development重评、统一最终矩阵仍未完成。旧384回合结果保持历史状态，不用本窗口训练身份成功回合替换它。

预算收据：本地`outputs/baseline_local_rl_20261009/budget_15h_2121/execution.json`，状态`budget_closed_review_required`，guard registration SHA `8fb5a27ff81f7388416ab6331f25b5cdb88ce23892981ba5a4f291f00dcb9e66`。
旧55k审计已核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage5/evidence/`（3091文件，12,856,965,783字节，manifest SHA `3f5465d4ee035771f03c8ec70f06ab08f80344a741eb1916f7e97676e921298d`）。

收口小型证据包（收据、四格报告、协议、条件和本报告）已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_15h_close_20261010/evidence/`
（8文件、60847字节，manifest SHA `f14b4e029cea7bf9ab4b452c2f7f2a81ec52279fd55ca7d6be51f93c8ef8d77a`）。
