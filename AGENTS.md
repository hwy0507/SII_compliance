# 本仓库的持续工作约定

## 最新RL状态：2026-10-26 参数17、Direct batch65536第13周期运行中

原Goal active，未健康收敛；最新交接[RL_PARAMETER17_SERL_BATCH13_20261026.md](docs/RL_PARAMETER17_SERL_BATCH13_20261026.md)。本段覆盖下方16/12快照。无子agent，物理/SPT与完整正式state保持。
完整参数16三路各+41250、30完整无abort，I18/18、A11/9、V17/17各30；reward−.533626/−17.182676/−2.825392，末1000loss1.869/6.085/1.976，termMAE1.063/.745/.829，Q均−8.378/+13.613/+26.576。全旧prefix/history/markers/MJB与新reward精确，health/图完成；导纳退步，未收敛。旧4072251/2/5及归档/审查已结束。
完整Direct12 524532steps/4156264critic，0/30、reward−31.019692、30完整无abort；全新单步/32步目标精确、旧483282raw/derived/ready/history保留、pending0。terminalMAE.093513/max2.961039，32步TD.079125，末loss.020545，Q−20.592；全state不变与图审查通过，仍全部approach。旧4121413与归档/审查已结束。
正式参数17 I1280294/A1280295/V1280296，GPU1/2/3、原CPU组各12sampler，B/runs/parameter_batch65536_cycle17_20261026_v1，从准确完整16全state接续一个17、设置不变。通用driver校验连续登记链至13；三check-only/实际各1000新增全prefix/history/marker/MJB/action/clock/reward0误差通过。归档1328339、完整17审查1328342，无自动18，必须pair_class恢复。
正式Direct13 PID1280297，GPU0/CPU0、30sampler共享1–12，B/runs/serl_multistep_batch65536_cycle13_20261026_v1/direct，从准确完整12全state接续；仅batch32768→65536，官方8:1/10critic/random2/noentropy/32步/actor48与gather+transfer保持。依据已完成正式11两臂probe，非辅助权重推广。check-only全state/下批/RNG/两构造相等与负守卫通过；真实1000新增/8000critic、旧524532全prefix和145mature+855pending/30MJB精确。归档1328360、完整13审查1328362，无自动14。
预登记纯正式180样本193.549秒GPU58.45/75.71/74.89/74.27%，四原learner全live；D/I/A/V10.628/24.779/25.348/25.213steps/s。该窗口均值全≥50%，非瞬时或永久保证。Direct吞吐较旧23.416下降54.6%，不能称提速。profile1364508已完勿重采，后续混合推理不替代。
冻结参数15九条全部审查完成，三路Task/Strict2/3、被动carry失败，动作误差0/fullstate不变/物理filter torque通过；原协调/评估全部结束勿重跑。I/A/V长期完成53.08/38.08/31.48s，接触合规14.96/100/100%，被动/短期无接触NA，非最终排名。
新配对只读1462229已完：导纳丢Strict短0100/0000/0900及长0400，无新增；短0000/新Task成功0600物理无效。Direct11/12均30approach，前160public0 .4518→.3571，0是nominal、更大减慢WBC；非因果证据。
新冻结随机Direct12协调1521445/evaluator1535401，B/runs/serl_cycle12_stochastic_representatives_20261026_v1；等待纯正式profile后已实际启动，GPU0低优先级/CPU52、原三代表最多330万子步0优化。独立seed2026102612，同seed动作相同/异seed不同/fullstate不变gate通过；最终物理/动作/折扣回报与Q诊断待完成，不重复。不是无偏期望回报校准证明。
远端仍dbb1d76（baseline f6e8f8c）；此前573d0469/ac6a028仅本地，GitHub认证待恢复，用户已被询问勿重复。HDD配额满，仅小交接/收据；完整小证据和大产物在SSD，不称HDD/arm1全备份。先查原17/13与随机评估，完成审查后及时衔接最新正式全state。

## 最新RL状态：2026-10-26 参数16、Direct单次传输12运行中

原Goal active，未健康收敛；最新[完整交接](docs/RL_PARAMETER16_SERL_TRANSFER12_20261026.md)。本段覆盖下方15/11运行中快照。无子agent，物理/SPT与完整正式state保持。
参数15已完整审查：I657000/652001、A656000/651001、V657000/652001，Task/Strict17/17、13/13、17/17，reward−2.227365/−10.361746/−2.855253；30完整无abort、新reward0误差/全旧prefix/history/markers/MJB通过。termMAE1.108/.853/1.375，Qmean−10.207/+1.427/+23.785、末loss2.339/18.577/3.443，A/V值仍移动，未收敛。旧2763218/9/20、归档2860572/审查2860589结束勿重启。
正式参数16 I4072251/A4072252/V4072255，GPU1/2/3与原CPU组各12sampler，B/runs/parameter_batch65536_cycle16_20261026_v1；准确15全state续一个16，不改batch65536/UTD1/terminal128/projection/Imin+A-Vmean/actor min/原LR。三check-only全state/重复恢复/负守卫通过；真实I/A2000、V3000新增全旧state/replay/history/marker/12MJB/动作/clock/reward0误差。归档4140193、完整16只读4140196；无自动17，必须pair_class恢复。
Direct11已完整483282/3826264，0/30、reward−31.241907、30完整无abort；全41250新增单步与派生目标精确，旧442032raw/derived/ready顺序/history保持、pending0。termMAE.078471/max4.312935，Qmean−20.636024，32步TD .068467；完整state只读不变/图已看，任务仍失败。旧2858708/3078520/3078535结束勿重启。准确11父SHA bd4e5de51a8e9cebe63fa7240a1e79427b1c81b1c0510be6dc51a0adee491195。
正式Direct12 PID4121413/GPU0/CPU0/30sampler共享1–12，B/runs/serl_multistep_transfer_cycle12_20261026_v1/direct，准确11全state续一个12，仅部署已等价核验的单次batch传输，gather与官方10/2/noentropy/8:1/batch32768/32步/actor48保持。新check-only全state/replay/下一批两batch构造/RNG相同0更新；真实1000新增/8000critic、旧483282前缀与新actor/action/clock/reward/30MJB及184mature+816pending全通过。归档4140210、完整12只读4140212，无自动13；须保留clock/multistep markers完整成熟顺序。
预登记180样本194.016秒纯四正式GPU48.43/75.82/74.29/74.28%，D/I/A/V23.416/24.967/25.518/25.333steps/s；原PID全live，Direct仍未50%、传输优化未显示新在线提速。观察4170654结束，不重采挑好结果；后续混合负载不替代。
只读正式11动作偏好诊断已完成，1024近期固定状态、0更新/物理；mode比replay Q均值高.0192、比公共全零高.0319、critic std.0438，七通道Q梯度绝对均值.0086–.0103。未执行候选、非因果物理效果，不改动作/nominal混合。原105292已完。
新有限batch32768/65536对照B/runs/serl_cycle11_batch65536_probe_20261026_v1：probe231521、独立review266278，准确11全state/replay/RNG每臂2000outer，共32000critic+4000actor、0新物理/不保存推广权重。两臂与独立审查均完成、原231521/266278退出、图已看。末termMAE .07618→.07228、max4.189→3.509、32步TD .07052→.07081、平均outer .04270→.11405s（约2.67倍，首编译单列）；候选未部署12，非在线收益，不重复。
冻结参数15三固定代表：B/runs/parameter_pair15_fixed_20261026_v1，I354445/A354448/V354759协调，I/A evaluator354447/354805，CPU52/53/54 nice19、GPU1/2/3推理，每路3例最多330万子步0优化。V已接续evaluator544452使用54，三个原协调继续，勿重复。新evaluate_pair_parameter严格pair_class/全部markers与全state恢复；最终物理/filter/torque/动作/状态审查尚待，非全30最终排名。
本轮实验提交ac6a028仅本地，push因编辑器GitHub凭据提示阻塞，远端最后核验仍dbb1d76；用户已被请求恢复登录，勿宣称本轮GitHub已发布。HDD配额仍满；本轮完整小证据SSD，大产物仅SSD。不要宣称HDD或arm1全备份；后续先收原16/12/有限probe/冻结15。

## 最新RL状态：2026-10-26 参数15、Direct等价gather11运行中

原Goal active，未收敛；最新交接[RL_PARAMETER15_SERL_GATHER11_20261026.md](docs/RL_PARAMETER15_SERL_GATHER11_20261026.md)。本段覆盖下方14/10运行中旧快照，无子agent，物理/SPT/完整正式state不变。
参数正式15：I2763218/A2763219/V2763220，GPU1/2/3、原CPU组各12sampler；B/runs/parameter_batch65536_cycle15_20261026_v1，准确完整14全state续一周期，batch65536/UTD1/terminal128/projection/Imin+A-Vmean/actor min/原LR不变。三check-only与真实启动prefix/history/marker/MJB/action/clock/reward审查通过，归档2860572、完整15只读2860589；无自动16。最新各24/30条件完成，先查原PID，不重复。
Direct10已完整并审查：442032steps/3496264critic、Task/Strict0/30，reward−32.757649，29完整+passive0500第1222动作global穿透abort。全部41097新单步与多步目标精确、原prefix/history保持、pending0。termMAE.097123/max5.88913、Qmean−20.76551，任务仍失败非收敛。旧1595728/1621561/1660936已退出，勿重启。
Direct正式11 PID2858708/GPU0/CPU0、30sampler共享1–12，在B/runs/serl_multistep_gather_cycle11_20261026_v1/direct，从准确完整10全state接续；只部署上一轮等价gather，官方10/2/noentropy/8:1/batch32768/32步/actor48保持。新check-only完整state/replay/下一采样精确；真实7000新增、旧442032单步/派生前缀与全部新映射/clock/reward/6070mature+930pending通过。归档3078520、完整11只读3078535，无自动12。
Direct须SerlMultistepLearner+replay_class保留clock/multistep markers、成熟顺序与pending；完整父ready按成熟顺序，不必天然sorted，审查须保留顺序并验证全覆盖，不能改采样器。
纯正式60样本64.30秒GPU49.05/78.42/74.13/72.20%，D/I/A/V23.716/25.504/25.053/24.711steps/s；Direct仍未达50%，后续冻结/辅助占用不替代。
新单次batch传输候选serl_multistep_batch_transfer：6批pytree/11负输入/完整下一8:1更新state与metrics精确，16critic+2actor辅助不保存权重；5轮微基准5.135→4.666ms，未部署11，不证明在线达标。原3236999已完勿重复。
只读条件配对：参数13→14退步来自少数主动条件，三路passive0/10；Direct9/10全30均approach，前160动作public0均值.432→.584（增大减慢WBC），非因果证据。原3354962已完。
冻结正式10三固定代表：B/runs/serl_cycle10_fixed_representatives_20261026_v1，协调3165841/evaluator3166321，GPU0低优先级、CPU54、0优化；已完成，原两PID退出，FINAL_SCIENTIFIC_REVIEW/FINISHED齐全；三例各1375动作/110万子步/完整55秒，Task/Strict0/3、均approach、无abort/无人接触。全部动作误差0与物理/filter/torque/MJB/完整state不变通过，不重跑、不当全30最终结论。
仓库仍SSD链接；HDD配额受限，完整小证据在GitHub/SSD，大型checkpoint/轨迹仅SSD，不能称HDD全备份。远端独立非RL main9dd59f2已快进保留。

## 最新RL状态：2026-10-26 参数14已完成、Direct多步目标10继续

收尾覆盖下方运行中快照：三参数14全30完整无abort，Task/Strict I17/16、A11/11、V17/16，reward−4.076/−13.729/−4.559，较13均退步。全新reward/旧prefix/history/配置/markers/MJB审查通过；健康诊断1286970也已完成退出，termMAE1.297/.835/1.314、Qmean−13.366/−44.672/+19.408、末loss3.389/30.123/6.026、Itermmax113.210，未收敛。三正式1254686/1254688/1254691与归档1286930已结束，勿重启；下一参数父为parameter_batch65536_archive_20261026_v1下准确14，SHA见交接文末。Direct1595728仍运行10，无参数15/Direct11登记，Goal active。

## 最新RL状态：2026-10-26 参数batch65536正式14与Direct多步目标正式10运行中

原Goal active，未健康收敛。最新[完整交接](docs/RL_BATCH14_AND_SERL_MULTISTEP10_20261026.md)，覆盖下方“无正式learner”。无子agent，物理/SPT/MJB/gates/filter/dt不改。
同准确正式13全state，batch32768vs65536三方法各两臂5000共30000辅助完成，不推广权重；termMAE I1.650→1.351/A.722→.668/V1.197→1.109，单更新耗时约1.9倍，非在线收益证明。原1076194/6/8及review1183654已完勿重跑。
参数正式14 PID I1254686/A1254688/V1254691，GPU1/2/3、原CPU组各12sampler，从准确完整13全state续一周期；仅batch65536，UTD1/terminal128/projection/I min+A/V mean/actor min/原LR保持。必须pair_class恢复三marker。
三check-only完整state/重复恢复/负守卫通过；真实各1000新交互全旧replay/history/配置/marker/12MJB/亲和性/参数input/clock/reward0误差审查通过。精确修改原trainer一处batch守卫，未改冻结原文件。
归档1286930在parameter_batch65536_archive_20261026_v1，完整14只读1286970在parameter_batch65536_cycle14_review_20261026_v1；无自动15，先查原PID，不重启。
Direct同准确clock9一/32步对照各2000outer，总32000critic+4000actor辅助完，0physics/不保存推广权重。400935行/300episode按6journal重建，全部clock/相邻state/terminal与1步还原、独立标量32步回报检查通过。
termMAE对照.559→32步.315、max42.176→12.294、Qmean27.107→−20.761；1步TD .064→.136，非当前策略无偏回报，非在线恢复。原1200322已完勿重复。
v1 float32乘法后累加与float64标量gate不符、v2缺CUDA_VISIBLE_DEVICES被单GPU守卫拒绝，均0更新保留；v3正确环境完成。独立review初用无JAX环境失败，serl_env只读重审通过，无重算。
新serl_multistep_state_adapter持久multistep_target_extension；原全部网络/Adam/RNG不改、原单步replay全字段保留，另存32步reward/bootstrap/endpoint/length及mature/pending。在线按stream成熟/终端冲刷，只采mature；actor48不看未来奖励，clock marker仍保留。
严格SerlMultistepLearner和replay_class恢复，旧clock/base loader会丢新目标，禁止替代。仅完整周期恢复，partial待处理流不可伪装新物理episode；本阶段容量环绕拒绝。
preparation v1在probe review缺失时0更新退出；v2完整400935派生/剥新区后全旧state/replay精确、105交错流在线行/每步恢复与采样/负守卫/两次恢复下一8:1更新精确通过；16critic+2actor gate不推广。
prepared9 SHA6bf4ec143049657f5a071569ce24d22ecca906e1446d23c1e9b6b88be4ccc44f，路径serl_multistep_preparation_20261026_v2/prepared_cycle09.pt，正式9无更新扩展。
Direct正式1595728/GPU0/learnerCPU0/30sampler共享1–12在serl_multistep_cycle10_20261026_v1/direct，仅一个10，无自动11；官方10/2/noentropy/8:1/batch32768与零示范保持。
check-only全prepared state不变/负守卫通过；真实1000新增/8000critic、全旧prefix/history/config/30MJB/亲和性/actor48/action7/clock/reward0误差、178新mature+822pending逐项审查通过，启动无terminal覆盖。归档1621561，完整10只读1660936。
纯四正式60样本63.92秒GPU44.53/70.62/73.53/74.87%，全原PID live，D/I/A/V21.213/23.419/25.171/25.312steps每秒。后三卡达50%，Direct仍未达，不以混合辅助替代。
Direct45秒外部栈发现回放索引/复制约28%叶样本；新跳过随后覆盖的单步reward/nextobs gather候选28批全字段/RNG相同，5轮CPU微基准11.147→7.600ms，0optimizer/physics。另16critic+2actor有限gate证明完整下一update的全state/metrics/RNG相同，无权重保存；未部署当前10，下一完整边界登记及在线吞吐仍待。
HDD4GiB配额写入失败，完整仓库7296文件逐hash复制验证后迁至SSD B/repository/SII_compliance，原HDD仓库路径为目录链接，Git历史不丢；B/repository/RELOCATION.json。HDD仅独立小证据备份，大产物仍SSD非arm1全备份。
收尾HDD未压缩/完整压缩备份仍受配额阻止；仅10新增源码+报告的ESSENTIAL_BACKUP.tar.gz与HANDOFF.md已在HDD核验，完整133文件包在SSD repository/RL_BATCH14_MULTISTEP10_29d142e8.tar.gz及GitHub。勿称全证据HDD备份。
收尾四正式仍运行，最新LIVE_STATUS见证据目录。先收完整14/10审查再决定下一阶段；后续父必须最新正式归档，不能回退。健康收敛/最终冻结/ESN/SPT/四卡要求仍待。

## 最新RL状态：2026-10-26 参数13与Direct critic-clock9均已完整审查

