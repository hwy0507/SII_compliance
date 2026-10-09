# RL baseline本地补强（2026-10-09）

用户最新要求：充分使用本机，服务器另有用途，禁止占用服务器计算。
本轮不是恢复旧Spark队列，也不覆盖已完成15小时比较。开工核对main
`694a94d6907d6624e615b9a9cccfe2242502bd2e`与baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取日志；无分支合并。

## 已确认与修复

- 本机airpig：Core Ultra 9 275HX、约15GiB RAM、RTX 5080 Laptop 16GiB；
  GPU驱动580.178.04可用。新建独立`.venv-sii-local-rl`，不改系统驱动/显示。
- 历史MuJoCo 3.11.0二进制在本地转换到原正式dt=5e-5后，SHA仍为
  `d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`。
  原几何、规划器、任务/Strict gate、48维输入和执行器限制不变。
- 新本地运行入口采用显式`SII_LOCAL_RUNTIME`，修正硬编码Spark路径和CUDA库搜索路径；
  未设置变量的历史入口保持不变。官方SimbaV2固定commit
  `86899c277cdc697b2b02d827243de1ea93f20a1d`；适配器仅替换源码目录路径，保存前后hash。
- 参数动作采用已登记full-range映射：旧中心乘0.5–2不能覆盖全合法区间；
  新映射保持零动作对应中心，并覆盖上下界。原变化率/能量罐约束不变。
- 独立参数轨迹审计兼容新映射的字符串版本标签：标签精确比较，数值字段仍逐项重放；
  补齐适配器源码hash。不会把版本标签强行转数值，也不会跳过数值审计。

## 有限开发计划

`tools/local_rl_campaign_20261009.py`登记、预检、1375步真实物理smoke、断点接续、
每项最多11000交互及八个development条件检查。五族全部覆盖：RL调VMC/导纳/阻抗、
直接metric/office_task；另为直接office_task与调阻抗登记历史低熵对照，共七配置、
同seed2026100911，最多77000个新训练交互。学习率按500000总步计划，
11000只是诊断段，不是收敛预算；到段尾审查后才决定50k/100k/250k/500k延长和三seed复核。

参数三族保持metric reward，直接两族各用原登记reward；没有把调阻抗悄然改成task reward。
所有配置从零开始，无teacher/BC；短smoke的完整checkpoint接续到相同配置，不重置计数，
也不把随机预热成功当学习成功。新旧低熵对照共用此次完整参数范围，因此这组对照检验探索强度，
不单独识别旧映射与新映射的因果效应。

训练仅用原32训练身份，诊断仅用原8开发身份。旧final24已公开，不再作为新留出结果；
本入口不复制、不读取封存final，也没有自动最终评估分支。开发检查全用原55秒和正式物理步长，
这仍是开发数据，不因dt较细就变成未见场景泛化结论。

初次smoke使用一个本机模拟器与GPU学习器，数值线程1，整组进程MemoryMax=3GiB/禁swap。
完成smoke后由`local_rl_parallel_20261009.py`登记资源补充协议，改为两个本机lane，
每lane最多一个模拟器、3GiB、禁swap，最大合计6GiB；启动要求本机可用内存至少7GiB。
每lane串行训练及其八条件开发检查，跨配置并行；已有进程检查和锁防重复，不按GPU占用率认定进展。
48小时是agent设置的此次有限队列失效保护，不是用户给定时长，也不是训练充分性的标准。
没有定时任务。失败/中断目录保留，已有完整收据核hash后可跳过，失败必须用新attempt。

## 当前状态与位置

GPU梯度/归一化/checkpoint两种动作维度预检、完整参数范围数值测试、正式模型hash核验均通过。
12:20 CST首个1375步/55秒真实物理smoke完整结束，用时5分30秒；Task=true、Strict=false，
RMSE 28.4595mm、峰矩49.0145Nm、峰速0.364766m/s，外穿透0.273794mm，最差接触为柱子—link6。
放置XY误差11.8742mm。动作/共同filter一致性误差0；独立子步奖励重建误差0，replay观测/原始动作一致。
这是AR(1)随机预热、梯度更新0，不能当成训练后RL提升或成功率；失败保留。
checkpoint包含1375条replay、优化器/归一化/RNG/条件顺序和hash。

12:21 CST两路本地长进程已启动：直接office_task从smoke checkpoint接续，调阻抗metric从零开始；
随后依照登记队列跑其余五配置及各八开发条件。两学习器GPU各约584MiB，
初始可用RAM约8.84GiB；每lane独立3GiB/禁swap/两个CPU亲和核，数值线程1。
资源补充SHA `267d16b273044cdc64349f15afa21f30f747111807e21dcef9419399296424ad`。
`parallel.execution.json`是当前队列状态；旧`execution.json`仅是已经完成的smoke阶段状态。
随后两路各再完成一个完整回合：直接动作接续回合Task=true/Strict=false（穿透0.342624mm），
调阻抗首回合Task=false/Strict=false（停在carry，穿透0.176869mm、放置XY误差87.338mm）。
都仍处于5000步随机预热；不把不同训练身份的单回合指标当方法排名。
调阻抗1375次参数重放及13750行伺服记录独立审计通过：能量/参数更新数值误差0，
最大等效关节速度命令0.702001rad/s、加速度8.0rad/s²、力矩变化率比约1.0，未放宽限制。
该追加审计小文件入Git；对应新原始回合仍在本地训练目录，未包含在下面较早的stage1大包。
初版`campaign_v1`仅登记，未派发物理回合；补齐参数轨迹审计后建立`campaign_v2`。

实际本地工作根：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/`。
其中`runtime/history/source_v9`和`parameter_v2`来自历史只读下载；
`campaign_v2/source`为本轮冻结执行源，`parameter_fullrange`为本轮适配器，
PROTOCOL/SOURCE_HASHES/PARAMETER_HASHES/RUNTIME_HASHES记录实际路径与内容。
协议SHA `ef3ec8c85bd06ccb2a915d861116286e29b78a13ec1df4da02f0c0a5825bd2bb`。

服务器旧数据来源（仅文件读取/传输）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`。
本轮已完成证据已归档并核对大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage1/stage1_verified_snapshot.tar.gz`，
190281186字节，SHA256 `ffdad404d6713fceda5e9824b2969b160379f1adecfc3a6dfb3af8b43bdeec12`。
包内包含`source/`、`parameter_fullrange/`、`continuation_source_v1/`、完整首回合/其checkpoint、
GPU预检和物理奖励审计、配置及全部输入hash。实际执行仍在airpig；服务器仅存文件。
它是已完成阶段快照，不包含正在变化的两路训练目录；后续产物待完成边界另行归档。
可直接审阅的小型证据位于Git的`outputs/baseline_local_rl_20261009/evidence_stage1/`。

未完成：本轮真实梯度后的闭环诊断、合理训练充分性证据、多seed、开发选模、新留出统一比较。
旧经典/RL零成功结论不因迁移/数值测试通过而改写，也不能据此声明ESN全面领先。
