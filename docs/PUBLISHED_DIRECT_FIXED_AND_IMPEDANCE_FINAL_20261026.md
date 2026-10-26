# 固定Direct的失败位置与Impedance有限阶段结束

目标继续，尚无充分收敛或最终ESN比较结论。本轮完成Direct三个代表条件的保存物理数据复核，
确认Impedance六周期正常结束，并依据已完成的辅助对照启动有限critic初始化诊断。

## 固定Direct与同接口名义控制

使用已预选fresh cycle3 checkpoint（165000步，SHA `fa9ebcd0c32d456ce17ac28c1d5db017b37f1f624d91aa8aaef3a1ea75f5cccd`），
三个代表条件全部完整55s，Task/Strict均失败于carry。相同条件的名义Direct短期/长期成功，
被动失败。相同MJB、fixture、nominal plan、dt及舒适阈值逐项核验；无ESN替代。

| 条件 | 学习策略Task/Strict | 名义Task/Strict | 峰值Nm：学习/名义 | 最后10s名义与filter残差方向余弦 |
|---|---:|---:|---:|---:|
| passive_corner_train_0000 | 0/0 | 0/0 | 38.984 / 38.596 | -0.9445 |
| active_short_train_0000 | 0/0 | 1/1 | 39.020 / 47.049 | -0.9413 |
| active_long_train_0000 | 0/0 | 1/1 | 39.455 / 46.617 | -0.9510 |

六条归档回合共660万物理子步只读复算，力矩/接触/时钟/原始日志一致；三条学习策略的
public filter和力矩投影重放均通过。名义归档复核物理和filter，**不声称旧名义归档也有力矩投影重放**。
源与checkpoint实际hash、actor49/raw48/common7、完整回合数和无actor truth均核验。

学习策略最后10s的公共filter线残差约0.0323–0.0326m/s，观测中的名义线速度约0.0391–0.0411m/s，
方向余弦均值约−.94至−.95，每个采样时刻点积为负。平均WBC scale约.889，
观测的平移pose error约19.1–20.1mm。该描述提示策略持续抵消前进，但下游WBC authority、
关节映射和真实速度还会影响执行，**未做因果干预，不把这个相关性当作全部失败原因**。
这些仍是中间cycle3结果，不是最终cycle5全部30条件接受结果。

学习策略长期条件发生5.9546s真实人接触，工程阈值下合规比例100%，任务却失败；
被动/短期无人接触，合规应为NA。低峰矩和100%接触合规不能替代Task成功，失败SPT为0，
本轮没有为不完整最终矩阵选择Tref。原固定矩阵协调3148346继续参数方法，未重跑已有物理。
只读review session92211完成；产物 `runs/fresh_cycle03_direct_fixed_review_v1/`。

## Impedance正常结束，但没有健康收敛证据

原PID3849956已退出，不重启。最终246984步/241985更新，六完整条件周期；最终checkpoint与
migration_archive字节hash一致：`437c2625c96eadddc94237b9dd8a3adae09db46325bfafb6fbd85e84390e9b3b`。
前期一次859-action提前中止造成总步数比完整247500少516，该失败保留。

最终一轮30/30全部完整55s，Task18、Strict17；被动0/0、短期10/9、长期8/8，各10条件。
短期0600外穿透峰值0.2304423mm超过原0.2mm门槛，Task真但Strict假，未放宽gate。
mean reward−2.274513，最近三轮range .096409，小于.5容差；相对前两轮改善1.049810，
未达到登记2的候选门槛。末1000优化日志均值：critic loss10690.2567、next_q_values1053.8310、
actor loss−1056.7185、alpha .164764。next_q_values是训练目标日志，不是独立Q校准测量。
reward平稳及有限loss不证明健康收敛，更不能替代完整冻结策略评估。

已逐30terminal/MJB/保存结果、奖励重建与replay索引核对，无新增physics/updates；
只读session8822完成，`runs/fresh_impedance_final_cycle05_review_v1/REVIEW.json`。
本轮没有重复执行原2472115等待中的整组cycle5网络诊断。
保持完整状态，不自动原样延长；下一在线阶段依据整组证据、固定策略和辅助诊断另登记。

