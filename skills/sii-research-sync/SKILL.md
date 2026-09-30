---
name: sii-research-sync
description: SII_compliance 项目的协作工作流程。在该仓库开展研究、代码修改、实验或交接时，先核对 GitHub main 与 baseline 的更新日志，优先本地计算并在服务器共享产物，收工按 AGENTS.md 更新进展、提交和推送。适用于 hwy0507/SII_compliance，不扩展到无关仓库。
---

# SII 研究同步

用于 `https://github.com/hwy0507/SII_compliance`。用户已授权本仓库每轮工作后的常规
commit/push；不要因本 skill 再索要相同授权。用户当轮的新要求优先。

## 开工：先读两个分支

1. 确认仓库根目录、origin、当前分支及工作区状态，读取根目录 `AGENTS.md`。本机常用仓库为
   `/home/airpig/桌面/hwy/compliance_control/SII_compliance`，其他机器用实际 checkout。
2. 查询远端真实分支，再 fetch 存在的分支。示例（在仓库根目录）：

   ```bash
   git ls-remote --heads origin refs/heads/main refs/heads/baseline
   git fetch origin refs/heads/main:refs/remotes/origin/main
   git show origin/main:UPDATE_LOG.md
   ```

   仅当远端确有 `baseline` 时再运行：

   ```bash
   git fetch origin refs/heads/baseline:refs/remotes/origin/baseline
   git show origin/baseline:UPDATE_LOG.md
   ```

   不切换或覆盖当前工作区来读日志，不拿陈旧 remote-tracking ref 冒充远端最新状态。
   若 baseline 或日志不存在，明确记录“分支／日志缺失”，不自建分支、不臆造更新；继续
   不依赖它的工作。网络失败时标明缓存 SHA 与时间，不宣称已检查最新；依赖最新状态的
   冲突解决、实验重复性判断和发布必须等核验恢复。
3. 对照上次进度，读完最新更新及其涉及本任务的报告；记录两分支 SHA、检查时间、相关
   改动、进行中实验与数据位置。尤其检查环境版本、gate、接口、teacher/checkpoint、
   解释器与物理参数是否变化。两个分支的日志不是自动合并代码的授权。
4. 检查本机与服务器相关进程、服务、checkpoint 和 `execution.json`，确认没有重复作业，
   再开展任务。不同 agent 的实验使用不同 run-id；不停止或覆盖别人的运行。

## 执行：本地计算，服务器共享

- 用户当前偏好：**尽量在本地计算，持久文件尽量放服务器**。本地保留代码 checkout、环境
  和高速临时工作集；checkpoint、轨迹、源码快照、审计、媒体优先归档到服务器。
  本地单 MuJoCo 环境、1–2 线程、MemoryMax≤3 GiB；本地不适合的已授权任务才使用 Spark，
  先查现有负载并保持总仿真并发≤4。不要为存储偏好重启稳定作业或更换已冻结解释器。
- SSH 使用既有密钥：`arm1@192.168.31.70`。共享根目录：
  `/home/arm1/sii_shared/SII_compliance`。
  - `source/<完整 commit SHA>/`：不可覆盖的已提交源码快照；未提交源码须另存 run 专属
    快照并记录内容 hash，不能标成干净 commit。
  - `runs/<branch>/<唯一 run-id>/`：该实验的配置、执行记录、源/模型 hash、checkpoint、
    原始轨迹、失败原因、审计与媒体。
  - `incoming/`：传输暂存区，尚未核验的文件不能写成“已共享”。
- 可先在本地算完，再用 rsync/scp 同步到专属暂存路径，核对大小与 SHA256 后发布到
  不存在的最终 run 目录。不要 `rsync --delete` 或覆盖已有同名运行；不要移动、改写其他
  agent 的既有 runtime。长任务在一致的 checkpoint 边界同步，不能把半写文件当有效产物。
- 新更新文档优先给出服务器端**主机＋绝对路径**，例如
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/<commit>/code/...`。
  同时记录 Git commit、分支、seed、命令、解释器/库版本、源/配置/checkpoint hash、实际计算
  主机和归档状态。GitHub 源码链接可作为辅助入口；本地路径仅作为执行来源或缓存路径。
- 不改历史 `execution.json` 中真实的本地执行路径来伪造远端执行；新建归档映射记录来源与
  服务器目的地。服务器不可用时明确标记“仅本地、待同步”，保留本地副本，不写不存在的
  远端路径。既有历史产物不因本规则被自动全量迁移或删除。

## 收工：重新读取 AGENTS.md，再发布进展

1. 重新读取仓库根目录 `AGENTS.md` 并执行；用户所称 agent.md 指该实际文件。检查是否有
   新的并行修改，只暂存本任务相关文件，不代替 baseline agent 提交其未完成工作。
2. 在根目录 `UPDATE_LOG.md` 顶部记录本次改动、开工时核对的两分支 SHA/缺失状态、验证、
   已完成／运行中／未完成、失败原因，以及**已核验的服务器代码和产物路径**。按需同步专题
   进度、周报或交接；不得将开发结果写成正式通过，不隐去失败或更改研究约束。
3. 将源码、配置、文档和小型证据提交到 GitHub；大型数据留服务器，仓库记录 hash 与地址。
   本任务默认遵循 `AGENTS.md` 推送 `main`；其他 agent 如获用户明确指定 baseline，遵守其
   分支授权，不将整条 baseline 擅自合并 main。推送前再次 fetch，安全整合冲突，不 force push。
4. 核对远端含本次提交，确认服务器共享副本与所记 hash 一致。最终交付给出提交号、
   `UPDATE_LOG.md` 入口以及实质结果；若推送或归档失败，明确区分本地完成与远端未完成。
   无文件修改的纯答疑不造空提交。

## Skill 自身维护

仓库版位于 `skills/sii-research-sync/`，可发现的安装版位于
`/home/airpig/.codex/skills/sii-research-sync/`。修改仓库版后同步安装版，运行
skill-creator 的 `scripts/quick_validate.py`，按同一收工流程记录并发布。其他机器可将
该目录安装到自己的 Codex skills 目录；不要依赖作者本机路径来读取 skill 内容。
