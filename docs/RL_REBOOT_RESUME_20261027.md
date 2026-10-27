# 2026-10-27 重启后恢复：Direct 中断25独立恢复、参数42与冻结41

用户在本对话明确要求“我回来了，继续刚刚没做完的goal接着做吧”。Goal工具确认active；覆盖此前关机paused状态，不是收敛完成。上一个环境保存轮次属于实际进展，本轮重新检查实际挂载/进程/检查点，未根据旧PID重启任务。无子agent。

共享SSD基础目录 B：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。代码实际在B/repository/SII_compliance，HDD路径是链接。本轮入口B/runs/reboot_resume_20261027_v1，仓库小证据docs/evidence/RL_REBOOT_RESUME_20261027。原关机快照不覆盖。

## 权威运行状态

- 参数正式42：B/runs/parameter_capacity_pool30_cycle42_20261026_v1，I/A/V learner351462/351463/351465，GPU1/2/3、CPU13–51，三路各30sampler共享原12物理CPU。每方法最多新增41250动作、单个完整周期，原学习设置和2m append保持；不是无界自动续训。
- Direct恢复26：B/runs/serl_interrupted25_recovery26_20261027_v1，learner645388，GPU0/CPU0、30sampler共享CPU1–12。新独立driver `resume_serl_interrupted25_20261027.py`；一完整原30条件周期、最多41250动作/33000000子步。与旧未启动的 `serl_capacity_batch65536_cycle26_20261027_v1` 不同，禁止启动旧完整父25入口。
- 冻结参数41：B/runs/parameter41_frozen_full30_20261027_v1，原计划实际评估I/A/V316550/316551/316552，根review316553；CPU52/53/54、GPU1/2/3。完整90×55s，最多123750动作/99000000子步，seed2026102638，0优化/正式replay写入。尚未完成全矩阵，勿重启。
- 参数42 startup351520已通过退出；归档351523、完整审查351524继续。Direct startup645389已通过退出，归档645390与完整review645391继续。PID仅为本轮身份入口，下轮核验/proc start_ticks和状态，不凭历史存在就认定live。

## Direct 中断恢复协议与实际验证

准确父为B/runs/user_shutdown_pause_20261027_v1/direct/checkpoint_before_interrupt.pt，SHA256 `f765ef4a5b256097e3c17365ee4305088d943cbdcdb7447a3edbfbeb24eda6ca`。1039290步、8274328critic/1034291outer更新，25不完整，最后完整history24。实际原25保存21000新transition，30条件各387–775步、无完成条件；中断前后差180条已执行但不在首选快照内，仍按原交接披露，不自动用中断后取证副本覆盖。

930条未成熟尾部（旧stream0–29各31条）原样保留在replay.pending中，所有旧raw、derived、ready顺序、RNG、network/Adam/history保持。由于MuJoCo现场和episode时钟未保存，旧pending不能获得真实后续32步目标：显式永久隔离、保持原成熟采样规则下不入样，不伪造done/终止奖励、不删除、不连接新环境。新物理回合使用stream30–59，并由运行时guard禁止向0–29追加。计数仍包含这些已执行曝光；此项限制不能隐藏为“全部旧数据可继续成熟”。

旧完整24→25协议由原capacity driver验证其自身历史链，新协议仅增加独立interrupted_stream_recovery字段。原物理、MJB、SPT奖励、gate/filter/执行器/dt5e-5、canonical48、官方SERL commit1fa2af7496be042e43d36120a7c8d1b71f1bfb59、10critic/随机2min/noentropy backup/8:1/batch65536/32步behavior目标均保持。

实际partial25 check-only通过：完整learner/replay/history digest、下一65536批与重新序列化恢复精确；30条旧stream追加拒绝、4个错误恢复协议拒绝；独立临时replay的990条合成transition检查32步成熟/终止flush/旧前缀不变/隔离队列保留。合成数据不保存、不进入训练，无优化或物理。未将这个测试写成MuJoCo现场恢复。

正式启动INITIAL_STATE_REVIEW再次确认与首选父全state精确。真实首1000新transition审查到1040290步/8282328critic更新：旧1039290 raw/derived/history全保留、930旧pending不变，121新mature+879新pending；30MJB/30sampler/CPU affinity、canonical48映射/clock/raw动作到公共动作、全部新奖励重算误差0。check-only和actual startup为两项不同证据。

新26是额外完整曝光，不是补完25；从完整24到新26结束最多新增62250条已保留经验，另披露180条未入首选快照。旧24–26窗口缺完整25且被环境中断，不能继续出三完整连续周期结论。旧Direct26冻结计划也需新lineage/窗口适用性登记后再执行；本轮没有启动它。后续续训/冻结必须识别930历史pending与新recovery字段，原complete-cycle验证入口不能直接套用。

