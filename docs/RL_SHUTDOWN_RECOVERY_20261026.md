> **已被2026-10-27最新暂停交接覆盖。先读 [RL_SHUTDOWN_RECOVERY_20261027.md](RL_SHUTDOWN_RECOVERY_20261027.md)。当前Direct已是SERL部分25，参数完整41，禁止根据本文历史“从零”叙述重置。Goal paused，等待用户重新授权恢复。**

# 用户要求关机前暂停：RL恢复交接（2026-10-26）

## 更晚更新：Direct 采用零示范 SERL 路线

用户不希望再采数据；已确认 SERL 支持纯状态、无示范从零训练。下一次默认随机初始化和空 replay，不加载示范、旧 CHEQ 权重或旧 replay，不新增人工纠正。下方先前允许已有示范的路线仅作历史备选。详见选择文档顶部澄清；不声称复现原论文20示范结果。参数 CHEQ 仍保留旧学习状态。Goal保持paused，未启动任何新计算。

## 暂停后的路线更新：Direct 选 SERL

**下次开机先读 [RL_DIRECT_SERL_SELECTION_20261026.md](RL_DIRECT_SERL_SELECTION_20261026.md)。** 用户允许参数 RL 继续 CHEQ，要求 Direct 换顶会方法，且明确“仅接受已有示范，不新增人工纠正”。已选 SERL（ICRA 2024）的 RLPD/SAC 思路作 Direct 适配来源。下文“四路 CHEQ”描述是暂停时的历史状态，不再是 Direct 自动续训指令。旧 Direct checkpoint 全部保留；新 Direct 须独立协议/初始化，不能冒充原 CHEQ continuation；参数 CHEQ 保留恢复状态。Goal 仍 paused，本次没有训练、仿真、测试或配置变更。

## 权威状态

用户明确要求暂停训练/评估，待开机回到本会话再恢复。持续Goal已通过工具置为 **paused**；不是完成，不得在用户恢复前派发任何计算。四正式learner、采样子进程、归档器与自动审查器已退出；八辅助任务在暂停信号发送前已全部正常完成。扫描/proc没有仍指向本项目SSD目录的Python任务。

暂停前已先复制原子落盘的checkpoint_latest，再给learner发送SIGINT。训练器会将KeyboardInterrupt记为FAILURE并尝试额外写checkpoint；这是用户中断，不是已证实的算法崩溃。中断可能落在优化器更新中途，所以推荐保留并核验 **checkpoint_before_interrupt.pt**，不要直接把中断后覆盖的latest当作完整更新边界。

## 恢复数据

项目仓库：`/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/SII_compliance`