原Goal active，未健康收敛；最新[完整交接](docs/RL_PAIR_MEAN_CYCLE13_AND_SERL_CLOCK09_20261026.md)。
本段覆盖下方“无正式learner”旧快照。物理/SPT/MJB/gates/filter/dt不改，无子agent，保留全部正式旧state/history。
正式12同parent/state/抽样流的min-vs-mean target pair诊断30000辅助完，0physics/不存推广权重；
A absQp95 461→385、V282→252，但termMAE min→mean I1.635→1.795/A.913→.991/V1.367→1.392，非全面修复。
v1第二次恢复foreach检查误报，1辅助更新后失败保留；幂等修复后minimum完整更新state/RNG/metrics相同，v2另2gate更新。
新正式parameter_pair_reduction_cycle13_20261026_v1 I3841250/A3841253/V3841255，原GPU1/2/3、各12sampler原CPU组；
从正式完整12全state续一个13，I保留minimum、A/V target改mean，actor仍minimum；terminal128/projection/batch32768/UTD1/原LR不改。
必须pair_class恢复新target_pair_reduction marker，旧exact/projected loader会丢新规则，禁止替代。
三check-only除marker完整state不变/重复加载/负守卫通过；三路真实1000新增完整prefix/history/配置/markers/12MJB/亲和性/input/clock/reward0误差通过。
归档3882892，parameter_pair_reduction_archive_20261026_v1；13只读4030423、三health齐全，无自动14。
Direct clock正式迁移v1随机模板转换gate失败0更新保留；v2先加载正式8再扩展，全部旧state/Adam/RNG/history精确保留，
仅8新零叶与replay追加时间列，旧366962行全字段可恢复；actor随机/确定输出相同、1375时钟/stream隔离/负守卫/恢复后更新复现通过。
入口16critic+2actor辅助更新不推广，prepared正式8 SHA752480635ecd70000cfdff97b2a50b824e32b0eb0c0cc8a251e14c5dd08d0e18。
严格SerlClockLearner持久critic_clock_extension；actor48、critic49结构化叶，官方10/2/noentropy/8:1、零示范保持。
新Direct3712508/GPU0/CPU0、30sampler共享1–12在serl_clock_cycle09_20261026_v1/direct，只一个9，无自动10。
已出现6次160–164动作global穿透abort，较8更早，全部保留。启动v1错误假设30live而失败，原文件保留；
v2按24live+6完成核验，新增10000/80000、全部新动作/obs/当前nextclock/reward0误差、6terminal/30MJB/父prepared全prefix通过。
归档3882888，serl_clock_cycle09_archive_20261026_v1；9只读4030422，须严格新clock loader，不重启旧8。
收尾Direct9完整400935/3167488、新增33973、0/30、reward−33.041、24完整+上述6早abort；全新映射/clock/reward0误差/30MJB/父prefix通过。
termMAE1.714但max65.252、Qmean27.636/max31.106，时钟单项未修复；完整state诊断不变/图已看。
原Direct3712508/归档3882888/审查4030422均已完勿重启，无Direct10；准确9 SHAa1a26f285f990ee2308f70a2f178527c2fabfec2b0e6bb1c973e00115981a61d。
新纯正式63.80s GPU49.93/40.67/46.27/40.93%，所有正式PID全窗口存活，每卡50%仍未达，不以辅助占用替代。
最终收尾13也完整：I574500/569501 A573500/568501 V574500/569501，Task/Strict18/17、13/13、17/17，
reward−2.288/−10.232/−2.836；termMAE1.628/.899/1.141，Qmean−16.800/−116.201/+10.435，末loss5.380/28.202/25.630。
三路全30完整无abort、全部新reward/父prefix/marker/MJB/三health及图通过；A任务17→13恶化，V Q仍移动，I终端max106.805。
原3841250/3/5、归档3882892、13审查4030423都已结束勿重启。当前无正式learner、无参数14/Direct10登记，Goal仍active。
后续准确父为pair_reduction_archive下13与clock_cycle09_archive下9，必须保留新markers及全state。
大产物SSD，HDD只小证据；持续GPU优化/健康收敛/最终冻结比较/ESN/SPT仍待。


## 最新RL状态：2026-10-26 参数11/12等价流水线与Direct8 critic-clock审查

原Goal active，未健康收敛；最新[完整交接](docs/RL_EXACT_PIPELINE_CYCLE12_AND_SERL_CLOCK_20261026.md)。
参数11三路全部完成：I18/17 A15/15 V17/16，各30完整55s；reward−2.357/−6.918/−4.587，
termMAE1.948/1.427/1.807，Qmean−24.052/−217.564/−67.944，A负向漂移仍在。
旧1110503/4/5及归档1110506/审查1131662结束勿重启。准确checkpoint见报告。
新前32二值mask接受检查+foreach Polyak：4896辅助更新、三路六次最终全state/sampleRNG逐项相同，
微基准+6.21/13.76/14.06%，不证明在线增益；旧probe已完勿重复填占用。
正式parameter_exact_pipeline_cycle12_20261026_v1：I2261725/A2261728/V2261730，原GPU1/2/3、CPU组各12sampler，
从完整正式11全部state/history续一个12，仅等价执行改动；terminal128/上界projection/pair2/batch32768/UTD1/原actorLR保持。
必须exact_class/projected_class恢复两个marker，禁止原loader静默丢目标；check-only全state不变/负守卫及实际启动1000步审查通过。
归档2261734、只读2261752在parameter_exact_pipeline_cycle12_review_20261026_v1等精确边界，无自动13。
收尾12已全部完成、无自动13：I533250/528251 A532250/527251 V533250/528251，Task/Strict18/17、17/17、17/17，
reward−2.214/−3.544/−2.842，termMAE1.953/1.021/1.283，Qmean−20.614/−232.570/−77.636、末loss5.476/115.199/98.975。
I终端最大误差94.267，A/V仍负漂移；全部新reward/父prefix/30MJB、三health与图完成。
原三正式2261725/8/30、归档2261734、审查2261752已结束勿重启。下一参数父为exact_pipeline_archive下准确12。
当前无正式learner运行，无参数13/Direct9登记，原Goal仍active，不是用户暂停或达标。
新冻结正式11三方法×三个代表共9完整55s/990万子步审查全完，三路Task/Strict均2/3，被动失败；
参数动作误差0、完整learner state不变、MJB/clock/filter/torque/raw-substep通过。原2337200/6/10及evaluator已完勿重跑。
I长主动接触舒适60.83%，A/V100%，被动/短主动无接触NA，非最终排名。
Direct8完整366962/2895704、0/30、reward−33.248、25完整+5穿透abort，termMAE2.165/max42.604；
全部新映射/reward0误差/父state审查通过。原438669/438672/855998结束勿重启，无正式9。
新critic-clock历史366962行重建已审查，v1 Q入口失败/v2 actor入口失败均0更新保留；
v3独立state48+clock叶，旧全部参数/Adam/counter/RNG可恢复，仅8新零叶，入口Q差异0、随机/确定actor精确通过。
v3同正式8两臂各2000outer共32000critic+4000actor辅助更新完成，0physics/未保存推广权重，图与独立审查通过。
clock/control终端MAE.985/1.171但p951.188/.854、max均43、Q均约17；局部改善非修复。
无正式clock持久adapter/迁移或Direct9登记，后续必须另验证完整state恢复，不得导入辅助权重。
新正式12 GPU观察0/40.13/38.67/40.17%，每卡50%未达、在线提速未证明；GPU0 Direct已停，勿重复旧辅助填占用。
物理/SPT/MJB/gates/filter/dt不改，无子agent，大产物SSD，HDD仅小证据。健康收敛/最终比较/ESN/SPT仍待。


## 最新RL状态：2026-10-26 目标Q投影参数11与Direct7/8（覆盖下方历史快照）

原Goal active，未健康收敛；最新[完整交接](docs/RL_TARGET_PROJECTION_CYCLE11_20261026.md)。
参数10全30完整/I18/16 A11/10 V17/16，reward−4.163/−15.491/−4.540；termMAE7.242/2.692/47.789，
加权末loss95.344/742.015/7760.742，终端加权未修复整体Q。原3818446/8/50及3965208已完勿重启。
原10health漏VMC已独立补齐到parameter_terminal128_cycle10_vmc_health_20261026_v1，原文件保留，合并索引有hash。
Direct6完整285867/2246944、0/30、reward−31.389，29完整+long0000第1149动作global穿透abort保留；
termMAE1.738、全部41024新映射/reward重建通过。新冻结6三固定代表330万子步/4125动作独立审查完，
Task/Strict0/3、均approach、人接触0/舒适NA，平均slowdown.5972；原507630/507861已结束勿重跑。
Direct438669/GPU0/learnerCPU0/30worker共享1–12仍在serl_pool30_cycle07_08_20261026_v1/direct，
官方8:1/batch32768/全state保持，仅有限7/8。启动10000/80000核验通过；归档438672，7/8只读855997/855998。
收尾7已完整327117/2576944、0/30、reward−31.159、30完整无abort；全新41250映射/reward重建通过，
termMAE2.422/p95=41.246、Qmean15.854仍偏；855997已完勿重启，438669进入8。
新有限cycle10目标Q上界投影3路×2臂×5000=30000辅助+2gate全部完，不推广权重勿重复填占用；
termMAE对照→投影I7.203→3.305/A2.840→2.036/V56.356→7.221，absQp95 1027→66/316→312/3615→418。
A负向漂移仍在，I in-bag无改善，V uncertainty大；不是在线恢复。32上界对比/disabled完整更新相同通过。
新正式parameter_projection_cycle11_20261026_v1 I1110503/A1110504/V1110505，GPU1/2/3与原CPU组各12sampler，
从正式10完整state/history续1周期11；保留terminal128/pair/batch32768/UTD1/原actorLR，仅投影target Q于熵项之前。
checkpoint保存terminal_loss_weight和finite_target_projection，后续必须projected_class恢复，原loader会丢目标。
三check-only全state仅加marker逐项相等/正负守卫通过；实际各1000新增、父prefix/history/优化器/12MJB/亲和性/
参数输入/clock/reward0误差核验通过。归档1110506，11只读1131662等待精确边界，无自动12。
新纯正式GPU54.68/41.33/40.87/40.47%，每卡50%未达；辅助窗口56.13/57.28/56.75/57.88不能替代正式。
物理/SPT/gates/MJB/dt不改；无子agent，大产物SSD，HDD只小证据。最终收敛/冻结比较/ESN/SPT仍待。


## 最新RL状态：2026-10-26 终端加权参数10与Direct5（覆盖下方旧运行状态）

原Goal active，未健康收敛。最新[交接](docs/RL_TERMINAL_WEIGHT_CYCLE10_20261026.md)。
V9已完勿重启1497979/1497983/2062386：409500/404501、17/17、reward−2.817，termMAE96.201、
末loss1318.913、Qp952919.910，pair未修复。Direct5已完审查2946490：244843/1918752、0/30、
reward−33.469，29完整+被动0300第1006动作穿透abort保留；termMAE1.719、全新增40881映射/reward重建通过。
原Direct2818100/GPU0/30sampler继续登记6，归档2833375/6只读2946491，不重复派发。
I/A固定target及固定target+actor/温度新4臂共20000辅助已完，复用旧uniform对照；Q尾部停止增长但term误差未修复。
新终端critic权重128诊断I/A各5000、V9原设置/128各5000，共20000+入口2更新已完；同正式初state和抽样流。
原设置→128终端MAE I13.088→7.540、A7.605→1.585、V114.529→14.891，Q尾部仍异常，不能称修复。
两组辅助所有PID已结束、不存/推广权重、勿重复填占用；父state digest直接核对正式checkpoint通过，图均已看。
新三正式runs/parameter_terminal128_cycle10_20261026_v3/{method}/train：I3818446/A3818448/V3818450，
GPU1/2/3，原CPU13–25/26–38/39–51各12sampler，仅1完整cycle10；从正式9全state/history直续，
只改critic终端权重128，原pair/batch32768/UTD1/actorLR保持，无辅助权重。该loss加权是算法适配非原CHEQ原样。
checkpoint保存terminal_loss_weight=128，后续训练须用新wrapper/helper，勿用原loader静默丢弃目标标记。
三check-only全state/RNG/Adam仅加标记严格相等、正负守卫通过；实际I新增4000/A/V5000、全父prefix/
原optimizer配置/history/12亲和性/MJB/新参数输入与reward重建0误差通过，非公共动态或物理子步重放。
准备v1漏校验依赖、v2 CPU恢复后CUDA延迟初始化改变单卡RNG，均未派发训练；v3预初始化全部generator修正。
启动审查v1错把参数向量与7维运动输出比较，失败保留；v2分开核验参数输入与公共形状/边界，阻抗零桥接通过。
新归档3818454/view parameter_terminal128_archive_view_20261026_v3；10只读3965208等精确边界，无自动延长。
纯正式60样本GPU56.48/43.85/40.92/40.08%，后三路采样约10.2核，持续每卡50%未达；混合辅助窗口不代替正式。
物理/MJB/gates/filter/dt/SPT不改，无子agent；大产物SSD，HDD仅文档；最终冻结验证/ESN/SPT与健康收敛仍待。


## 最新RL状态：2026-10-26 参数9、Direct4与30路采样试验（覆盖下方旧运行状态）

原Goal active，未健康收敛；最新[完整交接](docs/RL_CYCLE09_AND_SERL_POOL_20261026.md)。
Direct4正式203962/1591704、Task/Strict0/0、reward−32.559，29完整+1被动0900穿透abort保留；
原521120和归档533451均完成勿重启。旧审查2062387实际失败：粗替换把30回合写成40，
v1源码/错误保留；独立v2修正显式30并完整只读通过，termMAE1.217、state/RNG不变。
新Direct2818100/GPU0/learnerCPU0，runs/serl_pool30_cycle05_06_20261026_v2/direct，
2周期5/6、30sampler共享CPU1–12，保留完整state/history/batch32768/官方8:1/十critic、零示范。
只替换固定main两处调度，base+patch/hash收据齐；v1轮转单核候选只准备未启动，勿误作在线run。
新2000步/16000更新、父203962全prefix、30真实亲和性/MJB、新动作/nextstate/reward重建0误差通过。
归档2833375，5/6只读2946490/2946491等待精确边界，无后续自动派发。
I/A9已结束，原806847/806849/2062385勿重启：409500/408500steps、18/17与15/14，reward−2.223/−8.672；
termMAE15.377/7.494、末loss49.780/274.789继续恶化，尚无正式cycle10。
VMC8已完整审查368250/363251，17/17、reward−2.820、termMAE51.755、末loss725.854，pair非修复。
原1497979继续登记9、2062386只读等待，核实实际状态后操作，勿因历史快照/审查超时重启。
新I/A准确cycle9 batch32768vs256各5000共20000辅助更新已全部完成，不保存/推广权重，勿重复填占用。
两臂全state初始一致、sample初始seed一致但batch不同抽样条数不同；I终端MAE13.088vs27.043，
A7.605vs10.452，小batch无修复；全部预算/20点/原checkpoint不变核验与图通过。
新66.63秒GPU均值58.28/57.87/55.18/52.72%，GPU1/2是有限辅助非正式；结束后即时59/0/0/55%。
Direct30worker28.82steps/s对旧12worker29.34，无提速证据；尾部效果待测。持续每卡50%未达。
大产物SSD，HDD只小文档副本；原物理/MJB/gates/filter/dt/SPT不改，无子agent。最终冻结验证/ESN/SPT仍待。


## 最新RL状态：2026-10-26 VMC7恢复pair、SERL3及I/A8（覆盖下方旧状态）

原Goal active，未健康收敛。最新[审查与恢复](docs/RL_CYCLE07_VMC_RECOVERY_AND_SERL03_20261026.md)。
SERL3已审查：163214steps/1265720critic更新，0/30、reward−34.198，26完整+4global穿透abort保留，
termMAE1.005但任务未改善；521120继续登记cycle4，533451归档。3审查1210386已完勿重跑。
VMC all5原3419078已正常完成7勿重启：327000/322001，Task/Strict17/16，reward−4.602；termMAE54.90、
末loss394.57、Q范围−1236至1426，试验失败。统一7审查441621/归档3494331均结束勿重启。
新同cycle7全state三臂all5/pair/pair+criticLR.1各5000共15000辅助更新已全部结束，0physics、不推广权重；
terminalMAE47.25/33.04/42.27，pair Q尾部扩大/末loss920，不能称修复。旧辅助勿重复派发。
V新1497979/GPU3/CPU39–51/12sampler在runs/vmc_pair_recovery_cycle08_09_20261026_v1/vmc/train，
只撤回all5恢复pair、保留全部网络/Adam/replay/RNG和原LR，2周期8/9。仅新聚合history单列，旧history父中完整保留。
准备v1完成state校验后查错方法LAUNCH路径，命令生成失败未派发；改读原root LAUNCH并复核hash后实际启动，失败保留。
真实新增3000时父327000prefix/target2/原optimizer配置/12MJB通过；归档1497983，8只读1566165等待。
I/A8已审查：368250/367250steps，Task/Strict18/17与13/13，reward−2.272/−10.356；termMAE9.121/3.926，
末loss13.585/29.514，早期A改善未持续。原806847/806849继续登记9，无更晚阶段；8只读1566163已完。
I/A9只读2062385、V9只读2062386、Direct4只读2062387已等待相应精确边界，0训练/物理，不据等待超时重启。
实际mixing7最低0.2占比I29.11%/A54.47%/V99.34%，被动各0/10 carry失败；无因果阈值修改。
新纯正式窗口60.93/26.83/20.55/40.97%；另流水线66秒60.80/5.18/16.40/42.68，I尾部2→1workers，
V12workers使用10.32核/32.1steps每秒，均无辅助。GPU每卡50%未达，需真实采样/尾部调度优化，尚未部署新调度。
物理/MJB/gates/filter/dt/SPT不改，无子agent。大产物SSD，HDD仅文档副本，不能把有限诊断/低TDloss当收敛。


## 最新RL状态：2026-10-26 cycle6/SERL2与I/A cycle7审查（覆盖下方旧运行状态）

原Goal active、未收敛。最新[完整审查与续训](docs/RL_CYCLE06_AND_SERL02_REVIEW_20261026.md)。
官方SERL cycle2已完成勿重启3339709：123196steps/945576critic更新，Task/Strict0/30，reward−33.5245，
29完整+短0500在997动作global穿透abort保留；全新reward重建误差0，终端Q MAE2.348但p95 37.19。
三固定代表已完整330万子步/4125动作核验，动作/filter/torque通过，fullstate digest不变；仍Task/Strict0/3，
全approach、人接触0/舒适NA。评估144056与后处理215406已结束勿重启。原父协调CLI缺参已保留并交接修复。
新SERL521120/GPU0/CPU0–12在runs/serl_reviewed_cycle03_04_20261026_v1/direct，完整父state/history保留，
batch32768/官方8critic:1actor不变，2周期3/4；启动新增1000/8000、父123196prefix/12MJB通过。
新归档533451跟原PID，不派发训练。三参数cycle6 I18/17 A15/14 V17/16，reward−2.293/−8.591/−4.536；
终端Q MAE2.942/2.412/29.319，VMC all5仅降低Q均值而loss/终端误差更差，非修复。
I/A cycle7也已全审查：327000/326000steps，18/17与15/15，reward−2.349/−6.900，终端MAE3.649/1.951，
末loss3.505/5.866上升仍需观察。旧3070037/3070069已结束勿重启。新I806847/A806849 GPU1/2、原CPU组，
runs/clock_parameter_reviewed_cycle08_09_20261026_v1/{method}/train，2周期8/9、全state/history直续无新参数变化；
归档806853。新I/A真实新增3000/4000时父prefix/history/LR/12MJB核验通过。准备时系统python缺torch错误发生于导入前，无训练影响，收据保留。V3419078仍cycle7，未派新阶段。
只读441621在runs/reviewed_cycle07_audit_20261026_v1已审查I/A，待V后统一health；原归档3494331继续。
新60样本GPU62.53/23.48/27.33/48.10%，含真实阶段切换及GPU0冻结推理、无辅助训练，仍未四卡50%。
不用重复已完成辅助填占用。原物理/MJB/gates/filter/dt/SPT不变，无子agent，大产物SSD，HDD仅文档备份。


## 当前续训状态：2026-10-26完整cycle5/SERL1审查后（覆盖下方早期run状态）

