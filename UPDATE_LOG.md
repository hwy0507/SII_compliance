# 更新日志

本文件记录每次对话交付的文件修改、验证和结果边界；最新记录在前。对应提交号由 Git 历史
查询：`git log --oneline -- UPDATE_LOG.md`。持续提交约定见 [AGENTS.md](AGENTS.md)。

## 2026-09-30 — 初始81回合完成与首个BO决策复核

- 08:57 UTC再次核对main=`b1e14de2dade36eed6cc8d9ce448cd8b4a1565ad`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及日志，无新上游变化；未合并baseline。
- 08:40检查点的初始81回合10录取/71失败，VMC唯一合格fixture厚角2/短撞3/持续推碰0。
  不能把跨参数样本拼成单控制器成功率。实际BO已开始，首个VMC厚角c03录取1/3，低于c01
  的2/3；不称BO已改善。参数未锁定，validation/collection/新ESN未开始，固定预算继续。
- 新增首次BO只读审计及报告：前三候选训练证据独立汇总与history一致；读取九份真实MJB
  哈希，并核对peer audit记录的同模型hash，未冒称重读peer全部模型。冻结源与plan绑定；
  相同优化器实现、seed20260933重放差0。首次是可行性LCB，离散代理不是连续物理超限。
- 初始81条公平三指标图含所有失败，排除另计尚不完整BO尝试，PNG视觉核验通过。
  审计/图/status等44文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0848/evidence/`。
  review SHA=`979ea114c384ba23ced024f37601a35221ed3c27da9f9832ba97d6f14a6dc197`；
  PNG SHA=`31f933a44a09a1fea4eb0189130cc8bfd1ee29191219af9195efc6de8e0a8536`。
  更新三类记录/联合进度/周报。v10未重启，冻结测试、gate和执行器未改；十小时任务继续。

## 2026-09-30 — 54回合检查点与可复算的公平三指标图

- 07:18 UTC核对main=`24c5bac6f26bae935d2367b952ebe0f97bb6fc5b`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，未出现上游变化。稳定v10服务未重启。
- 07:35 UTC前两个初始候选54回合完成：8录取/46失败，全部已核验归档；第三组c02运行。
  VMC合格唯一fixture为厚角2/短撞3/持续推碰0，但短撞3条来自不同候选，不能拼成单策略3/3。
  银行未锁定，BO/独立验证/collection/新ESN尚未完成，截止与预算不变。
- 新增`plot_teacher_bank_search_20260930.py`和测试：只画共同完整候选前缀，核对每条audit SHA、
  fixture/MJB、方法/录取与anchor集合，保留所有失败，partial另计。stage-waypoint RMSE与
  峰矩/峰速分列展示，不当平滑全局路径误差，不挑最佳点，不冒称重新复算物理轨迹。
  5项证据/搬移/不覆盖校验通过；首轮27点PNG视觉检查通过。可选campaign-root映射服务器
  读取根，原执行路径保留，v3旧图不重写。联合进度/周报/主报告同步更新。
- 以下均已逐文件核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_0717/evidence/`含42文件（首轮PNG/PDF/点JSON/来源status/绘图源）；
  `teacher_bank_review_checkpoint_20260930_0722/evidence/`含36文件（支持服务器映射的新版源码/测试）；
  `teacher_bank_review_checkpoint_20260930_0736/evidence/`含36文件（54回合配对状态）。
  PNG SHA=`bf088ec34ac28340a6c19535654dc1d4f4d80885c63926e22643f2e1c9072824`，完整点JSON的
  SHA=`507cae91f03b65b2335c0c4fde6b08d09295dd46e1b1a1a1816f4f919b514c8e`。未改冻结源码或gate。

## 2026-09-30 — 完整首轮27回合及人手子步独立重建

