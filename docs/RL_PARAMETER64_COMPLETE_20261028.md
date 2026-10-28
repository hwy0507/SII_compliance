# 完整64审查、原62–64窗口完成与准确续训65

2026-10-28 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，Torch `B/env/bin/python`。开工真实fetch/read main6ac95d7be223d2c182c4917af5a2177d0aa406aa、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，非RL并行工作完整保留。原63详细结果与失败见[上一交接](RL_PARAMETER64_EARLY_ANCHOR_20261028.md)。

## 完整64

原三learner自然结束，均实际FINISHED `stopped_at_complete_cycle`。归档审查 `B/runs/parameter_capacity_pool30_cycle64_review_20261026_v1` 通过：各30×55秒/41250新transition，无abort；原63所有replay行精确保留，历史/优化器状态保持，每个新reward按冻结物理区间journal复算误差0，网络和优化器有限。不是独立原子物理子步重仿真。

|方法|steps / updates|reward均值|Task / Strict（分母30）|critic首→末1000|critic mean / max|
|---|---|---|---|---|---|
|I|2676648 / 2671649|-0.542027152|18 / 18|2.383212119 → 1.863037175|1.957014302 / 29.656642914|
|A|2677250 / 2672251|-8.512810311|14 / 14|1.495751109 → 1.279073123|1.321838431 / 60.237491608|
|V|2678250 / 2673251|-4.607563648|17 / 16|0.741987578 → 1.041693677|0.801867807 / 44.371902466|

完整checkpoint位于 `B/runs/parameter_capacity_pool30_cycle64_archive_20261026_v1/{method}/cycle_00064.pt`：

- impedance SHA256 `64bffb05c99116a1d9c306370b7a914f7c4597201e4d381eba4d04542f2b8648`。
- admittance SHA256 `32bded4278fc912a728eec0625472e43a458ee84448114df87fb6b37985a502d`。
- vmc SHA256 `c39302451cc0f7fff54f7fc3988812fe48086fb2a813f2f260111f5981953c66`。

完整64 loss位于 `B/runs/parameter64_loss_20261028_v1`。全部数值有限、步号连续、30完整回合及hash/均值/最大值独立保存复算通过；实际loss.png已查看。I critic下降而actor26.189493→25.646087持续下降；A critic早段后较低，但局部16500附近60.237492孤立尖峰/末段尖峰保留，actor先小降后持续升−10.111026→−9.903098；V critic约33000后密集burst/后段均值抬高，actor−14.400864→−14.039324上升。没有凭有限尖峰新增失败阈值，仍非平坦或整体收敛。

health实际六面板图已审，顶部右侧长标题裁切但轴/数据可读；I entropy近−5，A/V近−7，V alpha末段上升、A略降，全部有限且诊断network state不变。terminal in-bag MAE I .247306020、A .378672263、V .365562039；sampled TD MAE .224365335/.221831706/.166358429。0优化/物理；终端非零误差不是新停止门。

## 全部63→64标签核验

`B/runs/parameter_task_label_audit64_20261028_v1/COMPLETE63_64.json` 和独立SAVED_REVIEW核对全180rollout/90reward对、Task/Strict/physical计数与原Strict/abort变化通过，无Task-only遗漏：

- I short0600 Task保持true，外穿透.220418581→.190713768mm，physical/Strict恢复，累计reward−34.769579→19.357919。全I18/17→18/18。
- A short0000、short0900恢复Task/Strict；short0100 Task保持true、穿透.206329078→.169325198mm恢复physical/Strict。全A12/11→14/14。
- V short0600 Task保持true，穿透.186577601→.223143468mm失physical/Strict，累计reward17.834741→−34.815386。全V17/17→17/16。原.2mm门不改，失败保留。

## 原62–64窗口实际完成

`B/runs/parameter_capacity62_64_reward_stability_20261028_v1` 的REVIEW、独立SAVED_ARITHMETIC_REVIEW及实际reward_stability.png图审完成；结果文件为REVIEW，没有FINISHED。原3轮、相邻及首尾公式/5%/近零1/seed/5000 bootstrap保持：

|方法|62 / 63 / 64 reward均值|相邻相对变化|首尾变化|原描述性检查|
|---|---|---|---|---|
|I|−5.822772 / −2.392742 / −.542027|近零保护，不给比例|近零保护|未通过|
|A|−8.573957 / −13.711201 / −8.512810|59.916826% / 37.913458%|.713173%|未通过|
|V|−4.613582 / −2.856740 / −4.607564|38.079789% / 61.287497%|.130442%|未通过|

A/V首尾接近不能代替相邻大幅变化。独立保存算术不重抽bootstrap，区间仅条件构成敏感性，不是独立训练seed或冻结策略性能。I56–58/V53–55历史通过及59–61失败仍保留，不移动窗口端点。Direct33仍仅原训练集经验数值收敛，Task/Strict0/0，不启动34。

## V固定终端与预登记排序对照

