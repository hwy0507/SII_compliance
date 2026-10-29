# 五组已选模型的45条开发指标预检

本轮直接使用最终测试入口的独立actor/filter replay与v2指标审计，对一个精确execution快照里全部五组已选模型、各自九条共同开发闭环运行只读检查。不是未见测试，不产生局部T_ref/SPT，不按这些时间或力矩再次挑模型。

结果45/45通过：原Task与三特化Strict、13样本任务终态保持时间、完整预定horizon、子步有限性/时钟、执行器上限、外穿透和动作/filter回放均通过。两个ESN与三个RNN的九开发资格不只依赖原qualification的passed标志；但仍不能外推为最终泛化成功。

| 方法与seed | 已核回合 | 任务确认时刻范围(s) | 九回合中最大峰矩(Nm) | 九回合最大外穿透(mm) |
| --- | ---: | ---: | ---: | ---: |
| ESN 2026102802 | 9 | 9.08–22.20 | 52.532561 | 0.070872 |
| ESN 2026102803 | 9 | 9.32–18.76 | 51.886267 | 0.077015 |
| RNN 2026102801 | 9 | 9.00–16.84 | 51.630905 | 0.069107 |
| RNN 2026102802 | 9 | 9.52–17.96 | 50.513295 | 0.138010 |
| RNN 2026102803 | 9 | 9.24–17.00 | 51.804913 | 0.073652 |

上表为混合三场景开发条件的范围和最大值，**不是最终平均峰矩、方法胜负排名或正式SPT**。每回合完整逐关节峰矩/峰速/外穿透、任务时间和代理接触时间保存在JSON。人体舒适度仍NA；代理不当作实际人体舒适。

新增`code/mujoco_6d_vmc_benchmark/tools/audit_v9_selected_development_metrics_20261030.py`：先核3或12候选共同协议、精确选中候选与九条完整case、qualification/checkpoint hash，再逐格独立replay及最终指标计算。单格实现错误会完整记录failed_preserved，继续审查其余格；总报告任一失败不能标passed。原文件不改写，无积分/拟合/最终条件结果读取。输出冻结execution与registration快照，不因协调器后续推进覆盖来源。

真实本机服务`sii-v9-selected-metric-preflight-20261030.service` CPU6/Nice15/单线程/3GiB/swap0，01:03:42–01:04:29自然exit0、CPU23.434s；中途14/45、29/45进度核实，全部失败计数0。原仿真同PID1684974/Invocation继续，OOM0；完整12唯一后继仍等原top3完成，不重复仿真。

证据：`docs/evidence/nonrl_v9_candidate_catalogue_20261029/SELECTED_METRIC_PREFLIGHT_REVIEW.json`、`SELECTED_METRIC_PREFLIGHT_execution.snapshot.json`；快照SHA256 `5695b5797170fe2c0f9f8792e3503446e12e72fb6b5daf1c2f1fdde87b525b7b`，绑定原registration SHA256 `bc2994e299dec10fba75a50c53f3bf4e5064a4c5d253fb91472b6b3ba1add933`。最新共同协议独立prefix另见`SELECTED_FIVE_PREFIX_20261030.json`，其快照可晚于45条预检。

ESN seed01前三仍失败，MLP正在共同检查，其余结果不能被已有五组合格替代。完整12候选公平接续、九模型锁定、最终未见108和完整汇总/媒体仍待。原office组合108的57未完成保留；Goal active。
