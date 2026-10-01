## 2026-10-01 — 实现有界指标奖励修复并注册独立同step对照

- 基于main ba84ed8/baseline8e541d5，新增--error-transform bounded：每物理子步e²/(.12²+e²)训练积分及一致失败补偿界；旧quadratic默认保留。峰矩/时间/平滑/任务±20不改，原始三指标不裁剪。
- 21项奖励回归通过（含可加性、原始误差、极端提前失败/所有截断位置、terminal与非法输入）；新增bounded_reward_repair.py与report_reward_repair.py及docs/BOUNDED_REWARD_REPAIR_20261001.md。物理无扰动测试由监督器在真实训练前执行，尚不冒称已通过。
- 用户要求优先修复后，核cmd向旧entropy四worker发SIGUSR1，均rc0并保存checkpoint，实际约48.5–50k，共同40k进入原48条评测；不伪称完成原60k。supervisor1797525保持运行，不恢复其他暂停训练。
- 独立reward_scale_repair_03规划2seed新metric从零30k，与旧low_entropy同seed同step任务/指标共36条正式步长开发条件对照；LR计划100k，entropy-2，其余不变。新监督器等旧评测释放算力，先6.4s物理无扰动，再训练；13:12UTC安全停、13:41UTC真实交付。尚无新学习效果。
- 新冻结源预定 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/frozen_reward_repair_03，结果reward_scale_repair_03；源hash和实际PID由启动协议记录，不热改既有frozen_main_01。报告必须显式36矩阵与raw复算，保留失败，不以阶段冒充抓持。

## 2026-10-01 — 定位奖励尺度缺陷，明确当前RL不满足baseline交付要求

- fetch读取main=ba84ed8、baseline=140f71a。用户ESN视频取0/4/10/16/22s画面核看，可见抬升/搬运/释放撤离，task=True；未混作本轮固定checkpoint的同条件结果。
- 新audit_reward_scale.py扫描六路100k控制日志；排除warmup/跨界回合，metric30次提前失败补偿-178至-1810，normalizer分母364–366，office约5。原因是3m误差上界用于整个剩余时间；防逃避数学界不等于适合学习的尺度。
- 末5k动作分量RMS .38–.64，过滤后平移残差RMS .118–.269m/s，显著大于warmup；metric学习后226个结束回合均approach/align。未将随机训练动作当确定性测试速度，也未把相关性写成唯一因果。
- 新docs/RL_REWARD_SCALE_DIAGNOSIS_20261001.md及主报告明确不满足稳定抓取baseline要求、修复准入条件和未完成项。JSON在 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/REWARD_SCALE_AUDIT.json；原数据与冻结源不改。
- entropy_diagnostic_02 PID1797525–1797529正常，仍只检验熵，未修复reward；不重复启动或热改。剩余预算优先奖励尺度与确定性抓取验证，新训练须独立版本；尚无修复效果结论。

## 2026-10-01 — 低熵诊断运行中，补充48回合独立审计入口

- 读取main=ba84ed8、baseline=92f2f3a；entropy_diagnostic_02 supervisor1797525及四worker1797526–1797529正常，约19k步；无报错，无学习后完整任务成功。冻结训练源码与协议未改。
- 新report_entropy_diagnostic.py按8策略实例×6条件显式48回合检查，独立于主54矩阵；复用子步复算但不误用all54_present，核对checkpoint共同step/seed/path/hash、manifest、实际MJB、normalizer诊断和raw记录。分两个训练seed统计均值/SD，保留提前终止、物理无效和逐类事件分母。
- 无评测时的partial smoke通过：0/48、八组pending、没有伪造零指标或完成状态；尚未进行最终48条审计。源码/报告路径分别为 /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/report_entropy_diagnostic.py 和 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/entropy_diagnostic_02/report/。训练→评测仍由已有supervisor自动接续，不重复启动。

## 2026-10-01 — 100k主矩阵54条完成并发布；注册独立低熵诊断

