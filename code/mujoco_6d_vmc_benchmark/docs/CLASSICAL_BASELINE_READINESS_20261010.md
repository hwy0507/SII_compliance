# 经典 baseline：基础验收、停滞归因与补强

用户2026-10-10要求优先把VMC、导纳、阻抗做扎实。新计算仅在airpig本机；Spark只归档。

最新调度：18:00 CST在第12条完整回合及审计结束后，原串行协调器/监视器自然退出，
同一run交接至本机两路；详见文末“本机两路交接”。原12条结果完整保留，不新增候选预算。

用户再次澄清：验收要求是实现正确、公平且有依据的调参，不要求baseline必须解卡。
正常运行后的卡住是有效失败结果，不为强行过关添加恢复机制或无限追加预算。
开工已查询/fetch main `c705c652181dc255b5ac03a5942718f9c8070677` 与 baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取两日志/AGENTS/sii-research-sync。

## 已完成的交接与检查

- RL四格实验通过STOP_REQUESTED在完整第4回合结束后暂停：5500交互/1002梯度更新，
  coordinator `stopped_at_safe_boundary`，trainer `complete`。75个checkpoint文件hash及
  office_runner的episode_boundary/step重新核验通过；未发送进程组终止信号。
- RL设置包已核验存于
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_evidence_phase1_setup_20261010/evidence/`，
  793文件/151667090字节，manifest `e21d2b1a5d93e31b7dc7152c1cb1bd7fedec4134d5c4d43f29177888d4dfdd78`。
  新5500训练轨迹不包含在这个此前已封存的设置包中。
- VMC实际动作单位、阻抗参考投影的切向可动性、等效命令幅值/加速度与力矩幅值/变化率
  回归通过。原修复控制律尚未发现新的已证实代码错误；不会为制造修改而换控制律。

## 为什么补基础正控制

之前六条“关闭主动推力”验收仍有静态障碍，因此未完成放置不能排除基础搬运缺陷。
新的clear诊断保留机器人、负载、桌面/目标支撑面、初态、规划路线、目标姿态、任务门槛、
传感输入、执行器限制和dt=5e-5。先在原模型上规划，再仅关闭登记非支撑障碍的碰撞mask；
主动驱动关闭。球与桌面/地面的两个显式接触pair保留，不涉及机器人/负载。全部55秒。

这是单独保存二进制/hash的诊断环境，**不替换冻结综合场景，不计入最终比较成功率**。
七项完整性/选模/归档回归确认：frozen/events_off模型字节不变；clear/edge_only/active_only只修改
登记mask且恢复后整个二进制相同；机器人、物块与放置支撑未改。

入口 `tools/classical_acceptance_20261010.py` 使用独立源码快照、与RL共用本地仿真锁、
单模拟器/单线程/每worker3GiB/禁swap、有限回合清单、回合边界停止和不可覆盖失败收据。
初次v1在仿真前因过严的npair==0检查退出；保留失败。核实两个显式pair后创建独立v2，
并未更改历史运行或绕过机器人接触检查。

本机工作集（当前仅本地，待完整归档）：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/classical_local_acceptance_20261010_v2/`。
登记SHA `288c04ddca769670785c45083876fa420831e550e20f27f62de91e39068804b9`。

16:26 CST已核验发布设置/源码叠加/小型审计包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_local_setup_20261010/evidence/`。
其中`tools/`为本轮入口，`registration/`为三个不可变登记，`clear_audits/`为基础验收与控制器审计。
26文件/454548字节，manifest SHA `64d881b45f24b2b3023524ecc67f07a18822c0a303ddbacd106f8b1def695930`。
16:52 CST已核验完整10条诊断的小型结果/控制器审计/最新归档修复源码：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_diagnostics_close_20261010/evidence/`，
16文件/136639字节，manifest SHA `e6f1fa8fc85c222b51d7850fe5066b3e5cf05d7ea62900fa99d4981c2e20823e`。
其中`classical_diagnostics_verified_20261010.json`是10条核验后的诊断矩阵；不包含10条全部原始子步轨迹。
复现仍需历史`baseline_repair_15h_20261008/source_v9/`、`parameter_v2/`及各execution中
登记的冻结MJB/Menagerie/本机MuJoCo3.11.0运行时；小包不包含这些大型依赖。
完整基础诊断/源码/失败包1445文件/749877105字节正在传输，清单SHA
`1e9f6ad501ddf8b915c79f73630efc6bae3016f52fde5c82aba5e55492e345d7`；
目标`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/incoming/classical_readiness_20261010/`
尚未核验发布。一次性收尾服务等待原rsync后
逐文件核验，不重启传输；本地收据`outputs/classical_readiness_archive_transfer_20261010.json`。
收尾v1/v2在验证相对源路径时退出，原rsync与仿真均未中断：systemd默认cwd不同，且rsync
运行中会chdir进入源目录。现修正为核验发送进程cwd、原参数与预期归档目录，保留精确进程
身份/目的地址/逐文件hash检查；路径回归通过，16:33 v3实际waiting_for_transfer。

