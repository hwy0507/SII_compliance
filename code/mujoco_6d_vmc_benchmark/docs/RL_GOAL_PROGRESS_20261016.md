# 持续Goal：四类RL训练与收敛修复

用户于2026-10-16 12:52 CST明确开启Goal，要求持续推进并自主修复训练问题。Goal active，
尚未完成；旧15小时run正常按原截止收尾，新授权以独立有限阶段继续，不回写旧协议的截止。
沿用sii-research-sync协作流程，训练与分析在airpig，服务器只归档。

## 16:10 CST：末端邻近诊断，导纳真实学习继续

开工核对main `bc56632dbe6a4f92f1fe7cb1f529d6b50af32229`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及远端日志/AGENTS。导纳同PID2360933从
5500/501推进至6576/1577（steps/updates），4完整55秒回合physical_valid4/4、Task/Strict0/4；
第4return−25.347365861。下一回合在途；VMC排队，原协调器继续，无重复模拟器。

新只读工具`tools/diagnose_goal_terminal_neighbours_20261016.py`检查阻抗cp11000与导纳cp5500。
每回合末25个样本，在同回合距离末端至少50步的早期候选中寻找观测/动作邻居。距离为观测
差除以整个replay每维标准差（floor1e-6）的均方，加原始动作差均方，两组等权；这不是网络
真实normalizer或物理等价判据。保留短回合跳过收据，拒绝未闭合/非有限replay；不跨回合。

阻抗200对、导纳100对：观测RMS中位数.081423/.128995，动作RMS中位数.092459/.104988，
时间差中位数2.90/3.52秒。末端n25奖励均值−22.544659/−22.502375，对应较早窗口
−.051879/−.057405；bootstrap mask分别0/1。尽管部分输入接近，原始观测差仍非零，
**奖励分量不是完整Bellman目标**，不能据此证明时间混淆、真实Q高估、输入不足或学习不可能。
本轮未改actor输入/terminal处理/奖励；结果仅补充末端残差诊断，后续需实际训练对照验证。

3项边界/动作邻居/短回合测试、编译与diff检查通过；真实诊断在本机CPU6/1GiB/swap0，
exit0、峰值100,077,568字节、OOM/max0，无JAX/模型加载/梯度/仿真，checkpoint hash前后相同。
归档快照6383步/1384更新、temperature .0087939678，内存current3,118,579,712、
peak3,165,929,472/3GiB，OOM/max0/swap0。随后anon约1.76GB/file约1.29GB，接近上限
包含文件缓存，未据此重启；全GPU38°C/498MiB，训练仍CPU。新冻结源与登记hash通过。

第4导纳完整原始轨迹/cp5500、只读工具/测试/诊断收据、execution及optimizer快照已归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-terminal-neighbours-20261016T0810/evidence.tar.gz`，
267,986,596字节，SHA256 `19116474cc1bb4db182f5fcd829131fb68f1484d793c299194d1aa9cd5024d13`。
之后数据仍本机待安全边界归档，失败/在途行均保留。Goal active，无收敛或最终acceptance；
下一阶段仍为四族stage01结束后的真实GPU全循环预检，再推进奖励对照/后续训练。

## 16:00 CST：导纳进入优化阶段，释放已核验的重复传输缓存

开工核对main `25c904e1567e3e76f596c524c0f7adcd1ada40a9`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与远端日志。上一轮为实质进展。
同一导纳PID2360933从4000推进至5250步/251更新（5000步第1次更新），原协调器2329290继续。
3个完整55秒热身回合return−25.378512382/−25.374599982/−25.322365699，Task/Strict0/3，
physical_valid3/3；第4回合在途，VMC排队。不能把热身均值稳定当作收敛。

前三回合末10秒25Hz轨迹：第1在cursor17/28，误差14.230–16.205mm；第3在cursor18/28，
误差15.337–17.132mm。第2窗口跨cursor18/19/20/21，计数49/86/86/29，误差18.864–23.463mm；
不能概括成三回合完全静止或照搬阻抗的cursor20结论。每个采样点位置/重入条件均未满足，
但25Hz无法证明采样之间的物理子步条件，更不能据此宣称planner错误或进行最终gate审计。
cp2750/4125与冻结source/parameter清单通过；没有新仿真、奖励调整或重复进程。

本地磁盘检查约78GiB可用、训练保留线50GiB，服务器共享盘约3.3TiB可用。明确枚举9个本任务
临时传输包，逐一重新检查本地/服务器最终归档的大小与SHA256，确认本地为非symlink/单硬链接
的普通文件；执行前再核对全部inode/device/mtime/size/hash，然后仅unlink精确/tmp文件。
已清理stage01-0507、credit-0518、episodes38-40-0545、direct-close-0623、impedance-0649、
impedance-learning-0704、gpu-backend-implementation-0724、impedance-close-0738、
impedance-weight-pilot-0750九包，均带完整rl-goal前缀和20261016日期，详见收据逐文件路径。
释放5,077,083,233字节（4.73GiB）；free_before82,924,175,360、free_after88,000,159,744字节，
期间训练仍在写入。保留了本地所有原始训练目录/checkpoint/source和服务器全部归档，
没有递归删除/历史实验迁移。旧日志称这些/tmp包保留是当时状态，现以此条及删除日志为准。
完整恢复命令在`TRANSFER_CACHE_CHECK_20261016T0800.json`；删除journal逐文件fsync，
结果在`TRANSFER_CACHE_RESULT_20261016T0800.json`。第一次read-only检查因系统Python缺少
hashlib.file_digest而exit1，未生成检查收据、未删除；冻结项目Python在独立服务复核/执行均exit0。
本轮仅回收临时冗余，长期1M训练仍需按阶段归档/监视增长，未降低50GiB保护线。

导纳第2/3原始回合与cp2750/4125、前三carry结果、5000步/1更新快照、存储清单与cache收据
已核验服务器最终归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-storage-20261016T0800/evidence.tar.gz`，
396,011,348字节，SHA256 `6628bdf7dfa89cf61bfe3b62e8eed136dceaed3b1f333c95ee82f79cc95e6890`。
第1回合在上一轮0750包；本轮第4及后续新数据仅本机。归档快照memory.current2,778,599,424、
peak2,808,971,264/3GiB，OOM/max0/swap0。服务器只文件传输/大小/hash检查，无服务器计算。
Goal active，未收敛/未最终验收；原GPU/Direct奖励/阻抗奖励的准备状态不变，未派发。

## 15:50 CST：阻抗权重对照实现、登记和真实预检完成，现有导纳继续

开工核对main `b0e61c671691fc0e33d5193d3b9a00611fa46e2e`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS/远端日志。上一轮为实质进展。
导纳PID2360933/原协调器2329290真实推进至2750步，仍处5000步热身、0更新；2完整55秒回合
return−25.378512382/−25.374599982，Task/Strict0/2、physical_valid2/2，第3在途。VMC排队。

