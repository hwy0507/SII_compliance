# 参数44与Direct等价take27正式接续

Goal active。上一轮登记44恢复、43–45稳定窗口和27审查入口，本轮已收完整43/恢复26并正式启动44/take27，未重复训练或将阶段完成当作收敛。基础B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；代码B/repository/SII_compliance；小证据docs/evidence/RL_PARAMETER44_SERL_TAKE27_20261027。

## 当前正式运行

- 参数44：B/runs/parameter_capacity_pool30_cycle44_20261026_v1，I3195008/A3195009/V3195010，2026-10-27 09:26:05 UTC启动；GPU1/2/3、原CPU13–51，各30sampler。准确完整43全learner/replay/next65536恢复、PRELAUNCH通过；实际startup新增1000/1000/2000、旧全部replay/history/optimizer、30MJB/sampler/clock/action及新reward0误差通过。归档3195013、完整review3195014继续，startup3195012完成。
- Direct take27：B/runs/serl_recovery26_take27_20261027_v1，learner3712293/start_ticks28969795，09:39:41 UTC启动；GPU0/CPU0，30sampler共享CPU1–12。准确完整恢复26为父，原两臂单更新等价gate+实际完整26三批65536/reload全state检查均通过。正式部署已验证np.take读取，算法/采样分布/随机draw/字段顺序/optimizer不变。INITIAL_STATE_REVIEW和实际首1000 startup均通过（旧1080540回放保留，新144mature+856pending，旧930pending保持，新reward0误差）；startup3712297已结束，归档3712299、fullreview3712302继续。
- 冻结参数41原316550/316551/316552和review316553继续，全90尚未完成，勿重跑。
- 参数45仅恢复准备3232655：B/runs/parameter45_preparation_20261027_v1，7200秒等完整44及review/health后check-only，不自动训练。原固定43–45 waiter2190600继续，不重复登记或改阈值；45正式尚未启动。

两个正式阶段均单个有限周期，每方法最多41250新动作/33000000物理子步，原2m append/no-overwrite与history entry23、物理/MJB/gate/filter/dt5e-5不变，无辅助权重导入或无限自动接续。Direct28尚无已验证恢复入口，后续不能简单套旧完整父25/26 driver。

## 完整43科学结果

B/runs/parameter_capacity_pool30_cycle43_archive_20261026_v1保存三完整父；原review/health/FINISHED与独立保存算术B/runs/parameter43_saved_review_20261027_v1通过，诊断图已查看。三路30全55秒、无abort，新41250reward重建误差0，全部旧replay字段/history/2m marker保持，network/optimizer与所有保存optimizer数值有限。

| 方法 | 完整steps | Task/Strict | 平均reward | 最后q_loss | 首/末1000平均q_loss |
|---|---:|---:|---:|---:|---:|
| Impedance | 1811180 | 18/18 | −0.543030873 | 1.759946346 | 2.214874 / 1.990343 |
| Admittance | 1811000 | 15/14 | −8.566881964 | 1.138345122 | 1.464350 / 2.016501 |
| VMC | 1812000 | 17/16 | −4.612703379 | 0.585714579 | 0.892050 / 0.864179 |

I43改善Strict、A43任务/回报改善，但A末段loss上升；末单点loss较低不能抹去这段波动。当前不足以宣告整体健康稳定收敛，继续原前瞻43–45窗口与冻结41。

## 完整Direct恢复26与27准入

准确完整26 checkpoint SHA `a15ace5af79c539e8155704df23161f5814a32e2b5676ce0f97c85497f72f09b`，1080540steps/8604328critic/1075541outer。30全55秒/noabort，Task/Strict0/0，mean reward−30.906703397；末critic loss0.0110740634，首/末1000均值0.011998600/0.011340795。原health网络/optimizer/RNG未变，780真实终端；终端MAE约.04197067、成熟集合32步TD诊断MAE约.05005595，均为固定诊断pair/离策略局限，不能以低loss和失败平台回报判任务收敛。

恢复26全审查保留旧1039290 raw/derived/history，新增41250均成熟、无新pending；旧0–29共930 pending仍原样隔离。所有新32步behavior target独立标量重建、reward/action/clock映射通过。partial25仍不完整；没有伪造完整25或连接丢失的MuJoCo现场。