**四条clear诊断已全部完成，Task/Strict均通过。**每条均55秒、110万物理子步。

|诊断控制器|Task/Strict|放置XY误差 mm|RMSE mm|峰值力矩 Nm|峰值速度 m/s|
|---|---|---:|---:|---:|---:|
|名义共享WBC|通过/通过|6.826|21.955|42.154|0.061602|
|VMC|通过/通过|9.875|23.449|44.187|0.061602|
|导纳|通过/通过|12.342|31.165|49.012|0.066819|
|阻抗|通过/通过|20.695|19.486|42.545|0.080786|

外部最大穿透分别0.001606/0.001606/0.001682/0.002230mm。无障碍诊断不用于证明
复杂接触成功或某方法柔顺性更好。阻抗放置误差接近25mm边界，仍需后续扰动验证。
VMC完整1375步虚拟状态/动作/参数/能量独立重放误差0；导纳最大约6.95e-15。
三类参数shield重放通过，阻抗13750条伺服命令/加速度/弹簧误差/力矩变化率审计通过。

16:28 CST主动扰动诊断三类均已完成，全部Task/Strict通过：VMC的RMSE24.938mm、
峰矩44.188Nm、峰速0.369934m/s、外穿透0.155416mm；导纳28.444mm、51.158Nm、
0.364619m/s、0.148550mm；阻抗19.756mm、42.545Nm、0.366901m/s、0.140407mm，
阻抗放置XY误差20.713mm。VMC球/手/棍均有实际机器人接触，并非仅打开驱动而完全错过。
Task/Strict通过不等于峰接触力低：例如此VMC回合球接触峰约6400N，属于当前仿真接触模型，
不能据它证明硬件安全或所有柔顺指标良好。VMC/导纳独立状态/动作重放通过，阻抗独立
shield/伺服审计通过；三条edge_only归因随后均已完成。

接触覆盖另计，不能把“主动驱动已开启”当作全部实际接触：

|active_only控制器|球接触 s|人手接触 s|棍接触 s|
|---|---:|---:|---:|
|VMC|0.00195|4.24200|5.72020|
|导纳|0.00395|4.52215|0.36725|
|阻抗|0.00260|4.56890|0|

阻抗此回合没有碰棍，**不能据其Task/Strict通过声称棍推恢复验收通过**。VMC/导纳接触
时长也不匹配，三者不能仅按接触冲量排名。冻结综合场景仍使用同一时序；不为补接触而改正式gate。
edge_only三类均完整55秒失败、停carry，VMC/导纳/阻抗放置XY误差分别
79.198/44.146/85.735mm，桌沿穿透0.070541/0.082683/0.091266mm，均非超安全阈值早停。
这与clear/active_only成功形成支持桌沿阻塞机理的对照。

|固定所选控制器|clear基础放置|active_only放置|edge_only放置|
|---|---|---|---|
|VMC|Task/Strict通过|Task/Strict通过，球手棍实际接触|失败，carry|
|导纳|Task/Strict通过|Task/Strict通过，球手棍实际接触|失败，carry|
|阻抗|Task/Strict通过|Task/Strict通过，但未接触棍|失败，carry|

`report_classical_diagnostics_20261010.py`对10条完整诊断重新核验登记、模型/轨迹hash、
1375×48观察/1375×7动作、每条55秒、实际路线精确一致、各诊断组内模型完全相同；通过。
输出 `outputs/classical_diagnostics_verified_20261010.json`，零新增物理步、零final读取。
只证明这一个开发锚点上的诊断差异，不能外推为跨条件成功率。未以这些修改后的诊断环境
替换最终综合环境，也未将Task/Strict成功当作所有接触指标都优秀。

## 旧开发失败的具体证据

只读取既有development_000，不用final结果调参。最终选中参数对应历史确认候选vmc_09、
admittance_17、impedance_00；完整55秒末尾10个1Hz几何重建快照中，分别有10/8/10帧
存在物块—未知桌沿接触。另保留admittance_08候选的10/10接触诊断，不混作所选参数。
末尾名义平移命令约30–60mm/s，而实测运动接近静止；夹爪仍夹住物块，Task停carry。
这支持“桌沿接触停滞”，但单凭重建几何不证明唯一原因。