新修复假设：已有阻抗8失败回合跟踪奖励约−.09，而峰矩约−1.6至−2.8，跟踪信号偏弱。
把训练跟踪权重从4提升到40，使用同一物理子步积分的bounded_error_cost（尺度仍.12m）：
保留原metric基础权重4，新增明确标记的tracking_guidance权重36；所有其他奖励项保持。
提前失败补齐新增项的折扣最坏尾部；不改变最终物理/gate/actor48/filter，也不靠改门槛解卡。
这是单变量训练假设，不能保证能克服接触/可达性问题；需看真实paired任务与安全结果。
`goal_tracking_reward_20261016.py`与trainer拒绝未登记配置/不同奖励checkpoint混用；
`goal_tracking_pilot_20261016.py`复用fresh比较流程，支持5维阻抗，与旧7维Direct保持隔离。

新独立根`outputs/rl_goal_impedance_tracking_pilot_20261016`已prepared，登记SHA256
`52884e47b1db9e4ea4a050940e70d1edcf81aa46482d44412ba2976b69472a16`；
两臂impedance_control/impedance_tracking，同seed2026101421、各最多11000新交互/1M优化日程、
5000热身、n25/UTD1、CPU1单路/3GiB/swap0，派发保护截止2026-10-17T07:46:01.068951Z。
模型/optimizer/normalizer/replay均从零；cp11000只用于只读取历史replay预检，不用于训练初始化。
真预检读取同一个1375步完整训练回合，两臂各做一次丢弃更新：初始网络hash完全相等、
终端25步累计回报及mask正确、所有metrics有限、旧checkpoint hash不变，exit0。
峰值1,365,557,248字节、OOM/max0；无仿真/模型保存。43项Goal＋5项恢复测试、编译/diff检查通过。

`IMPEDANCE_TRACKING_WEIGHT_ARITHMETIC_20261016T0748.json`在相同8条旧轨迹上复算额外
折扣罚分.830188–.866527；不是新策略回报/效果，不能用不同奖励定义的raw return比较优劣。
真实require_predecessor_complete检查拒绝当前仍运行stage01；没有LAUNCH/后台等待服务/新模拟器。
既有Direct pilot登记hash仍`42f101068a4185f7d920900de8b18f63720720436254fb3f2bbe4ab4cb7f3c91`。
GPU完整循环验证仍先于后续训练对照；此新pilot是CPU登记，未冒称GPU实测或四族训练完成。

已核验incoming大小/hash与最终独立目录hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-weight-pilot-20261016T0750/evidence.tar.gz`，
198,505,376字节，SHA256 `de29e2588ac37a95b0c04b949b0acaab05e50dd1a9a9cf0b0ce153bbdc8b2a1f`。
含完整pilot冻结source/parameter/REGISTRATION/CREDIT_PREFLIGHT、算术结果、测试、
`PREPARATION_EVIDENCE_20261016T0750.json`及导纳首回合原始轨迹/cp1375/PROTOCOL。
快照2750步、内存current1,745,911,808/peak1,989,345,280、OOM/max0/swap0；第2及后续回合
仍仅本机，原模型/runtime仍依赖既有冻结路径。Goal active，尚无收敛或最终验收。

## 15:40 CST：阻抗11k闭合，导纳真实启动；8个失败回合完整保全

开工核对main `d26bf9b139cad17ddc786cdb91be2505b6214c9a`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与AGENTS/远端日志。上一轮为实质进展。
阻抗11000步/6001更新于07:35:46Z正常结束，step_budget、8个完整55秒回合、physical_valid8/8、
Task/Strict0/8。checkpoint0011000各文件hash通过；1M日程未完成，不能把有限段结束当收敛。
协调器PID2329290自动启动导纳PID2360933/user unit sii-rl-goal-7310d204f8a4，真实250→750步，
仍5000步热身、0更新、首回合在途；3GiB/swap0/单CPU1保持，OOM/max0。VMC尚未启动。

阻抗回报均值−25.587297829、总体标准差.473319155；第8回合−25.939879296。
8个末10秒窗口各250采样均停carry cursor20/28，位置与横向重入均不满足、姿态/速度均满足；
末回合位置误差12.7987–13.1865mm，forward−5.955至−4.829mm。参数动作在改变，energy_scale=1。
这不是独立物理子步审计，也不能把刚度、reward或障碍接触单独定为原因；最终gate未修改。
全8回合训练奖励复算一致：折扣potential合计均−.560238529（预期抵消），tracking罚
−.092243至−.096281、峰矩罚−1.589846至−2.833113，task罚均−10.059933。
小幅回报波动主要是峰矩差异，没有任务进展/收敛证据。

11000 cp只读诊断1159样本（固定规则包含全部末25步）：200末端附近样本absTD.320213、
actorQ−behaviorQ2.052449、策略维度饱和率37.7%；959远端样本absTD.0217425，最新回合
145样本absTD.401190，温度.00580246095。5500 cp末端absTD.928903不能直接作为同样本
改善率：样本数/轨迹/条件/归一化均变化。末端动作外推与残差值得继续查，但不是独立真实Q证明。
诊断无梯度/仿真/保存，checkpoint/RNG/normalizer不变，内存峰值895,913,984字节，exit0。
初次服务0738漏设WorkingDirectory，Python在/home/airpig找相对tools路径而exit2，未执行诊断；
在独立0738b服务明确工作目录后完成。失败与修复均写入归档收据，没有重启现有trainer。

已核验服务器最终归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-close-20261016T0738/evidence.tar.gz`，
272,146,819字节，SHA256 `dbc33e71d76da775d82c56017adc2435ad076f87ab3f1553f13d72895885c662`。
包内含第8回合原始数据、cp11000、最终training/optimizer/execution/PROTOCOL、
`IMPEDANCE_CREDIT_0011000.json`、`IMPEDANCE_REWARD_20261016T0738.json`和
`IMPEDANCE_CLOSE_20261016T0738.json`；后者保留8回合carry结果、收敛筛查、协调器快照、服务证据
与初次诊断失败。前7回合/checkpoint分包索引见下文；服务器只归档。导纳新轨迹仅本机。
四族均未满足前瞻收敛标准，GPU完整循环验证仍等stage01正常完成；Goal active、无最终acceptance。

## 15:26 CST：GPU训练路径已实现，等待现有阶段安全闭合后验证完整循环