- 06:26 UTC核对main=`f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，均无新上游变更。v10相同服务稳定运行，未重启。
- 06:32 UTC第一轮c00三类×三方法×三anchor共27条全部完成，5录取/22失败并逐条归档；
  持续推碰三方法均0/3。status确认三个类别共同完整候选前缀[0]、模型hash与历史一致。
  进入c01；固定6候选搜索未完成、参数未锁定，collection=0、新ESN未启动。
- 新增`teacher_bank_person_anchor_review_20260930.py`及专题报告，原hash全匹配；每条550000
  物理子步独立重建schema2连续段，差≤1.22e-13。VMC1.2516s/9.09595mm，尚差0.90405mm；
  导纳宏观约27mm不能替代连续段要求；阻抗连宏观也不足1cm。力阈值间断不能当几何脱离。
  保留所有失败，不改gate/冻结环境或源。同步联合进度、周报和三类主报告。
- 新脚本/JSON/完整配对汇总38文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/`。
  review SHA=`2f94c7999c3732582e38b69e005c75e257dda84f510b1f190842ac8e145c7835`。
- f3b42f5完整源码2623文件已核验发布到同一服务器
  `/home/arm1/sii_shared/SII_compliance/source/f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985/`；
  tar SHA=`274e159481c6f9545ce705b0bcfee90455f0c8caf7433aa7b8357d4a0f931b11`。10小时任务仍继续。

## 2026-09-30 — 首两条VMC合格搜索轨迹复核，完整保留接触峰力

- 06:16 UTC核对main=`5ded01a21ed07f57c28786c616507ade46974289`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及两分支日志，未合并baseline；Spark四个新worker运行，
  旧四个进程为T暂停态。本机v10稳定，未重启或新增仿真。
- 06:18 UTC v10完成21条搜索/5条录取/16条失败，另1条运行。共同c00配对：厚角VMC/导纳/阻抗
  0/3、0/3、2/3；短撞2/3、0/3、1/3。VMC持续推碰0/3，其余方法仍在运行；不提前作配对结论。
- 新增`teacher_bank_search_success_audit_20260930.py`及专题报告：VMC短撞337/671原hash与独立
  子步指标重算通过，冻结runner动作/状态重放通过。它们是初始参数搜索样本，不是BO改善，
  不代表独立验证。正式collection=0、参数银行未锁定，各类1000有效示范/新ESN未完成。
- VMC两条合格短撞接触峰力约1368/1350 N，阻抗合格短撞约2077 N；保留冲击风险局限，
  不用电机峰矩合规冒充低碰撞力/真实部署安全。未改变gate、模型或评分。
- status工具新增已完成rollout元数据哈希核验、接触载荷及原失败字段，不冒充独立物理复算。
  19项status测试通过；联合进度、周报及三类记录同步更新。
- 冻结源码输入审计：反馈控制器无直接外部真值字段，但共享task executive使用真实支撑/物块速度
  辅助松爪，并间接改变名义参考。专题文档明确该边界，不将当前系统称为端到端纯本体真实部署；
  本轮不修改共同协议或停止稳定作业。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`下：
  `teacher_bank_review_checkpoint_20260930_0603/evidence/`（40文件，首次VMC复核源码/JSON/报告）；
  `teacher_bank_review_checkpoint_20260930_0621/evidence/`（38文件，06:18状态及status源码/测试）。
  原始轨迹继续逐条归档到`teacher_bank_three_domains_20260930_v10/`。10小时任务继续，截止不变。

## 2026-09-30 — 首个公平配对与pilot失败归因，v10继续运行

- 05:36 UTC核对main=`7423d5ef94df05470ba14188a983f92fc51846b1`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`，已读日志，未合并baseline。
- 05:49 UTC，v10厚桌角c00完成三个方法各3个anchor、同模型hash配对，录取VMC0/3、导纳0/3、
  阻抗2/3。统计含失败，不称泛化；参数银行仍暂定，作业继续短撞类别，本机单环境/1线程/3GiB。
  VMC合格新教师仍0，全部搜索、独立验证、各类1000有效轨迹及ESN未完成。
