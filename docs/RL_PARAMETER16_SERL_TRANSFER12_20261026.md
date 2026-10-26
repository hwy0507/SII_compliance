# 2026-10-26 参数16、Direct单次批传输12与动作价值诊断

原Goal active，健康收敛与四卡持续≥50%均未完成。上一轮完成冻结10审查、发布和备份记录，属实质进展。本轮开工查询真实远端并fetch/read main `dbb1d76ed79177067c48ed49ff9f67f023c704aa`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。原参数15/Direct11及完整审查handle仍live，先等待其完整边界而未重复训练。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；本集群SSD为实际计算、环境、源码及大型训练产物位置。原HDD仓库路径是B/repository/SII_compliance的链接。HDD配额受限，上轮连17KB最小源码包都失败；不宣称HDD/arm1全量备份。

无子agent。物理/MJB/gates/filter/执行器/dt5e-5/30条件/SPT reward不改；保留全部正式网络、Adam、replay、RNG和历史，不重置、不回退、不推广辅助权重。官方SERL固定commit `1fa2af7496be042e43d36120a7c8d1b71f1bfb59`、10critic/随机2target/noentropy/8critic:1actor、canonical48/action7、零示范/纠正/nominal混合保持。

## 完整参数15：reward回升但价值仍移动

`B/runs/parameter_batch65536_cycle15_review_20261026_v1` 的完整REVIEW、health/DIAGNOSIS、FINISHED齐全，图已目视检查。三路各新增41250交互，30条件全部完整55秒、无abort，所有新reward从原journal重建误差0，旧replay全字段/history/optimizer配置/三个markers/MJB核验通过。

| 方法 | steps / updates | Task / Strict | reward | terminal MAE | Q均值 | 末1000 q_loss |
|---|---:|---:|---:|---:|---:|---:|
| 阻抗 | 657000 / 652001 | 17 / 17 | −2.227365 | 1.108246 | −10.207315 | 2.339150 |
| 导纳 | 656000 / 651001 | 13 / 13 | −10.361746 | .852945 | +1.427125 | 18.577483 |
| VMC | 657000 / 652001 | 17 / 17 | −2.855253 | 1.374519 | +23.785066 | 3.442886 |

相比14，三路reward回升，导纳成功11→13、阻抗/VMC Strict16→17；没有稳定改善的充分周期证据。A/V Q仍明显变化，I terminal最大误差93.587（需区分CHEQ刻意留出的out-of-bag行，不能把全部大误差当训练拟合异常）。后三路loss下降但尚不能宣称稳定。旧2763218/2763219/2763220、归档2860572、审查2860589均已结束，勿重启。

准确父 `B/runs/parameter_batch65536_cycle15_archive_20261026_v1/{method}/cycle_00015.pt`：

- 阻抗 `704393d07816a9e24303a47397ee8287490d4ddb62f881c5b2ea20683d8c9d52`
- 导纳 `a8ea24b96167488276c93fba6222a01fe388d114ea4ca5bd9326b6b825e26daa`
- VMC `ca5fabe1e1c605c9bc3574b7ab815cc553feed0c20d97dbbbcecfbb979c1f065`

## 参数正式16已启动并核验

`B/runs/parameter_batch65536_cycle16_20261026_v1/{method}/train`：I4072251/A4072252/V4072255，GPU1/2/3、CPU13–25/26–38/39–51各12sampler。准确15全state续一个16，保持batch65536、UTD1、terminal128、目标Q上界投影、I target minimum/A-V mean、actor minimum、原actorLR（I/V3e-4，A3e-5）。无自动17。

