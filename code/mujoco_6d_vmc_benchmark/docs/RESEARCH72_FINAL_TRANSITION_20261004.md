# 已登记开发到完整最终矩阵的连续衔接

2026-10-04 06:09UTC核验：一次性服务`sii-r72-final-transition-v1`实际运行，PID2513613，
MemoryMax512MiB、Swap0、CPUQuota30%、单线程，状态`waiting_for_predecessors`。
这是持续的依赖等待进程，不是定时任务；不增加训练/搜索/物理回合，不改变研究协议。
**当前没有实际最终选择、模型锁或开封，最终评估目录尚未创建。**

## 启动条件与执行顺序

必须等待teacher_bank、初始学习开发、followup、经典确认、增强网络开发、context开发、
新读出refit开发、teacher采集、全部RL队列、RL共同边界监护关闭、最终入口已知身份演练全部完成。
读取原final batch中定义的进程保护名单，确认训练/开发进程已退出；保留历史停止进程。
每30秒核对原协议、全部修订、整个固定runtime源码和前置状态，不读取条件manifest。
当前五项仍在等待：additional_development_v1、context_gate_development_v1、
context_readout_refit_development_v1、rl_office_adaptation_v2、rl_final_boundary_v1。

前置闭合后顺序调用已有实现：

1. `research72_select_learning_20261003.py`：仅按公开开发、全部seed的已登记共同排序规则选择学习变体。
2. `research72_finalize_selection_20261003.py`：纳入全部经典、名义WBC和15个RL共同边界，共38个模型。
3. `research72_final_lock_20261003.py`：核验全部模型、完成证据、协议与源码后冻结。
4. `research72_final_batch_20261003.py`：持精确锁hash后才开封，运行全部38×24=912回合及其原有独立批审计。

没有新增选模规则、按成败提前结束、删除baseline、放宽gate或改actor输入。
每个实际子命令使用独立MemoryMax3GiB/Swap0/单线程服务；final batch原四个有租约仿真队列保持，
总仿真并发≤4。依赖等待本身不占仿真槽，不重启稳定开发作业。
截止仍是2026-10-06 11:30UTC；原48h开发截止也未延长。

缺少前置、出现终止失败/未完成、源码/协议变化、已有开封/最终输出或任一命令出错，
均以`failed_preserved`保留，不自动重跑或选择替代checkpoint。已有最终输出不能被重新启动覆盖。
已有最终服务受该连续程序管理，**后续检查进度前先读它的execution.json及实际PID，不能再手工重复派发最终矩阵。**

最终物理少于912回合时，衔接程序不会标记complete。即使912完成，完成范围也仅为原批次物理与批审计；
独立RL actor回放、完整统计、媒体、论文结果与整体目标仍须继续完成，不自动宣称投稿就绪。

## 已验证范围与时间余量

8项合成检查通过：真实进程名单解析、监护watching保持待完成、终止/缺前置拒绝、四阶段顺序和锁hash、
选择失败不继续、37模型拒绝、911回合拒绝、已有最终证据不重启。
合成回调只验证编排；实际选模/冻结/batch本体由已有各自测试和审计覆盖，不能把本轮测试当真实最终结果。
实际服务PID/启动参数/内存限制及等待状态已核对，steps为空，FINAL_UNSEAL_RECEIPT不存在。

05:59公开成本快照：全部120拟合完成；RL165754交互/191536更新，context28/168、增强网络19/168、refit4/144。
按既有假设，剩余开发22.818–23.894h、最终912物理22.824–23.942h，保留2h收尾后余量3.673–5.867h。
仍不包含所有冷加载/额外等待；P90最晚最终启动估计为10月5日09:33UTC，不能据正余量追加搜索。

## 可复查入口

服务器`arm1@192.168.31.70`，本轮根`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。

- 监督源码/测试：`final_transition_source_v1/tools/`，两个文件已逐内容/大小/模式核验，
  tar SHA `7cfeb2dee5e9eef397a5d07be925adbd74760812b86e76a520d19931be3cb953`。
- 实际选择/冻结/物理runtime来自完整3289文件已核验源码
  `/home/arm1/sii_shared/SII_compliance/source/a3b8c97fa027f4bf9bb55149e45cac4f664be562/code/mujoco_6d_vmc_benchmark/`，
  源码tar SHA `0fd1ecbcdcff983818ec7c2ddf29108699f356295189a980b1c50dddd011a781`。
  supervisor新源码单独记录hash，不冒称它已包含在该runtime commit中。
- 登记：`final_transition_v1/SPECIFICATION.json`，SHA `665883fca7dc5dab7b3d80d64fcccd9b6ec1028fa9dbc271bcb4950edd8a9fe5`，Git副本同字节。
- 实时监督状态：`final_transition_v1/execution.json`；完成后才会有各步骤日志与选择/模型锁。
- **计划的**最终输出：`final_evaluation_v1/`，目前未创建。
- 公开快照：`EXPOSURE_SNAPSHOT_20261004_0559.json`，SHA `215ce131fcac2465e4a842cd1cf1984b1af89be7065826ac22a561d4ab89ea12`。
- 容量预测：`BUDGET_FORECAST_20261004_0559.json`，SHA `fb3dabe4a21ee43d898778b35a21eda77b3ade9120a5f62d4e6bf817a0e66b51`，Git副本同字节。
