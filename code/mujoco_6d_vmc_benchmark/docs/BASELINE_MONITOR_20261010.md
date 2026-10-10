# 本机 RL baseline 监看与 110k 收口审计（2026-10-10）

监看时间：2026-10-10 12:53 CST。开工按 `sii-research-sync` 核对了仓库状态、并行进程、两个分支日志和既有收口报告。远端网络在本轮不可用，因此本地缓存的分支 SHA 仅作为核对依据：main `6e31e394617b92ad067aab798e3037b930a6bfe9`，baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。

本机没有 `sii-local-rl`、MuJoCo、validate 或 overnight 进程；服务器只做既有产物读取/归档核验。本轮没有启动训练、仿真或服务器作业。两个扩展目录的外层启动收据仍带有历史 `status: running` 字样，但各自实际目录内的 `execution.json` 已完整写入 `status: complete`、`ended_utc` 和 `stop_reason: stop requested`，并且目录最后修改时间分别为 12:22:03 和 12:25:22 CST；不把外层旧状态当作运行中的作业，也不改写历史收据。

## 只读轨迹审计

使用已提交的 `tools/inspect_local_rl_progress_20261009.py`，解释器为 `/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python`，命令为：

```text
inspect_local_rl_progress_20261009.py --root outputs/baseline_local_rl_20261009/campaign_v2 --output outputs/baseline_local_rl_20261009/campaign_v2/monitor_audit_20261010 --training-suffix extended110000
```

审计产物 SHA256：`8ad74de12c28a5182f68a6626587b86eca08e8bf8cf6d2b1801843711af2fafd`。审计只读取已完成训练回合，新增物理步为 0、held-out/final 读取为 0，未把训练身份计数冒充 development 成功率。

| checkpoint | 完整训练步/回合 | Task | Strict | RMSE 中位数 | 峰值力矩中位数 | 峰值速度中位数 | 主要末阶段 |
|---|---:|---:|---:|---:|---:|---:|---|
| direct office_task 110k | 108458 / 40 | 6 | 2 | 52.579 mm | 51.700 Nm | 0.3667 m/s | carry（26） |
| RL impedance 110k | 104500 / 36 | 0 | 0 | 22.777 mm | 42.266 Nm | 0.3708 m/s | carry（20）、retreat（16） |

训练身份指标只能说明已见训练回合的行为。direct 组有 1 回合因全局穿透超过 2 mm 提前终止；impedance 组没有该类中止，但 36 回合仍全部未通过 Task/Strict。两组都尚未在固定 8 条 development 条件上重评，因此不能写成最终 baseline 成功率、不能与 ESN 做最终排名。

## 当前待办

- 对 direct 110k 和 impedance 110k checkpoint 做固定 8 条 development 条件重评，并保存完整原始 rollout、三项物理子步指标、动作重放和失败原因。
- 只有 development 结果稳定后，才进入独立 seed 确认和统一 final 矩阵；保留所有失败回合。
- 四格 reward/n-step 试验仍是 0 物理步的学习机制消融，必须独立闭环评估后才能纳入 baseline。
- 新计算需要新的明确预算登记；在此之前只做状态监视和只读审计。

服务器大轨迹与 checkpoint 当前仍主要在本机；既有已核验服务器归档见 `BASELINE_15H_CLOSE_20261010.md`，本报告不声称新大型包已上传。
