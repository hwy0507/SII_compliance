# Task成功条件SPT与传统控制器同条件补测

2026-10-27用户要求只在Task成功回合计算SPT，并将历史传统控制器加入最新ESN/RNN/MLP
闭环比较。原108回合已经完成，不重新训练或重跑；新run为
`nonrl_classical_task_spt_20261027_v1`，固定6套传统参数×原12条件，新增72回合，最终共180。
本研究不含RL，另一会话的RL训练与冻结评价协议不变。

## 新指标及已经可以确认的结果

`SPT_task_conditional = mean(T_ref / max(T_i,T_ref) | Task_i=true)`。
Task失败回合该项为NA、不进入分母；没有Task成功的模型为NA。Task成功但Strict失败也纳入。
Task/Strict成功率、力矩和机器安全统计仍保留全部回合。共同后验T_ref取完整登记矩阵
所有Task成功回合的最短完成时间，保持一个全局参考，不分方法/条件。

仅对已完成108回合重聚合，T_ref=34.360000000578864秒。原39.40秒只来自双通过回合；
参考变化来自新纳入的Task成功/Strict失败回合，不是改变轨迹、gate或算法。

| 方法 | Task | Task且Strict | 条件SPT | 成功平均完成时间(s) |
|---|---:|---:|---:|---:|
| ESN | 28/36 | 20/36 | 0.755738 | 45.774286 |
| RNN | 26/36 | 12/36 | 0.744141 | 46.720000 |
| MLP | 3/36 | 3/36 | 0.669989 | 51.333333 |

这是三个训练seed的回合池均值，每模型明细另存；不是36个独立训练seed。
新条件效率下ESN/RNN差距明显小于旧“失败填零”的SPT差距。MLP只有3次成功，不能仅按
成功条件效率解释其整体水平。最终180矩阵将重算共同参考；此表仅代表完整108子矩阵。
原报告SHA256 `da9d4fb55ccea6b7eaa4ffa99ccfafaf6e9fe76d94e26b0a2f9f961bc201c7d0`，未改写。

## 传统控制器来源与公平性范围

沿用2026-10-10有限模型式参数搜索、2026-10-13模型锁中每类的两套finalists；不根据本次
测试结果重新选参数，也不只展示其中赢家。具体数值、历史audit hash及依赖源码清单已锁在新run。

| 控制类别 | 固定配置 | 执行方式 |
|---|---|---|
| 导纳 | admittance_boundary_06、07 | 力/力矩驱动的虚拟动力学，经原公共动作接口执行 |
| 阻抗 | impedance_boundary_01、02 | 原生笛卡尔弹簧阻尼力矩、投影平衡参考、原有摩擦前馈与姿态项；保留公共限幅/限速 |
| VMC | vmc_boundary_00、05 | 原虚拟机械柔顺控制律、物理量纲动作适配 |

传统控制器不从30条示范模仿学习；其历史有限调参预算不同。它们是固定系统基线，不能称为
与ESN/RNN/MLP相同数据、相同优化器或相同训练预算的学习算法。每个固定配置只跑12条件，
不将完全相同的确定性重复伪装成三个训练seed。两套配置单列，不作为随机seed求方差。

12条件与原108矩阵逐字节相同；复用原冻结物理源码和MJB，MuJoCo3.11.0、dt5e-5、55秒、
原Task/Strict gate和执行器限制。历史参数选择早于这些条件；研究者已经看过学习组结果，
这次是事后扩展比较，不把既有测试曝光称为重新预注册的完全盲测。

## 执行与审计

