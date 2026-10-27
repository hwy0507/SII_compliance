# 参数45正式接续与Direct27–29固定窗口（2026-10-27）

Goal active：继续Direct SERL及三参数RL直到reward稳定、loss健康，并完成冻结验证与最终比较；当前未满足整体收敛。用户已恢复且授权继续，无需再次审批。没有子agent。

当前主机 `rltest-1025--a6ed2ff39b3c-z3ntpmmalx`；代码与大产物共享SSD：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`（下称B）。
仓库 `B/repository/SII_compliance`，HDD原SII_compliance为其入口。
本轮开工实际远端main `c546baf5f8e000303d1f29cbe8d22e033e4ce1f2`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。main新增另一主机传统非RL24/72进度，已安全快进保留；冻结训练源未改。
小证据：`docs/evidence/RL_PARAMETER45_SERL27_29_20261027`，MANIFEST逐文件hash，LIVE_STATUS含真实PID/start_ticks/命令/进度。最终归档/push收据另记。

## 完整参数44与科学判断

完整审查 `B/runs/parameter_capacity_pool30_cycle44_review_20261026_v1`，保存值独立复算 `B/runs/parameter44_saved_review_20261027_v1`。三方法全30×55秒、各新增41250，无abort；全部旧回放/history保留、新reward重建误差0，network/optimizer有限，health只读状态不变，诊断图已目视检查。

|方法|总交互步|Task/Strict（/30）|reward均值|最后q_loss|首/末1000 q_loss均值|
|---|---:|---:|---:|---:|---:|
|阻抗|1852430|18/17|−2.358478227|2.231508017|1.909950 / 2.772335|
|导纳|1852250|15/14|−8.735468331|2.106065989|2.250481 / 1.782218|
|VMC|1853250|17/17|−2.848943130|0.638369203|0.783312 / 0.764343|

阻抗末段loss升高且严格成功下降，不能称健康收敛。A/V有限且末段均值回落，但不能据此提前宣布固定43–45通过。原参数43–45 waiter2190600继续，统计窗口、seed2026102745/5000次/5%/近零保护1不变。

准确完整44 checkpoint位于 `B/runs/parameter_capacity_pool30_cycle44_archive_20261026_v1/<method>/cycle_00044.pt`：
- I `2de1dae021c92f604173691144e589b670a754692d892c0fdcf8114fcd2f8e35`
- A `fe93962a22c54475700aec83f5dea981fb280e208b53d91850f52ca88c982083`
- V `8d8ff0d83b5fcf751308ba12e5fc9848740328654fcbdb6417e5f87edec32f06`

43→44保存结果独立配对 `B/runs/parameter43_44_saved_outcomes_20261027_v1`，全部输入hash/模型/原gate验证，0物理0优化：
- I均值−1.815447，其中short0600严格成功真→假贡献−1.810938；外部穿透.191786→.244149mm跨原.2mm。Task均真，完成12.72→12.76秒。
- A均值−.168586；short0000严格成功丢失（.135288→.217249mm），short0600恢复（.234708→.194092mm），两者净贡献−.046229。
- V均值+1.763760，short0600恢复贡献+1.748214；穿透.213012→.188304mm。
这是保存回报算术与原物理有效性归约核对，不是学习/随机性或全loss的因果分解；不改阈值或重演失败。

## 正式45与下一轮准备

`B/runs/parameter_capacity_pool30_cycle45_20261026_v1`：I417803、A417804、V417805；UTC10:04:31启动。GPU1/2/3，CPU13–25/26–38/39–51各30sampler，原解释器/算法/LR/batch65536/terminal128/UTD1/2m追加回放/历史entry23不变。
准确44全部learner/replay/RNG/history、下一65536采样恢复检查通过，PRELAUNCH绑定fullreview/health/独立算术/检查hash；只启动一个有限周期。
actual startup417807已完成：I/A/V新增1000/1000/2000，各自旧回放/历史/优化器配置/30MJB/30sampler/action/clock和新reward0误差通过；archive417808、review417809继续。

新46准备 waiter504393，`B/runs/parameter46_preparation_20261027_v1`，四入口 `B/runtime/*parameter_capacity46*_20261026.py`。只在完整45review/health且三父退出后做实际check-only，7200秒等待，无自动训练。原history entry23/CPU39保持。
静态初版链式字符串替换把父cycle断言45误改46，启动前被assert拦截；失败草稿保留failed_static_v0，改为一次性替换并逐diff/AST/父子轮次验证后才启动waiter。没有运行错误父恢复、物理或优化。

44结束换轮有真实空档：当时GPU1–3瞬时降到0%，不隐瞒、不假负载。确认三父退出后将原只读完整review3195014/3195015从CPU53移到释放CPU13，health继承13；未改在途训练或冻结评估。之后实际45启动和采样恢复。保存的单次POST45_GPU_SNAPSHOT为GPU0–3 79/83/85/81%，只是瞬时观测；此前take27正式60样本窗口63.7167/63.5667/64.1833/58.6%仍为原证据，不重复测量或声称每瞬时≥50。

## Direct27–29与28入口

原正式take27 learner3712293（start_ticks28969795），`B/runs/serl_recovery26_take27_20261027_v1`持续，无重启。完整恢复26为1080540步、Task0/30；27尚未完整，不能用低critic loss代替任务收敛。

新固定窗口 `B/runs/serl_take27_29_reward_stability_20261027_v1`，waiter336744；在27 completed_conditions=0、28/29未启动时登记；已知完整26为配对基线，前瞻窗口27/28/29。seed2026102746，5000分类内配对条件bootstrap，5%/近零保护1，21600秒等待，CPU52，0物理/0优化、无自动停止或续训。数学计算块除周期标签外保持原式，实际episode步数检查保留全部失败分母。
四轮均2m回放、历史entry23、原中断25语义与930隔离pending不变；26→27等价take gather边界显式披露并绑定原gate，不将baseline差异当优化实现的因果效果。旧24–26因25中断不可完成，保留而不重启/冒充完整25。

新增通用有限接续源码 `code/mujoco_6d_vmc_benchmark/tools/resume_serl_take_recovery_continuation_20261027.py`：只接受准确连续完整27及之后，遍历hash绑定父链直到原26→27入口，原interrupted_stream_recovery不伪装，history仅26..parent且无完整25；完整网络/Adam/RNG/replay/930pending保持。沿用已验证take helper；采样物理体与27相同，仅续训metadata措辞改变。静态原真实lineage、9负contract+6负boundary、AST和main hash已通过；这不等于实际完整27恢复。

28准备 waiter154584，`B/runs/serl_take28_preparation_20261027_v1`。7200秒等待准确27fullreview/health及parent退出，再900秒check-only，无自动训练。当前runtime从27拷贝，准确parent27/new28；五审查模板与手动launcher静态准备完成，840终端/930隔离/新old.recovery_continuation断言正确。实际28尚未启动，完整27恢复仍待；不要重复跑准备进程。
源码SHA `9377282eb8c4fbf4191b8bce70a1b71d14c66f9d23618d53e533b59645cb477f`，main SHA `c8148342dcd48dc7f112681f01ab387e9d43868e27cc1f1d940e72981da046ed`。

## 下一次接续

1. 先核LIVE_STATUS和实际PID身份；四正式45/take27及冻结41原316550/316551/316552均继续，勿重复启动。冻结41当前约13/13/14完成，总90未完，不重跑冻结32/Direct16。
2. 完整45审查/health/独立算术及原43–45统计后，实际46check-only和科学review通过再启动46。45–47预计仍容纳于2m；48最大预算会越2m，必须在那之前单独验证容量方案，不覆盖旧回放或盲跑到满。
3. 完整27审查后独立保存算术/图、实际28check-only/科学PRELAUNCH，再用新28 launcher；其后29必须沿用新恢复链语义。原25完整父driver和旧冻结26入口不能直接复用。
4. 新Direct27–29统计仍须完整29；固定条件bootstrap不替代冻结验证/泛化或最终ESN/SPT比较。所有这些尚未完成，Goal保持active。
5. 大checkpoint/raw/runtime仅在共享SSD；HDD配额满，更新现有LATEST入口指SSD新交接，不宣称HDD或arm1全备份。新源码/小证据常规commit/push，保留远端并行非RL进度。