## critic初始化对照继续定位误差来源

原完整回放时钟诊断八进程现已全部正常结束，勿重启；24臂/120万辅助更新、1200诊断点
的完整函数初始化/采样hash/actor与replay不变核验完成，review session40035退出，八面板图已看。
三seed均值in-bag terminal MAE无/有时钟分别为Direct19.572/23.388、Impedance21.235/19.720、
Admittance34.713/33.771、VMC65.896/73.352。Direct/Admittance/VMC两臂多呈先降后回升，
不存在通用clock修复。部分Q后段负向移动；仅凭正负不能判断价值估计错误。
这是全量拟合数据的诊断，没有heldout分数；不推广权重或判定在线策略收敛。

新登记 `runs/fresh_initialization_critic_clock_v1/`，冻结工具同名runtime：
固定同一checkpoint actor/alpha/data/masks和seed20261027，online/target critic改为上游新初始化，
对照复用刚完成的同seed父critic初始化结果。两臂仍是零输入/已知时钟，每臂50k，
四方法共400k辅助critic更新的有限预算，0physics/0actor更新，不保存推广辅助权重。
这是明确的初始化×时钟对照，不能单独区分online和target初始化的作用，也不能作多seed泛化结论。

四PID391155/391156/391157/391158，复用已释放CPU1/3/5/7及对应GPU0–3；
与剩余原shard0同时运行。首4000更新启动核验通过，fresh critic hash与父不同、
checkpoint/replay/alpha/gamma相同，程序逐tensor确认actor严格保持父权重。
三个时钟/输入/终端守卫测试再次通过。正式runtime、actor、reward、physics/MJB、gate、
公共filter、执行器限制及dt均不变。此诊断未完成，不称修复或收敛；勿自动延长/重复派发。

完成原对照后，为避免仅一次随机critic初始化误判，新增独立replication登记：
`runs/fresh_initialization_replications_v1/`、同名runtime。seed20261026/20261028各自单独进程，
因此构造时critic随机初始化也独立；复用原seed20261027，不重跑旧结果。新增8进程、每臂50k，
增加80万预算，加原40万合计120万fresh-critic辅助更新，不是无限追加。
8PID648950/648956/648962/648967/648975/648978/648983/648987；
CPU8/9/10/11/12/14/15/16，GPU0–3各2，原seed27四任务继续。
首12–13k更新已核验，逐方法3个初始critic hash彼此不同、actor/replay hash相同。
正式physics/actor/learner不变；结果尚未全部完成，后续仍须审查，不自动推广。

## 接触候选进度和资源边界

第7/8例Admittance被动/短期完整55s/各110万子步精确复核，Task/Strict均假，保留原失败。
`SEVENTH_CASE_REVIEW.json` / `EIGHTH_CASE_REVIEW.json`；现8/12已独立复核，
原2273688继续，候选没有部署，不代表全矩阵验证或整体加速。
新GPU60秒混合负载均值89.18/89.25/92.47/89.38%，最低87/87/89/88%；
不能冒充纯在线训练吞吐，GPU_60S.json另存。VMC也已原阶段完成247500步，
FINISHED的cycles_completed=5是恢复后五轮，另加父cycle0共六轮。随后Admittance也已247500步结束，
原2472115的cycle5工具结果已全部产出、child543487结束，整组**科学复核仍待完成**；
不据阶段/工具结束声称策略收敛。新增replication实际更新后四卡瞬时均99%，不能外推持续保证。

服务器基址 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/`。
本报告及配套JSON记录原始产物地址/hash；大数据、环境和checkpoint不入Git。
实时fetch确认远端main=a52dfba4486af8d263d5cd0a976c3102482ff249、baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。
本地提交/远端发布分开说明；充分收敛、最终冻结矩阵、SPT_empirical、接触舒适审计和指定ESN比较仍未完成。