- 核对远端main=ba84ed8、baseline=107b21e；不合并同期main学生新权重。六路100k/190002更新和九组54条评测均rc0；52条55s，metric seed61002 case2/5仅0.44s提前2mm穿透终止。两RL组task/placement0；office物理18/18，metric14/18，ESN/混合/zero各6/6。
- 全54条实际子步复算通过，最大RMSE/峰矩/峰速差1.122e-11m/1.891e-6Nm/1.107e-8m/s；六条件跨方法MJB一致，记录的normalizer诊断冻结，审计无错。不能做混合时长统一排名。
- 新中文主报告 docs/SIMBAV2_BEHAVIOR_BASELINE_RESULTS_20261001.md 与publish_delivery.py；网页 http://192.168.31.70:8765/simbav2_behavior_20261001.html。三图PNG/PDF和五方法同case0状态重放媒体在campaign_01/report与media，web_demo/assets/simbav2_behavior_20261001/发布副本；每GIF276帧、三处帧不同、manifest hash核验，HTTP200及13媒体路径检查通过；UI打开队列未冒称已目视核验。
- 冻结全覆盖行为联合验收均0，但ESN人手局部6/6、棍2/6；zero人手也6/6。报告将任务/局部行为/曝光/unknown分开，不以未曝光概括柔顺失败。任务RL正式停approach，ESN到carry，混合多到load_transfer；不能称充分收敛或ESN全面优势。
- 剩余预算预注册独立entropy_diagnostic_02：仅entropy coefficient-.5→-2；两reward×2配对seed61001/2目标60k，LR总计划100k，其余不变，从头训练。现有主60k作为相同步数对照；共同最大周期step、八组×六已见参数条件评测。12:45UTC训练cutoff，13:41UTC交付截止；这是看过主结果后的诊断，不是独立确认或主结果替换。源码entropy_diagnostic.py，协议/状态/PID在 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/entropy_diagnostic_02/（启动后生成）。
- 主报告路径 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/FINAL_REPORT.md；全54审计RAW_METRICS_AUDIT.json。新脚本编译、diff检查通过；旧四路仍T暂停。新诊断效果尚未知，不暂停heartbeat直至诊断或截止真实交付。

## 2026-10-01 — 六路100k训练结束，36条RL正式步长评测完成并独立复算

- 本次fetch读取main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d、baseline=4dad929；main已新增teacher学生/平滑/增益/seed开发实验，本批保持预注册ESN checkpoint与冻结源e71a512，不混用其不同模型结果。
- campaign_01六路训练均正常结束、各100000 transitions/190002更新；共同checkpoint_step_0100000，TRAINING_STATUS.json和COMMON_BUDGET.json留存。六个RL评测进程均rc0、36条输出已生成；ESN/hybrid/zero仍运行，尚非完整比较。
- 新增独立只读审计源码 code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/audit_raw_metrics.py，按物理dt加权重算RMSE、实际qfrc_actuator整体及逐关节峰矩、末端线速度峰值；检查时间连续性、样本数、完整时长并绑定raw/NPZ SHA。
- 不等dt/负力矩/线速度分量/提前时长/错误时间序列断言通过；已完成36条全部复算通过（不是36条任务或物理全通过）。审计仅读取完成的summary，跳过尚在写入的三组，需最终54条结束后重跑。
- 代码与全部产物仍在Spark。审计 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/report/RAW_METRICS_AUDIT.json；原始评测 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/evaluation/。未改训练、冻结源、环境或行为阈值；最终报告尚待完整矩阵与敏感性验收。

## 2026-10-01 — 主批次已实际启动，冻结e71a512

