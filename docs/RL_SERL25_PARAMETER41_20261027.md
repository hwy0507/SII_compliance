# Direct25、参数41已接续：完整24/40结果与资源交接

2026-10-27 UTC。本集群 B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库 B/repository/SII_compliance（原HDD路径是链接）。实际主机与进程身份见小证据 LIVE_STATUS.json。Goal active，尚无整体健康收敛结论，无子agent。

## 当前正式训练

完整24/40的原审查、健康诊断、图与独立保存算术均已检查，准确不可变父的全state恢复check-only通过，PRELAUNCH_SCIENTIFIC_REVIEW记录后，启动一个有限原设置周期：

|方法|当前周期|原learner PID|实际启动审查新增|最大累计步数（全30无早停）|
|---|---:|---:|---:|---:|
|Direct SERL|25|2350595|1000|1059540|
|Impedance|41|2369246|1000|1728680|
|Admittance|41|2369249|1000|1728500|
|VMC|41|2369250|2000|1729500|

两原 startup/REVIEW.json 均 passed；保留全部旧replay字段、history、优化器配置及容量marker；30个原MJB/采样进程与新动作/clock/reward核验通过，奖励重算误差0。Direct首1000中137成熟、863pending，全部派生目标正确。check-only与实际新增启动审查分别留存，原startup进程正常结束，无重跑。

Direct25继承2m容量/历史entry23，非再次迁移；官方SERL upstream 1fa2af7496be042e43d36120a7c8d1b71f1bfb59、10critic/随机2取min/noentropy backup/8critic:1actor/batch65536/32步behavior目标保持。validated driver SHA 0ca9b613fb0e2e0f360769ca3ec9ae9f1674ef7b295f4de25986a3ba054b9e81、capacity helper c39abba32814bc713c58945eb3405f33118e1881b76fb60622c87a010132dd27，正式前核验未变。参数继续capacity replay+pair learner，全部optimizer/replay/RNG/history及2m历史entry23保留。physics/MJB/gates/filter/执行器/dt5e-5/canonical48/原30条件/SPT reward保持。

Direct archive2350598/fullreview2350599；参数archive2369305/fullreview2369308。当前完整25/41尚未产生，不能提前称完成。05:40:51附近实际快照D1021508、I1693647、A1693521、V1694546，均30运行/0完成，后续用原PROGRESS读取实时状态。

## 完整24/40的结果

|方法/周期|steps / updates|Task / Strict（各30）|平均reward|末1000 critic loss|terminal MAE / in-bag MAE|
|---|---|---|---:|---:|---|
|Direct24|1018290 / 8106328|0 / 0|-30.9249648873|0.01230372194|0.0308610592 / NA|
|Impedance40|1687430 / 1682431|18 / 18|-0.5890155965|2.0455891821|0.743359 / 0.212303|
|Admittance40|1687250 / 1682251|14 / 13|-10.3426270065|1.5846828271|1.134465 / 0.721100|
|VMC40|1688250 / 1683251|17 / 17|-2.8100161073|0.5670637148|0.529517 / 0.211805|

四路各30×55秒、无abort；新41250步奖励精确，所有旧replay/history/2m保留，网络与优化器finite。审查只读，不重复物理；reward由原物理interval journal重建，不冒充原始子步全重放。Direct旧977040 raw与derived精确保留、新41250目标准确、pending0；首1000loss .0127541293，全均值 .0125905591、max .0254054964；32步TD MAE .0364692211，Qmean -20.5173836、temperature .000399301，诊断前后network/optimizer/RNG不变。低loss没有转成任务成功。

参数40全周期mean loss I/A/V=2.301948927/1.580127854/.674471367。I有波动但较39改善，V改善；A虽在线loss下降，末端出现跳变且terminal/in-bag误差上升，不能宣称优化完全健康。terminal误差是诊断，未添加必须零误差的新验收门。

保存值配对39→40：I reward均值+1.9121323，long0000由失败到双成功贡献+1.93994788；A均值-1.64830193，long0200/0900成功转失败各贡献约-1.67，short0200恢复贡献+1.69619177；V均值+1.78953374，short0600 Strict恢复贡献+1.75242254。保留39 long0000原2mm早停，不改失败。Direct23→24均值-.0208854366，1m→2m容量变化披露，不当无干预因果比较；保存配对不解释在线loss因果。

