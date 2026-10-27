# 参数32全30冻结矩阵预登记与训练接续（2026-10-27）

Goal active。本报告接续[Direct20/参数31与冻结29完成交接](RL_PARAMETER31_FROZEN29_SEEDS_20261026.md)。上一轮已完整审查冻结29四动作seed、Direct17–19回报/loss并正式启动20，属于实质进展。本轮实际/proc与连续PROGRESS确认四原learner、原归档/review和21/32准备进程均仍live，未重启旧训练或已完成诊断。无子agent。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，实际host rltest-1025--a6ed2ff39b3c-2d5lfqki2m；仓库B/repository/SII_compliance，HDD原入口为symlink。跨UTC日期后保留原20261026 run-id，不改历史记录。

## 最新正式接续：完整31审查后32已启动

此段覆盖下方31仍运行的预登记时快照。31三路均30×55秒无abort，完整旧replay/history/2m marker保持，新增41250奖励重建0误差，网络/优化器有限；原REVIEW、health/FINISHED与图已审查。原31 learner3783467/8/9、归档3783472/review3783473、32准备3878413/调度3878414均完成退出，勿重跑。

|方法|steps / updates|Task / Strict（各30）|reward|末1000 q_loss|terminal MAE / inbag MAE|
|---|---|---|---|---|---|
|阻抗|1317000 / 1312001|18 / 16|−4.148708670|2.327977616|.890833561 / .310917918|
|导纳|1316000 / 1311001|13 / 12|−11.848439432|1.542265204|.829109499 / .412588385|
|VMC|1317000 / 1312001|17 / 16|−4.605202322|1.168400617|.651920282 / .320849825|

三末loss较30均上升，但有限且无数值发散；A/V采样必要soft-Q上界超出比例均.001123046852，不能称整体健康稳定。准确完整31父位于B/runs/parameter_capacity_pool30_cycle31_archive_20261026_v1/{method}/cycle_00031.pt：

- I ce52ed59cf87904a58c8238654eb5716dfa6d51be41fac6603bb21feadd5cedd
- A 5fe0a98d1570590aaf37c7fcfdf77668cc3dcc951f0abc3164c3fbb60e6fec8d
- V b02923c5a0c97a8060327a0a825f94fdf3960cd10307899f8c6707eaa5025229

独立保存回合配对30→31：阻抗均值−1.803523826，其中short0600 Strict真→假贡献−1.800073771；导纳均值−1.606846444，其中long0200 Task/Strict真→假贡献−1.679207643，short0600 Task假→真但Strict仍假；VMC无Task/Strict标签变化，均值−.039661751。全部90条件配对与完整均值/输入hash核验，0新物理/前向/优化；这是新30/31保存值核对，不是重跑27–29或因果分析。

三check-only精确恢复/下一65536/RNG与守卫通过。PRELAUNCH_SCIENTIFIC_REVIEW记录继续一个不变32以完成原30–32窗口的依据。2026-10-27 00:09:17 UTC正式32 I980495/A980496/V980497，B/runs/parameter_capacity_pool30_cycle32_20261026_v1；原30pool/batch65536/UTD1/terminal128/projection/pair/LR、2m历史入口23和全部正式state保持。startup980499、归档980500/review980501，先查实际启动审查；完整32预期I/V1358250、A1357250，updates=steps−4999，无自动33。

新33准备等待1007211/原32审查CPU调度1007212，只完整32后prepare+check-only。源码静态逐diff发现生成时parent断言被级联替换成33，实际prepare尚未执行、0训练；已改回准确父32并保留错误副本/初始不充分AST审查，重新核真实根/pool30/历史23/parent32/适配32审查均通过。原等待进程未重启，下一调用读取已修正脚本，不自动正式33。

新纯20/32固定60样本observer1067099已登记，仅实际32startup和四原正式GPU PID满足才采集；先查B/runs/batch20_parameter32_gpu_profile_20261027_v1/PROFILE.json，不重复/挑结果。轮次交接GPU1–3有真实空档，不用辅助推理掩盖。

## 新冻结32全矩阵：已固定预算，尚未仿真

在正式32尚未启动、完整32权重未知时，2026-10-26 23:59前固定选择完整32三参数策略和原全部30训练条件。实验B/runs/parameter32_frozen_full30_20261026_v1，冻结代码B/runtime/同名目录；PLAN SHA256 fed53352d96604d5aad339b7ad537d042040e2105646e94e1721d0448a120797。