- pilot02 4×10k全部正常完成；修正后的两个warmup放置回合实际获得+20，但postwarmup仍无grasp。两个初始温度在预注册训练覆盖分数上均为0，按平局规则选.01，不能称已解决学习或已充分调优。
- 最新source绑定的telemetry_invariance_02通过，time/qpos/qvel/ctrl/hand/stage/object/observation/action逐元素最大差均0，物理MJB与三指标一致。
- bootstrap PID1736362、主supervisor启动PID1737384；首批1737387–1737390分别为两reward×seed61001/61002，seed61003两路排队（操作前核对cmd，PID可能过期）。已见每路600真实transitions，约12.1–12.3steps/s，尚在5k warmup。
- 冻结源 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/frozen_main_01/code/mujoco_6d_vmc_benchmark/，source commit e71a512e6fe01eb4e0456c3dfb7d6c6b88afcb54。主协议 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/campaign_01/PROTOCOL.json SHA256=733675507e1cf4aabaeaa17d3562af2c759204a245c2554cc46d5046f08b8773。
- 真实状态读取同研究根BOOTSTRAP_STATE.json与campaign_01/STATE.json，各run的progress.json。自动共享评测、敏感性报告已接续；本条是启动验收，不是最终性能结论。20分钟heartbeat已更新精确路径和预算。只改本日志，不改正在运行的冻结源码。

## 2026-10-01 — 八小时基线接续：修正终末奖励混淆并实现事件时序验收

- 开工fetch并读取main=3336864、baseline=c918548；main十小时teacher-bank已收尾且无新ESN。本轮不合并main，旧四路训练保持SIGSTOP。用户授权窗口约05:41–13:41 UTC（北京时间13:41–21:41），不是收敛保证。
- 撤销上轮未提交的stage+lift成功草案。旧三个ESN摘要缺连续NPZ，行为unknown；含杯combined_v4_development的carry早于碰柱，cup要求不得删除。修正源码、定义与小证据；历史原始rollout和旧奖励实验不覆盖。正确审计路径 /home/arm1/vmc_mujoco_runtime/SII_compliance_eval_2e37ddc/outputs/behavior_success_audit_20261001/。
- 新behavior_telemetry_20261001.py每物理子步累积、4ms保存，只离线使用接触真值；behavior_evaluate.py区分冲击停稳恢复、碰撞后原目标重入并继续运动、承载接触中切向净滑移及任务净进展。保留placement/physical/exposure/unknown；局部推进不等于完整清障。20项时序/振荡/参考跳变/竞争碰撞/掉落反例通过。
- exploration_pilot_01实际4×10k：std=.02 warmup访问抓取及放置，开始学习后新回合退回approach。独立审计发现真实放置且物理有效仍因contact_coverage不足获-20。新增task_physical目标按placement_complete AND task_success AND physical_valid，不强迫碰遍障碍；旧legacy_strict仍可用。7项目标断言及4项旧证据断言通过；真official agent精确episode-boundary resume回归通过。
- exploration_pilot_02已启动4路，两reward×initial temperature(.01/.0001)，gamma=.9995、entropy-.5、std=.02，terminal均task_physical。.01分支单独检验终末修复，.0001分支检验过强熵项；只用完全在warmup后的训练回合选择共同配置。主实验计划两reward×3seed×100k，共同checkpoint，新冻结6参数条件55秒/dt5e-5重评RL、ESN纯学生、75%VMC+25%ESN及零动作控制。计划不冒称已完成。
- 10秒logger开关对照的物理状态/动作/模型/三指标均完全相同；主批次前bootstrap再检查最新source的invariance_02。有限时长与earlyabort分开；report_campaign.py检查原始dt/MJB/normalizer/seed，均值SD以训练seed为单位，支持空间阈值敏感性和partial报告。
- 所有新代码 /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/；全数据 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/；pilot_01/02与冻结源分开保留。BOOTSTRAP_STATE.json接续pilot→最新日志无扰动检查→campaign_01→共享评测→报告。正式报告预定campaign_01/report/REPORT.md；尚未生成的文件不是结果。
- 文档 docs/BASELINE_EIGHT_HOUR_PLAN_20261001.md、docs/BEHAVIOR_SUCCESS_DEFINITION_20260930.md（已更正）、docs/TRAINING_OBJECTIVE_AUDIT_20261001.md。源码仅baseline提交；权重、媒体、raw在Spark。heartbeat已恢复，每20分钟核验实际运行，预算到期交付实际证据后暂停。

## 2026-09-30 — 奖励主实验与40k补充诊断全部收尾，保留失败并交付审计报告

