# 当前代码组织说明

本目录是 `SII_compliance` 的当前 MuJoCo 主线。代码整理遵循一个原则：**不破坏已有服务器入口和同目录导入路径，同时把正式主线、兼容代码、实验工具和历史代码明确分层**。

## 1. 当前正式主线

论文复现和新实验只应从下面这条链路开始：

```text
fixed_panda_wbc.py
    ↓
wbc_velocity_residual_core.py
    ↓
fr3_contact_interface_20260917.py
    ↓
run_vmc_6d_constrained_push_20260918.py
    ↓
build_current_teacher_bank_20260921.py
    ↓
train_matched_action7_20260921.py
    ↓
run_matched_stage1_20260921.py
    ↓
evaluate_matched_guarded_push_20260921.py / office_complex_scene_v5_20260917.py
```

对应职责如下：

| 模块 | 职责 | 是否属于当前主线 |
|---|---|---|
| `fixed_panda_wbc.py` | 固定基座 FR3/Panda resolved-rate WBC | 是 |
| `paper_mpc_wbc.py` | NUS paper-style WBC/velocity layer 参考实现 | 是，作为 paper-WBC 参考 |
| `wbc_velocity_residual_core.py` | 统一 7D action、速度残差、安全过滤和伺服接口 | 是 |
| `fr3_contact_interface_20260917.py` | 因果 joint-load observer 与 6D wrench 估计 | 是 |
| `run_vmc_6d_constrained_push_20260918.py` | 六维 VMC teacher 动力学 | 是 |
| `vmc_compliance_baseline.py` | VMC 兼容封装和基础接口 | 是，但主要供复用 |
| `build_current_teacher_bank_20260921.py` | 构建 canonical teacher bank | 是 |
| `train_matched_action7_20260921.py` | MLP、nonlinear ESN、linear ESN 的公平训练入口 | 是 |
| `current_student_policy_20260921.py` | 冻结模型的部署 contract 和推理加载 | 是 |

## 2. 经典 baseline

经典控制器和 paper-WBC 不要与 teacher 采集脚本混为一谈：

- `run_rod_perturbation_benchmark.py`：直接 Cartesian impedance、rigid tracking 和 VMC 的统一对照入口；
- `vmc_torque_baseline.py`：力矩接口形式的 VMC baseline；
- `mlp_compliance_baseline.py`：历史 MLP compliance 接口；
- `paper_mpc_wbc.py`：paper-style WBC 参考控制层。

这些 baseline 应共享相同的 MuJoCo fixture、控制周期、WBC 名义轨迹、安全限制和任务成功 gate。只有柔顺 action 的生成方式可以不同。

## 3. Teacher 数据与审计

```text
search_unified_6d_teacher_20260921.py
    → 多场景 VMC 参数搜索与 Pareto 候选
build_current_teacher_bank_20260921.py
    → 统一 manifest 和 READY 标记
audit_four_scene_dataset_20260918.py
    → 物理有效性、来源和数据泄漏检查
convert_push_teacher_to_proprio48_20260921.py
    → 历史 push trace 转换为 canonical 48D observation
```

当前 canonical teacher 的要求：

1. 动作是统一的 7D action，而不是场景专用动作；
2. 输入只保留部署可获得的本体感觉/因果 wrench 信息；
3. 障碍物位姿、contact truth、事件时钟只能用于审计和 task gate；
4. split 必须按 `scene / physical fixture / VMC parameter group` 分层；
5. 同一 fixture 不能同时进入 train 和 test。

## 4. Student 训练与评估

正式训练入口只有：

```bash
python scripts/train_matched_action7_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/run \
  --model mlp \
  --seed 20260921
```

其中 `--model` 可选：

- `mlp`：无显式递归状态的多层感知机；
- `esn_nonlinear`：固定 reservoir 加非线性 readout；
- `esn_linear`：固定 reservoir 加线性 readout。

训练后使用 `run_matched_stage1_20260921.py` 进行多 seed 选模，用 `evaluate_matched_guarded_push_20260921.py` 和办公室场景脚本进行冻结模型评估。

## 5. Legacy 和历史代码

`scripts/` 目前仍然保持扁平目录，这是有意保留的兼容策略，因为大量脚本使用同目录绝对/相对导入，直接搬移会破坏服务器复现命令和已记录的 provenance hash。

旧版 teacher、PPO/RL、Direct-ESN、Fan-Ye、office recovery、overnight
campaign、旧 benchmark 和 Fetch/ManiSkill 工程已经从 GitHub `main` 移出，
完整归档于：

```text
/home/arm1/SII_compliance_archive/legacy_20260923_removed_from_main/
```

当前仍留在 `scripts/` 中、但不属于论文主结果的少量模块，是 office/runtime
所需的兼容支持；它们不能被当作 canonical teacher 或 student 训练入口。

## 6. 整理约定

- 新增正式脚本使用日期后缀和明确职责命名，例如 `*_20260921.py`；
- 新实验优先复用 canonical 6D VMC，不再复制一套场景专用 VMC；
- 结果、GIF、checkpoint、运行日志不提交到 Git；
- 代码路径变更必须同步更新 `README.md`、本文件和 provenance manifest；
- provenance 校验命令：

```bash
python tools/check_source_export.py
```

当前 provenance manifest 为 `docs/server_source_20260923.json`。

如果未来需要真正物理搬移脚本，应先把同目录导入改为显式 package import，并重新生成服务器源码 manifest；在此之前保持路径稳定比目录视觉上的“更整齐”更重要。