每方法一个独立外部动作seed2026102638，按原SHA256(seed:case)映射各条件随机流；3×30×55秒、最多123750动作/99000000子步。原随机CHEQ act/context/mixing、全部物理/MJB/gate/filter/actuator/dt5e-5/canonical48/SPT reward保持，step固定在父checkpoint训练步数。没有示范、nominal混合、优化或正式replay写入；不挑条件、不追加种子/延长、不推广辅助权重。

本批补齐参数策略全30冻结覆盖，固定checkpoint不以其结果好坏重新选择。单训练seed/单外部动作seed/训练条件，非held-out、多训练seed稳健性或最终ESN/SPT比较；不会仅因完整矩阵跑完就宣称训练收敛。此前29单条件四种子与Direct16全30均已完成，不重跑。

I/A/V独立evaluator分别CPU52/53/54、GPU1/2/3，仅三个单核物理子进程，数值线程1/nice10；正式CPU0–51保持。每方法串行30回合，任务资源使用有实际验证目的，不作填GPU负载。预计与正式训练并存时GPU占用是混合窗口，必须标明。

## 源码与入口核验

新增evaluate_parameter32_frozen_full30_20261026.py，保留原29已实测ExternalActions/gate/review_episode helper的逐字节源码；新入口主要改为parent32、全部30条件和单seed循环。必须capacity replay+pair learner恢复全部正式state，2m容量/历史入口23保持，完整learner/replay digest对父，原生连续随机流与外部切换流三步逐值、异seed和非法seed守卫通过后才可评估。每回合独立原生全动作重放与物理/filter/torque审查，完整learner digest不变；全30结束再验replay/父/source。

新增review_parameter32_frozen_full30_20261026.py，等待三方法完整FINISHED，核原PID/start identity、失败、21600秒有界审查窗口；收齐90格与原证据hash，报告Task/Strict/机器违规/回报/穿透/峰矩/接触及完成时间，生成图。审计通过与物理安全通过分开，全部失败和无人接触NA保留。

两新源码AST、真实解释器--help导入、原helper字节一致、90回合预算算术核验通过。尚无完整32父，实际恢复/随机入口/物理审查均未执行，不能称新评估已通过。源差异/ENTRYPOINT_REVIEW/PLAN见小证据docs/evidence/rl_parameter32_frozen_matrix_20261027。

## 原准备句柄与后续边界

新冻结准备进程639955，B/runtime/prepare_parameter32_frozen_full30_20261026.py：固定PLAN/source hash，最多等待7200秒，只在完整32 FINISHED/REVIEW通过后生成三注册，绑定准确32父hash、原完整32训练注册/条件、gate观测；三路各执行check-only。它不自动启动物理评估。启动脚本launch_parameter32_frozen_full30_20261026.py要求完整check-only及PRELAUNCH_REVIEW，然后才开三个evaluator与根审查；当前无LAUNCH。

原正式Direct20 learner46632/归档46745/review46750，21恢复准备87882/原20CPU调度87883继续。参数31 I3783467/A3783468/V3783469、归档3783472/review3783473，32恢复准备3878413/原31CPU调度3878414继续；固定30–32稳定性2830862仍按原预算等待，不重复或自动延长。所有训练下一轮必须根据完整科学审查接续最新全state。

## 同步与剩余事项

实际query/fetch/read main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变；GitHub认证仍待、已问不重复。指定ESN仍缺，不替换旧模型。大产物在SSD，HDD只小交接/收据，非arm1/HDD全备份。总体健康收敛、参数全30冻结实际执行和最终比较仍未完成。

参数32实际启动审查已通过：I/A新增1000到1318000/1317000，V新增2000到1319000；全旧1317000/1316000/1317000 replay字段/history/优化器设置/2m marker/30MJB/30sampler、动作映射/clock及新reward0误差通过。原startup980499已退出，归档980500/完整review980501继续。

纯20/32固定窗口原1067099已完成：60样本/69.080351秒，四GPU均值56.15% / 66.9% / 65.9% / 66.45%，逐样本GPU PID恰四原正式、learner身份全程保持；保存均值独立核验通过。不是每瞬时或所有后续时段保证，换轮实际空闲保留，不重采挑结果。