新driver `resume_cheq_batch65536_cycle16_20261026.py` 绑定准确15 review/health。旧batch probe来自13，仅为历史设置依据；沿已hash核验的父登记链找到原14登记绑定的13父，不冒充在15上重新对照过。三check-only完整state/重复恢复/负守卫通过、0更新。
真实启动I/A各2000、V3000新增：所有旧replay/history/config/markers完整、12MJB和实际进程亲和性、参数动作/clock/reward映射误差0。startup4140192已完。
归档4140193：`parameter_batch65536_cycle16_archive_20261026_v1`；完整16只读4140196：`parameter_batch65536_cycle16_review_20261026_v1`。必须pair_class恢复三个markers，旧loader不可替代。

## 完整Direct11：无abort、仍无任务成功

`B/runs/serl_multistep_gather_cycle11_review_20261026_v1` REVIEW/DIAGNOSIS/FINISHED与图已核验。483282steps/3826264critic，新增41250，Task/Strict0/30，reward−31.241907，30完整55秒、无abort。
全41250新单步奖励重建误差0，全部新32步reward/bootstrap/endpoints/lengths逐项精确；原442032 raw与derived前缀、旧ready顺序/history/config保留，完整边界pending0。

360历史terminal×10critic MAE.078471、p95.207200、max4.312935；抽样Q均值−20.636024，1步TD MAE.098616、32步TD MAE.068467，alpha.001119919；完整网络/optimizer/RNG只读不变。critic loss约.029→.024，Q均值只在较窄范围内移动；reward有所回升但任务0/30仍阻止健康学习完成结论。原2858708、归档3078520、审查3078535均结束。

准确父 `B/runs/serl_multistep_gather_cycle11_archive_20261026_v1/direct/cycle_00011.pt`，SHA `bd4e5de51a8e9cebe63fa7240a1e79427b1c81b1c0510be6dc51a0adee491195`。

## Direct正式12：部署等价单次传输

PID4121413，GPU0/learnerCPU0/30sampler共享1–12；`B/runs/serl_multistep_transfer_cycle12_20261026_v1/direct`，只一完整12，无自动13。仅在保留已部署gather的基础上，用 `transfer_class(SerlMultistepLearner)` 一次传输最终批结构；batch32768与算法设置全部保持。

上一有限6批pytree/11负输入/完整下一8:1更新等价probe已完成，本轮没有重复。新driver绑定其准确formal10历史父，当前恢复必须准确完整11。新check-only验证全部learner/replay/下批/RNG、该下批两种batch构造精确及负守卫，0优化。
真实启动1000新交互/8000critic：旧483282 raw/derived前缀/history/config保持、全部新actor48/action7/clock/reward误差0、30MJB/实际亲和性、184新成熟与816pending目标逐项核验通过。startup4140208已结束。
归档4140210：`serl_multistep_transfer_cycle12_archive_20261026_v1`；完整12只读4140212：`serl_multistep_transfer_cycle12_review_20261026_v1`，登记390历史terminal及全部新派生行审查。须严格保留clock/multistep markers、成熟顺序与pending，完整边界才续跑。

## 预登记180样本纯正式GPU窗口仍未达标

`B/runs/transfer12_batch16_gpu_profile_20261026_v1/PROFILE.json`：固定180样本，194.016秒，四原learner全窗口存活；窗口开始前各超过1000新交互，未与辅助更新或冻结推理混合。观察器4170654已结束，勿重复采样挑选有利窗口。

| 方法 | GPU平均 | 交互/s |
|---|---:|---:|
| Direct12 | **48.4278%** | 23.4155 |
| 阻抗16 | 75.8167% | 24.9670 |
| 导纳16 | 74.2944% | 25.5185 |
| VMC16 | 74.2778% | 25.3329 |

与上一短窗口Direct49.05%、23.7159steps/s相比，单次传输没有显示进一步在线提速，四卡≥50%仍未达到。不是严格同负载随机基准；不得拿后续混合负载补写为正式达标。

## 同状态动作价值诊断完成，不能当物理因果证据