SSD基础目录 B：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`

- 原训练：B/runs/cheq_clock_online_seed20261025_v1
- 暂停快照：B/runs/user_shutdown_pause_20261026_v1
- HDD独立备份：`/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1`
- 每方法子目录都有checkpoint_before_interrupt.pt与last_complete_cycle.pt。RECOVERY_MANIFEST.json记录各自SHA256/步骤/边界/字段；八文件torch.load和finite网络、replay长度核验通过，HDD复制逐hash通过。
- 正式冻结runtime：B/runtime/source_train17_clock；协议：B/runs/clock_online_control_v1/REGISTRATION.json。
- Python：B/env/bin/python；Python3.11.17，MuJoCo3.11.0；环境MUJOCO_GL=disable、OMP/OPENBLAS/MKL_NUM_THREADS=1。
- HDD frozen_dependencies保存冻结runtime、control登记/支持文件、30条件fixture/参考plan/预检MJB和JSON，逐hash清单DEPENDENCY_HASHES.json。不是整个SSD或环境/menagerie/原始轨迹备份；这些仍在原SSD路径，不得删除。
- GitHub HTTPS push一直认证失败。恢复时以本地仓库/备份为准，不能只clone远端假装拥有本地72+提交。HDD中repository.bundle另保留Git提交历史；不含大产物。

| 方法 | 推荐周期性快照steps | updates | 所处cycle索引 | 最后完整周期steps | 完整cycle索引 |
|---|---:|---:|---:|---:|---:|
| Direct | 213000 | 208001 | 5（部分） | 206250 | 4 |
| Impedance | 162000 | 157001 | 3（部分） | 122689 | 2 |
| Admittance | 161000 | 156001 | 3（部分） | 123750 | 2 |
| VMC | 162000 | 157001 | 3（部分） | 123750 | 2 |

上述推荐快照保存actor/5critic/target、优化器及moment/counter、alpha、RNG、缩放、replay及其RNG/mask。**没有MuJoCo中途物理状态**，恢复必须新开物理回合，不能宣称逐子步无缝。最新在内存的少量未落盘进度可能不包含，具体暂停前PROGRESS与保留快照差值在manifest。

当前trainer加载时一律start_cycle=checkpoint.cycle+1，即部分cycle不会补齐。这是下一次恢复必须显式处理的记账问题：采用部分快照可保留更多学习，但会出现不完整周期与编号跳过；须在新run登记保留的transition/完成条件、追加完整周期及评估矩阵，审查归档器/自动review对cycle编号的假设。不得把不完整周期算完整30条件，也不得默默回退到完整checkpoint丢掉约4万更新。完整边界快照是明确备用方案。恢复后仍应保持完整optimizer/replay/RNG，不fresh start，不导入辅助权重；先做必要的恢复验证，再按用户恢复授权继续。

## 原目标与研究合同

找到已发表、尽量忠实适配的数据驱动柔顺控制方法，在同一被动/主动短期/主动长期30条件集合将Direct/Impedance/Admittance/VMC充分训练，获得reward改善后稳定、健康优化及冻结策略验证证据，再与用户指定ESN公平比较。步数不设总上限，阶段预算/扩展须登记；不把6周期/flat reward当收敛。

采用CHEQ-core适配：CHEQ-ing the Box: Safe Variable Impedance Learning for Robotic Polishing（IFAC2025，DOI10.1016/j.ifacol.2025.10.241，arXiv2501.07985），官方源码1a3c1fee3332848068afdb127c4fa33eee420418。是有明确平台/数值改动的适配，不是reward-only逐字复现。

raw48；actor49=scaled48+own mixing context；critic/replay50额外剩余时钟，actor剥离clock。clock能通过不确定性/mixing间接作用于actor。Direct7、Impedance5、Admittance7、VMC7，公共执行动作7。5critic、Bernoulli masks、random-two target、raw action replay、nominal mixing；256x256、gamma.9995、tau.005、batch256、UTD1、lr3e-4、replay1M、LayerNorm及登记数值修正。仿真dt5e-5、servo.004、actor.04、55s/1375actions。

奖励SPT surrogate：成功/失败终端±25、完成效率最多5、PBRS5*(gamma*phi_next-phi)且终端next潜力0、非正物理代价。四路相同奖励，最终SPT_empirical按完整最终比较集合Strict成功的最短完成时刻统一取Tref；不从部分评估选Tref。舒适经验阈值[43.5]*4+[6]*3，人接触>0.05N，仅实际接触分母，无接触NA。Task/Strict、SPT、峰矩、接触舒适与机器安全均须报告，失败留分母。

物理/MJB、原Task/Strict gate、actor输入、公共filter、执行器限制及dt保持；新变化独立登记，不修改冻结runtime。用户授权4卡4090+55CPU；正式0–51，每方法12sampler+1learner，GPU0–3；52–54用于审查。不要复用旧PID判断新开机状态。用户当前暂停指令覆盖此前保持GPU占用要求。不要重启已完成辅助实验来占GPU。无子agent。

## 已有结果与未完成项

- 当前clock在线stage是fresh开始，原最多6x30条件，每方法最多247500actions；暂停时尚未跑完。完整cycle0 Task/Strict：D0/0、I18/16、A13/13、V17/16各30。完整cycle1：D0/0、I17/16、A12/11、V17/16；对应reward−32.921/−4.400/−13.797/−4.574，Qloss19.000/5.638/13.131/26.072。不能称收敛。
- Direct前四完整cycle reward−32.789/−32.921/−33.254/−33.280，无任务成功；第五完整cycle已落盘但未独立科学审查。参数方法cycle2 reward I−2.251/A−8.762/V−2.754，均未经新的完整组审查，不可替代cycle3/5审查。
- clock_cycle00_fixed_representatives_v1已移交clock_fixed_parallel_v2；12固定回合全部正常完成。Direct三例learned0/3 vsnominal2/3，均approach失败；残差与名义速度反向是描述，不是干预因果证明。
- 三参数接口三代表均learned/nominal2/3，全部被动carry失败；机器违规各0/3。Impedance长期时间20.00vs20.52s、峰46.41vs52.26Nm，但舒适13.00%vs24.07%更差。
- 本轮Admittance/VMC独立复审全部完成：各330万learned物理子步、4125actor动作重放误差0；nominal复用既有独立审查+raw hash。Admittance短期35.76vs45.28s、长期46.44vs42.48s，长期舒适均100%。VMC短期29.88s/47.25Nm、长期33.64s/46.80Nm、长期舒适100%；与nominal的完整表尚待统一汇总。
- 原固定矩阵协调器/评估器/聚合器已完，勿重启。新四方法统一固定科学汇总尚未生成。证据：runs/clock_direct_fixed_review_v1/REVIEW.json及runs/clock_parameter_fixed_review_v1/{impedance,admittance,vmc}/REVIEW.json。
- clock_cycle03_scientific_review_v1/review.py曾启动等待整组cycle3；用户暂停时停止，尚无REVIEW。原审查器1729905及归档器1729901均已停止；由于参数cycle3不完整，不能原样重启这条等待并宣称已有整组3。
- 全state恢复read-only检查runs/clock_full_state_resume_review_v2/REVIEW.json已通过，基于cycle1完整边界；它不等于本次部分边界恢复的充分验证。
- 辅助clock_temporal_return_transfer_v1首seed8臂16万更新已完整审查、图已看；记录无熵行为回报cycle0拟合/cycle1预测，parent/fresh迁移MAE D.562/.748、I6.572/7.931、A7.592/7.496、V5.872/5.579。不是SAC软Q、不是未见策略测试、不是在线学习结果。
- 新clock_temporal_return_replications_v1 seed20261027/20261028八任务全部自然完成，新增32万辅助更新；三seed共48万。仅启动核验通过，**全部三seed的最终汇总/独立检查尚未做**，先读FINISHED，不重跑。无辅助权重保存/推广。
- 当前四策略充分收敛、最终完整训练矩阵比较、最终SPT、指定ESN配对均未完成。指定ESN仍未获得，不拿历史ESN替代；此前已经问过，不反复追问。
- 最新远端main ce467b1773adeddfdfb82b8ccc424b97af23240b是另一主机25/55示范指标审计，已合并；baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。与本30条件RL矩阵区分。

## GPU 利用率目标（用户 2026-10-26 补充）

用户要求：**恢复正式训练后，GPU 利用率最好不要低于 50%，尽量充分利用已分配算力。** 这是资源效率目标，不是收敛或任务成功判据，也不是当前恢复计算的指令。

- 对参与训练的每张 GPU 记录利用率，优先看稳定训练阶段的连续 60 秒窗口均值，同时记录整体均值；区分启动、回合/周期收尾、评估和保存 checkpoint 的短暂低谷。
- 若持续低于 50%，优先排查 CPU/MuJoCo 采样、经验传输、同步等待和 learner 更新瓶颈，在已登记预算内优化并发、批处理与数据管线。改变 batch size、UTD 等学习设置时另行记录，不能仅为提高占用而静默改变算法。
- 正式训练和有研究用途的辅助任务分别报告；混合占用达到 50% 不等于正式训练达到 50%。不重复已完成任务或无界追加计算来制造占用；未达目标时如实记录实测值和瓶颈。
- 当前 Goal 仍 paused。以上要求在用户明确恢复后执行，本次不启动训练、仿真、测试、服务或辅助 GPU 任务。

## 用户恢复后执行顺序

1. 读取本文件、AGENTS、UPDATE_LOG、RECOVERY_MANIFEST；fetch/read两分支新内容，保留本地未推送提交。读取Goal状态，用户恢复授权后继续原目标，不能新建替代目标或自行称complete。
2. 检查GPU/CPU/磁盘、Python依赖、SSD及HDD备份和全部checkpoint/runtime/model/hash；确认没有旧/重复任务。HDD含关键快照和源码，不是全数据备份。
3. 审查部分checkpoint恢复语义及cycle/条件记账；优先保留所有已落盘学习状态，在独立新run恢复，新登记记录父快照hash、已完成周期、部分周期、补足评估/训练预算，不能覆盖旧run或删除STOP_REQUESTED伪装未中断。
4. 同步完成八辅助最终汇总和已完成12固定回合统一汇总，不重算已完成物理轨迹。
5. 继续正式训练并审查最新完整周期。Direct无改善需根据证据诊断探索/奖励/critic；参数方法亦需健康度与固定策略证据。不得无证据重复fresh reset，不得只靠GPU任务数声称进展。
6. 推进充分收敛、完整冻结比较、指定ESN/SPT交付；按AGENTS提交报告与日志、尝试push，认证失败如实记录且不索要私钥/token。
