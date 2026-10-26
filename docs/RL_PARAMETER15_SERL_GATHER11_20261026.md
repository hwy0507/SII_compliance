# 2026-10-26 参数15接续、Direct10完整审查与等价gather正式11

原Goal active，尚未健康收敛，四卡持续≥50%仍未全部达到。上一轮为实质进展；本轮开工fetch/read远端main `3d7db5a8d6c871f09b322e0f78f47dd6de521749` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。参数14已结束、GPU1–3空闲；Direct1595728及归档/审查仍live，未重启。用户要求不要让GPU长时间空闲，本轮在完整父审查和恢复gate通过后接续三参数15与Direct11。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；源码、环境、大产物均本集群SSD。仓库实际在 `B/repository/SII_compliance`，原HDD仓库路径为链接。HDD配额仍受限，仅可尝试最小交接备份，不能宣称全证据或大型权重已HDD/arm1备份。
无子agent，不干预另一主机非RL。物理/MJB/gates/filter/执行器/dt5e-5/30条件/SPT reward不变，完整正式网络/Adam/replay/RNG/history保留，不fresh reset、不回退、不推广辅助权重。

## 参数正式15：保持设置检验学习是否稳定

完整14已审查：I/A/V Task/Strict17/16、11/11、17/16，reward−4.076/−13.729/−4.559；termMAE1.297/.835/1.314、Qmean−13.366/−44.672/+19.408、末loss3.389/30.123/6.026，均非收敛。首次65536周期reward退步，而A/V值估计仍显著变化，因此登记一个**设置不变**的完整15观察学习轨迹，不宣称65536已改善任务，也不据有限probe自动无限延长。

准确父为 `B/runs/parameter_batch65536_archive_20261026_v1/{method}/cycle_00014.pt`：

- I `b6e2f84016e7423eae0202bbe2148761b640d7600312f7edc658f7eb00282500`
- A `80cb74644785e222677623541c8ac4252a466a70bcbcc6a0b04500323460382d`
- V `d41df3bbfafdbeb14eff5b65e492d6fea2c7727483e9e72e6add9bd1e9209d5a`

`B/runs/parameter_batch65536_cycle15_20261026_v1/{method}/train`：I2763218/GPU1/CPU13–25，A2763219/GPU2/CPU26–38，V2763220/GPU3/CPU39–51，各12sampler。batch65536/UTD1、I target min/A-V target mean、actor min、terminal128/target上界投影、actorLR I/V3e-4与A3e-5保持。必须pair_class恢复全部marker；只一个15，无自动16。

新driver `resume_cheq_batch65536_continuation_20261026.py` 核验最新14的cycle/health及完整checkpoint；旧13 batch probe只作为未变设置的历史依据，明确绑定上一登记的probe父，不冒充14上重新做过对照。
三check-only完整state/二次恢复/负守卫通过，0更新。真实启动审查覆盖每路至少1000新增（实际取到的snapshot见收据），全部旧replay/history/优化器配置/marker、12sampler/MJB/亲和性、参数动作/clock/reward重建误差0。
归档2860572：`parameter_batch65536_cycle15_archive_20261026_v1`；完整15只读协调2860589：`parameter_batch65536_cycle15_review_20261026_v1`。启动审查2860567已完成。

## Direct10：价值拟合明显改善，任务仍0/30

原1595728、归档1621561、审查1660936均已结束，完整10与图已审查。`B/runs/serl_multistep_cycle10_review_20261026_v1` 的REVIEW/DIAGNOSIS/FINISHED齐全：442032steps /3496264critic updates，新增41097；Task/Strict0/30，reward−32.757649，29完整55秒。
唯一短回合为 `passive_corner_train_0500`，1222动作后global penetration>2mm，停在approach，reward−39.907672；失败保留。相比9的6次160–164动作早abort，本周期次数和时机改善，但这不是安全/任务成功证明。
全41097新增单步奖励重建误差0、原400935回放前缀/history/config/clock/模型核验通过；所有41097新32步派生reward/bootstrap/endpoint/length独立精确，完整边界pending=0。

| 健康指标 | 正式9 | 正式10 |
|---|---:|---:|
| 历史terminal MAE | 1.713782 | .097123 |
| 历史terminal最大误差 | 65.252289 | 5.889130 |
| 抽样Q均值 | +27.636084 | −20.765509 |
| 固定pair 1步TD MAE | .053584 | .116139 |
| 固定pair 32步TD MAE | 未登记 | .100568 |