- 新增`tools/teacher_bank_pilot_failure_causes_20260930.py`及同名专题报告（研究目录内）：
  九条v8原始文件hash全部匹配，子步三指标独立重算差≤6.94e-18m，力矩/速度差0。
  球撞VMC主要晚期释放后滑落；导纳放置漂移、阻抗收敛超时。145mm误差跳变主要来自
  waypoint切换，不能当作碰撞末端位移。人推VMC/导纳约27mm宏观位移横跨微接触间断，
  不能说完全不会让位，也不能追认连续接触/schema2成功。原gate/源/失败记录未改。
- 归因JSON SHA=`c6d3469bea9113edf7416697d31950921b7d2fbf44da3f5016c2c74d6d020986`。
  41个新证据文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`；
  内含归因脚本/报告/JSON、当前status源码和v10_0549预算汇总。新增review归档的显式include选项。
- 已提交源码7423d5e的2618文件经SHA/大小/权限及完整文件集合核对，共享到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7423d5ef94df05470ba14188a983f92fc51846b1/`。
  tar SHA=`47399ebcc9e6463d81f001a3112642ff362e45e9ee46f046efff37229b8cf13e`；初次tar compare
  仅因uid/gid不同而退出，之后独立核验内容通过才发布。新增源码归档核验工具，不改源内容。
- 更新联合进度、周报和三类专题。未重启稳定作业、未新增仿真槽位，10小时原截止不变。

## 2026-09-30 — 三类pilot审计完成，v10公平搜索启动（10小时任务继续）

- 05:19 UTC接续核对main=`8dec129deecf2b769e765c5d91a54a64140a22a7`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`并读日志。baseline的SimbaV2
  campaign_03在Spark四路训练，本任务本机单环境/1线程/3GiB，不修改其分支或作业。
- 已完成v6六条主动pilot、v8九条三类别pilot及服务器归档；v8仅阻抗厚桌角fixture0通过，
  RMSE47.988mm/峰矩45.612Nm/峰速0.15314m/s。接触18840段、其中一个5ms段以0.231mm上抬
  通过已注册曝光，不称平顺明显蹭过。VMC同场任务成功但上抬0.0866mm不足0.1mm，保留拒绝。
  当前合格新VMC轨迹为0，不把3300配置定义当成功示范。未启动新ESN。
- 新训练厚边缘移至掌翼上方，避开下降手掌；18项跨类初态预检通过。只改新增训练域，
  冻结综合测试/gate/actor/执行器不变。几何失败、旧corner曝光不足与v5失败全部保留。
- 修复人手曝光方向与施推时窗，schema2保存每个物理子步；旧schema1不追认为新筛选通过。
  修复搜索anchor的物体形状覆盖（0/337/671），独立验证固定0/1/11。候选成功anchor数量
  优先，之后比较失败标签代理及原评分；不把该离散代理称作连续物理超限。
- 每次dispatch核验实际Panda资产85文件，模型hash跨方法/候选/阶段一致；新增曝光-物理
  时间绑定、观察q/dq-前后状态绑定。九条旧pilot关联只读复核全通过，原audit未改写。
  搜索开始前73项测试通过。数值异常停机待分类，不吞异常或伪造BO指标。
- v8于05:23:21 UTC按预定阶段锁在pilot后停止，末尾BlockingIOError是计划内边界停止，
  不算物理失败。v9只准备未运行。v10于05:29:05 UTC实际启动固定6候选×3anchor搜索，
  首回合完成并归档，未通过接触筛选。服务`teacher-bank-search-v10-20260930.service`。
  计算窗口仍截止13:48:16 UTC；heartbeat保留到14:28只做最后归档审计，不扩展计算授权。
- 已核验服务器根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`。
  其下`teacher_bank_three_domains_20260930_v10/`含源码210文件、metadata2文件、输入3文件，
  运行记录逐条发布。`teacher_bank_runtime_inputs_20260930/menagerie/`含实际Panda资产85文件；
  `teacher_bank_reaudit_v5_20260930/impedance/`为旧raw复审及源码；
  `teacher_bank_review_checkpoint_20260930_0527/evidence/`为34份新几何/pilot报告/计划停止证据。
  所有路径均已SHA256核验，未覆盖历史产物。
