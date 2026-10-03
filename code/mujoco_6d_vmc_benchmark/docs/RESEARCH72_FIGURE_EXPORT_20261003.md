# 最终审计报告的图表导出准备

2026-10-03 23:30 UTC。当前仅合成版式验证，**不是研究结果**，没有读取封存条件。

`tools/plot_research72_comparison_20261003.py` 接收最终汇总器已审计的 `REPORT.json`，
不选择权重、不重新计算统计量，不读取场景 manifest。固定顺序显示全部16方法族；
任务/严格成功图保留计划分母、缺失上下界、各完整seed和报告中已有的成对区间。
接触图覆盖人手、推杆、桌角、球和柱子，展示已有的P95和力模积分成对差值。
双方均严格成功、完整且实际接触的条件子集单独注明；没有有效配对显示NA，不能据此称总体或因果优势。
点区间用菱形，不把三个seed的探索性bootstrap区间解释为确定性保证。

每组输出SVG/PNG和源/输入/输出hash。正式调用不加 `--synthetic-demo`；合成输入不能伪装正式。
正式输入须含模型锁、审计证据及未读取封存manifest声明；仍由上游审计器负责逐证据核验。
图只辅助完整矩阵；失败、全部接触暴露及恢复删失仍须同时报告，不能只发布成功子集图。

本机单线程/MemoryMax3GiB完成三项测试：合成身份拒绝、全部方法/缺失保留、六文件及无接触导出。
使用38模型×6虚构条件，其中3条缺失、短失败和无接触，正负差值均覆盖；3测试通过。
23:29UTC三张PNG已目视核对，修复图例和缩短版底部注释遮挡；没有新仿真或拟合。
NumPy2.4.6/Matplotlib3.11.1，不改变Spark物理运行时。

已核验服务器归档（10文件，2,056,068字节）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/figure_engineering_archive_v4/evidence/`。
其中含实际源码、测试、合成输入、六张图和图表manifest；相邻 `ARCHIVE_VERIFICATION.json` 保留本地执行来源。
历史v2归档不覆盖，v3仅本地布局尝试未发布为归档。

| 证据 | SHA256 |
|---|---|
| 图表源 | `068b6390021df549102fe0ff0bf29c8578c131178ac0bf35bf8c0ed41ce6c138` |
| 测试源 | `c915fa43098ada7e2e9829bf3cfa055b1eae5fa1c093119c21c10f28328fa885` |
| 合成输入 | `c226cce82a72576b6163c5cbd29eafa0106b2753179fe02dc2e33cecf01b8894` |
| 图表manifest | `c7aba824acb76f603f37ac4cdd317b4c7480c0d6ae3bccc8d764eece91c512a9` |
| 归档manifest | `7fce50cef55ca5a05c2f1c8132746af0726a996dcbdde54ffe999e6f9613754f` |
| 传输tar | `f4ee52a04dbeb355b4df1bdd606bea4f0767f9a8215fdc628ff5ab377f4bf479` |

Git保存同字节 `docs/evidence/research72_20261003/FIGURE_EXPORT_SYNTHETIC_V4.json`。
真正最终报告、图表和留出结果尚未产生；不把工程验证算成ESN性能进展。
