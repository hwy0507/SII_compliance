# 接触—让位门控 teacher 全量重采与公平重训接续

本轮继续修复三分离特化主矩阵，不涉及 RL。已有证据定位到三个不同层次的问题：历史综合测试与新分离场景范围不一致；旧 teacher 对部分学生偏离缺少竖直路径阶段的横向恢复；部分 ESN 候选闭环进入训练特征范围之外后读出放大。后两者不能凭训练 MSE 变小就判定已解决。

## 已完成的修复与证据

最新 `VerticalStageScrapeTeacher` 沿用有界横向恢复，并只在 canonical48 估计横向载荷达到 1 N、相对接触时误差变化至少 4 mm 后，启用上限 0.02 m/s 的平滑路径切向补偿。不读取时钟、阶段、几何或成功标志；MJB、物理、dt=5e-5、输入、公共 filter、执行器和全部评估门槛不变。简单提前推进的旧版本三条均无合格棍推，失败保留。

接触门控版本的 rod09/04/01 三条完整开发探针独立审查均通过。rod09 实际接触 4.918 s，让位 5.04 s，越棍 10.68 s，持续回位确认 10.76 s，撤回开始 12.95 s。这不是 ESN 学习结果，也不是未见测试成功。teacher 调整使用了开发 validation 的 rod09；因此这六条 validation 是开发选模数据，不再声称是 teacher 的独立留出验证。最终 unseen108 未曝光。

[探针证据](evidence/nonrl_v9_candidate_catalogue_20261029/VERTICAL_STAGE_SCRAPE_TEACHER_PROBES_20261030.json) 中旧 collection 的摘要 execution SHA 曾手工抄错；实际为 `434f222598d4601f178b63731f75d206894a320d2144ad3ff76d868cb915ebcc`，与探针 REGISTRATION 一致。绑定中的旧摘要不改写，新增 [启动收据](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_SCRAPE_LAUNCH_20261030.json) 明确更正；原始轨迹未变。

## 当前真实运行

唯一物理采集服务 `sii-contact-yield-scrape-collection-20261030.service`，PID1827286，Invocation `ec3b6f480c184966bf86c5def563210d`。输出 `code/mujoco_6d_vmc_benchmark/outputs/contact_yield_scrape_collection_20261030_v1`。固定 30 身份、每场景 8 train/2 validation，复用相同 teacher 配置、场景参数、seed、MJB 的三条探针；新执行 27 条，每条一次。与旧初始 canonical48、MJB 和 filter 配对核对。失败完整保存，任一失败禁止建集。

04:13 上海时间快照已有 3 条完成且合格、rod03 在途；[独立前缀复核](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_SCRAPE_COMPLETED_PREFIX_20261030.json) 重新核 actor、标签、时间、初态、配置、来源与原 filter 审计。此分母是完成前缀，不能报作全 30 成功。采集实际 MemoryCurrent 约 1.04 GB/3 GiB，OOM0、实验 swap0；CPU6、单线程。

唯一训练等待器 `sii-contact-yield-scrape-training-handoff-20261030.service`，PID1829248，Invocation `38c81cf821ad40a8ab0bdee1f9ad16ab`；其执行记录位于 `outputs/contact_yield_scrape_training_handoff_20261030_v1`，当前 waiting_for_collection、dispatch_attempted=false，约60 MB。只等待，不增加模拟器。两服务均无自动重启。**不要重跑 prepare、collection 或等待器，不编辑任何已登记源码。**

## 后继步骤和边界

等待器最多等待两小时。须全30独立合格、采集停止、拿到公共计算锁后，逐帧复核后建集。纯 teacher 24/6 全轨迹划分，不混入未经 warmup 语义审计的学生前缀/teacher 后缀。全量数据合格才接续 ESN/RNN/MLP 各 3 seeds、每族每 seed 12 候选；神经 32k 更新，沿用统一 requested-action validation MSE 选模。75 个训练作业代表108个候选。九模型锁定后完整 fit/source/checkpoint/exposure/导出 actor 复核。新 builder 补齐旧 fit 审计要求的真实 lineage.hashes 字段，避免原 builder 接口不兼容导致假失败。

原29/30数据拒绝、新采集未完成拒绝、重复prepare拒绝、active/deactivating不派发、少于30/重复身份/不合格不得派发等控制通过。首轮控制误用了系统 Python，因缺 PIL 在 import 阶段退出，零物理；随后使用登记的 `.venv-sii-local-rl` 解释器复核通过。

等待器不自动派发最终测试。后继须先审九模型及必要的共同开发闭环；训练/teacher失败继续诊断数据、学习或场景接口，另登记修复，不修改历史失败或放宽门槛。最终仍是冻结分离 unseen108，Task、Strict、双通过SPT、平均峰矩、人舒适（实际缺通道记NA并分列代理）、机器合规。旧综合场景结果只作历史压力测试，旧57个未完成格也不抹掉。

目前训练尚未开始，未产生新 ESN/MLP/RNN 成绩，主矩阵仍待修复。Goal active。新的 raw 仅本地；此前服务器 raw 导出被自动审查拒绝，本轮未绕过或声称已归档。服务器未用于计算。

本轮宿主 fetch 成功，核 main `80c856d89627acc95b40c456781014b6989682a4`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 及两分支 UPDATE_LOG。普通 sandbox 网络/user bus 隔离失败已由宿主级核验纠正。