原Goal active，未收敛。最新报告[cycle5审查与续训](docs/RL_CYCLE05_REVIEW_AND_CONTINUATION_20261026.md)。
旧SERL两周期、参数batch试验均已结束勿重启：SERL1 Task/Strict0/30、reward−35.102，
passive0500在1199动作global穿透提前终止，失败保留；参数5 I18/18、A13/12、V17/16各30，
reward−.4647/−12.2195/−4.5981，终端Q MAE4.43/3.53/16.01，VMC Q仍增长。
三actor-LR对照已完成3万辅助更新，I敏感性小、A降低LR拟合改善、V无修复；V再做critic LR
5000和all5 target5000，复用原control，无权重推广。criticLR无修复；all5 Q下降但终端误差变差，
只作为有限在线假设，非官方CHEQ原样或已修复。重复control误派已停，末记录1500更新、失败留存。
当前四正式：Direct `runs/serl_batch32768_cycle02_20261026_v1/direct` PID3339709/GPU0，
保留全state、仅batch2048→32768、官方8critic:1actor，1完整cycle2；三参数
`runs/clock_parameter_reviewed_cycle06_07_20261026_v1/{method}/train` PID3070037/3070069/3419078，
GPU1/2/3，2完整cycle6/7。I设置保留，A仅actorLR3e-5，V仅target min2→5、actor仍原pair。
全部optimizer/moments/replay/RNG保留，A/V仅新阶段聚合history清空，父history仍完整保存。
新启动全prefix/实际更新增量/LR/target/MJB和有限网络检查通过，`runs/reviewed_continuation_startup_20261026_v2`。
v1只读浮点精确比较失败已修正并保留，不是训练失败。归档器3494331在
`runs/reviewed_continuation_cycle_archive_20261026_v1`只读随原进程结束；请核实当前PID身份，勿重复派发。
新正式66秒GPU64.73/55.35/46.67/42.27%，无辅助，四卡50%仍未全达。旧有限辅助已完勿重跑。
SERL吞吐probe4632critic更新结束不推广；新wrapper准确父hash/源码/协议守卫正负检查通过。
原物理/gate/filter/dt不改。完整新周期、冻结策略验证、最终ESN/SPT仍待；无子agent，大产物留SSD。


## 2026-10-26 本会话明确恢复后的新状态（覆盖下方历史 paused）

用户重新设置 active Goal 并明确要求恢复两类 RL 直至收敛。当前记录见
[恢复与 SERL 实现](docs/RL_RESUMED_SERL_IMPLEMENTATION_20261026.md)。参数 CHEQ 从部分
快照保留全学习状态，在 `runs/recovery_cheq_resume_20261026_v1/{impedance,admittance,vmc}/train`
已完成 cycle4；cycle3仍是不完整历史，不能计完整。三路全状态与后续 RNG/抽样独立核验通过。
本轮最初 Direct 名为 SERL 的 run 实际调用旧 CHEQ 作者双 critic SAC，已明确排除为 SERL
结果并在首周期收完后停止；不能续作正式 Direct。真正 SERL 使用固定官方源码
`1fa2af7496be042e43d36120a7c8d1b71f1bfb59` 已启动：`runs/serl_official_state_online_20261026_v1/direct`，
PID1809418，GPU0，零示范/随机初始化/空replay，官方十critic、高UTD8critic:1actor，2完整周期。
软件target/全状态恢复/后续随机更新验证通过；真实16000transition全部动作映射、观测缩放、
reward/done/nextstate及12模型核验，88008critic更新；当时0终端，不冒称终端物理审查。
三参数cycle4 Task/Strict18/17、14/13、17/17各30；Q终端误差12.42/9.54/44.50，VMC漂移未解决。
已独立登记1完整cycle5 batch-only试验：`runs/cheq_batch32768_online_20261026_v1`，
PID1809422/1809423/1809425，GPU1/2/3。batch256→32768、UTD1，保留完整learner/replay/RNG，
不导入1536更新有限吞吐probe权重；三路实际新增12000更新且父replay前缀精确核验。
batch改变梯度统计，不是等价优化或已证实改善。新run nice0；旧run已结束勿重启。
原周期归档器PID2135157在`runs/serl_and_batch_cycle_archive_20261026_v1`只读保存边界，
身份检查后随四learner结束；请查看实际PROGRESS而非按旧PID重启。更新阶段66秒GPU均值
14.88/45.33/41.95/44.57%，无辅助训练，仍未达50%。原Goal继续active，未达收敛。
无子agent。旧runtime和关机快照不覆盖。HDD只剩约688MiB，大产物写SSD。

收尾SERL完整cycle0已通过全41250journal/replay与30terminal/MJB标签审查，Task/Strict0/30、
reward−34.2233，全部approach；290008critic更新。末1000loss.01356但terminal Q MAE9.95，
不是收敛；真实nextstate占位/mask0已查、非raw-substep物理重审。归档cycle0 sha d8d3765b…，
只读诊断图已看，原1809418继续登记cycle1。参数cycle5只读收尾协调2515639/CPU54在
`runs/cheq_batch_cycle05_review_20261026_v1`等三FINISHED后审查/CPU诊断，不派发下一训练阶段。


**历史关机暂停记录（已被顶部本会话恢复授权覆盖）：用户2026-10-26要求服务器关机前暂停。Goal已paused，全部本项目训练/仿真/审查进程退出；未获恢复指令前禁止重启。先读docs/RL_SHUTDOWN_RECOVERY_20261026.md/.json。HDD备份 /inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1；快照D213000/I162000/A161000/V162000，均部分周期，MuJoCo物理状态未保存；完整边界备用分别206250/122689/123750/123750。恢复必须独立run并审查部分cycle记账，保留optimizer/replay/RNG，不fresh reset。八temporal重复已全完成勿重跑、最终三seed汇总待做；A/V固定3例独立审查均已完，12例统一汇总待做；cycle3统一review等待已停止且未完成。原PID全部历史信息，不据旧进度重启。**

用户于 2026-09-30 明确授权并要求：**每次对话结束前，将本次文件改动 commit 并 push 到
`https://github.com/hwy0507/SII_compliance` 的 `main`，同时维护根目录 `UPDATE_LOG.md`。**
本约定适用于本仓库后续任务，覆盖旧进度文档中“保持未提交／不发布”的历史要求；用户后续
明确变更指令时，以新指令为准。

## 2026-10-26 GPU 效率偏好

用户要求恢复正式训练后 **GPU利用率最好不低于50%**。各参与训练GPU按稳定60秒窗口记录，持续不足时优化实际采样/更新吞吐；正式与辅助占用分开报告，不把占用当收敛。具体见Direct选择文档与关机交接的GPU章节。此要求不解除当前paused，不启动占用任务，不重复已完成实验。

## 2026-10-26 更晚澄清：SERL Direct 优先零示范从零训练

用户不想再采数据，询问从零训练；已静态确认 SERL 原文与官方纯状态示例支持。当前默认 **SERL-state/SAC from scratch adaptation**：随机初始化、空 replay，仅自主在线交互；不加载旧 CHEQ 权重/replay、已有示范，不新增示范/人工纠正。下方已有示范叙述是较早备选，不再是数据前置条件。无先验数据则不做RLPD对半采样，不冒称复现论文20示范实验；公平比较披露ESN示范量和RL在线交互量。Goal仍paused，此次仅文档，待明确恢复再登记/实现/验证。

## 2026-10-26 暂停期间的新基线决策（优先于下方旧四路 CHEQ 恢复叙述）

用户将两路分开：参数 RL（Impedance/Admittance/VMC）可继续 CHEQ；Direct 改用顶会已发表方法的适配。用户明确只接受已有示范，不新增人工纠正。已选择 **SERL（ICRA 2024，DOI 10.1109/ICRA57147.2024.10610040）** 的 RLPD/SAC 直接运动目标学习思路，未实现或启动。先读 [Direct SERL 选择与交接](docs/RL_DIRECT_SERL_SELECTION_20261026.md)。不能把无在线纠正版本称为完整 HIL-SERL（Science Robotics 2025）。原 Goal 继续 paused；下次明确恢复后先审计已有数据是否为合法 RL transitions、输入/动作/公共执行层适配，再建立独立 Direct run；不能直接恢复旧 CHEQ Direct 充当新方法。旧 Direct 产物全部保留，参数 CHEQ 的 optimizer/replay/RNG 延续要求保持。此次只改文档，不改变 physics/MJB/gate/filter/执行器/dt，不启动训练、仿真、测试或 GPU 占用任务。

## 新用户任务：已发表基线与训练集比较（2026-10-25 后续澄清）

收尾更新：temporal_return首四任务已全部完成勿重启，REVIEW/图核验8臂16万/648点；迁移MAE parent/fresh D.562/.748 I6.572/7.931 A7.592/7.496 V5.872/5.579，非softQ。新独立两seed重复runs/clock_temporal_return_replications_v1八PID602548/602550/602552/602553/602556/602558/602560/602562、每卡2路/共享52–54/nice10、32万更新/0physics/actor、不推广不自动延长，八启动核验通过；三seed总48万。收完再评估，勿复制已完任务。

最新紧急GPU：新runs/clock_temporal_return_transfer_v1四辅助375116/375119/375120/375122，cycle0拟合/cycle1迁移、parent0/fresh、batch8192、总16万更新/0actor/physics，不推广或自动延长。共享52–54/nice10/线程亲和性已补齐；原A/V固定评估子树nice19继续，在线0–51不变。四正式仍活跃，勿重启。报告PUBLISHED_TEMPORAL_RETURN_GPU_RECOVERY_20261026；原AGENTS上方摘要的旧进度非实时。远端ce467b1示范25/55审计已读合并de7ac97，Goal active。

最新：Imp原3479276与接管3825230已正常完成勿重启，三固定回合独立330万子步/4125动作重放误差0，learned/nominal2/3；长期峰46.41vs52.26、时间20vs20.52但舒适13.00%vs24.07%更差。runs/clock_parameter_fixed_review_v1/impedance（session2111已完）。四真实cycle1全state/replay/RNG恢复v2通过，runs/clock_full_state_resume_review_v2（session80301已完），0updates/physics、不派发下一阶段；v1缺support失败留存。新matrix6/12，A/V及3996089继续，原四在线+1729901/1729905继续。报告PUBLISHED_CLOCK_IMPEDANCE_AND_RESUME_REVIEW_20261026；Goalactive。

最新：clock Direct三代表完整复核session30235已完，learned0/3 vsnominal2/3，330万learned子步/4125动作重放误差0，均无人体接触NA，方向余弦约−.999非因果。runs/clock_direct_fixed_review_v1。评估已资源交接：旧2960898有意终止勿重启，原Imp3479276/CPU54保留，3825230只读接管；新runs/clock_fixed_parallel_v2中A协调3825231/eval3825618/CPU52、V3825232/3825634/CPU53，3996089汇总，仍原12回合预算。原目录HANDOFF_TO_PARALLEL_V2指新登记。核验器首亲和性断言错已保留，v2正确验证learner首核0/13/26/39、A/V各100动作误差0（session25486已完）。正式四learner和1729901/1729905继续，source不变；报告PUBLISHED_CLOCK_DIRECT_FIXED_AND_PARALLEL_20261026，Goalactive。

收尾fetch main新增c3124ba322853c1e561657b58c4204ed2a64a1b6：已读并合并另一airpig主机用户授权旧产物清理/存储解除报告；保留双方UPDATE_LOG追加块。该清理未发生在本集群，不删除或变更当前RL产物，尚无新的指定ESN物理结果。本轮在线报告提交bbc8513，push仍因HTTPS认证失败未发布。

最新clock cycle1完整复核已完（session39167勿重启）：TaskStrict D0/0 I17/16 A12/11 V17/16各30，Qloss19.000/5.638/13.131/26.072，非收敛。Imp长0500第314动作global穿透abort，nextclock1061/1375与零bootstrap通过；119完整+1早停留分母。runs/clock_cycle01_scientific_review_v1；原四在线与1729901/1729905继续cycle3/5。新固定首Direct被动完整110万子步物理/filter/torque独立通过但任务假/approach、峰39.5586、人接触0/NA；runs/clock_first_fixed_case_review_v1。原2960898/2961606继续矩阵，短期也失败、长期在途，不重启。报告PUBLISHED_CLOCK_CYCLE1_REVIEW_20261026，Goalactive/正式GPU50%及最终ESN未完。

收尾Direct完整cycle1复核：82500steps/77501updates，30完整55s Task/Strict0/0、平均reward−32.920646（cycle0−32.788830，无改善）；失败approach24/align6。全82500 replay reward/done/current-next clock、30终端/模型/fixture/plan/dt核验，通过已保存回放证据而非raw-substep复审。原learner已进入cycle2，不重启。证据runs/clock_direct_cycle01_terminal_review_v1/REVIEW.json，未选新算法或奖励。

最新：四return_capacity辅助全完成勿重启；REVIEW.json与图复核，parent/fresh留出MAE D.300/.349 I12.438/12.610 A3.462/4.073 V9.149/9.979，非softQ/策略改善，不延长。新clock_cycle00_fixed_representatives_v1协调2960898/首2961606、CPU54，四cycle0×三代表12×55s固定复测已启动；首165action重放误差0/clock维度模型通过，尚无完整回合。原在线四路与1729901/1729905继续，勿重复派发。报告PUBLISHED_CLOCK_FIXED_EVAL_AND_RETURN_REVIEW_20261026，Goalactive/最终ESN与GPU50%未完。

最新本轮报告PUBLISHED_CLOCK_CYCLE0_AND_GPU_WORK_20261026：新clock首周期完整复核各41250/36251，TaskStrict D0/0 I18/16 A13/13 V17/16各30，非收敛；原在线四路和1729901/1729905继续。旧固定cycle3矩阵全部结束勿重启（12learned+12nominal/2640万子步）。新runtime profile正式GPU5.30/7.77/7.27/7.48%。用户紧急要求后登记四有限辅助return拟合2751144/2751146/2751148/2751151，runs/clock_cycle00_return_capacity_v1，四卡各一、CPU52–54共享nice10、总16万updates/0actor/0physics，不推广或自动延长。全部已启动，首混合60样本均值68.63/52.15/33.28/35.78%，非纯正式/未四卡50%。固定标签不含熵且父已见留出条件，不能作SAC Q或未见policy评估。完成后复核，不重复派发；Goal仍active。

收尾main已同步6dc2b24（非RL原始链30条审计与存储受阻交接）；那是另一会话Goal，不暂停本服务器RL。在线报告提交d81e531。

最新在线阶段已实际启动：runs/cheq_clock_online_seed20261025_v1，runtime/source_train17_clock，登记/决策runs/clock_online_control_v1。四learner1729888/1729892/1729893/1729897，CPU0–51各12sampler+1learner/GPU0–3；fresh/空replay、同30条件、6周期有限阶段。四6000-step/1001updates快照startup_review session34643已完整通过，actor参数、critic时钟列已更新、全部replay时钟/12model/input核验；不要重启。归档1729901/CPU52、诊断1729905/CPU53监视周期0/1/3/5，固定矩阵3148346/CPU54继续。正式GPU60s均值6.27/5.87/6.27/6.47，50%未达；辅助12全结束勿重启或为占用延长。
跨周期review完成：D81.322/49.061、I57.908/87.011、A183.942/44.849、V160.909/99.770，无/有时钟cycle1终端MAE；Imp3seed全变差、V2/3改善，非通用修复。预检四完整55s与逐replay核验通过、0updates，不能称学习成功。contact_math12/12独立精确复核1320万子步，COMPLETE_REVIEW.json，source17合并仅此3性能+5时钟文件，不是整体提速证明。固定Imp/Adm三代表复核已完（runs/fresh_cycle03_parameter_fixed_review_v1），各learned/nominal2/3，Imp长期舒适12.61%对24.07%、Adm100%双方；V仍在途。报告PUBLISHED_CLOCK_ONLINE_STAGE_20261026，Goal active；接下来继续新在线stage周期0证据及原VMC固定矩阵，最终ESN仍未指定。

收尾fetch/合并远端64fe259非RL九拟合与ridge审计（56物理回合因airpig存储未启动）；本地2294dd9实现，HTTPS push认证失败仍未发布。contact_math结果实际在results/FINISHED.json，已存在；未复核后四例勿称全部独立通过。

最新本轮：原fresh三初始化八重复及seed27均已结束勿重启；完整review/图已通过，终端MAE无/钟17.760/8.487、30.606/11.354、69.204/19.699、74.311/25.806，非未见/在线证据。末组5完整review图核验0/0、18/17、13/13、17/16各30，V短0600穿透.214652mm，全部旧formal停止。新12路runs/fresh_critic_clock_withheld_cycle_v1仍在跑，CPU0–11/GPU每卡3、有限120万辅助更新，PID见LAUNCH；60s平均98.07/98.27/98.90/98.50%，不要为占用延长。新增可选critic_clock代码四接口真实upstream验证及17测试通过；runtime/critic_clock_candidate_v1冻结五文件改动，actor49/critic50，mixing间接受时钟影响。runs/critic_clock_candidate_preflight_v1四single55s预检1312002–1312005/CPU12–19已推进，0updates，未选/启动正式在线阶段；预检/12辅助结束后复核再登记。报告PUBLISHED_CLOCK_CANDIDATE_AND_GPU_RECOVERY_20261026。固定cycle3协调3148346已转VMC，contact coordinator已退出须读results子目录再判断完成，原独立收据1–8保留、9–12仍待复核。Goal active，未完成最终ESN/SPT比较。

本轮收尾补充：原四formal六轮均已正常结束，A247500/原793968、V247500/511376勿重启；原整组5工具及child543487已完成，runs/fresh_ready_methods_audit_v2/fresh_cycle_05/FINISHED，科学复核尚待。原full-replay八probe全部结束勿重启，24臂120万/1200点review session40035完成、图已看；inbag MAE无/时钟D19.572/23.388、I21.235/19.720、A34.713/33.771、V65.896/73.352，非通用修复，runs/fresh_full_replay_critic_clock_v1/REVIEW.json。
为检验critic初始化随机性，新补两独立constructor/sampling seed26/28（原27复用）：runs/fresh_initialization_replications_v1、同名runtime，8PID648950/648956/648962/648967/648975/648978/648983/648987，CPU8/9/10/11/12/14/15/16，GPU每卡2。新增80万辅助critic，加原seed27的40万合计120万；0physics/actor、无权重推广、不自动延长。首12–13k实际更新、三初始critic hash不同而actor/replay同核验，原391155–391158继续。新瞬时四卡99%，非持续/纯在线保证。报告仍PUBLISHED_DIRECT_FIXED_AND_IMPEDANCE_FINAL_20261026；Goal active，下一步完整组5科学复核和fresh初始化结果，不能把当前无正式在线learner误报为训练收敛。

