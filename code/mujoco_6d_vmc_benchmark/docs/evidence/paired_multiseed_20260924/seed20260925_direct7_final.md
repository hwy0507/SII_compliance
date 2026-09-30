# direct7 seed=20260925 PPO8192：最终独立审计

完整运行通过：固定8192步/384更新、四项最终eval、冻结源、全部实际transition奖励和SB3 float32转换已核验。完整训练episode 13条，task 0/13，gate 0/13；partial步数[392]。

| 条件 | task/gate | steps / 实际s / 安全早停 | final stage | lift m | 当前阶段endpoint mm | 外部单对象力峰N |
|---|---|---|---:|---:|---:|---:|
| train/zero | False/False | 600 / 24.00 / False | 3 | 0.0603241 | 187.670 | 217.614 |
| train/ppo | False/False | 600 / 24.00 / False | 0 | -1.41448e-07 | 55.733 | 244.541 |
| validation/zero | True/True | 600 / 24.00 / False | 3 | 0.2285 | 7.068 | 87.698 |
| validation/ppo | False/False | 600 / 24.00 / False | 3 | 0.208408 | 24.173 | 29.369 |

stage1是抓取对齐，stage2闭爪，stage3抬升；当前waypoint误差不能替代最终抬升成功。两模式zero含义不同，不将zero6解析VMC与zero7执行残差混为一谈。

安全早停作为已终止的失败评估保留，须有invalid_physics及独立terminal审计；实际时长按记录核对，未伪称满24s。endpoint仅取实有末min(10,步数)帧。

审计报告中的逐episode列表包含完整与partial全部实际奖励、末next、控制器重播和telescoping残差。未记录critic/advantages，不能据此宣称实际bootstrap值已核验；单seed/少量fixture亦不构成泛化结论。

供后续prepare入口使用的flat原审计：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/docs/evidence/paired_multiseed_20260924/seed20260925_direct7_transitions.json`，SHA256 `124985bfa39e0cf77a0e298f928a1c209ab7cb560eccd87f235643fa824b1175`。

最终checkpoint SHA256 `6a29dc6a05eb2510b4f3e5f7965936ef808056e9d6f6223cc0e6da89326be30c`。

训练normalizer SHA256 `1e85f3324c57316890ca6a040a454775581a29d8bde738082ccf98ca06bc08a9`。