独立完整审查位于B/runs/serl_interrupted25_recovery26_review_20261027_v1，归档位于B/runs/serl_interrupted25_recovery26_archive_20261027_v1。新replay审查器按条件标量重建所有新32步目标，并检验历史pending精确保留；health的multistep前向只从成熟集合抽样，避免误用旧pending的endpoint=-1。完整26尚待，未宣告健康收敛。

## 参数42与冻结41

完整41原review/health已实际读取并绑定三准确checkpoint hash。三路42 check-only全learner、replay及下一65536采样精确；保留capacity replay+pair learner、历史entry23、terminal128、target Imin/A-Vmean、actor min、batch65536及原LR。实际首新增I1000/A1000/V2000审查通过，旧replay各字段/history/optimizer与新reward重算保持。

冻结41在原前瞻PLAN SHA `a541276ae23af43ac253d0bc0d6a3736fd5a601d8ba6d00307f727e3379df83a`下执行。真实41完整learner/replay、外部动作RNG同seed/异seed/原生动作一致检查均通过，再经PRELAUNCH_REVIEW启动。未重复已完成冻结32、Direct16或其他旧诊断。冻结41运行中，不能称全90结果通过。

## 39–41稳定性与导纳终端跟踪

原parameter_capacity39_41_reward_stability_20261027_v1审计首次执行因错误要求每周期固定41250更新失败。阻抗39有原安全门早停：29×1375+555=40430，应该保留在30条件分母中，不能剔除失败。原FAILURE/WAIT_FAILURE保留。

独立v2仅将步数约束改为sum(30实际episodes.steps)，逐步检查optimizer连续范围及full-horizon数量；所有输入hash、39/40/41条件、原seed2026102743、5000bootstrap、5%、nearzero1保持。一次实际统计与保存值独立算术/图核验通过，未重算物理回合。

| 方法 | 39→40→41均值表现 | 原5%判据 |
|---|---|---|
| Impedance | −2.501148→−0.589016→−0.585222 | 40/41近零保护触发，百分比不适用，未判通过 |
| Admittance | −8.694325→−10.342627→−13.768370 | 相邻18.958%/33.123%，首尾58.360%，未通过 |
| VMC | −4.599550→−2.810016→−4.610525 | 相邻38.907%/64.075%，虽首尾仅0.239%仍未通过 |

导纳原固定1224跟踪41与保存算术审查完成，B/runs/admittance41_terminal_anchor_followup_20261027_v1：同旧1224终端masked SSE8555.943222→1413.843020，ratio0.1652468913，下降83.4753%；旧40分母贡献降到0.122705776。全终端population贡献0.132486585。此为固定旧终端诊断，0优化/物理/replay写入，不能当全部在线loss因果分解。A41任务/回报仍退步，不能以该局部拟合改善宣布收敛。

## GPU、远端与下一步

本机重新启动后四卡最初无计算进程；实际为4张NVIDIA GeForce RTX4090，CPU cgroup额度55核、内存400GiB，当前共享SSD约4.6TiB可用。正式分配仍CPU0–51，辅助52–54。环境依赖已通过实际恢复与物理评估入口执行验证。

首新窗口60样本/123.351秒，GPU0–3均值42.5/69.45/61.1167/63.6667%。包含四正式+三冻结41推理，非纯正式归因，不宣称每瞬时≥50%。GPU0未达标：启动了新增2000步后单次稳定窗口，见reboot_resume_20261027_v1/steady_gpu_after_startup；此前读到CPU cgroup无节流、Direct主线程在CPU0运行。观察不制造额外GPU负载，不改batch/UTD或重复已完成实验。稳定窗口已完成60样本/123.587秒，均值42.7333/64.55/68.75/68.4%，GPU0仍低于50%，因此额外登记一次30秒/50Hz非阻塞py-spy只读Direct栈采样，源码/命令和结果在reboot_resume_20261027_v1/direct_profile。独立安装py-spy0.4.1到runtime/profiling_pyspy_0_4_1，不修改两个训练环境的已安装依赖，不重启learner；低利用率原因需由采样结果判断。

本轮真实查询/fetch/read main `822e5da08322674666359d9d4d7d61c59598d111`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。远端新增为另一主机非RL经典补测与Task条件SPT；其日志明确不追改另一RL协议。本RL仍原冻结物理/SPT协议，不能把另一机3/72或108完成当本RL收敛。

下一轮先核验本轮原四learner、冻结41和审查进程及实际steps，避免重复。优先处理GPU0稳定窗口/真实瓶颈，收齐参数42与Direct恢复26完整checkpoint、full review/health后再登记有限后继；完成冻结41。Direct原24–26与旧26冻结入口继续禁用，重新审查恢复链后建立新的前瞻稳定性窗口和冻结评估。最终充分收敛、完整公平比较、泛化及指定ESN/SPT仍未完成，不索要此前已经问过的ESN或GitHub凭据。
