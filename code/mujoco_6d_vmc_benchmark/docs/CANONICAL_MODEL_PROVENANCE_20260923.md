# 当前 48D matched student 模型来源审计

记录时间：2026-09-23 17:43:58 Asia/Shanghai（09:43:58 UTC）。服务器只读核查在记录前同一会话完成。通过 SSH 读取目录、JSON 和 NPZ，计算 SHA256；没有修改服务器文件，没有启动训练。

服务器：`arm1@192.168.31.70`。项目根目录：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark
```

本记录固定可用于新 panel **开发评估矩阵**的已存在模型；不将这些模型认定为经过完整论文冻结流程的最终模型，也不将新的开发矩阵称作未见过的 blind test。

## 正确的选模文件

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_6d_matched_students_20260921/RESULT_SUMMARY.json
```

文件 SHA256：`b99fbe9db02d406b96f3696b67c6e089c501116ac65d2a7314403b6e5fbe6060`。

该文件的 `aggregate.<model>.best_validation_checkpoint` 和 `best_validation_seed` 明确列出每个 family 的选模结果。文件声明 `office_used_for_training_or_selection=false`。下面使用的是该文件原有选择，不根据新 panel 结果重新挑选 seed。

| Family | 选中 seed | validation balanced scaled MSE | test balanced scaled MSE | 实际 NPZ contract |
|---|---:|---:|---:|---|
| MLP | 20260923 | 0.1993043523195655 | 0.3688349273741298 | `proprio48_action7_mlp_v1` |
| nonlinear ESN | 20260923 | 0.1716429275482696 | 0.3222500214467333 | `proprio48_esn128_action7_v1` |
| linear ESN | 20260922 | 0.4499339628153342 | 0.8389627895296199 | `proprio48_linear_esn_action7_v1` |

这些 MSE 是 teacher action imitation 指标，不等于闭环任务成功率。test 指标已存在于历史结果文件，本轮读取只用于记录来源，没有参与选模。

## Checkpoint 路径与 SHA256

MLP：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_6d_matched_students_20260921/mlp/20260923_retry1/best.npz
SHA256 5327061ccbfc147c410be355bd82c6769736978de971afa48a01844fc4dd87b7
```

Nonlinear ESN：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_6d_matched_students_20260921/esn_nonlinear/20260923_retry1/best.npz
SHA256 0f9d1c2970bbf9e35f9748eb68ae73c84340e6f4e193f3ee37e584970337975a
```

Linear ESN：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_6d_matched_students_20260921/esn_linear/20260922_retry1/best.npz
SHA256 2b9e7f45e8df8244c6fd856e75a34ccfb4226336d75ec65ac0bf8d1f847c3390
```

三份 NPZ 均使用 `allow_pickle=False` 打开，实查 `mean.shape==(48,)`、`std.shape==(48,)`，normalization 内嵌 checkpoint。各自目录的 `protocol.json` 和 `TRAINING_COMPLETE.json` 声明 observation_dim=48、action_dim=7，dataset manifest hash 与下文一致。

MLP 和 nonlinear ESN 的协议均为 100 epochs、48 steps/epoch、batch size 4096，使用相同 uniform scene / uniform episode / uniform time sampler 与 per-action training-std scaled MSE。MLP hidden=128，nonlinear ESN reservoir_units=128；选中 MLP best_epoch=80，nonlinear ESN best_epoch=100。Linear ESN 是 ridge readout 模型，不能仅因协议 JSON 也含 epochs 字段就声称它实际进行了相同梯度更新。

## Teacher bank 和 normalization

数据根目录：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_6d_four_scene_proprio48_20260921
```