10的330历史terminal×10critic p95误差.254248，温度.00125217；严格新loader完整learner/optimizer/RNG只读不变。1步TD与32步训练目标不同，不能拿其较高值直接判训练异常。
仍无一个任务成功，不能因loss/Q稳定就完成Goal；多步目标仍有离策略偏差，不是当前策略回报的无偏证明。

准确最新Direct父：`B/runs/serl_multistep_cycle10_archive_20261026_v1/direct/cycle_00010.pt`，SHA `ed5790843b1fef76efb371a4ac12ceb4b9b47093fbdb73d603a0372f18f9dc54`。后续不能继续从prepared9或旧9重复训练。

## Direct正式11：只部署已验证的等价gather

PID2858708，GPU0/learnerCPU0/30sampler共享CPU1–12，`B/runs/serl_multistep_gather_cycle11_20261026_v1/direct`。从准确10完整learner及派生replay接续一个11，无自动12。
保持官方commit1fa2af7496be042e43d36120a7c8d1b71f1bfb59、10critic/随机2target/noentropy/8:1、batch32768、32步目标、actor48、clock与multistep markers、零示范/纠正/旧CHEQ/nominal混合。
使用上一轮 `serl_multistep_replay_gather_20261026.py::optimized_class` 跳过随后被派生值覆盖的单步reward/nextobs索引。上一轮28批全字段/RNG与下一完整8:1更新全state/metrics/RNG相同，已记录16critic+2actor辅助gate，**本轮没有重复执行该优化诊断填占用**。

新check-only直接在准确正式10验证完整learner、完整replay及下一32768采样批/RNG一致、合同和亲和性负守卫通过，0优化更新。
实际启动7000新增/56000critic：原442032单步和派生prefix/history/config保持，全部新动作/actor48/clock/奖励重建误差0、30MJB/真实亲和性；6070新mature与930pending逐项派生审查通过。
成熟索引按在线可用时间加入，完整10的ready顺序不必等于全局索引顺序。新独立审查器要求**完整旧ready顺序保留，排序后覆盖全部父行**，不错误要求已学习的父ready天然有序；没有改变采样器或放松覆盖/唯一性要求。
归档3078520：`serl_multistep_gather_cycle11_archive_20261026_v1`；完整11只读3078535：`serl_multistep_gather_cycle11_review_20261026_v1`，将覆盖全部新派生及360历史terminal。启动审查3078505已完成。

## 纯正式GPU窗口：仍差GPU0

`B/runs/gather11_batch15_gpu_profile_20261026_v1/PROFILE.json`：60样本64.30秒，四原learner全窗口live，冻结评估和新传输probe尚未启动。

| 方法 | GPU均值 | 新交互/s |
|---|---:|---:|
| Direct11 | **49.05%** | 23.7159 |
| I15 | 78.4167% | 25.5043 |
| A15 | 74.1333% | 25.0533 |
| V15 | 72.20% | 24.7112 |

上一纯正式窗口Direct44.53%、21.213steps/s；新窗口吞吐约提高11.8%，但不是随机同工作负载基准，不能把全部差异精确归因于gather。**49.05不能向上取整为50，四卡要求仍未全部达到。** 后续辅助/冻结推理的混合占用不能替代该正式证据。

## 新单次批量传输候选：已验证，未部署

原clock/multistep batch先传输一个随后被覆盖的1步mask，再分别传clock与32步mask。新增 `serl_multistep_batch_transfer_20261026.py::transfer_class` 直接组装最终结构后一次device_put，保留原49维/finite/clock/bootstrap检查和连续actor48叶；不改抽样、网络、优化公式或checkpoint字段。
`B/runs/serl_multistep_transfer_probe_20261026_v1` 从准确正式10：六种batch大小1/31/256/4096/32768/65536全部最终pytree精确；11个错误输入两实现均拒绝；两次完整8:1更新全state和metrics精确，共16critic+2actor辅助更新、不保存权重。原3236999已结束，勿重复。
五轮交替顺序、每臂100次同步传输，中位5.1346→4.6664ms，约减少9.1%。测量时正式11及冻结10推理并发，是受共享负载影响的微基准，不是在线吞吐或纯正式GPU达标。候选尚未部署当前11，需后续完整边界登记、恢复检查与实测。