开工核对main `3c9b58b60787344d46b31792e9f32942e7b3e51b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与AGENTS/日志。上一轮GPU探针是实质进展。
同一CPU阻抗trainer2344947与协调器2329290活跃；9750步/4751更新、7完整55秒回合，
Task/Strict0/7、physical_valid7/7，第8在途。新两回合return−25.1302849/−26.3649992，
cp8250/9625 hash与冻结source/parameter manifest通过；其他方法状态未冒称成功。

新增后端模块与显式登记路径：普通历史CPU行为保持；GPU必须登记资源、实际JAX平台为gpu、
实际亲和性等于登记CPU（训练1，丢弃预检6）。CPU checkpoint跨到CUDA必须有明确迁移字段，
不偷偷降级回CPU。weights/optimizer/RNG/normalizer/raw replay保留，但浮点轨迹不保证逐位相同。
训练PROTOCOL/execution记录learning_backend、compute_runtime与内核memory快照；模拟器
子进程仍显式JAX_PLATFORMS=cpu，物理/MJB/dt5e-5、actor48、filter、gate、奖励/UTD1不变。
GPU0要求入场free≥4096MiB/温度<80°C，回合边界重新检查；JAX_PREALLOCATE=false、
MEM_FRACTION=.125仅为JAX池限制，不是整个GPU进程的硬显存封顶。主存3GiB/swap0硬限保留。

`rl_goal_stage_20261016.py prepare-gpu-preflight`须等待前序四方法均正常闭合并逐checkpoint
核验，才创建全新目录/源码快照/登记，各最多1375新增交互、合计5500、24小时派发保护。
逐族`probe_goal_credit_20261016.py --root <GPU阶段> --job <name>`必须实际CUDA、CPU6、
正确env下执行；正常检查25步终止窗口、原始replay、一次有限丢弃更新与cp hash后封存四族
预检，仍沿用全局仿真锁/单路/内存磁盘准入，不能从prepared直接冒充已派发。
这四回合是实际训练并保存独立checkpoint；只有四族各完整1375步/55秒、实际GPU/亲和性
匹配、OOM/kill0、swap0、峰值≤3GiB，才可用prepare-next准备常规11k续训。短回合/物理
提前失败保留，只能另登记有限GPU验证阶段继续，不以短回合推断完整循环内存通过。
普通GPU续训绑定完整循环验证的registration/execution hashes；后端切换不是奖励或最终gate变化。

当前真正调用prepare-gpu-preflight被活动stage01正确拒绝，
`outputs/rl_goal_gpu_preflight_20261016`不存在；没有GPU训练或额外等待服务。
既有`rl_goal_tracking_pilot_20261016`保持原CPU登记与冻结来源，未改写它的内容；新代码也为
未来显式GPU的fresh pair增加了真实GPU预检检查，但现有pair没有转换。下一步先完成在途
stage01；之后做独立GPU完整循环验证，再依据结果登记后续训练/奖励比较。

40项Goal测试＋5项恢复测试通过，覆盖未登记GPU/环境漂移/假绑核/未授权恢复拒绝，
GPU命令资源边界、父源与物理保持、全四族完整回合/无OOM门槛、短回合拒绝常规续训及有限
重试；trainer/dispatcher/后端编译通过。真实`GPU_BACKEND_GUARD_REGISTRATION_20261016T0721.json`
另登记102次CUDA丢弃更新，绑定backend guard源码hash
`60ffe466ae747b1cd7198faca20454e098958016ff5ce326d2eb4cd91a1f981d`，
同6875 cp、CPU6/2GiB/swap0/180秒，无仿真/模型写回。guard实际平台/设备/亲和性检查通过，
102更新有限、cp hash不变、exit0，主存峰值1,293,684,736，OOM/max0，GPU快照48°C/1425MiB。
计时286.83更新/秒为另一时点固定batch测量，不能把差异因果归到allocator fraction，也不是
完整训练循环或成功策略证明。guard预检已退出；CPU原训练持续推进。

第6/7原始回合、cp8250/9625、所有本轮源码/测试与GPU guard登记/结果和
`GPU_BACKEND_IMPLEMENTATION_20261016T0724.json`快照打包为
`/tmp/rl-goal-gpu-backend-implementation-20261016T0724.tar.gz`，534,028,451字节，
SHA256 `84534fda395ebba80b0b97ec9dbfaea450f2799f2c81313974e64e03d6b60f0e`。
已核验incoming大小/hash并发布至不存在的独立最终目录，再次核对最终SHA256一致：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-backend-implementation-20261016T0724/evidence.tar.gz`。
服务器仅传输/归档/hash。快照9625步/4626更新，memory.current
3,047,575,552、peak3,221,225,472、memory.max事件477、OOM0/swap0。内存回收压力增加，
没有放宽限制或重启。第8回合仍仅本机，Goal active，尚无收敛/最终验收。
收尾复核systemctl --user与实际PID一致，同一trainer推进至10500步/5501更新，temperature
.00606476；memory.current3,176,308,736、max事件565、OOM/kill0，第8回合仍在途。

## 15:10 CST：GPU丢弃更新探针通过，下一阶段可准备完整循环验证

开工核对main `5fbc2cbce35d2e923405fee9952b9478592f7850`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/日志。上一轮为实质进展；
本轮继续同一阻抗PID2344947，execution8000步/3001更新、optimizer8095步/3096更新。
第5回合完整55秒、return−25.6329256，Task/Strict0/5、physical_valid5/5；6875 checkpoint
全部hash通过。第五回合是第一个全程过热身的回合，最后10秒仍cursor20/28，误差
12.528–12.727mm，位置/重入均0/250通过，姿态/速度250/250通过；未解决carry阻塞。
末10秒实际参数中位数约[281.68,76.47,1.482,.662,1.155]，energy_scale均1，参数确实在变化。
Direct有限阶段0/8不变，导纳/VMC仍排队，fresh tracking pilot仍prepared；无最终验收。

前四回合奖励诊断保存`IMPEDANCE_REWARD_20261016T0700.json`（第5当时尚在途，明确排除）：
折扣payload势函数均−.56023853，抵消残差<4e-15是预期公式；折扣tracking罚约−.0951至
−.0957，峰矩罚−1.5898至−2.5828。相近失败回合的return变化主要来自峰矩，不能当收敛。
只读5500 checkpoint诊断`IMPEDANCE_CREDIT_0005500.json`共1021训练样本，含100个
末25步样本，后者absTD.92890、actorQ−behaviorQ2.10443；远端921样本absTD.02553。
终止4条absTD1.26775，温度.00956434；clip概率质量均值.00025095。早期末端拟合仍不足，
但这不是独立真实Q或因果归因。无梯度/仿真/模型保存，RNG、normalizer、cp hashes不变，
诊断exit0、峰值1,104,183,296字节；只包含501次已有训练更新的checkpoint。

