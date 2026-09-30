## 2026-09-30 — 100k奖励主实验完成、发现训练覆盖瓶颈并启动独立修正诊断

- 开工读取main e1d815c390d1221ee0bf80293e2b8179d2e1d3f8 与baseline日志；main的teacher-bank任务独立进行，未合并或修改其作业。
- 主实验 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03/ 完成8×100k transitions、每条190002更新/40000000物理子步；40候选验证、90最终回合和全部进程均正常收尾。冻结frozen_v3/source32d2ea5不变。
- 主selected测试每组3seed×6条件、全55s/dt5e-5、物理有效全通过，但task/placement/strict皆0。office_task RMSE10.4868±4.8930cm/峰矩41.9397±12.3139Nm/峰速.0936±.0363m/s；metric4.2742±2.4923cm/37.7209±1.2178Nm/.1503±.0214m/s。不能说三指标全面更好或已充分收敛。
- fixed100k有7提前global_penetration>2mm终止（office6、metric1），只作混合长度失败诊断；仓库report.py补实际时长、55s完整率与abort，3项报告测试通过。独立审计86回合原始时长、21回合raw三指标复算通过（含7abort）；plot_results.py逐90回合核对实际MJB与模型/manifest/hash。小证据和已视觉核验图见docs/evidence/simba_reward_20260930/。
- 648个完整训练episode无一进入grasp：起点与初始waypoint重合，旧potential退化为ready/.2，随机残差打断停稳后Phi=0占主组约72.6–99.95%。nominal_zero同环境可完成1/6任务（strict0），不能归咎环境不可达。当前结果不能排除训练设计人为弱化baseline，报告明确承认这一限制。
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
