# 参数56完整、VMC终端固定样本对照与准确续训57

2026-10-28，整体Goal active；reward平稳且loss无异常的原目标不变。Direct已接受训练条件下经验数值阶段，不重启34，Task/Strict0仍单列。本轮约30分钟原进程观察后，56三learner全部在完整周期结束，未因观察预算结束重启。用户要求科学工作完成后GPU仍保活，原v4继续。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；实际主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。开工已查询/fetch/read main `d50cf19bc7cae24c877a9a18556d989cb319096d`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，无新科学配置变化。[此前交接](RL_PARAMETER56_EARLY57_PREP_20261028.md)。无子agent。

## 完整56

三路各30条件×55秒、41250新增、无abort；完整旧replay全字段/history保留，reward逐条重算最大误差0，网络与优化器有限，4m与entry23/47双marker保持。完整loss全部41250数值字段、连续step、真实episode长度/均值、配对来源hash均独立复核；loss/health图已查看。

|方法|steps / updates|平均reward|Task / Strict（分母30）|critic首→末1000|全轮均值 / 最大|55→56 reward相对变化（描述性）|
|---|---:|---:|---:|---:|---:|---:|
|impedance|2346648 / 2341649|-4.037980626|17 / 16|3.063877→3.397728|2.965582 / 56.130260|70.65943%|
|admittance|2347250 / 2342251|-10.142217880|13 / 13|1.301958→1.184290|1.259369 / 9.888719|0.69625%|
|vmc|2348250 / 2343251|-2.808590365|17 / 17|1.013827→0.716591|0.865636 / 20.954407|38.61582%|

阻抗仍有高位critic和末段尖峰，actor首末1000从30.367590到30.981085。导纳本轮loss较平稳，但仅55→56均值接近不能替代连续固定窗口。VMC末1000loss回落、全轮均值.865636；56的reward因Strict恢复而明显改变。原53–55 reward5%通过的历史事实保留，但这个平台未延续到56，不宣称当前VMC整体收敛，也不删除旧通过结果。56–58窗口在56启动前已登记，仍等待57/58，seed/5%/nearzero1/5000bootstrap/全30分母不变。

归档`B/runs/parameter_capacity_pool30_cycle56_archive_20261026_v1/{method}/cycle_00056.pt`，完整审查`B/runs/parameter_capacity_pool30_cycle56_review_20261026_v1`。SHA256：

- impedance：`f6122e1c07aea3555cf5f8b5404f21c1b6f7dc9da382f11f19d71bed60812b9b`
- admittance：`547b4fbae213e334b0e902749538406bf51157a8efdc59d5a5ebba30d4f7289d`
- vmc：`2bd40601654d37f642e1acaf29ff607a26be3a57971dd6d9cfcbe8dc3eb73b4c`

health I/A/V全终端MAE1.107247/.635824/.584538、inbag MAE.531973/.250597/.274538；固定critics0/1、未投影min目标抽样TD MAE.274514/.234871/.178737。A/V训练使用mean目标，不把此诊断当正式目标校准。network状态未变。

## 配对门槛与实际任务变化

`B/runs/parameter56_loss_20261028_v1/PAIRED_GATE_REVIEW.json`保留全30配对reward。相同MJB及执行evaluator SHA核验，不是独立物理子步重放，不修改门槛。

- 阻抗long0000：55 Task/Strict成功→56均失败；56完整1375动作、无abort、外穿透.045542436mm、physical_valid仍true，不能误写成穿透abort。
- 导纳恢复long0900及short0600，失去long0200/long0300，合计Task/Strict仍13/13；short0600外穿透.211841055→.185678539mm，且Task也恢复。
- VMC short0600：Task两轮都true，外穿透.224568713→.177184360mm跨原0.2mm门，Strict恢复，回合reward−34.825205→17.937676。56全局最大穿透.201852018mm来自floor/ball，与本Strict外部穿透量不同，不能混用。

## VMC56终端出现前快照与完整56对照

`B/runs/vmc56_preterminal_followup_20261028_v1`。在56仍运行时复制独立快照`preterminal56.pt`，实际2334000步：完整保留55的2307000旧replay行，新增27000条均非终端；旧终端实际1674条。快照SHA256 `6bf838f50c30c7001ee86516ca932cc036b0e6690bd987a0aa36361f6dff1b02`，原快照保留共享SSD，不放Git或小包。

初次验证误用了阻抗旧终端1675计数而断言失败，复制已完成、正式训练未动。原快照及`INITIAL_CAPTURE_ASSERTION_FAILURE.json`保留；依据VMC55 health实际1674修正校验，逐字段比较完整父replay/history通过。没有重拍快照来选择结果。后续对照方案于56完整结束前登记、不是训练开始前预登记；绑定原learner/monitor、7200秒等待，原3413514已完成。