为解决当前CPU更新吞吐，新增`tools/probe_goal_update_backend_20261016.py`：
读取同一6875 cp，用固定seed20261016抽同256索引，分别在CPU/CUDA加载后做2次预热和
100次计时的丢弃更新；102次更新全部有限、原checkpoint不变，无模拟器、无模型保存。
现有环境已有jax/jaxlib/jax-cuda13-plugin/pjrt均0.7.2，无依赖安装或环境修改。
初版只设AllowedCPUs，未进程内验证，CPU时间62秒超过wall10.8秒，不作为单核对照；
其原始源码和结果保留在包内`rl-update-probe-initial-20261016T0705.tar.gz`。
登记修订`UPDATE_BACKEND_PROBE_20261016T0706.json`明确额外预算204，总计最多306次，
CPUAffinity=6且进程内assert亲和性[6]，两端串行、2GiB/swap0/最长180秒，初次失败保留。

修正后的CPU实测100更新25.7364秒（3.88555/s），CUDA100更新.52243秒（191.41469/s），
优化器吞吐49.263倍；CPU首次预热4.165秒、GPU45.799秒（包含编译）。主存峰值分别
1,395,916,800与1,411,497,984字节，OOM/max均0，swap0。GPU设备为RTX5080Laptop，
快照46°C/1424MiB为整机显存占用。相同batch索引/checkpoint hashes通过核对；首更新
critic loss差1.9e-6，actor entropy差约1.05e-4，不能声称逐位一致或同轨迹复现。
这是固定batch吞吐，不含物理仿真、IPC、在线归一化、采样/完整训练循环，不能声称整体49倍。
下一步应实现显式登记的GPU训练后端、验证完整训练回合和内存后在安全边界使用；
当前stage01和既有fresh tracking pilot均未修改、未重启，不能改写它们的冻结配置冒充原实验。

已核验归档（服务器只传输/大小/hash）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-learning-20261016T0704/evidence.tar.gz`，
267,168,254字节，SHA256 `762955989867d078a223f6619a07eaecfdacefc6c50a76b95a658fcd414e549e`；
含第5原始回合/cp6875、奖励/credit/carry诊断与源码、当前快照。快照训练memory.current
2,909,458,432，peak3,135,127,552/3GiB，OOM/max0/swap0。
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-backend-probe-20261016T0709/evidence.tar.gz`，
11,214字节，SHA256 `05d90a7d7c441719cdb68a3ee11d888661175f11a025fb0d16180e9173fa39e2`；
含完整初/修订探针源码、登记和三次结果。探针已全部正常退出，无后台探针或传输待收尾。
第6及后续回合仍仅本机，待安全边界归档；Goal active，未收敛/未完成。

## 14:53 CST：阻抗进入梯度更新，carry停滞已有可复算定位

开工核对main `9348836f2d03fde25b3a8f5977340dbddfa1c663`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`和AGENTS。Goal保持active，当前阶段
未结束，Direct仍0/8；admittance/VMC排队，fresh tracking pilot仍prepared未派发。
阻抗同一PID2344947于5000步开始第1次更新，5500步/501更新checkpoint hash通过，
最新观察5769步/770更新；第5回合在途。4个完整55秒回合return依次−25.493412、
−26.067121、−25.072284、−24.997477，Task/Strict0/4、physical_valid4/4。
不同条件且前三仅热身，不能把相近return当收敛，或按回合顺序认定训练改进。

新增`tools/diagnose_goal_carry_stall_20261016.py`与3项测试：检查冻结source hash，
对齐前一行post-step手位置和当前pre-step canonical error。重建目标严格匹配route，
防止相差一个控制周期的错位推断；覆盖半径与横向平面不同逻辑、最终点禁止平面捷径、
错位输入拒绝。四回合最后10秒各250样本全部在carry cursor20（28点中的第21点），
到达半径与forward平面条件均未满足；姿态<.12rad与速度<.025m/s均满足。
前三热身误差12.605–13.414mm，forward仍在点后4.436–6.425mm；第4回合含501次更新，
最后10秒仍12.737–13.002mm、forward−5.417至−4.790mm。三个planner/observation源
hash与执行记录吻合，路径重建误差0。末10秒energy_scale均1，参数确有变化。
注意canonical[26:32]是command−twist，不是原始twist；本工具直接使用明确的原生速度字段。

原生rollout的unknown-edge接触从10.12–11.02秒持续至55秒，累计43.98–44.88秒，
都发生在carry。该证据提示障碍接触/路径阻塞，尚未证明刚度单因果或可通过增大刚度解决；
不得调整最终gate，也不能把25Hz采样推断当全部物理子步证明。零action7是native阻抗
后端输出语义，实际5维parameter_actions存在；原生训练审计未替代最终统一验收。

`CARRY_DIAGNOSTIC_20261016T0650.json`保存前三热身回合（真实创建06:47Z，文件名仅标签），
`CARRY_POST_WARMUP_20261016T0649.json`保存第4回合；
`IMPEDANCE_CHECKPOINT_20261016T0649.json`保存execution快照、四checkpoint校验、
optimizer首尾与资源。归档快照optimizer最后5614步/615更新，所有已记录更新满足UTD1且
指标有限；温度0.00946349。内存2,736,730,112、峰值2,897,244,160/3GiB，OOM0/max0/swap0。
打包仅本机CPU6/1GiB/swap0、exit0，无模拟器；训练保持CPU1单路。GPU44°C/526MiB为
主机观测，不是训练用GPU。另查旧v3–v6协调器各单task，未改动无关服务。

四完整失败原始回合、cp1375/2750/4125/5500、捕获日志、诊断及源码/测试已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-20261016T0649/evidence.tar.gz`，
846,865,888字节，
SHA256 `6c87112421ddc26b3b3bb66ce090cf66ac0da0a0fd8612c0df1bae4a2fd30e10`。
上传后核验size/hash，再从独立incoming目录发布至不存在的最终目录，复核最终hash一致。
本地包`/tmp/rl-goal-impedance-20261016T0649.tar.gz`保留；第5及后续回合不在本包。
14:54观察6250步/1251更新；旧v3–v6均在等待failed Direct子服务（子服务MainPID0，
其他子服务inactive），不是四个并发训练；未更改这些旧收据/服务，当前只有一个阻抗模拟器。
后续继续观察学习回合、保存失败，再按已登记顺序接续导纳/VMC及fresh奖励对照；
本次定位不是修复完成或Goal完成，不做最终acceptance。

## 14:35 CST：Direct完整阶段证据保全，阻抗继续热身

核对main `9358461c2daae6e8cd629eeca3592342d133cdcb`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS及日志。上一轮登记/真实预检为进展；
本轮真实服务仍active，补齐归档并读取闭合训练诊断，未重复训练或改活动快照。
Direct8回合都停approach，native AUDIT的目标XY误差190.62–220.24mm，Task/Strict0/8。
补齐最后四回合episode41–44及cp57406/58781/60156/61531、整个阶段training/optimizer logs、
PROTOCOL/最终execution；所有checkpoint hash和source/parameter manifest通过。
`DIRECT_CLOSE_20261016T0623.json`包含终态Direct、已有8个训练AUDIT、当时阻抗750步
快照、cgroup与收敛检查；它不是独立最终审计。

