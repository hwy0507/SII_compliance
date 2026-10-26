# RL回报稳定性、完整冻结16与后继续训交接（2026-10-26）

原Goal active。按照原交接的“改善后回报稳定、优化健康、冻结策略验证”推进，尚未整体完成。当前30正式条件覆盖原建议中的32条件分母；不要求baseline任务成功才能承认回报稳定，也不把降低惩罚但不推进任务的平台称为任务学会。没有子agent。

## 实际位置与同步

计算主机为当前四卡RTX4090集群。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库R=B/repository/SII_compliance。原HDD SII_compliance路径为该仓库链接，大checkpoint/replay/raw只保存在SSD。此次再次查询、fetch并读取实际远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa及baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变。GitHub认证先前失败且用户已被询问，不重复索要凭据；最终push和归档状态见收据。

## Direct完整13–16回报与优化审计

B/runs/serl_cycles13_16_reward_stability_20261026_v1：冻结登记原始episode/optimizer日志、各轮完整REVIEW/DIAGNOSIS/FINISHED和协议hash。第13轮使用review_v2，不能误用未完成的v1。读取同一65536 batch正式阶段，核对30同身份/MJB/协议、全部165000条更新日志连续有限、原始reward和成功计数一致；0优化/0新物理。图已目视检查。

| 完整轮 | 平均reward | 末1000 critic loss | 末1000 alpha | terminal MAE | 32步TD MAE | Task/Strict |
|---|---:|---:|---:|---:|---:|---:|
|13|−31.066473|.0184803|.000887414|.0784644|.0619942|0/0（30例）|
|14|−31.033155|.0173838|.000801668|.0590950|.0574088|0/0（30例）|
|15|−31.004831|.0160087|.000739714|.0551734|.0538951|0/0（30例）|
|16|−30.932129|.0152321|.000671815|.0511442|.0484393|0/0（30例）|

末3轮14–16相邻均值绝对相对变化为.0912685%、.2344847%，首尾.3255392%，均≤5%；均值远离登记的1 reward单位近零保护区。斜率+.05051254/轮。13→16同条件配对平均变化+.13434326，28条件改善、2退步；在三类各10条件内部保持整条时间序列的5000次bootstrap（seed2026102625），变化95%敏感性区间[−.02962746,+.40435646]，斜率区间[−.01887003,+.13029883]。这些是条件组成敏感性，不是独立训练seed置信区间；在线收集时策略变化，不是冻结评估。回报稳定性5%描述检查通过，改善幅度小且不确定区间跨零，不自动停训、不解锁test、不宣布整体收敛。

B/runs/serl_cycles13_16_reward_terms_20261026_v1进一步聚合此前已物理重构验证的82500条transition奖励分项，逐条分项和与原reward一致，逐条件总和一致。13→16平均分项变化：progress+.00140974、occupancy−.00163858、torque_slew−.00233990、penetration+.08642161、peak_torque+.05049039；时间/终端/完成效率等为0。总和+.13434326，主要改善来自穿透与峰值力矩惩罚减小。两轮均30/30停在approach。应报告“回报趋稳、任务进展停滞”；不能把低loss/降低惩罚视为任务学会。温度整体趋小和initial熵低的问题由先前诊断保留，未部署失败的温度或actor-floor候选。

## 新冻结完整30条件验证（运行中，不能写已完成）

B/runs/serl_cycle16_frozen_full30_20261026_v1。登记时最新完整父为16，checkpoint SHA d2ee183f0ebbafa44dabb8dc318cc2091dfc031145a2192bd9a313f989067c5b。精确原完整learner/optimizer/RNG加载，正式文件只读、不写replay、不更新。使用原随机策略、外部动作seed2026102626、每条件由ID导出独立seed；不是使用actor-floor、固定噪声或nominal混合。

固定预算30原训练条件×55秒，最多33000000个dt5e-5子步；两shard按原条件列表交错分成15+15。原evaluator PID1749189/1749193，物理CPU53/54，推理CPU52/GPU0；只读物理/filter/torque reviewer1749197。每个shard均通过外部种子可复现/不同种子改变动作/全state不变的有限gate，实际物理已开始；查原RESULTS/POLICY_UNCHANGED/REVIEW/FAILURE，不重复启动。source runtime B/runtime/serl_cycle16_frozen_full30_20261026_v1完整冻结并登记hash。单个shard不是完整矩阵，须合并30唯一条件并完成审计才能称完整。

