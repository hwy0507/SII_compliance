# 持续推进记录（2026-09-23）

## 最新授权：VMC teacher＋ESN 联合优化（2026-09-27）

用户已要求修改目标并继续科研。以
[联合优化目标](ESN_VMC_JOINT_OBJECTIVE_20260927.md)为当前执行依据。
此前末尾 blocked/等待物理标定是历史状态，不再构成软件实验阻塞；
没有证据证明 teacher 或 ESN 已被充分优化。原纯本体、物理、安全门、
保留布局和完整失败存档要求不变。J1 固定八回合 teacher 机制筛查已定义，
从 R36 冻结源码隔离运行；不得覆盖旧结果。Spark 另有 Simba 训练，保留它，
本轮最多两个新仿真 worker。结果状态见新目标文档，未完成不得写成成功。

最新进展：J1 八回合 teacher 筛查已全完成，task8/8、strict4/8（所有强球撞
仍越限），11,000 步动作/状态重放与八条物理子步指标审计通过。J2 因 Spark
短时网络中断转本机单 worker，J3 在恢复后的 Spark 用两个 worker 验证剩余
四开发条件。没有重复运行 J1、没有新 ESN checkpoint。所有服务、路径、
hash、结果权衡及后续验收见[联合优化进展](ESN_VMC_JOINT_PROGRESS_20260927.md)。

用户授权下班后继续自主修正、运行 baseline，并给出可解释结果。此文件是后续唤醒的入口，不代表未完成实验已经取得结果。

## 当前状态：PPO三seed与SAC13六条件结果均已验收（2026-09-25恢复）

### ESN R3 与工作区状态（2026-09-25）

ESN R3 新开发集 `9320/9321/9322` 已完成，结果为 task `2/3`、strict gate
`1/3`；9320 穿透 `0.20770 mm`，9321 通过 gate，9322 抬升不足且终点误差
`221.56 mm`。因此不进入 blind validation，也不声称真实环境可用。R3 详情和
三条 raw rollout hash 见 [ESN_DAGGER_PROGRESS_20260925.md](ESN_DAGGER_PROGRESS_20260925.md)。

工作区检查已确认仓库稳定挂载于 `/home/airpig/桌面/hwy/compliance_control`。
此前“outputs 不存在”是命令在仓库上层 cwd 下使用相对 `code/...` 路径造成的映射
误报，不是挂载丢失或文件删除。后续使用绝对路径。R2 报告所引用的九条原始拟合
轨迹中目前仅能按 SHA256 恢复 `9310--9312` 三条；缺少其余六条时不执行 R3
12轨迹 readout refit，不用重建轨迹冒充原始输入。

### Proposed ESN follow-up (2026-09-25)

The proposed ESN is **not yet suitable for real-environment deployment**. The frozen six-condition result remains task `1/6`, strict `0/6`. A physical local parity rollout on fixture 9301 confirmed the frozen model can lift the payload (`0.2138 m`) but misses the final endpoint by `45.5 mm`. An offline history-only readout adapter improved teacher-action RMSE but failed badly in closed loop (`272.8 mm` endpoint error, `0.0042 m` lift), so offline imitation is not an acceptable success criterion.

The first student-on-policy VMC relabel pass was then evaluated without changing the reservoir, observation contract, safety filter, or gates. A conservative predeclared `beta=0.10` readout blend succeeded on 9301 (`6.3 mm` endpoint error, `0.2463 m` lift), but only `1/3` on development fixtures 9300/9301/9302; 9300 ended at `47.9 mm`, and 9302 at `90.4 mm` with insufficient lift. `beta=0.20` failed again on 9301 (`226.1 mm`). This is evidence that closed-loop distribution shift is the bottleneck, not evidence of a solved ESN or real-world readiness. Full table and hashes: [ESN_DAGGER_PROGRESS_20260925.md](ESN_DAGGER_PROGRESS_20260925.md). Next work is iterative student-on-policy collection and fixed VMC relabeling across all development fixtures, followed by untouched validation before any sim-to-real claim.

**SAC13 已完成**：服务器固定 plan SHA`125505dc0c07894c8c9d85bb04afd96d29bacc9a8a6927ab17bd68769bf3413a`，13/13 完成、0 execution error、zero7/9400 parity 通过；原始部署根保留在服务器 `outputs/sac_deployment_20260925_r1`，并已取回本地[395文件/854MiB归档](../outputs/sac_deployment_20260925_r1_archive)，rsync checksum dry-run零差异。独立报告已取回：[SAC13_RESULTS_20260925.md](evidence/canonical48_sac_20260925/SAC13_RESULTS_20260925.md)，JSON SHA`2dd33c0abf39346799afda68394b773d3970bd1d82e3e6abb3f52f11ac2c1db6`。两支均为同一训练 seed20260923，所有6条完整24s：online_only task/gate=0/6，waypoint RMSE`213.3874 mm`、实际峰矩`63.0880 N·m`、峰速`0.507779 m/s`；demo_prefill task/gate=0/6，`192.5289 mm`、`58.6043 N·m`、`0.470170 m/s`。demo分支的低一些均值不能视为任务改进：6条均停stage1、未到loaded-lift，online分支多停stage0/1；失败、接触不足和上游接触均保留。旧zero7六条仅作为匹配对照，不把parity样本重复计入均值。

**SAC准入现已审计通过**：完整根2.1GiB服务器/本机checksum零差异；两支各8192 Gym/reward/实际replay槽、8092次采样索引和在线RMS、actor/critic/entropy各8092真实更新及saved Adam计数均通过独立审计。主agent复核两报告全部15项artifact hash及实际更新数。报告[online_only](evidence/canonical48_sac_20260925/online_only_final.md) SHA`818c2a7883e6c8433621400a2984eeebde9e269e8fabe5a300857f3d5d113545`，[demo_prefill](evidence/canonical48_sac_20260925/demo_prefill_final.md) SHA`02936896178d223681cfc83e05ca4a8cb6468ed279fc3bc4999ec703a6ae8297`（均指同名JSON）。两支train/validation zero完整raw/transition/MJB exact；新SAC adapter同DGX CUDA对四条实际最终eval各600帧请求/执行/reset/RMS全exact，均无fallback。两最终learned评估均task/gate失败：online在两个条件都stage0，demo都stage1，全部24s但未抬物。额外600demo不保证学习成功；实际uniform replay的2,071,552次索引抽样中388,385次来自demo，不是50/50 RLPD。尚待独立SAC13部署工具/具体plan完成及审核，尚未新增物理。

**三seed主三指标现已完成**：[完整结果](PAIRED_MULTISEED_SIX_FIXTURE_RESULTS_20260925.md)，JSON SHA`7d9fac8c9a8c77ff36995df86c91f356cc6333ae87c6c83706a380cc09382683`。新增25条582文件/1,712,652,991 bytes归档checksum零差异，独立复算新24条learned及1parity，旧12learned+6nominal按固定hash复用；主agent再次核670项输入/工具hash及跨seed均值/总体SD通过。全部36 learned均完整24s；parameter6 task为[1,0,1]/6、direct7为[0,0,0]/6，strict全0。parameter6三seed均值±SD：155.760974±9.310115mm、38.952397±0.171136Nm、0.152618±0.008249m/s；direct7为136.940676±71.670986mm、35.044239±2.323292Nm、0.102683±0.044301m/s。SD按三个训练seed内六fixture均值计算，不把18条当独立训练。

direct7的seed24六条全停stage1、未触杆，49.645mm的低waypoint误差不是成功；seed25六条到stage3/触杆但物体全抬升不足，末6秒共同目标RMSE252.696mm。结果揭示小预算/单训练fixture方案的不稳定性，不支持挑选表现最好seed。旧25报告/源码冻结，后续SAC使用独立工具。

**当前下一步/分工**：SAC13条prepare/driver/report已在本机完成静态审查，固定为2支SAC各六fixture+1条zero7/9400 exact parity，复用旧zero7六条为匹配对照；但独立部署快照尚未同步到服务器，具体plan尚未冻结，因此尚未启动这13条物理评估。当前服务器无本项目仿真worker；勿重启已完成的PPO或SAC训练、25条PPO部署。SAC归档证书`evidence/canonical48_sac_20260925/archive_verification.json` SHA`9b3a6f0d06dae480f15233f9cd4232b200377dd88e9c56a5d430d29f78a64d79`，两端769文件/2,168,627,284 bytes、checksum空/exit0。本机以`PYTHONPATH=scripts:tools`运行完整测试为314 passed，`git diff --check`通过，无新MuJoCo环境。

## 历史运行记录（以下“最新/当前/尚未”均指当时，恢复工作以上节为准）

**当时实查**：25条PPO部署已结束；两支SAC也已COMPLETE，supervisor记录两实际returncode均0、总835.334s，各8192在线步/8092更新及原四项最终评估完成。完整归档/checksum、独立SAC审计、zero对照和真实部署adapter的同DGX CUDA输入回放正在收尾，尚不把训练结束标记当作成绩验收。主agent再次SSH实查全服仅既有WebUI Python、无本任务仿真worker，可用内存约116GiB；本机可用约11GiB，未开模拟。旧训练/部署PID均不重启。

baseline agent先收尾25条原始轨迹报告，再准备独立SAC13条driver/report；parameter agent负责完整SAC归档、zero/adapter回放与source，action agent独立审计。SAC六条件方案为两final策略各六fixture，加一条direct7 zero7/9400精确parity后复用旧zero7六条。初稿沿用PPO的nominal zero6 parity，review阶段已纠正；zero6与zero7是不同控制器，不能互相证明轨迹一致。新13条尚未冻结plan或启动，待具体plan、完整准入证据和资源复核后执行，不根据失败调gate或选checkpoint。

**最新状态（覆盖下方运行阶段）**：新增25/25部署已COMPLETE，active空、0执行错误，baseline agent正在完整归档checksum和独立50µs raw复算。driver汇总新两seed parameter6 task分别0/6、1/6，direct7均0/6，四组strict均0/6；nominalparity通过。此处仍是driver汇总，最终三seed主三指标须等独立报告，不提前填表。原deployment565765及两评估worker已结束，勿重跑。

SAC两支均已完成8192在线/8092更新，进入原固定train/validation × zero/SAC四项eval，尚无最终完整审计。8个2048/4096/6144/8192 checkpoint已取回，各zip显式seed20260923、步数、updates=step−100、实际actor/critic/entropy计数均一致；不从中选模。当前仅SAC自动评估占物理槽，最多2。新增SAC adapter/独立runner与13job方案正在准备（2final策略×6fixture+1zero9400 parity后复用旧zero六条），只做代码/只读回放，不自动启动。实际最终COMPLETE、完整归档/独立SAC审计、zero和同device adapter600输入回放齐后，才生成/审核新具体plan。

**SAC两支已实际启动（以下SAC未启动段均为历史）**：DGX `outputs/canonical48_sac_20260925_r1`，supervisor PID**569894**；online_only timeout/Python **569895/569896**，demo_prefill **569897/569898**。两支各seed20260923、8192在线步、标准SAC预期8092更新；额外示范分别0/600，固定最终checkpoint、CPU5/6各单环境单计算线程、每支7200s上限。最新进程核对为2SAC+2deployment=**全服4物理worker**，SAC各RSS约2.3GiB，启动MemAvailable122271277056 bytes。本机无新模拟。

SAC PLAN SHA`2a47e065b2fd8055ec67624a56e0942347e3d7a428f065d131803bdc284f4734`，BUILD`e13c350033469820f8125ca0f5bc2706c8f763e7fda816dde71e33df75153a6b`，supervisor`5de6a8284d279c1a725729289ea8793161277f933d2c0ab040c41a71292e4409`。主agent独立核本机和DGX201项source hash/readonly、两目标不存在及真实2空槽；DGX零仿真/零梯度preflight两初始网络/alpha/RMS exact、demo预填不改RNG，PREFLIGHT SHA`0b26d09fed4e92d02f5498ecf2836a49100919b2b805529edd5cea2fd55cf297`。实际启动后的初始产物/前101步一致性检查由parameter agent执行，不能把preflight当成实际训练前缀通过。

**真实SAC启动配对已验收**：`startup_pair_audit.json`确认两实际初始policy/alpha/RMS均匹配preflight且跨branch exact；前100 warmup及第101首次更新前所有记录的Gym action/obs/next/reward/done及全部实际replay字段逐值一致，首次entropy/critic/actor事件均step101/count1。整体zip/prefix hash因路径/metadata及600个预填槽偏移不同而不同，比较的是明确绑定的权重/数值字段，不要求整个文件字节相同；第101更新后自然分化允许。最新25deployment18/25、0执行错误；seed24两模型六条件均task/strict0，seed25尚未全完，禁止将部分结果当最终成绩。

SAC独立final审计工具已准备并主agentreview，覆盖全部Gym/replay/sample索引/在线统计/真实optimizer次数；未记录的sample张量字节、TD target/loss/梯度不冒称独立复算。末步恰终止时最后auto-reset obs可来自绑定normalizer.old_obs，明确无后继Gym journal独立见证。原整套249 tests后，新增finalaudit14+supervisor7共21项通过；没有更改运行snapshot。action agent待完整归档后进行真实SAC最终审计。当前尚无SAC成绩，25deployment最近14/25、无执行错误，保持原队列不重启。