- 收尾前通过Git transport relay fetch并读取远端main 2581451cc9c471b19c67286457bea8d3b8a4b2b7及baseline e47da59日志；main的teacher-bank任务独立继续，未合并或操作其作业。Spark HTTPS无凭据，GitHub发布沿用Mac /tmp/SII_compliance_baseline仅作Git传输中继；代码、训练与大产物均在Spark。
- 主实验保持冻结：8×100k transitions、40候选验证、90最终评测。验证选模两主组各18/18完整55s且物理有效，task/placement/strict均0。metric相对office_task的RMSE降低59.24%、平均回合峰矩降低10.06%，但峰速增加60.58%，不称全面提升。fixed100k的7条提前物理终止单列，不能作为完整55s排名。
- 独立补充 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/progress_dense_diagnostic_04/ 已完成4×40k from-scratch与24最终回合，全部进程rc0、共同step40000、实际全55s/dt5e-5；两奖励各2seed×6case。office_task RMSE19.1963±8.7552cm/峰矩39.5328±0.5060Nm/峰速0.1537±0.0571m/s，物理11/12；metric68.9315±9.3659cm/51.1195±1.5965Nm/0.3341±0.1010m/s，物理12/12；两组task/placement/strict及所需接触覆盖均0/12。保留所有失败计算均值。
- 新连续势函数增加了数值上有效的进度信号，但117已结束训练回合仍无grasp，未解决探索。它是查看主开发结果后的40k诊断，学习率衰减预算也与100k主实验不同，不能当单因素严格消融/独立重复验证。结果不支持“充分收敛”或“已排除人为弱baseline”，更不能宣称SimbaV2本质弱于ESN。
- 独立审计补充全部24回合原始子步：RMSE/实际力矩/峰速复算最大差1.86e-11m/1.87e-6Nm/1.47e-8m/s；实际模型、manifest、checkpoint metadata hash与时长核对通过，记录的normalizer diagnostics不变。审计范围与边界见 diagnostic/report/DIAGNOSTIC_AUDIT.json及.md，源码/模型/raw仍在上述服务器目录。
- 更新完整报告 docs/SIMBAV2_REWARD_STUDY_20260930.md、docs/evidence/simba_reward_20260930/小证据和服务器网页 http://192.168.31.70:8765/simbav2_reward_20260930.html；publish_report.py支持补充结果独立表。plot_results.py将648条训练记录命名修正为ended_episodes（含提前结束），不改数值或冻结源。
- 主报告 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/report/FINAL_REPORT.md；网页资产 /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/assets/simbav2_reward_20260930/；全部实验接续状态见study根ACTIVE_EXPERIMENT.json。主与补充checkpoint均保留，旧四路1150890–1150893复查仍T暂停。
- 本轮计算与评测已结束，报告发布核验后暂停simbav2 heartbeat；不恢复旧作业竞争算力、不新增超出本轮时间预算的训练。尚未达成可宣称充分训练的强baseline，也没有同协议ESN新排名。

## 2026-09-30 — 100k奖励主实验完成、发现训练覆盖瓶颈并启动独立修正诊断

