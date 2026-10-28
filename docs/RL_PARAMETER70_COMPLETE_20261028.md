# 完整第70轮、原68–70窗口与准确接续第71轮

2026-10-28 22:30:12 UTC，Goal active。实际主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD根`B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，正式解释器`B/env/bin/python`。本轮完成完整70审查、原68–70稳定性复核和准确有限71接续，属于progress。

## 完整70结果

原I/A/V三learner均自然结束，各30×55秒、41250新增/noabort，最终steps2924148/2924750/2925750。全部旧69 replay字段/history保持，新reward从冻结物理interval日志逐项重建最大误差0（不是独立原始子步物理重积分），网络/优化器有限。4m append replay及23/47历史标记保持。

全41250 optimizer记录连续/全字段有限，独立保存算术与实际loss/health图通过。

|方法|mean reward|Task/Strict（各30）|critic首→末1000|critic最大值|actor首→末1000|
|---|---:|---|---|---:|---|
|impedance|-0.570128980|18/18|1.886107→2.154869|17.623672|26.360863→26.369198|
|admittance|-6.801950887|16/15|1.174038→1.382074|25.071531|-8.978687→-8.766879|
|vmc|-4.596284873|17/16|0.987459→1.069618|24.854301|-13.006910→-12.947243|

完整图显示I critic波动且末段上升，actor中段升后回落接近起点；A/V末段critic有限尖峰保留，actor持续变化。前5000与中途前缀检查不能替代全轮。尚未整体收敛。

全180标签/90reward对独立核验：I/V标签不变；A long0900恢复TaskStrict，但short0600仍Task真、外穿透.203332713mm超过原.2mm而丢Strict（69为.189866344mm）。A均值变化较小是改善和退化同时存在，不证明条件行为稳定。I/A/V physical-valid30/29/29（各30），没有Task-only遗漏；V short0600仍失Strict。所有原门和失败保持。

## 原68–70固定窗口

原PLANe3a50567、端点、5%、近零1、seed2026102855、5000bootstrap、anchor55保持；REVIEW、独立SAVED_ARITHMETIC_REVIEW与实际图已审。未重跑bootstrap，独立算术不冒充独立bootstrap区间复算。

|方法|68→69→70均值|相邻变化|首尾变化|原描述检查|
|---|---|---|---|---|
|I|−4.020220→−.603698→−.570129|绝对3.416522/.033569，触发近零保护|绝对3.450091|未过|
|A|−8.521150→−6.863821→−6.801951|19.449594%/.901394%|20.175671%|未过|
|V|−4.604088→−4.620539→−4.596285|.357310%/.524923%|.169488%|描述性reward通过|

不能用A最后一对小变化替代完整窗口，也不能把V的reward通过当整体healthy convergence。保留原65–67 I/A失败/V通过和所有更早历史，不以新窗口替换旧失败。

## 完整2094旧终端对比

V/A原全部2094终端特征、动作、reward、mask精确，完整70另新增30（合计2124）。两份SAVED_VALUES_REVIEW独立数组/标量复核和实际图通过，0新物理/优化/回放写入，网络/RNG保持。

- V旧终端masked SSE4074.470065→3907.730986（−4.092289%）；原focus2050526 120.416201→22.919670改善，另四focus2299142/2046571/2423133/2423122分别1.521068→2.826301、1.012127→1.157100、1.996398→4.757417、.318113→12.511053退化。新30贡献.344596664高于旧2094贡献.195668708，全体.540265372；旧分母对照.198456192保留。V图近原点部分focus标签重叠，精确值由保存数组/JSON核验。
- A旧终端SSE1244.926690→2183.538874（+75.394976%），原66short0600/index2752093 55.213166→69.519956退化。新30贡献.318841092、旧2094 .109325742，全体.428166834；旧分母对照.110884716保留。原focus指66旧终端，不混同本轮70 short0600的新失败。

全部改善与退化保留，不以focus替代全体、不新增零误差门、不作梯度或因果解释。

## 准确接续71与后续任务

准确70 fullstate/replay/下一65536三路check-only exit0，学习率/mask/terminal128/batch65536/UTD1/reward/physics/gate不变。`runtime/prepare_parameter71_20261028_v1/DECISION71.json`绑定46项证据，SHA cdb67f8bd7baaebc5d4f6251495008b857cc926971a2955a75fea6b79676fa8f。

22:25:14启动有限71：I2902207、A2902208、V2902211同start42203070；archive2902216、startup2902218/start42203071。没有自动72。Direct33仍为原训练条件经验数值收敛、Task/Strict0/0，不启动34。

71完整loss2909138/start42204909，PLAN000ce694；原71–73固定窗口2909145/start42204920，PLANc160b5d6。71–73登记及提交03268f6c早于71训练，实际71身份/决策hash再次核验后才启动14400秒等待；原68–70现已全报告，窗口阈值不变。

实际71 startup已通过：impedance新增1000至2925148，旧2924148行精确, admittance新增1000至2925750，旧2924750行精确, vmc新增2000至2927750，旧2925750行精确。优化器/history/30模型/sampler/action/clock及新reward重建误差0全部通过；实际startup不同于先前check-only。

22:30:12三learner原身份live，steps2927133/2927747/2928729；全71loss与原71–73等待保持。71全标签/新终端基准与72仅恢复尚未准备，须后续继续，勿重复70已完成审查或旧learner。

## 连续观察与GPU保载

原70完成边界observer2091343/start42028788自然完成固定1200.544秒/41样本，FINISHED明确all_science_ready=false；仅观察结束，三路随后全部自然完成并完成归档/审查，没有重启科学。逐次live/FINISHED、进度、等待器与guard身份记录在`runtime/parameter70_completion_observation_20261028_v1`。中途约3.4万条optimizer记录全数值有限/连续，原字节前缀hash/边界/末1000算术另复核；该在途结果非完整70替代。

本轮从观察开始至71实际startup后，共398条guard采样，min55/61/64/57%、低于50[0, 0, 0, 0]，最大采样间隔5.319369秒。原v5五进程身份保持、科学全部完成也继续。含合成保载，不是纯科学吞吐或每瞬时保证；当前非跨重启服务。旧v4不复活。

## 保存与同步

共享SSD小包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER70_COMPLETE_20261028_223012/SMALL_EVIDENCE.tar.gz`，241成员/2857652字节，SHA256 `34e58fb4a241f54398a5298e9b8ada615e1cda30f003cb6c57590d9efc14d5f9`，逐成员字节/hash及Python AST核验。见[收据](RL_PARAMETER70_COMPLETE_20261028_SAVE.json)。HDD配额满，仅重写原有紧凑入口；大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份。

开工实际fetch/read main0be97cc8/baselinef6e8f8c，71–73前瞻提交03268f6c已push核验；收尾fetch/read main97c4dd88，非RL原拟合41→49观察/共享报告已读并fast-forward保留，无冻结RL源变化，无子agent；遵循仓库sii-research-sync。Goal active，未声称整体收敛。