**最新实际launch（优先于以下“未启动”历史段）**：DGX新输出`outputs/paired_multiseed_six_fixture_20260925_r1`，持久driver PID**565765**，启动自只读`outputs/paired_multiseed_deployment_source_20260925_r1/source`。真实plan SHA`c094ca89faa946e156843aa366592b43bc943f07c89f932c990d6273c6a5f467`，默认maxworkers2/confirmed slots2，全服≤4。主agent已审核确切25keys/4final模型，启动前再次核全部342input/173source、精确新输出不存在；实查全服仅WebUI、MemAvailable122415452KiB。先1条nominal9400精确parity，随后4模型9400，再余20；task/gate失败保留，执行错误停止新launch，不挑回合重试。baseline agent负责监控/归档/独立raw报告，勿重复启动。

新三seed主三指标**尚未形成**。SAC独立代码/无物理tests及review进行中，**尚未SAC训练**；参数agent已从PPO归档转为独立review。旧多seed训练queue549548已COMPLETE，4run全8192审计/8zero/4CUDA600回放通过、无fallback，整根3.8GiB末次checksum无差异。

**首条nominal已通过完整parity**：600帧、5NPZ/36字段逐值相等，JSON动力学和MJB相同；可复用旧nominal六条，parity不计性能均值。部署进入四模型9400预检，仍原driver565765，实际worker566449/566450；后续完整24条成绩待结束后raw复算。SAC当前12项真实SB3合成测试通过，主agent整套**249 tests passed**、diff检查通过；日志前后采样/RNG/全部policy参数及alpha/normalizer exact，final更新时序和terminal/partial成立。两agent独立review已过，parameter agent准备独立SAC source/两branch计划，尚未物理训练。

**部署后续进度**：四模型9400执行/对齐预检均通过，task/strict均失败且保留；已进入remaining20，最近状态6/25、0执行错误，worker567311/567591。nominal原9400任务失败但轨迹parity通过，二者不可混淆。主agent已读并批准SAC两个准备工具；拟独立`outputs/canonical48_sac_20260925_r1`，无物理preflight核两branch初始网络/alpha/RMS相同且demo不改RNG，随后等具体plan审核。实际SAC仍未启动。

**六run最终报告已完成**：[三训练seed汇总](PAIRED_THREE_SEED_COMPARISON_20260925.md)，JSON SHA`eec905398713208d024de84d90a322b48e5b1cd17bb45496ff7ff771aa21a3fb`。原seed20260923加新增两seed，每模式合计24576在线transition，6run全部final8192/384、24条最终eval完整保留。parameter6最终train成功1/3、validation0/3；direct7均0/3。新增4run整根3.8GiB归档checksum无差异，最后parameter6 flat audit SHA`80d9c7b93ea7328a39a0607de7bee4933480c9e621e3052f2ebef327783528e0`，主agent再核其7项artifact/flat哈希及zip seed/步数/更新均通过。训练queue已结束；以下运行中段均为历史。

action agent现转为已批准的[SAC/direct7方案](CANONICAL48_SAC_DIRECT7_PROPOSAL_20260925.md)实施与无物理测试，parameter agent收尾最后CUDA回放后独立审查，baseline agent收齐四run证据后冻结25条实际计划。**尚未SAC训练；尚未新增25条物理部署**。SAC标准uniform replay预填600demo不称RLPD，obs_rms仅在线train，实际post-add槽位和sample来源/terminal mask独立留档；需实现review和新source冻结后才能启动。

**最新完成标记（覆盖下方训练中状态）**：原多seed queue已COMPLETE，4/4 run、errors0、4806.06s；最后seed20260925 parameter6也COMPLETE，8192/384、2417.64s，train/validation最终PPO均task/gate失败。完整queue根目录（4run、全部日志与队列标记）增量归档、最后分支zero/独立审计/CUDA回放正在收尾；不得重启queue549548或原分支PID。

主agent已审查新增25job的prepare/driver/report，并独立SSH核`outputs/paired_multiseed_deployment_source_20260925_r1/source`的209项文件hash及只读权限；199原文件/165训练Python不变，仅加10文件。BUILD SHA`6ca2a7da41b994aa09fbd0cf8d9b82c74ee64f590e96a49b26aa200a9357ab6e`。最后证据齐后才生成具体plan并核查资源后启动，**25条仍未启动**。整套237 tests通过，之后两项driver清理测试及相关19项通过；原nominal9400的5NPZ/36数组只读self-parity通过。

**01:55接续更新（优先于下方01:31记录）**：新增4run中3条已完整归档并通过全8192独立审计、同模式zero原始轨迹/MJB精确对照和DGX CUDA600帧部署输入回放；最后seed20260925 parameter6也已达到8192/384，正在原队列的四项固定评估，尚无最终COMPLETE。不重启549548队列或552706分支。seed20260925 direct7最终train停stage0、validation到stage3但task失败；不同阶段的waypoint误差不可混作同一任务精度。完整证据见`evidence/paired_multiseed_20260924/seed20260925_direct7_final.md`及同名JSON。

下一步新增24条learned部署和1条nominal9400一致性复核的协议、prepare/driver/report已进入主agent审查；**这25条尚未启动**。先核最终4run证据、独立只读source及具体plan hash，再用最多2worker执行。统计先在各训练seed内汇总六fixture，再报告三个seed的分布；共享nominal六条不伪造为三次独立训练。当前本机可用约11GiB，未开新模拟。

**01:31心跳最新实查（UTC2026-09-24 17:31后，本段优先）**：持久队列549548正常，新增4run中**2已COMPLETE、2训练中，errors0**。seed20260924 parameter6/direct7各8192/384及四项eval结束，正在完整归档/独立审计，旧549559/549560不再作为运行依据。parameter6最终模型SHA`1b2dfab72987e94a0afd9e14a495369a9cf730acbf3f3b34954171dcb633ad8e`，direct7 `543bbc6bccd902f8039da4295817adc3099c72a96a11549198b3ac08cdf8e059`；从服务器完成摘要看，两模型train/validation PPO任务均失败，direct7两条均stage1，不能用当前waypoint误差冒充最终任务误差。下游正式成绩需全审计，不据这些结果改reward/选模型。

当前seed20260925 **parameter6 PID552706、direct7 PID552705**，首查2368/3200步、各RSS约2.4GiB、系统可用约112GiB；仍CPU5/6、各单线程CUDA、2物理worker。parameter agent接续归档/checkpoint/zero/离线部署parity，action agent接续完整8192审计；不重启稳定任务。baseline agent准备新增2seed×2模型×6fixtures=24条部署，另预先固定nominal9400原轨迹复核通过后复用原6nominal对照；当前只有协议/工具准备，尚未启动这组25条仿真。源、预算、gate与最终checkpoint规则保持原样。

上次00:30恢复时发现监控agent遭遇429限流，最后只报14/18；服务器作业并未中断。远端`outputs/paired_six_fixture_validation_20260924_r1/COMPLETE.json`和status证明**18/18已完成**，1543.4643s、source unchanged、0安全短回合。那次启动多seed队列前全服无本任务Python仿真worker、可用内存约116GiB；这不是当前资源状态，当前两worker见上段。本机一直未启动新增模拟。

- **已完成**：parameter6/direct7各8192步训练、四项冻结eval、各237文件完整归档与checksum、全8192独立transition审计、跨核zero/MJB exact、DGX CUDA600帧部署回放。parameter6 flat audit SHA`4fc389bc8b6c456a4ec7210b90ef2094af99127736ef1c8847775c3c611d1894`；direct7 `cdc544ef83fdb2972c3ec70ee19ab0b7c3baf48f20b9961885f3d62706ab8219`。
- **已完成的18部署**：plan SHA`8c42a62308007d210051f19dbe45b9a878df19450ca66b4545b63ff14d87864c`，原driver PID482611已结束，不重启。parameter6=1/6、direct7=0/6、nominal_train_vmc=1/6；strict全部0/6。完整归档及独立raw复算结果见下一条。
- **18条归档和报告均已完成**：`outputs/paired_six_fixture_validation_20260924_r1_archive`含464文件/1,249,993,338bytes，rsync checksum dry-run零差异（[证据](evidence/paired_gym_20260924/six_fixture_transfer_audit.md)）。[六条件结果及11方法附表](PAIRED_SIX_FIXTURE_RESULTS_20260924.md)重算全部新18条raw及原失败门；旧48条只绑定旧审计JSON复用，不能声称本次重算66条。主agent再核464项输入/工具hash全部匹配，JSON SHA`c417038bcc43c79ed52925cb942a7993b2eeb56595a9b731f92167adaf44b011`。周报已更新。
- **解释性结论**：parameter6对匹配nominal三指标均值均上升：RMSE147.493→155.205mm、峰矩38.5095→38.9733Nm、峰速0.148874→0.150369m/s；task同1/6，但成功fixture从9402换到9403，不是整体学习收益。direct7为135.982mm/38.3292Nm/0.156100m/s、task0/6；六条全到stage3/触杆，前四条能抬物但末端误差30.974–39.372mm未达15mm门，后两条抬物仅约25mm且长时间接触。旧fixture VMC与固定训练nominal有9组options不同，5/6→1/6的差距不能归于RL；详见周报参数表。
- **多seed已真实启动**：[复验协议](RL_PAIRED_MULTISEED_PROTOCOL_20260924.md)固定额外seed20260924/20260925，两分支各8192/同超参/同训练fixture/仅final，共4run。DGX根`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_multiseed_20260924_r1`，queue PID**549548**；当前20260924 parameter6/direct7 PID**549559/549560**、CPU5/6、各单线程CUDA。主agent实查512/544步、各RSS约2.29GiB、系统可用112.23GiB、errors0；不要重启原进程。20260925会在首对全部完成后自动运行，任何执行错误停止后续seed且保留已开始peer；每run7200s，最多2物理worker，全服上限4。
- **多seed冻结来源**：原196文件原样复制，仅加新入口/队列/协议，共199文件，原163执行源字节不变。主agent独立远端核199文件hash全部通过，manifest seed/8192预算及165 Python源集已核。BUILD SHA`84c6c1ab7b03256bfeebd257401d798d174033b60d71b19c320dca72634738e5`；PLAN SHA`ce54a417388bf2a351fac3b59cbf500f9ea6b2f02eb43813fff8b0e09d126c09`；本机同名根已保存BUILD/PLAN/PREFLIGHT/EXECUTION。前检0仿真worker/116.75GiB；没有重用旧模型或normalizer。
- **已完成的离线解释**：[训练行为诊断](PAIRED_TRAINING_BEHAVIOR_DIAGNOSIS_20260924.md)仅看8192训练transition和train zero/PPO，未用六验证选模。parameter6训练7/13完整回合task/gate通过，direct7为0/13；两者控制先验不同，不能把该差异全归因于RL学习。
- [训练行为完整修订诊断](PAIRED_TRAINING_BEHAVIOR_DIAGNOSIS_20260924_REVISED.md)区分K幅值与变化速率限制：训练探索85.828%步至少一轴限速，但确定性train/PPO仅11.5%，train/zero为0%；三者K幅值均未触界。逐episode从logscale=0重建clip公式且与原日志对齐，不能将训练探索限速比例推广到部署。原终端基础reward为0才可把折扣潜势return简化为−Φ(initial)；invalid/upstream处罚另计。
- **SAC仍未训练**：固定600条train demo进入真实SB3 ReplayBuffer的存取/归一化/终态掩码验收已通过，0仿真/0梯度。证据`docs/evidence/paired_gym_20260924/demo_r2_real_replay_verification.json`；仅证明数据接口，不是RLPD复现。
- **尚未完成**：新增多seed成绩、充分多fixture训练、canonical SAC/RLPD训练和新的office blind test。当前结果不支持proposed整体优势；不放宽gate、不剔除失败、不提交代码。
- **本轮检查**：原整套221 tests通过；后加持久队列4项无物理测试通过，包括首seed失败阻止后续seed、等待已开始peer及Popen后父侧写异常的有界子进程清理。`git diff --check`通过。后续完成run后须全归档/独立8192审计（强制finalzip seed存在且匹配）、对应zero原始轨迹/MJB及同设备回放；不能将运行中多seed当成成绩，也不直接复用seed20260923的六场景分数。

## 历史运行状态：DGX配对RL训练（2026-09-24，以下已被上节更新）

