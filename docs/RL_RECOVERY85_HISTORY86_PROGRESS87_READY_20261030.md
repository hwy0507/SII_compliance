# 完整85历史回放重建完成；86继续，87入口仅准备

2026-10-30T12:43:34.289913+00:00，Goal active。完整第85轮三方法全部10,577,448条保留replay已与历史日志和journal逐条对齐；因果累计穿透历史保存为独立SSD sidecar。原86继续，保存steps `{'impedance': 3558941, 'admittance': 3561104, 'vmc': 3561241}`。没有87科学决定或训练；恢复等待器和决策/派发/后续入口已准备。reward稳定与loss健康尚未共同成立。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`；大checkpoint/replay/raw/runtime保留共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。本次实际ls-remote、fetch/read main `2679effbd6ae4f5bb2fb215d70692a7b1e4ce775`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未改其他主机非RL成果，无子agent。按仓库sii-research-sync流程，发布以SSD本包PUBLICATION.json的成功push及之后实际远端核验为准。

新增 `runs/recovery85_history_lineage_inventory_20261030_v1`：每方法80级registration父链哈希逐项一致；额外用原LAUNCH/EXECUTION绑定仅registration链容易漏掉的早期原始与恢复日志，再接batch32768和后续全部轮次。每路81个物理日志完整JSON解析、哈希和连续step检查，按下一日志首step−1截取保留前缀，末端绑定完整85checkpoint。原shutdown与partial75截点由既有manifest/audit约束。I/A/V分别排除但保留1484/889/744条checkpoint之后的尾部，合计3117条，不删除也不混入恢复replay。独立保存审查复算覆盖区间/计数/父链。

新增 `runs/recovery85_history_reconstruction_20261030_v1`：预先固定1800秒、CPU53、torch1/CUDA隐藏，按I/A/V顺序只读完整85checkpoint和全部81日志。实际主审988.237秒，0新physics、0network forward、0optimizer update、0replay/checkpoint写入。每个原journal完整hash，累计外穿透有限/非负/单调，每条保留replay索引写入恰一次，不把同一episode的交错global step当连续区间。

|方法|保留transition|完整+部分episode cohort|部分cohort|动作前已知穿透超限行|含动作前超限cohort|缺失next context行|
|---|---:|---:|---:|---:|---:|---:|
|impedance|3523948|2580|35|84355|67|0|
|admittance|3526250|2580|36|75273|60|0|
|vmc|3527250|2580|36|56945|45|0|

逐位检查全部current50：原raw48经原checkpoint observation_scale的float32变换、context和criticclock；replay原action×float32context精确等于journal执行动作；reward/done精确等于transition log。next raw48与clock精确，terminal next复制前观测但推进clock；next context由下一transition或terminal同context检查，缺失数如表，不用未检查部分冒充全量。原checkpoint SHA前后相同、所有输入hash复核。

因果历史定义沿用已审84源码：journal第0行interval=None对应0；之后本行interval是当前动作之前已经完成区间的累计峰值。next使用下一journal，只有done行才使用TERMINAL.interval；不把最终峰值回灌到前面动作。完整+部分cohort全部保留，没有给中断回合伪造terminal。本次是保存日志及源码的一致性重建，不是独立重算物理子步穿透，也不重建实际历史minibatch包含次数。

独立 `review_saved.py` 重新按已哈希transition日志建立交错索引、回读全部sidecar，逐cohort检查next→下一pre精确连接、单调性、起点0、末值、原0.2mm门的计数/首次越界、部分cohort和全索引恰一次。与先前独立84审计的全部90条derived arrays逐位配对，并复核标量；不是只抽查失败例。全部保存审查通过。`history_coverage.png`四栏实际查看：81日志累计覆盖、全部cohort末点峰值（部分回合仅为保留末点）、动作前已知超限比例、部分回合累积；全部外接触穿透峰值与中断记录均保留。此字段是external_penetration_peak_m，不是原79安全中止的global穿透字段，不能用本次最大约0.24mm否定当时97.689mm的global异常。

本结果补上此前“全历史replay能否重建”的数据可行性证据。它不证明增加历史输入会改善拟合，不证明当前输入无法拟合或局部梯度竞争是历史Adam漂移原因。原85旧VMC误差改善同时A退化的事实保持；没有修改当前86/actor canonical48/critic输入/reward/masks/physics/filter/gates。未来如开展历史特征对照，须独立登记有限预算、配对数据与状态约束，本次没有推广任何辅助权重。

大型sidecar为float64 shape(retained_steps,2)，两列preaction peak/next peak（米），独立于原replay；以下均实际hash和大小核验，不进入Git小证据包：

- impedance: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery85_history_reconstruction_20261030_v1/impedance_causal_history.npy`，56383296字节，SHA256 `96cb48ff045efb1a1a85e37fb8386e63f9a1fab812850e6721197ed3f08b4e8d`。
- admittance: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery85_history_reconstruction_20261030_v1/admittance_causal_history.npy`，56420128字节，SHA256 `483500200613fcebaa8644ad7396f79525a0804d69aadd03be73d8787d7df87d`。
- vmc: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery85_history_reconstruction_20261030_v1/vmc_causal_history.npy`，56436128字节，SHA256 `46658db0055c67e80d7b51dd645b678bfa74ac982905115e20f68bae9ad55fa4`。

