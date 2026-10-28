# 参数58完整审查、原56–58统计与准确续训59

2026-10-28，Goal active。用户原目标仍为reward平稳且loss无异常。Direct已接受的经验数值阶段保持，不启动34；其Task/Strict0仍单独披露。用户要求科学工作完成后GPU也保持利用率，当前本机v5守护继续独立运行。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮实际查询/fetch/read main `e22724d455a44a17e74c334574b5a43bdf0b4204`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，fast-forward保留并行非RL冻结108准备；不修改其运行。无子agent。

## 完整58

原1846052/1846053/1846054三learner自然退出，各30×55秒、41250新增、无abort。`B/runs/parameter_capacity_pool30_cycle58_review_20261026_v1`的REVIEW/FINISHED/health通过：旧2387898/2388500/2389500行replay全字段精确保留、历史/优化器/4m双marker保持，新reward重算误差0，网络/优化器有限。reward审计重算物理interval journal，不冒称独立子步动力学积分。

|方法|steps / updates|平均reward|Task/Strict（分母30）|critic首1000→末1000|critic均值 / 最大值|
|---|---|---|---|---|---|
|阻抗|2429148 / 2424149|−4.044913633|17/16|2.937661→2.261838|2.620003 / 32.099697|
|导纳|2429750 / 2424751|−6.847756576|15/15|2.071317→1.402060|1.719277 / 46.974174|
|VMC|2430750 / 2425751|−4.541538664|17/16|0.751284→1.260509|0.827610 / 26.498606|

完整loss `B/runs/parameter58_loss_20261028_v1`：REVIEW/PAIRED_GATE_REVIEW/FINISHED及独立SAVED_REVIEW通过。三路全部41250数值字段有限、步数连续、实际长度与49–58全历史均值复算，配对来源/MJB/evaluator hash核验。loss图已实际检查：I总体下降但末段尖峰仍在，actor31.324890→30.928411；A尾段和尖峰包络下降，actor−10.057749→−10.293424；V最后约7000更新critic明显抬升，actor−14.031130→−13.835616。不能仅以有限数值宣称整体收敛。

health实际图已查看；全终端MAE I/A/V .994771505/.717090410/.619199268，in-bag .356602415/.294620200/.312874748，固定min-pair未投影TD .241474331/.250802512/.181164643，Q均值−30.660512/10.412842/13.659879。网络不变；A/V训练mean target与此诊断min target不同，不作校准证明。图标题边缘有裁切，数值与口径以完整JSON为准，未修改已登记执行源码。

归档 `B/runs/parameter_capacity_pool30_cycle58_archive_20261026_v1/{method}/cycle_00058.pt`，SHA256：

- I `3915287c94b9ca5ba737909f796299573090afb8298a28f8d402fc9e8693f398`
- A `2381a34ab518ab7fe155e1020aa0f0d1913868bd98246e8bb1be2db4c77784aa`
- V `0c3eb091982e7d72a40a8db94020a05ec620e53ca061a0b8648e5f0b53119670`

## 原57→58成功门变化

I short0100外穿透.201047→.176813mm恢复Strict；long0000失去Task/Strict但physical_valid true，无abort。A short0100/short0600分别由.208180/.205146降至.173811/.189686mm恢复Strict；long0300、short0900、long0900恢复Task/Strict，long0200失去Task/Strict但physical_valid true。V仅short0600丢Strict：Task保持true，外穿透.176717495→.221126668mm跨原.2mm门，回合reward17.931613→−34.797155；无阈值/奖励/物理修改。全部30配对保留，未独立重算接触子步。

## 原56–58稳定性窗口

`B/runs/parameter_capacity56_58_reward_stability_20261028_v1`原登记窗口完成，原源/seed2026102855/5000分层条件bootstrap/5%/nearzero1/全30及真实episode长度均保持。独立SAVED_ARITHMETIC_REVIEW复算所有均值、loss、配对差及相对标准，图实际检查；**未独立重跑bootstrap**。区间反映条件构成敏感性，不是独立训练种子或冻结策略性能。

|方法|56 / 57 / 58 reward|相邻相对变化|首尾相对变化|原5%|
|---|---|---|---|---|
|I|−4.037981 / −4.206100 / −4.044914|4.16344% / 3.83220%|0.17169%|通过|
|A|−10.142218 / −13.588546 / −6.847757|33.98002% / 49.60641%|32.48265%|未过|
|V|−2.808590 / −2.811774 / −4.541539|0.11334% / 61.51865%|61.70171%|未过|

56→58配对均值差95%条件bootstrap区间：I[−.071441,.049332]、A[−.176425,8.433544]、V[−5.275119,.064628]。明确保留阻抗本窗口reward通过，以及V原53–55曾通过事实；V56平台改变与58退化亦保留。I loss仍在改善，继续单轮观察趋势是否稳定，不引入零终端误差或Task成功新门。

## VMC全部1734旧终端对照

`B/runs/vmc58_terminal_anchor_followup_20261028_v1`原waiter完成。锚点57的1734×57输入/动作/reward/mask全部精确，完整58共1764终端；CPU冻结前向权重/RNG不变、health复现、独立保存标量复算通过，实际follow58.png已查看。登记发生于58运行中、完成前，不冒称训练前登记。初始展示标题/文件名修订保留在PRESENTATION_AMENDMENT和initial_registration，不是科学源漂移。

