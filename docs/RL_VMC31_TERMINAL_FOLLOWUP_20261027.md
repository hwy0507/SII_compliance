# VMC第31轮终端误差集中度与固定样本跟踪（2026-10-27）

Goal active。接续[参数32/冻结全30交接](RL_PARAMETER32_FROZEN_MATRIX_20261027.md)。上一轮完整31审查、正式32接续、未来冻结32全矩阵预登记均为实质进展。本轮实际/proc和连续PROGRESS确认四正式与所有原准备/审查进程存活推进，未重复派发。无子agent，正式物理/算法/状态不改。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；host rltest-1025--a6ed2ff39b3c-2d5lfqki2m。大产物SSD，HDD小交接/收据，非HDD/arm1全备份。

## 新问题与完整结果

VMC30→31 Task/Strict均17/16、reward−4.565541→−4.605202，标签无变化，但末1000 q_loss .808988→1.168401。对准确完整30/31作一次CPU52只读审计，B/runs/vmc30_31_terminal_concentration_20261027_v1；原1376756及保存值review1425189均完成退出，勿重跑。仅载全部agent权重作CPU前向，不恢复/更新optimizer，不执行物理或写正式replay；网络/前向RNG与所有原checkpoint/source/input hash不变。

审计全部924/954终端×5critic，匹配原health先float32减法再float64汇总的MAE/inbag MAE（原1e−9守卫未放宽）。population终端项按实际每critic mask与terminal128权重、全部有效replay分母计算；同924旧终端的奖励和mask逐值固定，单列旧分母，排除只因replay增长稀释。

|量|完整30|完整31|
|---|---:|---:|
|终端population加权loss贡献|.270694711|.559652621|
|top1占终端项比例|26.8377%|70.0533%|
|top5占终端项比例|57.3601%|90.1831%|
|当前轮新增30终端占终端项|29.2566%|90.0457%|
|同924旧终端mask加权SSE|2357.974399|500.973296|

终端项升为2.067468倍，但同924旧终端SSE降为原21.2459%（下降78.7541%）。用原30分母计算31旧样本项仍只有.057518154，使用新分母为.055709456，改善不是仅靠分母变大。新增31的30终端项.503943165，占31终端项90.0457%。

最大两条均为31新样本：short0600 replay index1304222（0-based）占70.0533%，终端reward−28.432058，5critic Q为−5.341111/+7.262658/+4.718761/−9.686090/−12.065763，mask全1；short0200 index1304225占16.4815%，reward+23.843508，预测仍偏低。它们的误差方向不同，不能仅从整体均reward或MAE断定所有拟合都恶化。

独立保存值review重算每行贡献、top比例、同924 SSE、旧/新分母项并核输入hash，1e−14算术守卫通过；图已查看。完整值存cycle30_terminal_values.npz和cycle31_terminal_values.npz。这里是冻结端点的终端population项，不含普通非终端TD，不等于历史GPU随机minibatch loss，也不能声称已解释在线loss增加的某个因果百分比。不据此更改terminal128、LR、特征、奖励、采样分布或推广辅助权重。

## 预登记固定954样本跟踪完整32

B/runs/vmc32_terminal_anchor_followup_20261027_v1；原等待1497589，7200秒有界。32仍运行时固定31全部954终端观测/action/reward/mask与focus1304222，PLAN SHA d5b81c5dd4215af75f1788104e785fbeaf332240bc46d1cd131e7e8c08b37225；旧31预测直接复用本轮保存值，不重复31前向，也不根据32结果重选样本。

仅完整32 FINISHED/REVIEW后固定准确32父/health/hash，CPU52恢复全部agent权重作只读前向；预期984终端，其中954旧行输入/奖励/mask逐值相等，30新行单列。检查旧954 SSE、原31分母下的贡献和focus恢复情况，网络/前向RNG/父checkpoint不变，0优化/新物理/replay写入。新跟踪源码AST、准确parent32/anchor31/954→984与focus断言核验通过；实际32推理尚未执行。原等待失败不自动延长或重跑。

这个跟踪检验当前新误差是否在既有32训练中得到拟合，不把回归均值或单条改善当作策略性能/整体收敛的因果证明。最终冻结全30仍独立进行。

## 正式任务与同步

Direct20 learner46632，归档46745/review46750，21准备87882/原20CPU调度87883保持。参数32 I980495/A980496/V980497，归档980500/review980501；33准备1007211/调度1007212只完整32后check-only，无自动33。固定30–32稳定性2830862及冻结32全30准备639955保持，不重复。新VMC跟踪1497589仅只读评估，不创建训练任务。

本轮原20/32持续推进，GPU1一次瞬时0后原learner与steps继续增长，随后四卡瞬时67/84/83/80%；没有据单次瞬时0重启训练或填负载。上一轮固定纯20/32窗口56.15/66.9/65.9/66.45%仍只代表当时，本轮未重复采窗口。

重新query/fetch/read远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变。三新源码AST，已完成真实CPU前向及独立保存值审查；跟踪32仅预登记，尚无完整32结果。小证据docs/evidence/rl_vmc31_terminal_followup_20261027含完整保存终端值、原输入hash、原PID、预登记与源diff（以JSON包裹原diff文本保留字节语义）。指定ESN仍缺、GitHub认证仍待，已问勿重复。Goal active。

科学提交d76398570cd3b83852980a36f71f02c18311f68b本地完成，push仍GitHub Username认证失败未发布。24成员完整小证据SSD B/repository/RL_VMC31_TERMINAL_FOLLOWUP_20261027_002336/FULL_SMALL_EVIDENCE.tar.gz，965856字节，SHA256 995ff3b980e67bd535dd6ae8e68fc32d8ee47d0aaba33244a72c5f774784a615，逐成员size/hash核验通过。HDD RL_VMC31_TERMINAL_FOLLOWUP_STATUS_20261027_002336/HANDOFF.md与LATEST_RL_HANDOFF.md入口已核验，大state/raw仍SSD，非HDD/arm1全备份。