- **两条训练均已COMPLETE（UTC18:44:48确认）**：parameter6亦8192/384，2408.72s，最终zip`b572e3a20e0a7955ee9bf014f48579aa2c07507136c7ba8bf40a482a3306e33f`、normalizer`aee95256242c170b18b65c7998679d462121df61602fb90dfd592e362094a715`。train zero/PPO均task/gate通过，validation zero/PPO均失败；全四项评估及source_unchanged齐备。参数train-zero与原名义VMC24数组finite/exact、MJB exact；完整归档正在传输，尚待独立8192审计。direct7独立8192审计和DGX CUDA600帧部署回放均已通过，未使用fallback。UTC18:46资源检查全服无Python仿真worker、内存可用116.73GiB、目标输出/plan均不存在；18条仍未启动，需收齐参数证据后重新检查资源再launch。
- **最新完成状态（UTC18:36后）**：direct7已COMPLETE，8192真实transition/384updates、四项固定评估全部完成，最终zip实际SHA`07b1558bd19e37be6d3d112bacee8fb721b365785fadbe29e3bb888b024d4197`、normalizer`f2fd9398fa52c81821397efdc4de0eac56edc060815e51dfb040326301b18ef2`。完整237文件已归档，服务器/本机`rsync -rnic`为空且exit0，已交独立agent审计。冻结`compare_episode`跨核1→6确认27数组finite/exact、MJB exact及600步终态契约通过，见`direct7_cross_core_zero.json`。direct7训练/PPO及验证/PPO均task/gate失败，验证zero通过；保留全部结果。parameter6已达8192/384，checkpoint SHA`b572e3a20e0a7955ee9bf014f48579aa2c07507136c7ba8bf40a482a3306e33f`，仍在四项评估，尚未COMPLETE。18条部署尚未启动。
- **后续执行已获条件授权，不需重复请示**：两branch最终COMPLETE、独立flat8192 transition审计、同device动作回放、跨核zero原始轨迹/MJB等价全部通过后，parameter agent可直接从已上传部署ROOT生成唯一18job plan，核全服真实worker/内存及目标不存在，确认至少2空槽且总并发≤4，再启动默认2worker driver。默认新输出`outputs/paired_six_fixture_validation_20260924_r1`；任何证据/执行/对齐不一致先保留诊断，不绕过、不重复job。task/gate失败是正常保留的实验结果，不能据此改变模型或停止挑样本。此授权不表示18条已经启动。
- **报告链也已备妥**：`tools/report_paired_final_audit_20260924.py`生成final8192报告及供prepare读取的flat原审计，合法安全早停保留真实时长/末min10帧；`tools/report_paired_six_fixture_20260924.py`消费18条完整归档并复算新raw，旧48条仅绑定已审计JSON复用。旧八方法JSON为`docs/PPO_POTENTIAL_DGX_RESULTS_20260924.json`，SHA256`ec921c8d04cc6af12b822548690f59b87ec5262342dd43b0d811ec7c3b2a6e9b`；可选11方法附表，不声称本次重算旧48。新增报告检查后主agent整套 **211 passed**，diff检查通过；尚无新18条真实比较报告。
- 新parameter6/direct7 Gym完整24s proofs均已通过，独立agent对两份600步transition/reward/controller日志审计通过；163执行源及134模型资产、fixture/runtime/device/nominal/protocol逐项相同。见[完整验收报告](PAIRED_GYM_PARITY_RESULTS_20260924.md)。parameter6 zero6与原名义VMC逐值同轨迹且task/gate true；direct7 zero7与原零动作逐值同轨迹且task/gate false。只证明桥接，不是学到的策略结果。
- **两条8192训练已实际启动**，服务器根`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_parameter_action_20260924_r1`。parameter6 timeout/Python为**472043/472046**，输出`training/parameter6`、日志`training_parameter6.log`；direct7为**472044/472045**，输出`training/direct7`、日志`training_direct7.log`。PID须结合完整命令核查，不能重启稳定作业。每条7200s上限、单环境/单线程，共2物理worker；CPU5/6为3.9GHz大核，同CUDA GB10。验收用了小核0/1，训练完成后还须核train zero与proof/名义参考的原始轨迹，差异须保留诊断。
- 两条共同seed20260923、potential reward、网络128×128、原PPO参数和8192真实互动预算，最后checkpoint固定、不据验证挑选。参数分支adapter始终使用完整训练nominal options；验证runtime scene/CORE按原fixture保留，日志区分这两来源。原所有失败PPO、经典控制器及proposed未覆盖。
- 只读source SHA：Gym`df37f7fb5aae99e2d430fb4fd3fbad218bf0716513bf961a8f3ca03af3e5482b`；入口`64b7c0dc315e25094c4e658d5e5193e82c8f7acd59f9de05db161663500b76cf`；总协议`d14cf2545489475f41ea407235cf0e21be6b109120d8506c2c10ace38f6174d3`。后续新增部署代码不同步进该snapshot；每次transition立即保存pre/next raw48、参数/K/D/action7/reward/terminal mask，另保存实际SB3 float32 reward；partial末真实next补齐，终态无actor观测则显式占位valid=false。
- 下一检查先读两个`progress.json`和`COMPLETE/FAILED`，训练结束会自动固定final模型并各跑train/validation × zero/PPO四条评估。收齐后需完整transition和partial末reward独立审计、source/model/asset哈希核验、跨核zero raw exact核验；没有最终标记前不报告学会任务。本机没有新MuJoCo训练。另agent在准备之后18条共同部署，仅代码/协议准备，不启动物理worker。
- **部署执行链已通过静态review并复制到DGX，18条尚未启动**：[18条协议](RL_PAIRED_SIX_FIXTURE_DEPLOYMENT_PROTOCOL_20260924.md)、[driver说明](RL_PAIRED_DEPLOYMENT_DRIVER_20260924.md)及独立loader/replay/plan/driver已准备。新增20项部署相关测试与9项示范导出测试通过，主agent整套 **201 passed**、`git diff --check`通过。计划绑定两份全8192 transition审计、实际SB3奖励日志及每episode hash。安全早停保留短前缀，600帧验收不足时仅用固定同branch proof raw作离线回放；不伪造后续物理、不因任务失败排除方法。driver先9400三方法再余15条，默认2worker，程序/对齐错误停止新增、已启动回合保留；真实旧VMC9400的480000子步复算已通过。
- **部署独立快照**：本机/DGX同名`outputs/paired_deployment_source_20260924_r1/source`，BUILD SHA256`0b326b8231056bb73f6d4637020bec5ba22ea487e2134169cbf7547527a106b5`。由已验收训练源复制196个原文件，只加10新文件；主agent上传后独立核206项hash及5模块导入全部通过、零仿真，证据`docs/evidence/paired_gym_20260924/deployment_source_upload_verification.json`。当前工作区`run_panel_classical_matrix_20260923.py`与训练源的唯一旧文件差异完整保留，未覆盖用户文件；独立快照保留原163冻结Python字节，plan每job前后全量核验，不只核入口。后续必须从此部署ROOT运行工具，不能从当前混合工作区直接生成plan或覆盖训练源。
- **SAC/RLPD数据准备完成，尚未训练**：[train-only示范说明](TRAIN_ONLY_SAC_RLPD_DEMO_FEASIBILITY_20260924.md)。固定预选parameter6 zero6 proof全600步导出真实execution_action7、raw48、原reward及done/timeout/next-valid，不读validation/test、不按成功筛选。推荐`outputs/train_only_action7_demo_20260924_r2`，manifest SHA256`9f9092c03abcbf80cbf3e036552fbd9d6a214cdd21af8dded5eed1c402eb0a56`。root review发现r1手工保留yield与SB3统一float32 scale表达式存在3349元素、最大5.96e−8舍入差；r1及原manifest完整保留，r2只修正actions_sac，600×7与实际SB3逐值一致，其余obs/next/执行动作/reward/mask均与r1exact。9项测试和真实差异证据在`docs/evidence/paired_gym_20260924/demo_r2_sb3_scale_action_verification.json`。示范属于额外600训练数据，不把8192在线+600示范称为与8192 online-only同总数据，也不把数据导出当作RLPD复现。
- **2048里程碑已确证**：parameter6实际2048步/459.47s，direct7实际2112步/457.16s；两份2048 checkpoint的model内部步数及96次更新与metadata一致，model/normalizer哈希完整见`docs/evidence/paired_training_20260924/milestone_2048.json`。RSS各约2.33GiB、系统可用112.37GiB，没有COMPLETE/FAILED。参数模型hash`9c30eab3…`，direct模型`3109f70d…`；仅留存诊断，仍固定最终8192，不以中间结果改选。
- **后续里程碑（UTC18:21后）**：parameter6已4544步，4096模型确认192次更新；direct7已6304步，4096/6144模型分别192/288次更新，均与checkpoint内部值及metadata精确匹配。RSS2.36/2.34GiB、系统余量112.33GiB，未见FAILED或COMPLETE。完整哈希见`docs/evidence/paired_training_20260924/milestone_4096_direct6144.json`，新checkpoint已归档。不同策略每步计算耗时不同，不把训练速度解释为性能好坏；仍只采用最终8192模型。
- **direct7已完成8192优化步，四条冻结评估进行中（UTC18:26后）**：step8192 checkpoint内384次更新及hash已核验，证据`milestone_direct8192.json`；当前正在train/ppo评估，尚无分支COMPLETE，不能称四条评估或最终独立审计已完成。parameter6仍在5824步，RSS2.41GiB、系统余量112.16GiB。继续原进程，不重启；只有最终COMPLETE后才冻结部署模型hash并做离线loader parity。
- **parameter6的6144里程碑亦通过**：最新实际6688步/1504.57s，6144模型内部288次更新和hash匹配（`01b8c929…`；normalizer`88b026d1…`），见`milestone_parameter6144.json`。direct7已进入validation/zero评估，仍未COMPLETE；无FAILED，参数RSS2.37GiB、余量112.31GiB。两个分支进程继续稳定运行。

## 最新执行状态（2026-09-24，恢复后的新实验）

### 配对Gym验收已实际启动（训练尚未启动）

新wrapper、入口及独立transition审计器已完成静态review；主agent运行`PYTHONPATH=scripts OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python -m pytest -q tests`，**172 passed**，`git diff --check`通过。审计包含真实返回reward、SB3 float32转换、参数/VMC重放、terminal占位和partial最后next，不声称记录了critic/GAE内部值。

DGX独立冻结根`outputs/paired_parameter_action_20260924_r1`，两条proof已实际运行：parameter6 timeout/Python PID468143/468146；direct7 PID468144/468145。各单环境、1CPU线程、总2worker；后续必须按命令核对PID是否仍属本任务。parameter6新Gym zero6对既有名义VMC完整24s；direct7先同源zero7参考，再新Gym zero7完整24s。首查参数分支已有151条transition，直接分支仍运行参考，无执行错误。两份`proof/{mode}/manifest.json`保存源码/模型资产/协议hash、fixture、名义参数及运行时；此时只有验收，不能称配对训练已运行。

parameter agent归档后由action agent执行独立transition审计，两份proof及独立审计全部通过才启动8192配对训练。baseline agent另行准备六条件部署协议/独立loader，不占模拟worker，不修改当前snapshot。旧失败模型与原始轨迹继续保留。

### 01:38心跳恢复：下一轮配对训练准备

已核对三个agent完成状态、DGX7job COMPLETE与原始归档；本机/DGX均无遗留Python仿真，实查可用内存约11.2/116.8GiB。没有重启任何旧作业。八方法结果已补周报，潜势PPO六条全停stage1、推杆未触发，低waypoint RMSE不代表任务成功。

新[RL参数6/直接动作7配对协议](RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md)已在训练前固定：同DGX运行时、各8192步、seed20260923、原PPO参数、原potential reward、最终checkpoint；parameter6整个名义VMC固定为训练配置，validation不换teacher。parameter agent负责独立Gym/入口、完整transition记录及24s parity；action agent独立审查reset/terminal/partial/输入与公平边界；baseline agent只读补八方法共同最终目标末6s误差和扰动曝光。当前实现/验收准备中，**新训练尚未启动**。先完整parity/source冻结，再开展实训；服务器计划两条单环境合计2worker，上限仍4。

八方法纯离线补充已完成：[EIGHT_METHOD_FINAL_GOAL_EXPOSURE_20260924.md](EIGHT_METHOD_FINAL_GOAL_EXPOSURE_20260924.md)及JSON/工具。相同既有最终目标[.54,0,.785]、末6s/25Hz共150帧、48回合全部保留，246输入/工具hash复核。潜势PPO虽然原waypoint RMSE19.976mm，最终点残差263.756mm，且六条位置轨迹全同、stage1、未抓取/触杆，持续右指碰桌面20.11s。旧PPOstage0碰护板，末段最终点残差74.531mm不表示持物成功；zero进入stage3但触杆19.02–20.50s且失败。原五方法对应数值逐条重现此前共同窗口结果。该报告解释公平性边界，不修改主指标/reward/gate、不用于选模。

