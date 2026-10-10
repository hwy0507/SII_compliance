# 无示范 RL 的有限预算证据研究

用户2026-10-10授权继续仅用本机算力，检验能否得到可发表的RL训练/调参证据。
结论不预设为RL失败：若修正后学会，必须报告并纳入强baseline。
本研究不把单seed零成功、增加步数、训练loss稳定或合成控制检查通过当作“充分收敛”。

## 研究问题与证据层次

直接动作RL评估无teacher示范、仅靠交互与奖励学习的完整方案；RL调传统控制器参数另列，
具有控制器结构先验。公共规划、执行链与人工奖励仍是先验，因此不能标成“无任何先验”。
ESN/RNN/MLP的同teacher对照用于研究网络结构；纯RL对照不能单独完成结构因果归因。

最终希望检验的有限命题是：在本文任务、输入/执行约束、预先公开的算法集合与预算下，
系统调参后的无示范RL是否仍缺乏可靠策略。不能从有限实验推出“RL普遍不适合”。

## 已有依据与本轮四格实验

原direct108458/impedance104500 checkpoint各八development均Task/Strict 0/8，
只有一个训练seed；此前11k/55k也零成功。旧结果及中断事故保留，未称统计收敛。
训练轨迹离线审计发现，旧终奖无法区分Task通过但Strict失败与完全未完成；
八条旧训练轨迹原回报标准差约3e-15，任务/安全拆分后约9.09。
这只是候选学习信号的证据，不证明闭环性能改善，也不否认势函数能影响TD学习。

第一阶段为前瞻登记的2×2实验，全部从零开始，不加载旧离线四格或teacher的权重/replay：

| cell | 终奖/安全设计 | 信用分配 |
|---|---|---|
| n01_original | 原Strict终奖 | 1步 |
| n25_original | 原Strict终奖 | 25步 |
| n01_task_safety | 原Task终奖＋连续安全峰值成本 | 1步 |
| n25_task_safety | 原Task终奖＋连续安全峰值成本 | 25步 |

拆分奖励沿用已实现定义：Task终奖±20，外穿透超过原0.2mm后的峰值增量成本
`20*Δ[x/(1+x)]`，`x=max(0,pmax/0.0002-1)`；提前终止补记剩余安全成本。
Strict评测规则不变，奖励元数据不进入actor。多步回报具有未校正的off-policy偏差，
公开为信用分配消融，不称它与原单步SAC估计完全等价。

四格同seed `2026101011`、相同训练身份顺序、48D本体/7D动作、官方SimbaV2代码与
500k学习率日程、探索/UTD设置。各自只运行到11k/55k两个完整回合边界节点。
每节点跑同8个development身份；最多220000训练交互＋88000评估交互（64回合）。
实际完整回合步数单列，不将累计节点相加，不因失败剔除短回合。没有最终测试访问。
这是单算法/单seed机制诊断，不是已完成的超参数搜索或多算法比较。

## 先行控制检查与停止方式

同一官方agent、归一化、回放、梯度更新代码先做12000交互的合成连续动作奖励学习。
48D随机观测，7D目标只用于计算负均方误差奖励，不作为动作标签/梯度或actor输入。
预登记通过条件为固定128样本的最终动作MSE<0.05，且≤初始MSE的50%。
seed2026101021，评估seed2026101022；完整原始回放、优化日志、初末动作和checkpoint保留。
未通过则停止新机器人派发、诊断实现。通过只证明此简单问题上学习栈能改善，
不能替代同机器人简单任务的正控制，不能证明office接口完全正确或RL充分训练。

15:25 CST控制检查完成：12000交互、14002梯度更新，MSE从0.1599343866降至
0.0206257533（下降约87.1%），两个预登记阈值均通过。checkpoint/原始回放/初末动作
已保存；四格首组n01_original随即开始物理训练。15:27实查250交互、一个模拟器，
worker MemoryMax3221225472、MemorySwapMax0、实际约1.6GB，尚无完整机器人回合结果。
逐文件核对四组source内容相同，历史全部scripts字节未变；仅登记的12个tools有新增/叠加。

