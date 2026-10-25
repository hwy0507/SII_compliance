# 完整延长折扣诊断与新鲜小批量在线阶段（2026-10-25）

四路原有限折扣probe已经完成并退出，40万辅助更新预算结束，没有新增physics，也没有保存或推广辅助权重。完整配对诊断不支持把减小gamma当作统一修复。下一在线阶段保留任务奖励和gamma.9995，从全新CHEQ-core状态、空replay开始，采用batch256/每环境步一次更新。已经实际派发，Direct/Admittance/VMC正在真实采集预热数据；这不是健康收敛结果。

## 完整配对证据

同一cycle6完整30×1375条历史transition子集，同一fresh seed和全初始化/RNG，Bellman与PBRS gamma共同变化；每接口两arm各50000更新，共400000。四个旧probe361333/361334/361335/361336已退出，勿重启。原始checkpoint和transition哈希、完整曲线更新编号、每arm记录与FINISHED一致性、两arm初始state和sampling RNG等检查通过。新旧每1000直到5000的40个共同前缀点metrics/diagnostic精确相等；因旧probe未存权重而重算，不能称独立重复。两张图已目视检查。

| 接口 | Q均值 γ=.9995 / .99 | 终端MAE γ=.9995 / .99 | 最后记录critic loss γ=.9995 / .99 |
|---|---|---|---|
| direct | 65.4335 / 19.0249 | 0.1654 / 1.1134 | 0.0801 / 0.1178 |
| impedance | 63.0574 / 12.1417 | 0.2745 / 0.7444 | 0.0772 / 0.1575 |
| admittance | 104.2027 / 13.2412 | 5.2395 / 0.7530 | 1.0209 / 0.2939 |
| vmc | 145.2065 / 36.9963 | 18.7446 / 5.6428 | 11.5995 / 2.3932 |

所有arm的末段采样策略熵已接近各自目标−5/−7，原5000更新未覆盖此阶段。较低gamma降低样本Q，但终端误差对Direct/Impedance更差、Admittance/VMC更好；VMC最后5000区间两个gamma的Q和终端误差仍增长。最后5000统计仅含5个每1000采样点，不冒充5000个逐更新loss平均。

Direct长gamma全部样本仍超过当前alpha下的必要上界，尽管终端MAE很小；VMC低gamma超限约4.02%，其余末点为0。上界是当前固定alpha/policy的必要范围检查，不是训练期间真实return校准。历史行为和CHEQ context固定、单seed、有限更新，不能由这些离线loss/误差推出在线成功或收敛。

55秒/1375动作的终端奖励在起点的折扣系数：.9995^1374=0.5029966，.99^1374=0.00000100637。任务成功门仍在完整回合结束判定；减小gamma会大幅改变长时任务优化偏好，不能仅凭Q较小选择它。

## 已登记并启动的新在线阶段

科学决定`runs/FRESH_REDUCED_REUSE_SCIENTIFIC_DECISION_V1.json`引用完整all5失败review、上述完整折扣review和新的初始化检查。原all5已经结束不原样延长；新阶段为完整fresh恢复方案，不是继承失稳actor/critic/alpha的单项batch因果消融。

- 使用已验证的source_train16，保留同一30条件、参考计划、physics/MJB、Task/Strict gate、actor信息、公共filter、执行器限制与dt5e-5；原冻结runtime未改。
- CHEQ5critics、原随机双target最小值、nominal mixing和自身context保留；actor49（canonical48加自身mixing）。Direct7、Impedance5、Admittance7、VMC7接口不改。
- 全新网络、target、Adam、alpha和RNG，空replay，不导入旧训练replay或辅助权重；seed20261025。actor/critic原学习率3e-4、gamma.9995、criticLayerNorm和已有数值修正保留。
- batch恢复作者配置的256，每个真实环境步更新一次。相对原16384×2，每环境步的replay样本抽取量减少128倍：完整41250步周期为10560000而非1351680000。作者原异步更新节奏并不等同本地固定UTD1，不能宣称原样复现。
- 独立登记六个完整30条件周期，上限每接口247500新真实transition。该预算是下一次阶段review边界，不是整个Goal步数上限；需检查reward学习改善、稳定性、critic/alpha及独立固定策略表现，阶段结束不自动通过。

新run `runs/cheq_fresh_reduced_reuse_seed20261025_v1`，派发器1146202、冻结`runtime/fresh_reduced_reuse_dispatch_v1`。每路等待对应原SAC双worker完成完整周期并退出，以及原有限probe完成并退出；不停止/复制在途任务。CPU：Direct0+11/12、Impedance14+25/52、Admittance26+37/38、VMC39+50/51，分别GPU0–3；与扩容后的四SAC40核不重叠，协调CPU53/原观察CPU13/原协调54，合计不超55核。

