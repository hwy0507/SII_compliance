# 2026-09-30 发布证据

`artifact_manifest.json` 记录相对于 `code/mujoco_6d_vmc_benchmark/` 的源路径、字节数、
SHA256，以及小型证据的复制路径。由 `tools/export_publication_evidence_20260930.py` 生成。

- `teacher_repair_20260930/`：MuJoCo 3.14 的误版本诊断，不能计入有效成功。
- `teacher_repair_canonical_20260930/`：固定 MuJoCo 3.11 的首轮八条有效实验。
- `teacher_repair_followup_20260930/`：第二轮四条有效实验；original 参照首轮同名场景，
  不是四条额外重跑。

上述目录只复制已有 JSON、Python 源码快照和 Markdown，保留原始内容与绝对路径以便审计。
NPZ、MJB、视频等原始大文件仍在本机／原实验服务器，未删除，未随普通 Git 推送。
该索引不涵盖所有历史 outputs 或服务器数据；小型历史 docs/evidence NPZ 另有版本管理。

复现需要取得原始数据、checkpoint 和所依赖的场景资产，并把它们恢复到工具所需位置。
必须核对 execution.json 的 Python/MuJoCo 版本和模型 hash；跟进脚本还依赖首轮已完成的
outputs 目录与固定 hash 的 runner 快照。此导出供审阅与核验，不能声称 clone 即可完整重放。

具体结论和未完成项见 ../../TEACHER_REPAIR_20260930.md。开发任务成功不等于综合 strict
通过；所有失败和版本不匹配记录一并保留。