`diagnose_classical_stall_20261010.py`仅对存档qpos/qvel进行mj_forward，零新物理步。
接触计数按每帧去重并用geom ID区分未命名碰撞体；不把重建接触几何当原物理子步力/冲量。
旧分析初稿保留，v2修正了“接触点数”与“接触快照数”的计数语义。

## 后续验收顺序

1. 已完成四类clear正控制及独立重放。
2. 已完成六条接触归因：三经典各跑active_only（原主动球/手/棍，关闭非支撑静态障碍）
   和edge_only（仅保留未知桌沿，关闭主动驱动）。规划路线和门槛仍同原场景。
   登记SHA `39b2a64bddf915285f67d10fbe11522363502274ed926f460453115f9b31a079`，
   本地 `outputs/classical_contact_attribution_20261010_v2/`。未启动的v1因补充物理早停计数和
   独立审计入口被v2替代，保存为superseded_before_dispatch，不冒充运行失败。
3. 已登记原冻结综合场景内的边界搜索：每类原所选中心＋水平刚度、垂向刚度/比例、平移
   阻尼三个坐标的2³上下界组合，9候选×同2开发条件×3方法=54回合；按Strict/Task、完整
   时长、真实物块目标距离、穿透、RMSE、峰矩选每类2个，补剩余6条件，共最多90回合。
   三类预算一致，参数在原合法范围，未更改控制律。不是扩大网络输入或加入场景专用动作。
   `outputs/classical_boundary_search_20261010_v1/REGISTRATION.json` SHA
   `44e1094a88d86130aa7ec2d22dea99acd63d6fab1ad3e6ec6a584f6ccfe7035e`。
   16:14 CST一次性连续服务`sii-classical-strengthen-20261010-v1`启动，先接触归因再搜索；
   每回合保存原始轨迹/源/config/hash并独立重放。不是定时任务；完成有限预算后停止审阅，
   不自动解封final或无限追加。物理早停作为失败计入；基础设施/审计异常保留并停机排查。
   归因队列已complete；CHAIN_EXECUTION已进入frozen_world_parameter_search，首条
   vmc_boundary_00在完整原综合环境运行。最终统一表仍需以后全部方法同一冻结设置重评，
   不把本机新开发成绩直接拼接成与旧Spark最终成绩同批次的比较。
   首条原中心VMC已完整55秒复现carry失败，独立审计通过；boundary_01已实际运行，
   并非只写了协议而未启动。仍需完成全部筛选及每类前二的八条件确认。
4. 完成登记预算后审阅参数敏感性、前二候选的八条件结果与实现审计；正常卡住计作失败，
   不以必须解卡为目标追加控制机制。若发现新的可复现实现错误，再针对错误修正并另记版本；
   原传统方法与enhanced teacher仍分列，不把增强恢复机制冒称原始线性导纳/阻抗。
5. 锁定配置后在冻结综合场景统一评估；所有失败保留，未解封新最终条件。

目前完成的是基础搬运验收和独立控制器审计，**扩展调参充分性审阅与最终重评仍未完成**。
论文不能把它写成“所有传统控制器已经充分调参且原理上不适合”。

## 17:11 CST 持续监视接续

17:12复查：累计4/90，第五条boundary_04已运行；监视器自动核验新增回合，两个服务active，
无ALERT。下方前三条指标及服务器START_SNAPSHOT保留其原检查时点，不改成后续结果。

原仿真服务保持运行，完成3/90条参数试验，均为VMC在development_000的不同参数，
Task/Strict均失败、完整55秒；这不是选定VMC跨条件0/3的成功率。
边界00/01/02的RMSE分别26.508/26.368/27.961mm，峰矩39.074/39.761/38.071Nm，
峰速0.369934/0.373336/0.381502m/s；物块放置XY误差82.695/84.195/108.170mm。
前3条外部模型hash一致，实际条件/seed/物理步长/路线、配置、轨迹与独立审计hash通过复核。
调参确实改变输出，但此单条件局部结果不足以宣布某候选最佳。当前boundary_03继续运行。

新增只读监视器`tools/monitor_classical_search_20261010.py`与4项证据完整性回归：
轨迹篡改/缺失状态审计必须拒绝，完整卡住/物理提前失败必须保留。真实前三条回放收据核验通过，
零新增物理步。程序不导入MuJoCo，不改变仿真来源快照、运行协议或条件，不重复派发。
终局重新核验全部已完成轨迹；选模时重算登记排序、确认条件和参数，防止悄悄替换候选。
未执行候选显式evaluated=0，不能当作失败或最终比较；开发候选表也不冒充最终留出成绩。

