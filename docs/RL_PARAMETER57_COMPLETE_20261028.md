# 参数57完整审查与准确续训58

2026-10-28，Goal active，保持用户原目标reward平稳且loss无异常；原科学契约及Direct已接受的数值阶段保持，Direct不启动34，Task/Strict0仍单独披露。用户要求科学工作完成后仍保持GPU负载，原v4继续。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。开工查询/fetch/read main `5780d89dfebb4bc96cecbbfc89ae0e4ceefc8e27`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，无新RL协议变化，无子agent。[前次交接](RL_PARAMETER57_ANCHOR58_PREP_20261028.md)。

## 完整57

三路各30条件×55秒、41250新增、无abort；旧replay全字段/history精确保留，reward重算最大误差0，网络/优化器全部有限，4m及entry23/47历史marker保持。完整loss独立算术检查所有数值有限、连续步号/真实回合长度/全历史均值及配对源hash，loss与health图均已查看。

|方法|steps / updates|平均reward|Task / Strict，分母30|critic首→末1000|全轮均值 / 最大|
|---|---:|---:|---:|---:|---:|
|impedance|2387898 / 2382899|−4.206099669|18 / 16|3.025917→2.759479|2.897149 / 44.776218|
|admittance|2388500 / 2383501|−13.588546023|13 / 11|1.399855→1.971112|1.307258 / 32.980095|
|vmc|2389500 / 2384501|−2.811773563|17 / 17|.876604→.688306|.745988 / 11.969300|

I仍有高位critic与尖峰；A尾段新大值群和均值升高、Strict下降；V在线critic降低但actor仍漂移，固定历史终端误差见下。56→57均值相对变化I约4.16%、A约33.98%、V约.11334%仅描述性，不能取代原56–58完整窗口。53–55原通过/失败事实保持，不另选窗口，不将零终端误差新增为通过门槛。

完整归档`B/runs/parameter_capacity_pool30_cycle57_archive_20261026_v1/{method}/cycle_00057.pt`，完整审查`B/runs/parameter_capacity_pool30_cycle57_review_20261026_v1`；SHA256：

- I：`896e06eaaa423855f211ae6ba1fd34697bc4874c8da05ec132558df82fd8ff20`
- A：`20b932d708c9bbc8574ff803301de864fe55f5303a0f8e91a3e0d01a58cbb998`
- V：`29f4e217a2fb3e0443cb4d40fc4a931ec703a0a49602eda8897eed46c92f76e2`

health全终端MAE I/A/V .987219/.758206/.667418，inbag .396190/.365898/.379323，固定min-pair未投影抽样TD MAE .263352/.230754/.182921，Q均值−30.800837/9.757082/13.489604；network不变。A/V训练用mean目标，此min诊断不是正式目标校准。

## 56→57配对变化

`B/runs/parameter57_loss_20261028_v1/PAIRED_GATE_REVIEW.json`保存全30 reward配对，变化样本MJB和执行evaluator hash相符，原Strict外部穿透.2mm门未改；非独立物理子步重放。

- I恢复long0000 Task/Strict；short0100 Task保持true，但外穿透.189876→.201047mm跨门导致Strict失败，合计18/16。
- A short0600与short0100 Task保持true，外穿透分别.185679→.205146mm及.180062→.208180mm，Strict失去；long0200恢复、long0900失去Task/Strict，后者physical_valid仍true、无abort。合计13/11。
- V所有Strict标签保持，short0600继续成功；总17/17。全部失败保留，三路均无abort。

## VMC全部1704固定旧终端对照

`B/runs/vmc57_terminal_anchor_followup_20261028_v1`原701140已完成，方案在57运行中、完整结束前登记，非训练前预登记。完整56固定1704输入/动作/reward/mask与57逐项一致，最终1734终端健康MAE复现；CPU只读前向、权重及forward RNG不变，零优化/物理/replay写入。NPZ独立math.fsum及图像审查通过。

旧1704 masked SSE从6276.914539到10668.293992，增加69.9608%；原贡献.392168662、按57当前分母.653160391、固定56旧分母.664766849。新增30贡献.000990976，所有终端贡献.654151367。它们是固定checkpoint/全体终端上的离线指标，不是历史在线采样loss，也不是因果分解。

此前两条历史失败index2050526/2299142的SSE分别2064.454636→187.079976、2070.640058→531.454426，显著改善；但全体旧行总误差仍增加，不能只看两条重点样本。回顾性最大新增项为index2046571、第49轮short0200成功样本，终端reward23.968563、完整回合19.173627；SSE1.920704→3853.403923，增加3851.483219，占旧全体净增量4391.379453的87.7055%。主要critic4 Q24.406975→−38.076424，mask五路均1。全数据保留，不把这一排名当选择/剔除规则或梯度因果证明。