- **本机潜势奖励PPO8192及四条冻结评估全部完成**：`outputs/canonical48_ppo_potential_8192_20260924_r1/COMPLETE.json`，1802.29s、8192步/384updates；13完整回合+392步partial，旧PID76963/76964不再视作运行任务。最终模型SHA256`5f07bf8bac134c8464dd5daa8d8c4b46aa547525004ad37d0173d6cf0f3b1609`，normalizer`944f583cce8b73df5f0328a9f981e47f96cb986e7eb35384be26742e922d9f9a`。中间checkpoints全部保留不替换。13训练回合及rod/front最终PPO都task/gate失败；两条PPO都停stage1抓取对齐，尚未闭爪/抬升。
- [潜势奖励最终同平台比较（修订版）](PPO_POTENTIAL_FINAL_COMPARISON_20260924_REVISED.md)：旧→新PPO外部单对象合力峰rod976.29→206.49N、front1138.24→373.28N；当前waypoint末端误差变为15.74/15.49mm，但不是完成最终抬升的误差，不能判任务恢复。old front还停stage0，前后误差目标不同，不能作为同目标精度改善。两组zero各27原始数组全等、9核心源/完整fixture/133模型资产核对一致。新reward确已改变运行表现，但在该单seed/小预算下未恢复能力。
- 新奖励对齐既有RL开发gate，取消旧密集成本，采用有限回合终端潜势归零的差分奖励；**这改变了基础训练目标**，不声称与旧reward等价。保持seed、8192互动预算、48D/action7、优化参数、最终checkpoint选择不变。旧失败模型完整保留。未完成前不判断改善；以后不能用旧reward审计工具解释新reward。
- **DGX冻结旧PPO8192+zero六条件共12条已完成**：根`outputs/ppo_matched_validation_20260924_r1`，旧timeout PID448694已不再作为运行依据；564.29s完成，无执行错误，约782MB归档及12条480000子步指标复算通过。42条新旧验证在每个fixture的MJB完全相同，新12条初始48D观测与原VMC逐值相同。PPO/zero task及strict均0/6；PPO RMSE179.069mm、峰矩51.5716Nm、峰速.327079m/s，zero为209.466mm/31.8267Nm/.079997m/s。见[PPO_DGX_MATCHED_RESULTS_20260924.md](PPO_DGX_MATCHED_RESULTS_20260924.md)。不要重启，结果已纳入周报。
- 教师历史12条完整归档及审计已完成，task/gate均0/12，不入成功示范bank。新增[接触余量诊断](CONTACT_MARGIN_HISTORY_DIAGNOSIS_20260924.md)：30条峰值外部穿透均来自杆，22条越门量0.863–12.822μm；18000帧保存姿态未复现子步峰值，因此不能认定数值误差或改判通过。共同目标窗口的辅助结果仍显示ESN抬升/恢复不足。
- **contact sidecar三组6条全部完成并归档**：r2 driver457129已完成、worker释放；`outputs/contact_sidecar_20260924_r2_archive`及[CONTACT_SIDECAR_RESULTS_20260924.md](CONTACT_SIDECAR_RESULTS_20260924.md)。3组ON/OFF/历史全部18个rollout数组、physics/contact及物理子步raw逐值一致。r1的集合列表顺序FAILED完整保留；r2仅规范源码明确set字段，复用首对、只新跑后4条。r2协议SHA256`d754b8e28eaa24a399ddaa94e026f981e84635bcaf5919ee91bb1529671295aa`。
- 峰时证据：VMC9403/MLP9400/ESN9403都为杆×link7、stage3。峰深度分别.1993926/.2008633/.2128090mm，≥.2mm累计0/.25/1.00ms。保存完整步前/步后状态的scratch原碰撞查询复现峰值（不积分、不切CCD）；VMC约9e−16m差，MLP吻合、ESN约.0113μm差且仍越门。短峰解释25Hz漏采，不是放宽门或改判通过依据；solver诊断不等于物理误差界。
- 新增[RL→VMC参数接口](RL_VMC_PARAMETER_INTERFACE_20260924.md)及8项离线测试，包含真实CoreTeacher零参数一致性。独立review发现缺K/D时两构造器默认值不同，已强制显式名义K/D并测试。最终adapter SHA256`7f2cb469ed3c548f3b769be7a649b3ba21c3f921f5a31e4c3285db717376c5ea`。同train push_00000的原VMC/零旋钮两个24s闭环parity已结束（原timeout454725），独立 **FINITE_EXACT_AUDIT passed=true**：52数值数组全有限、原rollout/physics/contact exact、600×6零请求/零logscale及名义K/D exact、MJB一致，两条task/gate均true。证据`outputs/vmc_parameter_parity_archive_20260924_r1/parity/FINITE_EXACT_AUDIT.json`。原FAILED是contact.pairs/robot_bodies集合列表不同排列，原样保留；独立审计仅规范源码明确set字段，未排除真实动态差异。这不是调参RL训练，不重复启动；DGX成功不证明此前本机失败仅由硬件造成。
- 新reward的[独立审查](PPO_POTENTIAL_REWARD_REVIEW_20260924.md)未发现需中断的终止/bootstrap错误。[最终训练奖励审计](PPO_POTENTIAL_REWARD_AUDIT_20260924_FINAL.md)核对156冻结源，13完整回合势差折扣恒等式最大残差5.27e−16；392步partial只复算前391项，缺末next observation与实际SB3 reward buffer的限制保留。最近整套`PYTHONPATH=scripts ... pytest -q tests` **148项通过**。不要在仓库根无路径运行pytest，outputs含多个旧测试副本会造成重复模块收集错误。
- **潜势最终PPO DGX部署7条已全部完成并归档审计**。远程`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/ppo_potential_validation_20260924_r1`，299.00s、无执行错误；旧timeout/driver PID462791/462792已结束，不再视作运行任务。最多2worker完成模型六条及zero9400重验，后者全部原始NPZ（含子步）有限且与旧对照逐元素一致，其余5zero复用旧完整归档。DGX600帧动作parity maxerr2.980232e−7通过，normalizer冻结。[7job协议](PPO_POTENTIAL_DGX_PROTOCOL_20260924.md)在本机四条评估汇总完成前落盘，不因本机失败改动；只用最终8192模型，不选中间模型。458MiB完整本地归档`outputs/ppo_potential_dgx_archive_20260924_r1`，服务器/本机rsync checksum dry-run无差异，源码/模型哈希及全部7条子步三指标、时间轴、finite复算通过。
- **八方法DGX表已完成**：[PPO_POTENTIAL_DGX_RESULTS_20260924.md](PPO_POTENTIAL_DGX_RESULTS_20260924.md)。潜势PPO仍task0/6、strict0/6，全部24s，六条全停stage1且rod均未触发；子步RMSE19.9756mm、真实峰矩31.7391Nm、峰速.135352m/s。该RMSE针对当前stage waypoint，低值不代表完成抬升/搬运或恢复任务，也不能把未触发杆条件解释为更优接触响应。48条八方法记录沿用原42条并追加6条潜势PPO，本机指标未拼入DGX表，旧失败模型和结果全部保留。
- **后续必要工作**：优先实现真正RL-tune-VMC action6训练桥和transition全记录，目前调参方向只有已验证接口，没有训练成绩。具体待办见[VMC零参数结果与下一步](VMC_PARAMETER_ZERO_PARITY_RESULTS_20260924.md)：先Gym zero6=nominal同源闭环，再冻结同seed/budget/final规则，记录原始参数/K/D/action7/reward/next_obs，固定训练名义配置、不按验证换teacher参数。仍缺充分多fixture、多训练seed及canonical SAC/RLPD和office blind test，不为填满GPU重复无信息回合。当前本机和本分支DGX均无训练/评估队列，下一轮需先查资源并冻结新协议，不重启已结束潜势8192。
- 最终代码复核：`PYTHONPATH=scripts OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-canonical-rl/bin/python -m pytest -q tests`（解释器用工作区完整路径）**149 passed**；`git diff --check`通过。代码保持未提交，原冻结source/模型不覆盖。尚未完成论文级多条件/多训练seed RL及office blind test，不把运行中实验当作结果。所有稳定任务不重启。

## 最新恢复状态（2026-09-24 00:38起）

此前action/parameter两个agent因服务429限流中断；后续数次唤醒未形成新的工具执行证据，不能称这些时段持续开展了新实验。已独立启动的作业不受agent限流影响。此次恢复已先核对完成标记与PID，没有重跑。

- 服务器teacher history12条已完成独立归档和离线监督/slew误差分析，PID433583已退出；六对MJB一致，真实首次接触分别发生在approach/stage0及loaded-lift/stage3。固定teacher task0/12、gate0/12，不能作为成功演示直接补入训练。完整约796MiB本地归档及155源hash、2模型、12×480000物理子步复算均通过，见 [12条诊断结果与最小修正](TEACHER_HISTORY_DIAGNOSTIC_20260924.md)。
- 本机PPO8192-r2已完整完成且失败模型保留，不再训练。parameter agent正在准备同平台DGX最终checkpoint推理parity和新12条评估（PPO×6、zero×6），匹配已冻结9400–9405条件及原MJB/物理子步指标，独立snapshot、最多4worker；实际启动状态待其报告。
- 原106回合和7.25GB归档/78条raw复核已完成，不重复运行。baseline agent在已有归档上分析接触峰值来源与gate余量，不占服务器物理worker。
- 新增[训练目标审计](PPO_TRAINING_OBJECTIVE_AUDIT_20260924.md)：按冻结reward对13完整训练回合复算，唯一task成功回合的从reset折扣return排第13。gamma=.995下600步终端+5从起点只贡献.2483；密集waypoint误差可能与进度/静止验收存在激励差异。此证据不证明退化的唯一原因，不改已有reward、不选中间模型、不用validation调参。
- 当前同平台PPO比较尚未完成；不得把本机x86的PPO指标直接拼DGX表。后续实际进度以本节之后新增状态为准，以下历史记录保留。

## 固定教师接触历史诊断：已完成并独立审计

