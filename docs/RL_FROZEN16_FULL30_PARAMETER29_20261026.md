# Direct16全30冻结验证完成与参数续训（2026-10-26）

Goal active，四路整体健康收敛仍未证明。Direct16冻结全训练矩阵已完成，正式Direct18继续，参数28完整审查已完成，正式29已启动。前序科学依据见RL_PARAMETER28_TERMINAL_CONCENTRATION_20261026.md，29准备及固定27–29稳定性窗口见RL_PARAMETER29_PREPARATION_20261026.md。没有子agent，没有改物理/MJB/SPT/gate/canonical48/action7/任何正式learner、优化器、RNG、回放或历史标记。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，R=B/repository/SII_compliance，原HDD仓库路径为该目录链接。实际计算/大产物在SSD；HDD只有小交接与收据，不是HDD/arm1全量备份。

## 冻结Direct16完整结果

原B/runs/serl_cycle16_frozen_full30_20261026_v1的evaluator1749189/1749193及review1749197均完成退出，勿重跑。REVIEW.json通过，30×55秒、41250动作/33000000物理子步，全30原训练条件、外部独立动作seed2026102626、原随机策略，没有改确定性mode或增加预算。

冻结父仍为准确完整16（689532steps/5476264critic），checkpoint SHA256 d2ee183f0ebbafa44dabb8dc318cc2091dfc031145a2192bd9a313f989067c5b。两个分片POLICY_UNCHANGED的初末完整learner digest均为87a2a606a399acd3d8314e40618a67fc7b17316a2f4284ed4d7ad9f63706bcb1；全网络/优化器/计数/RNG状态不变，0优化/0正式replay写入，原checkpoint/source/hash守卫通过。

| 原训练条件类别 | 完整55秒 | Task | Strict | 中止 | 机器安全违规 | 终态 |
|---|---:|---:|---:|---:|---:|---|
|被动角点|10/10|0/10|0/10|0|0|10条approach|
|主动短期|10/10|0/10|0/10|0|0|10条approach|
|主动长期|10/10|0/10|0/10|0|0|10条approach|

全30人体接触时长为0，舒适度全部NA，不能把没有接触当作柔顺优秀。三类最大单关节峰矩分别45.962386、45.428634、47.023777Nm；这些是实际记录峰矩，不是人体舒适阈值通过声明。Task/Strict均0支持本冻结策略尚未学会任务，不证明其他seed/策略永远不能成功。

原review对全部33000000已保存子步汇总物理指标，并独立重放公共filter和力矩投影/幅值/slew/前值递推/执行器链接；全30通过。保存结果的峰矩、穿透、接触与合规时长重建误差0，filter及torque projection最大绝对误差0；elapsed汇总误差≤8.881784197e−13秒。不是独立重新运行全动力学，也没有重构native reference wrench/Jacobian。SAVED_SUMMARY.json另逐文件hash核对30个审查JSON并分组汇总，无新增前向/仿真/优化。

这是一个训练seed、一个外部动作seed下的全训练条件冻结诊断，不是held-out、多独立训练seed、确定性mode、指定ESN或最终SPT比较。结合已完成13–16回报审计，证据支持回报改善主要降低惩罚、随后趋稳且任务停滞；仍须完整当前18健康/回报结果及其他三路稳定性，不能仅因审查passed就宣称整体健康收敛。

## 原正式训练与等待器

Direct18 learner2732254、归档2732257/review2732258仍运行；19准备等待3088320只完整18后check-only，CPU调度3269262仅原18退出后复用CPU0。无自动19训练。

参数28原三learner3733553/3733556/3733557、归档3733614/review3733617、恢复准备4005782及CPU调度4005783均已完成退出，勿重跑。三路30×55秒无abort、旧I/V1152000与A1151000回放全字段/history/2m历史marker保持，新41250 reward重建误差0、network/optimizer有限，REVIEW/health/FINISHED和图审查通过。

| 方法 | 完整steps / updates | Task / Strict（/30） | reward | 末1000 q_loss | terminal MAE | inbag MAE |
|---|---|---|---:|---:|---:|---:|
|阻抗|1193250 / 1188251|18 / 17|−2.369572402|1.455425530|.783424741|.219322185|
|导纳|1192250 / 1187251|14 / 14|−8.690925126|1.398468841|.593407164|.181417408|
|VMC|1193250 / 1188251|17 / 17|−2.814530758|.764321464|.664457906|.354284873|