[另一个只读输入诊断](RL_VMC56_INPUT_COMPARISON_20261028.md)检查49/55旧失败与56新成功的57维输入：canonical48差异较小但动作不同，完整输入不相同；56新成功的critic0 mask0。不能宣称严格状态混叠，也不能简单说critic0直接由该单条新终端监督拉偏。此诊断未修改配置。

## 准确58与继续评测

`B/runtime/prepare_parameter58_20261028_v1`原427130完成，实际57父全learner/replay/下一65536恢复三路退出0，4m及历史marker/原配置保持。完整57各项证据及图已审，DECISION58绑定hash，明确I尖峰、A reward/尾部loss退化、V固定旧终端误差尚未稳定，继续原配置有限单轮58以完成原56–58窗口，无自动59。

58于08:26:59 UTC启动，`B/runs/parameter_capacity_pool30_cycle58_20261026_v1`：I1846052/A1846053 start37173515，V1846054 start37173516；archive1846055/start37173517，startup1846056/start37173518。GPU1/2/3、CPU13–25/26–38/39–51，每路30sampler，batch65536/UTD1/terminal128/有限上界投影/I min与A/V mean target/actor min全部不变。真实startup已通过：I/A新增1000、V新增2000，完整父2387898/2388500/2389500回放行全字段/history/优化器超参数保持，4m历史marker/30MJB/实际各30sampler及新reward重算0误差；报告记录的time是审查进程开始时间，完成依据实际文件落盘与结果。

完整58 loss/配对审查waiter1862646/start37177502，`B/runs/parameter58_loss_20261028_v1`，CPU54/7200秒，58启动后登记；源码轮次逆变换/AST/hash通过，描述历史49–58全部保留，原53–55及56–58统计设计不变。独立保存算术脚本已准备，实际审查尚待。

冻结55原1869175/1869176/1869177、root1869178（start36428775）继续，原90完整评测尚未完成，不能从部分成功推最终结果；41的2m与55的4m差异仍单列。原56–58统计788599/start36203076继续，不能因观察截止而重启训练或重选窗口。

GPUv4原supervisor1629438/start35566457、workers1629439–1629442保持。57三路全部退出后四卡仍约69–81%，包含合成保活，不是纯训练吞吐或永久每瞬时保证，也不是跨重启服务。

## 观察异常与保存范围

本轮有界观察session19485登记1800秒，每50秒只读核验。工具在08:21:50最后输出后返回退出码143，未达到原观察截止，原因未确认；`B/runtime/observe_parameter57_completion_20261028_v1/OBSERVER_EXIT.json`保留事实，不伪称正常完成。正式57此前已正常完整退出；原archive/58恢复/终端跟踪与guard身份随后重新检查均存活并正常完成相应审查。没有因观察工具退出重启任何科学任务。

大checkpoint/replay/raw仍共享SSD。小证据和收据在本轮发布时补入，不称HDD/arm1全量备份。保持Goal active，继续原58、冻结55、原窗口及GPU守护。


## 收尾实际进度与发布证据

08:33 UTC原58三learner、archive、loss等待、冻结55三evaluator/root、原窗口与GPU守护全部PID/start核验live；58步数2391413/2392086/2393177，冻结55完整15/15/14条件，最新GPU81/89/91/93%含合成保活。真实startup已读并通过，首批检查点仍留共享SSD，不放小包。

本轮小证据`docs/evidence/RL_PARAMETER57_COMPLETE_20261028`；完整准备/57归档健康/loss与配对/终端跟踪/输入比较/58实际恢复与startup/后续loss准备及观察异常和live状态均包含。共享SSD包`B/repository/RL_PARAMETER57_COMPLETE_20261028_083425/SMALL_EVIDENCE.tar.gz`，101成员、888423字节，SHA256 `bfc840fa06220540747f9cd0e273d8131cc6f8f460b9c5e0cda686b52a09d678`，所有成员逐字节及Python AST核验。收据[RL_PARAMETER57_COMPLETE_SAVE_20261028.json](RL_PARAMETER57_COMPLETE_SAVE_20261028.json)。不含大checkpoint/replay/raw，非HDD/arm1全备份；现有HDD LATEST入口指向本文。

收尾fetch/read远端main `05fa61c95b1064d83bf05bd05047e101b8b81bc5`，包含非RL原30完整、读出修正四例和v4重采及归档；其交接明确RL不在范围。已正常fast-forward保留并行工作，当前训练使用独立冻结runtime，未改变RL配置。