全部旧1734 masked SSE10684.465854→2441.892212（下降77.1454%）；旧贡献.654151367→.147199553，若沿旧分母为.149744203。新30贡献.374114301，总终端贡献.521313854。三focus SSE：2050526为187.079976→63.844565，2299142为531.454426→261.094828，前轮最大回归2046571为3853.403923→3.432177。先前旧行退化已显著改善，不隐去这一正向结果。

新增`review_new_terminals.py`对保存数组逐标量检查全部30新行，按真实total_steps−1映射回合，未重新前向。NEW_TERMINALS_REVIEW通过：short0600索引2423133贡献.317962698，占新30的84.9908%，masked SSE5275.945304；critic mask[1,0,1,1,1]，终端reward−28.415384，Q[1.036933,24.366343,3.702034,13.860041,11.456488]。第二为short0200成功行贡献.031976944。属于事后误差分布诊断，保留全30、不排除样本，不作在线minibatch/梯度因果或状态完全混叠证明。

values.npz SHA `8d99c2d3890a75856b0ddcbb49afcaeec4a943ec01e55728e25cba7a4119c27c`。

## 有限59与未来窗口

`B/runtime/prepare_parameter59_20261028_v1`原waiter完成，实际全58 learner/replay/下一65536恢复三路退出0；不是静态语法检查。DECISION59绑定18份完整证据及图、原56–58统计、新未来窗口与check-only日志，只派发单轮59，无自动60。I reward通过已明确记录，A/V不稳定、V末段loss抬升使整体目标仍未完成；不改变reward/gate/physics/LR/mask/optimizer/replay。

59运行 `B/runs/parameter_capacity_pool30_cycle59_20261026_v1`，09:33:44 UTC启动：I4084699/A4084701/V4084703，start均37574080；archive4084708/start37574081；startup4084711/start37574081。继续GPU1/2/3、CPU13–25/26–38/39–51、每路30sampler。真实startup结果与最新进度见下方收尾补充，禁止以启动本身冒称startup通过。

59完整loss `B/runs/parameter59_loss_20261028_v1` waiter4089956/start37575729，CPU54/7200秒。代码在59启动前适配并逆变换/AST/hash核验，启动后绑定实际身份；保留49–59全历史、58→59配对，独立review_saved须在FINISHED后手动执行并另看图。

未来原连续59–61窗口 `B/runs/parameter_capacity59_61_reward_stability_20261028_v1`，在59启动前登记，waiter4067967/start37570184，CPU54/14400秒；固定原seed/5%/nearzero1/5000条件bootstrap及anchor55，逐文件适配逆变换/AST通过，非结果选择窗口、不替换53–55和56–58，不自动训练或停止。尚无59–61结果，不因等待超时重启任何科学任务。

## GPU与冻结评测

当前运行守护仍为 `/tmp/sii_gpu_util_guard_20261028_v5`，共享源/归档 `B/runtime/gpu_util_guard_20261028_v5`。supervisor3256866/start37410686，workers3256867/68 start37410690、3256869/start37410691、3256870/start37410693。STOP不存在；旧v4已退出，其STOP有意保留。科学任务完成也继续运行，不是跨重启服务；完整前次停顿和60采样证据见[GPU v5交接](RL_GPU_GUARD_V5_20261028.md)，不保证所有瞬时无低谷。

原冻结55 `B/runs/parameter55_frozen_full30_20261028_v1` 三evaluator1869175/76/77及root1869178，start均36428775，继续原90回合计划与全4m状态/随机数恢复。09:34约24/23/22完整条件，未完整、不重启。41回放2m与55回放4m差异单列，不能作泛化或容量因果证明。

## 保存与继续

本轮小证据位于`docs/evidence/RL_PARAMETER58_COMPLETE_20261028`；共享SSD归档包/成员与hash见[保存收据](RL_PARAMETER58_COMPLETE_SAVE_20261028.json)。大checkpoint/replay/raw仍位于原共享SSD，非HDD/arm1全备份。现有HDD LATEST入口指向本文。下一轮核验原59及冻结55身份，完成59后审查完整loss/health与固定窗口进度再决定60，GPUv5保持运行。

## 09:39 UTC收尾实测

59真实startup/REVIEW通过：新增1000/1000/2000，旧2429148/2429750/2430750行全replay字段/history保留、原optimizer参数/4m marker/30MJB和各30sampler一致，action/clock映射及新reward重算0误差。startup原进程已完成；报告time字段是审查初始化时刻，不是完成时刻。

原59实际2432849/2433486/2434563steps，各30sampler继续；冻结55完整24/23/23、原三evaluator/root身份保持。原59 archive/loss、59–61窗口及v5五进程均PID/start核验live。GPU77/97/92/91%，包含合成保活。原58和全部58审查已完成，不重复启动。

共享SSD包`B/repository/RL_PARAMETER58_COMPLETE_20261028_093927/SMALL_EVIDENCE.tar.gz`，140成员/1630442字节，SHA256 `189a6647b27ff9e2d02e918aee0a6aeaec7dd8c1f5b8cbbb666381288bfe2dff`，所有成员字节和Python AST核验。收尾再次fetch/read main `b546441a6d142154585225f5bf2ef0687a28ac89`，为并行非RL数据/拟合前缀进展，fast-forward保留，不涉及本机RL配置。