12条预声明24s回合于9月23日20:13:27启动、20:19:49全部完成（382.7秒），driver PID **433583已退出**。服务器输出 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/teacher_history_diagnostic_20260923_r1`，COMPLETE/FINAL_RESULT/status均确认完成，禁止重跑。随后结果读取因自动审批接口HTTP429限流暂停，9月24日恢复并完成独立分析；不是整夜持续新增实验。

完整本地归档 `outputs/teacher_history_diagnostic_20260923_r1_archive` 含12个MJB与全部物理子步原始数组。155项源码、2模型、12短trace/MJB的hash通过；12×480000物理子步峰值/误差独立复算通过；六组MJB完全相同且命令仅event_stage/output不同。approach六条未进入持物阶段，loaded六条全部末端误差>15mm。冻结ESN全程action RMSE虽低于MLP，角向slew误差却四组均高，不能当闭环改善。完整独立证据 `evidence/classical_20260923/teacher_history_audit_20260924/analysis.json`。不重训、不将失败批次加入成功bank；下一步先验证teacher补集资格。

冻结协议SHA256 `a395492482c7c116d0d9d327c8c8d1a0c88fea78927df1c0d9f9b87a2ff79c39`；本地副本 `evidence/classical_20260923/teacher_history_protocol.json`。按训练push最小ID选定teacher `push_00000`，新train seed9600/9601/9602、新validation seed9610/9611/9612，各approach/loaded_lift一条。1017项历史push及930x/940x物理描述检查无精确重叠；六组阶段配对除event_stage/output外参数完全相同。这里只验证局部数值物理配置不同，不声称未见布局泛化；未读test NPZ。结果只作冻结MLP/ESN在teacher轨迹上的动作与安全slew误差诊断，不替换冻结模型、不补抽失败seed，不作为student闭环性能结果。

## 最新状态（2026-09-23 19:35 唤醒）

- 已检查 driver PID413277 与命令，未重复启动。统一测量28/28完成；原24条每条18数组与旧实验完全一致。
- 经典固定预算开发搜索已到47/48，未见执行错误；最后一条结束后原driver会自动冻结selection并执行预先指定六条件×五方法的30条验证。当前最多4worker，服务器可用内存约116GiB。
- 已生成 [全物理子步三维比较](SUBSTEP_THREE_METRIC_COMPARISON_20260923.md)：原导纳25Hz峰速均值漏计约3.21%，其余方法约0.01%–0.77%；本模型实际峰矩与旧命令峰矩恰相同。所有原法的误差都主要来自抬升/恢复，详细XYZ和阶段贡献已列出。
- 本机PPO640及四条冻结评估已完整结束，不再是运行中。见 [canonical48 PPO报告](CANONICAL48_RL_PILOT_20260923.md)：rod零动作/PPO均失败，front均通过开发gate；PPO接触合力更高，尚无改善证据。27数组parity、60项静态重建检查通过。
- 本次重新派发三个agent：服务器收齐固定预算并审计；补全7方法同条件因果表及离线数据/记忆机制；PPO train-only诊断及同配置8192步新预算计划。后者须先检查原VMC同fixture和reward，实际新PID/输出待启动后记录，不能把计划当运行。
- 未放宽gate、未改变已冻结模型/搜索、未运行新的alpha筛选。以下按时间保留此前记录，状态以本节及后续更新为准。

### 本次唤醒后续更新（19:51）

- 48/48开发搜索已完成，无执行错误；预声明规则选出 `impedance_k900_z1.2`（task3/3、gate1/3）及 `admittance_k150_z0.7`（task2/3、gate2/3）。新条件验证已进入后半程，不凭中间结果改参数。
- 9301的七方法完整物理对照现已补齐：`docs/evidence/classical_20260923/measured_ablation_complete7/REPORT.md`。低通降低三方法峰速/矩，但ESN子步RMSE从150.49升至225.47mm，VMC从137.05升至207.97mm且任务从成功变失败，原反证结论成立。
- 本机 **PPO8192实际稳定运行**：`outputs/canonical48_ppo_8192_20260923_r2`，Python PID47496/timeout47495；读取独立只读源码 `outputs/canonical48_ppo_source_snapshot_20260923_r2`，不修改运行中的reward或接口。19:51进度1632步、RSS2.34GiB、系统余量9.16GiB，640前缀检查仍在跟进。每2048步更新后保存checkpoint；45min timeout保留中间证据。
- 早期8192-r1在最后记录416步时为源码隔离停止，保留 `INTERRUPTED.json`，不算完整种子、不再因此重复启动。PPO8192协议与train-only诊断见 [CANONICAL48_PPO_8192_PROTOCOL_20260923.md](CANONICAL48_PPO_8192_PROTOCOL_20260923.md)。
- 本机原VMC在恢复的rod训练fixture上也未完成任务（末端误差52.39mm），当前仅能证明静态配置重建。agent继续核对旧teacher runtime lineage，不能把历史accepted当作本次成功。
- 新teacher离线审计正在核查714个push训练参数组、实际接触阶段及固定抽样36条的标签重放。已有抽样教师在ESN低通新状态均给正x，而ESN给负x，因此不能把方向反转简单归因于教师参数混合；完整报告待审计结束。
- 当前全套 **117 tests passed**，原始捕获源码120个及Python语法全部验证通过。基于新子步报告已明确导纳内部参考速度整形与residual学生不同，不能仅凭约0.08m/s低峰速判优。

### 服务器本轮106回合已全部完成

已核对两级COMPLETE与campaign status=complete，PID413277已退出，48开发+30验证无执行错误。不再把服务器队列标为运行中，不重复启动。

六条件验证终值（task/gate，子步RMSE mm / 实际峰矩 Nm / 子步峰速 m/s）：阻抗6/6、1/6，67.6458/35.5451/.122216；导纳5/6、1/6，141.4174/35.9089/.079997；VMC5/6、1/6，148.1251/36.7591/.119597；MLP5/6、0/6，132.9366/36.6001/.145266；ESN1/6、0/6，160.2036/36.4644/.145770。不能宣称ESN更优，也不能把task通过当作完整验收。

终值已在 `docs/evidence/classical_20260923/fixed_budget/validation_final.json`，开发结果及selection也已归档。106条完整原始数据已复制到 `outputs/server_archive_20260923`，服务器/本机 `rsync -rnic` checksum dry-run无差异、退出0。[固定预算最终报告](CLASSICAL_FIXED_BUDGET_VALIDATION_20260923.md)及同名JSON已生成：48条选模与30条验证全部通过独立raw复核，包括600×48观测、480000物理样本、有限性和50μs/24s时间轴、float32物理峰速/峰矩/全程XYZ和分阶段RMSE、任务/gate、78个实际MJB与各fixture配对、134份冻结脚本及协议/两模型hash。未放宽rtol=1e-6/atol=1e-7舍入容差；独立选择与冻结选择函数均精确等于原selection。

本机 **PPO8192-r2已全部完成**：`outputs/canonical48_ppo_8192_20260923_r2/COMPLETE.json`，总1548.22s，8192真实transitions/384优化更新，13完整训练episode+392步partial；四条24s冻结评估齐全，进程正常结束，勿重复启动。2048/4096/6144/8192checkpoint均保留。最初640步observation/action/phase与旧640试验逐元素完全相同，完整源码snapshot hash始终未变。

固定最终PPO8192在rod/front均task=false、gate=false（final stage分别1/0），末端误差294.15/94.43mm、峰值外部合力976.29/1138.24N；rod最大外部穿透0.21233mm超过0.2mm。两条zero对照与640试验完全一致，rod失败/front通过。13个随机训练episode中1个task成功，但这不等于确定性部署成功；此次加预算后固定最终策略退化，未用中间checkpoint替换、未据验证调参。详见 [8192协议与最终结果](CANONICAL48_PPO_8192_PROTOCOL_20260923.md)。

Lineage审计已找到hash匹配历史source：完整VMC配置、estimated/memory、observer、WBC、安全core均匹配；初始q差约3.94e−8并在接触中放大，历史完整数值环境仍未知，不能断言硬件唯一原因。见 [teacher lineage](CANONICAL48_TEACHER_LINEAGE_20260923.md)。本机结果不拼接DGX三指标表。

纯48D→7D PPO部署adapter已实现，640checkpoint在DGX既有SB3环境离线600帧parity通过（maxerr4.47e−8）；8192本机CPU对GPU动作parity通过（1.19e−7）。没有启动新的DGX物理worker；后续需要同平台zero/VMC参考及冻结ESN/MLP共同fixture评估，见 [部署准备](CANONICAL48_PPO_DEPLOYMENT_20260923.md)。

### 下一阶段的已授权工作

- 教师参数/历史离线审计已完成，见 [TEACHER_MIXTURE_HISTORY_AUDIT_20260923.md](TEACHER_MIXTURE_HISTORY_AUDIT_20260923.md)。真实config去重为train714/validation227种。训练首次持物接触119/714，但687/714条有后续持物接触；累计25Hz持物接触样本时长中位train1.12s、validation7.12s。fixture与事件阶段耦合，不能单独认定记忆/参数混合是根因。
- `action_lit_resume` 已被派发将报告内12条固定教师、两启动阶段诊断具体化并启动：新3train+3validation物理fixture，各approach/loaded_lift，24s、至多4worker，固定训练来源teacher配置、协议/源码snapshot先冻结。不使用930x/940x训练，不读test轨迹，只做冻结MLP/ESN离线误差和接触历史诊断，不自动重训；实际PID/路径等它启动后记录，当前不要重复启动。
- `baseline_resume` 已完成106条raw全量归档及48+30条完整独立复核，552个开发job文件和336个验证job文件hash已写入最终报告JSON。原106队列不再运行；新12条教师诊断由action agent独立管理。
- `parameter_lit_resume` 在8192稳定训练之外，继续旧teacher/current VMC的lineage只读审计和PPO部署adapter准备；最终PPO若去DGX评估，必须与同平台zero/VMC等共同对照，不能把本机指标拼入DGX表。
- 本周报现在含后来新增的六条件验证段，不要用旧 `report_baseline_progress_20260923.py` 直接覆盖它；旧三条件工具需要重跑时另选输出文件，保留新结果。

## 持续执行

### 2026-09-25：ESN multi-trajectory DAgger checkpoint closed-loop result

The development-only checkpoint
`outputs/esn_onpolicy_dagger_multi_20260925_r1/onpolicy_multi_adapted.npz`
(SHA256 `ade53e8a06b306c60519b900eb5f4e8a86d212cf20e8a1c2069bba4800e35f2e`)
was physically rolled out with the fixed loaded-lift runner using the project
`.venv-rl` environment.  Seeds 9300/9301/9302 all failed task completion with
the same final trace: endpoint error 141.82 mm, lift 122.24 mm, substep RMSE
178.30 mm, peak actuator torque 41.18 Nm, substep peak speed 0.11882 m/s,
and maximum penetration 0.20242 mm.  All entered LOADED LIFT and retained
grasp/contact, so this is a post-contact closed-loop failure rather than a
missing trigger.  Each raw rollout has SHA256
`285c0a67f19f1fb70c76ff04486cfe94bbf6b7a24bd13eefdce46dda232ba010`.

This iteration lowered offline teacher-relabel action RMSE but produced no
development task success; it is not used for validation selection and does
not replace frozen proposed ESN.  The failed system-Python launch
(`gymnasium` missing) and the relative-path launch failure are retained as
execution diagnostics.  Next work is causal inspection of the common
readout/projected-action/safety-filter state before any further DAgger grid;
do not claim ESN real-environment readiness from this checkpoint.

The follow-up translation-only diagnostic adapted only action channels 1--3
and froze slowdown/rotation channels.  Its checkpoint SHA256 is
`06cdee0788188da935fd0359c65afe06559ad5d41d45098e5dbd658f5ccbc3e4`; it
reduced offline relabel RMSE to `0.0603012`, but its fixed-scene physical
replay still failed task and strict gate (endpoint 18.008 mm, lift 0.25048 m,
substep RMSE 162.047 mm, peak torque 37.894 Nm, peak speed 0.12316 m/s,
penetration 0.21034 mm).  This excludes the narrow hypothesis that the full
readout failure was caused only by altering slowdown/rotational outputs.  Both
diagnostics remain development-only and do not justify validation selection or
real-environment readiness.

### 2026-09-24：冻结PPO8192 DGX同平台12回合已完成

实际新服务器根：`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/ppo_matched_validation_20260924_r1`；timeout父PID448694（需结合命令确认），日志 `driver.log`，完整12job及源码/模型hash为 `evaluation/protocol.json`，进度 `evaluation/status.json`。独立 `source/` 由此前固定验证source逐字节复制并只增加loader/driver，设为只读；启动前全baseline Python文件hash一致。

协议 [PPO_DGX_MATCHED_PROTOCOL_20260924.md](PPO_DGX_MATCHED_PROTOCOL_20260924.md) 固定最后8192模型、normalizer和9400–9405六条件PPO+zero共12条。先串行PPO9400和zero9400，MJB和共享配置与原验证一致才启动余10条，最多4worker。原gate/50μs物理子步metrics完全沿用；零动作不使用settle_only；所有失败和安全提前终止保留。既有VMC/MLP/ESN/经典六条件结果用同平台/MJB匹配，禁止拼本机指标。

DGX最终8192离线600帧parity已通过，max绝对误差2.3841858e−7、normalizer冻结、clip±12。本次仅部署评价，PPO单rod/8192interaction训练预算与ESN imitation不同，不能称等训练预算baseline。

**服务器evaluation/COMPLETE.json已确认12/12完成**，耗时564.29s，无执行错误；PPO8192与zero均task0/6、strict gate0/6，所有fixture MJB与原验证一致、source snapshot未变。driver正常结束，已释放worker给独立contact sidecar任务，不再运行本队列。全12原始MJB/子步trace已归档至本机 `outputs/ppo_dgx_matched_archive_20260924_r1/evaluation`（约782MB），每条MJB/result hash核对、float32子步三指标独立复算、50μs时间轴和finite检查均通过；**12条首个48D观测与各自原VMC逐元素完全一致**。

同平台七方法42回合表见 [PPO_DGX_MATCHED_RESULTS_20260924.md](PPO_DGX_MATCHED_RESULTS_20260924.md)。PPO8192六条件均值：子步RMSE179.0691mm、真实峰矩51.5716Nm、子步峰速0.327079m/s；zero为209.4661mm、31.8267Nm、0.079997m/s。PPO相对zero误差较低但两个方法均0/6任务成功，且PPO更快/峰矩更大；不能用误差单指标判优，不能把训练不足的PPO当成RL方法上限。其他五法指标与已审计固定预算表一致。没有换中间模型隐藏失败。

### RL调参接口零参数闭环parity已启动（非训练）

服务器新根 `outputs/vmc_parameter_parity_20260924_r1`，timeout父PID454725，日志driver.log，parity/protocol.json记录两条完整command/env；各24s名义VMC与零参数VMC，同train push_00000、完整显式K/D、原48D/action7/WBC/physics，2worker，与contact sidecar2合计≤4。本机没有为该检查新开仿真，避免与潜势reward训练冲突。

独立只读snapshot的adapter最终hash为7f2cb469…，已纳入显式K/D缺省边界修正；主agentadapter本体没有被本分支修改。协议见 [VMC_PARAMETER_ZERO_PARITY_PROTOCOL_20260924.md](VMC_PARAMETER_ZERO_PARITY_PROTOCOL_20260924.md)。必须比较真实action、obs、physics/contact全部动态字段；teacher_action记录语义差异仅按预声明规则核对，不能事后排除动态差异。运行中snapshot保持不变；结束后还会独立检查所有数值数组finite，防止双方相同NaN/Inf被当作有效等价。尚未取得两条结果，不能声明调参RL训练完成。

- 已创建本任务每小时唤醒自动化 `sii-baseline`。本机需保持开机且应用运行；服务器已启动的独立作业不依赖本机界面，但新的检查/决策依赖唤醒。
- 项目根：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark`。
- 服务器：`arm1@192.168.31.70`，使用现有 SSH 密钥；项目 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`，Python `/home/arm1/vmc_mujoco_runtime/.venv/bin/python`。
- 本机 Python：`/home/airpig/桌面/hwy/compliance_control/.venv-rl/bin/python`；menagerie `/home/airpig/robots`。
- 本机约 16 GB 内存，此前 16 worker 导致 OOM。单 MuJoCo 训练环境、1–2 CPU 线程；服务器所有队列合计最多 4 个仿真 worker。先查现有作业，禁止重复启动。GPU 在 sandbox 内不可见不代表驱动损坏；agent 升权检查确认 RTX 5080 正常。不要因此重装驱动或重启。

## 当前三路分工

1. `baseline_resume`：独立测量 wrapper，统一记录物理子步末端速度、实际 actuator torque 与阶段误差；必须先验证加测量前后动力学轨迹不变，再服务器重跑 8 个方法/版本 × 3 条件。它统一管理服务器并发及 ESN 消融队列。
2. `action_lit_resume`：ESN/MLP/VMC 原始 trace 因果诊断，隔离 slowdown、平移 yield、旋转 yield 等作用；所有消融命名为开发诊断，不能替换 frozen proposed。
3. `parameter_lit_resume`：将 PPO 迁移到 canonical proprio48/action7 与 teacher split，先保证零动作和原 runner 一致，再小预算训练/冻结验证；只用 train/validation，不能用 test 选模型。
4. 主 agent：审阅实验设计与代码、固定经典控制器搜索预算及验证协议、汇总证据与进度。

## 已有可靠基线

见 [周报](BASELINE_WEEKLY_REPORT_20260923.md) 和 [经典接口修正记录](REFERENCE_CLASSICAL_DEVELOPMENT_20260923.md)。旧实验均已结束，105 项测试通过；原始 source export 120 项通过。当前三条件结果不能支持 ESN 整体占优，也不能从失格阻抗的低误差认定其最好。

- 原冻结模型和 teacher split：`CANONICAL_MODEL_PROVENANCE_20260923.md`。
- 原五方法、K300/K900 阻抗、r2 导纳是开发实验；r1 导纳执行错误保留。
- 指标旧口径：25 Hz waypoint RMSE、4 ms applied command torque、25 Hz speed peak。新的物理子步指标须独立命名，不与旧值拼表。
- 每个 fixture 的 9 个非 smoke MJB 哈希一致（含失败 r1 archive）；29 份含 smoke 的记录已核验。

## 当前诊断事实（消融尚待验证）

ESN/MLP/VMC 全部在 2.44 s 进入 loaded lift，失败并非未进入抬升阶段。ESN 在 9301/9302 的终点误差约 72.2/60.0 mm，而 VMC 约 5.7/11.0 mm。冻结 checkpoint 离线重播与原 action 相差小于 1e-15；观测归一化没有触发 ±12 裁剪差异。slowdown 的尾部值只导致约 90%/96% nominal scale，是否为失败主因需配对消融，不能凭相关性认定。

新增诊断见 [ESN_PANEL_CAUSAL_DIAGNOSIS_20260923.md](ESN_PANEL_CAUSAL_DIAGNOSIS_20260923.md)：ESN9301 尾部横向 action 逐帧正负交替，raw physical yield 均值 -0.00063 m/s，经共享 action slew 重放后为 -0.04169 m/s；MLP9302 也存在相似现象。这是动作与限速历史交互的证据，尚不等于闭环因果结论；后续还有关节投影，不能把该请求值称作实际末端速度。

## 本轮新增验证与队列（18:47 左右）

- 全套测试现为 **115 passed**（约 0.88 s；RL bridge 尚在开发，后续新测试另报）。
- 统一物理子步采样已通过 VMC/导纳 r2 各一对 8 s on/off smoke：18 个原 trace 数组逐元素相同，160000 个物理样本、50 μs 步长；测量开销约 6.2%/6.6%。确认只读测量没有扰动原轨迹。
- 服务器 agent 已固定顺序队列：9301 的 ESN x-off、ESN/MLP/VMC 同 alpha=.25 因果低通 4 条，随后原 8 版本 ×3 条件的 24 条统一测量。4 worker 池，优先消融。
- 上述 28 条全部执行成功且物理采样完整后，再启动经典参数 48 条开发搜索 +30 条共同验证。方案见 [CLASSICAL_TUNING_PROTOCOL_20260923.md](CLASSICAL_TUNING_PROTOCOL_20260923.md)，runner 为 `scripts/run_classical_fixed_budget_20260923.py`；已通过 5 项选择规则/失败保留/物理配对检查测试。
- **顺序 driver 已实际启动，PID 413277**（PID 需结合命令核对，不能将后续复用的 PID 当作同一进程）。远程 base 为 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923`；总日志 `base/measured_campaign.log`；状态 `base/measured_campaign/status.json`。
- 阶段一日志 `base/measured_campaign/measured.log`，28 条输出 `base/measured_campaign/measured28`；阶段二日志 `base/measured_campaign/fixed_budget.log`，48+30 输出 `base/measured_campaign/fixed_budget`。隔离快照 `base/source_substep_batch` 和 `base/source_fixed_budget`。检查这些文件再决定下一步，禁止重复启动。
- on/off smoke 证据已归档 `docs/evidence/classical_20260923/substep_metrics_invariance_smoke.json`；动作偏置图为 `docs/evidence/classical_20260923/action_slew_bias.png`，仅为离线请求重放，不是实际执行速度。
- 本机 PPO agent 继续实现 canonical bridge 与零动作一致性验证；未取得结果前不能宣称当前 48D RL baseline 已完成。
- RL 重建发现当前 panel runner 在归档 PANEL_CONFIG 未含 rod_height_m 时强制使用默认 0.60 m，而所选归档 train fixture 实际为 0.65 m。agent 正在独立 bridge 中显式恢复归档高度并系统核对其他物理参数；保留错配 smoke，不把它计作有效复现。零动作 parity 是 bridge 与恢复配置后的当前 runner 一致，不等于证明历史 teacher 源码逐字节一致。