`B/runs/serl_cycle11_action_preferences_20261026_v1/REVIEW.json`；原协调105292已结束。固定正式11最近41250行中预登记seed均匀选1024状态，比较原replay、当前mode、4个独立随机策略样本、公共全零候选、只清public0和只清其余6通道的候选。仅critic前向和动作梯度，0优化/0新物理、不保存权重；全learner/optimizer/RNG与父checkpoint不变。

官方actor优化10critic均值加entropy。mode比原replay动作Q均值高.019239，比公共全零高.031885；mode的critic间std均值.043798。把public0清零或其余通道清零分别低.010195/.027411；七个raw通道的平均绝对Q梯度约.00857–.01027。mode平均public0 .363971，其余通道abs>.95占3.60%。

这说明同状态下预测的动作价值差较小，并不证明critic校准正确，也不证明候选在物理上更优。公共0对应raw第一通道−1，增大public0减慢WBC。上述候选没有被执行、混入正式训练或作为示范。

## 有限32768/65536批量对照完成，未部署正式12

纯正式GPU0仍48.43%，登记 `B/runs/serl_cycle11_batch65536_probe_20261026_v1`，probe231521、只读review266278，CPU54/GPU0。准确完整11父，分别恢复完整learner/replay/RNG，各2000outer，总32000critic+4000actor，20个诊断点；gather/transfer/32步/官方8:1保持。

两臂等优化步数但65536抽样量为两倍，不是等数据或隔离吞吐比较；与正式12共享GPU，不作纯正式利用率证明。仅比较现有价值拟合、loss及更新成本，0新物理、不保存/推广权重、不在线改当前12。两臂均已结束，原probe231521与review266278退出，REVIEW/INDEPENDENT_REVIEW齐全、图已目视检查。每臂20点均有限，完整初始learner/replay/sampleRNG/诊断逐项相同，结束后父state/replay/checkpoint不变、不同抽样量导致sampleRNG不同已记录。

| 批量 | 末terminal MAE / max | 末32步TD MAE | Q均值 | 末100 critic loss | 排除首更新的平均outer耗时 |
|---|---:|---:|---:|---:|---:|
| 32768 | .076180 / 4.189171 | .070519 | −20.724751 | .023475 | .042698s |
| 65536 | .072278 / 3.508619 | .070815 | −20.710033 | .023212 | .114047s |

65536终端拟合略好，TD无明确改进，平均更新约2.67倍耗时；首更新65536含新shape编译101.75s，32768为3.70s，单列不当稳态吞吐。学习轨迹都有瞬时误差上升，不是收敛证明。候选仅供下一完整边界结合正式12结果决定，不修改当前12，也不把本probe当在线利用率证据。

## 冻结参数15的三代表诊断已派发

`B/runs/parameter_pair15_fixed_20261026_v1/{method}`；协调I354445/A354448/V354759，GPU1/2/3推理，CPU52/53/54、nice19。固定每类0000共9回合，最多990万子步，0优化；与原冻结11代表相同，无新nominal。I/A evaluator354447/354805已实际启动；V已在probe审查完成后启动evaluator544452，使用释放的CPU54；三个原协调器都继续运行，不重复派发。

新增 `evaluate_pair_parameter_20261026.py` 严格pair_class恢复正式15目标估计器/其余markers及完整state，显式拒绝marker缺失；运行前全state digest相同。每路原协调器负责三回合后独立物理/filter/torque/动作/clock/MJB/完整state不变审查。尚未完成，不是全30最终比较；必须核验原PID和最终REVIEW/FINISHED后再下结论。

## 后续

参数16与Direct12四正式运行，完整边界审查已派发。有限batch对照已完成，先收冻结15以及完整16/12结果；后续父必须最新完整正式checkpoint，禁止回退或引入辅助权重。
每卡持续50%、reward稳定且价值/loss健康、任务行为改善、最终完整冻结比较与ESN/SPT交付仍待。不能以局部低loss、窗口占用或有限阶段结束完成Goal。
