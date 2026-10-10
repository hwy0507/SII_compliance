# 经典 baseline：基础验收、停滞归因与补强

用户2026-10-10要求优先把VMC、导纳、阻抗做扎实。新计算仅在airpig本机；Spark只归档。
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
五项完整性/选模测试确认：frozen/events_off模型字节不变；clear/edge_only/active_only只修改
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
复现仍需历史`baseline_repair_15h_20261008/source_v9/`、`parameter_v2/`及各execution中
登记的冻结MJB/Menagerie/本机MuJoCo3.11.0运行时；小包不包含这些大型依赖。
完整基础诊断/源码/失败包1445文件/749877105字节正在传输，清单SHA
`1e9f6ad501ddf8b915c79f73630efc6bae3016f52fde5c82aba5e55492e345d7`；
目标incoming/classical_readiness_20261010尚未核验发布。一次性收尾服务等待原rsync后
逐文件核验，不重启传输；本地收据`outputs/classical_readiness_archive_transfer_20261010.json`。

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
shield/伺服审计通过；三条edge_only归因正在进行。

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
2. 正在执行六条接触归因：三经典各跑active_only（原主动球/手/棍，关闭非支撑静态障碍）
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
4. 再依据因果结果决定必要控制设计；不同控制律另列，保留传统原法与
   enhanced teacher这一更强model-based参考。不能把添加恢复机制后的算法冒称原始线性导纳/阻抗。
5. 锁定配置后在冻结综合场景统一评估；所有失败保留，未解封新最终条件。

目前完成的是基础搬运验收和独立控制器审计，**完整接触恢复、扩展调参充分性、最终重评仍未完成**。
论文不能把它写成“所有传统控制器已经充分调参且原理上不适合”。