- 开工读取main e1d815c390d1221ee0bf80293e2b8179d2e1d3f8 与baseline日志；main的teacher-bank任务独立进行，未合并或修改其作业。
- 主实验 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/ 完成8×100k transitions、每条190002更新/40000000物理子步；40候选验证、90最终回合和全部进程均正常收尾。冻结frozen_v3/source32d2ea5不变。
- 主selected测试每组3seed×6条件、全55s/dt5e-5、物理有效全通过，但task/placement/strict皆0。office_task RMSE10.4868±4.8930cm/峰矩41.9397±12.3139Nm/峰速.0936±.0363m/s；metric4.2742±2.4923cm/37.7209±1.2178Nm/.1503±.0214m/s。不能说三指标全面更好或已充分收敛。
- fixed100k有7提前global_penetration>2mm终止（office6、metric1），只作混合长度失败诊断；仓库report.py补实际时长、55s完整率与abort，3项报告测试通过。独立审计86回合原始时长、21回合raw三指标复算通过（含7abort）；plot_results.py逐90回合核对实际MJB与模型/manifest/hash。小证据和已视觉核验图见docs/evidence/simba_reward_20260930/。
- 648个已结束训练episode（含提前物理终止）无一进入grasp：起点与初始waypoint重合，旧potential退化为ready/.2，随机残差打断停稳后Phi=0占主组约72.6–99.95%。nominal_zero同环境可完成1/6任务（strict0），不能归咎环境不可达。当前结果不能排除训练设计人为弱化baseline，报告明确承认这一限制。
- 剩余预算启动独立progress_dense_diagnostic_04：两reward×2seed各40k从零训练，shared连续pose/speed potential、UTD2；不改actor/任务gate/物理/filter。新快照 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/frozen_v4_progressdiag/，协议/patch/hash在其根；supervisor /home/arm1/vmc_mujoco_runtime/reward_study_20260930/PROGRESS_DIAGNOSTIC_PID_04.json；结果 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/progress_dense_diagnostic_04/。6项势函数测试+真实4step smoke通过。该补充在主实验诊断后注册，非独立确认，不混入100k主结果；正在运行，尚无效果结论。
- 仓库实现位于code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930/；完整报告docs/SIMBAV2_REWARD_STUDY_20260930.md；服务器主报告和曲线 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/report/。公开展示入口 http://192.168.31.70:8765/simbav2_reward_20260930.html，媒体仍留Spark。
- heartbeat已更新接续补充诊断，约18:30前交付实际完成结果。旧四路训练保持SIGSTOP，不重启；现有主实验负结果、旧pilot均保留。

## 2026-09-30 — 主训练实际启动与自动验收安排

- 有效主实验为 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/；
  source commit 32d2ea5，source快照 frozen_v3，不热更新。
- supervisor PID1385951，首批worker1385964/1385965/1385966/1385967（仅为启动时记录，
  操作前必须再次核对PID命令）。首批实际进入随机warmup，约26–27 policy steps/s/worker；
  GPU更新与完整checkpoint roundtrip已单独验证，学习效果尚待主训练与评测。
- 主实验2奖励×3seed共6条；2条no-smooth消融；100k transitions目标/条、UTD2，
  8000s/run墙钟上限。若预算先到，选共同实际完成checkpoint，不伪称满100k或收敛。
- 每10k步存checkpoint，另外存跨间隔后首个episode-boundary checkpoint以支持精确恢复。
- 自动顺序：训练 -> validation候选选择 -> 55s/dt5e-5 test ->
  主组六条共同训练步数fixed_final评测；报告和曲线数据由report.py汇总。
- 已建立本会话20分钟heartbeat（ID simbav2），检查真实进程/日志/失败，正常进展安静；
  目标2026-09-30 18:30前提交真实结果与限制。新增报告仍保存Spark并push baseline。
- 接续入口 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/ACTIVE_EXPERIMENT.json。
  旧四路暂停、pilot01/02保留；不得误把这些旧进度当作本轮主实验进度。

## 2026-09-30 — 训练侧随机动作审计后冻结主实验

- campaign_02 的配对随机warmup物理轨迹、reward子步积分核对通过，但 smooth=.005
  在55s累计约32.94，超过误差1.47/峰矩3.10，不符合弱辅助约束。
  未读测试策略结果；将主实验smooth固定为.0002（无平滑消融为0），从头配对训练。
  pilot保留至 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_02/。
- 主实验 campaign_03：Office task vs metric 各3seed，目标100000 transitions/seed、UTD2，
  2seed无平滑消融，最大4并行；单run墙钟上限8000s，报告共同实际完成checkpoint预算。
- 冻结源码 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/frozen_v3/，
  输出 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/。
  validation-only选checkpoint；另外所有主组在共同训练步数重测，避免各自最优选择掩盖预算。
- 训练和验证dt=1e-4，最终全55s评测dt=5e-5；所有结果必须注明stage-waypoint参考。
- report.py按训练seed作统计单元，报告三指标及strict/task/physical/placement；
  不跨reward比较总回报，不把零成功归因算法本质，不声称固定预算已证明收敛。

