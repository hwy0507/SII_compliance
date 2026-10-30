# 完整89、稳定性失败及边界诊断交接

2026-10-30 UTC，Goal active。第89轮三方法及archive/full review/固定87终端跟踪全部正常完成；原冻结88与GPU v7保持程序继续。**未收敛，90未决定、未登记、未启动，Direct34未启动。** 原训练PID3433021–3433023、archive3433024、固定终端等待4055969已正常结束，不要重启。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。前序见[89稳定性准备](RL_HISTORY89_STABILITY_READY_20261030.md)。本轮计算源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_completion_20261030_v1`；完整训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle89_20261030_v1`；准确完整checkpoint `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle89_archive_20261030_v1/<method>/cycle_00089.pt`；完整审查 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle89_review_20261030_v1`。

| 方法 | 完整steps | mean reward | Task /30 | Strict /30 | checkpoint SHA256 |
|---|---:|---:|---:|---:|---|
| impedance | 3688948 | -2.360401615823 | 18 | 17 | `b15a3229263f0e1283889b85847febf411e964b91aed05a1a57ff3c26151b68e` |
| admittance | 3691250 | -11.989807390395 | 13 | 12 | `dd711c30794b95602d685d7a1014fd9355cbb427c5ea37e90a36f4560ebc6b4d` |
| vmc | 3692250 | -4.601529770957 | 17 | 16 | `16520eb5cee4521e4986fba919d8daea6c675dc58b0fb4ebbb97262038537989` |

三方法各30×55s、41250新transition/update、0abort；旧10,948,698行全部精确保留，新总计11,072,448行。全新51维current/next、raw→mixed动作及所有reward复算误差0。原history51 critic/replay、actor49隔离、学习权重和Adam、容量4m及历史23/47标记、LR/reward/masks/terminal128/batch65536/UTD1保持。全state/恢复与前缀审计详见原89启动证据；本轮没有重复迁移。

critic首1000→末1000 mean：I1.850637334→1.906305303（max36.066699982），A1.193332950→1.292978051（max18.906759262），V.777596097→.867219645（max60.554065704）。全部loss有限但末段均值上升、尖峰仍在；actor缓慢漂移。固定早期5000结果只是前缀，不能替代完整41250记录。health/loss/训练全90配对/固定终端四张图已实际查看，各自PLOT_INSPECTION绑定hash。

完整88→89全部90条对照见 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_completion_20261030_v1/INTERPRETATION.json` 与 `training88_89_all90.png`。I mean变化+0.014952281，无Task/Strict标签变化；A−6.787970094，Task丢失short0300/long0200/long0900，Strict还丢失short0600；V−1.786483825，仅Strict丢失short0600。无新增通过条件。A/V终端reward项分别贡献−6.666666667/−1.666666667，仅算术分解，非策略因果归因。

原88—90窗口PLAN不变：seed2026102861、5000bootstrap、nearzero1、相邻5%。88→89相对变化I0.629%、A130.492%、V63.462%；A/V已经违反必要条件，任何90结果都不能逆转原窗口失败。I仍不能声称完整窗口通过。`EARLY_WINDOW_FAILURE.json`保留原PLAN/hash；没有全三周期统计、bootstrap或新替换窗口。不能为凑窗口盲目启动90。

固定原87终端跟踪 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_fixed87_terminal_followup_20261030_v1` 全部I2605/A2604/V2604行、all5/原masks/原始87 initial_control及已保存88预测保持。89恢复后0update/0physics，learner/RNG/checkpoint不变。89−88 masked SSE（critic0..4）：I[95.687190,−2782.676920,365.106803,9288.196479,2975.999834]；A[180.185950,−356.711810,80.752865,−583.498667,−106.861038]；V[−44.237431,−9.890996,6.600121,67.447710,105.707614]。相对原87，V全部5仍改善，I c3/c4及A c0/c2退化。所有critic/行保留，未晋升离线拟合权重。

`FIXED87_SSE_CONTRIBUTORS.json`精确分解所有行/5critic，top10仅解释。I c3最大退化原row195208，reward−28.35566、history .504114，Q88−27.40384→Q89+22.41979，单项SSE增加2577.24；其他几个大项也刚超过history .5。这支持研究“显式已知穿透违规标志能否更稳拟合”的假设，尚非证实根因。

新可复现 `review_boundary.py` 核验冻结adapter/evaluator源hash：raw累计外穿透≤.0002m，无额外容差，Strict还依赖Task/abort/未知边缘等门。全10,824,948原87 sidecar行及7813终端精确核对；本数据中raw>.0002与float32 history>.5分歧为0。数学反例nextafter(.0002,+∞)说明float32特征可能舍入成.5；若后续诊断新增标志，应从**动作前raw累计穿透>.0002**计算，而非舍入特征阈值。该标志不是最终Strict标签，不可泄漏未来；没有证据认为本次退化由舍入造成。保存SSE全部总和/正负数/解释行已独立复算，0新forward/update/physics。

下一步候选是单独登记有限配对离线critic拟合：准确完整89，两臂相同52维模型及新零列/零Adam矩，控制臂新增输入0，候选臂原始因果违规位；原51权重/Adam均保留，同固定87全终端/原masks/all5/三方法，有限步数，无actor/alpha/target更新、无物理、无权重推广。**目前仅候选，未登记或运行，也未实现52维正式架构。** 必须先绑定完整89与全部输入/源/预算、验证插入列51及动作列移位/初始预测/Adam/RNG；不能直接复用旧50→51迁移。

原冻结88 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1`：当前保存完成数 `{'impedance': 12, 'admittance': 12, 'vmc': 12}`，具体condition/action/物理PID及start见SAVE_SNAPSHOT。evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409原身份保持；原21600s截止，不延长/重复派发。最终全90、最终内存不变、raw审计及82→88全90配对仍待。保留所有早期失败。

原v7 supervisor97370与worker97399–97402身份保持，阈值50%、目标70%，无STOP，科学任务结束也继续运行。本轮466采样min `[66, 64, 65, 64]`%，低于50次数 `[0, 0, 0, 0]`，末值 `[76, 79, 69, 79]`%；包含合成负载，单独记录，非科研吞吐或每瞬时保证。历史v7预热0与v6 31/33/44低谷全部保留；不是重启自启服务。

本轮实际query/fetch/read main9207ff427aa1c90e6e27926dbe86c8a3943e4f0e及baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，无新远端科学改动。按sii-research-sync发布，无子agent。共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_COMPLETE89_BOUNDARY_DIAGNOSIS_20261030/SMALL_EVIDENCE.tar.gz`，118成员/7549150字节，SHA256 `1513cd1bf5cf98887f746739be2cc03431b9d94fdad03385e30f157088b474cd`；tar逐字及Python AST已核，index/commit逐字核验另见包外收据，成功push与真实ls-remote后才写PUBLICATION。大checkpoint/raw仍原SSD；HDD仅254字节原位指针，非HDD/arm1全备份。

Direct33数值接受但冻结30 Task/Strict0/0；Direct28中断缺最终内存不变证明。指定ESN仍缺失，不重复询问或替用其他主机模型。partial75、74—76不可判、79安全中止、全部失败稳定性窗口、halfstd拒绝及软件失败保持。完整reward稳定、loss健康、最终冻结评测与原ESN比较尚未完成，Goal active。
