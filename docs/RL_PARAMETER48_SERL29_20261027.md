# 完整参数47/Direct28审查与正式参数48/Direct29接续

2026-10-27，Goal active；尚无四方法整体健康收敛或最终比较结论。继续使用sii-research-sync，无子agent。

执行主机 `rltest-1025--a6ed2ff39b3c-z3ntpmmalx`；共享SSD根B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；源码B/repository/SII_compliance。本轮再次查询/fetch/read远端main `75e29e7aa05eb47b9d106de7453463940395ed08`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。main仅增加另一主机非RL经典42/72审计归档，已安全快进保留，不混作当前RL结果；正式冻结源码未修改。

## 已完整审查的训练结果

参数47三路每路新增41250，全30条件×55秒，无abort。原归档/fullreview/health/FINISHED完成；保存episode与optimizer算术独立核验及诊断图目视检查完成。所有旧replay字段/history完整保留，新增奖励重建误差0，网络和优化器有限。奖励审计来自原物理interval日志，不冒称独立重算全部物理子步。

|方法|累计步数|Task/Strict（各30）|平均reward|末次Q loss|首/末1000次Q loss均值|
|---|---:|---:|---:|---:|---:|
|impedance|1976180|18/17|-2.379692817|1.651479244|2.756887 → 2.506422|
|admittance|1976000|13/12|-12.047562939|1.253541231|1.629519 → 1.375069|
|vmc|1977000|17/17|-2.834139572|0.523817897|1.525565 → 0.567449|

三路本轮末1000均值下降，图中仍有尖峰/波动，有限和局部下降不等于整体健康收敛。固定46–48尚待完整48；此前43–45未稳定。检查点 `B/runs/parameter_capacity_pool30_cycle47_archive_20261026_v1/<method>/cycle_00047.pt`；精确SHA见saved review与fullreview。

Direct28完整1163040步/9264328 critic更新，新增41250，全30×55，无abort，Task/Strict0/0，平均reward−30.909500493。末critic loss .010795381，首/末1000均值 .010665973/.010136176，终端MAE .027547715，TD32 MAE .031618915。原fullreview/health/保存算术与图通过，旧1121790 raw/derived/history和930历史pending完整保留，新样本全部成熟。checkpoint `B/runs/serl_take_cycle28_archive_20261027_v1/direct/cycle_00028.pt` SHA `96d1d7e74c50f34e6965b4aa80d06a315a709cab78ffcb3ba957031e49947f7d`。低loss不能当作任务成功。

## 参数46→47保存结果配对

`B/runs/parameter46_47_saved_outcomes_20261027_v1`：全部30条件/MJB、原physical-valid/Strict gate和输入hash核验。I成功情况不变，均值−.054458；A均值+3.418308，其中成功切换条件贡献+3.366408。long0200/0300、short0200获得Task/Strict；short0000穿透.183795→.203122mm丢Strict，short0600丢Task且Strict一直失败。V均值+1.792298，short0600穿透.215310→.178476mm恢复Strict，贡献+1.754792。

只做已保存在线结果的算术归因，0物理/优化；没有证明loss、随机性或策略学习的因果份额，没有调整原.2mm gate或筛去失败。

## 实际48与29已经启动

参数48于12:00:24 UTC启动：I359275/A359279/V359281，GPU1/2/3，CPU13–25/26–38/39–51，每路30sampler。准确完整47全learner/optimizer/replay/RNG/history及下一65536样本检查通过；独立PRELAUNCH通过。4m append容量正式部署，旧2m历史marker与entry23、后续entry47 marker均保留，原terminal128、目标I-min/A-V-mean、actor-min、batch65536、UTD1、学习率/物理/MJB/gates/canonical48/dt5e-5不变。实际startup新增1000/1000/2000通过：旧行/history/优化器配置、30MJB/sampler、动作/时钟与新reward0误差。archive359361/fullreview359363，startup359358已完成。

Direct29于11:56:09 UTC启动，learner241542，GPU0/CPU0–12、30sampler。准确完整28三批65536/RNG/reload/全state和PRELAUNCH通过，原通用driver不变。实际startup新增1000到1164040步/9272328critic：旧1163040 raw/derived/history精确，148新成熟+852新pending，930旧隔离不变；原30MJB/sampler/action/clock和奖励0误差。archive241547/fullreview241549，startup241545完成。旧pending仍禁止跨reset续接、伪造终端或采样endpoint−1。

## 跨200万审计和下一轮准备

只读actual48边界审计401313，`B/runs/parameter48_boundary_preparation_20261027_v1`，CPU52/nice15。等待各路真实原子checkpoint≥2001000，核对旧47所有replay/history、双marker、优化器配置、全部新增reward/action/observation/clock与终端映射，克隆保存RNG依原mask-rejection采65536，检查旧行及≥2m行均覆盖。不是实时learner采样日志；尚未观察到实际跨界，不提前声称通过。原始审计快照只存SSD。

参数49仅准备401495，`B/runs/parameter49_preparation_20261027_v1`：绑定48真实PID/start_ticks，7200秒等完整48原review/health和父退出，再1000秒外层/900秒内层check-only；无自动训练。沿用完全相同两4m源码和全部依赖，entry23/47保持不变，不把47扩容入口误改成48；5模板、prepare/launcher/setup共10源码hash冻结，health逐字相同，下游奖励/动作检查仅周期差异。完整48恢复尚待。

Direct30仅准备464829，`B/runs/serl_take30_preparation_20261027_v1`：7200秒等待完整29、900秒实际check-only，无自动训练；下一正式周期前须检查已固定27–29统计。通用driver/hash保持，五模板固定29→30/900终端/930隔离。首次生成器静态断言要求startup wrapper直接出现quarantined字样，因其委托独立audit而失败；失败记录保留，改为检查真实audit引用和helper930后通过，失败时尚未启动等待或训练。没有重做已通过的driver数学验证。

固定Direct27–29 waiter336744、参数46–48 waiter1908379保持原seed/5000/5%/近零1，窗口未完成。Direct29冻结prepare3802347保持此前全30与同冻结16动作seed2026102626计划；准确完整29恢复和物理尚未发生。原参数冻结41 PID316550/316551/316552及root316553继续，完整90尚待；Direct29物理须其全完成/审查通过后才能用CPU52–54。

## 资源与交接

固定60样本/83.057秒混合训练与冻结41推理窗口，GPU0–3均值[61.45, 62.93333333333333, 60.13333333333333, 59.36666666666667]%；保存均值独立复算通过。四正式PID身份逐样本保持。这是窗口均值，不是每瞬时保证或纯正式吞吐，也不包含此前换轮空档。

原transition4149397已经完成。保存的父退出→新Popen界：I257.717–259.719秒，A317.776–319.778，V333.822–335.823，Direct274.722–276.724。这不是GPU精确idle或首更新延迟；不隐去轮间审查/恢复低利用。没有假负载。

小证据 `docs/evidence/RL_PARAMETER48_SERL29_20261027`，138文件逐hash/大小、Python AST核验。实时进度见LIVE_STATUS，所有PID再次行动前重验。下一步优先实际48跨界/完整冻结41审查，继续当前48/29，待固定窗口后审查49/30与冻结29，不重复已完成评测。大checkpoint/replay/raw/runtime留原共享SSD；HDD满，仅更新已有LATEST入口，不声称完整HDD/arm1备份。本轮commit/push/小证据包收据另记。