## 2026-09-30 — 修复 campaign 子进程解释器路径

- 首次 campaign_01 在导入 numpy 前退出：对虚拟环境 Python 使用 resolve() 将软链接解析成
  /usr/bin/python3.12，丢失 venv。已改为保留 venv 绝对路径，算法与环境未运行，无学习结果。
- 失败日志完整保留在 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_01/。
- 重启使用独立 frozen_v2 快照与 campaign_02 输出，不覆盖失败记录。

## 2026-09-30 — GPU 官方算法验证完成，冻结配对训练方案

- 新隔离环境 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu：
  JAX 0.7.2/CUDA13, MuJoCo3.11；官方update约122.26次/秒，CPU大核7.37次/秒。
  GPU normalizer/optimizer checkpoint save-load动作差为0；仅补jax.tree_map API别名。
- 冻结两主奖励组各3种子41001/41002/41003，目标各60000 transitions、UTD2；
  另配对2种子metric无平滑项消融；最大4仿真并发。
- 新main几何检查：训练原计划variants3/4及val5/6初始柱座与物块穿模，全部排除；
  合法训练variants -4/-3/-2/-1。验证layouts0/1与6条最终评测manifest提前固定。
  测试中旧三布局属于已看过开发条件，另三条仅新物理参数draw；不称盲测新办公室泛化。
- 物理子步reward/trace、normalizers、replay与RNG以及episode-boundary恢复已验证。
  4步连续训练与2+2恢复的111个网络/优化器叶子完全一致。
- 默认validator与新增hooks零动作6.4秒重放，模型hash和所有轨迹/指标完全一致。
- 运行源将冻结到服务器 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/frozen/，
  训练输出 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_01/；
  此日志是执行计划，具体已启动/完成状态以CAMPAIGN_STATE.json与各progress.json为准。
- 评价只使用raw物理指标和严格任务门槛。运行归一化/discount后不能把reward恒等式直接当作目标指标等价性。
  当前尚无长训练效果或收敛结论。

# Baseline update log

## 2026-09-30 — 官方 SimbaV2 奖励对照：接口修复及开跑前审计

- 开工已读取 main 38caf3152282df4963435bb65c11c93a1e4fffa5 与 baseline 5934200 日志，
  整合当前 main 源码到 baseline；不修改 main，保留双方日志。
- 修复 Spark checkout 的 Git 历史：初始镜像根提交 d386341 保留在
  snapshot_initial_20260930，当前分支使用 GitHub 原始提交历史。
- 原论文与官方 commit 86899c277cdc697b2b02d827243de1ea93f20a1d 核查：
  没有通用 Office reward；官方采用环境 reward + 动态奖励/观测归一化。
  两主组为 Office task（成功/失败、势函数进度、时间成本）与 metric（在相同 task 上增加
  全子步平方误差积分、实际归一化力矩峰值平方增量、弱 requested action 平滑）。
  稀疏 task_only 仅为可选诊断，不能冒充论文原生 Office 奖励。
- 新源码：code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930/。
  validator 新增可选 policy override/训练侧 metrics hooks；默认命令行行为与既有物理、任务 gate 保持兼容。
- 服务器开发与运行目录：/home/arm1/vmc_mujoco_runtime/reward_study_20260930/；
  Git 源码：/home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/。
  论文 PDF 与提取文本：上述运行目录 paper_sources/。
- 旧四路CPU训练经用户明确授权 SIGSTOP 暂停（未终止，内存保留），PID与checkpoint证据及恢复方法：
  /home/arm1/vmc_mujoco_runtime/reward_study_20260930/PAUSED_OLD_RUNS.json。
- 已验证 reward 15项单测；真实6.4s/64000子步误差积分与共同 evaluator RMSE复算相对差
  2.58e-10；峰值增量累计与最终峰值平方一致。
  证据：reward_interval_smoke_64s/VALIDATION.json。
  官方agent更新、网络/优化器/normalizer/RNG保存恢复与raw replay不被污染检查：
  official_agent_validation.json。train_smoke_01 为160步随机期管线检查，不是学习效果。
