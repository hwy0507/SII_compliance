# 先完成baseline，再扩充teacher数据与统一重训（15小时）

用户2026-10-12晚授权；保守起点21:28 CST，派发截止2026-10-13 **12:28 CST**。
15小时包含当前baseline等待、审计、采集、训练和比较，不能从采集开始重新计时。
一次性systemd任务，不创建定时任务，不使用服务器训练/仿真。

## 当前事实与数据基数

- 21:45实际服务 `sii-teacher-student-15h-20261012-v3.service` active，PID1676275；
  `execution.json`为`waiting_for_baseline`，新仿真/新拟合均0。旧配对服务PID1649757未重启。
- 已核对新协调器只持有自己的`coordinator.lock`；全局`.local-rl-compute.lock`仍由原baseline持有。
  不再出现父进程拿全局锁、等待再次抢同一锁的子进程这种死锁。
- 启动时baseline已复算123/168行，仍在顺序推进。必须全部168行、64新参考回合完成，
  独立完整性审计passed且报告落盘后，才允许teacher搜索或数据训练。
- 现有refined数据实际是**20训练身份×1375=27500帧，5验证身份×1375=6875帧**；
  不是32个合格训练身份。32是上游训练候选条件数。此前MLP部分选中旧版数据，
  本轮新模型将统一同一数据/身份split，不沿用这种数据版本差异。

## 有限执行顺序

1. 等baseline完整21配置×8开发条件矩阵，独立核对原始子步、动作链、权重、条件和汇总。
   先发布baseline表和审计，再进入数据工作。RL/经典失败全部保留；不追加baseline训练预算。
2. 在冻结物理环境及原扰动分布内生成新的训练/验证身份，不读保留场景、不改几何、gate、
   动作限制或actor输入。teacher中心是已有增强VMC teacher09，新增5个七维log-LHS候选，
   共6候选×同2训练身份=12搜索回合。这是有限首批筛选，不能称穷尽七维参数空间。
3. 只有两身份均完整Task/Strict通过的候选进入RMSE/峰矩Pareto集合；按预登记RMSE、
   峰矩、名字选择一个teacher。峰速保留原安全约束并报告，不奖励速度尖峰。
   若无合格候选，保留失败并用历史中心采集，不称新搜索成功。
4. 新采集始终固定这一个teacher。最多80完整回合（64train＋16validation），按
   每1验证＋4训练顺序交错；**07:58 CST停止新采集派发**，完成在途回合后留4.5小时给学习和比较。
   数量是上限，按当前单路吞吐预计只能新增数十条，不能把生成配置数写成已采示范数。
5. 导出仅原Task/Strict/55s全部通过的实际轨迹，原始请求、clipped、filtered和执行量分开保存，
   teacher/filter逐帧重放；失败及未派发身份写拒绝账本。至少新增8train/2validation才能拟合。
   追加旧版refined的25条真实示范，身份不重叠、不重标旧数据。
   如果新teacher不同于历史中心，明确这是两teacher示范混合，不是仅增加样本量的单因素消融；
   不将teacher身份送入actor。搜索回合不作为学生标签，不堆叠同身份多个teacher的冲突动作。
6. 同一数据重训128宽度纯ESN、普通RNN/MLP、特征匹配RNN/MLP。三seed固定为
   2026101201/02/03；ESN每seed12个储备池/读出候选；神经网络每seed3个学习率×4000更新，
   以三seed平均整身份验证动作MSE选学习率。matched网络继承同数据ESN/memoryless父模型，
   必须计算父模型训练成本，不能称同计算预算。所有离线候选保留。
7. 先验锁定首seed2026101201的五模型，在同baseline的8个开发身份各运行55s、dt=5e-5，
   共40新回合。其余两seed仅完成离线对比；不事后挑最好seed，也不称三seed闭环泛化证明。
   逐回合复算物理子步指标/接触覆盖/冲量/恢复，动作和状态重放，最后独立检查40行及聚合。
   12:28后停止新派发，完成在途回合和审计；不自动延长窗口，不隐去未完成网格。

## 公平性和参数解释

本轮检验“较少可训练参数是否能达到相当控制效果”，不预设ESN胜出。
ESN的固定储备池、输入矩阵和上下文投影也占内存与计算；结果同时列可训练参数和存储浮点
标量（包含固定矩阵/归一化，不能混称全部都是网络参数）。128宽度不等于相同参数量。
matched保留既有特征/时间尺度和读出形式以检验循环权重训练的影响；ordinary为普通网络对照。
已有神经拟合损失含固定0.25动作差分项，ESN本批为point读出；不能把此批解释成完全相同损失的
单因素结构消融。全部真实监督数据、公共48D/7D接口、允许本体字段和部署filter一致。

教师仍是**增强VMC teacher（含已有本体恢复机制）**；不把它改名为纯传统VMC。
学生部署无teacher、无混合控制器，不加入接触真值、事件时刻、任务阶段、球状态、视觉或距离。
示范量增加和开发矩阵改善都不能替代独立最终泛化；保留条件本轮不解封。

## 执行、恢复与归档

- 本机单模拟器、每worker1线程、MemoryMax3GiB、Swap0；协调器MemoryMax1GiB、无自动重启。
  开始worker需MemAvailable≥4GiB、磁盘余量>35GiB；每worker硬超时30分钟，失败传递非零退出。
- 仿真解释器：`/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python`。
  拟合解释器：`/home/airpig/桌面/hwy/compliance_control/.venv-rl/bin/python`，Torch2.11.0、
  NumPy2.4.6、MuJoCo3.14.0，仅离线训练；物理仍使用原冻结运行时。两环境预检导入通过。
- v1准备时缺少本地历史conditions缓存；改用hash核对过的仓库evidence。v2预检发现仿真环境
  无torch；v3明确分离拟合解释器。v1/v2原目录保留、未执行仿真/拟合，无实验结果覆盖。
- 恢复会核对已完成任务命令和产物hash并跳过；遇半写/运行中收据不重复启动，保留并报错。
  `STOP_REQUESTED`在回合边界生效。不要仅看到systemd active就称已训练。
- 源码和初始数据包已经核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_student_setup_20261012_v3/evidence/`。
  源码在`source/tools/teacher_student_15h_20261012.py`；603文件、24327306字节，
  manifest SHA256 `6b95404ace71424690d410c73cab63e17df518c4ee7d66b7d4f3c3b404cf7748`。
  该包**只有配置/源码/历史数据，不含尚未产生的新结果**。
- 本地执行根：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/teacher_student_15h_20261012_v3/`。
  `REGISTRATION.json` SHA256 `cf96a169faa9a57b73cd2a5a52ce8620f56eabce7e796545b0ea65e2db28be13`。
- 后续在baseline/data/final边界独立打包，服务器只做文件传输/hash核验。原始baseline168轨迹
  完成后归档；新搜索/采集/评估轨迹在最终归档，失败同样保留。每阶段`ARCHIVE_STATUS.json`
  明确verified或pending，未核验绝不宣称已共享。
- 每阶段生成`TEACHER_STUDENT_15H_LIVE_20261012.md`并更新UPDATE_LOG、联合进度和周报；
  仅在本任务文件无并行修改、main安全前进时commit/push并核对远端。网络/并行冲突写pending，
  不force push、不覆盖其他agent文件、不因发布失败丢弃计算结果。

验证：16项协调器/配对审计回归通过；冻结拟合模块导入通过；真实等待状态/零派发/全局锁
归属检查通过。当前完成的是基础设施和登记，新增示范、重训、40闭环结果均尚未完成。