最终61,531 checkpoint的只读诊断完成：2127条样本=1024均匀抽样与全部45回合末25步的
去重并集，末端被故意增采样，不是总体无偏平均。终止45条absTD0.09649；末25步1125条
absTD0.10500、当前动作Q比历史动作高1.79795；远离终止1002条Q均值0.74485、target0.75985。
最新回合50条absTD1.92057，表明新数据仍未充分拟合。温度0.00093858，全部样本裁剪概率
质量约0.0009%；不能据此宣称真实Q高估、收敛或n25优于n1（前后样本组成不同）。
诊断服务`sii-rl-credit-final-20261016-0628.service` exit0，峰值1,077,571,584字节/OOM0；
无梯度更新/模型保存，checkpoint hash、RNG与归一化统计均未变；没有final/heldout访问。

14:34阻抗同一trainer PID2344947仍active，3000步/0梯度更新，尚在5000步探索热身。
已完成2个完整55秒回合，return−25.4934119/−26.0671207，physical_valid2/2、Task/Strict0/2，
第三回合在途。首回合抬升160.36mm但停carry、目标XY误差90.17mm、RMSE23.29mm；
属于原生训练诊断，不是最终独立指标，不能把早期阶段进展当成功。2750 checkpoint hash通过。
内存1,650,655,232字节/3GiB，此前OOM0/swap0。admittance/VMC尚未开始；fresh tracking
pilot保持prepared，等待原四族阶段全部结束，未新增等待服务或派发。

服务器独立目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-close-20261016T0623/`。
`evidence.tar.gz` 1,108,637,123字节，SHA256 `eeac5a2a0fe96e3c418a28873958525af94a4b11d2648a65412f2aa7b9c52062`；
`final_credit.tar.gz` 8,496字节，SHA256 `8ecd59850acb138616b03e0c8c037d00261a0b862bc26778f50781f49f5342da`。
两包最终远端hash均核验；首次传输自动审批超时，按提示重试完成，没有把超时当拒绝授权。
结合此前credit包的episode37、episodes38–40包，stage01 Direct全部8回合及checkpoint现已共享；
这不是更早所有历史训练的全量归档。阻抗新回合仍仅本机、待同步。Goal继续，未收敛/未验收。

## 14:21 CST：Direct阶段0/8，阻抗自动接续；fresh奖励对照预检完成

开工核对main `80c0b6133b48ae5c24f682b0c5f0ba30e02a83d0`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与日志。Direct正常结束该有限阶段：
61,531步/95,189更新，新增11k/11k；8个完整55秒回合Task/Strict0/8，physical_valid3/8。
末两个return−21.8339448、−39.4224188。最终61,531 checkpoint实际hash通过；原worker
已退出，原协调器PID2329290继续自动启动impedance_payload、PID2344947，真实250步/0更新，
处于登记5000步探索热身，不能因0更新误认卡住。admittance/VMC仍排队。Direct没有收敛，
原1M优化日程未完成；第5至8回合大型原始产物目前仅本机，待下一次同步。

奖励候选落实为独立`outputs/rl_goal_tracking_pilot_20261016/`两组有限对照：
direct_control与direct_tracking均从零初始化，不加载旧actor/critic/optimizer/replay/normalizer；
相同seed2026101421、n25/UTD1/1M日程、5000步热身、条件顺序、训练预算11k，合计22k。
唯一处理差异是tracking CONFIG。历史已续训Direct不能充当这个fresh对照组；两组原始reward
目标不同，报告效果应看匹配条件的Task/Strict、阶段与跟踪指标，不能用不同奖励数值作胜负。
本pilot最多各8个完整回合、单seed，只能提供可行性证据，绝不等于96回合收敛或四族完成。

登记SHA256 `42f101068a4185f7d920900de8b18f63720720436254fb3f2bbe4ab4cb7f3c91`，
截止2026-10-17T06:16:14.522695Z；硬限单模拟器/CPU1/1线程/3GiB/swap0、内存/磁盘准入不变。
前序`stage01`四族全部正常闭合且checkpoint吻合后，才能用本pilot冻结source中的
`rl_goal_stage_20261016.py launch --root <pilot绝对目录>`派发。launch和run双重检查前序，
仍持全局dispatch lock；当前只完成准备，没有LAUNCH/训练进程，没有创建额外等待服务。
通用四族收敛统计不能用于这两个pilot组；不能将这两组混入原四族lineage。

30项相关测试通过，覆盖fresh/同seed/仅奖励差异、前序在途/失败拒绝、缺失预检/错误处理拒绝。
真实running前序提前启动检查被拒绝，未创建LAUNCH。预检服务
`sii-rl-tracking-preflight-20261016-0617.service`正常exit0，峰值1,357,033,472字节、OOM0，
CPU6/2GiB/swap0；同一历史1375条训练transition分别灌入临时fresh模型，各一次丢弃更新。
actor/critic/target critic/temperature初始hash完全相同，n25末端窗口独立复算通过、指标有限、
源checkpoint hash未变；没有模拟器、模型保存或训练收益证据。冻结manifest与总预检均复核通过。

源码/测试、完整冻结source/parameter、REGISTRATION和CREDIT_PREFLIGHT已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-pilot-20261016T0618/evidence.tar.gz`，
2,318,827字节，SHA256 `948a868c5ff1a10fdcb237eef83def388055b665c32757b92446175d09e488ca`。
预检所读历史51,906 checkpoint在此前credit归档中；本包不重复其大型replay。
下一步跟踪阻抗的真实steps/updates与完整回合，然后依次收尾其余方法并启动已准备的对照。
Goal active；训练收敛、统一acceptance和独立最终审计仍未完成。

## 14:10 CST：密集tracking组件完成，尚未启动新奖励训练

核对远端main `e47c4164013760b1d0c30d90eb7f6d85780b287a`与baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS及日志。同一协调器/Direct worker活跃，
14:09 optimizer60,090步/93,748更新；六完整回合Task/Strict0/6、第七在途，其他三类排队。
58,781 checkpoint、冻结source/parameter manifest通过；内存3,168,563,200字节、OOM0，
硬限回收max1371，3GiB/swap0保护继续，不重启活动作业。

新增`goal_tracking_reward_20261016.py`，采用已有metric中的权重4与.12m误差尺度，只增加
`-4*sum(dt/55 * error²/(.12²+error²))`，不增加torque/slew项，也不改变Task终止奖励。
提前失败加上剩余完整/部分RL interval的gamma折扣最坏成本；gamma.9995、RL dt.04s和
55s时间窗保持。全回合附加成本在[-4,0]，不是可通过拖延刷取的正奖励；并不声称最优策略
不变，密集成本有可能影响取舍，需真实训练和最终任务验证。

