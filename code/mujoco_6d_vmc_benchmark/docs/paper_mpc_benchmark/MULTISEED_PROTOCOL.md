# Paper-MPC 多评估种子协议

## 目的

Paper-MPC 三场景基准原先只使用一个评估种子（`20260819`）。评估脚本现在支持显式传入多个种子，逐个重置 MuJoCo 环境，并把每条原始 rollout 与聚合统计分开保存。这样可以把任务成功率、抓取时刻误差、峰值接触力和恢复时间报告为均值 ± 标准差，同时保留逐种子证据。

## 运行方式

在服务器上激活 MuJoCo 环境后：

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
export MUJOCO_GL=osmesa

python run_paper_mpc_benchmark.py \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --esn /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_bench/esn_final_101.npz \
  --mlp /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_bench/mlp_h128_s2.npz \
  --student-budget 0.03 \
  --eval-seeds 20260819,20260820,20260821,20260822,20260823 \
  --phase students \
  --out /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_bench/results_students_5seeds.json
```

`--eval-seeds` 是逗号分隔的整数列表；脚本会保持用户给出的顺序并去除重复值。省略时仍使用历史默认种子 `20260819`，因此旧命令保持兼容。

## 输出契约

- `results_students_5seeds.json`：原始结果行，格式仍是 JSON list；每行新增整数 `seed` 字段。现有单种子结果读取脚本无需改动。
- `results_students_5seeds_summary.json`：按 `name` 聚合的统计。每组包含 `seed_count`、`success_count`、`success_rate`，以及 `at_grasp_err_mm`、`peak_postimpact_err_mm`、`peak_torque_nm`、`obstacle_force_n`、`recovery_s` 的 `mean/std/min/max/count`（无有效值的指标不写入）。

接触力检测现在只使用 `contact_peak_force` 的 `robot_geoms` 参数，不依赖进程级全局缓存；这避免多个种子连续运行时复用上一个环境的几何集合。

## VMC 调参说明

`--phase vmc` 的第一阶段仍只在首个评估种子上做配置筛选，以保持原有 sweep 成本和“先选配置、再评估”的协议。第二阶段用选出的每个场景最优配置跑全部 `--eval-seeds`，因此 `vmc_best/*` 组才是多种子比较应使用的结果；`vmc_k*` 行属于首种子的调参记录。

## 解释结果

成功率按组内原始 rollout 的布尔值取均值；连续指标只对有限值计算统计量，缺失恢复时间不会被当作零。正式报告应同时引用 sidecar 的均值/标准差和 raw list 中的每个 seed，避免只报告一个幸运种子。
