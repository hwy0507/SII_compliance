# 完整68审查与准确续训69

2026-10-28，Goal active。实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD根
`B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `B/env/bin/python`。
承接[原68连续观测和排名](RL_PARAMETER68_WAIT_RANKED67_20261028.md)。整体训练收敛仍未证实。

## 完整68

原三learner1065436/1065438/1065440（start41034355）全部自然结束，未重启。
`B/runs/parameter_capacity_pool30_cycle68_20261026_v1` 的完整归档/审查通过；各30×55秒、41250新增、noabort，
旧67的2800398/2801000/2802000 replay全字段和history保持，冻结奖励复算误差0，网络/优化器有限。
奖励复算来自物理区间journal与冻结实现，不冒充独立原始子步物理重建。

|方法|steps / updates|reward均值|Task/Strict|critic首→末1000|critic均值 / max|actor首→末1000|
|---|---|---:|---|---|---|---|
|I|2841648 / 2836649|−4.020219919|17/16|1.894274253→2.156668372|1.856950154 / 32.325042725|25.770858643→26.263010462|
|A|2842250 / 2837251|−8.521150101|14/14|1.289235631→1.187916865|1.234552887 / 10.320878983|−9.133686520→−9.085063750|
|V|2843250 / 2838251|−4.604088252|17/16|.736125171→.944134060|.759054288 / 24.599201202|−13.334110606→−12.999248530|

`B/runs/parameter68_loss_20261028_v1` 完整loss/paired/独立复算/实际loss.png审查完成。
I/V末段critic尖峰及末均值升高，三个actor净上移，A先降后升；数值有限不等于稳定。
未增加有限尖峰阈值或零终端误差门。原68–70窗口只完成68，不能提前给窗口通过/失败结论；端点保持。
原65–67 I/A失败、V仅描述性reward通过，旧59–61/62–64失败与历史I56–58/V53–55通过全保留。

完整health `B/runs/parameter_capacity_pool30_cycle68_review_20261026_v1/health/DIAGNOSIS.json`，
I/A/V终端2065/2064/2064；in-bag MAE .385741169/.182953109/.191674707，
sampled TD MAE .249823968/.204413328/.141046573，网络未改、0优化。实际training_diagnostics.png已审，
右上长标题末端有裁切但数据可读；V末段alpha升高及loss时序关联不是因果证明。

完整checkpoint位于 `B/runs/parameter_capacity_pool30_cycle68_archive_20261026_v1/{method}/cycle_00068.pt`：

- I SHA256 `6e0d22beaefe11f0c6236e90f0abefa6dea583ca3973b6e0778cf024ae7b1b0a`。
- A SHA256 `e6378e4dade785ef436f14ca389cefb2afa6f69dbaa26a48240ce3b9857dcdaa`。
- V SHA256 `19741b4b0fb419cc8111f557b0878b41e0227630a38e3b58b61c06240885331d`。

## 全标签67→68

`B/runs/parameter_task_label_audit68_20261028_v1` 的FINISHED68、COMPLETE67_68及SAVED_REVIEW完成。
180 rollouts/90 reward对、全计数与独立loss统计吻合；没有遗漏Task-only变化。

- I short0600 Task保持真、Strict真→假，外穿透 .197559748→.243067698 mm。
- A short0600 Task/Strict均真→假，外穿透 .189113375→.229946417 mm；long0200、short0900恢复Task/Strict。
- V short0600 Task保持真、Strict真→假，外穿透 .173536027→.204827931 mm。

本轮三路physical-valid均29/30，不能把noabort或Task成功当成全部physical-valid。
全部失败保留，原.2mm门没有更改。

## 全2034固定终端与原67排名跟踪

`B/runs/{vmc,admittance}68_terminal_anchor_followup_20261028_v1` 的FINISHED/REVIEW/
SAVED_VALUES_REVIEW及实际follow68.png/PLOT_INSPECTION完成。全部固定输入/动作/reward/masks精确，
健康值重现、权重与前向RNG保持，0优化/物理/replay写入。图含所有旧2034及原focus，V小误差点文字有重叠，数值另存JSON。

|方法|全2034旧SSE 67→68|变化|旧贡献 / 新30贡献 / 全2064贡献|
|---|---|---:|---|
|V|4748.245926948→935.692793729|−80.293927%|.048200028967 / .150377119690 / .198577148656|
|A|3370.449233136→804.199541674|−76.139693%|.041424518476 / .001320288602 / .042744807078|

V原五focus2050526/2299142/2046571/2423133/2423122全部改善，SSE分别
18.647175→8.083281、351.402854→6.108994、3.068889→1.468263、1826.420823→74.557916、12.701238→5.782801。
A原66 short0600/index2752093从572.396931降至31.453106；它是旧固定样本，不能与新68失败回合混为一谈。
V新30误差贡献仍高，不能用旧样本改善宣称整轮稳定。

本轮68完成前另登记只读保存值跟踪 `B/runs/vmc68_ranked67_terminal_followup_20261028_v1`，
PLAN SHA `5541a1e710e94cdc1695d25b5c99f5295c0dbcb1e319735b34f340af504a56b9`，
原waiter2566624/start41302356自然完成。沿用已验证全68前向数组，0额外前向，保留完整67事后排名的全部2034行，
固定前2 index2423133/2299142，不改原五focus。独立标量/向量审查通过，1240改善/794退化，
前2的1826.420823→74.557916及351.402854→6.108994不替代全体结论，无因果/新门。
真实提前调用被Incomplete68拒绝、无REVIEW输出，原始拒绝证据保留；映射逆变换/覆盖计数/显式字段适配/AST通过。

## 实际续训69

三路准确68 full learner state/replay/下一65536恢复检查全exit0，30sampler/4m追加/历史23与47 markers保持。
`B/runtime/prepare_parameter69_20261028_v1/DECISION69.json`绑定42证据，SHA256
`8ce8b0d303375b2f2a9d169436f1b3a28073431b6c28912bfc8e01ad933beeb5`。
完整68审查后决定一个配置不变有限69，无自动70训练；Direct33仅原队列经验数值收敛、Task/Strict0/0，Direct34false。

2026-10-28 20:15:53 UTC实际启动 `B/runs/parameter_capacity_pool30_cycle69_20261026_v1`：
I3088968/A3088970/V3088972，start均41426931；GPU1/2/3，CPU13–25/26–38/39–51，各30sampler。
归档3088977/start41426932，startup3088980/start41426932。保留完整优化器/RNG/replay/history，
原reward/gate/物理/LR/masks/terminal128/batch65536/UTD1不变，没有辅助权重或reset。

完整69 loss实际部署成功 `B/runs/parameter69_loss_20261028_v1`，waiter3093145/start41428217，
PLAN SHA `055ba0a0437527a50361ee8fd1c6ded9cf783e46b1252c1cd7d05b9f60eb40b9`，CPU54/7200秒。
49–68历史保持追加69、paired68→69；部署逐项核验DECISION全部证据及真实69三learner身份，四原源hash保持。
原68–70 waiter1085142/start41039557、PLAN e3a50567继续，未提前改变端点或宣告窗口结论。
69全标签/V+A新锚点和70仅恢复尚未准备，完整69结果待。

## 运行观测与同步

原68完成边界观察2493123/start41289221：19:52:56–20:12:56共41样本/1200秒，三原learner全部自然完成，
归档及等待器按原任务推进；观察计时结束不是科学失败，没有重启。独立REVIEW通过。
234条guard采样最低71/66/66/65%、低于50全部0/maxgap5.277774秒；包含合成保载，非瞬时保证或纯训练吞吐。
科学完成后也继续v5；实际控制在/tmp，旧v4 STOP仍在共享SSD，当前并非跨重启服务。

开工实际fetch/read main4c952453/baselinef6e8f8c。收尾main0f3e2c45的另一主机非RL棍组审计、
全30有一失败/学习被阻止、垂向阻尼有限对照的新日志与报告已读并fast-forward保留；没有本机冻结RL源变化。
无子agent，Goal active。大checkpoint/replay/raw留共享SSD；HDD仅原地紧凑交接入口，不称HDD/arm1全量备份。

## 20:20 UTC 实际启动审查与归档收据

69实际startup REVIEW通过，SHA256 `9f459067ed78dd1c999cb4521e7a01c76b581e558b94048c116f516ae3d3830e`：
I/A/V实际检查新增1000/1000/2000，旧2841648/2842250/2843250全部replay/history/优化器参数保持，
新reward复算0，30sampler/MJB、原配置与CPU分配核验。不是仅check-only或静态准备。
20:20:47快照三learner原身份live，steps2844643/2845229/2846239，尚无完整/失败；archive/loss69/原68–70和五guard均live。

完成边界观察之后至本快照另92guard采样，最低72/68/69/68%、低于50全0/maxgap5.253261秒；
即时GPU78/70/73/72%。含合成保载、非瞬时保证；科学完成也继续v5，非跨重启服务。
快照/原始样本/复算位于 `B/runtime/parameter68_complete_publication_20261028_v1`。

共享SSD小证据包 `B/repository/RL_PARAMETER68_COMPLETE_20261028_202047/SMALL_EVIDENCE.tar.gz`，
197成员/2121265字节，SHA256 `7817f3ffdf1884a25b2226af71a805d79d8bfbc353ff2ad0101b601a36008dee`。
逐成员字节/hash、Python AST、tar回读核验通过，显式收本轮小证据和实际69运行依赖，未递归收693个旧工具。
[收据](RL_PARAMETER68_COMPLETE_SAVE_20261028.json)，[清单](evidence/RL_PARAMETER68_COMPLETE_20261028/MANIFEST.json)。
大checkpoint/完整replay/raw及startup大快照仍共享SSD原路径，不称HDD/arm1或完整环境备份；
原有HDD LATEST只原地更新精简入口。