这是单训练seed、单外部动作seed的训练集冻结策略验证；不是held-out测试、独立训练重复、确定性mode或最终ESN比较。保留全部失败和无接触NA，不选最终SPT_empirical参考。指定ESN仍缺，前次已询问，不重复问或用旧ESN替代。

## 正式训练与续接

Direct17原4158035、归档4158038/完整review4158039继续；不修改正在执行的源码。官方10critic/random2-min bootstrap/noentropy backup/8critic:1actor保持；actor用all10 mean。canonical48/action7、32步目标、batch65536/gather+transfer、所有历史state/markers/replay/RNG保持。public0=0 nominal，越大越减慢WBC；gamma^(k−1)mask由learner再乘gamma是正确gamma^k，不改。

Direct18准备/启动/监视脚本已写入B/runtime/*serl_batch18*20261026.py；等待准备PID1660818只在完整17 REVIEW/DIAGNOSIS/FINISHED通过后做check-only，不自动训练。末17终端数540，18审查570；CPU范围(1,13)及历史batch试验不能随轮号替换。正式18尚未启动，以后续LAUNCH为准。

参数26原I904989/A904991/V904993、归档905057/完整review905060继续。27准备/启动/监视脚本位于B/runtime/*parameter_capacity27*20261026.py；等待准备PID1633945仅等完整26后check-only，不自动训练。保持2m append replay容量与历史入口23、pair learner、原batch65536/UTD1/terminal128/projection/Imin+A/Vmean、原LR；必须capacity replay loader。大于原1m后的保留旧行采样与原ring覆盖不等价，不能隐去。

参数稳定性审计已预先固定容量阶段24–26、seed2026102627/5000次条件bootstrap/近零1/5%判据。B/runs/parameter_capacity24_26_reward_stability_20261026_v1原等待PID1811254，只等完整26审查后冻结输入hash再做0优化/0物理审计。不能把23→24扩容混作不变阶段；必须区分loss有限和优化健康。

## 算力与剩余事项

先前纯正式17/26的180样本208.44秒窗口四卡均值56.53/72.63/71.00/71.61%，仅适用于该窗口。当前新增冻结推理共享GPU0，不能用当前混合占用冒充纯训练达标；回合尾部和恢复检查空闲须如实记录。已预先准备下一轮，完整审查/恢复检查通过后及时衔接，不重复已完成探针制造负载。

当前仍待完整26稳定性与健康解释、27正式衔接、完整17检查与18衔接、冻结16全部30条件和物理审计，以及最终多seed/指定ESN比较。整体Goal保持active。

## 第26轮完成后的实测更新（覆盖上面的26运行中/27待启动快照）

完整26已通过全旧replay/history/2m marker/finite审查，三路各新增41250的SPT reward重构误差0；全部30条件55秒完整、无abort。原26 learner/归档/完整review均退出，禁止重启。健康图和24–26稳定性图均已目视审查。

| 方法 | 完整steps/updates | Task/Strict（30例） | reward | 末1000 q_loss | terminal/inbag MAE | Qmean |
|---|---|---|---:|---:|---|---:|
|阻抗|1110750/1105751|18/17|−2.231404|1.698353|.802874/.259679|−5.341276|
|导纳|1109750/1104751|12/11|−13.657883|2.150401|.832421/.435008|10.008714|
|VMC|1110750/1105751|17/17|−2.807895|.811671|.636377/.342623|19.238332|

精确26父SHA：I 5f8ebb47f36cf19d3870b00ba7ce069c790a3923a5d8b1b9ad69b8be5f215f3a；A ec5024083d50f7bc251e32ef9116b376f8b6481c7d341aae2e2de5edce150ff7；V b72539cb92cc43869226b52033e179d040b1ae8d35af43ab3d6fd888b512ae59。路径B/runs/parameter_capacity_pool30_cycle26_archive_20261026_v1/{method}/cycle_00026.pt。

容量24–26审计已完成，原1811254退出勿重跑。阻抗相邻均值变化2.1504%、3.7682%，首尾1.6988%，5%描述检查通过；配对+.038562，条件敏感性95%区间[−.028496,+.108954]，15改善/15退步。阻抗整轮平均loss1.4654→1.6905→1.8161，尽管最新末段从1.8563回落到1.6984，不能只因reward稳定就称优化健康。

导纳相邻变化22.7468%、155.5372%，首尾97.4106%，未稳定；24→26配对−6.73937，条件敏感性区间[−13.46574,−1.60476]。末段loss由25的1.1999增至26的2.1504，终端inbag误差.2218→.4350；同轮前约34000更新loss接近1.2，末段明显抬升。VMC相邻变化27.6063%、39.1665%，首尾55.9604%，回报改善但未稳定；配对+3.56794，区间[−.00004009,+8.849149]，末loss1.6292→.8117。bootstrap局限同前；不存在独立训练seed证据。

最新健康诊断A/V的20480个Q样本分别有.000439453/.001171875比例超过当前alpha下全局必要上界（I为0），误差与尖峰保留，不能宣称全部价值校准通过。全state有限/无abort不等于没有优化异常。决定保留完整26原state续一个有限27，观察新一轮响应；不回滚、重置或盲目改学习率。

27三check-only完整learner、旧replay、下一65536采样及RNG精确通过，容量/历史入口与负守卫保持；正式27已于21:15:55 UTC启动，I2286139/A2286140/V2286141。startup2286143、归档2286144、完整review2286145。B/runs/parameter_capacity_pool30_cycle27_20261026_v1；无自动28。实际各1000新增startup状态以startup/REVIEW.json为准，未完成前不写通过。

为缩短交接空闲，仅在原26 learner退出后，把原只读review905060/905091移至释放CPU13；随后准备2237108放CPU13、check-only A2256390/V2256391放CPU26/39，避免争用冻结物理53/54。相关TRANSITION_CPU_ASSIGNMENT.json留档；未改源码/精度/学习state，全部在正式27前结束。A/V完整26至27派发间有约4分半必要审查恢复等待，不能声称GPU从未空闲。以后可在已释放的正式CPU组完成这些只读交接步骤来减少争用。

新27固定首5000 optimizer记录只读检查已登记（各方法首次5000、末1000为该前缀内部），原PID2339586，B/runs/parameter_capacity_pool30_cycle27_20261026_v1/first5000_loss_audit；用于追踪26末loss抬升后的响应，不是完整轮稳定性或因果证明，不重复已有25结果。先查原REVIEW再决定后续。

27实际各1000新增startup已通过：旧I/V1110750、A1109750全字段prefix/history/优化器/2m marker/30MJB/30sampler/action/clock及新reward0误差，原2286143退出勿重跑。固定首5000只读检查2339586已完成，末1000 q_loss为I1.353320/A1.708645/V.777713；相较26末回落，但A仍高于25末1.199879，只是早期响应，不是完整健康稳定。

新A26终端与loss时序审计B/runs/admittance26_terminal_loss_20261026_v1原2457889已完，0优化/物理，不重跑。25→26丢Strict的5条件为active_short0900、active_short0600、active_long0300/0500/0200，无新增Strict成功。short0600第1103001步（本轮index34500）任务仍成功但Strict失败，终端reward−28.4719、全回合16.7071→−34.7528；此前1000 loss1.22215、从该步起1000 loss2.60524，时序与末段抬升相邻。窗口重叠/策略变化，未追踪实际抽到的replay批，不能当单条终端导致尖峰的因果证明，不据此改terminal128或LR。

Direct18准备尚未执行前，已将准备/check-only设为释放CPU0，并加原4158035退出守卫，仍须完整17 review后执行，避免争用冻结物理CPU54；decision在B/runtime/serl18_preparation_cpu_decision.json。正式18是否已启动以新LAUNCH为准。冻结16目前两分片各已完成3条，全部矩阵尚未完成，不能提前写全state最终不变/独立物理审计完成。