准确完整父SHA256：

- D24 `112eda44c8cda14c5f3b4b3ce934dab7882fa254ac516e1ca4e1b5e24fe852e4`
- I40 `4a0b47956c1eb32aef76e3f560a1837b090d1a8c380298d3f30ee29e42136960`
- A40 `60b6da86066aa759dc719d14c500ab39a0b9ba4b4c9a01088156f5c3c82ebdcf`
- V40 `8a53c0571181ba1bd126301bd4b9bf5eb70c34f5aada2c6e2dc7d948004e7f7e`

## GPU窗口与衔接

新原observer2537747仅一次60样本/69.3677707秒，CPU54读nvidia-smi，0训练/物理/人为负载。原25/41实际startup都通过后启动，每样本GPU计算进程集合恰为四正式PID且/proc身份保持；source hash、保存均值独立复算通过。GPU0–3均值58.3167/59.0833/58.7167/58.5%。这是此窗口平均，不保证每瞬间或整段任务均≥50%。已完成，不重采。

原transition observer1739008完成退出；2秒采样的原父退出到新spawn区间：Direct163.9297–165.9306秒，I253.1221–255.1230秒，A303.1429–305.1461秒，V323.1543–325.1552秒。期间包括完整审查/恢复/科学判断；这不是精确整卡空闲时长。保留真实空档。24/40上一纯窗口不重复。

## 已登记的下一步

- Direct26：waiter2397737、释放CPU调度2397769；B/runs/serl26_static_preparation_20261027_v1/WAIT_REGISTRATION.json。原八模板hash未变，新调度绑定真实25 learner/review。7200秒，仅完整25审查后恢复check-only，无自动训练。
- 参数42：waiter2397589、调度2397590；B/runs/parameter42_preparation_registration_20261027_v1。五入口上下文替换、AST、41→42/CPU39/历史entry23已核验，绑定真实41 PID；7200秒，仅准备check-only，无自动训练。scheduler中“before41 launches”是沿用的说明字符串；实际调度绑定正在运行的41审查，用于随后42准备，不影响执行。
- 原Direct24–26窗口1470790和参数39–41窗口3482651保持；原5%/近零1/5000分类配对bootstrap定义和原seed不改，完整统计仍待，不新开重跑窗口。
- 参数冻结41准备1833369仍等完整41。见 [前瞻登记](RL_FROZEN41_REGISTRATION_20261027.md)：完整41终点、同冻结32外部seed2026102638、全30×3×55秒、最多123750动作/99000000子步、CPU52/53/54、GPU1/2/3，0优化/正式replay写入。准备只做完整父恢复，不自动物理评估；待原check-only和科学审查后另启动原有限90回合。PLAN SHA a541276ae23af43ac253d0bc0d6a3736fd5a601d8ba6d00307f727e3379df83a。

下一次优先检查原25/41进度与完整审查；41完成后读取原39–41统计、冻结41准备，科学判断后接续有限阶段。A40 terminal/in-bag误差上升可做后续有界定位；不重跑完成的冻结32、VMC1164、I39静态碰撞或Direct百万边界检查。

## 证据与发布

小证据 `docs/evidence/RL_SERL25_PARAMETER41_20261027`，445份原文件共4880073字节，逐份copy/hash核验，另有LIVE_STATUS、衔接保存复算和MANIFEST。包含完整24/40审查/health/图/保存值review源与结果、25/41实际启动和登记、26/42准备及新GPU原样本。大检查点/轨迹仍在B/runs，未宣称HDD或arm1全量备份。新归档、HANDOFF仅SSD，现有HDD LATEST覆盖后回读。

本轮续接核实真实远端main=7d69ac57974888d32f98d208f0097e7ec8f64426，baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d；fetch/read两日志，main最新是另一主机非RL97/108，非本机RL或指定最终ESN完成。本轮commit/push与归档收据收尾单独记录。整体收敛、完整41冻结结果与最终比较仍未完成。