本机airpig：单模拟器、单线程、CPU1、MemoryMax3GiB、MemorySwapMax0；全局仿真锁避免
与其他本机作业重复。服务 `sii-nonrl-classical-task-spt-20261027-v1.service`。
计算目录：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/nonrl_classical_task_spt_20261027_v1/`。
入口 `tools/run_nonrl_classical_extension_20261027.py`，启动后执行run内冻结coordinator副本。
`execution.json`、每回合`rollout.progress.json`和`PROGRESS.md`是真实进度；先查服务/PID再操作。
`--run`拒绝已运行/失败/完成状态，失败原件保留；`STOP_REQUESTED`只在完整回合边界停止。

各回合保留policy trace一致性、公共filter独立重放、原始物理子步指标、穿透/峰矩/速度/RMSE、
源码/参数/config/MJB/轨迹hash及任务失败。**经典worker没有完整独立控制器actor重放**，
尤其阻抗的完整平衡参考/Jacobian原生力矩链不能用action7一致性代替；新报告明确标注这一限制。
学习组已有的完整actor/filter审计不因此降级或改写。

comfort保持原经验阈值 `[43.5,43.5,43.5,43.5,6,6,6]Nm`，只在人机实际接触力>0.05N
的物理子步按dt计分，无接触为NA，不宣称人体舒适认证。机器安全另列，包括穿透>0.2mm。

新聚合器四项测试通过：Task/Strict分离、排除失败且共同参考、无成功NA、异常时间与重复回合拒绝。
准备前核验6套依赖与历史audit全hash一致，以及旧108报告、锁模和冻结源码未改。
服务已启动并确认物理时间推进。72回合尚未完成，完整传统组结果、共同参考与最终归档待完成。
小型登记/108新口径证据先发布，运行中不把局部成绩称最终排名。

首回合已完整完成55秒及审计，用时369.42秒，协调器自动接续第二套导纳；启动链有效，
不是只有systemd active。按首回合粗估72回合约7.4小时，阻抗耗时可能不同，最终以实际进度为准。
首回合未完成Task（carry结束），原始失败保留，不作全组排名；OOM事件0、worker swap0。

2026-10-27 07:28 UTC：两套导纳在首条件已完成，原协调器接续阻抗01，未重复启动。
新增 `tools/audit_nonrl_classical_extension_20261027.py` 为独立只读审计入口；
`--progress --include-learned` 完成原108及首2经典回合的120,135,200个物理子步核验，
源码/config/参数/checkpoint/MJB/轨迹hash、完整回合/保存hold与lift的Task reducer、
Strict穿透门、完成时间、峰矩/速度/RMSE、接触合规与机器违规、公共filter重新重放均一致。
审计1分10.09秒、单CPU2/3GiB/禁swap，没有新物理仿真。原完整actor重放仅继承匹配hash的
学习组收据，经典仍不声明完整actor/servo重放；Task检查也不是重新构造全部支撑接触几何。
证据 `ORIGINAL108_AND_FIRST2_AUDIT.json`；状态是progress，不是180最终验收。
未完成72时默认最终审计拒绝测试通过。最终模式须全180身份齐全并逐行/逐方法重算共同参考、
成功分母与条件SPT，最终分支等待实验结束后实际执行。

2026-10-27 07:33 UTC：完成3/72，首原生阻抗01完整55秒后正常退出，协调器接续阻抗02。
首阻抗任务仍失败（carry），峰矩34.936Nm、外部穿透0.140350mm；没有据低力矩计为成功。
`FIRST_IMPEDANCE_PHYSICS_AUDIT.json`对已完成3回合330万子步审计通过，1.804秒/退出0。
原生力矩后端的保存物理指标/源码/参数/hash和公共filter核查有效；仍不声称完整原生servo重建。
收据共享至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_first_impedance/FIRST_IMPEDANCE_PHYSICS_AUDIT.json`，
2898字节，SHA256 `c6433ff7d775b92a1642e94d09e996142a9aac8423afdd1d45e4a7d7326e82cc`；
本地与远端一致。审计器精确源码已在audit110共享包中。完整矩阵仍在运行，不作局部排名。

## 归档

### 独立归档接续服务

`sii-classical-archive-pipeline-20261027-v1.service`于08:25 UTC启动，PID188540，单CPU2/
单线程/3GiB/禁swap/Nice10；原物理服务PID179772/CPU1保持。入口
`tools/watch_nonrl_classical_archives_20261027.py`，执行冻结副本位于run内
`published/archive_pipeline_v1/source/`，自身登记/状态与原物理execution分离。

它只等待登记的12个条件，每个条件六套配置都已完整结束才审计、打包和传输；不派发仿真、
不改控制器、不自动重启主作业、不写Git。通过独立文件锁、拒绝重复run/prepare、独立远端
目录和严格hash检查避免重复或覆盖；首条件已有包只重新核验后接管，不重新传输。
重复run/prepare的真实拒绝检查通过。源/注册hash在每个条件前核对，失败保留并退出归档作业，
原仿真继续由原协调器管理。`STOP_REQUESTED`放在pipeline目录时，在条件边界停止归档。