最新固定fresh3 Direct三代表完整复核完成session92211，0/0各3（nominal2/2），都carry；六归档660万子步、learned三filter/torque、nominal物理/filter、MJB/fixture/plan/dt/hash一致，nominal无torque投影重放声明。最后10s residual与obs nominal方向余弦−.94至−.95，描述非因果；长期真实接触5.9546s舒适100%但Task假、其余NA。runs/fresh_cycle03_direct_fixed_review_v1。原3148346继续参数。
Imp3849956已正常六周期结束勿重启，246984/241985；final ck437c2625…与archive一致、30完整terminal/MJB/reward/replay核验，Task18 Strict17（被动0/0短10/9长8/8），短0600穿透.230442mm保留；loss10690.257/targetQ1053.831，reward−2.274513/改善1.0498<2，非健康收敛。session8822/runs/fresh_impedance_final_cycle05_review_v1已完；不自动原样延长，原2472115仍等整组5。
完整回放原shard1四PID4005367/4005615/4005949/4006167均已结束勿重启，shard0继续第三seed。部分配对未显示通用clock修复；新同seed20261027 fresh critic初始化×clock对照已登记实际更新：runs/fresh_initialization_critic_clock_v1、同名runtime，PID391155–391158，CPU1/3/5/7/GPU0–3。每臂50k共40万辅助critic、0physics/actor，不推广权重/不延长；actor逐tensor同父、data/alpha/gamma同、critic新hash不同，首4000核验，3测试通过。不要重复启动。第7/8 contact完整精确复核假/假，SEVENTH/EIGHTH收据、8/12独立完成、原2273688继续未部署。新混合GPU60秒均值89.18/89.25/92.47/89.38%、最低87/87/89/88。VMC原阶段也已247500结束（恢复5+父0），Admittance收尾，原2472115已见D/I/V三final仍待A。报告PUBLISHED_DIRECT_FIXED_AND_IMPEDANCE_FINAL_20261026.md/.json。Goal未完，后续须完整辅助/整组5证据再定在线阶段。

最新固定actor/alpha critic时钟诊断已完成：runs/fresh_critic_clock_probe_v2，3666074/3666075/session73879退出勿重启；12万辅助更新/0physics/0actor，配对初始化/采样/hash与图复核。D/V后一轮终端MAE无/有时钟130.799/123.232、150.348/138.577，均较起点变差，非修复/不推广。v1缺依赖、0更新失败保留。
用户再次紧急要求提高利用率后，已依据此结果登记完整回放四方法时间/零对照：runs/fresh_full_replay_critic_clock_v1、同名runtime，8进程4005286/4005367/4005526/4005615/4005732/4005949/4006084/4006167，CPU0–7/GPU0–3每卡2，3seed分片2+1、每臂50k、总120万辅助critic更新/0physics/0actor；full replay两周期全拟合、无heldout，fresh Adam/固定actor alpha，原正式不动。不保存推广辅助权重，不自动延长。八项启动核验各7000更新，读原PROGRESS/FINISHED勿重启。新增FIFTH/SIXTH contact收据完整精确通过，两Imp主动TaskStrict真；6/12独立复核，协调已7继续。固定cycle3 Direct3条件失败，原协调已3审计转Imp3897988。新混合GPU60秒均值89.37/91.87/94.62/96.12%、最低88/88/89/89%，非纯正式吞吐。报告PUBLISHED_CRITIC_CLOCK_DIAGNOSIS_20261026.md/.json；原三formal/cycle5审计继续，Goal/最终比较未完。

最新fresh cycle3四路完整复核完成(session26337退出)，Task/Strict0/0、18/17、13/12、17/17各30，被动全0/10；loss119.043/1173.444/830.029/720.415、terminalMAE144.124/247.539/332.196/431.386均较1增。120terminal/MJB/4ck/hash/reward/780source与图通过，Imp/Adm短0600穿透.232502/.207465mm>.2mm保留；runs/fresh_cycle03_scientific_review_v1。原2472115等5，别重复派发。
Direct4055508原六轮已正常结束勿重启：247500/242501，final ck1f43dda8…，最终30完整55s/TaskStrict0/0；改善.09068<2、最近range.476<tol.660但plateau false，loss390.695、terminalMAE247.853。独立诊断session46540退出，30terminal/model/hash/reward及图核验，runs/fresh_direct_final_cycle05_review_v1。不自动原样延长，不称收敛，Goal继续/其余三learner在训；下一阶段依据完整证据另登记。
新固定cycle3的4×3确定性矩阵已启动：runs/fresh_cycle03_fixed_representatives_v1，reg8ce8f780…，工具runtime/fresh_cycle03_fixed_representatives_v1；readiness3005171/session66123已结束勿重启。协调3148346、Direct评估3148347/首physics3152099，CPU54/GPU0–3串行推理、source16，预算12×55s/1320万子步、0updates，复用12名义行，不选Tref。首ck/actor49/raw48/common7/MJB/dt/CPU通过；尚未全完成，poll原PROGRESS。接触math2273688继续，Direct3/12/330万子步完整精确通过，第三收据THIRD_CASE_REVIEW；随后Imp被动也完整精确通过，FOURTH_CASE_REVIEW，现4/12/440万子步；旧3047099已退出，短期3298289继续，非整体加速/部署。报告docs/PUBLISHED_FRESH_CYCLE03_AND_DIRECT_STAGE_20261026.md/.json。GPU50%/充分收敛/最终SPT/指定ESN未完。

最新只读replay clock核验完成，runs/fresh_cycle01_clock_review_v2，session47719退出勿重启：四cycle1共329484transition/240episode，日志前缀globalstep与replay reward/done/context及nextobs连续精确；独立known_clock仅55s/40ms，Imp859步早停next仍516/1375，不编码未来中止。v1/session82442错误断言累计elapsed为单步时长，失败保留，非训练clock缺陷。240终端近邻无精确obs或obs+action重复，距离不是混叠因果证据，未选/训练时间critic；0physics/updates，正式输入/learner不变。
contact math原2273688首例Direct/passive0000完整55s/110万子步已复核精确通过（Task/Strict假），runs/contact_math_validation_v1/FIRST_CASE_REVIEW.json；第二例active_short也已完整精确复核，SECOND_CASE_REVIEW.json，现2/12/220万子步，非整体通过/加速/部署。旧2536553退出，active_long新child2792032继续，读PROGRESS更新身份，不重启。原四learner和2471936/2472115/2472286继续。报告docs/PUBLISHED_REPLAY_CLOCK_REVIEW_20261026.md/.json；Goal/GPU50%/最终比较仍未完。

最新接触math完整候选已独立构建并启动有限验证，未部署：runtime/contact_math_candidate_v1（父source16），runs/contact_math_validation_v1/REGISTRATION.json hash84015ef9…；冻结工具runtime/contact_math_validation_v1。3守卫测试、780/24/150/128实际hash通过；12×55s动作重放/1320万新子步、0updates，CPU53/nice10/CUDA禁用。协调2273688/首child2273849已live，首例537动作前缀观测/区间/潜势与MJB/adapter/dt通过；尚0/12完整验证，勿称通过/整体加速/自动部署，poll原PROGRESS/RESULTS/FAILURE/FINISHED，勿因超时重启。原训练52核/配置未动。
Direct cycle2/3只读60终端/model完整复核完成：2/2→0/0各30、均55s，reward−29.59422→−33.25034；短0100/0000在54.040/54.160s成功（阶段release但原gate真），1375保存区间穿透峰值一致且≤.2mm。不是原子步重审/固定策略成功，成功随下一轮消失，不称收敛。runs/fresh_direct_cycle23_terminal_review_v1，0新physics/updates。报告docs/PUBLISHED_CONTACT_MATH_CANDIDATE_20261026.md/.json。原四learner/2471936/2472115/2472286继续，Goal/GPU50%/最终矩阵/ESN未完。

最新fresh cycle1完整科学复核完成，runs/fresh_cycle01_scientific_review_v1，0新physics/updates：120完整55s，D/I/A/V Task/Strict0/0、18/17、13/13、17/17各30，被动全0/10。loss25.869/53.403/79.790/49.420、terminalMAE72.259/81.622/115.690/104.931均较0增；非健康收敛。Imp原DIAGNOSIS含0/1两轮，其他恢复后只含1，统一filter cycle1后Imp reward−2.396327。4ck/hash/120terminal/MJB/reward/780source核验，图已看；Imp短0600外穿透.2276335mm>.2mm，1375区间核验。原2472115继续等3/5，不重复派发。
接触math微探针1566953/session9489已完成勿重启：runs/contact_math_probe_v1/VERIFIED_SUMMARY.json；30MJB269020几何对、65536+5+8715范数逐字节一致，仅连续float64(3,)。局部CPU比geometry3.399/norm1.460；18mj_forward、0mj_step/新transition/updates，非全轨迹/整体加速。未准备/部署完整环境候选，live未改。新GPU60s正式均值5.63/5.73/6.15/2.58%，50%未达，无辅助任务。报告docs/PUBLISHED_FRESH_CYCLE01_AND_CONTACT_MATH_20261026.md/.json。原四learner/2471936/2472286继续；Goal/最终矩阵/ESN未完。

最新小batch外部profile完成，session41020/44666均退出勿重启：runs/fresh_small_batch_profile_v1 50Hz有13–14s滞后，保留不能作正常计时；v2 10Hz各主线程599样本无lag/Errors0。D/I/A/V selector等待78.80/49.92/45.58/65.78%，target1.00/3.51/3.84/2.84%，D5→0/V6→6尾部而I/A12稳定。代表Admittance sampler physics93.32%/等待动作5.01%/CPU93.61%；55核quota无新增throttling、窗口平均34.33核。不是CUDA计时/全局因果结论。
最终SCIENTIFIC_REVIEW覆盖初步REVIEW的Polyak建议：优先调查采样循环与周期尾部，不优先Polyak、不改live batch/UTD/dt；未准备或部署性能候选。source780/parameter24 hash重验，0新physics/辅助updates。docs/PUBLISHED_SMALL_BATCH_THROUGHPUT_PROFILE_20261026.md/.json。四learner及2471936/2472115/2472286继续，Goal/GPU50%/最终比较未完。

最新四路12worker交接均已实际生效：D4055508/I3849956/A793968/V511376继续；原A1314547/V1146204已正常首轮结束勿重启。A/V各41250父→42250/37251新snapshot全replay/history/Adam连续及首12实际模型输入核验，父09b8415f…/62d054ba…。只读196372/session4132已FINISHED退出勿重启；runs/remaining_fresh_resource_resume_review_v1。DISPATCH_FINISHED不是六周期/Goal完成，2471936/2472286继续。
原2472115四路同cycle0诊断已完整复核、现等cycle1；Task/Strict0/0、17/16、12/11、17/16各30，四路被动均0/10，loss9.334/8.003/11.392/7.338、terminalMAE36.201/36.646/51.131/52.502；120终端/model收据+ck/hash/reward/network与图核验。Imp29完整+长期0000 859actions/34.36s全局穿透abort（物块/凸边87.21165mm）；I/A/V短0600分别.225314/.205722/.216555mm超原.2mm，失败保留。D第二轮0/30、reward−33.20797；非收敛/名义改善结论。
扩容后正式GPU60秒均值6.07/6.80/5.83/5.98%、min0，无辅助GPU训练，50%仍未达；后续需定位当前配置吞吐，不为占用率改live UTD/batch。文档PUBLISHED_FRESH_CYCLE_AND_HANDOFF_PROGRESS_20261026.md/.json。继续原六周期和1/3/5审计，Goal/最终固定策略矩阵/SPT/指定ESN仍未完。

最新fresh Direct完整cycle0只读诊断已完成，session29414/52532均退出勿重复：41250/36251，Task/Strict0/0各30、全55s；loss9.334、TD MAE.401、终端MAE36.201。精确重建41250mask/最终replay RNG、36251采样含6346终端抽取；最后1条未抽，另2条≤20次，>100次20条in-bag MAE4.84、out-of-bag97.60。不能把整体终端误差全部解释成发散，也不是健康收敛；继续原阶段不改mask/设置。30terminal/MJB/reward/network与两图核验，0physics/updates。runs/fresh_direct_cycle00_diagnosis_v1、docs/PUBLISHED_FRESH_DIRECT_FIRST_CYCLE_20261026.md/.json。原四learner与2471936/2472115/2472286继续；原四路完整审计还会按原计划做，别重复派发训练。Goal/ESN/GPU50%仍未完。

最新2026-10-26：四原SAC均正常结束勿重启；Imp1557140最后cycle4/228528/412500、Task17/Strict16各30、30完整55s，final/archive fb4786b3…核验。新Imp3849956直接12worker已实际学习，4000步fresh初始化及15000/10001onset核验，14fixture/MJB/plan/dt通过；首只读断言错把executed7维当参数5维，失败收据保留，只修核验器，训练未动。runs/impedance_fresh_start_review_v1。
Direct原1215546也正常结束cycle0/41250/36251，Task/Strict0/0、reward−32.96638；新4055508由原协调自动12worker全state续余五周期。父15eb2266…/复制/EXECUTION一致，新46250/41251父replay/history精确、Adam连续及首12模型输入核验；runs/direct_fresh_resource_resume_review_v1。原A1314547/V1146204仍首轮，2471936/2472115/2472286继续，勿重复派发；接续以resumed_from/hash为准，registration restart_reason仍描述整个fresh阶段起源。
最新纯正式GPU60秒均值10.02/6.13/1.18/1.05%，仅D/I已12worker，50%未达，无辅助GPUjob。文档PUBLISHED_INDEPENDENT_RESOURCE_HANDOFF_20261026补充；0新增核验physics/updates，不改live设置，不是收敛/最终比较。Goal active，指定ESN仍缺。

最新Direct/VMC原SAC也已完整结束勿重启：1215621 cycle8/384621steps/722758updates，Task/Strict0/0；726082 cycle5/268509/495000，17/17，各30。D28完整55s、被动0671/0400于395/902action穿透abort保留；V30完整。60terminal/MJB/时长/replay及final ck与archive hash核验，ad62c3f1…/2643cb15…。新run DIRECT_SAC_DRAIN_REVIEW.json、VMC_SAC_DRAIN_REVIEW.json；文档PUBLISHED_INDEPENDENT_RESOURCE_HANDOFF_20261026已补充。原SAC仅Imp1557140继续，三fresh原PID仍cycle0；2471936/2472115/2472286继续等待各自完整边界，尚无新恢复learner。不是critic健康/收敛/最终接受。

最新首路SAC收尾确认：Admittance1316018正常结束cycle4/226765steps/412500updates，勿重启；30完整55s条件、Task/Strict13/13，terminal/MJB/时长与replay核验，最终ck与migration_archive cycle00004 hash06925f84…一致。新run ADMITTANCE_SAC_DRAIN_REVIEW.json。fresh Adm1314547仍cycle0，2471936继续等其完整边界后才12worker恢复；尚无新learner派发。此为完整停止证据，不是critic健康/收敛；文档PUBLISHED_INDEPENDENT_RESOURCE_HANDOFF_20261026已补充。

最新2026-10-26改为按方法独立完整周期交接，覆盖旧v1统一预热等待：旧协调1956030/fresh1146202/SAC691298已通过停止入口正常退出勿重启；新2471936，runs/CHEQ_FRESH_READY_METHODS_V2.json、runtime/fresh_ready_methods_v2、输出cheq_fresh_ready_seed20261025_v2。已向三fresh及三新SAC写完整周期STOP，原Imp1557140已有STOP字节不变；7原learner均live继续，尚无新learner恢复。D/A/V待各自fresh+SAC当前完整周期后全state resume，Imp待原SAC4后直接fresh12worker/六周期，不先派双worker。source16/batch256/UTD1/奖励等不变，六周期总预算扣原已完成，52核分配不变。
旧只读1968149已在idle/nochild/no completed时替换为2472115，runs/CHEQ_FRESH_READY_METHODS_AUDIT_V2.json、fresh_ready_methods_audit_v2，继续0/1/3/5真实跨run审计；新archive2472286跟随空LAUNCH，旧early/migration在父全退出/保存后才停。4守卫测试、780source/24参数/30条件/7进程身份hash通过。启动D14431/A12271/V13153均cycle0、Imp旧215028/20条件；状态draining，扩容/收敛/GPU50%/ESN未完成。docs/PUBLISHED_INDEPENDENT_RESOURCE_HANDOFF_20261026.md/.json。

最新SAC新run Direct7/VMC4只读复核完成，原诊断session21874已退出勿重启：Task/Strict0/0与17/16各30，loss1722495/10207173、terminalMAE11622/39222，较旧5/3继续恶化；不改fresh设置。D被动0200于663action/26.52s穿透abort，其余29完整55s；VMC30完整、短0600Task真Strict假，保存interval复算穿透.223470mm>.2mm。60terminal/MJB/奖励/checkpoint/网络和两图核验，非新全子步安全审计。runs/sac_post_reallocation_cycle_review_v1/REVIEW.json及VMC_STRICT_FAILURE_DETAIL.json，docs/PUBLISHED_SAC_POST_REALLOCATION_REVIEW_20261025.md/.json。原fresh三路和Imp原1557140实际推进，1956030/1968149仍等待，勿重复启动。

最新fresh学习启动只读核验已完成：D/V6000步各1001updates，网络/target实际改变、Adam有效、旧replay字段精确保留；三路9000预热行与fresh初始化核验。不是收敛。D8385/Adm7171/V8480时均cycle0，Imp仍等原SAC1557140完整4。
已登记并启动资源优先协调器1956030，runtime/fresh_sampling_priority_v1，runs/CHEQ_FRESH_SAMPLING_PRIORITY_V1.json；目前等待原fresh1146202与SAC691298四路更新并退出，尚无新STOP。之后自动完整周期停止SAC、CHEQ保存全state后2→12sampler，52核分配；六周期总预算扣除原已完成，不重计，source16/batch256/UTD1/奖励等不变。勿重复派发或提前绕过依赖。
原只读observer1156327在无child/无完成stage时已明确替换为1968149，runs/CHEQ_FRESH_PRIORITY_AUDIT_V1.json/output fresh_priority_audit_v1，原0/1/3/5跨原run和新cheq_fresh_priority_seed20261025_v1真实归档。保留SUPERSEDED及首次pidfd_open不可用的信号前失败收据，不重启旧observer。7守卫测试和780source/24parameter/30条件/plan hash通过。最新纯正式GPU均值11.93/7.17/31.72/3.58%（部分SAC周期尾部），50%仍未达、扩容尚未生效。docs/PUBLISHED_FRESH_LEARNING_AND_RESOURCE_PRIORITY_20261025.md/.json；Goal、ESN仍未完。

