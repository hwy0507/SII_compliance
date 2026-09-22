# Scripts 入口索引

脚本目录暂时保持扁平，以保留服务器复现路径和同目录导入兼容性。按功能使用下面的入口，不要按文件名猜测主线。

## Canonical 主线

### 控制与观测

- `fixed_panda_wbc.py`：固定基座 WBC；
- `paper_mpc_wbc.py`：paper-style WBC 参考层；
- `wbc_velocity_residual_core.py`：统一 action、安全栈和速度伺服；
- `fr3_contact_interface_20260917.py`：因果本体感觉负载估计；
- `run_vmc_6d_constrained_push_20260918.py`：六维 VMC；
- `vmc_compliance_baseline.py`：VMC 兼容封装。

### Teacher 数据

- `search_unified_6d_teacher_20260921.py`：VMC 参数搜索；
- `collect_four_scene_pareto_20260918.py`：多场景 Pareto 采样；
- `build_current_teacher_bank_20260921.py`：teacher bank 构建；
- `audit_four_scene_dataset_20260918.py`：来源、物理和 split 审计；
- `convert_push_teacher_to_proprio48_20260921.py`：历史 trace 转 canonical 48D。

### Student 训练与评估

- `train_matched_action7_20260921.py`：MLP/nonlinear ESN/linear ESN 统一训练入口；
- `run_matched_stage1_20260921.py`：多 seed 训练和选模；
- `current_student_policy_20260921.py`：冻结推理 contract；
- `evaluate_matched_guarded_push_20260921.py`：冻结 student 棍推评估；
- `office_complex_scene_v5_20260917.py`：复杂办公室开发测试场景。

## Baseline 和独立实验

- `run_rod_perturbation_benchmark.py`：rigid、Cartesian impedance、VMC 对照；
- `run_benchmark.py`：基础 benchmark 工具；
- `run_grasp_impact_benchmark.py`：抓取/球撞基础场景；
- `run_panel_push_20260920.py`：挡板/棍推场景；
- `run_loaded_push_audit_20260918.py`：持物棍推审计；
- `render_compliance_audited.py`：审计后的渲染与指标导出。

## Legacy / historical

以下脚本保留用于复现旧结果或转换旧数据，不应作为新实验入口：

```text
capture_legacy_teacher45_20260918.py
run_contact_transfer_20260916.py
contact_transfer_student_20260916.py
office_task_v4_20260917.py
office_recovery_scene_v*.py
fan_ye_esn_*.py
run_fan_ye_esn_*.py
train_ppo_sixd_stiffness.py
evaluate_ppo_sixd_stiffness.py
lift_diag*.py
overnight_*.py
run_benchmark_v*_ladder.py
```

`legacy` 只表示协议或数据格式旧，不表示代码一定错误；但这些入口不能替代 canonical 6D VMC teacher pipeline。

## 快速选择

| 目标 | 入口 |
|---|---|
| 运行名义 WBC | `fixed_panda_wbc.py` / `paper_mpc_wbc.py` |
| 生成 VMC teacher | `search_unified_6d_teacher_20260921.py` → `build_current_teacher_bank_20260921.py` |
| 训练 MLP | `train_matched_action7_20260921.py --model mlp` |
| 训练 ESN | `train_matched_action7_20260921.py --model esn_nonlinear` |
| 训练线性 ESN 消融 | `train_matched_action7_20260921.py --model esn_linear` |
| 检查数据来源 | `audit_four_scene_dataset_20260918.py` |
| 运行复杂办公室开发场景 | `office_complex_scene_v5_20260917.py` |

