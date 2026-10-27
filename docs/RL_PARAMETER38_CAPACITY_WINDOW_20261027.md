# 参数38接续、37完整审查与Direct24–26窗口登记

2026-10-27。Goal active、无子agent；整体健康收敛尚未达到。前轮[Direct24容量准备](RL_SERL24_CAPACITY_PREPARATION_20261027.md)结果保持，已完成辅助验证不重复。当前原进程/进度以本轮FINAL_LIVE_STATUS.json与原run为准。

## 参数37完整结果

三路各30×55秒完整、无abort、新增41250条；全旧回放字段/历史/2m marker保留，全部新reward重建误差0。完整REVIEW/FINISHED、网络只读health及曲线通过。保存optimizer日志scalar均值核验，不把finite当健康稳定。

| 方法 | steps / updates | Task / Strict（30） | reward均值 | 末1000 loss | terminal MAE / in-bag MAE |
| --- | --- | --- | --- | --- | --- |
| Impedance | 1564500 / 1559501 | 18 / 17 | -2.358542363 | 2.997857029 | .901673 / .350376 |
| Admittance | 1563500 / 1558501 | 13 / 11 | -13.487784162 | 2.325373755 | .932620 / .516331 |
| VMC | 1564500 / 1559501 | 17 / 17 | -2.852235784 | .805686247 | .508731 / .204816 |

首1000→末1000 loss分别2.503240→2.997857、2.258132→2.325374、.716063→.805686；全轮均值2.605299/1.881603/.724675。I仍高且末段升高；A先下降后末段升高；V末段小幅升高。原36–38固定窗口待38结束，不提前判稳定。

完整37父SHA：I52d5fc29f83beee550895d9e57aa85c83386aa349d6e69aecf32aa3daa774aa5，A4fb05a82735694ab3f181345a92d4bb1dab08c7271ca0e49306dc7057f585726，V3a6afc2b6b1f47dedc29fe739480e6e85287a5b80b82cef31ac6a7700d39e9bc。

## 36→37保存条件配对

六份episodes输入hash/完整30条件/MJB一致与全均值差核验；证据PAIRED36_37_OUTCOMES.json，0新物理/优化。以下是保存值算术，不证明随机性或策略学习的因果份额，也不修改gate/reward或重跑失败条件。

阻抗均值只+0.051816868，却有两个Strict互换：short0100假→真贡献+1.802585020，short0600真→假贡献−1.807935765。两者Task均真；不能用接近不变的均值推断条件表现不变。

导纳均值−4.950470276；long0200 Task/Strict真→假贡献−1.689338987，short0100 Task仍真但Strict真→假贡献−1.725475102，short0900 Task/Strict真→假贡献−1.687784238。其他条件合计抵消一小部分，所有条件均保留。VMC无Task/Strict切换，均值−.010832075。

## 参数38已从完整37接续

三check-only全learner/replay/RNG和next65536精确，PRELAUNCH读完整37/health/图/配对结果后正式启动一个有限38。原物理/MJB/gate/filter/actuator/dt、SPT reward、输入、batch65536/UTD1/terminal128/projection/目标reduction/actor/LR、30pool均保持。仍必须capacity replay+pair learner，历史2m入口23不重标，所有旧行保留。

启动1793072651.17，I1714249/A1714251/V1714253；startup1714318、archive1714320、完整review1714322，run为parameter_capacity_pool30_cycle38_20261026_v1。原37 learner/归档/审查及原38准备140023/140026完成勿重启。实际startup结果见补充，不把check-only当actual startup。

新39仅恢复等待1752770/原38审查CPU调度1752771，runs/parameter39_preparation_registration_20261027_v1；7200秒等原完整38审查后check-only，没有自动训练。五入口同时替换/AST/准确38父与39目标/原65536/CPU39/历史容量23守卫通过，实际恢复尚待。正式39仍须读完整38结果与原36–38审计，不凭准备脚本自动派发。

## Direct容量后的固定24–26观察窗口

新只读waiter1470790，runs/serl_capacity24_26_reward_stability_20261027_v1；审计源码audit_serl_capacity24_26_reward_stability_20261027.py。登记时23仍训练中、0完成条件，24/25/26均未启动；所有窗口结果尚未知，baseline23策略已经在训练，明确部分前瞻状态。不替换已完成20–22结论，不重跑原窗口。

固定23为配对baseline、24–26为稳定性窗口；原5%相邻与首尾均值变化、近零1保护、5000次按类别配对bootstrap保留，seed2026102742。输出完整30条件均值/Task/Strict/早停/配对变化/条件敏感区间/斜率、loss/温度及终端和32步TD诊断，保留失败分母，不新增Task或policy-invariance阈值，不自动宣告收敛/停训。

明确23原1m→24的2m容量变化：24–26必须同一持久marker和历史entry23，学习器、30条件、输入/奖励/clock/32步目标/batch合同一致。23→26的配对变化不能分离容量、策略和训练时间的作用；分类bootstrap不是独立训练seed或冻结策略置信区间。未来review的methods.direct.replay_capacity需提供passed/new_capacity=2m/marker，25/26监控须保留该字段并正确处理继承2m父，不能照抄24的仅1m入口断言。

等待21600秒（因尚需23结束和后续三个有限周期），无自动延期/训练/停训。计划固定23路径为serl_multistep_batch65536_cycle23_20261026_v1，24–26为serl_capacity_batch65536_cycle{c}_20261027_v1及同名review路径；各完整REVIEW/FINISHED/DIAGNOSIS后才登记全部实际输入hash、执行一次统计。AST/--help/原定义/未启动状态/hash与原waiter live核验通过；实际统计尚未执行。

## 仍在运行与后续顺序

Direct23原257351/archive257407/review257409继续；24容量恢复等待1003919/释放CPU调度1003920保持。完整23后先沿用原准备结果，读full23科学审查/check-only后再启动有限24，核actual startup与1001000边界。前轮容量验证776433和replay-only35329已结束，禁止重跑或把辅助state推广。

原参数36–38稳定性2889814继续。冻结参数32 I2466385/A2466386/V2466387与根2466388继续原90×55秒、动作seed2026102638，0优化/正式replay写入；完整矩阵尚待，已完成回合不重跑。新混合23/38/冻结32 observer1752772固定60样本、等actual startup后运行一次；先查PROFILE，不重复采样，不以新窗口隐藏37→38的真实空档。

HDD配额满，本轮小证据/HANDOFF/收据在SSD，既有HDD LATEST只更新指针并回读；不称大型checkpoint/raw或arm1全备份。远端同步、提交与归档结果另记，不重复索取GitHub凭据或指定ESN。Goal active。

实际38 startup1714318已完成，I/A/V新增1000/1000/2000至1565500/1564500/1566500，旧1564500/1563500/1564500全部回放字段/history/optimizer配置/2m marker/30MJB/sampler/action/clock和新reward0误差通过。实际check-only与新增startup是两项核验，均已通过，勿重跑。

混合23/38/冻结32原observer1752772已完成，60样本/65.766757秒，GPU0–3均值[54.8, 73.63333333333334, 73.86666666666666, 73.33333333333333]%，逐样本七原PID身份保持，保存均值独立核验通过。非纯正式吞吐或每瞬时50%保证，不抹去37→38空档；勿重采。远端main a3e9e04/baseline f6e8f8c本轮重新fetch/read未变。