- 旧比较发现fixture偏移（RL内部再次+101*variant）、RL专用额外残差包络、外载荷误当执行力矩：
  新接口统一 canonical slowdown action7，移除旧RL额外包络，使用完整子步actual qfrc_actuator。
  不能将旧矩阵列作本次论文排名。
- 未完成：GPU隔离环境吞吐验证、配对多seed长训练、验证集checkpoint选择及最终共同评测。
  当前没有新学习效果结论；开发 dt=1e-4 与正式 dt=5e-5 明确区分。

# 更新日志

本文件记录每次对话交付的文件修改、验证和结果边界；最新记录在前。对应提交号由 Git 历史
查询：`git log --oneline -- UPDATE_LOG.md`。持续提交约定见 [AGENTS.md](AGENTS.md)。

## 2026-09-30 — 协作 skill：双分支开工检查、本地计算与服务器归档

- 新增 `skills/sii-research-sync/SKILL.md` 与 `agents/openai.yaml`，安装至
  `/home/airpig/.codex/skills/sii-research-sync/`，允许自动选择。开工先 fetch/读取远端
  main、baseline 的 `UPDATE_LOG.md`；收工重新读取 `AGENTS.md`，记录并发布本轮进展。
  同步更新根目录 AGENTS 与 README，让未自动加载 skill 的后续 agent 也有入口。
- 本轮远端检查（2026-09-30，Asia/Shanghai）：main=`f098678ad1532f1b87c7e2ac803faa301c4c65ca`；截至本轮查询，
  远端没有 baseline 分支，因此无 baseline 更新日志可读。没有擅自创建分支或合并代码。
- 新默认偏好：尽量本地计算，服务器共享持久文件。共享目录为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`，源码按 commit 隔离，
  实验按 branch/run-id 隔离；先同步并校验，再把服务器绝对路径写入更新文档。
  本地缓存和实际执行来源保留，不改历史 execution.json，不覆盖别的 agent 或 runtime。
- 本轮归档的是已发布研究源码，服务器代码位置：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f098678ad1532f1b87c7e2ac803faa301c4c65ca/code/mujoco_6d_vmc_benchmark/`。
  此路径对应本轮开始时的研究代码；本轮 skill/文档更改以 GitHub 新提交为准。
  未全量迁移历史 outputs、原始大轨迹或 checkpoint，不声称它们已在新共享目录。
- 验证：仓库版与安装版 skill 均通过 skill-creator 的 quick_validate，目录内容一致；
  使用现有 `.venv-canonical-rl` 中的 PyYAML 完成校验，未安装新依赖。文档差异检查通过。
  本轮没有修改算法、环境或启动仿真。
- 已完成：skill 编写安装、双分支状态检查、共享目录创建与研究源码归档。2026-09-30
  03:10:53 UTC 逐文件校验服务器快照：2,592 个文件 SHA256 全部一致，无缺失或额外文件。
  本轮没有运行中的新实验；历史大文件仍在原位置，后续按实际任务逐批归档。

## 2026-09-30 — 积累成果同步与每轮自动提交约定

### 文件更新

- 新增根目录 `AGENTS.md`，落实用户“每次对话结束前 commit、push main、记录更新”的授权。
  新增本日志，README 增加当前状态与入口。此次同步的起点为 `2e37ddc`。
- 纳入 9 月 23 日至今未提交的研究代码、配置、测试、报告与小型证据：统一物理子步指标、
  经典控制器预算实验、canonical48D/action7 及参数动作 RL 对照、ESN 记忆消融、
  VMC＋ESN 联合优化、延迟球撞、综合环境的版本化开发、纯 ESN 与 MLP 比较和动作重放审计。
  各历史实验的冻结配置、失败原因与结论以各自报告为准，不合并为一个“全部成功”的结论。
- 纳入独立 teacher 修正实现 `scripts/vmc_teacher_stable_readout_20260930.py`、
  `tools/teacher_repair_campaign_20260930.py`、`tools/teacher_repair_followup_20260930.py`、
  `tools/audit_teacher_repair_20260930.py`，以及 `docs/TEACHER_REPAIR_20260930.md` 和进度、周报。
  上述路径均相对 `code/mujoco_6d_vmc_benchmark/`。
