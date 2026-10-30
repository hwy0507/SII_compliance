# 第92轮继续：原90—92稳定性完整输入与实际图绑定准备

本轮补齐原稳定性分析的图与 loss 收据来源绑定，原数值统计未运行、未改变。Goal active，三路第92轮训练及原冻结90继续；尚不能宣称 reward 平稳且 loss 健康。

实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。本轮按 `skills/sii-research-sync/SKILL.md` 实际 query/fetch/read main `3fa4b77a872875a1a1b516e2b2df92273c66396e` 与 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；两个分支没有新增科学协议。无子agent。

## 已完成的输入检查

最终来源 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_stability_ready_20261030_v1/bind_inputs.py` 与 `BINDING_PLAN.json`、原来源 diff 一同保存。实际完整90/91共六组的 protocol/review/health/finished/episodes/optimizer 引用与已发布 COMPLETE91_BINDING_REVIEW 完全一致；每组追加准确 loss_plot、health_plot、loss_review、plot_inspection、window_plan、early_window_failure 六个 hash 引用。必须存在当轮两张实际图、逐图已查看记录及正确 SHA，loss 汇总中的图 SHA 也必须一致；后续原 audit/review_saved 会检查全部输入引用。

`INPUT90_91_READY_REVIEW.json` 通过，真实缺完整92被拒绝。`PLOT_BINDING_GUARD_REVIEW.json` 的16个错误元数据案例全部被拒绝，覆盖未查看、空/缺/重复图、单图未查看、错SHA、loss汇总错SHA及错轮次。来源自身与原早期失败 hash 被锁定。builder仅是生成中间来源，最终源及diff为权威版本，含执行前追加的来源/早期失败锁。

原 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation90_92_reward_stability_20261030_v1/PLAN.json`、audit.py、review_saved.py 字节未变：90/91/92，seed2026102861，5000 bootstrap，nearzero1，相邻5%。原90→91 I42.5116001%、A20.8292134%已违反必要条件，`EARLY_WINDOW_FAILURE_91.json` 保留；V .0964836%仅一个相邻对。不得因等待完整92而抹掉失败。REGISTRATION/REVIEW仍未生成，无完整窗口统计。原 review_saved 独立复算标量，不独立重算 bootstrap 区间，此限制保持。

## 运行与GPU实测

原105进程身份连续保持 600.241秒、61次观测，三路steps均增长。保存时 steps `{'impedance': 3791337, 'admittance': 3794104, 'vmc': 3795479}`；冻结90完成数 `{'impedance': 18, 'admittance': 18, 'vmc': 17}`，每方法总30。原92 learner463617/463619/463621、archive463623；固定87终端等待器1234380；冻结90 evaluator283421/283428/283430、collector283433、postprocessor292743继续，不重启、不延长原截止。训练全92/health/loss与固定7813终端92比较、冻结全90/raw/88→90 paired及内存不变证明仍待。

GPU 121样本，四卡最低 `[77, 68, 69, 71]`%，低于50计数 `[0, 0, 0, 0]`，末样本 `[82, 91, 97, 97]`%。包括原synthetic guard的占用，不是纯科研吞吐，也不是每瞬时保证。原 `/tmp/sii_gpu_util_guard_20261030_v7` supervisor97370与四worker97399–97402继续，threshold50/target70/min duty.7；按用户要求科研完成也继续保活，不写STOP。不是重启服务。原warmup0及v6历史31/33/44低利用率记录保持。

## 后续明确入口

仅当完整92 REVIEW、FINISHED、health、loss已经完成并实际查看两张图、记录准确 PLOT_INSPECTION 后执行：

```bash
/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_stability_ready_20261030_v1/bind_inputs.py --cycle92-run /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle92_20261030_v1 --cycle92-review /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle92_review_20261030_v1
/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation90_92_reward_stability_20261030_v1/audit.py --root /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation90_92_reward_stability_20261030_v1
/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation90_92_reward_stability_20261030_v1/review_saved.py
```

随后实际查看生成统计图并保存检查结果。不得将这个准备文档当完整窗口验收；绑定脚本不会自动训练或运行统计。没有新训练派发或自动93/Direct34。

第92轮首5000的I密集critic尖峰、actor上移及V约2000尖峰簇仍保留，非健康收敛。原完整91混合结果与所有失败窗口、partial75、不可评74–76、79/90安全中止、halfstd拒绝及软件失败均保留。Direct33原数值收敛验收保持，冻结全30 Task/Strict0/0；旧28缺最终内存证明，恢复2完整不变。不能额外用task成功替代数值目标。指定ESN仍缺，不替换他机模型。

科学协议保持：冻结物理/MJB/dt5e−5/Task与Strict gate/canonical48/filter/执行器限制；每方法30×55秒、最多41250新增、append-only4m replay与23/47标记、terminal128/batch65536/UTD1及原LR/reward/masks。critic/replay52、actor49、clock49/history50/raw bit51；学习过的history/violation、Adam/RNG及双架构标记保持，不提升离线拟合权重。

## 保存与恢复

SSD小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_STABILITY_READY_20261030/SMALL_EVIDENCE.tar.gz`：59成员、1688683字节、SHA256 `6a91206b1c8bd8055b612de87839319b4b57642d53ce570b636e1a09d877fcf5`，所有tar成员逐字核验，Python AST通过。清单位于 `docs/evidence/RL_VIOLATION92_STABILITY_READY_20261030/MANIFEST.json`；发布后commit、index与blob逐字检查及实际远端核验记录在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_STABILITY_READY_20261030/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。

HDD配额满，仅原地更新现有 `sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md`，严格254字节并回读；大checkpoint/raw/replay/runtime仍在共享SSD，不是HDD或arm1全量备份。主要恢复依据 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`，本交接与前轮诊断互相衔接。