查看pipeline自身`execution.json`、`logs/`及`ARCHIVE_000.json`至`ARCHIVE_011.json`。
主仿真当前完成数以run根execution为准；pipeline的`campaign_completed`是上一次等待时的快照。
12包全部核验且主run生成完整报告后，自动执行独立最终180审计。即使pipeline最终成功，
状态仍为`raw_archives_and_final_audit_complete_pending_publication`，之后还需主agent检查并发布
完整结果/最终证据；不能把服务active或首条件接管当作Goal完成。

启动后已核验首包远端hash并写出`ARCHIVE_000.json`，随后真实等待并进入第二条件审计/归档。
精确源码/登记/启动快照包13,129字节已共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_archive_pipeline_registration/ARCHIVE_PIPELINE_REGISTRATION.tar.gz`，
SHA256 `f7f3b2099f3e17f5165a3fd03dbc860dea947988643c207836c0682e8bcb92b6`，本地/远端一致。

第二条件001已由该作业实际完成全部流程：660万子步审计、318文件打包前后/包内hash核验、
上传、远端临时及最终hash/大小验证，随后自动等待条件002。新包730,459,913字节，
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_physics001/PHYSICS_BUNDLE.tar.gz`，
SHA256 `c0b1e4f18c7b5fdaa796229db9526166d367ed9dcfc62524d5f1edd31ee0c070`。
收据 `CLASSICAL_CONDITION001_ARCHIVE.json`、`CONDITION001_PHYSICS_AUDIT.json`，
快照 `ARCHIVE_PIPELINE_FIRST_NEW_CONDITION.json`。此时主仿真12/72完成且已进入第三条件；
共享新经典原件12/72，未声称剩余60回合或最终180审计完成。两服务OOM事件0、swap0。

### 单条件打包入口

2026-10-27 10:26 UTC：第五条件004的6回合/660万子步审计及归档完成，累计30/72，
原协调器已进入第六条件。该组六回合完整55秒、Task/Strict均失败、公共filter误差0，
保留失败和独立经典actor/servo重建限制。318文件原件前后/包内hash一致，
726,543,883字节包已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_physics004/PHYSICS_BUNDLE.tar.gz`，
SHA256 `738d31a699901d40649b566119a9b0a3095ab13babb1a0f42c3073f639b8b589`，本地与远端临时/最终一致。
收据`CLASSICAL_CONDITION004_ARCHIVE.json`和`CONDITION004_PHYSICS_AUDIT.json`。
原108+新30回合已原始共享；余42和完整180比较仍待。memory.max累计12、OOM/kill0、swap0，
本地可用空间约517GiB；两原服务正常，观察会话在第五包完成后正常退出。
本轮先查询/fetch/read并安全快进main至`06df65e6fb9b527473c2b276d3109c5cf8809013`，
baseline仍`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，非RL源码及冻结协议未变。

2026-10-27 09:48 UTC：第四条件003全部6回合及660万子步审计通过，累计24/72，
原协调器已进入第五条件；前三包保留。第四包318文件原件前后及包内hash一致，
726,692,174字节已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_physics003/PHYSICS_BUNDLE.tar.gz`，
SHA256 `c3a20533156f9bd0035e473e4e3f8fe6c67198b8828cc6c17d7616abb48e8acc`，远端临时/最终一致。
收据`CLASSICAL_CONDITION003_ARCHIVE.json`、`CONDITION003_PHYSICS_AUDIT.json`。
本组六回合完整55秒、Task/Strict均失败、公共filter误差0，仍保留全部失败与actor重放限制。
原108+新24回合已原始共享；余48和最终180汇总尚待，不生成部分矩阵参考或排名。
物理cgroup memory.max累计仍12次，OOM/kill及swap0，两原服务继续；只读观察在第四包
核验后正常退出，不影响仿真或归档服务，不新增/重启作业。

2026-10-27 09:10 UTC：原协调器完成第三条件002，累计18/72，已接续第四条件。
归档服务自动完成第三组6回合/660万子步审计、318文件原件前后及包内hash检查，
728,329,915字节包已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_physics002/PHYSICS_BUNDLE.tar.gz`，
SHA256 `ff3750c2face9fa3cccacbed4ba3b6a02e74e6ece40124bcd7d58631cac675a5`。
远端临时及最终文件hash/大小均与本地一致，收据`CLASSICAL_CONDITION002_ARCHIVE.json`和
`CONDITION002_PHYSICS_AUDIT.json`已发布。该组6回合完整55秒、Task/Strict均失败，
公共filter重放最大误差0；保留失败，不以无机器违规或低矩代替Task成功，不作局部排名。
审计范围仍不包含完整独立经典actor/servo重建。当前共享覆盖原108和新18回合，余54仍待。
本机物理服务曾记录12次memory.max命中，但OOM/kill及swap均0，后续内存回落约1.43GB；
这是内存上限触发记录，不记作OOM，也不据此重启正常推进的服务。
已安全快进main至`dc35b325982d12b5634501be534a5bd75876cc42`，保留另一任务的RL交接；
非RL源码/协议未变化，未修改现有冻结运行副本。