trainer仅从显式Goal job `tracking_guidance`读取固定CONFIG，且限定Direct/office_task/
task_safety组合，避免叠加已有metric成本。未登记保持旧行为。恢复前比较父子tracking配置，
禁止旧reward replay/normalizer直接续到新目标；未来试验优先全新同seed对照，而非无依据
保留已学critic和旧奖励。收敛统计fingerprint包含tracking配置，不能混合不同目标回合。
现有prepare-next仍是原配置精确接续入口，不能用它暗中部署这一处理；新处理尚未登记/派发。

27项Goal相关测试通过（新增密集成本方向、剩余分数步、gamma1/.9995/.9、提前失败、
参数边界/非有限值、旧新恢复拒绝、收敛统计拒绝tracking漂移）；trainer编译通过。
用五回合冻结完整日志执行真实奖励复算，结果`TRACKING_COUNTERFACTUAL_20261016T0610.json`：
episode37与40原折扣回报同为−11.4082118，候选变为−13.9029927/−11.6288941；
所有原Task/Strict失败标签保持。仅算术反事实，没有新轨迹、模型更新或checkpoint/replay改写，
不能当成策略收益改善。下一步在独立有限新处理登记后做实际训练比较，当前stage继续。

源码/测试/复算结果与完整输入快照已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-component-20261016T0610/evidence.tar.gz`，
1,239,902字节，SHA256 `bbe188dc15aa95c10bdf4c1930733cee1e9513349754cbf552bb9089638f6c1e`。
Goal仍active；四方法收敛、统一acceptance及最终独立审计都未完成。

## 14:01 CST：奖励分解给出下一阶段调整依据

核对main `ea271110dc9ef16da2047e2df8fa374eefa8cc28`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与远端日志。上一轮归档为进展，
本轮补齐`diagnose_goal_reward_signal_20261016.py`及3项针对性测试；只读训练数据。
快照五个完整回合的奖励组件、gamma、终止label、逐步连续性和势函数抵消全部通过。
每1375步只有1个Task reward非零（−20），n25中只有25/1375=1.818%窗口直接包含终止奖励；
这不是说其余步没有shaping信号，也不是说多次bootstrap无法传播奖励。
折扣shaping和都是−0.6249994097574，残差<1e-15；此抵消是有意设计，无需删除终止抵消。
安全罚分依次0/−12.5152096/−17.7244568/0/−13.9713077，跟踪error项当前为0。
两个零安全罚分回合的有界跟踪cost0.8902505与0.0720529，折扣总回报却相同；
五回合reference potential最大值都停留在初始0.12499988，原生AUDIT都在approach。
这表明当前训练目标在这些安全失败轨迹间无法持续奖励更好的跟踪；尚未证明是唯一根因。

下一阶段优先检验已有有界密集tracking项（训练奖励），最终Task/Strict不变；但更换奖励
不能直接续用旧raw reward replay/normalizer假装同目标精确恢复。须单独登记、重建或隔离
旧奖励数据，并保留原处理组，不能把当前immutable stage就地改掉。尚未部署新reward。

14:00同一worker仍active，58,781步/92,439更新、阶段新增8250/8250；6个完整回合Task/Strict
0/6、physical_valid2/6，第6return−22.475132，第7在途，其他三方法未开始。58,781 checkpoint
实际hash通过。memory.max事件1162，OOM0/swap0，继续监测硬限回收与实际吞吐。
新诊断保存全部捕获execution/protocol/closed logs及已有AUDIT/hash，明确未完成回合。
工具/测试/快照已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-reward-signal-20261016T0600/evidence.tar.gz`，
1,225,327字节，SHA256 `30a9b7c1c8e615098a3d7d2596684e03e5a865e236fa7c74400f34e43e4db9c6`。
第五回合之后原始大型产物仍仅本机、待同步；Goal active，未收敛、未最终验收。

## 13:55 CST：五个完整失败回合，补齐大型证据归档

实时核对main `436552af7c5417c9033ffd87dfb26ce8e5707559`与baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、两分支日志及AGENTS；Goal仍active。
同一协调器PID2329290、trainer2329294真实运行；57,750步/91,408更新，阶段新增7219/7219。
五个完整55秒回合依次return−21.667945、−34.277519、−39.487075、−21.871979、−35.653907；
Task/Strict联合0/5、physical_valid2/5，第6回合repair_train_017在途。其他三方法仍排队。
57,406 checkpoint hash核验通过；第5回合原生训练AUDIT同样停在approach，max_lift0、
目标XY误差192.09mm、RMSE803.36mm。不同条件的回报不能直接证明n25有效或无效；
目前无成功样本，不能称收敛。未执行最终统一acceptance或独立最终审计。

worker MemoryCurrent3,151,167,488字节/MemoryMax3GiB，memory.events max434，OOM/kill0、
swap0。此前增长有较多file缓存；现已出现硬限回收压力，继续观察实际吞吐和OOM，不移除保护。
本轮完成episode38–40全部原始轨迹和checkpoint53281/54656/56031的归档，附05:46Z
execution/收敛统计/优化器奖励窗口/训练AUDIT/资源快照及生成脚本；source/parameter manifest
和这三个checkpoint均已核验。服务器最终文件大小与SHA256一致：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-episodes38-40-20261016T0545/evidence.tar.gz`，
835,219,332字节，SHA256 `77b7fca926a438e8c83a96ae2e01a0c1f075420aae69e1340916112dc61860e4`。
episode37此前已独立归档；episode41及之后仍仅本机、待同步。服务器无计算，无重复训练。
本轮为运行核查与失败证据保全，未新增训练算法修复；下一步看有限阶段完整结果与自动接续，
再依据已有动作外推/approach失败证据登记后续调整，持续Goal不因本轮结束而完成。

## 13:39 CST：收敛统计检查落地，训练仍未满足判据

本轮核对main `dee4c4ba65b5866d1e31fe0d15122c34da47d384`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read日志与AGENTS。上一轮完成了精确
接续能力和真实恢复验证，属于进展；本轮保持同一协调器/Direct worker运行，没有重复派发。
13:39 optimizer已记录55,804步/89,462更新；最近已闭合checkpoint为54,656步，hash通过。
本阶段3个完整55秒回合return−21.667945、−34.277519、−39.487075，均值−31.810846、
总体标准差7.480807，Task/Strict联合0/3、physical_valid1/3，第四回合在途。
temperature最新约0.00058627；这些早期样本不是收敛或调参有效的证明。

新增`screen_goal_rl_convergence_20261016.py`落实先前登记的96回合、两个32回合窗口、
各窗全32训练条件覆盖、各窗Task AND Strict≥90%、均值漂移≤5%、末窗CV≤25%判据。
均值相对漂移明确定义为abs(new_mean-old_mean)/max(abs(old_mean),1e-12)，CV为总体标准差/
max(abs(mean),1e-12)；负回报同样处理。此数值解释在任何合格窗口出现之前固定。

沿新阶段的hash绑定lineage，只累加每段自己的闭合rows，不相加累计episodes/steps；
Direct旧n1继承的37回合不能混入本n25收敛统计。早期失败/非完整回合仍在分母，在途回合
单独保留；重复、缺失、乱序、跨奖励/agent配置拼接和缺失父方法证据会报invalid_evidence。
每份统计保留实际读取的execution与protocol快照/hash，以免活动文件后续更新导致无法复核。
统计的training_candidate即使为true，也始终不代表最终acceptance或Goal完成。

8项有针对性的测试通过，覆盖失败reward平台、Task/Strict不同时成功、条件缺失、样本不足、
均值漂移/方差、失败分母/在途回合、重复/非有限值、精确接续计数和奖励漂移拒绝。
真实阶段检查结果：Direct样本3、联合成功0；其余三类not_started，all_training_candidates=false。
统计工具只读训练收据，无仿真、无梯度、无模型选择或最终验收。
worker内存2,913,398,784字节/上限3GiB，随后memory.stat约1.97GB anon和0.92GB file缓存，
OOM/oom_kill=0、swap.current=0；系统可用内存约5.54GiB。继续观察硬限，不移除保护。
本轮源码/测试/完整统计快照已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-screen-20261016T0539/evidence.tar.gz`，
41,304字节，SHA256 `45442e7ee148cdc6cd734afe9594700778551612fd30f9837809b2b14f7ca311`。
服务器只归档/hash；第二个新回合之后的大型轨迹/checkpoint仍本机待同步。

