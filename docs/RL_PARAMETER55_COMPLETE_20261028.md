# 参数55完整、原53–55统计与准确续训56（2026-10-28）

整体Goal active，继续直到reward平稳且loss没有异常。Direct已达到原训练条件下经验数值标准，不启动34；Task/Strict仍0，不等同任务成功。用户明确要求科研完成后GPU也继续保活，原v4独立运行至STOP/关机。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；实际主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮已实时查询、fetch及读取main `eca3efd48288309648270b025fe9d5377c2ceb50`和baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`的日志，无新增科学配置变化。[此前准备](RL_PARAMETER56_WINDOW_PREP_20261028.md)。没有子agent。

## 完整55结果

三路均30条件×55秒、41250新增动作、无abort；原replay全字段/history保留，reward从原物理区间journal逐条重算最大误差0，模型与优化器有限，4m容量及entry23/47双marker保持。

|方法|累计steps|累计updates|平均reward|Task/Strict（分母30）|critic首1000→末1000|critic最大|
|---|---:|---:|---:|---:|---:|---:|
|阻抗|2305398|2300399|−2.366104652|18/17|3.449113→3.177660|34.433048|
|导纳|2306000|2301001|−10.213327931|13/13|1.911840→1.279401|45.506172|
|VMC|2307000|2302001|−4.575430096|17/16|1.013950→1.023333|25.163879|

完整loss与独立保存算术通过、所有数值字段有限。阻抗actor首末1000从28.915869到30.359098，critic仍高位；VMC末段尖峰簇保留，不能以有限数值代替健康收敛。完整loss/health图已检查。

完整父审查`B/runs/parameter_capacity_pool30_cycle55_review_20261026_v1`；loss及配对gate`B/runs/parameter55_loss_20261028_v1`。归档`B/runs/parameter_capacity_pool30_cycle55_archive_20261026_v1/{method}/cycle_00055.pt`，SHA256如下：

- impedance：`f40d213a77ad737b7a3649765c8e73f59e6a83fdec6eb3a90f303fe514a90278`
- admittance：`f1542e92249691987f4553b88704fbdefb4b22a93dfd15c95cba047091ab682a`
- vmc：`bf759d9a2619338ff22e00a8144297b4a805575cc078e32790bb8505180ea2bd`

health终端inbag MAE为.326896/.240013/.213893，全终端MAE为.926200/.632547/.550966。固定min-pair、未投影的抽样TD MAE为.308138/.208297/.150550；A/V正式训练使用mean目标，不能把该诊断解释为其正式目标校准或在线loss。

54→55配对审查保留真实失败：阻抗long0000由54的593步/23.72秒全局穿透abort恢复到1375步/55秒且Task/Strict通过；global penetration98.36444mm→.180479616mm。阻抗short0100 Task原本就通过，外穿透.215793309→.183417442mm跨原0.2mm门，Strict恢复。导纳Strict新增short0300/long0300/short0200/long0200、失去long0900；VMC无Strict或abort变化。同MJB/evaluator哈希已核，不是独立物理重放或loss因果分析。

## 原53–55固定统计

`B/runs/parameter_capacity53_55_reward_stability_20261028_v1`已完成，图已检查；本轮另独立复算30条件均值/相邻及首尾变化并校验图SHA，没有重新抽bootstrap或换窗口。原seed2026102852、5000bootstrap、5%与nearzero1不变，阻抗54实际40468动作和abort全部纳入。

|方法|53→54相对变化|54→55相对变化|53→55相对变化|原5%检查|
|---|---:|---:|---:|---|
|阻抗|51.2034%|61.1748%|41.2950%|未通过|
|导纳|79.4844%|33.2500%|19.8058%|未通过|
|VMC|0.28614%|0.12978%|0.15599%|通过|

VMC reward标准明确通过；loss尾部尖峰/此前尾部抬升仍待跟踪，本轮没有作VMC整体数值阶段接受决定。I/A reward尚不稳定。Task成功率单列，不添加新的收敛门槛。下一56–58窗口在56启动前已登记，waiter788599/start36203076；它不替换本窗口，也不自动训练。

## 固定1645终端样本跟踪55

`B/runs/impedance55_terminal_anchor_followup_20261028_v1`已完成，独立保存值审查及图通过。固定原54的1645条输入、动作、reward与mask不变，masked SSE29645.016280→8845.030720，比率.2983648461，即下降70.1635%。55全1675终端population贡献.8699104515，其中旧1645为.5618722247、新30为.3080382268。用原54分母计算旧样本贡献.5721035608，避免把分母增长误作拟合改善。原54 abort行index2252691 SSE3437.822101→1698.576707，55贡献.1078832196。

该结果仅CPU冻结前向，权重/RNG不变、0优化/物理/replay写入；没有普通TD项或历史minibatch，不是总在线loss分解，也不证明后续控制性能。

## 准确56续训与冻结55评测

准确55→56 check-only三路退出0；完整learner/replay/下一65536样本恢复精确，4m与历史marker保持。原准备221126及冻结55准备3641528均正常结束，没有重启。完整55证据审查后写`B/runtime/prepare_parameter56_20261028_v1/DECISION56.json`，只批准原配置单个56，不自动57。

56于06:22:51 UTC派发，路径`B/runs/parameter_capacity_pool30_cycle56_20261026_v1`。I1869168/start36428762、A1869169/start36428763、V1869170/start36428763；归档monitor1869171/start36428763、startup1869172/start36428764。原GPU1/2/3、CPU13–25/26–38/39–51、每路30sampler、batch65536/UTD1/terminal128/上界投影/I target min及A/V target mean/actor min全部保持。实际startup审查见本文件下方补充；不能只凭check-only宣称真实启动正确。

冻结55准确恢复三路退出0、完整4m replay与learner digest通过，外部随机动作与native三动作精确；本次确为55，不以先前53恢复代替。原PLAN SHA `906bb31f23a3c63b49edc5e298407c284c81af173cd3d5f816581c4325fac986`保持，三方法各原30条件，总90回合、seed2026102638、每回合55秒，最多123750动作/99000000物理子步。只推理，0优化/replay写入。

评测路径`B/runs/parameter55_frozen_full30_20261028_v1`，I/A/V evaluator1869175/1869176/1869177（start36428775），rootreview1869178/start36428775、固定21600秒观察。CPU0/1/2、review3、全推理GPU0，CUDA_VISIBLE_DEVICES保留0,1,2,3用于恢复父CUDA RNG。完整评测结果尚待，不作成功结论；与冻结41比较时明确41的2m、55的4m差异，原训练条件评测不是未见条件泛化或容量因果证明。

## GPU与恢复入口

v4 `B/runtime/gpu_util_guard_20261028_v4/guard.py` supervisor1629438/start35566457，workers1629439–1629442/start35566468,35566468,35566469,35566469；CPU52–54，STOP不存在。刚续接即时GPU0–3为79/69/72/70%，包含独立合成负载，非训练吞吐或每瞬时永久保证。即使科研结束也保持守护；它不是跨重启系统服务。

恢复时先核原PID及/proc启动ticks、LAUNCH和实际checkpoint。不要因观察超时重启，不重新训练55/Direct34，不reset replay/optimizer/RNG或导入辅助权重。先核56实际startup与正式进度、冻结55进度；完整56后再读取review/health/loss决定下一轮。原56–58窗口不改，loss问题与所有失败保留。

## 保存范围

小证据`docs/evidence/RL_PARAMETER55_COMPLETE_20261028`含完整55审查、loss/health图、原53–55统计及独立算术、固定1645值/图、56决定/准确恢复及冻结55恢复/启动收据；MANIFEST逐来源大小/hash核验。大checkpoint/replay/raw仍在以上共享SSD路径。HDD仅更新现有LATEST入口，非HDD或arm1完整备份；共享SSD小包及实际startup补充见下。

第56轮完整loss及55→56配对审查已登记并启动：`B/runs/parameter56_loss_20261028_v1`，waiter2023556/start36455483，固定7200秒，CPU54避免占用冻结评测CPU0。基于55已验证脚本仅适配轮次、描述性历史追加56与CPU；逆变换/AST/hash审查通过，实际episode长度及30分母保持。登记发生于56启动之后，不冒充训练前预登记；不自动57，也不替代原53–55或56–58窗口。

实际56 startup最终已通过：I/A/V首批新增1000/1000/2000，分别完整保留2305398/2306000/2307000旧replay行；原optimizer配置/history/4m双marker/30MJB/每路30sampler/动作与clock映射通过，新reward重算误差0。见`stage56/ACTUAL_STARTUP_REVIEW.json`。这是首批非终端检查，不代替完整56。冻结55三路实际STARTUP_REVIEW也通过，已开始物理评测，当前进度见小证据STATUS.json。

共享SSD小包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER55_COMPLETE_20261028_062935/SMALL_EVIDENCE.tar.gz`，1243598字节、100成员（含manifest），SHA256 `8654d771bf2ec337693363a154aa98f1ec0d159e104b4b08454d770352f3c4fa`，所有成员大小/hash逐项核验。收据`RL_PARAMETER55_COMPLETE_SAVE_20261028.json`。归档时正式56已推进至2309507/2310145/2311175步，冻结55首例各800/900/800动作；GPU0–3为87/94/92/92%，包括guard。

收尾fetch发现远端新增76379853eb85f89bc7557a67e0930105cb5f76a2，已阅读其非RL特化场景纠错报告、日志及相关SPT改动；其明确不改变本RL协议。本机训练/冻结评测均使用已冻结runtime，保持原源hash。发布时正常合并并完整保留双方新交接，不将非RL旧诊断提升为正式结果。