阻抗Strict保持、末loss下降但reward略降；导纳与VMC任务/回报恢复，尚不稳定。抽样Q超过当前必要soft上界比例I0/A.00136718748/V.00214843755，V比例比27增加；不能把有限loss和拟合误差改善等同于整体校准健康。PRELAUNCH_SCIENTIFIC_REVIEW已记录继续一轮原设置以完成固定27–29窗口的依据。

准确完整28父B/runs/parameter_capacity_pool30_cycle28_archive_20261026_v1/{method}/cycle_00028.pt，SHA分别：I7a85c929be8599e6b128e82b63fae05f60feccc4027a68e3f22b739b814f906d；A2acc0242f1fa0a464af5a19e1e75138725e7f59b5a643c74cab80a4b134ea87d；V97de1ff4b520fdd7d19dda03e4c832befcbf50f62d593c2fb1ab43facb57d167。

29三check-only全learner/replay/下一65536/RNG精确与负守卫通过。2026-10-26 22:25:22 UTC正式29启动：I946578/A946579/V946580，B/runs/parameter_capacity_pool30_cycle29_20261026_v1；startup946582、归档946583/完整review946584。准确最新28完整state续一个周期，原GPU1–3/CPU13–51/30pool/batch65536/UTD1/terminal128/projection/Imin+A-Vmean/actor min/LR不变，必须capacity replay+pair learner、2m历史入口23保持。实际启动审查另查startup/REVIEW.json，不拿check-only代替新增检查。无自动30。

固定参数27–29稳定性窗口原4175982在等待全部完整结果，27输入hash已封存，在28运行/29尚未训练时预定，现仍等待完整29。原5%/近零1/三类5000配对bootstrap规则，不自动停训。核所有完整优化记录、整轮/首末loss/alpha/terminal/inbag/TD，不能仅凭finite叫健康；不是新训练或已完成24–26重跑。

## 运行资源与发布

冻结evaluator退出后GPU PID集合已回到恰四正式learner。新一次纯18/28占用观测B/runs/batch18_parameter28_after_frozen_gpu_20261026_v1，原645110，登记60样本/每秒1次、每样本严格核四GPU PID及原进程start identity。这是参数28后段的实际运行窗口，不是所有sampler都活跃的稳定吞吐基准；不添加GPU负载、不按占用挑选重采，原645110已完成：60样本/68.317217秒，四GPU均值54.1/69.233333/74.933333/67.733333%，D/I/A/V吞吐10.3488/22.4980/25.6158/23.0103steps/s；逐样本原learner全部live且GPU PID恰四正式。此窗口均值均≥50%，不保证每瞬时、也不包含此前过渡空档，勿重复观测。

本轮实际查询/fetch远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，与已读日志SHA一致；GitHub HTTPS认证仍失败，不重复问用户。固定窗口提交35585c4已本地提交，完整冻结结果另随本交接提交。小证据docs/evidence/rl_frozen16_full30_parameter29_20261026保存原30条物理review及最终状态/源hash，raw子步、checkpoint仍SSD。指定ESN缺失，已问不重复、不替代。

正式29实际启动检查已通过：impedance新增1000至1194250、admittance新增1000至1193250、vmc新增2000至1195250；全部旧replay字段/history/优化器配置/2m历史marker/30MJB/30sampler/action/clock和新reward0误差通过。原946582完成勿重复，归档946583/完整review946584继续。

本轮最终科学提交9912e081ee4c7bbbb400ffda0bbaac17ee2696e7仅本地，push仍HTTPS用户名认证失败；重新fetch main dbb1d76/baseline f6e8f8c未变。完整本轮小证据包/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_FROZEN16_FULL30_PARAMETER29_20261026_222836/FULL_SMALL_EVIDENCE.tar.gz，103成员逐hash核验、1140684字节，SHA256 d53d8b6fabc738333b1f9b13a53a46111dca310f000bfba5e9c8a784ef69eeb4。HDD小交接/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_FROZEN16_FULL30_PARAMETER29_STATUS_20261026_222836/HANDOFF.md及收据/LATEST已核验；大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。Goal active，原Direct18/参数29持续，固定27–29审计等待4175982保持。