## 既有完整周期的条件配对行为审查

`B/runs/cycle14_parameter_and_direct10_behavior_audit_20261026_v1/REVIEW.json`，0新优化/物理；三个参数各30配对条件、原journal与来源hash核验。
I13→14失去 `active_long_train_0000` Task/Strict成功；A失去short0000/0200与long0500、增加short0900；V Task成功条件不变，但short0600失去Strict，解释其reward下降。三参数被动条件均0/10，奖励差很小，主要退步来自少数主动条件。
CHEQ实际平均authority在多数类别略增加，但不能据相关性断言mixing阈值导致退步，更不能擅改阈值。
Direct9→10各30条件最终阶段全部approach；同长度前160动作的平均public0 .4323→.5837，其他六通道abs> .95占比4.36%→11.88%。public0=0是nominal，增加它减慢WBC。两周期的状态和action RNG不相同，这是描述而非干预因果结论。

## 新冻结正式10的三固定代表诊断

`B/runs/serl_cycle10_fixed_representatives_20261026_v1`，协调3165841、evaluator3166321。准确正式10，原三个固定代表passive_corner/active_short/active_long的0000；GPU0低优先级推理，learner与physics均CPU54，顺序执行，最多3×55秒/330万子步。0优化，无新nominal，不是全30最终比较。
新evaluator严格加载multistep/clock全state，actor仍48；独立动作重放构造已知当前clock，不使用未来奖励。MJB/逐子步物理/filter/torque、全部动作与最终完整state不变均由协调器登记检查。
本阶段已完成，原协调3165841/evaluator3166321均退出，FINAL_SCIENTIFIC_REVIEW passed与FINISHED齐全。三例均1375动作/110万物理子步/完整55秒，无abort，Task/Strict均0/3，全部停在approach。全部4125动作独立重放最大误差0、MJB/逐子步物理/filter/torque审查通过、完整learner/optimizer/RNG不变。平均public0分别.131383/.132899/.131383，三例无人接触，舒适比例NA。
相较冻结6仍0/3，没有任务进步；不能把训练时随机动作的平均public0与确定性冻结值当同策略分布比较。RESULTS内physical_substep_audit_completed是evaluator阶段原始false，随后独立PHYSICAL_AUDITS_COMPLETE与FINAL_SCIENTIFIC_REVIEW证明审查完成，未回写原结果。

## 后续

四正式15/11当前持续推进，完整边界归档/审查均已派发。先收完整15与11以及冻结10，重点检验任务、reward、价值与loss是否共同稳定；不以局部低误差完成目标。
后续参数必须采用最新完整正式父，Direct必须保留clock+multistep+完整派生replay，不可丢marker、回退旧权重或采样未成熟行。新批量传输优化只在完整边界经登记部署，不覆盖运行中的冻结源码。
持续每卡≥50%、健康收敛、最终完整冻结比较与ESN/SPT交付均未完成。Goal保持active。

## 发布前同步与状态快照

再次查询远端，main已推进到9dd59f2f0fb6be04fce255bd7c395b50d029d9ee，baseline保持f6e8f8c2711a93f0b5dfc88c608bd82647084d5d；读完新增非RL第八条件/最终报告入口记录后安全快进合入。未改其运行。
证据目录docs/evidence/rl_parameter15_gather11_20261026，SOURCES.json记录原SSD路径与逐文件hash；LIVE_STATUS.json记录采样时间、真实进程和训练进度。参数15最新各24/30完成；Direct11仍30条件并行，冻结10前两例已完成而第三正在approach。运行中RESULTS只作状态快照，不能冒充最终审查。

收尾冻结10三例完整审查已完成（覆盖上面的运行中时间快照），0/3且全部approach；四正式仍live。

- 最终发布61c3e3e38d79ca586328ea503517df8ccc927a5e已push并查询远端核验。107文件完整小证据包SSD B/repository/RL_PARAMETER15_GATHER11_20261026_145131/FULL_SMALL_EVIDENCE.tar.gz逐项hash验证，691350字节/SHA89d97163e5c91ffe920cf6408af70f67522e8ba0fe3b5fe75d7f7a025d78ccfb。HDD本次连17272字节最小源码包也因配额失败，仅HANDOFF/收据/LATEST入口可写；删除本次不完整副本，不宣称源码包已HDD。新FINAL_LIVE_STATUS保留收尾进度。