| 文件 | 实际 SHA256 |
|---|---|
| `manifest.json` | `8762b865a9bce8f3dd98e3495d71b3ad0e05d900c69e7e878b98b46fbff78847` |
| `normalization_train_only.npz` | `d6b0d6463fd79a85481acdc0dde6e73c30241228bc757dcf10356c5006ae4e21` |
| `quality_certificate.json` | `77eaf3e446834988f8c4137818935769d845ad642e7db49032c8ad80094e292d` |
| `READY.json` | `1f0fd304d1c563ecfe8a6caa7b9edb8a65225e6cd23d3bebf72f99fc3e0a9339` |

Manifest contract=`proprio48_action7_6d_v1`。READY 中记录的 manifest SHA 与本轮实算相符；模型训练协议中的 manifest SHA 也相同。证书声明 observation_dim=48、action_dim=7、fixture_disjoint=true、parameter_group_disjoint=true、office_data_used=false。

| Split | Episode 数 | Sample 数 | ball | push | corner | table_corner |
|---|---:|---:|---:|---:|---:|---:|
| train | 841 | 486050 | 9 | 714 | 16 | 102 |
| validation | 255 | 146575 | 2 | 227 | 1 | 25 |
| test | 89 | 48625 | 2 | 67 | 1 | 19 |

Physical fixture 分配：

| Scene | Train fixtures | Validation fixtures | Test fixtures |
|---|---|---|---|
| ball | `b_anchor`, `b_left`, `b_right` | `b_loaded` | `b_fast` |
| push | `rod`, `rear`, `combined` | `front` | `rear_combined` |
| corner | `c_anchor`, `c_left`, `c_right` | `c_wide` | `c_narrow` |
| table_corner | manifest 中标为 train 的 hash fixture | manifest 中标为 validation 的 hash fixture | manifest 中标为 test 的 hash fixture |

table_corner 的具体 hash fixture 和 parameter_group ownership 保存在上述 manifest，不通过本文件简写代替原始清单。

## 实际计算的 split 不相交证据

本轮从 `manifest.json["rows"]` 按 `row["split"]` 构造集合，实际计算下列交集；不是仅引用 quality certificate 的布尔字段：

| row 字段 | train ∩ validation | train ∩ test | validation ∩ test |
|---|---:|---:|---:|
| `physical_fixture` | 0 | 0 | 0 |
| `fixture_hash` | 0 | 0 | 0 |
| `parameter_group` | 0 | 0 | 0 |
| `content_hash` | 0 | 0 | 0 |

12 项交集均为空。此检查证明 manifest 记录的标识和 content hash 跨 split 不重叠；没有重新读取全部 episode NPZ 并重算 content hash，也没有重新运行教师生成过程。

## 必须排除的旧模型与审计局限

- `outputs/paper_stage1_matched_20260921/selection.json` 虽然命名为 matched，实查该目录九份 `models/*/*/best.npz` 的 normalization 都是 45D，contract 分别为 `current_four_scene_action7_mlp_v1`、`four_scene_contact45_action7_v1`、`linear_esn_action7_v1`。它们不能当作当前 proprio48 模型。
- 没有选用 9 月 2 日的历史 Direct-ESN，也没有基于新矩阵表现选用后续 DAgger、corner focus 或 reservoir scan 模型。
- 原有元数据声明 office 未用于训练或选择，但本轮无法证明此前研究者是否已经查看或使用过 held-out 输出来改变数据、超参数、场景或研究方向。因此它们仅用于开发矩阵；正式 blind test 必须重新制定并冻结未参与开发的评估协议。
- SHA256 固定的是当前服务器文件字节；服务器目录不是 canonical Git checkout。没有因此证明历史训练脚本与今日 GitHub 源码完全相同，也没有重新执行训练。
- 数据 manifest 的 split 不交叉并不能单独证明传感器输入无泄漏、fixture 物理真实性或 reward/gates 正确。这些需要独立审计 runner 与 observation 构造。
- 当前 ball/corner 的 validation/test episode 数较少；MSE 不足以支持强泛化结论。新 panel 矩阵需要记录 checkpoint hash、执行脚本 hash、场景/config、原始 rollout 和严格 gate 结果。