## 13:31 CST：四方法精确接续能力完成，当前阶段继续

开工核对main `24fd0bd0dc6fda266053bcee6b7ddf7dd23dcd1b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS和两分支日志。上一轮新增真实诊断证据，
属于进展；本轮同一stage/worker仍active，持久化54,500步/88,158更新，新增3969/3969。
已结束2回合Task/Strict0/2，第三回合在途；另外三类排队。13:31 worker内存2,604,490,752
字节、峰值2,685,267,968，3GiB/swap0，OOM0。较早快照中约645MB为文件缓存；不能仅凭
memory.current上升就断言模型内存泄漏，也不能忽略后续硬限压力。

此前阶段工具只支持Direct从n1迁移、其他三类从零启动，不能用它反复重开来代表累计训练。
现增加`prepare-next`：必须四类都完成上一有限阶段、无未结束回合、trainer与协调器终态
一致、各自最终checkpoint和父execution hash匹配，才准备独立新目录。每类从自己的n25
checkpoint保留原始replay、网络/优化器/RNG/normalizer，仍各新增11k/1M日程，24h派发保护。
复制上一阶段的冻结trainer/worker/物理代码与parameter；仅替换协调器和预检工具，内容清单
重新登记。不同超参数、最终不足11k的尾段或异常恢复，须另按证据登记，不能混入这个精确接续入口。

后续工作顺序：`rl_goal_stage_20261016.py prepare-next --previous-stage <已完成阶段> --root <新目录>`；
在同样硬限的独立本机预检服务中，按新目录冻结工具依次运行
`probe_goal_credit_20261016.py --root <新目录> --job <四种方法各自name>`；
四份真实预检收据齐全后`seal-preflight`，最后才允许`launch`。预检只做一次丢弃的更新、
不保存新模型；登记hash、checkpoint hash和方法身份逐一绑定，缺任何一类就不能launch。
每个新阶段由Goal根据上一阶段证据决定，不自动建立无界队列，也没有acceptance入口。

15项相关测试通过，新增4项覆盖四族独立继承、活动/失败/缺失/未闭合父阶段、checkpoint篡改、
四份预检及hash绑定。对当前真实running stage调用prepare-next，正确拒绝，未创建stage02。
独立53,281步checkpoint的同配置n25恢复探针通过：53,281条raw replay、恢复后采样RNG逐项
可重复、一次更新指标有限、原checkpoint hash不变；exit0、峰值1,128,882,176字节、OOM0。
这只是Direct真实恢复验证；另外三类尚无本阶段checkpoint，其真实预检尚未完成。
活动stage01继续使用原冻结快照，当前未创建或派发下一阶段，未证明收敛、未做最终验收。
本轮源码/测试/两项真实检查脚本与收据已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-continuation-20261016T0530/evidence.tar.gz`，
14,259字节，SHA256 `bcde86e186923ad2679e97160ee328eb8018216cb0a5d405928c4f0c0b466ea9`。
服务器只归档/hash，53,281 checkpoint本体及后续原始轨迹仍在本机待同步。

## 13:22 CST：目标分布与动作外推诊断

本轮核对远端main `02053647aba71bc623b0c53fe65d60fc002a8f5b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read日志和AGENTS。上一轮是实质进展，
本轮确认同一协调器、trainer和唯一模拟器仍活跃，没有重新派发。第二个完整55秒回合已结束，
到53,281步/86,939更新，本阶段新增2750/2750；return分别−21.667945、−34.277519，
Task/Strict0/2、physical_valid1/2，第三回合已启动。第二回合完整结束但物理有效性失败，
不能因无abort而算成功；原始失败收据保留。

新增`tools/diagnose_goal_rl_credit_20261016.py`，对固定51,906 checkpoint作训练replay只读诊断。
没有新仿真、梯度更新、模型保存或最终测试数据。固定seed取1024个均匀索引，再加入38个回合
各末25步，去重共1948条；末端样本被刻意加权，整体均值不是replay总体的无偏估计。
独立复算上游categorical Bellman atoms的裁剪后期望与被裁剪概率质量，保留entropy项；
采用当前actor一次固定随机样本和保存的target critic，不把它当作真实最优Q。

|训练样本组|样本数|历史动作Q均值|投影后target均值|绝对TD残差均值|当前动作Q减历史动作Q|
|---|---:|---:|---:|---:|---:|
|真实terminal|38|−2.7672|−2.8679|0.1018|2.4470|
|距terminal不足25步|950|−2.6652|−2.8527|0.1884|2.5416|
|距terminal至少25步|998|2.6072|2.6576|0.0848|0.0784|
|最新完整回合子样本|57|0.9657|−0.0536|1.1743|0.0446|

整体被裁剪概率质量均值0.00006649（0.006649%），terminal组0；这次样本不支持支持集
边界截断是主要原因。当前动作维度中abs(action)>.95占33.43%，历史动作6.74%；在末25步
当前策略的Q比历史动作高约2.54，而新回合TD残差明显较大。这提示历史replay分布外动作
估值及新回合信用回传值得继续查，并不单独证明实现bug，也不构成n25的因果优劣比较。
当前非末端entropy修正均值−0.00388，远小于正Q量级；历史MC仍不是当前soft-Q真值。

2项独立目标数学测试通过。真实诊断exit0、峰值924,012,544字节、OOM0，运行在CPU6/
2GiB/swap0/180秒有限服务；模型文件hash、normalizer计数与模型RNG均未改变。
13:20训练worker内存2,324,885,504、峰值2,351,804,416字节，3GiB/swap0硬限、OOM0；
系统swap已满是既有宿主机状态，worker实际swap.current=0。GPU44°C、513MiB，仅作资源观测。

下一步保留本次登记的n25阶段，检查后续回合/四方法队列。若terminal附近历史拟合继续良好
但当前动作高估及新轨迹失败持续，再在新有限阶段登记replay分布/actor或entropy调整；
不因单个回合就中途更改活动源码。当前四方法均未证明收敛，最终acceptance仍未运行。
本轮诊断工具/测试/结果/监视快照、首个新完整回合原始轨迹及51,906 checkpoint已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-credit-20261016T0518/evidence.tar.gz`，
264,505,895字节，SHA256 `f4a47b6801fae4d367caebb92dc2e0fd48765e9117feae4ac45d7ff2f1bec7dd`。
本机/服务器hash一致，服务器只归档；第二回合及之后新checkpoint/轨迹仍本地待同步。