## 首批闭环结果与本机训练（约 19:00 更新）

四条消融均已完成完整 24 s，原 24 条统一测量正在接续运行。首批证据在 `docs/evidence/classical_20260923/measured_ablation_first4/REPORT.md` 及 `analysis.json`；三条原法的同批物理峰值仍待齐全，不能提前拼新完整表。

- ESN 关闭 x-yield：任务失败，终点误差 213.21 mm，外接触持续到 24 s。
- ESN 固定 alpha=.25 低通：尾部 x-action 标准差从原 .276 降至 .01499，slew 额外均值偏置消失，但策略在新访问的状态上仍持续请求约 -0.0350 m/s 的横向让位；任务失败，终点误差 218.55 mm。
- MLP 同一低通：任务成功，终点误差 6.76 mm；完整 gate 因 .2053 mm 穿透失败。
- VMC 同一低通：从原任务成功变为失败，终点误差 206.65 mm；穿透 .1996 mm 已满足门槛。

因此“仅消除高频 action/slew 偏置就能恢复任务”已被反证。滤波引入的延迟会改变接触逃逸，不能把简单低通当作通用修复；不继续扫描 alpha 或只给 ESN 挑有利滤波。不改变 frozen proposed，把这组保留为因果诊断。

本机 canonical48 PPO 已实际启动：训练 PID **39497**（需结合命令确认），输出 `outputs/canonical48_ppo_pilot_20260923_r1`，日志同名前缀 `.launch.log`。单环境/CPU线程1/affinity2核、GPU分配限制、RSS7GiB/系统余量2.5GiB保护、45 min timeout。计划 640 training steps，然后 train/validation 各 zero 与 frozen PPO 完整回合，不称为充分训练。

零动作 parity 已通过：6.4 s、160 步，actor48/action7、physics_states、contact_samples、原 rollout 数组逐项完全一致；`zero_parity/ZERO_PARITY.json` 保存证据。恢复高度后 scene_differences={}、physical_panels_equal=true，但仍不声称历史 runtime 逐字节等价。实查训练 416 steps，RSS约 2.27 GiB、系统余量约9.47 GiB，CUDA分配约18 MiB。小 MLP 与单环境物理步进导致 GPU 占用低，不为刷利用率开启危险并发。

## 后续验收规则

- 不放宽 0.2 mm 穿透门，不删除失败，不用测试结果调参，不更换有利 checkpoint。
- 全程误差必须同时报告阶段误差和任务/接触通过率；原误差大多来自 Z 抬升，不等同横向接触品质。
- 经典参数搜索先写候选、预算、选择规则和新验证条件，再运行；不同执行家族的差异单独说明。
- PPO pilot 必须明确训练数据/互动预算不同于 imitation ESN；front validation 没有 rod stroke，不能强套 panel rod 接触门。
- 每轮保存源码/协议/模型 hash、命令、原始结果、执行错误、资源/运行状态与下一步。看到稳定运行中的作业先追踪，不重启。
- 最终论文验收仍需更多物理条件、独立训练 seed、冻结后的新 office blind test。不能把开发调参最优值叫未见测试成绩。

### ESN coverage audit (2026-09-25)

Offline causal replay and state-coverage analysis are complete. No MuJoCo was
started in this pass. The adapted readout exactly reproduces the recorded
physical action (RMSE `1.46e-16`, max absolute `9.16e-16`), so the negative
rollout is not a loader/checkpoint mismatch. Loaded-lift slew intervention is
`76.95%` for the adapted readout and `82.71%` for frozen ESN, with no amplitude
clipping. Source review confirms `observation[39:45]` is the encoder-derived
6-D wrench consumed by `SixDVirtualDynamics`; the failure is not explained by
a simple 3-D wrench index error.

The descriptive coverage audit used six frozen training traces, six held-out
traces, and three deterministic student traces. It did not use held-out data
for model selection. Normalized feature RMS / p95 / max was
`1.1616 / 2.2608 / 16.5491` (train), `1.2481 / 2.3876 / 17.7513` (held-out),
and `1.6732 / 3.2289 / 18.4573` (student). Reservoir-state norm RMS / p95 /
max was `4.0185 / 4.9418 / 5.5450`, `4.2028 / 5.2225 / 6.2039`, and
`4.9492 / 6.1052 / 7.3301`. Student traces entered stage 3 at about `2.52 s`
and remain a fixed-scene replay, not independent geometries. These statistics
support closed-loop distribution/history shift as the leading working
hypothesis, not causal proof or deployment evidence.

Artifacts: `outputs/esn_dagger_causal_audit_20260925_r2/` and
`outputs/esn_state_coverage_audit_20260925_r3/`. Coverage JSON SHA256 is
`16be8f58e9cf5f97cf42b206ff27b4b4dd05faef46c2472ccbc209f2256a995f`; causal
JSON SHA256 is
`8e0213064aea52684919ca98c3be86ca290e75e8c1753a63a3bde73444c6d508`.
Do not continue same-scene beta/filter scanning. The next valid ESN step is a
predeclared iterative on-policy collection/relabel pass over development
fixtures, followed by untouched validation; no real-environment claim is
currently justified.
# Historical proposed ESN checkpoint: R10--R13 (2026-09-26)

Baseline work is unchanged. Proposed-method continuation is documented in
`docs/ESN_SAFETY_ROBUSTNESS_REPORT_20260926.md`. The R10 ESN completes all
nine evaluated 9330--9345 tasks, including teacher-infeasible 9332, but strict
penetration is 3/3 on development and 4/6 on the first cross-condition set.
R11--R13 did not achieve a full development safety screen; blind validation
was therefore withheld. At that decision point the method was task-robust in
MuJoCo but not yet cross-condition safety-robust or real-robot ready.  This
status was superseded by the audited R30 result below.

### Final R30 safety closure and once-only blind audit (2026-09-26)

The status above records the earlier R10--R13 decision point.  Subsequent
R14--R30 work is complete.  R30 is now the promoted proposed-method
checkpoint for the audited MuJoCo claim:

- exposed eight-condition screen: task+strict `8/8`;
- exposed nine-condition remainder: task+strict `9/9`;
- all exposed conditions: task+strict `17/17`;
- hash-frozen 9360--9367 blind plan: run exactly once, task+strict `8/8`;
- no failed or unsafe episode was removed, and the unchanged strict gate was
  `all_external_max_penetration <= 0.2 mm`.

The R26--R29 failure chain is causal evidence rather than hidden tuning.
Shorter/stronger expert pulses moved the unsafe peak between conditions;
slowdown did not slow the externally driven rod; and R29's stage-2 +z floor
0.65 nearly removed contact on several conditions but prevented grasp, giving
task `0/8`.  R30 changed timing, not the gate: a learned detector reads only
the proprio48-driven reservoir history, rejects stage-2 hard negatives, and
starts a fixed 20-step +z floor-0.65 pulse after loaded-lift/stage-3 evidence.
Offline stage-3 TPR is `1.0`, stage-2 hard-negative FPR is `0.0`, and archived
independent exposed trajectories trigger three to four control steps after
stage 3.  Deployment does not read stage, clock, fixture identity, geometry,
or contact truth; it uses proprio48 plus policy-local reservoir/counter state.

Uniform physical-substep metrics are:

| Set | Task / strict | Mean trajectory RMSE (mm) | Max peak torque (Nm) | Max peak speed (m/s) | Max penetration (mm) |
|---|---:|---:|---:|---:|---:|
| Exposed 17 | 17/17 / 17/17 | 45.085197 | 41.735517 | 0.253463 | 0.188467 |
| Blind 9360--9367 | 8/8 / 8/8 | 44.840836 | 40.968086 | 0.252826 | 0.183139 |

Audit anchors:

- checkpoint:
  `outputs/esn_r30_phase3_selector_20260926/floor_065_pulse20/hierarchical_margin_vertical_pulsed.npz`,
  SHA256 `3f6ed39af0c103ee6af07fada710cd90a781233041fb02c3f850996f22a3aae1`;
- frozen blind plan: `configs/esn_r16_blind_plan_20260926.json`, SHA256
  `f4960829720474bfa1975a3af876cd3318f7573b471fe84f80b6e94801a659ec`;
- Spark read-only source/model/control manifest: SHA256
  `56c53d1274d4dbc9fed61f3653aa1eea1b499acfea889e9b764ee232f9931afa`;
- combined exposed summary: SHA256
  `52a6cf0db1bd0e466548ce0821871a591a86d151b9dab94d56a4ec57f844699c`;
- blind summary: SHA256
  `c55288e02bf55b2fe575c5a5c8c9d6b47d21bc6763d5cac2c00c393141b670fa`;
- detailed narrative and machine-readable report:
  `docs/ESN_SAFETY_ROBUSTNESS_REPORT_20260926.md` and `.json`.

Spark was checked after completion: no R30/MuJoCo rollout process remained,
and the R30 source/model/control trees contained no writable files.  Do not
rerun or tune on blind fixtures 9360--9367.  The local promoted checkpoint,
frozen blind plan, development summary, and blind summary were also changed
to read-only permissions after their hashes were verified.  The defensible claim is
**cross-condition robust in the audited guarded moving-rod MuJoCo setup**,
not full-office success and not real-robot ready.
The guarded-rod result does not authorize a hardware-readiness conclusion.
The next phase is actual office-v5 task recovery and safety validation;
HIL and hardware trials remain future work after office success and sensing
delay/noise and control-period jitter are validated.