`B/runs/vmc64_terminal_anchor_followup_20261028_v1` 全1914固定63终端输入/动作/reward/mask精确，CPU前向复现health、权重/RNG不变，独立标量复算及实际follow64.png已审。旧1914 SSE9786.920509937→6539.575074569（下降33.1804619%）；旧贡献.543920540150→.357691508098，使用旧分母after .363302242838；新30贡献.344211032334，全1944贡献.701902540432。新30贡献较大，因此旧行改善不代表全部终端误差已改善。values SHA256 `d239537483048dbe2b039db516ed01c1db55d8b45e07f7ac3d60fe2031de8bb6`。

原五focus中2050526 SSE146.377992→4.616749、2299142 362.458630→199.500995、2046571 7.549246→2.008070、2423133 436.588628→4.818018改善；2423122 .300759→1159.197633明显退化。图中原点标签重叠，精确值以REVIEW为准。原mask为0的head不计入in-bag SSE；没有新停止门或梯度因果主张。

`B/runs/vmc64_ranked63_terminal_followup_20261028_v1` 在64完成前固定全1914原63排序与两条原最大误差，完成后只读保存值复算，全旧数组/分母精确、原完整64总量复现、独立保存聚合/计数通过：543行改善、1371行退化。2464220 SSE2238.586046→57.427672、1603101 2139.275917→3.492563改善；全部1914保留，不用两条改善替代全体或原五focus结论。0新前向/物理/优化/replay写入。

## 准确续训65

`B/runtime/prepare_parameter65_20261028_v1` 三路完整64全state/replay/下一65536恢复check-only exit0，checkpoint hash与上表一致。普通读写/fsync/逐字节部署方法实际执行成功；此前原copyfile全零失败证据仍保留，不改科学源码。DECISION65绑定29项完整审查/图审/历史窗口/下一窗口/恢复证据，奖励仍变化、actor仍移动且V critic后段抬高，因此继续一个原配置有限65：不重置、不引入辅助权重、不改reward/gate/物理/LR/mask/终端128/batch65536/UTD1/4m append。

16:00:07 UTC实际启动 `B/runs/parameter_capacity_pool30_cycle65_20261026_v1`：I3518809/start39892318、A3518810/start39892318、V3518811/start39892319，archive3518812/start39892319，startup3518813/start39892319。仍GPU1/2/3、CPU13–25/26–38/39–51、每路30sampler，仅一轮，不自动66。实际startup I/A/V前1000/1000/2000审查通过，旧2676648/2677250/2678250 replay全行精确保留，history/optimizer hyperparameters/30sampler/MJB保持，新reward复算误差0，未覆盖新终端。

完整65 loss已由静态源码逐字节部署到 `B/runs/parameter65_loss_20261028_v1`，实际waiter3549843/start39897957、CPU54/7200秒，PLAN SHA `d92fb5a877cb1aaef7cb1a1a580374629427d4baa65ac274e435b5d9720b0412`。保留全49–64历史追加65，paired64→65和原0600不变；实际65完整复算/图审待。

预登记65–67窗口 `B/runs/parameter_capacity65_67_reward_stability_20261028_v1` 已在经审查65真实启动后启动waiter3549846/start39897958、CPU54/14400秒；原PLAN SHA `517dbefb03fe7630530100d658e35e6108528a18af564b01911b2e53a81bd0f0`字节不变，LAUNCH单独记录实际启动。全部65/66/67完整结果尚待，不提前判定。66/67训练不会由该只读等待自动派发。

## 等待、GPU和保存

`B/runtime/parameter64_verified_wait_1543_20261028_v1` 共26真实样本（15:43:50–15:56:23），原learner身份保持至各自FINISHED/自然退出，归档原monitor退出由实际ARCHIVE_REVIEW_FINISHED确认；一次ps查询恰逢其自然结束而返回1，随后真实完成文件核实，无重启。全所需审查输出到齐后observer exit0，随后逐项实际科学复核，不用路径存在替代通过。

同区间147条原guard样本min74/66/63/63%、mean78.85714286/78.69387755/82.77551020/83%，低于50全0、maxgap5.179956秒；含合成保活，非每瞬时保证或纯科学吞吐。当前v5五原进程保持，科学结束也继续保活，v4 STOP不动；v5位于/tmp，当前不是跨重启服务。

最新小证据见[收据](RL_PARAMETER64_COMPLETE_SAVE_20261028.json)及[清单](evidence/RL_PARAMETER64_COMPLETE_20261028/MANIFEST.json)，完整包175成员/1856103字节，逐字节、tar成员大小/hash和Python AST核验通过。大checkpoint/replay/raw仍原共享SSD，HDD配额满仅重写既有LATEST，非HDD/arm1全备份。原65继续，Goal active，无子agent。

16:05补充：实际65 startup已通过，当前原三learner/归档/loss/窗口/五guard身份全部live；steps2679943/2680507/2681579，GPU 0, 80 %; 1, 97 %; 2, 98 %; 3, 97 %。非完整65，Goal active。

共享SSD完整小证据包：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER64_COMPLETE_20261028_160519/SMALL_EVIDENCE.tar.gz`，SHA256 `bda6c095c689e2ff9e2782efa3b1fbdb0e12b943587c1bea3f5e688cc8776a4c`。大产物仍原共享SSD，非HDD/arm1全备份。