27实际check-only完整learner digest a79bbcf4ac4161e0f377b624ad7ae02b43e233c584ed6937ab52efb420f6bfc5、replay digest a9faf9dc0471ded2a5c403e74fb098c2a4104e873a98fc44727068ec6682f947；候选对原读取三批65536/随机状态、完整序列化恢复/nextbatch精确，两个错误边界拒绝，0优化物理。PRELAUNCH绑定26review/health/保存算术、原等价gate和27模板manifest。完整26新流30–59全部flush后27复用，旧930永久隔离保留，后续完整27应810终端而非把25补全后的840。

## 换轮与GPU实测安排

原43退出后，只把原只读review coordinator及当时子进程从共享CPU53移到已释放CPU13，后续health继承；44准备等其FINISHED，未改任何在途learner或冻结物理。原26退出后类似把只读review移到CPU0，health原入口设置CPU52后再移到空CPU0；27准备依赖其FINISHED，无正式并发抢占。完整迁移收据在两transition目录。

43→44原有界观察2915615已完成，进程退出→新spawn范围I286.13–288.15秒、A346.60–348.61秒、V358.70–360.72秒；不等于整卡准确idle时长，不宣称每瞬时50%。26的第一次独立退出观察时进程已不存在，旧脚本把初始化时刻误写last_seen_alive，原件保留为OBSERVATION_ORIGINAL，已更正为null并说明缺少最后live时间；不能据此捏造精确衔接时长。

新且仅一次部署后GPU观察B/runs/serl_take27_gpu_profile_20261027_v1，原observer3746077：要求实际startup通过且Direct新增至少2000步，再取60样本、间隔1秒（nvidia-smi开销另计），逐样本原7任务身份核验、记录GPU计算PID及真实Direct步数。基线是此前42.7333/64.55/68.75/68.4%混合窗口，不重跑旧窗口/额外训练，不把不同在线阶段和checkpoint时序的差异当纯因果速度提升。实际GPU_PROFILE与SAVED_RESULTS_REVIEW已完成：60样本/119.257508秒，GPU0–3均值63.716667/63.566667/64.183333/58.6%，本窗口均超过50。全部60样本恰7登记compute PID，GPU0仅正式Direct3712293；保存均值/1326新步和约11.1188steps/s独立算术核验。不是每瞬时保证，不将GPU0比此前高20.9833个百分点当严格因果提升；不重复该完成窗口。

## 接续与同步

优先读27实际startup/部署后GPU结果，核对原44推进、45恢复及43–45窗口；完整27后必须恢复新recovery_continuation_stage与930隔离pending，旧完整周期driver不能直接复用。冻结41全90、充分收敛/最终公平比较/泛化/指定ESN仍待，Goal保持active。无子agent。

本轮开工真实fetch/read main5edb997、baseline f6e8f8c，收尾远端变化另记；源码/大checkpoint/raw在共享SSD，HDD配额满，不声称arm1或HDD全备份。Git与验证小证据归档收据另附。

实际take27首1000 startup已通过：1081540steps/8612328critic，旧1080540 raw/derived/history、930历史pending保持，新144mature+856pending目标精确，30MJB/sampler/CPU affinity/clock/action及reward重建误差0；原startup3712297完成。新GPU observer3746077已进入原60样本采样，尚不提前给均值。

收尾真实fetch/read远端main2c1f639（含aa1f4c3，另一非RL经典18/72与第三条件归档），baseline仍f6e8f8c；已读新增日志，运行中的RL冻结源/协议不变，双方记录保留。

实际take27首1000 startup通过，旧1080540 raw/derived/history与930pending保持，新144mature+856pending、新reward0误差。部署后原3746077窗口已完成60样本/119.2575秒，GPU0–3均值63.7167/63.5667/64.1833/58.6%，均超过50；保存算术/全部7原compute PID逐样本核验，GPU0仅正式Direct。不是每瞬时保证或纯因果速度比，勿重跑原窗口。
科学提交1f3a8a0后安全合并远端2c1f639，合并提交6a37c0a；UPDATE_LOG双方完整逐行顺序核验保留。
