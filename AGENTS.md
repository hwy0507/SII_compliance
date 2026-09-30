# 本 baseline 分支的优先约定

本会话用户明确指定：只提交/push baseline，所有新增项目文件保存在 Spark。
以下继承的 main 约定作为背景；其中 main 发布/本地计算偏好不覆盖本分支用户授权。
开工读远端 main 与 baseline 的 UPDATE_LOG.md；本分支 workflow 见
[skill](.codex/skills/sii-compliance-repo-workflow/SKILL.md)。
当前真实 Git checkout 为 /home/arm1/SII_compliance_baseline；历史错误的独立根提交
保留在分支 snapshot_initial_20260930，当前 baseline 已恢复原远程提交历史。
运行中的实验使用冻结 source 快照，不热更新 runtime。

# 本仓库的持续工作约定

用户于 2026-09-30 明确授权并要求：**每次对话结束前，将本次文件改动 commit 并 push 到
`https://github.com/hwy0507/SII_compliance` 的 `main`，同时维护根目录 `UPDATE_LOG.md`。**
本约定适用于本仓库后续任务，覆盖旧进度文档中“保持未提交／不发布”的历史要求；用户后续
明确变更指令时，以新指令为准。

## 每次开工前与存储偏好

- 本仓库任务使用 [sii-research-sync](skills/sii-research-sync/SKILL.md)。先查询远端分支并
  获取、读取 `main` 和 `baseline` 上的 `UPDATE_LOG.md`，记录 SHA 和与本任务有关的更新，
  再开始研究或修改。分支／日志缺失须如实记录，不自建、不使用陈旧引用冒充最新状态。
- 优先在本地计算，文件持久化与跨 agent 共享优先使用
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`。
  源码存 `source/<commit>/`，实验存 `runs/<branch>/<run-id>/`；使用独立目录与 hash 核验，
  不覆盖既有服务器 runtime。允许本地工作副本和缓存，历史数据不自动迁移或删除。
- 新更新文档的代码与产物位置优先指向已核验的服务器绝对路径，同时保留实际计算主机、
  Git SHA、环境版本和源/产物 hash。未上传的文件明确写“仅本地、待同步”；不改写历史执行记录。
- 每次收工重新读取本文件并执行以下流程。若其他 agent 有用户明确指定的 baseline 分支
  工作约定，遵守其授权；不得擅自把 baseline 全分支合并到 main。

## 每次交付前

1. 检查分支、远端、工作区和并行任务，保留他人的改动；通常只提交本次任务的文件。
   本次首次同步另获授权纳入截至 2026-09-30 的已有研究积累。
2. 在 `UPDATE_LOG.md` 顶部增加记录：日期、修改目的和文件、验证、研究结果与局限、未完成项。
   不以任务阶段名或文件名推断成功，不把开发结果写成正式结论。
3. 做与改动相称的验证，检查暂存差异、大文件和敏感内容。仅为答疑且无文件改动时，不必造空提交。
4. 显式暂存目标文件、提交，检查远端 `main` 是否前进，然后正常推送到 `main`。
   不使用 force push，不重置或覆盖其他 agent 的工作；必要时安全整合远端提交。
5. 核对远端包含新提交；最终回复说明提交号和更新日志位置。若认证、网络或冲突阻止发布，
   如实说明本地提交和远端状态，绝不声称未完成的 push 已成功。

## 产物和实验边界

- 不提交凭据、私钥、环境目录、临时锁或运行日志。大型原始轨迹、编译模型和视频保留本地／
  原实验服务器；提交配置、源码、报告、必要的小型证据和产物 SHA256 清单。
  `.gitignore` 不等于删除产物，Git clone 也不等于完整原始数据备份。
- 发布时说明缺失的大文件、绝对路径和运行时依赖；复现实验须按 execution.json 核对解释器、
  MuJoCo 版本、模型及源码 hash。不得用重编译后的不同模型冒充归档模型。
- 当前优先修正 teacher 并验证特化条件，再做纯 ESN。未经用户新授权，不改冻结环境、gate、
  actor 输入、执行器限制，不解封保留条件，不把 dt=1e-4 开发结果当作 dt=5e-5 正式结果。
- 保留失败回合。读取进度、运行服务和 execution.json 后才启动实验，避免重复；本机一个
  MuJoCo 环境、1–2 线程、MemoryMax≤3 GiB，Spark 总仿真并发≤4。
