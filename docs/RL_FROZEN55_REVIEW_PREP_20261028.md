# 冻结55完整复核准备与原59继续

2026-10-28 10:01 UTC，Goal active。[此前59完整接续入口](RL_PARAMETER59_EARLY60_PREP_20261028.md)与[58完整结论](RL_PARAMETER58_COMPLETE_20261028.md)保持。上轮为实质进展，本轮已核验原59/冻结55继续并新增完整评测独立复核；尚不具备整体完成证据，不宣称收敛。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。开工实际查询/fetch/read main`02dc99ea69cab057f9d13ef993f890a705389098`、baseline`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，工作区干净，无新科学协议变化，沿用sii-research-sync，无子agent。

## 新独立完整复核

`B/runs/parameter41_55_frozen_comparison_20261028_v1/review_compare.py`要求41及55各完整90回合报告，逐来源hash检查、独立math.fsum均值、原Task/Strict/外穿透.2mm门、真实actions/substeps/全时长与abort、接触/扭矩/完成时间字段对照、完整learner/replay不变与零更新收据核验。小rollout/MJB/source另核验；原physical/filter/torque大raw审查保留，不冒称独立重做全部物理积分或每项子步计算。

实际`--preflight41`已对原完整41全部90回合运行通过，报告`PREFLIGHT41.json`明确仅41；不是55结果。准备时55仍在评测中，不改其原PLAN、evaluator、rootreview或预算。脚本将保留41/55每方法全30条件，逐模型与实际evaluator字节核对同条件、同seed和相同物理来源，汇总reward差及Task/Strict恢复/丢失，不挑选少数条件。

原55 `COMPARISON_LIMITATIONS.json`保持：41 replay2m、55 replay4m且训练曝光不同；同条件冻结检查点对照不是容量孤立因果、独立训练seed泛化、完整收敛或ESN最终比较。无新bootstrap或显著性声明，无新停止门。

等待程序`wait.py`绑定原55三evaluator1869175/76/77和root1869178（start均36428775），等原完整REVIEW通过且这些进程自然退出后执行独立复核。新waiter **783809/start37723293**，CPU54/固定7200秒，计划SHA`ec2e1d193120f715a7a92e34aa27015ea4d6e43f882bbf64356df806a1fbd258`，源码hash/AST/实际PID-start核验通过。原55计划SHA`906bb31f23a3c63b49edc5e298407c284c81af173cd3d5f816581c4325fac986`不变。**实际55复核和41→55结果尚待**，没有新仿真/优化/自动训练。

## 当前原任务

10:01原59 I/A/V步数2449141/2449955/2451139，各30sampler继续。原learner4084699/4084701/4084703 start37574080身份保持；原完整loss4089956、archive4084708、全1764终端等待387806、60仅恢复294526、59–61窗口4067967均沿用此前登记，无重复启动。I原56–58 reward通过、A/V未过及V59前5000高位loss事实保留，整体未收敛。Direct不启动34。

冻结55完整27/26/25，原身份继续，不因观察期限重启。当前尚无全90结果；完整原评测后先读原REVIEW/各FINISHED及新比较REVIEW/FINISHED/FAILURE，实际查看原frozen_full30_results.png，再发布完整结论。

GPUv5仍实际运行`/tmp/sii_gpu_util_guard_20261028_v5`。原supervisor3256866/start37410686、workers3256867/68 start37410690、3256869/start37410691、3256870/start37410693全部live，STOP不存在。最新76/68/95/93%含合成保活，科学完成也继续；旧v4 STOP有意保留，不是跨重启服务。此前共享等待异常继续保留，不宣称所有瞬时永久达标。

## 归档

本轮7成员小证据位于`docs/evidence/RL_FROZEN55_REVIEW_PREP_20261028`，共享SSD包`B/repository/RL_FROZEN55_REVIEW_PREP_20261028_100135/SMALL_EVIDENCE.tar.gz`，18825字节、SHA`4201e9bdf12485c5d48e6160b1e60331010e594386980859ca134511d0ffcd5d`，逐成员字节及Python AST通过。[收据](RL_FROZEN55_REVIEW_PREP_SAVE_20261028.json)。原大科学产物仍共享SSD，非HDD/arm1全备份；现有HDD LATEST入口指本文。

收尾fetch/read main `e6bd92c20a07097c6c9d0e5c8e7455e3890667e6`，新增并行非RL六指标呈现准备/来源复核并整理其历史日志位置。AGENTS/UPDATE_LOG冲突核实本机仅新增前缀后，以该原字节前缀加完整远端内容解决，保留双方进展及历史位置修正；原冻结runtime不变。