在完整56相同1704终端输入/动作/reward/mask上比较快照与最终critic：旧1674来自快照原replay，新30当时尚未出现，使用未来固定样本离线评估较早权重。只CPU前向，最终健康诊断MAE一致、权重/forward RNG不变、0优化/物理/replay写入；原快照全部replay前缀与最终56逐字段相同。独立保存算术和图均通过。

|固定样本组|masked SSE之前→之后|比率|统一最终分母的贡献之前→之后|
|---|---:|---:|---:|
|旧1674|1851.686757→6245.190815|3.372704|.115414932→.390187786|
|新30|134.909751→31.723724|.235148|.008418134→.001980876|
|全1704|1986.596508→6276.914539|3.159632|.123833066→.392168662|

这些贡献均固定使用最终分母，较早值是较早权重在最终样本集合上的离线值，不是当时真实在线loss。没有普通TD项或历史实际minibatch重建，不能据此作梯度因果解释。

回顾性按旧样本SSE增量排序：最大两条分别为第49和55轮`active_short_train_0600`历史失败记录，replay index2050526/2299142；终端reward约−28.42（不同于完整回合reward约−34.9）。它们的SSE增量2048.951567/2021.785292，合计占旧1674净增量4393.504058的92.6535%，主要由critic0预测分别−28.986→16.717和−35.329→17.007贡献。mask仍完整保留（第二行critic1/2为out-of-bag不计入SSE）。不删除两条失败、不重采样、不改权重，也不声称两条与新样本观测完全相同或已证明状态混叠。这使loss问题更具体，但没有宣布解决。

## 准确57与继续运行的冻结55

准确56→57 check-only三路退出0，完整learner/replay/下一65536样本与随机状态保留、4m双marker通过。完整56 loss/health/终端对照图审查后写`B/runtime/prepare_parameter57_20261028_v1/DECISION57.json`：I奖励波动/尖峰，A固定窗口未完成，V新reward变化及旧终端误差上升，因此批准原配置有限单轮57，无自动58。

57于07:24:48 UTC启动，`B/runs/parameter_capacity_pool30_cycle57_20261026_v1`，I3947388/start36800486，A3947389/V3947390/start36800487，archive3947391；startup为原launcher生成，真实通过情况见下方补充。GPU1/2/3、CPU13–25/26–38/39–51、每路30sampler、batch65536/UTD1/terminal128/上界投影/I min与A/V mean target/actor min全部保持。

完整57 loss及56→57配对审查`B/runs/parameter57_loss_20261028_v1`，waiter4039965/start36815886、CPU54、固定7200秒；源码轮次适配逆变换/AST/hash通过，57启动后登记，实际episode长度保留，不替代原56–58窗口。未来窗口788599/start36203076继续。

冻结55原I/A/V evaluator1869175/1869176/1869177及rootreview1869178身份保持，已经各6/30，完整90尚待；全推理GPU0、原seed与计划不变，不重启，不以部分回合结果宣称成功。41的2m与55的4m差异继续单列。

GPUv4原supervisor1629438、workers1629439–1629442保持；56全部退出后观察四卡仍约69–80%，含合成保活，不是训练吞吐或永久瞬时保证；用户要求科学结束也继续运行，它不是跨重启服务。

## 保存与下一步

小证据`docs/evidence/RL_PARAMETER56_COMPLETE_20261028`；大checkpoint/replay/raw以及新预终端快照仍共享SSD，非HDD/arm1完整备份。约30分钟观察窗口正常结束，未重启任何原任务；归档及实际57恢复随后正常完成。

继续原57训练和冻结55，核真实startup、完整loss/health；保持56–58固定统计及历史53–55结果。后续可跟踪上述两条历史终端，但不能用该诊断替代整体reward/loss标准或作静默训练配置修改。最新进程状态、实际startup和小包收据见下。

实际57 startup已通过：I/A/V首批新增1000/1000/2000，完整保留2346648/2347250/2348250旧replay行，原history/optimizer配置/4m双marker/30MJB/30sampler/动作clock映射保持，首批reward重算0误差；本首批不含终端，不代替完整57审查。startup3947393/start36800488已完成。

共享SSD小包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER56_COMPLETE_20261028_073630/SMALL_EVIDENCE.tar.gz`，1163737字节/77成员（含manifest），SHA256 `dcc5725ae15cf11c7409fa96e7daeb68fa31276edc2780e037b6edf187610fc9`，逐成员字节核验，收据`RL_PARAMETER56_COMPLETE_SAVE_20261028.json`。新预终端大快照不在小包中，其原路径/校验记录已保存。

发布状态快照：57 I/A/V累计2355111/2355766/2356855steps、各30sampler；冻结55分别7/8/7完整条件、下例继续。全部原身份核验，GPU80/90/95/94%包含保活。

收尾读取远端新增d43ff0ad（含cee97403非RL三场景教师资格/30身份采集）及其交接，确认其明确不改变本RL任务；本机全部训练/冻结评测使用独立已冻结runtime。正常合并双方新增日志，保留对方采集进度与本轮RL证据，不强推。
