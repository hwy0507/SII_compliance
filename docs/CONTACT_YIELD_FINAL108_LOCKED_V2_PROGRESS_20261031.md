# 特化场景模型 final108 一次性比较进度

## 已锁定结果

本轮复用用户批准的 v7 公平重训，不重复执行已经完成的 75 个候选：40 条轨迹、21,500 帧，75/75 候选完成，FIT_AUDIT 通过，九个 checkpoint 已锁定。MLP 后续按相同六条 validation 和预算完成宽度容量诊断；三个 seed 均依既有 validation 规则选中宽度 384。拟合误差下降不作为闭环成功证据。

固定 27 条 train00 开发闭环已完成并经 wide-loader 独立复核：Task 27/27、Strict 24/27、actor/filter replay 27/27 精确。ESN 与 RNN 各 9/9 双成功；MLP384 为 6/9。三条失败均为 rod00 MLP384，峰外穿透 0.251768、0.243292、0.222516 mm，均超过原冻结 0.20 mm 门槛。失败 ID、回合和轨迹全部保留。人体舒适度无人体力通道，仍为 NA。

## final108 登记

新增版本化入口 `code/mujoco_6d_vmc_benchmark/experiments/evaluate_contact_yield_unseen108_locked_v2_20261031.py`，当前有效目标目录为 `code/mujoco_6d_vmc_benchmark/outputs/contact_yield_locked_unseen108_20261031_v3/`。它把 fixed27 v4 的原九模型精确绑定到冻结 12 条 unseen 条件，共 108 格；开发失败及其统计写入登记，不再作为派发门槛。该变化只允许比较预先锁定的模型，不替换模型、不改 validation 选择、不用测试结果调参。此前 v1、v2 目录仅有登记文件，因随后加强来源绑定/启动空闲检查而未执行；均保留，禁止运行。

原 final108 物理执行、Task/Strict 与机器 gate、SPT、力矩/速度审计、失败分母、条件配对、source/config/checkpoint hash 和独立复放保持不变。使用已经过 fixed27 验证的 MLP384 loader 包装器和同一物理 worker，以支持新 MLP checkpoint 格式；模型与测试条件均不变。v3 一次性登记已生成，执行 `execution.json` 尚不存在，物理回合尚未派发。启动前代码会确认选择服务和历史 final108 handoff 均 inactive，之后底层 runner仍验证资源并独占全局仿真锁。

固定开发复核结论绑定：27 行，Task 27、Strict 24，失败为三个 `rod_00__special_mlp_scratch_*_w384` 模型；所有 27 行 actor/filter replay 最大误差均为 0。正式 final108 的 SPT 以全部方法双成功的共同最短完成时间作 `T_ref`；只在 Task 与 Strict 同时成功的回合上汇总，失败仍留在成功率分母。人体舒适度仍报告 NA，扰动接触代理单列。

## 执行限制

2026-10-31 本轮容器实际 cgroup 为 `app-org.chromium.Chromium-1534058.scope`：`memory.max=max`、`memory.swap.max=max`、`cpu.max` 不可读、affinity 为 CPU 0–23。`systemctl --user` 返回 bus `Operation not permitted`，NVIDIA driver不可访问。当前环境不符合登记的 CPU6、单线程、MemoryMax 3 GiB、swap 0 资源约束，故未运行物理 episode，也未生成任何 final108 结果。向自动审批申请建立无仿真的 user-systemd 资源预检 scope 被拒，给出的理由是当前环境显式只读且 approval policy=never；按拒绝要求没有改用其他执行通道。需在获准的受限本机执行环境通过资源检查后，才可以对v3登记运行一次；基础设施失败及科学失败都须保留，不得在同一目录自动重试。

最初一次 GitHub 查询失败；随后恢复只读查询并 fetch，读取到 `main=d9507f2f319856428246018c77922a9fc1425aaf`、`baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。main 新增的 history89 RL 接口与证据更新未改本专题冻结条件、模型或登记，与本轮无冲突。本轮提交 `72d318a5a3a9cdbc94744da4b3c5964f670d3817` 已推送并从远端核验；登记 JSON 远端 SHA256 为 `e4f3b353eb45c4b672fc666154b9a90628bea604964f1e714f3ace4d9e5b88b6`。baseline 未修改。