- 已更新README、联合进度、周报、三类专题及schema2/手掌阻塞诊断；新增独立审计测试和
  review归档工具。未完成：搜索、锁定参数验证、各类1000条合格teacher、ESN与正式泛化。
  `teacher_bank.json`搜索中只是暂定选择；截止partial block须单列，公平比较用共同完整预算。
- 搜索启动后另扩展只读status，独立核验decision/anchors/执行记录和模型hash、reuse/recovery、
  共同完整候选前缀、截止partial，以及完整搜索后才locked。该工具13项测试通过；没有改
  v10冻结源码或运行过程。实时PID核验需宿主上下文，沙箱生成报告可能看不到systemd进程。

## 2026-09-30 — 启动三类 teacher 数据与经典 baseline 的 10 小时任务

- 开工核对 main=`38caf3152282df4963435bb65c11c93a1e4fffa5`、
  baseline=`59342005b11b5892b18301fd9b52c6b07ad87f45`；开工时其日志仅有初始化，
  其工作区 `/home/arm1/SII_compliance_baseline` 不由本任务修改。
  04:15 UTC再次核对baseline已到`5bc21d8d19eaf60691f561f0ad9dd4409749e667`，已读新日志：
  SimbaV2奖励配对训练/GPU验证与布局合法性修正；不合并其分支，不占用Spark仿真槽位。
- 用户新增授权：三类各至少1000训练环境，VMC同时作teacher/model-based baseline，导纳/阻抗
  同场景同预算调参，多agent协作，持续10小时。窗口至2026-09-30 13:48:16 UTC。
- 新增 `tools/teacher_bank_{design,rollout,campaign,classical,exposure}_20260930.py`、相关测试和
  `docs/TEACHER_BANK_THREE_DOMAINS_20260930.md`、独立场景审查报告（路径相对研究目录）。
  生成3000训练+300验证配置，支持冻结源码、约束BO、原始/过滤动作、物理子步与接触曝光审计。
- 已完成34项新测试；动态pilot发现新训练桌角连接件初态与机器人相交，正确拒绝并归档，
  修正为绕手爪连接后42个初态预检通过。v4九条动态pilot已于04:16 UTC启动。
  v4完成一个有效物理回合但没有真实上抬碰face，不可入库；导纳adapter在仿真前失败已修。
  v5于04:30 UTC启动，VMC/导纳前两条均在align被训练face挡住，负结果保留，继续其他配对。
  尚无合格新teacher轨迹；未启动ESN、不改冻结综合测试或保留集。
- 已核验服务器源码/失败路径：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v2/`。
  v4源码206文件/metadata2文件也已核验归档到同一父目录下
  `teacher_bank_three_domains_20260930_v4/`，动态轨迹完成后逐条归档。
  不覆盖失败记录。详细实时状态和限制见上述专题文档。
- 新增进程身份恢复：仅确认旧PID已退出才另开retry目录，旧文件逐字节保留，基础设施失败
  不进入BO；新增只读状态汇总器。53项测试通过。公共评分移除对力矩阻抗不公平的action7
  平滑罚，补配对MJB一致性和阻抗命令→实际物理力矩审计。
- v5源码209文件、metadata2文件已核验归档到同父目录`teacher_bank_three_domains_20260930_v5/`；
  几何诊断/初态成功及失败的7份JSON已核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_archive_20260930/evidence/`。
- 重要纠正：旧corner task/strict成功不是“上抬碰face成功”证据。新曝光审计把桌面支撑与
  真实上抬碰边分开。十小时按98.3s首回合吞吐无法跑满9000次配对采集；搜索前预注册
  6候选×3anchors/方法/类、每类3个独立验证、之后剩余时间配对采集，3000有效数据目标未完成。
- v5阻抗完整仿真后审计触发3GiB限制，原因是NPZ逐行索引重复解压且保留整列view；已修为
  一次读列＋生成器，54项测试通过。旧raw独立复审4.39s成功，13750servo/550000子步实际力矩
  映射误差0；原failed execution不改写。该复审仅本地、待归档。
  v5现已停止；v6冻结源码的主动短撞/持续推碰六条pilot已启动，仍单环境/1线程/3GiB。

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
