# 完整参数45/Direct27与正式46/28（2026-10-27，Goal active）

用户要求继续至reward平稳、loss健康并完成原交接验证/比较；当前仍未整体达到。上一goal turn完成4m容量候选验证，本轮完成完整45/27审查、原43–45稳定性结果和正式46/28接续，属于实质进展，无子agent。

共享SSD B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；代码B/repository/SII_compliance，原HDD SII_compliance为入口。开工实际查询/fetch/read main80dafb2840751885f8a49fb5727516d8dc484267、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保留另一主机非RL30/72进度。小证据docs/evidence/RL_PARAMETER46_SERL28_20261027，LIVE_STATUS记录原PID身份/进度，MANIFEST记录所有副本hash；最终归档/发布另记。

## 完整参数45及固定43–45

`B/runs/parameter_capacity_pool30_cycle45_review_20261026_v1`全review/health/FINISHED通过；`parameter45_saved_review_20261027_v1`独立保存算术通过；两张health/稳定性图已目视检查。三路各30完整55秒、41250新增、无abort，旧replay/history精确保留、新reward重建误差0、optimizer/network有限、health只读状态不变。

|方法|总交互步|Task/Strict（/30）|reward均值|末次q_loss|首/末1000 q_loss|
|---|---:|---:|---:|---:|---:|
|阻抗|1893680|18/17|−2.422920694|2.481996775|2.740677 / 2.759868|
|导纳|1893500|12/12|−12.089458336|1.370126009|1.715937 / 1.373354|
|VMC|1894500|17/17|−2.766779335|0.524376035|0.633689 / 0.765695|

完整45 checkpoint：B/runs/parameter_capacity_pool30_cycle45_archive_20261026_v1/<method>/cycle_00045.pt。
- I SHA db34a5b4f5e9352506ea2ae89c76ef858c4ab168cb8ce78add0caee64bbe31e9
- A SHA 36e1112008af0ca17829b9371b05b25ac723dda303e3061ae7ed1dcec9305f6b
- V SHA e78ef003743a4f6a19ec19139def6f198c195e55b799a9eaca71f4373bc9d901

原固定43–45 waiter2190600已完成，`parameter_capacity43_45_reward_stability_20261027_v1/REVIEW.json`通过表示统计实现/输入检查通过，**不是三路稳定通过**。I触发近零保护（43均值−.543031），百分比判据禁用；A首尾变化41.118535%，V40.018269%，均不满足原5%。原seed2026102745/5000分类内配对条件bootstrap/近零1/真实回合长度/全部失败分母保持。
`parameter43_45_stability_saved_review_20261027_v1`独立核对所有输入hash、保存的30条件均值/差值/百分比/斜率/成功变化计数及图hash，未重跑bootstrap。条件组成敏感性不是独立训练seed或冻结策略性能。

44→45保存配对 `parameter44_45_saved_outcomes_20261027_v1`：I无成功切换、均值−.064442；V无切换、+.082164；A均值−3.353990，其中成功变化贡献−3.332891。A long0200/short0200/0600/0900失去Task/Strict，long0900恢复Task/Strict，short0000恢复Strict；Task净15→12/Strict14→12。原模型、gate与saved物理归约检查通过，0物理优化；不是loss或随机性因果分解。A loss下降而任务变差，I/V末段高于首段，不能声称整体健康收敛。

## 正式参数46、47准备与46–48窗口

正式 `parameter_capacity_pool30_cycle46_20261026_v1`：I1829718/A1829722/V1829726，UTC10:43:15启动；archive1829782、review1829785。准确45全learner/replay/RNG/history、下一65536及PRELAUNCH通过，原GPU1–3/CPU13–51/每路30sampler/batch65536/UTD1/terminal128/I-min/A-V-mean/actor-min/LR/物理不变，只一个有限周期，容量仍2m。
actual startup1829781已结束通过：I/A/V新增1000/1000/2000，旧回放、history、原优化器配置、30MJB/sampler/action/clock和新reward0误差保持。
47仅准备1858092，`parameter47_preparation_20261027_v1`，四runtime入口*parameter_capacity47*；7200秒等待完整46/health及三父退出后check-only，无自动训练。一次性轮次替换/AST/真实父PID/entry23/CPU39核验，准确46恢复仍待。