17:10启动一次性连续服务`sii-classical-monitor-20261010-v1`，每60秒检查，结束或异常退出。
原仿真每worker3GiB/禁swap，监视器512MiB/禁swap（实测约11MiB），无新增仿真并发或定时任务。
输出根`outputs/classical_boundary_monitor_20261010_v1/`：`LATEST.json`是进度，
`CLOSE.json`是停止时快照，`ALERT.json`是监视异常；不会因算法失败自动重启。
原RL保持5500步安全暂停。按前三条耗时估计剩余约8.8小时，仅作吞吐估计，不延长90回合预算。

已核验源码/登记/启动快照小包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_monitor_setup_20261010/evidence/`。
5文件/151713字节，manifest SHA `936c58e6febbc85024a1024409a54eca0006311b7238a432554d8090f2c2e57d`。
其中`START_SNAPSHOT.json`仅为启动时快照，不是服务器实时监视结果；实时结果仍在airpig本地，
未声称新90回合完整原始轨迹已归档。服务器本轮只读与传输/核验，没有启动计算任务。

## 本机两路交接（2026-10-10 18:00 CST）

18:07实测首批两回合均完成55秒且shield/动态重放通过，耗时362.176/361.000秒。
约6分钟完成2条，相比此前约6分钟1条吞吐改善；不同参数并非配对测速，不能断言精确加速比。
累计14/90（VMC9、导纳5），全14条条件/seed/模型/配置/轨迹/审计证据再核验通过，
下两条boundary_05/06自动派发，预计余下约3.8小时。新增两条仍Task/Strict失败并保留，
没有把吞吐改善说成算法成功。新核验快照仅本地`outputs/classical_parallel_first_pair_verified_20261010/`，
下面服务器设置包是原12条启动时点，不含后续新轨迹。

用户指出算力利用不足。实查24个逻辑核，但原worker只占满1核，约0.7–0.9GiB；
可用内存约7GiB、内存PSI近零，串行调度过于保守。经典MuJoCo worker主要受CPU限制，
本次通过并行独立回合提速，不迁移到GPU物理引擎或服务器。

17:55左右登记STOP_REQUESTED，原admittance_boundary_02完整55秒及独立审计后自然退出；
没有发终止信号。旧execution、CHAIN_EXECUTION和停止请求保留在run的`serial_handoff_v1/`。
12条完成结果（VMC9、导纳3）与旧收据逐项相同。原REGISTRATION SHA仍为
`44e1094a88d86130aa7ec2d22dea99acd63d6fab1ad3e6ec6a584f6ccfe7035e`。

18:00:58启动`sii-classical-parallel-20261010-v2.service`，新协调器
`tools/parallel_classical_search_20261010.py`只派发原冻结worker，持有原全局仿真锁。
每路单线程/3GiB/禁swap，分别绑定独立CPU1/6；worker合计最多6GiB。无在途时需至少7GiB
可用内存才能派发，已有一路时需至少4GiB才启动第二路，无第三路。初始实测8220925952字节可用。
保持原54筛选+36确认，选模必须等全部54条筛选结束。所有失败保留，基础设施/审计异常后
停止新派发并等另一路结束；不将先完成的候选提前选中，不重新跑旧结果。

资源补充登记`DISPATCH_V2.json` SHA
`9e3a17005cdb3329910fd7a3e8e11302ff280c7fc7442418bd5cce89cffc1726`。
控制器/worker来源、参数、seed、环境模型、gate、actor、执行限制与登记排序均不变。
根`CHAIN_EXECUTION.json`是旧串行收口记录，当前状态以根`execution.json`和上述v2服务为准。
新监视器`sii-classical-monitor-20261010-v2.service`使用
`outputs/classical_boundary_monitor_20261010_v2/`，支持两路active_jobs并验证资源补充登记；
v1监视器的CLOSE是安全交接记录，不代表90条全部完成。

18:02观察到两个worker分别在CPU1/6上约100% CPU、各约0.66GiB RSS，可用内存6.4GiB，
内存PSI为0；两路实际派发admittance_boundary_03/04。预计余下约4小时，尚非实测最终加速比。
7项完整性/内存准入/防重复回归通过，12条交接结果重核验通过，0新增检查物理步。

18:03已核验源码、资源登记、串行交接和启动快照至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_parallel_setup_20261010/evidence/`。
11文件/318902字节，manifest `d47aed02df06a3a83795c7020d74124042f6e9f5cdf0190bd3b1ea3302b0051c`。
源码入口`source/parallel_classical_search_20261010.py`；复现worker仍用原run冻结来源。
小包START_SNAPSHOT是12条完成/2条在途时的快照，实时进度仍在本机。服务器未启动实验。