- 新增 `tools/export_publication_evidence_20260930.py`，导出 teacher 的小型审计 JSON、运行配置、
  源码快照及哈希索引到 `docs/evidence/publication_20260930/`。原始大文件不进入普通 Git：
  `results/` 下 NPZ/MJB、证据目录编译模型，以及原本已忽略的 outputs、视频等仍在原处。
  本次清单覆盖 results 大文件、证据 MJB 和三轮 teacher 输出，不覆盖所有历史 outputs 或服务器。
  小型 docs/evidence NPZ 仍纳入版本管理。没有删除原始数据；需要完整重放时还须取得清单中的本地产物。

### 已有实验结果（与本次发布检查分开）

- teacher 两轮完成 12 条有效 55 s、dt=1e-4 开发回合；动作、内部状态及过滤链独立重放误差为 0，
  每条 550,000 个物理子步复算指标。此前误用 MuJoCo 3.14 的四条诊断保留，不混入有效结果；
  有效实验固定 MuJoCo 3.11，并核对综合模型 SHA256。
- 当前候选 `velocity025_stiff2`：corner-placement 的 task/strict 均通过；综合单柱 v4
  task=true、strict=false（缺少要求的柱接触）。综合 waypoint RMSE 37.406 mm，峰值实际力矩
  48.127 Nm，峰值末端速度 0.070574 m/s，外部穿透 0.144922 mm。
  相对同模型原版，放置阶段动作差分 RMS 0.306187→0.042031，降低约 86.3%。
- 尚未完成：特化场景全协议与跨条件验证、综合 strict、正式 dt=5e-5，以及稳定 teacher 数据上的
  新纯 ESN 蒸馏。此次发布没有新训练，没有改冻结环境或 gate。
- README 中 9/29 的 delayed-ball 正式通过结果和早期 cup/pillar 综合失败属于不同版本；
  不可与当前单柱 teacher 开发回合互相替代，也不能据此声称 ESN 已全面优于 baseline。

### 发布验证

发布内容扫描：814 个 Python 文件（包含归档源码副本）语法通过，1,216 个 JSON 可解析；
已检查的私钥、GitHub token、AWS key 和含密码 URL 模式无命中。相关既有测试
`test_esn_load_gated_20260929`、`test_esn_impact_response_20260929`、
`test_office_canonical_audit_20260927`、`test_physics_substep_metrics_20260923`
共 9 项通过。发布集合约 60 MB，最大单文件约 7.6 MB，无超大单文件。
产物索引含 1,642 项、17,382,062,868 字节（含保留在本地的原始数据和已复制的小型证据）。
本次不重复运行已经完成的长仿真实验。
发布整理同时移除了八份历史 Markdown 的行尾空白或多余末尾空行，不修改实验内容。
`git diff --cached --check` 通过；推送前 fetch 确认远端 main 与此次同步起点一致。


## Baseline branch workflow history

# Update Log

This file tracks code and experiment updates on the `baseline` branch. New entries go at the top. Large experiment artifacts remain on DGX Spark; each entry records their absolute server paths so another agent can inspect them without downloading them to a workstation.

## 2026-09-30 — Initialize baseline workflow

- Created the `baseline` branch from GitHub `main` at commit `2e37ddc95d94a4a01d531ae1bf2625a454826d2a` (`Add office-v5 ESN baseline handoff`).
- Inspected `main`: it did not contain an `UPDATE_LOG.md`; therefore this is the first log entry and there are no prior main-log entries to reconcile.
- Added the project workflow skill on the research Mac at `/Users/hwy/.codex/skills/sii-compliance-repo-workflow/`.
- Spark canonical branch checkout: `/home/arm1/SII_compliance_baseline`.
- Existing simulation/runtime and experiment artifact root: `/home/arm1/vmc_mujoco_runtime/`.
- This entry records workflow setup only; no experiment, model, or benchmark result was modified or claimed.