最新SAC原Adm/VMC3只读observer3759872/child1319809已完成退出勿重启；60完整terminal/MJB、checkpoint/reward/network和图复核通过。Task/Strict12/12与18/18各30；loss2→3 146717→1790203、537785→3062208，Q18097→43734/28848→82018，terminalMAE3754→13778/11169→23290，不健康收敛。runs/sac_remaining_cycle03_audit_v1/REVIEW.json。三路SAC扩容生效后的正式GPU窗口36.45/5.78/23.38/25.58%，50%仍未达，无辅助GPUlearner。
最新补充：Admittance旧2758791已正常结束3/185515/330000，SAC新1316018在4实际更新9worker；fresh新1314547真实采集预热。父checkpoint和首9/2模型/输入/dt/CPU通过。四路只有Impedance尚等原1557140完整周期；原observer3759872已派发只读1319809做Adm/VMC3整组，勿重复启动。
最新extended discount四probe361333–361336已全部完成并退出勿重启：40万辅助updates、0physics、无权重保存/推广，8arm初始化/采样/输入hash、完整曲线和40个旧共同前缀精确核验、两图已看。低gamma降Q但非通用误差修复：终端MAE长/短 .165/1.113、.275/.744、5.240/.753、18.745/5.643；VMC两arm末段仍增长，.99起点终奖系数约1e-6。runs/consistent_discount_extended_cycle06_v1/COMPLETED_REVIEW.json。
已科学登记fresh reduced reuse新CHEQ阶段：FRESH_REDUCED_REUSE_SCIENTIFIC_DECISION_V1.json，source16现实际部署（冻结manifest的prepared是构建时记录不改）。batch256/UTD1、原pair目标、LR3e-4、gamma.9995/同奖励和LayerNorm、全新网络/Adam/alpha/RNG与空replay；6完整周期，不是收敛/总Goal上限。不导入辅助权重/旧replay。派发器1146202，runs/cheq_fresh_reduced_reuse_seed20261025_v1；VMC1146204、Direct1215546已真实采集、仍5000步预热updates0，其余等原SAC释放CPU。新CPU D0+11/12、I14+25/52、A26+37/38、V39+50/51，GPU0–3；不与SAC40核重叠。observer1156327等完整0/1/3/5，只读12h保护；勿重复派发。source16全hash与四构造预检、2派发守卫测试通过，v1缺helper失败保留、v2通过。
SAC原Direct1010728已结束6/304286/562088，新1215621进入7实际更新9worker；父ck/首9模型输入dt通过。原VMC726082继续，资源协调691298仍等I/A，原observer3759872仍等Adm3。新Direct/VMC首2实际模型输入/CPU通过。辅助退出后的正式GPU均值4.42/4.88/2.65/33.27，50%未达；当时多路仍旧双worker/预热，不外推后续。docs/PUBLISHED_EXTENDED_DISCOUNT_AND_FRESH_STAGE_20261025.md/.json。Goal未完、ESN仍缺。

最新SAC采样资源交接已登记派发，协调器691298、迁移archive691379；runs/SAC_SAMPLER_REALLOCATION_V1.json，冻结工具runtime/sac_sampler_reallocation_v1。原四SAC各STOP_REQUESTED仅在完整30条件周期边界交接，勿删除/重启原队列。VMC原2397784已正常结束cycle3/186009/330000，新726082在runs/sac_sampler_seed20261025_v1实际更新cycle4、9worker CPU40–48，learner49/GPU3。父ck 7a62caf0…字节与resume hash一致、首9模型/48obs/dt通过。其余原1010728/1557140/2758791仍收尾6/4/3，随后自动迁移。保持同source09和同training registration字节，单独资源登记workers2→9；未来采样顺序非逐位等价。新分配Direct10+1–9、Imp23+15–22/24、Adm36+27–35，避开四probe0/14/26/39、observer13、协调54。
6守卫测试通过；原777source/24parameter/150upstream/128robot及30条件/plan实际hash重验。GPU混合60样本均值59.65/57.20/58.10/65.35、min20/43/12/10，不是正式独立达标。四原extended probe首arm50000已结束、第二arm进行中，勿重复启动；完整配对review待。原observer3759872已见VMC3仍等Adm3，source16未部署。docs/PUBLISHED_SAC_SAMPLER_REALLOCATION_20261025.md/.json；Goal未完，ESN仍缺。

最新all5阶段10/11已全部结束并完整科学review，旧四learner1325445/1328516/1333006/1338945及audit1346884/reviewer1346887均退出勿重启。11 steps574194/574721/575570/576276，Task/Strict0/18/11/17各30；四loss/terminalMAE再增、Direct/Admittance退化，不原样延长all5。120终端/模型/hash、reward/network及图复核；runs/BELLMAN_FINAL_SCIENTIFIC_REVIEW_V1.json。source16仍prepared，尚未选下一在线stage，Goal未完。
新有限extended discount四probe361333/361334/361335/361336在GPU0–3、CPU0/14/26/39实际更新：原fresh cycle6同seed数据，原random2目标，.99/.9995 Bellman和PBRS匹配，各arm50000共400000辅助updates、0physics、不保存推广权重。原5000末entropy仍正，延长查后期漂移；前4000/5000与原metrics/diagnostic精确相同（重算，不独立重复）。runs/consistent_discount_extended_cycle06_v1、runtime/consistent_discount_extended_v1。读原进程/PROGRESS/FINISHED，不重复启动。GPU60样本混合均值63.53/55.98/60.57/61.23，min44/44/49/46，非正式独立达标。原四SAC09及剩余cycle3观察3759872继续。
名义矩阵120/120已全完成，旧2210514/2210515退出勿重启；新只读380039完成后60，复用前60，COMPLETE_MATRIX_REVIEW.json。Task18/18/16/17、Strict18/18/15/17；Admittance短0600穿透0.209567mm超原0.2mm安全失败保留，舒适67.00/31.98/72.22/72.10%，无接触NA，Tref未选。报告docs/PUBLISHED_BELLMAN_FINAL_STAGE_REVIEW_20261025.md/.json。物理/actor/filter/gate/执行器/dt未变，指定ESN仍缺。

最新固定名义Impedance/VMC完整各30已复核，3919824只读进程退出勿重启：Task/Strict18/18和17/17，分类0/10/8与0/10/7，机器安全0/60、失败均carry；峰矩59.2441/48.0088Nm，实际接触各8回合、时间加权舒适31.9774%/72.0975%，无人接触NA、含失败分母、不选Tref。60例6600万原子步hash/模型/公共filter/零action/reward、实际幅值/相邻servo slew及接触复算通过，0新physics/updates。旧v4无投影内部trace/首previous torque，明确不称完整投影重放。source06/14保护manifest及5实际源文件相同已核验。runs/nominal_completed_impedance_vmc_review_v1/COMPLETED_REVIEW.json和docs/PUBLISHED_NOMINAL_IMPEDANCE_VMC_COHORT30_20261025.md/.json；后续整矩阵复用这60项，不重仿真。原slot1已结束，slot0/八learner/11审计/剩余SAC3观察仍继续；source16未部署，目标未完成。

最新SAC Impedance完整3/187278只读audit完成、3712274退出勿重启：Task18/30 Strict17/30、分类0/9/8，短0600失Strict/长0300新增；loss2533→19285、Q2488→5252、terminalMAE519→1540，非健康收敛，原1557140进入4不改。30条件/terminal/MJB及冻结inputs/hash/reward/network和图核验，0physics/updates。runs/diagnosis_sac_impedance_cycle03_v1/REVIEW.json，docs/PUBLISHED_SAC_IMPEDANCE_CYCLE03_REVIEW_20261025.md/.json。
新只读observer3759872仅等原SAC Admittance/VMC完整3，勿重复派发：runs/SAC_REMAINING_CYCLE03_AUDIT_V1.json；输出runs/sac_remaining_cycle03_audit_v1，冻结同名runtime。3h是观察期限，不停训练；报告形成后仍需科学review。原八learner、CHEQ11审计1346884/1346887继续。nominal117/120，slot1完成60项/2210515已退出勿重启，slot0原2210514继续剩余3；整矩阵审计/Tref仍待。source16未部署，目标未完成。

最新同样本9→10只读Bellman诊断完成，3520396已退出勿重启：四接口各4096共同非终端/348终端、全replay字段及固定父next-actions相同，八checkpoint与输入hash重验、网络/零bootstrap/组件加和与图核验。0更新/physics，原live不改。固定父动作pair-all5差9.97/36.21/15.42/74.59→97.93/135.48/90.27/140.16；自身policy折扣目标差389.45/131.43/95.79/141.07，均大于平均熵项绝对值52.00/10.51/9.60/34.46。负Q允许，不称真实低估/因果证明，终端MAE前三升/VMC降；有符号TD近0不能替代绝对误差。runs/matched_bellman_targets_cycle09_10_v1/REVIEW.json及docs/PUBLISHED_MATCHED_BELLMAN_TARGETS_20261025.md/.json。原八learner与11审计继续；nominal116/120，原2210514/2210515继续。source16未部署，等完整10/11科学review；目标仍未完成。

最新all5第10轮四路已完整归档且原audit/9→10 review完成，四learner均进入原11：steps532944/533471/534320/535026；Task5/18/15/17、Strict5/17/15/17（各30），父9 Strict10/18/15/17。120完整条件/terminal/model及checkpoint hash核验，奖励重建/网络不变通过，图已检查。末1000 critic loss194368/1133707/890992/1590253均较9增，Q−4093/−16747/−11522/−17506；terminalMAE2949/6869/9107/8213（VMC下降，其余升）。不把Q上界超限0/0/8.82/2.10%当校准或修复。原11保持，1346884/1346887继续等11，不提前部署source16/改算法。
新SAC Direct完整5只读audit完成、2862832退出：265240步，Task/Strict0/30、全approach；loss69660→216712、Q32510→59261、terminalMAE1738→3445，非健康收敛。30条件/模型/terminal、冻结输入/奖励/网络不变及图核验；0physics/更新，原6继续。runs/diagnosis_sac_direct_cycle05_v1/REVIEW.json。
冻结9参数矩阵已9/9结束，旧4191390/1836087退出勿重启；与原Direct确定性3例合成12例，Strict0/2/2/2（各3），全55s/三审计，无机器安全违规。新VMC短/长27.52/32.40s、47.1968/46.6636Nm、接触NA/100%(6.62165s)，被动carry失败；新VMC审计输入hash重验，四checkpoint/模式核验。COMPLETE_FOUR_INTERFACE_REVIEW.json留证。原Direct随机9例Task9 Strict7和2安全违规独立保留，不替代确定性0/3，不选最终Tref。报告docs/PUBLISHED_BELLMAN_CYCLE10_REVIEW_20261025.md/.json。目标仍未完成。


最新contact v2原协调器2530701/末worker2249466已正常结束，勿重启：12/12完整55s对照全部精确通过，共1320万子步，复用1项/新增11项1210万子步。COMPLETED_REVIEW核验FINISHED/注册/source/12条件集合及原始MJB/journal/terminal/substep字节hash；原数组比较收据通过，set规范仅robot_parts。保留v1失败。当前source14三原接触文件与原07/15相同已确认。
已准备source_train16但未部署：从15只替换已验证的3接触读取文件（audited_velocity_env、validate_office_apparatus、published_compliance_episode），内容与contact_candidate_v2精确相同；learner/Adam helper/trainer/Bellman保持15，780source hash及保护manifest核验，4接触测试通过。组合无新physics/updates，下一阶段须当前10/11完整科学review及独立登记，不自动派发/改live。产物runs/combined_performance_preparation_v1，证据docs/PUBLISHED_CONTACT_VALIDATION_COMPLETE_20261025.md/.json。
GPU_60S_02含正式训练及固定VMC推理、不含辅助学习：60样本/77.19s均值35.13/39.40/30.07/33.97%，min全0；八PID身份及真实增量核验，50%未达。四CHEQ14仍10收尾；SAC Direct5已归档进入6，其余SAC3继续，非收敛。VMC9被动完整55s carry失败，其余在途/整组三审计仍待，参数矩阵6/9。目标仍未完成，指定ESN仍缺。


最新source_train15准备完成但未部署：只在CHEQ实际load_state_dict把59个Adam scalar step归CPU，SAC分支不改。独立adam_resume_preparation_v1进程2122767已结束，四真实all5 parent按CUDA入口恢复、更新间保存/重载、后续两更新的完整数值state/metrics/agent与alpha梯度均精确相等；16辅助更新、0physics、父checkpoint/replay不变、无权重保存导入。真实SAC Direct4恢复对照不变（0更新），不外推SAC提速。原/候选779/780 source及24parameter/150上游/128robot资产全hash核验，仅learner及新增helper差异。CANDIDATE_PROTOCOL是准备状态，需当前10/11完整科学review再登记下一阶段；不是等待新用户许可，不自动派发。当前CHEQ14、SAC09及原评估继续，50%/收敛/最终比较未完成。证据docs/PUBLISHED_ADAM_RESUME_PREPARATION_20261025.md/.json，产物runs/adam_resume_preparation_v1。


最新采样/性能候选：live_bellman_profile_v1四路60s采样完成、1600842退出；每路14995样本中11996空栈/2999非空，REVIEW显式两分母，不把空栈当GPU空闲或非空栈当已识别主线程时间。正式resume map_location=CUDA使noncapturable Adam保留59个CUDA scalar step；_get_value同步开销可复现。独立adam_step_device_validation_v1四接口×两顺序×两arm×256=4096辅助更新已完成，1825205/6/7/8退出；仅step移CPU，完整数值state/agent gradients/RNG及其他位置精确相同，父replay不变，0physics/无权重导入。四helper+五profile测试通过。共享计时speedup0.9634–1.1772，不称普遍提速/50%达标。候选未接入正式adapter/runtime，当前10/11不改；后续边界需恢复/序列化入口验证。证据docs/PUBLISHED_ADAM_RESUME_PROFILE_20261025.md/.json。
Admittance9三代表条件已完成九份审计及输入hash核验：Task/Strict2/3，被动carry失败；短/长45.04/45.32s、峰矩51.2252/52.6288Nm、接触NA/100%(5.03325s)，无机器安全违规。长比nominal42.48s慢，非完整cohort/收敛。ADMITTANCE_COMPLETED_REVIEW.json留证；evaluator RESULTS历史audit_completed=false早于后处理，未修改，以后续独立收据为准。原790746结束勿重启；参数矩阵6/9，4191390转VMC1836087 CPU13（重验）。contact v2现10/12精确通过、VMC短期1884386继续，未部署。四CHEQ14及四SAC09继续，auditor1346884/reviewer1346887等完整10/11；GPU50%、最终收敛/SPT/指定ESN比较仍未完成。


**最新实际训练优先于下方仅准备快照：** all5 Bellman在线stage10/11已启动于runs/bellman_minimum_online_seed20261025_v1/source14；四learner1325445/1328516/1333006/1338945真实更新10，dispatcher1316612正常退出、archive1349161。actor原pair及LR3e-5、权重/Adam/alpha/RNG/replay/gamma/batch16384/UTD2保留，仅Bellman目标2→5和新阶段聚合history变化；9worker每路不变。Impedance learner CPU54、workers14–22留CPU13给在途参数评估，其余原CPU。科学review BELLMAN_ONLINE_SCIENTIFIC_REVIEW_V1明确允许剩余固定9参数评估与新训练并行，父checkpoint不变，不取消/重选。无辅助权重/STOP，原SAC09继续。7资源阶段+2诊断target测试、首36MJB/dt/plan和父state保留核验通过。
Direct9随机三seed×三代表条件9/9全55s三审计已完成，旧590268/9/70及evaluator退出勿重启；Task9/9 Strict7/9、两短期机器安全违规保留，长期三seed时间53.40/52.84/25.28s，舒适77.38/80.59/100%。原确定性0/3保留，图已检查，非完整cohort/收敛。审计1346884/reviewer1346887按实际target5等待完整10/11，3h仅observer保护。GPU正式窗口均值40.63/36.95/37.95/30.93%未达50%，无辅助学习；contact v2已9/12精确通过未部署。证据PUBLISHED_BELLMAN_ONLINE_STAGE_20261025.md/.json。source14manifest的prepared_only是构建时记录，不改冻结manifest；实际启动看新EXECUTION。目标仍未完成。

最新source_train14 / bellman_resume_preparation_v1仅准备、未选/启动在线阶段：checkpoint显式all5 Bellman规则，原actor pair保留；6+8测试、四真实父9完整state/序列化恢复和下一更新精确等同离线候选验证通过（8辅助更新、0physics、无权重导入），1019496退出。父state/replay/moments/RNG不变，仅规则及新阶段聚合history变化；source14仅learner/trainer/helper三差异，全部hash与保护manifest核验。CANDIDATE_PROTOCOL缺最终科学decision，禁止自动派发，不称论文原样/等价优化。证据PUBLISHED_BELLMAN_RESUME_PREPARATION_20261025.md/.json；原四SAC09继续，source13亦未部署。
Direct9随机短期三seed Task3/3、Strict1/3（先前“一成功两失败”指Strict）；seed41/43外穿透0.212277/0.223520mm超原0.2mm门槛，seed42为0.118590mm。均完整55s，原协调器后处理审计仍等三条件；长期继续，不覆盖原确定性失败。SHORT_FIRST_PHYSICAL_REVIEW.json留证。contact v2现8/12精确通过未部署，cycle9参数继续Admittance。目标仍active。

最新补充：Direct9固定随机诊断首个被动条件三seed均完整55s/1375动作、Task/Strict成功（原确定性该条件失败），但原协调器后处理审计仍待整组三条件结束，不推广其余条件/收敛。PASSIVE_FIRST_PHYSICAL_REVIEW.json留证。Impedance9三确定性条件现三审计全通过，无机器安全违规；被动失败、短/长13.04/20.04s成功，峰矩46.2532/51.7783Nm，接触舒适NA/22.0727%。IMPEDANCE_COMPLETED_REVIEW.json已冻结；剩余参数评估继续。

最新SAC完整归档只读审计已结束：Direct4、其余2（步223990/146028/144265/144759），Task/Strict0/0、17/17、11/11、17/16；120条件terminal/model及奖励/网络不变验证，图已检查。四critic loss/Q较cycle1增加，不称健康收敛；原四SAC09仍运行，无STOP或新优化干预。审计runs/diagnosis_sac_latest_completed_v1/REVIEW.json。
新固定Direct9随机动作诊断fixed_direct_cycle09_stochastic_v1已启动，三seed2026102541/42/43×原三0000条件共9全55s，原确定性0/3保留对照。coordinator590268/590269/590270、evaluator590314/590313/590312，CPU0/1/2（重验）；source stochastic_evaluation_v1，原live runtime未改。真实checkpoint预检同seed精确/异seed不同/确定性seed无关/网络不变通过；启动MJB/dt/ck和首journal已核验，尚无完整结果。勿按新模式挑最好seed替代确定性评估。
旧cycle7矩阵已12/12完成、803220退出勿重启，Strict0/2/2/2（各3）、三审计通过；新VMC短/长27.48/31.88s、47.1963/46.6762Nm、舒适NA/100%。当前cycle9参数评估仍运行；contact v2已7/12精确通过未部署。证据PUBLISHED_SAC_HEALTH_AND_STOCHASTIC_EVALUATION_20261025.md/.json。最终目标仍未完成。

