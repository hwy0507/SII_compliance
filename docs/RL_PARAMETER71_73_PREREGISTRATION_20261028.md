# 条件性71–73固定稳定性窗口前瞻登记

2026-10-28。当前原70三路仍在运行、完整70/原68–70结论尚未产生，71/72/73均未训练。Goal active。当前执行仍以[70交接](RL_PARAMETER70_EARLY_LOSS_WAIT_20261028.md)和[终端/恢复计划](RL_PARAMETER70_ANCHOR_FOLLOWUPS_20261028.md)为准。

登记位置`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_capacity71_73_reward_stability_20261028_v1/PLAN.json`，SHA256 `c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf`。连续非重叠的下一窗口固定[71,72,73]，仅在70完整审查后仍需续训时适用；并不授权自动训练或停止。新waiter尚未启动，须经科学审查并真实启动71后才可开始固定14400秒观察，不能提前消耗其等待预算。

原公式、相邻与首尾5%、near-zero guard1、bootstrap seed2026102855、5000重采样、anchor55协议、4m容量标记、CPU54和输入审计全部保持。三个脚本仅同时68→71/69→72/70→73映射，保护完整SHA字面量，逆变换与AST/diff/hash逐一通过。全部anchor55注册hash重验。

原68–70 PLAN仍为`e3a50567b669cb5a8a37ca9aefbca4efcb84ae39d4549af2fc720a99420e95bf`，原等待1085142/start41039557保持；必须完整报告其结果，不能被新窗口替代。65–67、62–64、59–61失败与历史通过全部保留，不选择有利端点或增加科学阈值。新计划包含登记时实际70进度，无71–73数据或通过结论。

当前原70完成边界观察器2091343/start42028788，`runtime/parameter70_completion_observation_20261028_v1/`，1200秒/30秒间隔，后台独立于工具会话；这是有限观察器，不是训练调度器。观察结束不意味着原科学结束，也不构成重启理由。原guard3256866及四workers继续；科学全部完成也保载，当前非重启自启服务。

本次source/PLAN/小证据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER71_73_PREREGISTRATION_20261028_220141/PLAN_EVIDENCE.tar.gz`，9成员/8517字节，SHA `57390f3919d23e756ea2047c6378e5ffe7e8c6b2255bf13427c1a02990d9b5a2`，成员逐字节/AST核验。见[收据](RL_PARAMETER71_73_PREREGISTRATION_SAVE_20261028.json)。大数据仍共享SSD，无HDD/arm1全备份。

开工fetch/read main0be97cc8/baselinef6e8f8c，保留独立非RL工作；冻结RL源/环境/物理/gate未变。遵循仓库sii-research-sync，无子agent。