### R30 full office-v5 correction (2026-09-26)

The first canonical48 R30 transfer to the actual historical complex office
scene (articulated person/hand, free ball, independent rod, cup, pillar, desk,
and thick corner) failed.  On the fixed seed-2026091751 variant-0 all-events
21 s run, all 525 policy frames stayed in `approach`: task `0/1`, strict
`0/1`.  Maximum external penetration was safe at `0.177712 mm`, but required
person-hand contact was absent.  The reservoir selector false-triggered its
20-step +z pulse at `0.08--0.84 s`, rather than after loaded lift.  This is
direct evidence of office-domain reservoir-history shift.

Raw result/trace SHA256 are
`706f106f5c205154c8fc37566de10642a13c55ee4d4cd972ccd1d43f7c46bcfa`
and `c40ee0d56aac3eab4ea567692ad3ade324fd92e5f5837e2c11c241402fc0eab1`.
See `docs/ESN_R30_OFFICE_COMPLEX_RESULT_20260926.md`.  The run is retained as
an exposed failure and cannot be hidden or called blind.  The next valid work
is paired diagnosis of the base readout and pulse timing before selecting a
repair, while keeping future layouts untouched.

### Office-v5 causal diagnosis and new ESN (2026-09-27)

See `docs/ESN_OFFICE_RECOVERY_20260927.md` and frozen
`configs/esn_office_development_protocol_20260927.json`. Three development and
three withheld office layouts are declared; withheld layouts remain unused.
Nine short paired diagnostics are complete. R30 and pulse-disabled R30 both
fail approach even without driven events, while zero residual grasps and
reaches carry. Thus the early pulse/ball alone does not explain failure: the
base learned readout has persistent free-space drift in the office posture.
Fixed external-contact target variable shadowing, retained global metrics,
and added scratch-kinematic substep audit and full replay state/model saving.

Four full 55 s teacher/zero diagnostic runs have ended on Spark. R31/R32/R33
are complete: task success is 0/3, 1/3 and 3/3 respectively on the same three
declared development layouts. R33 uses 128 reservoir units in six independent
axis blocks, a bias-free nonlinear readout and causal VMC distillation. Exact
zero-load equilibrium and no cross-axis leakage were checked on the trained
model. All three cases physically place/release/retreat with cup stability.
No task/physics gate was weakened. Seven targeted tests pass.

R33 strict result remains **0/3**: original/strong ball exceed .2 mm at 50 us,
and all cases lack the full declared rod-contact exposure (hard case has no
rod contact). Fine-step probes give original .196223 mm and hard .207370 mm
at 1.5625 us, agreeing with the preceding refinement within .001 mm; these
probes do not retroactively replace full-task results. The strong-ball safety
failure survives refinement and occurs before the first post-impact 25 Hz
actor observation. Do not claim that more readout fitting alone removes it.

Checkpoint SHA256 `ba5575e4dd48c5773396ebf7b59b9911d3f0320b8a908dc88260b6331061835d`.
Campaign root `outputs/esn_office_recovery_20260927/`; frozen runtime
`r33_snapshot/`; training/model `r33_axis_memory/`; original trace
`r33_local_all/`; extra fixtures/probes `r33_screen/`; verified original
office GIF/MP4 `r33_original_replay/`. `all_results.md/.json` preserve all
30 episodes including failures and 0.2 s probes. One failed memory-limited
training attempt is additionally retained in `r32_vmc_memory/FAILED_ATTEMPT.json`.
Spark source/results remain isolated in
`/home/arm1/vmc_mujoco_runtime/esn_office_r33_20260927/`.

Completed: development task 3/3 and original office animation. Outstanding:
first-impact safety/control architecture, adequate stress exposure, common
validated physics resolution, once-only withheld audit and hardware work.
No blind office layouts have been executed. Zero-residual WBC and six-D VMC
also complete the original office task, so ESN-only superiority is unsupported.
Keep the overall safety goal active; do not restart the completed development
jobs or call this real-robot-ready.

Final round check: all R33 actions independently replayed with max absolute
error <=2.20e-15; all three substep metric summaries independently reproduced.
Extra-layout MJB and full substep sidecars have been archived locally. All
seven R33 Spark jobs exited 0 and no office evaluator remains running. No
automation was re-enabled. Continue from this completed round, not by
relaunching R31–R33 or rerunning withheld seeds.

### First-impact causality and stress continuation (2026-09-27, next goal turn)

Previous turn was progress (R33 task3/3, strict0/3), not completion. Confirmed
no old server job, then completed four new 0.2s hard-ball bandwidth probes.
Zero feedback reproduces .207370134mm exactly. Faster causal encoder-load
feedback at 50us or every 1.5625us physical step, with unchanged motor torque
and slew limits, yields .207370154/.207370170mm: no improvement. All input,
rate and parity checks passed. Local J/M estimate gives only about 5.95nm
additional motion during the .4ms contact window, versus 7.37um excess; this
is a local estimate, not a global impossibility theorem. Nine redundant
initial posture candidates were screened without changing EE pose; intrinsic
worst-direction inertia improves only .372%, and the selected pose does not
reduce y inertia. No setup change or new proposed checkpoint was promoted.

Evidence: `docs/ESN_FIRST_IMPACT_BOUNDARY_20260927.md`,
`outputs/esn_office_impact_bandwidth_20260927/`,
`outputs/esn_office_posture_screen_20260927/`.

Six full stress runs are now executing on Spark under
`/home/arm1/vmc_mujoco_runtime/esn_office_resolved_stress_20260927/`, using a
new isolated snapshot and three workers. First .2s resolves physics at
1.5625us, remainder 50us, common to zero and R33. RMSE now records per-sample
dt and uses physical-time weighting for mixed resolution; eight tests plus
an independent .24s boundary/peak/weighted-RMSE check pass. Added rod start7,
start9 and hold6 conditions are extra pressure tests, not replacements for
the original three layouts or their failures. Frozen plan:
`configs/esn_office_resolved_stress_20260927.json`. First three runs have ended;
last three remain in flight. Collect all final results before reporting totals.

An asynchronous scope question is pending: whether to authorize a separate
shared pre-contact sensing safety layer, keeping the ESN proprioceptive.
The original handoff's proprio-only/unpredictable-contact definition prevents
silently adding visual/event information to obtain a pass. No new sensing
branch has been implemented. Existing in-scope stress work continues while
waiting; do not assume elapsed time authorizes the new branch. Overall goal
stays active, not complete or blocked.

Resolved-stress six-run queue has now finished, all exit0. Frozen R33: task4/5,
strict3/5. Original office, rod-start7 and rod-hold6 pass all gates at .196223mm;
rod-start9 fails load transfer and exposure; hard ball completes but remains
.207370mm with no rod contact. Zero residual also passes original office.
Full original-case data is local, independent action replay <=1.61e-15 and
time-weighted substep RMSE verified. New strict-passing original GIF:
`outputs/esn_office_resolved_stress_20260927/original_strict_replay/replay.gif`.

R34 fixed global gain=.5 candidate is now running a six-case, three-worker
queue on Spark at `/home/arm1/vmc_mujoco_runtime/esn_office_r34_stress_20260927/`.
This targets the remaining in-scope load-transfer bias; it does not purport
to fix pre-observation first-impact safety. Checkpoint SHA256
`7c9455afa2d419857424bd7ea3e18b12faeafa56133f54796e9fb69b0f0b635e`;
plan `configs/esn_office_r34_stress_20260927.json`. No blind fixture used and
no new sensing authorized yet. Do not launch duplicate queues.

### R34 final collection and independent audit (2026-09-27)

All six jobs finished exit0; no office worker remains. R34 task6/6, strict3/6.
Original/start7/hold6 strictly pass. Start9 has zero rod exposure; plus has
.225s, below .4s; hard completes with .799s rod exposure but .207370mm
penetration. All failures retained. Full six-case archive (~562MiB) is local.
Independent time-weighted RMSE, peak torque/speed and 8,250 actions/reservoir
states pass; max action replay error9.99e-16. Offline reset comparison shows
history dependence only, not closed-loop memory benefit. Audit tool:
`tools/audit_office_r34_results_20260927.py`; audit artifact:
`outputs/esn_office_r34_stress_20260927/R34_INDEPENDENT_AUDIT.json`.
Strong-ball replay saved and visually checked, clearly labelled tasktrue /
strictfalse: `outputs/esn_office_r34_stress_20260927/hard_task_success_replay/`.
Current report: `docs/ESN_OFFICE_R34_FINAL_20260927.md`; weekly report updated.
No withheld layouts run; no new sensing authorized or implemented. Overall
goal remains active and incomplete. Do not relaunch finished queues or
re-enable automation; the pending scope question is not implicit approval.

### Closed-loop memory ablation underway (2026-09-27)

Previous goal turn made progress, not a no-progress block. New fixed five-job
diagnostic compares R34 retain/reset/zero across original, rodstart7 and hard,
reusing four existing matched references. No sensing branch, blind access,
gain search or retraining. Plan `configs/esn_office_memory_ablation_20260927.json`;
protocol `docs/ESN_OFFICE_MEMORY_ABLATION_20260927.md`. Nine tests pass.
Snapshot tar SHA256 9e7b560ed69ed78148dff73897aa99db089788449c78a9d122b1bd14ca0e49f2.
Spark isolated directory `/home/arm1/vmc_mujoco_runtime/esn_office_memory_ablation_20260927/`;
queue PID891870, three single-thread workers. Verified first three live at
simulation33s. Do not relaunch; collect all failures and final task outcomes.

Memory ablation queue now finished: all five new episodes exit0. With four
reused references, nine outcomes complete. Retain/reset/zero task=3/3,1/3,3/3;
strict=2/3,1/3,1/3. Reset original/hard remain load_transfer; late error
13.437/14.217mm exceeds12mm condition and ready stays0. Zero rodstart7 misses
rod entirely; its strict failure cannot establish ESN superiority under
identical actual contacts. All hard peaks unchanged at.207370mm. Full raw
data locally archived; all9 metrics and6 neural action/state replays verified;
three-way model/fixture/args/core sources/initial state parity pass. See
`docs/ESN_OFFICE_MEMORY_ABLATION_20260927.md` and campaign
`MEMORY_ABLATION_RESULTS.json/.md`. No workers remain; no blind layouts,
no additional sensing, no new candidate trained. This turn made progress
through causal evidence, but full safety objective remains unachieved.

### Completion and repeated-blocker audit (2026-09-27)

Goal tool now returned `blocked`, not complete or paused. Current-state audit
confirms task6/6 but strict3/6, hard peak.207370134mm and two insufficient rod
exposures; withheld evaluation is prohibited until development passes.
All queued work is terminal, no live worker. The same unanswered research
scope decision persisted across impact diagnosis, R34 collection and memory
ablation; independent useful work was completed while awaiting it. Current
next concrete proposal adds shared pre-contact sensing beyond original
proprio-only scope; no approval or implementation exists. Do not interpret
automatic continuation as approval, rerun finished jobs, or claim completion.
Full requirement-by-requirement evidence and resumption conditions:
`docs/ESN_OFFICE_COMPLETION_AUDIT_20260927.md`.

### Explicit user decision: proprioception only (2026-09-27)

User rejected additional sensing: "不可以加感知，就是要纯本体感知". This
supersedes all previous pending-sensing language. No visual/range/precontact
branch is permitted; no such approval is pending. Continue existing scope,
preserve full objective, gates and failed episodes. See
`docs/ESN_PROPRIO_ONLY_DECISION_20260927.md`. New bounded numerical contact
audit tests parity/tighter solver/native CCD without modifying materials,
mass, incoming speed or controller; short probes never count as task success.

All three numerical probes finished exit0 on Spark, full outputs archived
locally. Parity exactly reproduces.207370134380mm; tightened solver gives
.207370134378mm; nativeCCD gives.206770251160mm, all above.2mm. Independent
MJB material/inertia/geometry/actuator checks and initial-state/observation
parity pass; zero actions and diagnostic-only task flags verified. Source
tar SHA7161b7d915eb4621da9c4a7a7cca725f162d7c95ffbce4fb31d153bb2d09334a.
No numerical change promoted, no ESN success credit, no live queue. The
user's pure-proprioception decision is resolved, not pending; do not request
visual/range sensing again. Full safety goal remains unachieved.

### R35 fixed-budget history aggregation (2026-09-27)

User requested continued work within pure proprioception. One bounded
readout-refit candidate uses all14 declared histories (old5 + R34all6 +
resetall3), same128 reservoir/seed, same teacher,3200 updates,output_gain.5.
No stage/truth/event inputs, no blind access; six-case re-evaluation is
explicit development regression. Protocol `docs/ESN_OFFICE_R35_AGGREGATION_20260927.md`.
Spark isolated `/home/arm1/vmc_mujoco_runtime/esn_office_r35_stress_20260927/`;
single-thread training started after confirming no old worker. Frozen source
and input tar SHA1bc7d3016e9a1ccdf2ff3c5f6015176295566908dbac9f50fcae8c3cd592018f.
Check current training/process state before doing anything; do not duplicate.