最新actorLR8/9四接口及原整组audit/reviewer已全部正常结束，旧四learner勿重启；9 Task12/18/15/17、Strict10/18/15/17（各30），四critic loss继续增加。完整review为runs/ACTOR_LR_FINAL_SCIENTIFIC_REVIEW_V1.json。
新bellman_minimum_cycle09_v1有限all5目标诊断完成、四辅助343783/343785/343787/343805退出，40000更新/0physics/无权重导入、同state/RNG/replay/采样验证与图通过；真实两更新preflight通过。all5相对pair降低四Q/MAE，但Admittance MAE仍高于父，CHEQ最低权重比例仍100%，不是修复。未选/启动下一在线CHEQ阶段，不自动用source13；作为算法消融候选，不称论文原样。四SAC09继续。
Direct固定9三代表全55s/Task Strict全失败于approach，三审计通过；原3574939已退出，勿重启。剩余三接口固定9 coordinator4191390/Impedance4192870 CPU13顺序运行（重验），source12/audit_v6、checkpoint/MJB/dt原合同。原7矩阵9/12、VMC继续CPU54。contact v2现6/12精确通过，未部署；nominal96/120。
GPU含辅助60样本均值61.03/54.87/56.73/54.52%、min12/0/12/1；非正式纯训练吞吐且辅助已结束。证据PUBLISHED_ACTOR_LR_FINAL_AND_BELLMAN_PROBE_20261025.md/.json。指定ESN仍缺，收敛/最终对比未完成。

最新Impedance也完成原9/492221并正常退出，旧923788勿重启；Task/Strict18/18（各30）、被动/短/长0/10/8，reward−0.49960。ck sha4851052f…及30条件terminal/model已核验。原audit已收Direct/Impedance，尚等Admittance/VMC，不把Direct回落推广四路。

最新Direct9有限criticLR诊断完成、3798731退出：同完整state/moments/RNG/replay，criticLR
3e-4/3e-5各5000辅助更新；actorLR3e-5/alphaLR3e-4不变但actor/alpha仍在副本学习。3测试及
实际恢复/采样hash、父replay不变验证通过，0physics/无权重保存导入，图已检查。Q1335.07/1311.73、
terminal MAE375.82/307.13，两个Q均增、上界超限不一致；不据此部署criticLR或推广四接口。
证据PUBLISHED_CRITIC_LR_DIRECT_PROBE_20261025.json；runtime/critic_lr_probe_v1，正式9未改。
辅助前GPU60样本8.25/22.75/30.50/40.27%，四卡50%未达。原整组9审计仍待其余归档。

最新Direct完成原actorLR9/491694，旧919723正常退出，勿重启；9checkpoint已归档sha a9b11de1…，
Task12/30 Strict10/30、被动/短/长6/4/0，8→9 Strict13→10。首/末1000 critic loss230.75→4194.21，
非健康收敛。30条件terminal/model与hash核验；其余三路原9、四SAC09、原audit/reviewer继续。
新独立interim_cheq_cycle09_direct_v1使用释放CPU0/GPU0推理，coordinator3574939/evaluator3575318
（重验），source12/原audit_v6，同3个预选0000条件；首MJB/dt/ck核验、347动作，尚无完整结果。
该登记前瞻指定其余三接口同cycle9同条件，完整归档后派发，不重复Direct；原cycle7矩阵仍CPU54。
contact候选v2现3/12完整精确通过（Direct三类），原2530701转Impedance被动child3472390（重验），
未部署；source13仍只准备。完整group9审计前无新trainer/奖励/阈值干预。
证据PUBLISHED_DIRECT_CYCLE09_AND_EVALUATION_20261025.json；下一步须完成原整组review和余三接口固定9评估。

最新冻结cycle7 Impedance三条件评估完成、矩阵6/12，原coordinator803220已转Admittance evaluator
2887423（重验）。被动carry失败、两主动成功；全55s/物理filtertorque审计通过/无机器安全违规。
长期19.72s/51.2546Nm/4.7492%接触合规，nominal24.0739%、cycle3 37.2665%。不是当前actorLR结果。
新只读fixed_impedance_contact_tradeoff_v2完成、3304773退出：3计算测试、3×110万子步独立复算、
模型/plan/fixture/dt配对及奖励重建通过，图已检查，0physics/更新。joint2/6超阈92.1/79.4%
有重叠；cycle3→7 bounded超幅积分反降.9587→.5315s，舒适惩罚减轻但时间合规变差。
现reward平滑超幅与条件时间比例不等价；总reward7仍更差，不作因果/bug结论。9完成科学review
应同时考虑目标一致性与critic健康，当前9未改奖励/阈值/训练。v1准备缺nominal torque审计未启动，
v2明确nominal缺该项、只验证其物理/filter，勿说三者都有torque重放。证据PUBLISHED_FIXED_IMPEDANCE_CONTACT_TRADEOFF_20261025.json。

最新7/8 soft-target只读诊断已完成、PID2916267退出：八checkpoint网络不变、终端bootstrap零，
0更新/physics。8后继Q528.14/2070.42/780.21/8046.32、平均熵贡献全负；高正target主要来自预测
后继值，无新实现bug结论。8 implied最低权重99.9268/99.9756/100/100%；当前9另存各1000
行为context全0.2，CHEQ仍为混合控制，勿当独立RL成功。不同replay/样本不作LR因果结论。
证据PUBLISHED_ACTOR_LR_SOFT_TARGETS_20261025.json；原9、SAC09和原审计继续，无新干预。
contact v2已2/12完整精确通过，原协调器2530701已转Direct长期child3013076（行动前重验）；
候选未部署，不重复首两回合。source13仍只准备，当前9完成科学review前不派发。

最新8整组只读audit及7→8配对review完成、图已检查；原auditor969396/reviewer969397现等9。
Q均值527.54/2091.51/775.46/8027.20，当前alpha上界超限99.91/42.74/28.93/35.59%；末1000
critic loss231.43/37502.40/19218.17/309861.91，各较7增长，非健康收敛。Direct/Admittance
训练Strict改善不替代价值校准，Impedance丢long0000、VMC丢short0600。保持原9，无新干预/部署。
证据PUBLISHED_ACTOR_LR_CYCLE08_REVIEW_20261025.json；0更新/physics、网络不变与奖励重建核验。

最新四路actorLR cycle8均完成并精确归档，全部进入原9：Task/Strict Direct14/13、Impedance17/16、
Admittance15/15、VMC17/16（各30）；Strict分被动/短期/长期3/6/4、0/9/7、0/10/5、0/9/7。
父7 Strict0/17/12/17→13/16/15/16，改善不一致；非固定策略接受/收敛。四checkpoint hash、
120条件/terminal/model收据核验。原audit969396已启动child2614571读取8；review969397等报告，
勿重复诊断或提前改9。证据PUBLISHED_ACTOR_LR_CYCLE08_TRAINING_20261025.json。

最新contact验证v1正常物理完成首55s后因JSON robot_parts集合序列顺序误拒，旧2014112/2019617均
退出，失败保留；只规范该明确set字段，不放宽其他数组/数值/顺序。4测试和首完整110万子步
重审通过：MJB/journal/terminal/轨迹/filter/torque/逐子步精确一致，完整result除登记provenance及
该set顺序一致。新runs/contact_candidate_validation_v2 coordinator2530701、Direct短期worker2535538
（重验），复用首回合、只新增剩余11；runtime/contact_candidate_v2未变且未部署。勿重启旧v1。
证据PUBLISHED_CONTACT_VALIDATION_RESUME_20261025.json。
Impedance也完成8/450971步并入9，Task17/30 Strict16/30（被动0/10、短期9/10、长期7/10），
较父7 Strict17/30略降；不要以Direct改善概括四路。其余8尾段继续，整组审计等待。

最新Direct已完整完成actorLR cycle8/450444步，Task14/30 Strict13/30；被动3/10、短期6/10、长期4/10
Strict，reward−10.16369（父7−32.91163）。真实归档sha8ca70658…已核验，30条件/terminal/model收据
核验；已进入原登记cycle9，不停/重派。首/末1000更新q_loss211.68→231.43、logged nextQ380.30→527.14，
未健康收敛；整组immutable审计仍等其他8归档。不把训练内成功当固定策略接受或LR因果证明。
新只读fixed_direct_regression_v1已结束、0更新/physics，9条同模型/plan/fixture的固定3/7/nominal
比较及图已检查；reward仍偏好两主动nominal成功，失败间小改善可伴随任务退化。7末记录手部
误差23–34mm超过阶段12mm，不能据此放宽gate；不是当前8的失败诊断。证据PUBLISHED_FIXED_DIRECT_AND_CYCLE08_20261025.json。

最新cycle7固定矩阵3/12：Direct三条件全55s、Task/Strict全失败，stage lift/lift/release；两主动
nominal成功，低力矩不能当改善。物理/filter/torque审计通过，无机器安全违规。旧804667正常退出，
coordinator803220已派Impedance evaluator1952370（重验），勿重启Direct。证据PUBLISHED_FIXED_CYCLE07_DIRECT_20261025.json。

最新独立接触候选验证已启动：runtime/contact_candidate_v2，runs/contact_candidate_validation_v1；
coordinator2014112、首Direct被动worker2019617（行动前重验）。仅验证12条cycle3冻结动作全55s，
source07三文件读取替换；原字段源与live12一致，parameter/robot manifests一致。每次IPC比较obs/奖励
遥测，最终严格比较MJB/journal/terminal/全轨迹/filter/torque/逐子步，失败停该验证，不动训练。
2软件测试+真实归档自比较通过；首156完整interval/124800子步prefix精确一致，**不是完整通过**。
CPU10 nice10单worker、无learner/优化器更新；候选未部署正式训练、无STOP。v1候选未运行保留。
现有四CHEQ12原8/9及四SAC09继续，13仅准备。证据PUBLISHED_CONTACT_CANDIDATE_VALIDATION_20261025.json。

最新接触读取有限对照v1/v2均结束：三类×5状态，编号/顺序/dist/frame及读取前后积分状态精确一致。
v2 CPU计时bulk IDs局部2.33–4.66倍、中位4.55；只测编号提取，不是完整物理/奖励/轨迹等价或GPU提速。
v1 wall共享调度波动，已保留；共30 mj_forward、0 mj_step/更新，正式runtime未改。下一步可在
独立候选验证完整循环/轨迹，不能凭microbenchmark部署。source12原8/9及SAC09继续，13仅准备。
证据PUBLISHED_CONTACT_ACCESS_PROFILE_20261025.json；两probe进程1714191/1749461已退出。

最新只读physical worker采样完成：60s/4895样本/0错误，Direct source12 active-short0600；
observer inclusive53.50%、mj_step叶18.82%，默认排除idle，仅单worker采样分母，不当全局瓶颈或提速。
未改physics/遥测/运行时，无新仿真/辅助更新。证据PUBLISHED_PHYSICAL_WORKER_PROFILE_20261025.json。
四CHEQ12/四SAC09继续更新，原8/9阶段不得提前替换；GPU四卡50%仍无达成证据。

最新后续准备：source_train13 / completed_stage_dispatch_v2已冻结但**未部署或派发**。修复source12
后续factorNone固定要求3e-4的问题，显式登记/核对父LR可原样保留3e-5及完整周期历史，拒绝重复乘.1；
不改plateau/actor/目标/物理合同。5+8共13测试和四个真实低LR准备状态全字段保留检查通过，
0新physics/更新/权重导入，无STOP。证据PUBLISHED_UNCHANGED_LR_PREPARATION_20261025.json；
runs/unchanged_actor_lr_preparation_v1/CANDIDATE_PROTOCOL.json仅结构候选、缺科学review，不是可执行的阶段登记。
当前四CHEQ仍source12运行原8/9、四SAC09继续；必须完成并复核当前阶段，不能提前迁入13。


最新source12在线GPU窗口：60样本/67.60s均值42.22/30.42/31.08/31.48%，min5/9/0/0，无辅助GPU
更新、含固定Direct推理，四卡50%仍未达到。原始ACTOR_LR_ONLINE_GPU_60S_01.json。

**当前实际训练：actor LR新阶段已启动，优先于下方旧快照。** 原critic-reset cycle6/7四路及旧audit/
review全部正常结束并复核：cycle7 Task/Strict0/0、18/17、14/12、17/17，各30，被动全0/10，
四路critic末段loss仍增；不称修复/收敛。新科学review为runs/CRITIC_RESTART_FINAL_SCIENTIFIC_REVIEW_V1.json。
80,000次actor LR有限辅助更新已结束、四辅助进程退出，0physics/无权重导入；小幅数值收益仅支持在线试验。
新runs/actor_lr_online_seed20261025_v1 / source_train12真正更新cycle8，actor LR统一3e-5，
其余权重/critic/alpha/Adam moments/RNG/replay/masks/目标/物理合同保留，不再resetcritic。旧critic_restart
字段仅历史来源。两新完整周期8/9后复核；不是总训练预算或收敛门槛。PIDs Direct919723、Impedance923788、
Admittance927495、VMC932939；coordinator911732正常完成、archive941236（行动前重验）。
source12沿用已证明等价target梯度优化，新完成阶段dispatcher无STOP、必须读完整父归档及科学review。
13测试和真实完整checkpoint/四路状态保留检查通过。不要重启旧source08或live-parent旧迁移器，source11未用。
SAC09四路仍继续。新只读audit969396/reviewer969397等8/9，登记ACTOR_LR_STAGE_AUDIT_V1与
ACTOR_LR_PAIRED_REVIEW_V1；3h仅observer保护，不停训练。证据PUBLISHED_ACTOR_LR_CONTINUATION_20261025.json。
cycle3固定矩阵12/12完成，全部物理/filter/torque审计通过、无机器安全违规，Strict0/2/1/2（各3），
不当完整cohort排名。新cycle7同12条件矩阵已在CPU54运行，coordinator803220、Direct evaluator804667；
冻结source08 cycle7，不是新actorLR策略。nominal75/120，CPU52/53继续。详见PUBLISHED_FIXED_CYCLE03_COMPLETE_20261025.json。


最新边界：Impedance完成cycle7/409721步、Task18/30 Strict17/30、被动0/10，原两轮预算正常退出，
cycle7已归档。勿重启旧981510；其余三路source08仍完成7，四SAC09继续。原auditor900989/reviewer2655393
等待整组；source11继续仅准备，整组科学复核尚未完成。详细证据见PUBLISHED_CONSISTENT_DISCOUNT_AND_PASSIVE_20261025.json。

最新：consistent_discount_fresh_cycle06_v1全完成，四路×两arm×5000=40,000有限辅助更新，进程全退出。
同fresh全learner/采样，对cycle6全部30个完整回合的独立副本匹配Bellman与PBRS gamma .99/.9995；
两项测试和真实奖励重建通过。低gamma组Q/终端误差略低，但两组Q仍增、alpha仍适应，且远期成功
信用骤减；不应用到正式训练。0physics/无权重保存或导入，原replay不变。报告图已检查。
只读被动0900对比：cycle3曾37.32s成功，5carry失败，6/7lift失败；相同MJB/规划/fixture，7首align
29.72s。单条件changing-policy证据，不当固定策略成功或因果结论。详见PUBLISHED_CONSISTENT_DISCOUNT_AND_PASSIVE_20261025.json。
混合GPU60样本均值50.28/12.17/36.73/21.85%，仍不达四卡50%，记录辅助退出，不当纯正式吞吐。
正式source08仍cycle7、SAC09继续；source11仅准备，不提前STOP/协调器，等全部7及原审计/review后继续。


最新奖励尺度有限对照reward_units_fresh_cycle06_v1已完成：四路×两尺度×2500=20,000辅助更新，
0physics/无保存或导入权重/父replay与正式训练不变，四辅助进程均退出。两项测试通过、报告和图已核验。
scale1/.04同fresh actor/critic/alpha/RNG，仅sample reward不同；初始alpha相同导致相对熵压力改变。
换回原奖励单位后缩放组Q/终端MAE更大；温度仍在适应，无长期/在线优劣结论，不应用为正式修复。
证据PUBLISHED_REWARD_UNITS_PROBE_20261025.json。最新60样本GPU均值38.97/43.38/27.17/34.73%，
min均0，四卡50%未实现；CYCLE07_POST_PROBE_GPU_60S_01.json。四CHEQ source08仍cycle7、四SAC09
继续；source11仅准备，原cycle6/7完成并复核前不写STOP/启动performance协调器。


最新固定评估：cycle3矩阵9/12，Admittance被动/主动短期失败、主动长期成功；三项审计通过、无机器
安全违规。长期42.88s/49.95Nm/100%对nominal42.48s/54.16Nm/100%，短期低力矩仍失败。CPU54
现评VMC，evaluator3248872（重验）；nominal64/120。与当前reset cycle6明确分开。

最新：四路critic-reset cycle6全部完整归档、进入原登记第二轮7，auditor900989完成cycle6，
reviewer2655393完成5→6，两者等7；0诊断更新/physics，图已检查。Task/Strict1/1、18/17、16/16、17/16
（各30），Direct严格0→1、Admittance13→16、Impedance不变、VMC17→16，被动仍全0/10。
Q133.87/123.41/326.08/1384.20，当前alpha上界超限0/37.95/99.50/0%；VMC critic仍增长。
不是四路收敛或修复成功，继续原两轮试验，source11不提前部署/勿写STOP。详见PUBLISHED_RESTART_CYCLE06_REVIEW_20261025.json。
SAC第二完整周期只读诊断diagnosis_sac_cycle01_all_v1已FINISHED并退出，Task/Strict0/0、17/16、
14/13、18/18（各30），被动全0/10；Q/loss较首轮增长，Direct99.85%超保守上界，不与不同曝光CHEQ排名。
SAC四路source09仍训练，最新全cache GPU窗口均值39.28/32.17/10.87/28.77%，仍未四卡50%；
ALL_SAC_CACHE_GPU_60S_01.json，含CHEQ周期交替与GPU2评估。新证据PUBLISHED_SAC_SECOND_CYCLE_20261025.json。

最新SAC接续完成：四路都在source09真实更新，MIGRATION_FINISHED已落盘，原协调器已结束。
Direct1010728/Impedance1557140/VMC2397784/Admittance2758791，常规archiver2767227（重验）。
不要重启旧SAC进程或迁移；下方Admittance仍排空是本轮稍早快照。

最新完整周期：Impedance已完成critic-reset cycle6，368471保留步/41250新增，Task18/30、Strict17/30，
与父5相同且成功条件名单无增减；reward −2.25857→−2.41005，同17成功条件平均时间16.65→19.38s。
被动仍0/10，首轮无任务收益证据；当前进入原登记第二轮7，其他方法6尚未全部完成，勿提前截短试验。
新只读配对review PID2655393，runs/CRITIC_RESTART_PAIRED_REVIEW_V1.json，冻结runtime/
critic_restart_paired_review_v1；等原auditor900989生成完整6/7报告，自动比较5→6、5→7、6→7，
0physics/0更新、不管训练生命周期。观察失败不等于训练失败。4项测试与实际parent自比较通过。
历史cycle3报告因缺明确网络不变证据被拒，日志保留，不放宽guard。详情PUBLISHED_RESTART_FIRST_CYCLE_20261025.json。
SAC VMC也已迁入source09并更新，新PID2397784；Direct/Impedance同样在09，Admittance仍旧06排空。
原协调器2370128继续，禁止重复迁移。以上PID行动前必须重验。source11仍仅准备，未部署。

