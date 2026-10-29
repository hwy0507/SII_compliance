# 当前三特化108六指标报告入口（2026-10-30）

真实最终评测仍未开始，本文件不是结果报告。公平75fit正在推进；本轮实际11项完整，第二组RNN seed02已到19392update。三原服务仍active，无重复运行。此前Goal轮为verified wait加前9记录审查，本轮补全最终交付入口，不改变训练/物理/选模或gate。

## 交付入口

新增code/mujoco_6d_vmc_benchmark/experiments/report_contact_yield_final108_20261030.py，只读取固定新运行outputs/contact_yield_isolated_unseen108_20261030_v1/FINAL_REVIEW.json。必须完整108且status=verified_complete_isolated_unseen_matrix；同时要求final108等待器已完成且其review_sha256匹配当前独立报告；重新核新模型adapter来源、注册/执行/reviewer hash、108身份顺序/精确replay和原aggregate/grouped汇总。拒绝未完成或被修改的报告，不读取历史108来填充当前结果。

待原final108等待器实际完成后，使用登记MuJoCo解释器在benchmark执行：

```bash
MPLCONFIGDIR=/tmp/sii-final-report-mpl /home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python experiments/report_contact_yield_final108_20261030.py --output outputs/contact_yield_final_delivery_20261030_v1
```

使用本任务既有登记解释器，无需新建环境。该交付目录必须不存在。仅生成报告，无训练/物理/选模；最终媒体仍另生成并核验，不能仅据报告入口准备完毕标Goal complete。

输出四CSV（108回合、九模型、三family、family×scene）、六指标PNG/PDF、REPORT.md及原始报告/执行/注册和产物hash收据。各family汇总36回合、三个seed，明确是pooling，不冒称mean±seed SD；九模型表保留各seed的Task/Strict/BOTH计数。

六指标保持Task、Strict、双成功条件SPT、全部回合峰矩均值、人舒适度NA和机器合规率。T_ref沿用原独立review的全局双成功最短时间；无双成功时T_ref/SPT皆NA，失败保留分母。人体力通道未测，不能把接触力矩代理改名为真实舒适度；代理接触时长与时间加权比例在独立表列出，无接触NA。原terminal hold仍13采样/0.48s，非逐子步终态证明。完整失败原因及horizon审计留原JSON，不因CSV只导标量而丢失。

## 控制与当前限制

新增check_contact_yield_final_report_20261030.py：纯合成108输入验证部分成功与全失败；缺少失败行、重复行、伪T_ref、改SPT、捏造舒适度、actor重放错误、重放身份错误、最终等待器未完成、review hash漂移均拒绝；全失败108仍全部导出且SPT/人体舒适为NA；重复导出拒绝且不改原文件。见CONTACT_YIELD_FINAL_REPORT_CONTROLS_20261030.json。两新源AST与diff检查通过。

排版只在/tmp合成fixture上检查，六panel/坐标/NA/图例目视无裁切。这张合成检查图不是实验结果，未放入仓库，也不会用作最终报告。控制没有访问实际最终条件/轨迹；不能把控制通过称为当前108通过。当前尚未生成真实六指标表或图。

本轮main84c24f9b1a83adad0bbab2cfaffd1dfc668dbbdf、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d已宿主fetch/read。新增文件仅experiments，未修改已登记scripts/tools/运行中协调器，等待链源哈希仍须保持。Goal active；新raw仅本地，未绕过先前自动审查的服务器导出拒绝，无服务器计算/RL/删除。