15:34 CST首个训练回合完整55秒/1375动作交互，公共filter重放误差0，Task/Strict均失败。
该回合属于5000步随机预热，不能算训练后策略成绩。累计2000交互时的只读快照
`FIRST_TRAINING_MONITOR.json`已核验：1完整预热回合、0已学习回合，第二回合继续运行，
新增分析物理步/梯度更新均0。首个完整开发评估节点尚未到达。

新trainer在回合边界检查`STOP_REQUESTED`标记与磁盘余量；协调器在每次新派发前也检查。
需要停机时创建该标记，等待当前回合及checkpoint保存。不向整个systemd unit广播
SIGUSR1，不重复此前误中断子仿真的操作。没有自动重试/覆盖失败目录。

## 运行与复现

15:23 CST启动一次性连续服务`sii-evidence-phase1-20261010.service`，不是定时任务。
实际主机airpig；单模拟器/单数值线程，worker MemoryMax3GiB、MemorySwapMax0；
协调器独立1GiB，入场MemAvailable至少5GiB，保留50GiB磁盘。无Spark训练/仿真/分析。
派发安全截止为注册时起48小时，这是agent选择的资源保护，不是用户指定时限或收敛规则。
完成四格后收口审计，不自动回到旧165k/220k/500k续步计划。

本地执行来源：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/evidence_phase1_20261010/`。
登记SHA256：`b7430fc8771c427facb9df03e6ac3079e45dab8d6a531c32b3c134db36480610`。
根REGISTRATION、各cell PROTOCOL/SOURCE_HASHES/PARAMETER_HASHES、实际命令/managed收据、
checkpoint hash、逐回合轨迹/审计/奖励与优化日志组成复现链。源来自历史冻结source，
只叠加登记列出的学习/奖励遥测/审计工具；公共物理源与模型保持原字节。
正式MJB SHA `d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`，
dt5e-5、55秒、32训练/8开发身份、Task/Strict、限幅/变化率/公共filter不变。

代码：`tools/rl_evidence_campaign_20261010.py`、`rl_optimizer_positive_control_20261010.py`；
trainer增加合作式停止与磁盘检查。12项单元回归通过（四格完整性3、回放4、奖励5）。
运行产物当前仅本地，服务器源码/登记小包核验后另记，不称原始新轨迹已全部共享。

已封存793文件/151667090字节的设置与完整合成控制包，manifest SHA
`e21d2b1a5d93e31b7dc7152c1cb1bd7fedec4134d5c4d43f29177888d4dfdd78`，正在传输至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/incoming/rl_evidence_phase1_setup_20261010/`。
当前是incoming暂存，未宣称共享核验完成。一次性本机服务`sii-evidence-archive-finish-20261010`
等待现有rsync精确PID身份结束，逐文件核验后才发布至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_evidence_phase1_setup_20261010/evidence/`。
状态入口为运行根`SETUP_ARCHIVE_TRANSFER.json`；发布失败会保留源和暂存、不覆盖同名run。
包内四组source字节相同只存一份，参数wrapper/协议逐cell保存，合成回放/checkpoint/日志完整。
新物理训练轨迹未包含在此设置包；旧closed110k传输不被重启。新归档收尾工具
`finish_evidence_archive_20261010.py`对独立run名称做路径约束，正常名称与四种越界输入检查通过。
开工实查main `b7844023bad24ecd6c4f3b9e4969a84351f97037`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取两日志及AGENTS，无分支合并。

## 尚未完成的论文证据

1. 同机器人简单任务正控制，与综合场景结果隔离登记。
2. 第二算法（如PPO）及带记忆RL的同接口实现/验证；不能用旧不匹配环境的PPO冒充。
3. 有限奖励/探索/学习率搜索后，至少5个独立训练seed；开发场景重复不是独立训练seed。
4. 有根据的预算扩展曲线，报告固定实际改善幅度与其置信区间；不把“不显著”当等效。
   五seed是起点，是否足以排除5个百分点改善取决于方差与场景相关性，不能预保证精度。
5. 模型/配置锁定后的共同独立测试，Task/Strict与接触覆盖、恢复/安全等指标完整报告。

以上尚未启动的部分不能写成已在后台运行。第一阶段结果将决定下一项最有信息增益的实验，
无论是成功、失败还是不确定，均保留公开。