最新GPU窗口：辅助退出后60样本/67.64s均值50.48/23.65/31.15/43.10%，min13/0/0/0，
仍未持续四卡50%；RESTART_ONLINE_GPU_60S_02.json，含GPU2固定评估，source11未运行。

最新：target-gradient实际运行时v2验证完成，四接口两顺序4096辅助更新全used-state/非target梯度
精确一致，0physics/无权重导入，所有辅助进程退出；共享负载提速0.972–1.293倍，不保证在线提速。
source10首次接续协议检查因umbrella含CHEQ/SAC而被错误CHEQ-only guard拒绝，未启动，失败保留。
已新冻结source11（不覆盖10），learner/helper与已验证10完全相同，仅trainer改amendment作用域；
8项软件测试和实际协议验证通过。REGISTRATION_CHEQ_TARGET_GRADIENT_PREPARED_V2仅准备，
**没有STOP/协调器/替代训练**。保持source08原critic-reset两轮cycle6/7，完成科学复核后决定是否采用；
不要提前运行performance协调器截短试验。source11优化不再重置critic，全部学习状态保留。
cycle3矩阵6/12，Impedance两主动通过、被动失败；长期20.64s/51.66Nm/37.27%对nominal
20.52s/52.26Nm/24.07%，三个物理/filter/torque审计通过，无机器安全违规；仍非整体或收敛结论。
CPU54现评Admittance，nominal59/120；原四路CHEQ和四路SAC继续，行动前重验真实进程。
详情docs/RL_PUBLISHED_DIAGNOSTICS_20261025.md及PUBLISHED_TARGET_RUNTIME_VALIDATION_20261025.json。

最新补充：SAC Direct和Impedance均已迁入source09并真实更新，其余两路仍排空。nominal57/120。
四路critic-reset启动后的60样本/66.81s GPU均值57.17/47.87/28.50/33.22%，min2/0/0/0，
辅助更新和profiler已结束，含GPU1固定评估；SAC Impedance启动时间与窗口关系另存证据，不称稳态
独占测量，四卡持续50%仍未实现。原始RESTART_ONLINE_GPU_60S_01.json。

- **最新实际状态：critic-reset四路全部交接成功，原协调器已正常结束。** 当前run仍为
  `runs/critic_reset_online_seed20261025_v1` / source_train08；新Direct1471404、Impedance981510、
  Admittance1373289、VMC1099359已产生真实新steps/updates（行动前重验PID身份）。常规archiver1477077。
  early归档已正常退出无遗漏，父cycle5四个checkpoint全部归档，父进程正常结束；不要恢复旧STOP或重启协调器。
  当前cycle6，仍按登记运行两个新完整周期6/7；两轮结束需自主复核/继续Goal，不把阶段结束当收敛。
- 父cycle5四路Task/Strict为0/0、18/17、13/13、17/17（各30），无健康收敛。新只读阶段审计器
  PID900989，`runs/critic_restart_stage_audit_v1`（冻结runtime/critic_restart_audit_v1）已完成父cycle5
  全报告/图，正等新cycle6/7精确归档；0更新/0physics，三小时仅是observer派发保护，不停训练。
  父Q均值10913.10/6996.29/122751.82/68614.76，末1000更新critic loss约8.18万/13.22万/9008万/1225万。
  网络不变和回合奖励核验通过，图已目视检查。不要把巨额Q解释为高任务回报。
- `runs/critic_restart_early_health_v1`已经结束：当时仅Impedance/VMC有新checkpoint，分别新增
  6000/4000transition、12000/8000更新，Q均值32.07/447.27，当前alpha上界120.64/4709.82，样本
  无超界；in-bag终端MAE32.30/440.51，全来自父replay且当时无新完整回合。图已检查，VMC仍有Q
  增长/loss回升，不是收敛或成功证明。诊断新增父/新终端分栏、精确reward源码上界合同和网络不变检查。
- 60s live py-spy剖析完成：14995样本/0错误，11996空Python栈，2999可识别栈中更新60.32%、
  等仿真25.21%、replay6.27%、checkpoint3.20%、actor3.00%；不能把空栈当GPU空闲或声称全卡提速。
  profiler装在独立tools/py_spy_0_4_1，正式Python环境未改，profiler已退出。
- 新候选 `published_target_gradients_20261025.py` 仅抑制unused target参数梯度，保留actor通过动作输入
  的梯度；**未部署到正式runtime**。`runs/target_gradient_validation_v1`两顺序×四接口×256/arm，
  4096辅助更新结束，完整learner/optimizer/alpha/RNG及所有非target梯度精确一致，只有unused target
  梯度按设计不同。父状态不变、权重丢弃，进程都退出；两顺序提速1.009–1.197倍但共享负载/顺序波动，
  不当在线提速或GPU50%证明。当前critic-reset科学试验的learner源码和其他设置保持。
- cycle3固定中期矩阵3/12已审计：Direct三回合均55s失败于carry、无机器安全违规，physical/filter/
  torque审计通过；active-long接触6.7698s、阈值比例100%，不能替代成功。当前CPU54评Impedance，
  evaluator847406/协调器3686420（重验）。nominal本次55/120。SAC Direct已迁入source09新run并真实
  更新，其他三个仍在原cache协调器2370128排空；不要重复派发。详情见最新诊断文档及
  `PUBLISHED_RESTART_HEALTH_AND_PROFILE_20261025.json`。目标仍未完成，指定ESN仍缺。


- **最新科学修复派发（优先于下方历史快照）**：`runs/critic_reset_online_seed20261025_v1`，
  `REGISTRATION_CHEQ_CRITIC_RESTART_V1.json`，协调器PID429389（行动前重验）。父CHEQ performance v3
  正在cycle5，STOP_REQUESTED是完整周期边界交接；勿恢复父进程或重复启动协调器。新阶段不是精确性能
  接续：仅重置critic/target/critic Adam，保留actor/alpha/它们的optimizer、RNG、replay/masks、reward、
  gamma、batch16384/UTD2和全部physics/control合同。新seed2026102528，每路两个新完整30条件周期后复核。
  不导入辅助权重；critic变化会改变CHEQ uncertainty/mixing输出，规则未改。新阶段cycle history清空，
  父history和checkpoint保留在restart receipt，不能跨reset拼接收敛曲线。初始仅排空，须读MIGRATION/
  LAUNCH/PROGRESS确认实际更新。source_train08未改，准备/协调器冻结runtime/critic_restart_dispatch_v1。
  三种真实接口网络的软件回归和实际Direct完整checkpoint准备通过；这不是已证明的优化修复。
- CHEQ第五完整轮cycle4四路Task/Strict为0/0、17/16、15/14、17/17（各30），平均reward
  −32.889049/−4.035049/−8.756420/−2.836609；全部归档无遗漏。Direct由6/30退化至0/30，
  四路passive仍0/10，不称学习收敛。正式SAC仍由原cache协调器排空，禁止另开迁移。
- `runs/value_bound_cycle03_v1`完成0更新/0physics：120回合奖励/势能望远镜及replay对齐通过，
  四路固定alpha的保守global soft-Q上界3404.05/3654.93/15888.00/18637.88；5critic×4096样本
  超界99.49/51.05/57.64/62.79%。说明该固定policy/alpha价值未校准，不定位某个bug。hidden-clock
  阈值仅作上下文诊断；无时钟critic的terminal MAE也可能含观测混叠误差，不能要求其必然归零。
- `runs/policy_feedback_cycle03_v1`三arm×四接口×1000更新全部结束：冻结actor/alpha显著减弱
  Direct/VMC的短窗增长，但Impedance/Admittance仍增长。固定alpha单独无效，非长期因果证明。
  `runs/fresh_critic_evaluation_cycle03_v2`两batch×四接口×3000=24000辅助更新也全部结束；冷critic
  Q转负且无正global超界，但仍移动、终端误差未消除，不能说恢复收敛或batch256更优。等更新不等采样。
  两批辅助权重丢弃，不作常驻GPU负载。fresh v1因CPU/CUDA不变性比较错误在0更新/0physics退出，
  v2修复比较设备，保留失败；新在线仅reset一因素，未改变batch或引入新的奖励/信息。
- cycle1固定中期矩阵已FINISHED，12/12审计完成：四路passive失败，Direct两个active也失败，
  三参数方法两个active通过；无机器安全违规，不是完整30条件最终比较。新cycle3同12条件/同nominal
  矩阵 `runs/interim_cheq_cycle03_representatives_v1` 正在CPU54，协调器3686420、Direct evaluator3686874
  （重验）；标签前缀改为cheq_cycle03_，无重复cycle1评估。nominal本次47/120，继续CPU52/53。
  没有最终共同SPT参考、指定ESN或完成比较；GPU持续四卡50%仍未证明。

最新补充：critic-reset early archiver PID500618；协调器已写四路边界交接STOP，尚无替代learner，
无MIGRATION_FAILURE。nominal后续49/120。辅助更新结束后的60样本/66.75s GPU均值
34.43/38.67/34.88/39.22%，各卡有瞬时0，仍未达持续50%。原始SOURCE08_ONLINE_GPU_60S_02.json。

以下条目保留此前阶段证据；发生状态冲突时以上方最新条目和真实进程/收据为准。

- **最新GPU replay缓存接续：CHEQ已完成，SAC仍排空，勿重复启动。** CHEQ从performance v2/source_train07迁入
  `runs/cheq_performance_seed20261025_v3` / source_train08；SAC从performance v1/source_train06迁往
  `runs/sac_performance_seed20261025_v2` / source_train09。CHEQ协调器正常完成，SAC协调器PID2370128（重验）。
  四路CHEQ已在新run实际更新cycle4；SAC尚无新learner，旧Direct在cycle2，其余cycle1。旧run的
  STOP_REQUESTED是迁移请求，不可恢复。CHEQ第四轮全部归档无遗漏，新常规archiver PID2660326。
  首次启动因误指向父runtime未包含的协调器文件而退出，未创建STOP/子作业；失败收据保留，
  已用独立冻结runtime/device_replay_dispatch_v1修复。先查MIGRATION_PROGRESS/FAILURE和真实句柄。
- source_train08/09各只改变trainer和新增device cache；分别保留07/06的原learner、算法、physics、
  actor/filter/gate/dt。CPU replay/RNG/checkpoint仍权威，GPU只同步缓存/gather，多占约0.40–0.42GiB。
  两轮反转顺序验证共6144辅助更新全部state/optimizer/target/alpha/RNG/replay/gradient精确一致；
  辅助权重丢弃、进程已结束。9项协议/replay/归档软件测试通过，不把微基准加速当GPU50%达标。
- 新run各有early_cycle_archive迁移期监视器，跟随逐步增加的learner列表，待协调器启动常规
  cycle_archive后自行退出，避免先迁入learner完成周期时漏存；不是另一套训练。旧archiver继续保存父周期。
- CHEQ第四轮四路Task/Strict为6/6、18/17、13/13、17/17（各30），均值−22.61414/−2.24736/
  −10.43662/−2.81063。Direct首次1个passive严格成功，另5个active-short；参数三路passive仍0/10。
  缓存接续后60样本GPU均值40.90/33.22/40.12/32.10%，仍未达50%；所有辅助更新进程已结束。
  `runs/diagnosis_cheq_cycle03_v1`完整只读诊断/图已结束：四路in-bag终端MAE358.05/1063.08/
  21892.57/8474.15，Q均值4607.57/3691.79/32102.17/18220.59，critic继续恶化；下一步重点是价值
  学习稳定性，不能因Direct成功数增加就称收敛。未选定新的科学修复或改奖励/discount/critic信息。
  SAC Direct第二轮0/30，均值−35.57527，全部
  失败于approach，2个原2mm穿透abort，40978新增步。只读诊断Q均值3401.98、终端MAE329.77，
  最近1000更新q_loss624.17，仍恶化；不是健康收敛。runs/diagnosis_sac_direct_cycle01_v1已结束。
- 最新中期固定cycle1矩阵6/12审计完成：Direct三失败；Impedance passive失败于carry，两个active
  Task/Strict通过。active-long完成52.40s对nominal20.52s，接触阈值比例74.48%对24.07%，峰矩
  51.54对52.26Nm，是单条件效率/舒适折衷，非总体改善。CPU54现评估Admittance；nominal31/120。
- `runs/action_value_cycle12_v1`已完成0更新/0physics只读诊断，进程已退出，不作常驻GPU负载。
  cycle1/2同1024状态×12相同候选动作，replay prefix/网络不变；cycle2跨critic分歧中动作均值偏置
  仅解释12.24/32.72/17.83/28.74%，去偏置后所有候选uncertainty仍>.2。不能把问题仅归于共享
  价值偏移，也不能把Q偏好当真实动作改进。正式reward/gamma/mixing阈值未改，无替代修复被选定。
- 上次finite-check接续已全部迁入 `runs/cheq_performance_seed20261025_v2` / `runtime/source_train07`，
  四路已产生真实steps/updates，正在cycle3（第四整轮）。v1正常结束，cycle1/2全部归档无遗漏；
  新归档器继续。迁移保留全部learner/optimizer/RNG/replay/masks/history，只优化finite检查。
- 第三整轮cycle2的Task/Strict分别3/3、17/16、12/11、17/17（各30）；平均reward约
  -27.8272/-4.2768/-13.7767/-2.8037。Direct首次成功但其他改善不一致；所有方法passive仍0/10。
  Impedance active_long0000触发原2mm穿透abort，581步，完整周期新增40456步，其余41250；保留失败。
  `runs/diagnosis_cheq_cycle02_v1`已完成只读诊断/图，Q和critic loss仍明显增大，不称健康收敛。
- SAC四路也已全部完成旧cycle0并迁入 `runs/sac_performance_seed20261025_v1` / source_train06，
  真正更新，正在cycle1；原cycle0严格成功0/16/12/15（各30），每路82500更新。
  `runs/diagnosis_sac_cycle00_v1`已完成。它与CHEQ第三周期不是相同曝光，不能据当前数值排算法优劣。
  **这两套较早的finite-check迁移已完成；最新cache迁移状态看本节顶部，禁止重复派发。**
- `runs/discount_sensitivity_cycle01_v1`四接口×两gamma×2000更新全部完成，总16000辅助更新。
  深复制完整恢复且父状态不变；.99降低Q但终端误差仍大，且1374步终奖折扣约1e-6，.9995约.503。
  只改辅助Bellman gamma，stored reward仍含.9995 shaping；不是完整替代objective，不能选为正式修复。
  正式gamma/reward/uncertainty阈值未变，辅助权重不得进入比较，所有辅助进程已结束。
- Direct固定cycle1的3个中期回合均完整55s失败于lift，physical/filter/torque审计已通过；
  active_short/long的nominal成功，不能用RL低峰矩/高接触比例替代完成。CPU54现评估Admittance，
  整体6/12已审计；nominal矩阵本次31/120，继续CPU52/53。未选最终T_ref。
- source07迁移后无辅助训练窗口GPU均值38.33/30.98/30.08/32.22%，50%目标仍未实现；
  不能把finite-check微基准加速或已结束辅助作业写成在线达标。原始记录SOURCE07_ONLINE_GPU_60S_01.json。
- `runs/soft_target_mixing_cycle01_v1`只读诊断已结束，0更新/0physics；cycle1样本四路CHEQ几乎
  全部映射到最低混合权重0.2，近期每路1000真实transition也全部context0.2。熵项平均为负，
  不可把巨大的正Q解释成该样本的正熵奖励。绝对uncertainty阈值的奖励尺度适配仍需验证，未修改。
- `runs/learner_profile_cycle01_v1`有限64更新剖析已完成且不保存权重；finite检查约占27.9%、
  replay采样约14.6%调用时间。最新66.5s GPU均值42.13/47.35/37.87/39.71%，未达50%。
- `runs/concatenated_finite_check_validation_v1`因验证脚本反复恢复时共享CPU optimizer step tensor
  而未通过全状态等价；失败保留。v2 deep-copy每个恢复并检查父状态不可变，四路全部通过。
  旧terminal/batch辅助工具也缺同样防御复制，源码已修复；旧结果不再称optimizer完全一致的对照，
  未重写旧runtime/结果，也没有把辅助权重放进正式训练。source_train07只变finite helper。

- 历史主训练 `runs/cheq_performance_seed20261025_v1` / `runtime/source_train06` 已在cycle2结束并迁出；
  完整cycle0/1/2历史保留。source_train06只减少有限值检查同步，不改学习更新。
  性能迁移保留network/optimizer/target/alpha/RNG/replay/masks/history，区别于早期LayerNorm重启。
- 第二完整周期（cycle1）严格成功0/17/13/16（各30），上一周期0/18/12/16；平均return约
  -33.0687/-2.2419/-10.4761/-4.6481。改善不一致，不能宣称充分学习/收敛。critic loss和Q仍增长。
  `runs/diagnosis_cycle01_dispatch_v1`已完成，结果在 `runs/diagnosis_cheq_performance_cycle01`，
  四路cycle1精确checkpoint已归档、无遗漏，不重复执行该监视器。
- SAC四路已由原协调器迁入 `runs/sac_performance_seed20261025_v1` / source_train06，
  正在cycle1。原 `runs/sac_layernorm_seed20261025_v2` 四路均正常结束，checkpoint和父收据保留。
  **旧run的STOP_REQUESTED是协调迁移，不是取消Goal；先查原进程、LAUNCH/MIGRATION收据，禁止重复派发。**
- 正式训练占52核；CPU52/53继续执行 `runs/nominal_four_interfaces_cohort30_v1` 的120回合固定矩阵，
  不是空闲资源。逐回合physics/contact/filter/reward审计和失败保留，未完成矩阵不选最终T_ref。
  CPU54为只读诊断、轻量协调和有限辅助GPU作业共享。
- `runs/terminal_fitting_replication_v2`两个seed2026102511/12、四接口、两采样variant均已完成，
  SUMMARY.json已落盘，所有辅助dispatcher正常结束。terminal10%降低in-bag误差，out-of-bag基本不变，
  普通误差略升；这是固定标签拟合，不是策略改善。权重不得混入正式比较，不再当常驻GPU负载。
- `runs/batch_sensitivity_cycle01_v1` 四接口各两variant×2000更新均完成，SUMMARY.json已落盘。
  同cycle1父状态直接切batch256使in-bag终端误差高于16384；是等更新非等采样、继承大batch状态的
  离线敏感性，不能宣称官方小batch较差或在线最优，不改正式batch/reward/replay；辅助进程已结束。
- 当前CPU54运行 `runs/interim_cheq_cycle01_representatives_v1`，冻结四个cycle1 checkpoint，
  每接口在每类首个登记条件（passive_corner/active_short/active_long的0000）评估，共12回合，
  配对固定nominal同条件记录，含physical/filter/torque审计。原训练52核和nominalCPU52/53保留。
  这是中期固定策略诊断，不是完整30条件最终比较，不选择最终T_ref。先查LAUNCH/PROGRESS/FAILURE，
  不把CPU54当空闲或另开重复评估。源码冻结 `runtime/interim_matrix_v1`、audit wrapperv6。