按完整条件归档入口：先用 `audit_nonrl_classical_extension_20261027.py --progress --condition <id>`
核查该条件全部6个完成回合，再用 `archive_nonrl_classical_condition_20261027.py --root <run>
--audit <condition_audit.json> --output <new_directory>` 打包。审计现在绑定源run、模型锁及每回合
原始文件hash；打包前后重哈希原件，并读取每个tar成员核对大小与SHA。缺配置、在途回合、
改写轨迹、错误审计器版本都拒绝，不把活动execution快照称最终状态。四项小型合成文件测试
通过（完整包验证且原件不变/在途回合拒绝/改写轨迹拒绝/缺配置拒绝）；真实未完成条件也被拒绝。
旧审计收据不改写，对应旧版审计源码仍在其既有共享包中。

服务器只用于本轮归档，不计算。已核验登记包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_registration/REGISTRATION_BUNDLE.tar.gz`。
大小2,001,510字节，SHA256 `dc4f40656985e1fced46077ebab0d81e97380dc1070d6dfe1136ca79977c148b`，
含冻结coordinator/物理/经典控制器源码、参数/协议/条件及108新旧聚合报告。收据见
`docs/evidence/nonrl_classical_task_spt_20261027/REGISTRATION_ARCHIVE.json`。
未完成回合不复制为完整证据。全量最终原始产物在72回合结束和核验后另行归档。

110回合审计与对应两版审计器源码独立共享包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_audit110/PROGRESS110_AUDIT_BUNDLE.tar.gz`，
18,690字节，SHA256 `aabca99f4ffb4ce981bc753f1ec4b85c98f96aeaa3769d14e9ae74b1db55c412`。
只读收据已共享；本批新增原始物理轨迹仍仅本地。

### 首条件原始物理包与原108归档补齐（覆盖前述仅本地快照）

第一条件全部6套传统控制器完成55秒、660万子步审计，`CONDITION000_PHYSICS_AUDIT.json`
状态为`completed_classical_condition_audit_passed_not_final`。6回合Task/Strict均失败，
低矩/无穿透违规不替代任务成功；仅首条件，不计算局部SPT排名。归档器真实运行15.378秒，
318个文件逐一核验，源码/参数/完整轨迹/失败/metrics均保留；冻结物理/coordinator未改。

已共享原始包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_physics000/PHYSICS_BUNDLE.tar.gz`，
729,714,755字节，SHA256 `3c7432b5610533a537d0e4749c9b17ae88c2f1dd385b1c9972ef0c3d86c4d80f`。
本地/远端临时/最终hash一致，收据 `CLASSICAL_CONDITION000_ARCHIVE.json`。

另发现原108学习组只有前72原始回合此前已共享，最后36只有小型结果证据。
本轮复用008旧完整条件审计、重新按既有入口核验009–011，补齐837文件/36回合物理原件：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_new30_fair_20261026_v2_physics_008_011_20261027/PHYSICS_BUNDLE.tar.gz`，
4,317,470,894字节，SHA256 `a70370763742ee2978d5e11b5740a05ccc229dc49c3765f6d4a16c9b31e66ca7`。
打包96.806秒，原件前后/每个tar成员/远端临时及最终hash一致。此前前72的四包远端hash也
重新读取并匹配旧收据；因此原学习组108条原始物理数据已全部共享，不是只共享最终小表。
收据 `LEARNED_LAST36_ARCHIVE.json`。本地原件未删，服务器未仿真或训练。

初次009–011审计命令因条件编号的命令层变量展开失败，被未知条件守卫拒绝，未启动仿真；
随后改为明确参数列表，三条件核验均通过，失败见 `ARCHIVE_AUDIT_COMMAND_RETRY.json`。
目前传统组9/72完成、下一原阻抗worker继续；完整180汇总、剩余63回合及其原始归档待完成。