当前Direct新1215546、Admittance新1314547、VMC新1146204已产生真实transition，仍在5000步预热、updates=0，不能称梯度学习已启动。Impedance仍等原SAC完成。source16冻结RUNTIME保留prepared_only构建时文字，实际部署以新登记/EXECUTION为准；未改写历史manifest。

只读observer1156327在`runs/fresh_reduced_reuse_audit_v1`等待完整cycle0/1/3/5归档，12小时仅是observer派发保护，不停训练。提前启动者由early_archive记录完整checkpoint，四路开始更新后交接正常archive。

## 验证、原SAC交接与资源限制

2项派发守卫测试通过，覆盖污染replay/续接拒绝、CPU重叠、原进程仍活跃时等待、PID复用、无成功收据和错误完成收据拒绝。四接口CPU构造预检确认空optimizer/replay、默认pair target、gamma、49维actor和动作shape；0physics/0updates/无权重保存。v1因digest工具不在learner runtime而在创建learner前失败，原失败保留；v2从既有冻结验证目录读取helper并通过。source16的780源/24参数/150上游/128机器人实际文件hash全部核验。

VMC、Direct、Admittance新环境各首2例实际MJB/55s/dt/参考计划/无truth/基准48维遥测与7维动作核验，通过实际worker CPU亲和检查。新EXECUTION确认无resume、无recovered_replay，batch256/UTD1/pair/LR正确；尚非完整新回合审计。

原SAC资源协调器691298继续：Direct旧1010728已在cycle6/304286步/562088更新正常结束，新1215621实际更新cycle7，9worker绑定CPU1–9；父checkpoint副本/EXECUTION哈希精确，首9实际模型和输入/dt通过。其周期并非全55s，早停失败仍保留，不能用总步数推断成功。Admittance旧2758791已完成cycle3/185515/330000，新1316018实际更新cycle4/9worker，父checkpoint及首9模型/输入/dt/CPU核验通过。VMC新726082继续cycle4；原Impedance仍完成原周期。原observer3759872及只读子进程1319809现已完成退出，Adm/VMC cycle3整组已科学复核，不重复派发。

辅助probe结束后的60样本/66.76s纯正式训练窗口GPU均值仅4.42/4.88/2.65/33.27%，最小均0。该窗口多数接口仍为双worker周期收尾，fresh CHEQ在预热；正式独立50%仍未达到。之后Direct完成9worker交接，但不能用未测量的后续窗口宣称达标。提高仿真采样吞吐继续必要，不能把先前辅助混合均值当正式结果。

三路9worker生效后的第二个纯正式窗口（60样本/66.47s）均值36.45/5.78/23.38/25.58%，最小均0，仍未达50%。原始GPU_60S_FORMAL_ONLY_02保留；当前没有辅助GPU learner。

## 原SAC Admittance/VMC完整cycle3新证据

原观察与诊断已结束；核验60个完整55s/1375动作回合的终端/模型、checkpoint原件/快照hash、reward重建与网络未变，并检查训练诊断图。Admittance Task/Strict12/12（各30，分类0/7/5），失败carry17/release1；VMC18/18（分类0/10/8），失败carry12。均为变化中训练策略，不是冻结策略比较。

cycle2→3：Admittance末1000 critic loss146717→1790203、样本Q18097→43734、终端MAE3754→13778；VMC loss537785→3062208、Q28848→82018、终端MAE11169→23290。两者都有成功回合，但优化诊断明显恶化，不能称健康收敛。新fresh方案仍需独立在线验证，不能以选择了新方案代替修复证据。收据`runs/sac_remaining_cycle03_audit_v1/REVIEW.json`，0新physics/更新。

## 证据与剩余任务

集群SSD根：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。上述所有相对runtime/runs路径均基于此处。

- `runs/consistent_discount_extended_cycle06_v1/COMPLETED_REVIEW.json`及`report_v1`：完整配对收据、SUMMARY、LATE_WINDOWS、Q/误差图和优化诊断图。
- `runs/cohort30_v2/REGISTRATION_CHEQ_FRESH_REDUCED_REUSE_V1.json`与`runs/CHEQ_FRESH_REDUCED_REUSE_DISPATCH_V1.json`：新训练和资源协议。
- 新run的STARTUP_REVIEW、DIRECT_STARTUP_AND_SAC_MIGRATION_REVIEW与GPU_60S_FORMAL_ONLY_01：实际启动和资源证据。
- 同名报告JSON索引必要原文件hash，全部大模型/轨迹/环境留SSD。

后续继续原交接与新鲜在线阶段的实际学习/健康review；最终收敛、固定策略完整矩阵、共同事后Tref/SPT和指定ESN公平比较仍未完成，ESN仍缺。已fetch/read main a52dfba和baseline f6e8f8c，无远端新增变更。本地提交与push结果分别报告。