- `runs/interim_impedance_torque_audited_v2` / wrapperv6完整55s透明性验证已通过：原checkpoint、
  原cuda:1、同条件，物理/actor/接触精确一致，1375次filter及13750次公共力矩投影重放误差0，
  与1100000物理子步实际执行器力矩精确对应；幅值/slew/原limits通过。该回合scale<1次数0，
  激活幅值投影分支由单测覆盖。不是native reference/wrench/Jacobian重建，也不是最终策略验收。
  v1仅排队未physics即取消，旧收据保留，不恢复；本次真实审计已结束、释放CPU54。
- `runs/parameter_cycle_audit_v1`此前90回合123750次参数shield精确重放通过，rate限制约
  53.87/70.23/53.32%、energy限制0；参数确实改变。重放保存的storage state不等于全局被动性证明。
- 最近无辅助拟合的周期末尾60s GPU均值22.80/25.18/15.93/14.82%，当时每learner只剩1–3个回合；
  最新完整并发加batch诊断60s均值50.20/50.03/50.92/55.85%，该窗口平均达标但含辅助作业。
  batch辅助结束后最新在线加单次GPU0推理窗口42.67/36.47/37.93/39.87%，仍未达50%。
  需区分完整并发/周期尾部/辅助负载，GPU性能问题未解决。
  指定ESN仍缺；无充分收敛、完整最终矩阵或ESN比较结论。详见执行/诊断文档。
- 持续 Goal 的最新授权优先：用户已将论文选择、必要方法/接口适配、三类任务集上的仿真和
  四卡4090训练决策交给当前 agent，取消总训练步数上限，要求训练至改善后稳定并公平比较。
  不再就上述已授权事项重复询问。仍须保留原始任务/安全判据，记录新模型来源和所有适配，
  不把新编译模型冒充缺失历史MJB，不把短窗口平坦或阶段结束当作收敛。
- 用户已授权搜索并尽量忠实适配已发表data-driven柔顺控制方法、设计任务奖励、训练参数RL/
  直接动作RL至有学习改善后的reward稳定且loss诊断正常，然后与指定现有ESN在训练集比较。
  此授权覆盖本会话早先的只读等待要求；具体接口适配按上述最新授权单独登记。
- 本轮训练集SPT按用户新要求，用全部登记结果中最短严格成功完成时间作共同T_ref，称为
  `SPT_empirical`；明确事后参考及训练集范围，不重写旧实验或冒充预登记规划参考SPT。
  力矩参考阈值可经验登记/先行校准，但不按方法或最终排名反调；无人接触仍记NA。
- 读 `docs/RL_PUBLISHED_BASELINE_SELECTION_20261025.md`：候选来源、官方代码SHA、
  真实依赖缺口及新指标工具。该筛选文档记录的是当时的依赖缺口；现在新source runtime和训练已启动，指定ESN仍未定位；
  不得重新生成不同模型充当归档模型。CHEQ的控制混合上下文属于算法适配，须明确登记；
  不引入障碍物真值等部署不可得actor输入。

## 当前 RL 交接与服务器授权（2026-10-25，优先于历史资源约定）

- 接手 RL 先读 `docs/RL_SERVER_START_20261025.md`（项目介绍、4卡并行、当地启动入口），
  再读 `docs/RL_SPT_TRAINING_HANDOFF_20261025.md`（reward、优化器、收敛和审计）。
- 关于两篇柔顺控制论文的迁移判断，继续读取
  `docs/RL_TWO_PAPERS_TRANSFER_ASSESSMENT_20261025.md`：只采纳参数残差、历史本体输入和
  privileged critic 分栏等设计原则；论文平台的动作、奖励、阈值和结果不能直接当作 FR3 配置。
- 用户更正服务器有 **4张RTX4090、55核CPU**，要求尽量利用算力、多组并行；服务器 agent
  自行确认当地路径/设备并执行，无须向本机 agent 提供地址。**该新授权覆盖下文及旧 skill
  中“本机计算、服务器只归档”的限制。** 不因此修改旧run收据、物理/MJB、gate、actor输入或dt。
- 新入口初始支持四路独立learner、一卡一路、四接口×三seed、每方法每seed最多百万真实步；
  先实测完整回合及真实更新，再扩大并行。服务器逐job登记GPU UUID、CPU集、RAM/显存、
  环境版本与hash；本机3GiB限制只适用本机，服务器新run默认每路8GiB/禁swap，按实际内存准入。
- 本次只发布方案/代码，未启动训练。SPT导向reward是训练代理；正式完成时刻/T_ref和人体
  舒适阈值仍待登记/标定，不得将其写成已有的正式SPT/安全认证结果。

## 非 RL 重评与学习诊断（2026-10-26 补充）

- **用户最新主路线**：仅用扩展采集的新增30条（24train/6val），采用历史固定储备池＋解析ridge
  的ESN训练方法，与从头训练的普通RNN/MLP公平比较。读`docs/NONRL_NEW30_FAIR_COMPARISON_20261026.md`。
  当前`nonrl_new30_fair_20261026_v2`三方法×三seed×12候选全部训练完成，9模型选择与验证动作重放
  已独立审计通过；原协调器在2026-10-26 07:16 UTC进入108闭环回合，继续评测12个
  预登记新条件。禁止重复派发；先查service/execution/progress。旧55条梯度ESN和未启动56回合修复组
  保留为历史诊断，不再自动接续为主路线。数据、方法选择和测试曝光边界按新登记执行，不承诺ESN获胜。
- 该非 RL 会话的 Goal 仅含非 RL；集群 RL 由另一会话按顶部最新交接独立执行。用户授权本轮 `T_ref` 取整个冻结矩阵中
  Task AND Strict 成功回合的最短完成时间；这是后验参考，不证明最优时间。覆盖上方旧的待登记说明，
  不改变 RL 正在运行的协议。舒适阈值采用每关节执行器幅值的 50%、实际人体接触 dt 分母，
  是经验代理而非人体舒适标定。完整定义见下述标准文档。
- 先完成 `nonrl_spt_matrix_20261025_v4` 的 64 条评测和审计；不能覆盖原回合、重复启动或据中间结果宣称优越。
  若 proposed 优势有说服力，再扩展公平非 RL baseline/复杂场景；否则先审计采样覆盖，再检查学习和收敛。
- 数据/学习修正使用独立 run；全体 primary 学习方法共享数据、预算和选择规则。已检查过的条件
  不再作为修正方法的未见测试集；任何新确认性比较须提前冻结新条件，保留全部失败与非优势结果。

## 旧产物清理状态（2026-10-26 用户授权）

- 用户要求删除当前新指标研究不再使用的旧实验输出；已按文件清单清理38,960项，释放约416GiB。
  先读 `docs/STORAGE_CLEANUP_20261026.md` 及其两份删除清单；历史execution中的路径不保证仍存在，
  不自动补下载全部旧产物。被裁剪的中间checkpoint目录即使还有JSON也不代表能续训。
- 当前64回合SPT矩阵、七模型复测依赖、数据/示范来源、共享runtime、RL新协议来源和最终模型
  均保留并核验。此例外仅针对此次明确授权的旧产物；当前研究仍保留完整失败证据。
- 空间阻碍已解除，56回合dry-run准入通过；清理本身不等于物理复测完成，未启动新仿真。

## 当前评估标准（2026-10-25 起）

用户已将本项目的人机柔顺控制评估标准改为：优先保证人身安全、机器安全和任务完成，再比较完成效率。
后续 RL、ESN、经典控制和其他方法的正式对比必须读取并遵守
`docs/EVALUATION_STANDARD_SPT_20261025.md`：主效率指标使用 **SPT（Success-weighted Path Time）**，
不再使用 SPL 作为主效率指标。主结果必须同时报告 Task/Strict success rate、SPT、峰值广义力矩、
人体实际交互期间的舒适力矩合规比例，以及机器安全违规率。不得用 reward、低力矩但未完成任务，
或无接触时段的低力矩比例替代这些指标。SPT 的参考量、舒适力矩阈值、接触分母和安全门必须在
实验开始前登记并冻结，不能根据测试结果回调。

## 每次开工前与存储偏好

- 本仓库任务使用 [sii-research-sync](skills/sii-research-sync/SKILL.md)。先查询远端分支并
  获取、读取 `main` 和 `baseline` 上的 `UPDATE_LOG.md`，记录 SHA 和与本任务有关的更新，
  再开始研究或修改。分支／日志缺失须如实记录，不自建、不使用陈旧引用冒充最新状态。
- 历史本机计算/归档默认如下；本轮服务器训练服从上方2026-10-25新授权。既有文件共享位置为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`。
  源码存 `source/<commit>/`，实验存 `runs/<branch>/<run-id>/`；使用独立目录与 hash 核验，
  不覆盖既有服务器 runtime。允许本地工作副本和缓存，历史数据不自动迁移或删除。
- 新更新文档的代码与产物位置优先指向已核验的服务器绝对路径，同时保留实际计算主机、
  Git SHA、环境版本和源/产物 hash。未上传的文件明确写“仅本地、待同步”；不改写历史执行记录。
- 每次收工重新读取本文件并执行以下流程。若其他 agent 有用户明确指定的 baseline 分支
  工作约定，遵守其授权；不得擅自把 baseline 全分支合并到 main。

## 每次交付前

1. 检查分支、远端、工作区和并行任务，保留他人的改动；通常只提交本次任务的文件。
   本次首次同步另获授权纳入截至 2026-09-30 的已有研究积累。
2. 在 `UPDATE_LOG.md` 顶部增加记录：日期、修改目的和文件、验证、研究结果与局限、未完成项。
   不以任务阶段名或文件名推断成功，不把开发结果写成正式结论。
3. 做与改动相称的验证，检查暂存差异、大文件和敏感内容。仅为答疑且无文件改动时，不必造空提交。
4. 显式暂存目标文件、提交，检查远端 `main` 是否前进，然后正常推送到 `main`。
   不使用 force push，不重置或覆盖其他 agent 的工作；必要时安全整合远端提交。
5. 核对远端包含新提交；最终回复说明提交号和更新日志位置。若认证、网络或冲突阻止发布，
   如实说明本地提交和远端状态，绝不声称未完成的 push 已成功。

## 产物和实验边界

- **2026-10-16用户开启持续Goal**：用户明确要求持续推进四类RL直至有可验证收敛证据，
  遇到问题自主诊断修复。该新授权承接原15小时训练任务；旧run仍按原截止保留真实收据，
  后续使用独立登记的有限阶段预算，不把旧窗口结束或阶段跑完当作Goal完成。允许有记录的
  超参数/训练奖励/训练任务调整，最终物理/MJB、Task/Strict gate、canonical48输入、公共
  filter、执行器限制及dt5e-5保持；本机计算、服务器仅归档。当前stage01登记25步回报、
  UTD1、四方法各新增最多11k交互、24小时派发保护、单模拟器/3GiB/禁swap。后续阶段依据
  证据登记，不自动无界派发；完成仍须训练收敛、四方法完成及最终独立测试/审计。

- **baseline验收目标（用户2026-10-10再次澄清）**：要求实现正确、调参有充分且可审计的
  依据、比较条件公平，不要求baseline在复杂任务中一定成功或解卡。排除实现/调参缺陷后
  仍卡住，应保留为该方法在所测条件下的失败；不得为强行过关持续添加手工恢复机制、改环境
  或无限追加搜索。完成已登记的有限调参并如实报告证据和局限，不能仅凭卡住就断言实现有错，
  也不能跳过实现与调参核查直接宣称proposed优越。

- **历史本地计算限定（2026-10-09；本轮被2026-10-25服务器授权覆盖）**：新的RL baseline修复、训练、仿真和分析
  全部在本机运行，禁止使用Spark算力；这覆盖下方历史批次的服务器计算授权。
  服务器只可做既有文件读取/传输/归档，不启动或恢复旧训练队列。先测本机内存和吞吐，
  再登记有限预算与并发；保留OOM保护和失败，不以占满GPU作为进展。
  本轮`baseline_local_rl_20261009/campaign_v2`在完整单回合预检后登记本机两路并行，
  每路最多一个模拟器/3GiB/禁swap，数值线程1，合计最多6GiB；启动可用内存至少7GiB。
  以其`LOCAL_RESOURCE_AMENDMENT.json`为准，不外推并发，也不与原单路调度器重复启动。
  **2026-10-10经典搜索资源调整**：用户指出本机利用不足后，
  `classical_boundary_search_20261010_v1`允许在原回合及审计结束的安全边界交接至本机2路。
  每路单线程/3GiB/禁swap、分别绑定CPU1/6，首次派发可用内存≥7GiB、已有1路时≥4GiB；
  共最多6GiB worker上限，仍占用同一全局仿真锁。以该run的`DISPATCH_V2.json`为凭据，
  原90回合/参数/条件/seed/worker来源/排序规则不变，不重复已完成回合，不启动服务器计算。

  **2026-10-10过夜15小时baseline接续**：用户授权一次性15小时窗口，
  `sii-overnight-baseline-20261010.service`先等待上述经典90回合自然完成；随后在全局锁释放、
  可用内存≥7GiB且没有活动RL服务时，从已保存的RL checkpoint创建独立
  `outputs/baseline_local_rl_20261009/overnight_15h_20261010/`并接续。协调器不持有仿真锁等待，
  不覆盖旧`running`收据；RL每路仍1线程/3GiB/禁swap、服务器不计算，15小时是有限安全窗口，
  不是收敛或成功条件。经典与RL失败均保留，最终比较需独立审计后再做。

- **2026-10-11恢复防复发**：用户在发现昨夜启动失败后重新授权本机继续RL并监视。
  使用独立新run保留失败；协调器不得持有全局仿真锁调用会再次获取该锁的子进程。
  子失败必须传播非零退出码，实验失败收据优先于systemd的success；启动后核对真实steps/
  updates/完整回合/checkpoint，不能仅凭active宣称推进。停止用独立STOP_REQUESTED在回合
  边界落盘，不向整个进程组发送停止信号。当前两路3GiB/禁swap/1线程限制不变。

- **2026-10-13公平比较加速（用户新授权）**：`fair_comparison_20261013_v2`可按
  `dispatch_v3/REGISTRATION.json`切换为本机最多4路独立回合，CPU1/6/2/7、每路1线程、禁swap。
  先完成当前子作业并保留31个已完成拟合，再交接原全局锁；不改冻结source或39拟合/288回合协议。
  第一个原计划ESN完整回合测内核cgroup峰值（含审计压缩），只有保留≥2倍余量时神经策略
  worker才用1.5/2GiB上限，否则3GiB；经典/RL保持3GiB。派发须满足
  `MemAvailable ≥ 新worker硬上限 + Σ(运行worker硬上限−当前cgroup内存，最低0) + 0.75GiB`。
  上限4路不等于必须开4路；内存不足等待，基础设施失败停止新派发并收完其他在途回合。
  旧STOP_REQUESTED仅按登记hash消费为本次交接，新停止入口DISPATCH_STOP_REQUESTED。
  不重算完成回合、不延长原48小时派发截止、不使用服务器算力，不关闭用户桌面应用。
  **同日实测补充dispatch_v4**：完整55秒ESN的内核峰值1,159,131,136字节，原粗档位会
  将所需2.16GiB向上取整至3GiB，妨碍并行。v4改为1.5–3GiB间每0.25GiB一档，保持
  ≥2倍峰值，神经worker初始2.25GiB。其他类别先3GiB，在该类别完整回合测得峰值后
  按同一规则下调；取已完成完整回合峰值最大值，短回合不降低上限。同样的内存准入/
  总4路上限/固定实验预算；复用39拟合、已完成回合和原pilot。v3的停止文件仅用于登记
  交接，当前停止入口为DISPATCH_V4_STOP_REQUESTED。以dispatch_v4/REGISTRATION.json为准。

- **Spark显示配置保护（用户2026-10-09明确要求）**：保持Xorg自动识别显示器。
  `/etc/X11/xorg.conf`当前不存在，旧强制headless/HDMI配置仅存为
  `/etc/X11/xorg.conf.sii-backup-20261009`，不得为训练、EGL渲染或远程访问恢复它。
  已恢复时实际输出为`USB-C-1`、2560×1440约60Hz；这是观测值，不应硬编码端口/模式。
  研究任务不得修改Xorg、GDM、GRUB、显示驱动、显示分辨率或创建强制虚拟显示配置；
  如确需系统显示变更，必须有用户针对该变更的新授权。计算使用现有离屏运行时。
  详见`code/mujoco_6d_vmc_benchmark/docs/SERVER_DISPLAY_INCIDENT_20261009.md`。

- 不提交凭据、私钥、环境目录、临时锁或运行日志。大型原始轨迹、编译模型和视频保留本地／
  原实验服务器；提交配置、源码、报告、必要的小型证据和产物 SHA256 清单。
  `.gitignore` 不等于删除产物，Git clone 也不等于完整原始数据备份。
- 发布时说明缺失的大文件、绝对路径和运行时依赖；复现实验须按 execution.json 核对解释器、
  MuJoCo 版本、模型及源码 hash。不得用重编译后的不同模型冒充归档模型。
- 当前优先修正 teacher 并验证特化条件，再做纯 ESN。未经用户新授权，不改冻结环境、gate、
  actor 输入、执行器限制，不解封保留条件，不把 dt=1e-4 开发结果当作 dt=5e-5 正式结果。
- 保留失败回合。读取进度、运行服务和 execution.json 后才启动实验，避免重复；本机一个
  MuJoCo 环境、1–2 线程、MemoryMax≤3 GiB，Spark 总仿真并发≤4。
  **本批次例外（2026-10-08）**：用户再次要求加速并充分利用服务器算力后，
  `office_v7_uniform24_20261008` 已在回合边界从 4 路提高到 8 路；每路仍为单线程、
  MemoryMax=3GiB、MemorySwapMax=0，只用高性能核。以该 run 的 `DISPATCH_V2.json`
  为调度补充协议，不恢复旧四路协调器，不修改冻结物理/模型/条件，不擅自外推到其他作业。
- **新批次例外（2026-10-08 21:23 CST）**：用户另授15小时baseline修复/重评并开放本机与
  Spark算力。`baseline_repair_15h_20261008`登记Spark新仿真并发≤10、单线程/每worker3GiB/禁swap，
  本机仍≤1个模拟器；保留四个历史暂停RL进程。以新批次PROTOCOL/后续资源收据为准，
  不把旧四/八路限制误作本批必须等待审批的条件；也不无界增加并发或改环境/gate。
- 用户给出小时预算时，协议必须记录授权起点、派发截止及依据。自动化的 RRULE/UNTIL
  只表示唤醒日程，不构成延长计算预算的授权。若会话、协议与日程时间冲突，先核对来源；
  无法确认剩余预算时停止新派发，保留已启动回合并完成审计，报告冲突后等待新的预算。