Initial seed-regenerated training completed but exact W invariant failed
at3.1e-15 cross-CPU eigensolver differences. Preserved failed attempt/model;
fixed trainer to read frozen R34 reservoir arrays directly, refit3200 updates.
Total cost includes both attempts, not hidden. Corrected modelSHA
6b0fffe58be6cb2930b4272e75e8dc0708ace320c29d9e21e2aaa49456c7b3c5;
snapshot_v2SHAc3bae173b68f37d4c354ecb22338973f8f09607fa5ceddb52cfaa1914648287c.
Exact reservoir/gain, zero-load and axis isolation passed. Offline own-trace
errors improve but synthetic validation worsens5.6%, recorded honestly.
Six-case regression running, queuePID910344, initial workers910348–910350
verified atsim40s. No first-impact improvement claimed; collect all outcomes.

R35 six-case queue now ended, all exit0. Task6/6, strict3/6, same gate failures
asR34. Five waypoint RMSE values improve but four final object XY errors
worsen; hard peak remains.207370134mm. R35 NOT promoted over R34. Complete
raw archive synced and remote checksum dry-run clean. Independent six-case
substep metrics and8250 action/state replays pass (max9.44e-16); matched
MJB/fixture/args/common source comparison passes. Nine tests pass. Final
report `docs/ESN_OFFICE_R35_AGGREGATION_20260927.md`, complete campaign JSONs
include R35_STRESS_RESULTS, R35_INDEPENDENT_AUDIT, R34_R35_COMPARISON and
R35_OFFLINE_AUDIT. Preserve both training attempts and snapshots. No live
queue, no test opening, no new sensing. This is progress through a completed
negative candidate test, not full safety completion. Do not relaunch R35.

### Pure-proprio observer causal audit underway (2026-09-27)

Previous turn completed a negative R35 regression, so it was progress.
New two-run read-only diagnostic uses frozen R34 original/hard, no controller
or estimator changes. Constraint/contact/friction truth only enters a sidecar,
never ESN/task. Independent observer reconstruction passed local.08s smoke.
Compare all full rollout arrays exactly before interpreting error attribution.
Plan `configs/esn_office_observer_audit_20260927.json`; protocol
`docs/ESN_OFFICE_OBSERVER_AUDIT_20260927.md`. Spark isolated directory with
same name; two single-thread workers, exec session9021. Source tarSHA
0ee03d81d2f8ee75b1c0c3de9e4b522d50e5d70ac1d094c3f9b52eb2ca85d685.
Do not duplicate or infer completion from this running-state note.

Observer truth audit completed: two full R34 trajectories exactly match every
saved reference array, all recorded source/MJB hashes equal, reconstructed
observer inputs exactly match. Load-transfer joint error normRMS.530/.511Nm
maps to equivalent force error2.004/2.200N; dynamics residual~1e-5Nm, friction
uncertainty dominates. No actor/task received truth. Full results saved in
`outputs/esn_office_observer_audit_20260927/OBSERVER_AUDIT_RESULTS.json/.md`.

Started one fixed calibration scale.005→.001rad/s, default remains.005,
sameR34 model. Four explicit trials original/hard × ESN/zero, both task and
actor use same proprio observer, thresholds/world unchanged. Added old-scale
shadow observer on each same trajectory, output read-only. Twelve tests and
.12s local probe pass. New Spark campaign esn_office_observer_scale_20260927,
three workers, exec session20753. Snapshot_v2SHA
bcfccaf32a5d29a8e83023e672105cea72fc6948444ea53b0ffdd82e9ecb41e8.
This tests friction-estimation bias, not pre-contact information or a promised
first-impact fix. Check existing jobs before any new launch.

Observer-scale four-run queue completed exit0; all raw files archived and
remote/local checksum dry-run clean. Candidate .001 is REJECTED, default .005
unchanged. ESN original/hard both regress from task success to load_transfer
failure; zero both still succeed. Same-trajectory stage5 old-shadow/candidate
joint RMS norms: ESN .449074/.648496 and .436995/.636904Nm; zero
1.230900/1.099598 and1.238413/1.095888Nm. ESN stage5 position gate never
passes (616/586 samples), final error12.0891/12.2249mm; load signal mostly
passes, so do not call this absence of unloading detection. Four55s substep
metrics, ESN action/state replay, zero actions, paired MJB/world/args/source
audits pass. Results OBSERVER_SCALE_RESULTS and OBSERVER_SCALE_AUDIT in
outputs/esn_office_observer_scale_20260927. No simulations remain in this
queue. Next bounded diagnostic checks reservoir fixed-point teacher fidelity,
without adding sensors, changing gates or opening withheld scenarios.

### R36 fixed-point regularized readout (2026-09-27)

Offline check found nonzero steady-load distillation bias, including a few
wrong-sign tiny-load outputs. One predeclared closed-form correction preserves
reservoir, nonlinear readout, gain .5, zero equilibrium and axis isolation;
only signed-axis linear weights change. No observer-scale data used. Static
interpolation RMSE .00173284→.00081816, original synthetic dynamic validation
.01480553→.01486034 (+.37%). Wrong-sign checks4→2, so no passivity guarantee.
Offline criteria pass, but candidate is NOT promoted. Source/data/model/plan
hashes in outputs/esn_office_equilibrium_20260927/FIT_REPORT.json.

Six original development conditions launched with EXACT frozen R34 source
and original .005 observer; three single-thread Spark workers, session85998,
isolated esn_office_r36_stress_20260927. ModelSHA
4b61ada5e76d4741b90bc3f71a1cf40c89b9e804950853c8c8dc6df06c51eda2;
snapshotSHA63b74ca27d4835027e5bdf21a10e96a62774875af64f0a44cb47212840bdd5f5.
Protocol docs/ESN_OFFICE_EQUILIBRIUM_20260927.md and configs/esn_office_r36_stress_20260927.json.
Inspect existing jobs, do not restart. First pre-observation ball peak is
not expected to improve from this force-only readout; full safety still open.

R36 six-run queue COMPLETED exit0, no live worker/queue. All raw outputs
archived, remote/local checksum dry-run empty. Six paired MJB and ALL recorded
source hashes match R34 exactly. Independent55s physical-time metrics and8250
action/state replays pass (max action error1.07e-15). Task6/6 strict3/6,
unchanged failure families. Four waypoint RMSEs fall but two rise; five final
object XY errors worsen. Mean RMSE146.960→146.940mm, mean episode torque
peaks38.598→38.815Nm, speed peaks.133857→.134103m/s. R36 NOT promoted;
R34 and observer default .005 remain reference. Complete report
docs/ESN_OFFICE_EQUILIBRIUM_20260927.md, R36_STRESS_RESULTS,
R34_R36_COMPARISON and R36_INDEPENDENT_AUDIT in campaign directory.

Additional read-only causal audit: four hard-impact R34/zero × observer
.005/.001 runs have EXACT equal stored physical arrays for51200 substeps
through80ms. Ball contact55.0578–55.5094ms precedes first nonzero wrench at80ms;
earlier actor inputs/actions/reservoir strictly0. This rules out fixing this
first event by zero-equilibrium-preserving readout changes under the current
force-only architecture and fixed reset, NOT all proprioceptive controllers.
Evidence outputs/esn_office_observer_scale_20260927/ZERO_INPUT_PREFIX_AUDIT.json.
No sensing permission pending, no withheld access, no hardware success claim,
no global impossibility claim. No repeated scale/gain/readout scan justified
for the first impact; any next experiment must name a new causal mechanism.

### Surface inertia and optimistic motor-authority audit

Previous turn completed observer/R36 negative candidate tests: progress, not
no-progress. New robot-only hand-surface screen adds rotational mobility to
the prior center-point inertia screen. Same9 IK postures,26 fixed hand-frame
support directions, no ball direction/clock selection. Original posture is
already minimum worst surface effective mass6.499621kg; nearest alternative
6.528441kg is worse. No initialization change, all234 values archived in
outputs/esn_office_surface_inertia_20260927.

Three .08s optimistic post-contact authority probes launched in isolated
Spark esn_office_oracle_authority_20260927,3 workers,session52021. These are
explicit PRIVILEGED OFFLINE DIAGNOSTICS, never deployment or ESN success:
parity, local normal-acceleration torque oracle with original slew, and
unphysical instantaneous torque-box oracle. No pre-impact action, unchanged
world/gates, no ESN input change. SnapshotSHA
b6176f1a06891ab9dabb7baeaed9ac5875cea972f86e8c8ce63cb5d035f89761.
Check existing session before polling/relaunch. Protocol/evidence explanation
docs/ESN_OFFICE_SURFACE_AUTHORITY_20260927.md. Not a global control bound.

Three oracle probes completed exit0. Parity all trajectory/metric arrays
match prior solver parity EXACTLY. Max penetration .207370134/.207370163/
.207375110mm for parity/slew/instant; no improvement. Recorded motor torque
matches commands. Correct rate semantics audited: parity obeys original4ms
ZOH rate budget despite jumps at physical substep boundaries; instant oracle
does not. Never count privileged/unphysical probes as ESN results. Full audit
outputs/esn_office_oracle_authority_20260927/ORACLE_AUTHORITY_AUDIT.json.

Single additional READ-ONLY .08s contact-response audit started on Spark,
esn_office_contact_response_20260927,1worker,session93757. Clone states at
three declared penetration crossings and compare unconstrained vs contact-
constrained acceleration sensitivity without touching live physics/control.
SnapshotSHA078a8d6e272f1182bcac85d7edda8134da13dac5878c47750862c7b72ecf6061.
This follows observed torque/hand-motion change without penetration gain;
not a material/gate change. Require exact parity before interpreting clones.

Contact-response job COMPLETED exit0. All rollout, ball-detail and substep
arrays exactly match parity. Independent local reconstruction/forward solves
reproduce three saved state sensitivities. At3.949/103.988/191.378um depth,
free separating acceleration increments62.405/62.412/62.423m/s² become
.014736/.000442293/.000442370m/s² under contact constraints. High impedance
and coupled constraints absorb most motor effect into changed contact force.
This is local mechanism evidence, not a global impossibility theorem or proof
that contact parameters are wrong. No parameters/gates changed. All four new
short jobs ended; no new full-task successes or ESN checkpoint promotion.
Independent reports in outputs/esn_office_contact_response_20260927 and
outputs/esn_office_oracle_authority_20260927. Surface screen retained original
posture. Full goal still active/incomplete; this turn is progress.

User was asked via async input whether to authorize INDEPENDENT SHARED CONTACT
CALIBRATION (with physical evidence, not selecting parameters by ESN passage)
or preserve current physics and continue software-only research. This is a
new benchmark-boundary choice, NOT the resolved sensing question. No response
yet and no material/solver modification authorized or implemented. Proposal
docs/ESN_CONTACT_CALIBRATION_PROPOSAL_20260927.md. Preserve all original
failures, .2mm gate, proprioception-only constraint and unopened held-out set.

Final remote/local checksum dry-runs clean for both new diagnostic result
directories; authoritative process listing confirms no office simulation
workers remain. Source compilation and git whitespace checks passed. No
commits, automation changes or external publication performed.

### Reporting artifact completed while calibration decision remains pending

Previous goal turn was progress (surface/oracle/clone diagnostics), not a
verified wait. No new user authorization arrived with automatic continuation.
This turn completed an explicitly requested reporting deliverable from saved
R34 hard-case data: outputs/esn_office_impact_explanation_20260927/final/
first_impact.gif and .mp4, bilingual technical quantities/Chinese labels,
full-scene context, collision closeup, penetration threshold and actor timing.
No dynamics integration or world/control changes. The geometry reconstruction
peak agrees to2.95e-11mm; sparse-state gaps are not joined into invented dense
curves. Live graph timestamps use stored configurations (one fine-step cache
offset versus original contact stats is explicitly disclosed).

Local render constrained to3GiB memory/512MiB swap, single CPU thread, ended.
Decoded MP4=164frames/20fps/8.2s; GIF124 coalesced frames retains8.2s. Peak and
end-frame images inspected; media checksums and zero action before80ms checked.
Current full-goal evidence table and media links:
docs/ESN_OFFICE_CURRENT_EVIDENCE_20260927.md. Read-only rollout/execution search
found no three withheld-seed result records. Goal active/incomplete, R34
retained6/6 task3/6 strict; calibration/material changes still unapproved.

The same new calibration-boundary question has now remained unanswered across
two consecutive goal turns (oracle/clone turn, then this reporting turn).
Independent authorized reporting work was completed here; do not relaunch
finished diagnostics or repeat the visual to manufacture progress. Do not
reuse the historical rejected-sensing blocker or treat continuation as an
answer to the new physical-benchmark choice.

### Third consecutive boundary revalidation: goal blocked, NOT complete

Fresh reads confirm R34 still task6/6 strict3/6;14 most recent simulation
execution records all terminal exit0, no Spark or local relevant workers,
reporting asset hashes unchanged. Previous turn was reporting progress;
this turn is status/blocker revalidation, not new experimental progress or
a verified wait. New shared-contact-calibration decision remains unanswered
for the third consecutive goal turn; do not conflate with resolved sensing.
No specific evidence-backed in-scope software next action is presently
available; no global impossibility claim is made. Independent calibration
would change frozen physics and requires a decision plus physical evidence.
Audit docs/ESN_OFFICE_BLOCKED_AUDIT_20260927_R2.md completed; update_goal
returned status=blocked. The objective was NOT completed or narrowed.
Keep all artifacts/failed episodes/.2mm/proprioception/withheld boundaries.
No repeated experiments, automated task re-enabling or publication performed.
