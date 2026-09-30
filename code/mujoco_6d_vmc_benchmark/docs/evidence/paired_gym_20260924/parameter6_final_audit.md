# parameter6 PPO8192：最终独立审计

完整运行通过：固定8192步/384更新、四项最终eval、冻结源、全部实际transition奖励和SB3 float32转换已核验。完整训练episode 13条，task 7/13，gate 7/13；partial步数[392]。

| 条件 | task/gate | steps / 实际s / 安全早停 | final stage | lift m | 当前阶段endpoint mm | 外部单对象力峰N |
|---|---|---|---:|---:|---:|---:|
| train/zero | True/True | 600 / 24.00 / False | 3 | 0.242989 | 5.639 | 217.108 |
| train/ppo | True/True | 600 / 24.00 / False | 3 | 0.243871 | 4.799 | 217.108 |
| validation/zero | False/False | 600 / 24.00 / False | 3 | 0.12955 | 111.724 | 116.299 |
| validation/ppo | False/False | 600 / 24.00 / False | 3 | 0.135123 | 107.095 | 132.462 |

stage1是抓取对齐，stage2闭爪，stage3抬升；当前waypoint误差不能替代最终抬升成功。两模式zero含义不同，不将zero6解析VMC与zero7执行残差混为一谈。

安全早停作为已终止的失败评估保留，须有invalid_physics及独立terminal审计；实际时长按记录核对，未伪称满24s。endpoint仅取实有末min(10,步数)帧。

审计报告中的逐episode列表包含完整与partial全部实际奖励、末next、控制器重播和telescoping残差。未记录critic/advantages，不能据此宣称实际bootstrap值已核验；单seed/少量fixture亦不构成泛化结论。

供后续prepare入口使用的flat原审计：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/docs/evidence/paired_gym_20260924/parameter6_training_transition_audit.json`，SHA256 `4fc389bc8b6c456a4ec7210b90ef2094af99127736ef1c8847775c3c611d1894`。

最终checkpoint SHA256 `b572e3a20e0a7955ee9bf014f48579aa2c07507136c7ba8bf40a482a3306e33f`。

训练normalizer SHA256 `aee95256242c170b18b65c7998679d462121df61602fb90dfd592e362094a715`。