新前瞻固定46–48窗口1908379，`parameter_capacity46_48_reward_stability_20261027_v1`，在46三路零完整条件、47/48未启时登记；seed2026102747/5000/5%/近零1/真实长度，10800秒等待，原统计计算块除轮次标签逐字节一致，dpi144未改。0物理优化，无自动停止/训练。
窗口显式规定46/47为2m，48准确47→48进入已验证4m候选；保留历史entry23/旧marker，增加followup。48审查必须输出 `replay_capacity_followup`=新marker及 `current_replay_capacity`=4000000；48协议依赖保留46全部旧hash，恰增加 `parameter_replay_capacity4m_20261027.py` 和 `resume_cheq_capacity4m_pool30_20261027.py` 两项，分别绑定followup/helper与当前driver哈希。不能静默把这次容量边界当相同回放条件或因果效果。
4m候选仍未部署，准确47恢复、新48协议/双marker监视器及实际2m跨界验证仍待，见RL_PARAMETER_CAPACITY4M_20261027.md。部署时使用本窗口约定的原`parameter_capacity_pool30_cycle48_20261026_v1`和对应review命名；勿另起不匹配路径使固定窗口等待失效。

## 完整Direct27与正式28

完整27 `serl_recovery26_take27_review_20261027_v1`：1121790交互步/8934328 critic更新，30全55/noabort，Task/Strict0/0，reward−30.908317531，末loss.011174692，首/末1000 .011249371/.010699524；terminal MAE.049629074，32步TD MAE.049493156。全部旧1080540 raw/derived/history保留，新41250全部成熟，原930隔离pending保留，新pending0；动作/clock/model/reward0误差、finite/native health全state不变、独立保存算术及图通过。不以低loss与失败回报平稳代替任务健康收敛。
完整27 checkpoint `B/runs/serl_recovery26_take27_archive_20261027_v1/direct/cycle_00027.pt`，SHA e85376716ba6bcd1b6b89e3b365c289d0e7261de726f4b5ec201e081a2adad1d。

正式28 `B/runs/serl_take_cycle28_20261027_v1` learner1978250（start_ticks29377217），UTC10:47:36启动。新通用有限恢复driver实际完整27全learner/replay/RNG/history、原vs take三批65536与reload检查通过，原partial25恢复链和930隔离保持；仍原官方10critic随机2目标、8:1/batch65536/32步behavior return，CPU0/GPU0、30sampler CPU1–12、一个有限周期，无辅助权重。
startup1978253/archive1978254/fullreview1978257。实际首1000启动检查通过：1122790步/8942328critic，旧1121790 raw/derived/history精确，新增146 mature+854 pending，原930pending不变，30MJB/sampler/action/clock/reward0误差。startup cp SHA cb442934d745316accf9375420bee3eb718164d9f0a47a7f759462658527d083。

29仅准备2044155，`serl_take29_preparation_20261027_v1`，7200秒等完整28review/health/父退出后900秒check-only，无自动训练。通用driver与main hash保持，继承先前静态证据而不重跑；五模板/手动launcher AST/28→29/870终端/930pending检查通过，实际完整28恢复仍待。原Direct27–29固定waiter336744继续，不启动旧24–26或完整父25入口。

## 资源与接续

`parameter45_serl27_transition_20261027_v1` 原1615532已完成：只在原全部参数45或Direct27 learner退出后，将其原完整只读review及health迁到释放CPU13/0，未改正式learner/物理sampler/冻结41。记录原身份、每次实际affinity变化，保持新准备依赖FINISHED。
退出观察→后继spawn时间界：I234.50–236.51秒，A301.59–303.60秒，V303.60–305.60秒，Direct159.41–161.41秒。是进程观察界，不是精确GPU idle或首次优化时长；换轮有低利用，不加假负载、不重跑已完成GPU窗口。
冻结41原316550/316551/316552及review316553继续，全90尚未完，不重跑冻结32或Direct16。下一次先核四正式46/28和上述原准备/统计进程，依据完整父结果接47/29；各actual startup已通过，勿重复执行。
整体reward稳定/loss健康、冻结验证/泛化与最终ESN/SPT比较未完成，Goal active。大checkpoint/raw/runtime保持原共享SSD，HDD配额满仅更新既有LATEST指针；归档不冒充HDD或arm1全备份。