`runtime/prepare_recovery87_20261030_v1`：科学trainer逐字同86、五metadata扩展可逆；每方法19协议+8边界拒绝、实际未完整86拒绝已保存，保留原82500负例和20261078 dummy seed。startup/archive/fullreview/health与完整loss87/86→87配对来源均准备，health两个真实依赖导入/hash/AST通过。恢复等待PID267147/start573644568，只在完整86后做恢复检查，不启动训练；本次保存实际恢复完成=False。

`runtime/recovery87_completion_preparation_20261030_v1`：decision87/launch87/deploy_loss87准备，原历史76—78/79—81/82—84和84→85固定输入检查函数逐字保留，DECISION86继承证据全部重hash。新强制完整86/replay/reward/loss/health/所有标签/两终端/实际图，以及准确87全learner/optimizer/replay/RNG/next65536恢复。另强制原固定2514、all5、84/85/86结果、保存复核和实际图，PLAN SHA `2f7c719eb64c36ce20b8135ca5d18748c0683bb4bf45d6e44a2f953ce44e5041` 不变。缺完整86、缺DECISION87、缺LAUNCH87、缺固定2514完整86结果四真实入口拒绝通过。无CONTINUATION_REASON/DECISION87/LAUNCH87，不自动87/88。

`runtime/recovery87_followups_20261030_v1`仅准备标签和终端helper：完整86 anchor2574→预期87共2604，数字AST只改轮次/计数；缺真实87LAUNCH在任何派发前拒绝，未部署。`runtime/recovery86_history_progress_20261030_v1/plot_fixed86.py`准备完整固定2514三checkpoint六栏图，真实未完整86拒绝已保存；完成后需运行并实际查看，再写原followup目录PLOT_INSPECTION.json。完整86后先审所有结果与实际图，才决定下一有限周期或登记修订。

原86三learner3407146/3407147/3407150（start573509827）、archive3407153（start573509828）、loss/标签/两终端/固定2514等待继续。新观察11样本/300.008秒，共29身份保持live或原成功终止，steps单调，保存逐行回读；有限观察自然完成，不是新长期supervisor。

冻结82进度(完成条件,在途条件,动作) `{'impedance': (27, 'active_long_train_0600', 1200), 'admittance': (23, 'active_long_train_0300', 900), 'vmc': (24, 'active_long_train_0337', 600)}`。原evaluator/rootreview/55→82比较/独立保存raw审计继续，需完整90、最终全learner/replay内存不变证明、实际图和比较。原55秒/dt5e−5/seed2026102638不改；这些是开发训练条件和单动作seed，不宣称泛化或最终ESN排名。

原85—87 PLAN SHA `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`、seed2026102858/5000bootstrap/nearzero1/5%/anchor55和原4小时截止不改，完整85/86在途/87未启动，原waiter446402和标量446428继续。原82—84 I近零不可判/A,V失败5%，原76—78/79—81以及partial75/原74—76不可判均保留，79安全中止不删除。Direct33数值阶段接受但冻结30 Task/Strict0/0，无Direct34；原中断28缺最终内存不变证明仍披露。指定ESN仍缺，不替换其他主机模型。

GPU原v7 supervisor97370及worker97399—97402继续，控制目标70%、用户阈值50%；493样本最低[76, 66, 66, 65]%、低于50次数[0, 0, 0, 0]，末值[80, 72, 94, 71]%。即使所有科学任务完成，也继续合成补载，不以占用冒充科学吞吐。历史v7预热0、v6的31/33/44低谷保留；采样间瞬时不能保证，该进程不是系统重启自启服务。原guard源码及启动/控制快照已另存本轮runtime的gpu_guard_v7.py.txt和GPU_GUARD_SOURCE.json，保存不启动第二组worker。

共享SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY85_HISTORY86_PROGRESS87_READY_20261030/SMALL_EVIDENCE.tar.gz`，128成员/2006524字节，SHA256 `1087dbae7093e04dddfbd2c1406db103c13b7016c8a04f93a65a7ad7f941f151`；逐tar成员原字节/AST检查，Git index/commit blobs另核。large sidecar/checkpoint/replay/raw仍原SSD，非HDD/arm1全备份。HDD LATEST原位254字节；归档运行日志为当时快照。

后续：先核原86、冻结82、87restore-only、固定2514、原85—87和guard身份/失败/成功标记，避免重复派发。完整86后审全部结果与固定旧输入三checkpoint对照，生成并实际查看对应图，再登记具体决定。全历史重建成功是可行性证据，不取代reward稳定与loss健康，也不是自动变更科学协议的理由。Goal active。