## 旧恢复批次最终事实

`rl_tuned_20261015_v4/recovery_20261016_1140b/direct_task_safety`在12:41:42安全退出，
50,531步/84,189更新、累计37回合；本段新增6875步/6875更新、5个完整55秒回合，
Task/Strict均0/5。return依次−22.1773、−35.2090、−38.6078、−40.0133、−22.1345；
仅2/5 physical_valid，3条安全失败全部保留。最终checkpoint_0050531逐文件hash通过。
status=complete仅表示旧有限段已结束，training_complete=false，不代表训练完成或收敛。

## Stage01：检验长回合信用分配

历史在线2×2 n-step研究在第一组n01尚未完成时停止，n25没有在线结果。当前n1 checkpoint
多数terminal目标已拟合、非终止Q却与历史行为回报差异明显；这构成信用分配候选依据，
不是证明实现错误。采用已有上游SimbaV2的25步critic和已测的跨回合安全replay reducer。

这次只调整n_step=1→25，UTD保持1，reward/gamma/学习率/动作接口/物理均不变。
Direct从旧50,531步checkpoint迁移，保留网络/优化器/RNG/normalizer/原始单步replay；
只在采样时生成25步回报，遇terminal立即截断，无跨回合拼接，不伪造奖励或成功样本。
其余三类使用登记的payload reward从头训练，所有raw reward和失败轨迹保留。
25步未作离策略校正，存在行为策略偏差；本阶段没有匹配的从头1步对照，不能声明因果胜出。

|顺序|方法|起点|本阶段总步上限|新增交互上限|
|---|---|---:|---:|---:|
|1|Direct/task_safety|50,531|61,531|11,000|
|2|Impedance/payload|0|11,000|11,000|
|3|Admittance/payload|0|11,000|11,000|
|4|VMC/payload|0|11,000|11,000|

四类优化器总日程仍为1M交互，表中是有限阶段节点，不缩小持续Goal的完整训练目标。
完整回合边界限制可使实际交互小于上限。队列串行、每回合保存、worker硬限3GiB/swap0/
CPU1/数值线程1，协调器独立256MiB。进场要求可用内存≥3GiB+768MiB、磁盘余量≥50GiB，
同一派发锁及宿主机worker检查防重复。阶段派发保护截止2026-10-17T05:00:57.926303Z，
即10月17日13:00:57 CST；这是agent登记的有限保护，不是“到时算收敛”。

代码以独立source快照运行，允许后续Goal继续修复仓库而不改动活动worker的源码。
阶段没有acceptance入口，子作业错误会向上传播并保存失败，而不是让协调器假报成功。

## 可复核的收敛要求

在本阶段训练开始前登记：至少96个结束回合，最后两个32回合窗口均覆盖全部32个train身份，
两窗口return均值相对变化≤5%、末窗口return变异系数≤25%，且每个窗口Task AND Strict
同时成功率≥90%。所有失败均入分母；这只是训练收敛候选筛选，最终仍需四方法训练完成后的
统一acceptance与独立物理/动作重放/hash/指标审计。当前样本远未满足，不称已收敛。

## 启动前验证与当前入口

9项恢复/阶段约束测试、4项现有多步replay测试通过。真实50,531步checkpoint预检验证：
agent与上游critic确为n_step25；末25条transition的折扣奖励与独立求和一致，next_state均
止于真实terminal；恢复50,531条原始replay后一次优化更新指标有限，原checkpoint hash未变。
预检无新仿真、不保存模型，exit0、峰值1,161,908,224字节、OOM0。

本地阶段根：`outputs/rl_goal_20261016_stage01/`；登记SHA256
`661ffad196a667731bf34c9bb3855eb6ec81070bd5a6393b06a41f5b5443fcf1`。
协调器`sii-rl-goal-stage-3ced1757b345.service`，Direct worker
`sii-rl-goal-2dc62bfe00c9.service`已启动，接续状态见阶段execution与各方法execution。
其余三方法是明确队列任务，不把排队写成已经训练。停止使用本阶段STOP_REQUESTED，等待
在途回合/检查点保存，不停止仍有子模拟器的父容器或广播信号。

开工main `11809cb960cb4acdcb6ebe1a431d622979d2a3ec`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/读取，保留无关未跟踪文档。
13:11:34首个完整55秒回合结束：新增1375步/1375更新，到51,906步/85,564更新。
return−21.667945，physical_valid=true，Task/Strict均false；checkpoint_0051906全部hash
核验通过，agent与replay保存的n_step均25，第二回合已启动。这证明新训练/保存链路闭合，
不是收敛证据，不能将单个不同condition的return与上一段直接做因果比较。

新阶段源码快照/登记/预检/启动及13:07监视收据、旧恢复全部5个完整回合原始轨迹和
最终50,531 checkpoint已归档核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stage01-20261016T0507/evidence.tar.gz`。
大小750,006,095字节，SHA256
`a65bf3966e17f1a38beb244cfa7983a40a7e9bb54f7f5b8f851ee3dda38ff13a`，本机/远端一致。
服务器只传输/归档/hash，没有训练或分析计算。新阶段51,906 checkpoint及新回合轨迹仍仅本地，
留待下一次安全边界归档；原始物理runtime/MJB仍依赖登记的既有路径，此包不是完整环境镜像。
