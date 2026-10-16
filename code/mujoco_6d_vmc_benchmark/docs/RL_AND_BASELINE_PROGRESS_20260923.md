# RL 与经典柔顺 baseline 工作记录（2026-09-23）

## 2026-10-17 04:30 CST — 控制组十八回合：出现retreat但物块未放置成功

上一轮为已验证等待；本轮同一PID2502235从22,500步/17,501更新推进至24,750步/
19,751更新，观察约11.5分钟，协调器2502213保持active。开工查询/fetch/read
main `175a00679d5a63348833cb2b524c598b8febd411`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。
没有重启、重复派发或研究源码修改。观察器目标18回合并归档后正常结束，训练继续。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`已完成44k预算56.25%。
18回合均1375步/55秒、physical_valid18/18，Task/Strict0/18；平均return
−25.459916354、标准差.446578570。ep16/17（repair_train_013/011）回报
−25.510348452/−24.790855485，分别终止于retreat/carry。
24,750条交互、19,751次更新连续且指标有限，18回合reward分解/总和、AUDIT/trace hash、
cp24750成员hash通过。末temperature .001785144、critic loss7.017396。
occupancy组尚未启动，没有奖励处理收益或收敛结论。

ep16首次在本control闭合记录中进入retreat，需区分手部阶段与真实物块成功。
读取原生rollout与冻结判据：48.36秒进入load_transfer、49.04秒release、49.56秒retreat；
max_lift .153743m，但最终物块(.470675,−.265030,.424997)m，目标(.69,−.31,.545)m，
XY误差.223887940m，placement_hold_s=0、release_supported=false、placement_complete=false。
因此完整时长/物理有效并不满足稳定放置要求，Task/Strict失败与原生判据一致；
contact_coverage=false仅为诊断，不能拿它当本回合Task失败原因。未进行独立物理重放。
rollout.json SHA `9bf2355bb0afe52a515b8a69d748f8bc5381c4ed284902d5e953d9bc7180a277`、
AUDIT SHA `21ec2b7690e74e753c4f6cd12ef474a7352ac0e7e8e6d509a8c39d22bc943750`
均与已核验原始归档member大小/hash一致；冻结gate来源hash与原生记录一致。
不能将进入retreat当成功，也不据此断言掉落时点、原因或控制器修复已奏效。

归档时worker current2,433,253,376字节、peak2,888,511,488、max3,221,225,472；
memory.max事件/OOM/oom_kill/swap0，free58,046,984,192字节，50GiB保护保持。
收工worker仍active、current2,530,291,712，GPU43°C/1437MiB。
本机CPU1/单线程/CUDA0/.125/UTD1保持；CPU6/1GiB/swap0归档助手6.622秒正常退出。
服务器仅归档及hash，全部失败保留，冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5不变。

本轮证据独立归档并再次远端核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2015/evidence.tar.gz`，
10,992,222字节，SHA `0422d9f425663d07775b076a8c01eafe53c135c2a0401ab8c64ac936cc320cba`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T2015，含闭合日志、训练screen、观察/归档映射。
新增原始轨迹/checkpoint于同主机共同根 `/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-9a5268aec7cb8c6b635403a2/evidence.tar.gz`，272,023,530字节，
  SHA `e4d00bf98d46b2b696ffe613500cd1ec98b5883083648b337327470e0fdaa8a0`。
- `goal-stream-eb6481cac4f4201d9a6bc278/evidence.tar.gz`，271,401,316字节，
  SHA `833699740d082565804768ac77645f784450b2d722048ef0a5f16bcba7db3068`。

Goal active；继续44k×2对照并保留这类“手部推进但真实物块失败”的区别，四族均未证明收敛。
最终acceptance与独立物理/action-filter审计尚未执行。按sii-research-sync更新三份进度、
diff检查后提交/push main，保留无关meeting文件。


## 2026-10-17 04:14 CST — 已验证等待：控制组22k步，十六完整回合尚无成功

上一轮完成原生动作/停滞诊断；本轮确认同一协调器2502213/worker2502235存活后，
从20,250步/15,251更新观察至22,000步/17,001更新，约9.5分钟，无重启或重复派发。
开工查询/fetch/read main `c7400ac979497f4e0cb6035ebdf50c3f8de99bf2`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`完成44k预算50%；
16回合均1375步/55秒且physical_valid，Task/Strict0/16，均未证明收敛。
新增ep14/15（repair_train_015/019）return −26.029092712/−24.977225453，carry失败；
全16平均−25.498580653、标准差.441282141。22,000交互与17,001更新连续且有限，
16回合reward分解/总和、AUDIT/trace hash、cp22000成员hash通过。
末temperature .002250975、critic loss7.500761、actor loss1.571514、entropy−.175552。
occupancy组尚未启动；控制失败reward平台不是成功或处理收益证据。

归档时worker current2,395,394,048字节、peak2,848,673,792、max3,221,225,472；
memory.max事件/OOM/oom_kill/swap0，free58,156,675,072字节，高于50GiB保护线。
收工同一worker active、current2,415,771,648，GPU42°C/1440MiB。
本机CPU1/单线程/CUDA0/.125/UTD1保持；CPU6/1GiB/swap0归档助手7.890秒正常完成。
观察器只在目标回合及归档完成后结束；训练继续第17回合。

证据已独立归档核验，并再次从服务器读取大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2005/evidence.tar.gz`，
10,173,291字节，SHA `7318bd8ee255fd6d3c6731d43af589ee1a62df049e2e8a87d4954f140023a6f3`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T2005，保留WATCH、闭合日志、训练screen和映射。
新增原始轨迹/checkpoint重核于同主机共同根 `/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-a045808f4f18e5d556ca147e/evidence.tar.gz`，271,566,092字节，
  SHA `bfef83c999e7edcaea7f25f6de07f4ab44b64b354d44647dc242b0867b8e00e7`。
- `goal-stream-1c819d0c4484899952ec0176/evidence.tar.gz`，271,931,949字节，
  SHA `024838ba97582db37eb89e9fdc062ab206265edf3d4fbc936ff3741c85e28c00`。

服务器仅归档，活动代码f788fcb/登记d37b16975a6f…不变；冻结物理/MJB/gate/canonical48/
filter/执行器/dt5e-5保持。本轮属于已验证等待，无研究源码修改；四族仍未证明收敛，
最终acceptance及独立物理/action-filter重放未执行，全部失败保留。Goal active，
继续登记44k×2对照；三份进度diff检查后提交/push main，保留无关meeting文件。


## 2026-10-17 04:04 CST — 十四回合原生动作诊断：并非始终低刚度，停滞原因仍需对照验证

上一轮为已验证等待；本轮增加固定闭合前缀的原生动作/路径点诊断，避免将早期低刚度观察
外推成全部失败的原因。开工查询/fetch/read main `7dcf03ff5360664e5696a35e0b4bd6af3290951c`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。
协调器2502213/worker2502235均真实active，实时优化已到20,072步/15,073更新；
本轮诊断固定ep0–13、19,250已闭合步，不把在途记录混入结果。

对14回合逐一验证AUDIT/rollout与执行记录hash、parameter_trace及parameter_actions原始动作/
实际参数逐元素一致，输入文件前后hash保持。全部5维数组有限；运行原有冻结来源匹配、
前后步时间对齐及路径点重构检查。只读25Hz训练原生记录，未运行新仿真/梯度/物理子步/
action-filter replay，没有修改活动checkpoint、reward或source。

新证据限定了下一步判断：

- ep8/9末10秒实际第一维刚度中位834.553681/1123.982370，明显不同于ep4/5的
  189.317379/178.694966；仍停在waypoint20。不能把所有失败归因于始终低刚度，
  也不能据此推断提升刚度必定无效：条件不同，策略持续变化，尚非因果对照。
- ep11末10秒cursor18→20，观测到两次前进；其他13回合末10秒cursor20不变。
  所有回合当前采样target的position/rejoin readiness为0，但planner先更新后采样，
  因此零readiness不能被解释为全程没有推进。该诊断明确保留时序语义。
- ep12/13末10秒位置误差中位12.775111/12.849531mm，当前冻结半径为12mm；
  对应刚度中位232.280391/322.356390。只说明这些尾段仍未跨越当前路径点条件。
- 完全学习回合ep4–13，各维|raw_action|>.95比例约2.11%–13.96%，并非整段动作
  恒定饱和。至少一维触发原生rate-limit记录的tick比例99.709%–100%，不能将
  任一维过滤比例误当每一维均失效或证明失败由filter造成。
- ep8/9/13出现能量缩放，tick比例5.1636%/1.2364%/.2182%；其他回合为0。
  之前ep0–5的零缩放观察仍成立，但不能外推到后续全部回合。

诊断根BENCH/outputs/rl_goal_stream_carry_20261017T2000；CARRY_ACTIONS包含完整逐回合输入hash、
参数统计、原生gate/path证据与限制，实际脚本/tmp/sii_goal_stream_carry_20261017T2000.py也归档。
本机CPU6/单线程/1GiB/swap0，峰60,559,360字节、OOM0，13.859秒正常完成。
已核验且再次远端读取大小/SHA的共享证据：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-carry-20261017T2000/evidence.tar.gz`，
28,537,644字节，SHA `372af0b6309ef71ca941db25ace8e45dd1189d495a2b260b1f6299dcab6eacdd`。
服务器仅存储/传输/hash。收工worker内存2,511,310,848字节，GPU43°C/1447MiB。

继续已登记44k×2 occupancy对照，不据上述观察擅改刚度边界/filter或额外混入其他处理。
活动代码f788fcb、登记d37b16975a6f…保持；四族训练收敛未证明，当前control仍0/14联合成功。
最终acceptance未执行；全部失败保留，Goal active。按sii-research-sync更新三份进度、diff检查、
提交/push main，保留无关meeting文件。


## 2026-10-17 04:00 CST — 已验证等待：控制组十四回合，连续更新与归档通过

上一轮完成12回合证据发布；本轮对真实存活PID2502235有界观察约9.5分钟，
从17,750步/12,751更新推进至19,250步/14,251更新，协调器2502213持续active。
按sii-research-sync查询/fetch/read main `57b9f4a1ad5a2967ad399ede6abb7d4d3131db90`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/进度，收工重读AGENTS。
无研究源码或训练配置改动，无重复训练；观察器达到14回合且归档完成后正常退出，worker继续。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`的14回合均1375步/55秒、
physical_valid14/14，Task/Strict0/14；平均return −25.497926591、标准差.427819936。
新增ep12/13（repair_train_006/031）return −24.775301155/−24.998685579，均carry失败。
ep12原生RMSE23.551309mm、峰矩35.941719Nm、峰速.388448807m/s、穿透.156059713mm、
放置XY误差.085631292m；只是训练原生记录，不是独立验收。回报变高不等于任务完成。
19,250交互及14,251更新序号连续且指标有限，14回合reward分解/总和、AUDIT/trace hash、
cp19250成员hash通过；末temperature .002821193、critic loss7.599995。
控制44k预算已完成43.75%；occupancy尚未启动，没有奖励处理收益结论。
已读冻结协调器逻辑：仅正常step_budget结束且checkpoint通过才接续另一组，异常保留失败。

归档时worker MemoryCurrent2,359,603,200字节、peak2,812,641,280、max3,221,225,472，
memory.max事件/OOM/oom_kill/swap均0；磁盘可用58,265,899,008字节，50GiB保护保持。
收工服务仍active，GPU40°C/1440MiB；CPU1/单线程/CUDA0/.125/UTD1保持。
归档助手本机CPU6/1GiB/swap0、9.652秒正常退出。服务器仅归档/大小/hash核验。

本轮证据已独立归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T1950/evidence.tar.gz`，
9,334,574字节，SHA `01a170160822793de10863b19f0c266ce17cac213350af2ab94bd2e1781e5f2f`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T1950，含观察、闭合日志、训练screen、
实际脚本与归档映射。新增原始轨迹/checkpoint已重核，同主机共同根
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-ecb2188a818f31ec636cf4d4/evidence.tar.gz`，270,561,939字节，
  SHA `862cd135df5f53b3e28c3ed2ad1e317f8370d7415585b41c74593723e42039b7`。
- `goal-stream-4fb246fb459d819256748ab1/evidence.tar.gz`，271,347,558字节，
  SHA `5f60956e721ad39b47d574b756353e1776fae91e42903f510c20c885b779e183`。

活动代码仍f788fcb，登记SHA d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6。
物理/MJB、最终gate、canonical48/filter/执行器/dt5e-5保持；全部失败保留。
本轮是已验证等待，四族尚未证明收敛，最终acceptance/独立物理与filter重放尚未执行。
Goal active；继续44k×2登记对照，之后按配对任务/原生指标选择调整，不将小预算pilot当最终完成。
仅提交三份进度，保留无关meeting文档；diff检查后正常push main。


## 2026-10-17 03:48 CST — 已验证等待：控制组十二回合，奖励对照继续

本轮承接同一PID2502235从14,500步推进至16,500步的观察与归档；协调器2502213保持active。
复核远端main `135e1c7349bf108ae40d59e3d293b7bdfdd40e18`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read两分支日志、AGENTS与两份进度。
沙箱fetch网络失败后宿主fetch成功；baseline没有新的RL变更。Goal保持active，没有重复派发或重启。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`已核验16,500连续交互、
11,501连续有限优化更新，44k控制预算完成37.5%；12回合均1375步/55秒、physical_valid，
Task/Strict均0/12，平均return −25.599748795、标准差.372667896。
新增ep10/11（repair_train_017/012）return −25.693374591/−26.003577436，均carry失败。
12回合reward分解与总和、AUDIT/trace hash、cp16500全部成员hash通过。
末次temperature .003578299、critic loss7.789541、actor loss.616567、entropy1.863455。
收工实时读取已达17,358步/12,359更新，第十三回合仍在途；不能与已归档闭合统计混算。
occupancy处理组尚未启动，不比较不同目标的总reward来宣称收益；四族均未证明收敛。

归档时worker内存2,313,179,136字节、峰2,769,199,104、硬限3,221,225,472，
memory.max事件/OOM/oom_kill/swap均0；磁盘可用58,362,855,424字节，50GiB保护保持。
宿主19:46UTC复核同一服务active、MemoryCurrent2,460,209,152、GPU43°C/1438MiB。
归档助手CPU6/1GiB/swap0，5.824秒正常结束；本机CPU1/线程1/CUDA0/.125/UTD1训练保持。
物理/MJB、最终gate、canonical48、filter、执行器与dt5e-5均未改。

本轮证据归档已核验并再次读取服务器大小/SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T1935/evidence.tar.gz`，
8,495,607字节，SHA `9f3694059aa9a0f1a2e5b80b3afc9e62495780796f1e2e145e8c025b1d151dca`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T1935，含WINDOW、TRAINING_SCREEN、
闭合训练/优化日志、WATCH、归档收据和实际观察脚本。新增原始轨迹/checkpoint已核验于同主机
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-732f56334291d23283af4822/evidence.tar.gz`，268,897,079字节，
  SHA `7ca042aa49162a5f9090338455c0c8e1b005180b0e905093e66567d0f0f4386d`。
- `goal-stream-61f2565877a723e74fba984b/evidence.tar.gz`，269,570,697字节，
  SHA `70c3d5f0633ab36861ff41abf4f1e4a83d42b5a3f19cf0b8a7efd6d37facf81c`。

当前32训练条件均events=all，现有worker没有课程/state-reset入口；本轮未改变任务或引入teacher/replay。
活动研究代码仍f788fcb，登记SHA `d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6`。
先完成登记44k×2配对，再按相同条件/曝光的任务与原生指标决定下一调整；不将失败reward平台当收敛。
本轮仅更新三份进度，保留无关meeting文档及全部历史失败；未执行最终acceptance或独立物理/filter重放。
收工重读AGENTS，文档diff检查后提交并正常push main；Goal继续，不以观察器退出作为训练终止。


## 2026-10-17 03:29 CST — 已验证等待：同一worker闭合十回合，控制组继续运行

上一轮为固定样本critic诊断进展；本轮为对已确认存活的PID2502235的已验证等待，
从12,000步/7,001更新观察到13,750步/8,751更新，持续约10分钟，协调器2502213保持。
开工按sii-research-sync查询/fetch/read main `46a226438adf3edb8aa2717086e5536c83470876`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。
没有重启、重复训练或修改活动snapshot；观察器达到十回合且归档完成后正常退出，训练继续。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`闭合10个1375步/55秒回合，
physical_valid10/10、Task/Strict0/10。新增repair_train_010/027 return
−25.759603751/−25.400400406，均停在carry；保留全部失败，不将回报平台视为收敛。
13,750交互序号与8,751优化序号连续且指标有限；10回合reward逐项/总和、AUDIT与trace hash、
cp13750全部成员hash通过。最后temperature .004527187、critic loss8.104725。
控制组44k预算完成31.25%，occupancy组仍排队；没有处理收益或四族完成结论。

worker峰2,731,810,816字节、3GiB硬限、memory.max/OOM/oom_kill/swap0；
记录时MemoryCurrent2,280,210,432字节，本机free58,428,452,864字节，50GiB保护保持。
沙箱nvidia-smi不能访问驱动，随后宿主复核43°C/1441MiB且优化持续，未误判为GPU故障。
服务器归档盘可用3,553,241,657,344字节，仅查询容量/传输/hash，未使用服务器计算。
新增两回合归档耗时41.446/38.407秒后同一worker继续；正常归档等待不算训练异常。
CPU1/线程1、CUDA0/.125/UTD1、冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持。

本轮闭合日志、训练screen、逐回合原生结果、监视轨迹、脚本与新增轨迹已独立归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T1920/evidence.tar.gz`，
7,669,855字节，SHA `cb41442eedf21dd0a07792a7404ee5ee9a608adc4696014de5973eeffbb1f284`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T1920；分析/归档本机CPU6/1GiB/swap0。
新增原始回合/checkpoint已重核服务器大小/hash，同主机共同根
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-0aa94c08d05b7ead45da3481/evidence.tar.gz`，268,001,970字节，
  SHA `e3724b0c7cd8ce949600049b1420d660377dfb6afcc7ed17eda7cb5294c3655d`。
- `goal-stream-640d8cde1a6b99e95e5ee828/evidence.tar.gz`，269,075,243字节，
  SHA `f3c1658daf6dfc157a99eded7394063267e2d61173b629f245d935b8014b42ec`。

活动研究代码仍f788fcb、登记SHA d37b16975a6f…，本轮无研究源码修改；文档diff检查后提交/push main。
Goal active；继续control到登记边界，核对后续occupancy派发。四族均未证明收敛；
训练screen条件仍不满足，最终acceptance与独立物理/action/filter重放未执行，历史数据未删除。


## 2026-10-17 03:15 CST — 固定终局样本确认critic能学习罚分，策略泛化仍未解决

上一Goal轮有训练链路/失败定位进展；本轮开工查询/fetch/read main
`131615dc7414a03c8dafd3048ff2175ffdd0ac4c`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/进度，收工重读AGENTS。
同一协调器2502213/worker2502235持续active。只读观察到第八回合及归档闭合，未重启或重复启动。

阻抗fresh control已闭合11,000步/6,001更新（44k预算的25%），8回合全1375步/55秒、
physical_valid8/8，Task/Strict0/8。新增repair_train_022/000回报−26.077511768/−25.892417060；
末10秒均250采样停在carry waypoint20/28，位置误差中位12.801975/12.738583mm，
radius/rejoin readiness0，rotation/speed均250/250。冻结12mm门槛未改。
11,000交互、6,001优化记录连续且有限，8回合reward逐项及总和、AUDIT/trace hash、
cp11000成员hash通过。occupancy组尚未启动，没有奖励处理收益结论。
收工live optimizer为11,342步/6,343更新；第九回合在途。

本轮先以cp9625的1,131个预定训练样本检查n25 categorical critic：
平均clipped mass1.55e-6、终局窗口0，未见显著support截断。较早6回合末25步TD残差均值
.0269027；刚闭合第七回合为3.6951479。这些新终局数据刚进入训练，不能凭此判定学习故障。

随后在cp9625与cp11000上固定全部前7回合的末25步，共175条完全相同历史样本：
经验池前9625条每字段字节hash一致，独立逐步折扣求和与n25回报一致；
没有bootstrap的终局窗口直接对比已保存尺度下的奖励目标，两个checkpoint均截断0。
第七回合25条TD绝对残差均值3.695133→.016740，normalizer分母6.278640→6.015730；
换回原reward尺度残差23.200407→.100701，说明新增1,375更新确实学到了这批失败罚分。
并非所有历史样本都改善：前6回合平均绝对残差.026902→.046366，后者最大2.903373。
不能将局部拟合改善等同于策略收敛。

cp11000当前actor动作Q比历史动作Q高：前6回合末段均值差2.898145、第七回合2.729928。
这是相同历史状态下critic估值的泛化/外推疑点，未执行替代动作的物理结果，不是已证实的
真实Q误差或失败因果关系。继续既定44k×2奖励对照；不因该疑点修改活动网络、扩大support、
放宽filter/gate或立刻同时叠加正则化。完整对照后再依据任务结果与估值证据决定下一实验。

两只读诊断本机CPU6/2GiB/swap0/CUDA0完成，峰1,291,501,568/1,280,163,840字节、
max/OOM均0；网络/RNG/归一化/checkpoint在各探针内均未改变，新增梯度/仿真0。
训练峰2,694,467,584字节、3GiB硬限、max/OOM/oom_kill/swap0；
收工MemoryCurrent2,293,448,704字节、GPU42°C/1439MiB。分析/归档CPU6/1GiB/swap0。
研究实现仍f788fcb，活动登记d37b16975a6f…及解释器/物理/MJB/48维/执行器/dt5e-5均保持。

报告、固定样本索引/逐样本估值/原数据hash、闭合日志、原生新轨迹和脚本已上传并重新核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-credit-followup-20261017/evidence.tar.gz`，
6,898,258字节，SHA `ec8e868bf6605583c85f40b8c7b34bbdb0fc775cd12d5441342e67aa291ba4de`。
本地缓存BENCH/outputs/rl_goal_stream_credit_followup_20261017；服务器只传输/归档/hash。
新增两回合完整原件/checkpoint独立归档重核如下，同主机共同根
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-ff349b04467a9829252d900f/evidence.tar.gz`，267,262,273字节，
  SHA `0f9fe58a43b4ad034302d3b18e8ed10133e9f17529acc6103a5073d3c647b9f5`。
- `goal-stream-d929a5499e35e76fc29df4da/evidence.tar.gz`，267,502,587字节，
  SHA `fdc8c8246765cd2cefab96ecbdf626eadc87ec21b3b22f04df5b456c94a5022d`。

本轮无研究源码变更；诊断脚本和断言验证随证据保留。三进度文档diff检查后提交/push main。
全部失败/历史数据保留；四族均尚未收敛，最终acceptance和独立物理/filter重放未执行。
Goal保持active，继续健康control并核对occupancy自动接续。


## 2026-10-17 03:04 CST — 阻抗早期学习链路核验通过，完整回合仍停滞于carry

按sii-research-sync查询/fetch/read远端main `9f4b8747dfea25e66e1007941b32678d5e31d6de`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/进度；收工重读AGENTS。
Goal工具确认active。本轮观察同一worker PID2502235从6500推进至8250，协调器PID2502213保持；
观察器在两个全程学习回合闭合后正常退出，训练未停止。收工optimizer实测9228步/4229更新。
未重复派发、重启或修改活动source；occupancy处理组仍排队。

已封存分析覆盖8250条连续交互与3251条连续优化更新，全部优化指标有限。6个完整55秒
回合均physical_valid=true、Task/Strict0/6。前三回合warmup，第四混合，第五/六全程学习；
后两回合return −25.633716548/−25.106000635。六回合总体return均值−25.395017、
标准差.379481，仅为早期描述，失败平台不算收敛；不足96回合和两个完整32条件窗口。
step8250 temperature .007397509、actor loss−.3102534、critic loss8.802989。

本轮新增训练链路核验：checkpoint经验池action与控制器收到的5维raw_action逐项一致；
reward与final_reward在浮点精度内一致；terminal恰在6个闭合边界；parameter_actions与
parameter_trace一致；各回合reward分解/terminal/potential求和通过；cp6875/8250全部成员
hash通过。没有发现“优化更新但动作未连接”证据。这里是原生记录/文件一致性核对，
没有执行新的独立物理子步或action/filter重放，最终acceptance未运行。

两全程学习回合末10秒各250采样均处于carry waypoint20/28，无采样cursor变化。
重建目标残差0；radius/rejoin-plane readiness均0，rotation/speed readiness均250/250。
位置误差中位数12.769655/12.639503mm，冻结门槛12mm未改；该结果定位停滞，
不能独自证明根因或任务不可行。原生记录的rate-limit比例从warmup约.608–.623升至
两个学习回合均1.0，energy-limit均0；这不是因果结论，也不是放宽公共filter的依据。
两回合实际刚度均值约269.986/268.013、末段中位数189.317/178.695，合法范围150–1800，
无刚度硬上界导致不可行的证据。继续既定44k control/44k occupancy同seed对照；
处理组尚未训练，不跨奖励定义比较总return来宣称改善。

当前worker MemoryCurrent约2,351,947,776字节，峰2,656,804,864，硬限3GiB；
memory.max/OOM/oom_kill/swap均0，GPU43°C/1439MiB，磁盘余58,563,842,048字节。
CPU1/线程1、CUDA0/.125/UTD1、50GiB余量及全部冻结物理/gate/输入/执行器保持。
分析在airpig CPU6/1GiB/swap0完成；服务器仅归档/hash。训练源码仍f788fcb，
登记SHA `d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6`。

本轮报告、闭合日志、6回合原生诊断、观察与归档收据/脚本已独立归档，收工重新核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-early-learning-20261017/evidence.tar.gz`，
14,095,897字节，SHA `7888eaeb0accadfacce3b4f5f3d1ab7a6fc97fd72d18158ff12911786117283f`。
全部6个原始回合/checkpoint远端归档均在分析中重核大小/hash；新增ep4/5位于同主机、
共同根`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-8c0e92f011ff3f8c38099b4c/evidence.tar.gz`，266,364,943字节，
  SHA `1b60e738d486843d3073478c25413d53186dfb8a86c34b585a0185664f0dc4b4`。
- `goal-stream-92f5dd52122e58bc89788efb/evidence.tar.gz`，266,072,999字节，
  SHA `bcb1ce09417b792be0aafc5d9d3db368ff12fc8b55854ebd4c95e7f97f43ffda`。

本地报告缓存为BENCH/outputs/rl_goal_stream_early_learning_20261017。
两回合归档约35.5/37.4秒后原worker自动继续。历史数据未删除，全部失败收据保留。
本轮未改研究代码，不重复无关测试；文档diff检查后按约定提交/push main。
Direct/阻抗/导纳/VMC均尚无收敛证明；继续诊断和登记实验，Goal保持active。


## 2026-10-17 02:47 CST — 阻抗进入真实优化更新，旧checkpoint远端恢复验证通过

按sii-research-sync开工查询/fetch/read main `f788fcb9f74dfced22180ddd421184a5048249c8`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与Goal progress。
普通沙箱网络失败后宿主核验成功；收工再次fetch/查远端，两分支未前进，并重读AGENTS。
上一轮为真实启动/修复进展；本轮对已确认存活的同一PID2502235持续观察15分钟，
协调器PID2502213保持，未重启、重复派发或改活动源码/冻结协议。只读观察器已正常结束。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`前四个回合已闭合到5500步/501更新：
repair_train_008/029/001/007均1375步/55秒、physical_valid=true、Task/Strict0/4。
return依次−25.493412/−26.067121/−25.072284/−24.997567；均值−25.407596、标准差.425116。
前三回合全部warmup，第四回合跨过5000步开始学习，不能把这些早期不同condition的return
或小方差当收敛/奖励改进。训练筛查为false：不足96个回合及两个完整32-condition窗口。
occupancy处理组仍排队，尚无本轮奖励对照结果；四类Goal均未证明收敛，最终acceptance未运行。

5500条交互按step1..5500连续、501条optimizer按step5000..5500/update1..501连续，
所有优化指标有限；四回合reward逐项/terminal/potential求和、AUDIT和checkpoint hash通过。
step5500的actor loss−.0813624、critic loss8.985741、temperature .00956446，均为训练诊断。
收工实测5750步/751更新，第五回合在途；worker峰2,621,403,136字节、3GiB硬限，
memory.max事件/OOM/oom_kill/swap均0，GPU43°C/1439MiB；free58,647,646,208字节。
CPU1/单线程、CUDA0/.125/UTD1、50GiB余量、44k×2预算和全部冻结输入/物理/gate保持。

真实第三/第四回合的工作副本管理已执行，最新cp4125/5500逐成员hash通过。
cp1375及2750的大本地工作副本在各自远端核验后释放；原始完整版本和失败收据保留远端。
实际下载cp1375所在包，在独立一次性/tmp目录重建其全部9个成员，再用原checkpoint
验证器检查episode_boundary、step及成员hash，全通过；没有重编译模型或写入活动训练目录。
验证后的重复下载/重建临时副本已清理，可由下述归档精确恢复。历史其他run未删除。
各回合归档耗时约26–43秒，成功后同一worker自动继续；这些文件核验不是独立物理/action重放。

本轮闭合日志、501次更新、reward分解、训练筛查、15分钟PID/steps观察、旧cp重建证据、
原始归档完整地址/hash索引和脚本已上传并核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-learning-start-20261017/evidence.tar.gz`，
1,095,611字节，SHA `2759b6956042f538b06ae924cfa04c050f2049222c7011321699968a4561cd88`。
新增ep1/2/3原始数据与各自checkpoint已由训练流程独立归档，并在本轮重核远端大小/SHA：
服务器主机`arm1@192.168.31.70`，共同根`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-fe6f4f3f05ceab4f6bb4c2cf/evidence.tar.gz`，193,801,251字节，
  SHA `2ee94fff6cefa084b816fb92b73cbb6422f551dfc3205e30418da6b059d294ef`。
- `goal-stream-0e675db8295f38c5685cc3b8/evidence.tar.gz`，194,069,554字节，
  SHA `662964169a614e6678b15c7d281b9fbb692ec431d897619c336252988883945d`。
- `goal-stream-43fd4f7a9d13c4e41b185c6a/evidence.tar.gz`，264,820,990字节，
  SHA `bc1650addd7572742cc81299614e6aced420584f6f804aeb461f3c9b6eb85afc`。

计算/重建/分析均在airpig，服务器仅文件/归档/hash。运行登记仍为d37b16975a6f…；
完整冻结source及Python依赖见上一轮归档，当前研究代码提交f788fcb未改动。
继续健康control到登记边界并核对处理组接续，再按完整数据决定四类下一阶段；Goal保持active。

## 2026-10-17 02:16 CST — Direct正则化对照关闭，新阻抗44k对照以预登记工作副本策略接续

开工查询/fetch并读取main `474f80d100c301b1c195716a6442f860de8e0a58`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与AGENTS；普通沙箱fetch连接失败后，
宿主机fetch成功，两分支未前进。继续现有Goal，不重复创建或把阶段完成记成收敛。

Direct正则化组自然关闭32,262步/27,263更新，本段11,000次连续有限更新，8回合全部
1375步/55秒、physical_valid=true、Task/Strict0/8。return为−21.856347/−21.845347/
−21.867770/−21.850740/−21.849019/−21.782428/−21.832327/−21.775935，最终temperature
.006969546。峰值3GiB、memory.max505，OOM/oom_kill/swap0。全部8个checkpoint成员hash、
AUDIT、reward逐项复算通过。协调器2489803/worker2494519均自然退出，未重启健康进程。

控制组仍为30,984步/25,985更新，8尝试中7完整/6physical_valid、Task/Strict0/8。
严格相同condition和训练暴露的完整配对只有ep18/19：正则化reward分别低.016929/.159174；
RMSE分别59.631636→36.605086mm、486.685389→42.111425mm，穿透均略增。
从ep20开始，控制的97步提前失败使两组暴露不同，后续保留而不混作等预算配对。
全组物理有效率的差异是单seed训练观察，不能推出总体调参有效；两组都没有任务成功，
稳定的失败reward不是收敛。完整PAIR_REPORT及全部失败保留，最终acceptance未运行。

服务器独立归档已逐一核验大小/SHA，本机airpig计算，服务器仅文件传输/归档/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-regularized-close-20261017/evidence.tar.gz`，
1,893,048,841字节，SHA `87ab1ea077c1bbb9d48c2161aafaf3a2d646842bd44fd8677c11b5f592d1eeff`。
含正则化ep19–25原始轨迹/checkpoint（ep18已有上一轮独立归档）、完整11k日志、比较/筛查，
以及新存储源码快照、预检与失败记录。当前历史原始轨迹和checkpoint删除0。
仅在重核远端hash后释放3个/tmp重复tar，共4,183,705,513字节，CACHE_RELEASE收据保留恢复地址；
此前历史100文件删除拒绝未绕过。

新工具goal_prospective_storage_20261017仅接受全新rl_goal_stream_*目录，必须在任何job
输出/LAUNCH/execution出现前封存STORAGE_POLICY；旧run不可追认。每个完整或提前失败回合
先保存checkpoint，再用CPU6/1GiB/swap0辅助服务打包、逐成员核验、独立服务器目录发布并
核验最终hash，落盘恢复收据后才释放该新批次四个大临时文件。最新两个checkpoint留本地，
较早checkpoint也必须先核验各自远端副本才释放工作副本；小轨迹/日志/全部失败收据保留。
restore只写缺失的原始字节，拒绝覆盖不同文件，不重编译MJB。断网/hash不符/容量不足则
保留现有副本并在已保存checkpoint边界报告失败，不继续派发或创建重复进程。
该前瞻策略不授权删除历史数据，不修改活动旧训练源码。

109项Goal测试通过，其中8项新测试覆盖历史/在途/软链接拒绝、断网、篡改、释放中断恢复、
最近两checkpoint保留及精确恢复。全新合成文件完成真实服务器上传/下载/逐字节恢复，
不是仿真结果。首次CUDA预检因仅用AllowedCPUs而affinity检查不符，0更新失败保留在
rl_goal_stream_occupancy_20261017；改为显式taskset后使用独立_v2，不覆盖失败。
新CUDA预检2次丢弃更新通过、初始网络一致、reward normalizer和n25 terminal复算通过，
原cp hash未变；峰1,609,830,400字节、OOM0。

新批次本地根`outputs/rl_goal_stream_occupancy_20261017_v2`，登记SHA
`d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6`。
保留已准备occupancy科学对照：两组fresh、同seed/配置/44,000步，差异仅
4*(1−measured payload phi)*dt/55训练附加成本；不把不同reward总值差当改进。
源码/预检重新冻结，单模拟器CPU1/单线程/3GiB/swap0、CUDA0/.125/UTD1、1M优化器日程、
物理/MJB/最终gate/canonical48/filter/执行器/dt5e-5保持。
根据原cp体积与工作副本上限，额外空间估计4,543,866,268字节（含2GiB余量）；
仍保留50GiB每回合保护。估计不是最坏情况保证。
18:15:32 UTC启动协调器`sii-rl-goal-stage-51973845a385.service`及control
`sii-rl-goal-03c22cf08c22.service`，实际PID2502213/2502235；第二组排队。
18:22:11 UTC首个repair_train_008闭合1375步/55秒，physical_valid=true、Task/Strict=false，
return−25.493412。仍是5000步warmup，更新0，不是学习有效性证据。1375条连续reward日志、
原生audit与cp1375全部hash通过。自动归档辅助服务28.924秒成功，四个新大工作副本释放后
第二回合接续；本地cp1375仍完整。首次真实原始归档为
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/goal-stream-a963f5309264e9830049c265/evidence.tar.gz`，
193,117,060字节，SHA `0cb14189dd735e55136ce8875431905b69ecc6c506d8e74110c52fde90b81709`。
另从服务器下载该包，核对全包及所有原始/模型成员hash一致，下载重复缓存核验后释放。
这只验证文件完整性和归档链路，不是独立物理重放；真实较早checkpoint释放仍待第3回合验证。
首回合运行证据/闭合日志/新工具和8项测试已独立归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-first-episode-20261017/evidence.tar.gz`，
340,777字节，SHA `0e4158cf7726e31f41f9ad032bb64ba62acafffb8a2679a1ddf68d41c14fb203`。
收工18:25 UTC观察1750步/0更新，第二回合在途；worker当前约1.89GB、峰1.98GB，
OOM/max/swap均0；GPU上次宿主观测40°C/1115MiB。本地free58,865,954,816字节。
按sii-research-sync收工重读AGENTS；两分支复核仍为开工SHA，保留无关未跟踪meeting文档。
四方法均未证明收敛，Goal保持active；没有统一acceptance或独立最终物理/action重放。

## 2026-10-17 01:43 CST — Direct控制组关闭，正则化组已接续并取得首个对应回合

开工实时查询/fetch/read main `6b069036afe2fcf2ab24e739a3465b8792c14cb4`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS；按sii-research-sync收工重读。
上一轮完成真实派发，本轮持续核对PID2489819直至正常退出，未中断健康worker或改活动源码/登记。
同一协调器2489803于17:35 UTC自动接续正则化worker2494519，无重复模拟器，Goal继续active。

Direct控制组有限段正常结束30,984步/25,985更新，新增9,722次连续有限更新。
八次尝试：7完整、6physical_valid、Task/Strict0/8；第三次ep20/repair_train_030为97步/3.88秒，
global_penetration_exceeded_2mm提前失败，return−41.398965；ep22/repair_train_024虽然完整，
physical_valid仍false，return−39.207510，原生训练收据RMSE560.324mm、穿透1.373658mm，阶段align。
其他六次return约−21.686至−21.865，仍是任务失败。余下预算不足容纳一个完整回合，
按既定边界停在30,984而非强行凑32,262；不是异常暂停。峰3GiB/max2190，OOM/oom_kill/swap0。
全8个checkpoint成员hash、AUDIT hash、reward逐步组件/求和与9,722条连续日志核验通过，
保留短回合与完整但物理失败回合。尚未完成两组比较，更不代表Direct收敛。

正则化组确认actor_bc_alpha=1、actor_regularization_migration=true，从同一原cp21262恢复，
其余agent/reward/seed/physics/48维/filter保持。首个1375步/55秒回合已闭合至cp22637，
对应控制组同一repair_train_021、同一21262→22637训练暴露，双方physical_valid=true、Task/Strict均false：
- reward：控制−21.839418，正则化−21.856347，差−.016929，没有提升。
- 原生训练RMSE：59.631636→36.605086mm；峰矩44.300316→37.913303Nm；
  峰速.346483→.334012m/s，穿透.134222→.135829mm，放置XY误差.259996→.183428m。
- 双方最终阶段仍approach。只是一对训练条件下的局部指标改善，不能推出整体调参有效、
  收敛或最终验收通过；策略在回合内继续更新。全部未对应、短回合与失败项仍在PAIR_REPORT中。

首个正则化回合1,375条连续有限更新、原checkpoint恢复hash、reward分项与新cp22637成员hash通过。
收工真实optimizer23,466步/18,467更新，temperature .002711194；
`sii-rl-goal-baf3c94bbf55.service` PID2494519 active，内存2,275,340,288字节，
max/OOM/swap0、GPU42°C/1438MiB。CPU1/单线程/3GiB/swap0/CUDA0/.125/UTD1不变。
第二回合在途，后续继续按原有限预算训练，不因单对局部改善提前选择策略或改协议。

本轮仅释放已重新核验服务器最终副本的/tmp阶段关闭重复tar，1,336,207,540字节；
原始轨迹/checkpoint删除0，CACHE_RELEASE.json保留精确恢复地址。历史100文件删除拒绝仍未绕过。
free61,909,770,240→63,245,971,456（释放时）；收工59,031,752,704字节，50GiB保护保持。

已核验服务器独立归档，本地/暂存/最终大小和SHA一致，服务器仅文件/hash：
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-control-close-20261016/evidence.tar.gz`，
  2,020,110,510字节，SHA `645294b33182491fe654a8c6a3991fe12964ab4c514c87e6213200c49ccb2983`。
  全控制组8尝试及cp、完整training/optimizer日志、原生失败收据、reward复算、
  pair/screen快照、缓存释放收据与本轮脚本。
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-first-pair-20261016T1742/evidence.tar.gz`，
  270,546,162字节，SHA `8b7dfe9bd2d352503724be6ff91a8a4bbbd9eada5fe8d7f01e3e9f402865d237`。
  正则化首个完整回合/cp22637/1375更新、首对比较、登记及脚本。之后新数据仅本地，待安全边界归档。

继续正则化组至登记边界，再依据全部证据比较两组。阻抗occupancy试验仍未派发、容量待解决。
四方法尚无可验证收敛，未进行统一acceptance或独立最终物理/action审计；Goal范围与完成标准不变。

## 2026-10-17 01:09 CST — 四族阶段关闭，Direct正则化在线对照已真实接续

开工实时查询/fetch/read main `f3b38923f05a2a318bb51805dae4fe9235934cec`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，按sii-research-sync开工/收工重读AGENTS。
上一轮是归档进展；本轮持续核对同一VMC真实PID/步骤，直到协调器和worker均MainPID0/inactive，
再启动已准备的有限对照。没有重复训练、未修改活动/冻结源码或协议，Goal继续active。

VMC在17:03 UTC正常关闭23,375步/18,376更新；本段8回合全部1375步/55秒、physical_valid，
Task/Strict0/8。11,000条连续有限optimizer更新、逐回合reward求和、AUDIT与checkpoint成员hash通过。
八次return为−25.216931/−25.206806/−25.658431/−25.216424/−24.923777/−25.304485/−24.912112/−25.323514；
峰3GiB、memory.max2650为硬限回收事件，OOM/oom_kill/swap0。四族stage02_v2终态finite_stage_complete。
所选lineage的Direct/阻抗/导纳/VMC分别18/17/17/17闭合回合，联合Task AND Strict均0；
Direct完整14/physical13，另外三类各17完整/physical。均不足收敛所需回合和两个完整窗口，
不能把参数RL的稳定失败reward视为收敛，未运行最终acceptance。

新增只读VMC失败诊断覆盖捕获时前4个完整训练回合：末10秒均carry，
位置误差中位15.872/12.393/16.009/12.350mm，对应路径点17–18，仍高于12mm门槛；
参数速率限制tick占99.42%–100%、能量限制0。与其他参数方法的carry停滞表现相似，
不构成限速导致失败的因果证据，不放宽冻结限制；未做独立action/filter或物理重放。

本轮核验并释放5个明确/tmp重复传输tar，共2,613,878,367字节，服务器原包逐一重新核对大小/hash，
原始轨迹和checkpoint删除0。CACHE_RELEASE.json列出完整恢复地址；此前被拒绝的历史100文件操作未执行。
Direct容量估计使用最近10尝试平均1026.9步/尝试，预计两组22次尝试，包含剩余VMC、replay增长和2GiB余量：
free65,288,507,392，估计新增11,429,325,176，剩53,859,182,216字节，略高于50GiB保护。
这不是最坏情况保证；更短失败会增加checkpoint，逐回合磁盘检查不变。收工free62,677,520,384。

17:05:28 UTC按原登记启动Direct alpha0/1对照：
`sii-rl-goal-stage-210cab565c96.service` PID2489803，
控制组`sii-rl-goal-c05f012de695.service` PID2489819，正则化组尚排队。
准入可用内存7,941,910,528字节、GPU宿主核验36°C/15303MiB空闲，无旧RL worker；
单模拟器CPU1/单线程、3GiB/swap0、CUDA0/.125/UTD1保持。原cp21262、相同reward/seed，
每组最多新增11k至32262、1M优化日程，登记SHA `1be1942c09c6f03b5b361b0c694e9449331edd36aa0febd451e6055601a87f45`不变。
启动证据核验21,590步/16,591更新、328次连续有限新更新，原checkpoint恢复hash一致；
收工optimizer已22,000步/17,001更新，max/OOM/swap0。尚无本轮完整回合收益结论，不能预称正则有效。

已核验共享（本地/暂存/最终大小与SHA一致，服务器仅存储/hash）：
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stage02-close-20261016T1705/evidence.tar.gz`：
  1,336,207,540字节，SHA `3e5e76e408cc07d153282e95727aa546cd10e7539d04e7bf605eb821e4745775`。
  含VMC cp17875/19250/20625/22000/23375与对应5回合原始数据、完整11k日志、
  四族screen/终态、容量/缓存释放收据及前4回合诊断、全部本轮脚本。
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-pair-launch-20261016T1708/evidence.tar.gz`：
  206,410字节，SHA `6655309c511f9111d9f4a42680ab511aa4f4ec0cda28e85f65b738798ec65af3`。
  含真实launch/恢复快照、登记和预检收据、328次连续新更新前缀及pair报告。后续训练原始数据仍本地，待闭合归档。

下一步继续真实Direct两组在线对照，按完整失败/成功与相同条件、训练暴露核对结果；
阻抗occupancy对照仍需容量，尚未派发。四方法最终收敛与统一测试仍未完成，不缩小Goal范围。

## 2026-10-17 00:38 CST — VMC真实推进与Direct在线对照接续核验

开工查询/fetch/read远端main `f9969c69a396b94c6663cd05c6a048a9cfc91b0b`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按sii-research-sync开工与收工重读AGENTS。
Goal工具确认active，承接原持续目标，不重复创建或启动worker。本轮无训练源码/协议修改。

当前协调器2447861/VMC2479454与其单个模拟器正常推进；核验期间optimizer从17,307/12,308推进到
17,858steps/12,859updates，temperature .003200021。execution快照17,750/12,751。
当前段已核验前三完整回合均1375步/55秒、physical_valid，Task/Strict0/3；
return依次−25.216931、−25.206806、−25.658431，不能据此声称reward收敛。
内存当前3,110,014,976、峰3,202,686,976字节，max/OOM/oom_kill/swap0，GPU39°C/1439MiB。
free62,989,017,088字节，50GiB保留线继续；不存在重复RL训练worker。

本机CPU6/1GiB/swap0归档helper核验cp16500、4125条连续有限更新和三个已结束回合reward求和、
AUDIT hash及checkpoint各成员hash。新增第3回合原始产物/cp16500、闭合日志前缀、现场快照、
登记与Direct既有预检记录核验共享至独立目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-progress-20261016T1640/evidence.tar.gz`，
269,013,117字节，SHA256 `475880a8c61e86cbf8f56819f79c778f76477fe0e476a30a3b5fb453205b00a6`。
本地/暂存/最终大小和hash一致；服务器仅存储/hash；16500之后数据待后续安全边界归档。
归档脚本随包保存，现场收据本地位于outputs/rl_goal_vmc_progress_20261016T1640。

已重新核验Direct alpha0/1有限在线对照登记、source/checkpoint和封存预检（未重复学习预检）；
登记SHA `1be1942c09c6f03b5b361b0c694e9449331edd36aa0febd451e6055601a87f45`不变。
两组均从cp21262增加最多11k交互，尚无LAUNCH/execution。等待当前四族阶段全部闭合，
派发时仍须复核全局锁、磁盘/内存/GPU、截止；本次通过静态核验不等于派发准入或在线收益。
阻抗occupancy对照仍待存储容量，未移除历史原件、未绕过既有删除审批拒绝。
四方法均未证实收敛，未最终acceptance；Goal保持active，下一实质步骤为本段结束后的Direct在线对照。

## 2026-10-17 00:30 CST — 新奖励接续修复与真实CUDA保存恢复核验

开工实时查询/fetch/read main `40bc1546ae10ae2aa1ea02c1cad916c62f763049`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，依sii-research-sync开工/收工读AGENTS。
上一轮闭合导纳并找到错误放置失败类型，属于实际进展。当前协调器2447861/VMC2479454未重启；
归档快照15,500步/10,501更新，收工16,091步/11,092更新。已完成前2个新回合均1375步/55秒、
physical_valid、Task/Strict0/2，return−25.216931/−25.206806；cp13750/15125和2750条连续有限更新核验。
VMC约2.81GB/max/OOM/swap0、GPU39°C，free63,482,564,608字节，50GiB保护继续。

修复新reward已能独立试验但未完整接入四族选型/后续接续的缺口：
`goal_selected_continuation`识别occupancy双组，逐job核对并保留payload_occupancy_guidance，
记录原试验登记/hash来源，选回旧checkpoint时明确清除该job的新reward字段。
只按已登记trainer/helper的精确hash识别可选实现迁移，其余冻结源码仍须一致；
可与既有actor正则化实现共用同一冻结来源，不改active source或已准备pair。
`rl_goal_stage`保留后续来源和必要依赖，拒绝缺失来源/悄然删改reward；
`probe_goal_credit`在分配agent前核对checkpoint奖励定义，预检封存与再验证同时核对奖励身份。
新fresh pair准备清除上一段的occupancy来源，防止错误继承。

101项Goal unittest通过，新增5项覆盖选择后再接续、独立冻结入口、fresh历史计数、源码/奖励篡改、
活动pair拒绝、显式旧模型重选及预检封存；修改收据hash也不能绕过奖励身份检查。
合成48回合失败历史保持联合成功0，不因fixture阶段结束判为收敛。

真实本机CPU6/2GiB/swap0/CUDA0预检通过：使用1375条既有训练replay重算已登记reward，
丢弃一次更新后保存专用PROBE_ONLY检查点，再重载并核验4网络/优化器/RNG、归一化统计/计数、
raw replay与下一次抽样完全一致，重载后另一次丢弃更新有限；原cp23375及三份登记hash不变。
已登记四族/Direct正则化/occupancy源码兼容检查通过，删除或改reward权重被拒绝。
峰2,137,206,784字节、max/OOM0。该检查点只有replay诊断用途，不是候选策略、没有在线训练或新增仿真；
未来实际选中checkpoint仍必须完成四方法逐一预检，不能用本次fixture代替。

源码/新增测试、真实CUDA保存恢复收据及诊断检查点、VMC前2完整回合/cp与2750连续日志已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-occupancy-continuation-20261016T1630/evidence.tar.gz`，
666,344,069字节，SHA256 `f47bb1fc7ca8626479b4f7d06c466ed2dc2eb7541a0d904ead5d8a2eab79836f`，
本地/暂存/最终大小和hash一致，VMC checkpoint成员hash核验通过。预检source保留当时4个新测试版本，
delivery/source另收录最终第5个封存检查测试；运行时代码未在预检之后变化。服务器仅文件/hash。
VMC cp16500及之后的新产物不在本包，待后续安全边界归档。

Goal保持active，四方法仍未证实收敛、未运行最终acceptance。继续VMC至已登记边界，再按现有协议和资源检查
推进Direct正则化对照；occupancy配对尚未派发。历史100原文件删除仍待明确授权，本轮未删除原件或checkpoint。

## 2026-10-17 00:15 CST — 导纳阶段关闭、VMC接续与错误放置诊断

开工实时查询/fetch/read main `fd1b5660c87a88477507b306941105a307525987`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，按sii-research-sync开工/收工读AGENTS。
上一轮有实际工具修复/归档进展；本轮保留所有失败、原件和活动source，历史100文件移除仍未获明确批准，未执行。

导纳正常关闭23,375步/18,376更新，本段11,000条连续有限更新、8完整55秒physical_valid回合、Task/Strict0/8，
末return−25.351177、temperature .001980882；cp23375成员hash和逐回合reward求和核验。
协调器2447861自动接续VMC2479454（sii-rl-goal-f97f0a2da6b1），收工实测12,978步/7,979更新；
无重复worker。导纳最终峰3GiB/max2369、OOM/swap0；VMC当前约2.52GB/max/OOM/swap0、GPU38°C，
free64,913,981,440字节，50GiB保护保持。四方法当前选中lineage闭合回合数18/17/17/9、联合成功均0；
这是训练screen快照，未证实收敛、未最终acceptance，VMC本段首回合在途。

新增8阻抗/6导纳完整训练回合的动作和reward诊断：原始动作std约.51–.66，几乎每tick至少一维受参数速率限制，
能量限制0。不能据此判定零控制能力或放宽限速。7阻抗carry末段位置误差中位12.69–15.83mm，
6导纳为14.12–17.03mm；阻抗ep16却已进入release/retreat，物块目标XY误差258.172mm、release_supported=false。
首次carry-only诊断因此报错，原脚本/失败收据保留，修正适用范围后全量保留14回合，峰506,691,584字节/OOM0。
固定轨迹occupancy重算对该错误放置额外成本−3.097749，其他7个阻抗carry为−2.0065…−2.0506；
支持已登记在线候选的检验理由，不代表新策略收益。详见`RL_PARAMETER_FAILURE_DIAGNOSIS_20261017.md`。

诊断/源码/失败收据、导纳ep13–15和cp19250/20625/22000核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-parameter-diagnosis-20261016T1615/evidence.tar.gz`，
852,248,130字节，SHA `2e724776968fb1d0dd32a4a512a895892b20a51c71934430093cf0ce70a08dbb`。
导纳最终回合/cp23375、完整日志和四族screen补包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-close-20261016T1615/evidence.tar.gz`，
278,175,559字节，SHA `d2ebefcd27119b779e8cf6b8c3b9c35203f091f82d7d6eadaf3a57fee2a219e0`；
两包本地/暂存/最终一致，服务器仅文件/hash。VMC新数据仍仅本地、待安全回合边界归档。
Direct正则化/阻抗occupancy两组准备协议保持未派发；继续VMC，当前四族阶段闭合和资源准入后才开后续有限对照。
Goal active；本轮为真实训练推进和新失败类型证据，不把阶段结束或shadow成本当收敛。

## 2026-10-16 23:58 CST — 导纳持续推进、归档核验提速与存储保留审批

开工实时核对main `50af442b2b75ff6351eff48114aae54b6a11d7d2`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两分支日志，开工/收工重读AGENTS。
持续Goal保持active；协调器2447861和导纳2467890未重启。15:58 UTC execution为20,250步/15,251更新，
optimizer已到20,287步/15,288更新，temperature .002585187；真实推进。当前段5个结束回合均完整55秒、
physical_valid，Task/Strict0/5，return依次−25.493493、−25.264967、−25.422910、−25.312598、−25.247658；
第6回合在途，VMC尚待本段接续。导纳峰3GiB、memory.max483、OOM/oom_kill/swap0，GPU38°C；
本地free67,053,481,984字节，保持50GiB保护。Direct/阻抗仅有限段结束，四方法均未证实收敛，未最终acceptance。

离线归档核验helper改为一次顺序解压扫描，仍扫描全尾部并拒绝重复/链接/缺失/大小或hash不符成员；
10项既有保留/恢复unittest通过。只读盘点首次目录层级识别错误得到0候选，修正后重新核验25个已结束历史回合；
两份盘点收据均保留，未据错误结果删除数据。已生成25份逐回合计划，精确列出100文件共3,655,768,123字节及
原件inode/mtime/hash、服务器包/member/hash；另记915个checkpoint及其他文件的保留前hash。
自动审批拒绝批量本地移除：AGENTS规定“历史数据不自动迁移或删除”，本批缺少明确删除授权。
拒绝发生在进程创建之前，无evict服务、无RESULT/删除journal；随后100原件全部重新hash确认在本地。
`outputs/rl_goal_storage_20261016T1550_v2/OFFLINE_RETENTION/REVIEW.md`是可审阅方案，
READY.json链接精确清单，BLOCKED.json保留拒绝证据；等待用户批准，不能拆分或绕过拒绝。

不受阻的缓存清理已完成：重新核验服务器和本地hash/大小/身份后，仅释放16份重复/tmp传输包，
6,630,480,093字节，free61,298,081,792→67,928,477,696；原始轨迹/checkpoint删除0。
收据TRANSFER_CACHE_RELEASE_20261016T1555.json保存逐文件恢复地址；T1252缓存实际映射T1116归档，
查证后才释放。后续经批准的离线保留/恢复须先重新下载相应已移除缓存，不能跳过归档核验。

源码、测试、盘点/计划/拒绝/缓存收据和导纳ep11/12原始回合、cp16500/17875及截至17875的5500条连续有限更新
已核验到独立目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-storage-delivery-20261016T1600/evidence.tar.gz`，
548,097,492字节，SHA256 `4c5c1cdcd3d3232ac2017ff9e9fcc57432f65e1071e08f74d3980e42f9836d0a`，
本地/暂存/最终一致；逐回合reward和、checkpoint成员hash已验证。服务器仅文件/hash。
cp19250及其后新产物仍仅本地、待下一安全边界归档。已准备Direct正则化pair和阻抗occupancy pair均未派发；
继续现有导纳→VMC，四族阶段闭合并满足资源准入后才开展后续登记对照。预检不代表在线改善或收敛。

## 2026-10-16 23:40 CST 物块进度奖励有限对照准备

原stage02_v2导纳2467890持续推进，收工16,250步/11,251更新；ep9/10完整physical_valid、Task/Strict0/2，
return−25.493493/−25.264967，cp13750/15125和2750连续有限更新/逐回合回报和核验。
新`rl_goal_impedance_occupancy_20261016`登记fresh control/weight4物块进度成本两组，各44k、1M优化日程；
同seed/物理/输入/滤波/执行器，原四族训练和已准备Direct alpha0/1对照不变。登记
`b3cb37f91cb713f4878fc7a0e79ae506a846feef159236baa72dd74f557caf1d`。
96项测试与真实CUDA预检通过：同初始化、1375训练样本奖励/归一化统计独立核验、末25步回报求和、各一次丢弃更新有限，
源cp23375不变、仿真/保存模型0，峰1,516,871,680字节/2GiB、OOM/max/swap0。
隔离trainer准入通过，实际提前launch因四族未闭合拒绝、无LAUNCH/execution；仅准备，未证实online收益。
报告/screen识别新reward并拒绝混用，双组不等于四族；采用候选前仍须完成明确的选型接续兼容核验。
证据及前2导纳原始回合/cp已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-occupancy-ready-20261016T1540/evidence.tar.gz`，
547,562,429字节，SHA `766cab7086f18f6305632f316daa1f06a0695491438d01b0d7ccdd25f62a2fc7`，本地/暂存/最终一致。
64回合估计需20.10GB且不含增长/缓存，当前尚不足以在50GiB保护区之上完整存放；继续核验归档/离线保留再派发。
重新核验远端后释放3份重复tar缓存2,164,485,381字节，free59.79→61.95GB；原始轨迹/cp零删除，可下载服务器包恢复缓存。
当前导纳峰3GiB/max1、OOM/swap0、GPU38°C。按sii-research-sync核对两分支main a63ff29/baseline f6e8f8c及收工AGENTS。
Goal active，四方法未证实收敛、未最终acceptance；服务器仅归档，所有失败保留。

## 2026-10-16 23:25 CST 阻抗阶段结束、导纳接续及reward诊断

stage02_v2阻抗23,375步/18,376更新，本段11,000连续有限更新、8完整physical_valid回合、Task/Strict0/8；
末return−25.320493、temperature .001968527。协调器自动接续导纳2467890，观测12,500步/7,501更新；VMC待运行。
阻抗3GiB峰/max3175但OOM/swap0；导纳约2.55GB峰、OOM/swap0，GPU38°C。主机已有swap占用与worker区分。
cp19250只读credit与5回合分解显示动作有变化、无能量限幅触发，末段位置误差约12.7–15.8mm，任务仍失败。
99个路径点切换中97个局部误差成本上跳，收紧误差尺度可能加重推进惩罚；因此未采用该直觉候选。
新增未部署物块进度occupancy成本helper和测试，93项Goal测试通过；shadow显示无局部参考切换项，
但这只是不同reward的固定轨迹重算，不是新策略改善；未接入trainer/登记在线处理或重标历史replay。
phi不保证成功时为1，需独立有限配对及奖励一致的训练历史。既有Direct actor正则化pair仍待四族阶段结束。
4份诊断/源码与阻抗cp17875–22000和原始回合已核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-payload-diagnosis-20261016T1520/evidence.tar.gz`，
1,088,411,543字节，SHA `dc7f72746fd2c72f8371dade4b5292b0fe9586846d9a09ee64f365a8e3e8fa31`。
最后cp23375/回合及完整日志补包267,249,973字节，SHA
`0d6c9510a533779f87676215e7079e0c92d450b27f879ec69327cd095c043f86`，已核验同服务器runs/main下
`rl-goal-impedance-stage02-close-20261016T1525/evidence.tar.gz`，本地/暂存/最终一致。
实时查询/fetch/read main fe07aa9/baseline f6e8f8c，收工重读AGENTS；本机计算、服务器仅文件/hash，free约61GB。
收工导纳13,250步/8,251更新、峰2.65GB、max/OOM/swap0，free60.999GB。
Goal active，未证实任何方法收敛、未最终验收，所有失败保留。详见RL_GOAL_PROGRESS_20261016.md本次条目。

## 2026-10-16 23:00 CST 正则化分支接续与失败统计保持

原阻抗worker2455377未重启，归档快照17,000步/12,001更新，收工18,250步/13,251更新。
新增4完整55秒回合、physical_valid4/4、Task/Strict0/4；前三回合/cp13750/15125/16500及4125连续有限更新已核验归档。
补齐已完成正则化pair→显式选型→四族接续→后续普通阶段入口，保留各方法实际参数快照/optimizer/replay，
不重复迁移；分支前失败另存源收据，处理后固定配置窗口不混用旧回报，短失败和在途回合仍明确计数。
90项Goal测试通过，跨阶段测试为合成闭合收据；真实pair仍未开始，未选赢家、未修改任何活动source。
同reward配对报告要求完整reward/prior/config/恢复来源相符；只有等身份/等曝光的完整回合作比较。
证据服务器目录`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-regularized-lineage-20261016T1455/`，
evidence.tar.gz SHA `1553ff87d7c62ad6f5c0e18e6b95eb905504debb36b9c1ebcdb7019602182122`（808,823,865字节），
最终代码source_final.tar.gz SHA `d31acdcb7af0d0e0d53fa381b68b9288cf1cbad34939d8a95fc8333efa1bc98f`（21,964字节），本地/远端一致。
核验远端后移除T1415/T1440两份重复传输缓存2,479,027,859字节，可从服务器恢复；原始回合/checkpoint零删除。
free升至63.66GB；阻抗峰3GiB/max287、OOM/swap0。开工main e19feda/baseline f6e8f8c已查询/fetch/read，收工重读AGENTS。
Goal active，继续四族队列及后续在线验证，所有方法未证实收敛，未最终acceptance。

## 2026-10-16 22:40 CST Direct闭合与actor正则化配对接续预检

stage02_v2 Direct完成有限段21,262步/16,263更新，新增10回合=7完整+3穿透短终止；
physical_valid6/10、Task/Strict0/10，全部10,269新增更新连续有限、reward和/cp hash核验。
自动接续阻抗2455377，观测14,000步/9,001更新，首个新完整回合return−25.729180仍失败。
新online pair从Direct最终cp21262共享恢复，alpha0/1各新增11k；仅迁移原生actor_bc_alpha，
optimizer/replay/normalizer/RNG和冻结物理/reward/输入保留。86项Goal测试、隔离导入和两组trainer准入通过。
两组真实CUDA预检验证完整网络/优化器hash及统计/RNG精确恢复，各一次丢弃更新有限；
处理组额外保存/重载验证通过，无仿真/部署。前置四族尚未闭合，实际launch被拒且未创建派发记录。
登记`1be1942c09c6f03b5b361b0c694e9449331edd36aa0febd451e6055601a87f45`；
运行根`outputs/rl_goal_actor_regularization_online_20261016`，只完成预检，不证明正则化在线收益。
Direct峰值3GiB/max事件1330但OOM/swap0；两组预检峰约1.33/1.56GB，roundtrip1.63GB，均OOM0。
尾6Direct原始回合/cp及pair证据本地包1,611,100,590字节，SHA
`da29a35e1835a90b48e7a684bb09f79da6e750a413a6844b55f4fc799533b806`，本地/服务器hash一致，已核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-bc-online-ready-20261016T1440/evidence.tar.gz`。
服务器仅存储/hash；本轮未删除数据。收工阻抗14,750步/9,751更新，OOM/swap0，仍正常运行。
main610cdbc/baseline f6e8f8c实时查询/fetch/read、收工重读AGENTS；四族未收敛，Goal active、未最终acceptance。

## 2026-10-16 22:15 CST Direct只读信用诊断与动作正则化探针

stage02_v2原训练进程持续16250步/11251更新；新增5闭合、3完整、physical_valid2/5、Task/Strict0/5。
前4回合/cp11333/11446/12821/14196和3203连续更新/回报和核验，第5回合/cp15571仅本地待同步。
cp12821较早250末端窗口absTD .005644但当前动作Q高.681024，最新25末端absTD2.456717；
clip概率质量均值.0000248693，支持继续调查动作偏移，不证明真实Q或实现bug。
新增同cp/同批次alpha0/1各256丢弃更新探针，使用原生SimbaV2 actor_bc_alpha，仅内存修改、无仿真/模型保存。
动作历史MSE .557015→.230609，饱和4.8131%→.1116%，只是训练replay诊断；未部署处理/未证明任务收益。
81项Goal测试通过；探针峰值约1.32GB/2GiB、主训练峰2.786GB/3GiB，OOM/swap0。
诊断/探针/前4原始回合及cp已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-credit-regularization-20261016T1415/evidence.tar.gz`，
867,927,269字节，SHA256 `a2af18129ff12927befd61ee26f0f48c07ddd985051271d2175f2ad3f92dd2e8`。
按sii-research-sync读取两分支与AGENTS，保留失败和活动快照；Goal active，无收敛或最终验收结论。

## 2026-10-16 22:05 CST Direct配对闭合与四方法接续修复

完整Direct control/tracking均0/8；tracking11000步/6001更新、8完整physical_valid7/8，
control10993步/7完整+1短失败。3个完整学习配对RMSE中位差+241.535mm，额外tracking权重未证明收益。
选Direct fresh-n25 control cp10993和原GPU验证三参数cp12375，各新增11k，不重置学习。
第一次selected stage在派发前缺pilot依赖失败，无trainer输出，完整保留；修复快照依赖及预检checkout回退，
2回归先失败后通过，全部79项Goal测试通过。独立v2快照隔离核验与四族真实恢复预检通过。
当前`rl_goal_selected_20261016_stage02_v2`，协调器2447861、Direct2447875，已真实恢复推进。
归档快照11333/6334，随后前2接续回合13.60/4.52秒穿透终止、Task/Strict均false；cp11333/11446仅本地待归档。
OOM0/swap0，原3GiB/单路资源和冻结接口不变，50GiB磁盘保护保持；短失败增加cp开销，需跟进归档。
服务器已核验两包（主机arm1@192.168.31.70，根`/home/arm1/sii_shared/SII_compliance/runs/main/`）：
`rl-goal-direct-pair-selected-20261016T1350/evidence.tar.gz`，1,014,664,550字节，
SHA256 `4926680f57691f57adb2845fcb33882f8dd0f9e0a2cd5648b1333ecbb4cb64c2`；
`rl-goal-selected-snapshot-fix-20261016T1400/evidence.tar.gz`，3,259,135字节，
SHA256 `c471f8b7da9a223097010736e7db974ee2dd2d59225175ad3610f923d778d0df`。
首包重复本地tar已移除，原始数据/cp保留，服务器可恢复；修复按快照内容hash标识。
按sii-research-sync核对两分支并保留失败；Goal active，工作流恢复不等于策略收敛，无最终验收。

## 2026-10-16 21:35 CST 逐方法接续实现与Direct tracking学习

tracking原worker7000步/2001更新，5完整Task/Strict0/5；cp2750/4125/5500及501条连续有限更新核验。
首全学习配对RMSE+241.535mm、峰矩+10.129753Nm，仍失败，不能声称加tracking权重已修复。
新增显式四族来源选择接续，保留各自cp/奖励/optimizer/replay/RNG，拒绝未闭合来源/跨族/变更冻结源；
下一普通stage沿新末cp接续。收敛统计沿真实分支保留失败、不混不同奖励历史，原门槛不变。
78项Goal测试通过，真实GPU/阻抗/Direct冻结源兼容；Direct running被正确拒绝，尚未实际选择或派发新stage。
学习轨迹/cp、兼容证据和候选实现已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learning-selection-20261016T1335/evidence.tar.gz`，
648,113,768字节，SHA256 `9c2e566639765d54913205185058758431faaa1a450ced8536878259fef3d8d6`。
peak3GiB/max512、OOM0/swap0；继续完整Direct对照，随后按证据/存储预算接续。Goal active，未收敛/未最终验收。

## 2026-10-16 21:15 CST Direct末回合安全失败保全，tracking自动接续

Direct control实际10993步/5994连续有限更新，7完整55秒+1短回合，Task/Strict0/8；
末回合54.72秒穿透3.930900mm中止、return−41.679094，不能写成8完整或已收敛。
原协调器自动启动tracking worker2432993，快照2250步/0更新；首1375步实际额外奖励−.388026116762，
非reward replay数组和初始模型/obs_norm均与control一致，只证明接入、不证明有效学习。
已完成阻抗16失败回合64个大型文件离线保留，回收2,294,939,982字节；服务器原件保留、144cp文件hash不变，
离线后完整配对报告相同。恢复清单/日志/RESTORE.md保存并归档，最终审计前须恢复所需原件。
control末4回合/cp含失败、tracking首回合/cp、学习/奖励核验和离线收据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-control-close-retention-20261016T1310/evidence.tar.gz`，
1,198,940,149字节，SHA256 `4d38896ac3492a6ddbf0993dab9482fd30172a08e21cf2b954afcc83297677eb`。
本机计算、服务器仅存储/hash。继续完整tracking对照；后续需同时安排checkpoint存储和精确接续，
不能在约19GB安全余量内直接派四族44k（当前体积估算已约39GB）。Goal active，四类未收敛/未最终验收。

## 2026-10-16 20:55 CST Direct真实更新与原始归档恢复

Direct原worker归档快照7000步/2001更新，5完整55秒physical_valid5/5、Task/Strict0/5。
cp5500有501条连续有限更新，actor/critic hash改变；cp2750/4125/5500及5500条训练记录核验通过。
新增已闭合训练回合四类大文件离线/恢复工具，10安全测试及全部69项Goal测试通过。
已完成阻抗失败回合暂移4文件144,291,728字节并恢复，33回合文件与9checkpoint文件hash保持；
最终零离线文件，未删当前Direct数据，尚未批量执行长期保留。内存peak3GiB/max383，OOM0/swap0。
新轨迹/cp、工具/测试与实测收据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-learning-offline-20261016T1255/evidence.tar.gz`，
647,988,847字节，SHA256 `7d96b43f7bc0b9edd606baef6d4297f1e7a5deec30872f9f871a850f7458adea`。
第5回合/cp6875仍本地待归档；继续Direct完整对照及后续较长训练。Goal active，四族均无收敛结论，未最终验收。

## 2026-10-16 20:40 CST Direct热身与有限接续预算

Direct原进程3250步/0更新，两个完整55秒Task/Strict0/2、physical_valid2/2；5000热身尚未结束。
首回合/cp1375核验通过。后续prepare-next新增显式22k/33k/44k预算能力，保留四族各自cp、
1M上限和资源保护，59项Goal测试通过；新长阶段未派发，活动Direct快照未改。
14个本地/远端重新核验的重复/tmp传输包已移除，释放5,461,537,291字节，服务器可完整恢复；
原始实验/轨迹/cp/失败不删，长期存储仍需继续处理。
首回合、缓存回收与代码/测试证据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-first-storage-20261016T1240/evidence.tar.gz`，
189,850,878字节，SHA256 `7c74a262eb65e4121a5ab0b5b4fcc0e663dd3af71d1e2689f858d7914b29b6ad`。
Goal active，继续Direct对照；四方法未证明收敛或最终验收。

## 2026-10-16 20:28 CST 阻抗对照结束，Direct v2接续

阻抗control/tracking各11000步/6001更新、8完整55秒、physical_valid8/8、Task/Strict0/8。
4个全学习配对的RMSE中位差−.100881mm，但放置误差+2.718305mm，峰矩/峰速/穿透略增；
提高跟踪权重未证明有效修复，有限pilot不是收敛。最终checkpoint/日志核验通过，失败全部保留。
原服务正常退出、全局锁释放后启动Direct v2，control PID2424017已750步/0更新热身，
from scratch、n25/UTD1/CUDA0、各11k预算，后接weight4处理组；没有重复仿真。
最终两回合/cp、完整对照及Direct启动证据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-pair-close-direct-launch-20261016T1226/evidence.tar.gz`，
540,752,690字节，SHA256 `77e18a30d230fd041a5042cc1165e996c6d3abf0b8567876ee30fa2f9d2ab436`。
Goal active，继续Direct及后续四方法训练；未最终验收。

## 2026-10-16 20:15 CST 两个全学习配对完成、仍未解卡

tracking原进程9000步/4001更新，6完整55秒Task/Strict0/6、physical_valid6/6。
cp6875/8250及3251条连续有限更新核验通过。两全学习配对的RMSE中位差−.100881mm、
放置误差−1.274364mm，但峰矩/峰速/穿透略增，未证明有效收敛。
两回合末段carry20/28；首回合servo遥测表明名义指令非零、等效速度限幅几乎无影响，
进一步排查不能直接归因为该限幅器。未改活动源码/gate，OOM0/swap0，保留内存限制。
两原始轨迹/cp/配对/诊断已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learned-20261016T1212/evidence.tar.gz`，
534,465,416字节，SHA256 `aa19ceb33724a597a141fd8b10074635bb7da0af6d4fdfaeb0c741871188f5fb`。
Goal active，继续完整配对及Direct v2，未最终验收；详见Goal进度。

## 2026-10-16 20:05 CST tracking进入真实更新，原进程继续

tracking原trainer2413986已6500步/1501更新，四完整55秒Task/Strict0/4、physical_valid4/4。
cp5500的501条更新连续有限，actor/critic保存文件改变；cp2750/4125/5500及5500步日志核验通过。
配对报告3热身/1混合/0全学习；混合对RMSE差−0.00004432mm、放置误差+0.017674mm，
无有效改善结论。继续登记处理组，未重复启动或改活动快照；OOM/max0、swap0。
第2–4轨迹/cp、学习日志和配对/核验证据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learning-20261016T1200/evidence.tar.gz`，
653,909,672字节，SHA256 `9d26c72d6443420a51ffd36aaddf1b53c621e204de963b2bafc76633b0cf09ac`。
Goal active，Direct v2待阻抗对照完成，四类均未证明收敛/最终验收；详见Goal进度。

## 2026-10-16 19:43 CST tracking首回合实际奖励/replay核验

tracking2500步/0更新热身，首完整回合return−26.51296、Task/Strict失败、physical_valid=true。
与control同条件首回合轨迹/动作及未更新网络hash完全一致；1375区间新增成本为−36*bounded_error，
合计−1.019543795131，实际checkpoint replay奖励匹配，五个非reward数组一致。
证明处理实际进入训练，不证明学习改善；当前只有1对热身、0对学习结果。原trainer健康，无OOM/swap。
首轨迹/cp/奖励分解/配对与replay核验已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-first-20261016T1142/evidence.tar.gz`，
193,524,455字节，SHA256 `ebc3e5cb64c190426c45684c0b376d5939f5588080bde14d3ae6d39d9a3b6a03`。
Goal active，继续处理组及后续Direct，尚未收敛/最终验收。

## 2026-10-16 19:35 CST 阻抗control11k闭合，tracking自动启动

control11000步/6001连续有限更新、8完整55秒，Task/Strict0/8、physical_valid8/8，未收敛。
原协调器自动启动tracking trainer2413986，实际from scratch、跟踪总weight40，现750步/0更新热身。
control最后3回合/cp8250/9625/11000及完整日志/交接/诊断已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-control-close-20261016T1132/evidence.tar.gz`，
803,419,415字节，SHA256 `16f0082c6802fa746cb1e2a83342746458166d65821add63bee32d3e8a8cf0ae`。
control共8回合及所有边界cp加此前包均已保全，服务器仅存储/hash；其最终内存max1828但OOM0/swap0。
两个全学习回合末段仍carry20/28、位置约12.6–12.8mm，继续既定权重对照，不作改善结论。
Direct v2待当前配对结束，Goal active，四类尚无收敛/最终验收证据。

## 2026-10-16 19:16 CST 阻抗8000步，配对报告与第五回合归档

原trainer2400811到8000步/3001更新，五个完整回合Task/Strict0/5、physical_valid5/5。
第五全学习回合return−25.68230、仍carry，尚未收敛。新增配对报告按条件/曝光匹配及热身阶段分组，
保留所有失败/缺失，不比较不同reward总分；6测试和真实报告通过，处理组未启动因此无配对效果结论。
工具/报告/第五轨迹/cp6875已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-pair-report-20261016T1116/evidence.tar.gz`，
266,677,855字节，SHA256 `6c16b1005c956b60e11604f29b1c7d8e9deb199096c2efa7a0fbb2709c193093`。
内存包含约1.46GB文件缓存，随后3GiB触顶回收max85、OOM0/swap0，仍真实推进；继续跟踪压力。
Goal active，未改活动训练或冻结接口，未最终验收。

## 2026-10-16 19:07 CST 阻抗热身转学习已核验

原trainer2400811到6000步/1001更新；cp5500的501条真实更新连续且有限、actor/critic文件hash改变，
cp4125/5500源文件及归档成员hash通过。第四完整回合return−24.997562，四回合Task/Strict0/4、
physical_valid4/4，无收敛结论。OOM/max0、swap0，仍单模拟器/3GiB/UTD1/CUDA0。
第三/第四轨迹与两个checkpoint、截至5500步日志和核验源码已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-learning-20261016T1105/evidence.tar.gz`，
459,990,965字节，SHA256 `c7b7c8a674282783bc8c056ebfdf69d2dfad617768efd949cd77ed32938c3d60`。
Goal active；继续阻抗control→tracking，Direct v2后续接续，最终acceptance仍未运行。

## 2026-10-16 18:58 CST 阻抗control三个热身回合闭合

Goal active，原trainer2400811持续4125步/0更新（5000步热身），三个55秒回合
physical_valid3/3、Task/Strict0/3，return−25.49341/−26.06712/−25.07228。
OOM/max0、swap0；第四回合已启动，未重复派发或改活动源码。下一核查5000真实更新及5500checkpoint。
第二回合/cp2750核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-warmup-20261016T1058/evidence.tar.gz`，
193,890,501字节，SHA256 `89398d832ac2abe46b389832768c8ba648fc8187f322fc25c1d74c434c8868f0`。
归档首版误处理在途行的失败及修复记录均保留，训练未受影响；第三回合仍本地待同步。
阻抗处理组/Direct v2尚未启动；当前无收敛/最终验收结论，详见Goal进度。

## 2026-10-16 18:50 CST 修复Direct GPU准备依赖遗漏，阻抗热身继续

旧Direct快照转GPU只刷新部分模块，实测入口ImportError；修复为配套刷新五模块，保留原失败目录。
回归先复现失败，修复后52项Goal测试通过。Direct新v2目录实际CUDA预检通过、OOM0，未启动仿真。
原阻抗trainer2400811继续2250步/0更新，首1375步完整热身Task/Strict失败、physical_valid=true，
return−25.49341，cp核验通过；同seed历史CPU热身两轨迹文件hash一致，不能据此声称学习改善。
首比较对匹配NaN误判的失败也保留。修复/预检/失败/首回合与checkpoint已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-preflight-fix-20261016T1048/evidence.tar.gz`，
SHA256 `86cf7d09e6693291a4a251bc3fee4833621b253f5006a0f909ed583dae9ec421`。Goal active，尚未收敛/最终验收。

## 2026-10-16 18:40 CST 四族GPU完整验证闭合，阻抗奖励对照已开训

四族各新增1375步/1375更新、完整55秒，checkpoint/奖励/资源检查通过，OOM0/swap0。
四回合Task/Strict均失败；n25谱系各9回合仍全失败，未收敛。导纳/VMC原始数据与四族收尾归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-close-20261016T1035/evidence.tar.gz`，
SHA256 `1940f7934c88cc047e72d031ce7c369a0c2ebccd945d8d0abe81ad924f9642d8`，前两族引用原独立包。
阻抗GPU新配对已prepare/preflight/launch：跟踪权重4对40，两fresh同seed组各11k、串行/3GiB/swap0，
冻结物理/gate等不改；control trainer2400811已有250交互/0更新（5000热身），tracking仍排队。
源码/登记/预检/启动快照已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-gpu-launch-20261016T1038/evidence.tar.gz`，
SHA256 `92303c15324ca854e402f2fa1dc083d2d5ad5bf549dad9a8b8d764d3da8b092a`。Goal active，无奖励改善/收敛或最终验收声明。

## 2026-10-16 18:25 CST GPU前两族完整回合已归档，导纳在途

Direct62906/96564、阻抗12375/7376，各新增1375步/1375更新，两完整55秒回合Task/Strict均false；
Direct physical_valid=false、阻抗true。checkpoint/更新序列/reward重算通过，峰值约2.31GB、OOM0/swap0。
阻抗末10秒仍cursor20/28、误差12.599–13.074mm，支持后续已登记跟踪权重对照，未证明根因或收敛。
两完整轨迹/checkpoint/日志及诊断已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-first-pair-20261016T1022/evidence.tar.gz`，
SHA256 `80052f2894e1ed09256961858a2a63c04ab266241625f1ed92b8925dd90d657e`。
导纳原PID2396091已11472/6473，VMC排队。Goal active；四族GPU循环完成后先运行阻抗奖励配对，未最终验收。

## 2026-10-16 18:10 CST 四族首段结束，GPU实际接续训练

Stage01四族各8完整回合Task/Strict0/8；Direct61531/95189，另三族11000/6001（steps/updates）。
VMC均值−25.261000130/std .067965733，physical_valid8/8；失败平台不算收敛，Goal active。
四族最终checkpoint及VMC末两原始回合/奖励/日志已核验归档至服务器runs/main/
`rl-goal-stage01-close-20261016T1002/evidence.tar.gz`（完整主机根同下），SHA256
`e8274358f90e0bfc895d7cb41e5fb2be331a76516937d79b623bd590e66a0642`。
新GPU阶段各1375步，四族各一次CUDA恢复预检均通过；10:08Z实际启动，Direct由61531推进至
61912步、95570更新（新增381/381），OOM0/swap0，首回合在途。保持单模拟器/3GiB/冻结物理等，
不是GPU完整回合验证已通过。源码/登记/预检/真实启动收据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-launch-20261016T1010/evidence.tar.gz`，
SHA256 `15e0f26aea078cb9bff45175d0953ab0f6cfee6d55a800bb69e583dcae11cc1f`。后续完整循环通过后运行奖励对照，未最终验收。
18:13复查Direct GPU首个55秒完整回合结束62906/96564，cp九文件hash通过；return−38.73316，
Task/Strict与physical_valid均false，保留失败。峰值2,306,428,928字节、OOM0/swap0。
协调器已自动接续阻抗；Direct新轨迹/checkpoint暂仅本地待后续归档，不冒充已进入启动包。

## 2026-10-16 17:40 CST VMC六完整回合，学习更新继续

VMC原PID2375301推进至8500步/3501更新，第7回合在途；6完整55秒physical_valid6/6、
Task/Strict0/6，第6return−25.157868312，末10秒cursor18→20，仍未完成任务或收敛。
cp8250与奖励重算通过，OOM0/swap0。原始回合/checkpoint/优化器及资源收据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-episode6-20261016T0940/evidence.tar.gz`，
SHA256 `199cc0cb0b465e947f566e398a227782e683dc2eaae561863b9adc05ef0be312`。Goal active，冻结设置不改，后续GPU验证与奖励对照不变。

## 2026-10-16 17:30 CST 纠正零路点就绪计数的含义，VMC五回合仍未成功

VMC7250步/2251更新，5完整55秒physical_valid5/5、Task/Strict0/5，第5return−25.33003。
规划器先换目标再记观测，0/250位置就绪不能单独证明停滞；只读诊断新增cursor推进计数，5测试通过。
复核21回合：阻抗8/8末窗cursor20不变，导纳3/8末窗仍推进，VMC5/5末窗推进1–2个路点。
失败标签不变、不推断因果改善；冻结环境/gate不改。第5回合/cp6875及修正诊断已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-waypoint-progress-20261016T0930/evidence.tar.gz`，
SHA256 `79b7d1bacc2cb2383cc3fd5beb4ccd5dea5ded3fafb06f7ed3c2c650d13fabbf`。Goal active，VMC第6回合在途。

## 2026-10-16 17:20 CST VMC学习更新与checkpoint实际变化通过核验

VMC原PID2375301推进至6000步/1001更新，4个完整55秒回合Task/Strict0/4、physical_valid4/4，
第4 return−25.284312267。cp4125→5500中updates0→501，四类网络文件hash变化，501条更新
连续且指标有限；首次学习已落盘但尚无收敛。第5在途，OOM0/swap0，冻结源/限制不变。
第3/4回合、两checkpoint及更新/奖励/资源证据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-learning-20261016T0915/evidence.tar.gz`，
SHA256 `bce8ae27d12b34b3097b19045d61bccb73359cf8d6dfc6108832593d075b1c79`。Goal active，训练继续。

## 2026-10-16 17:05 CST 导纳critic诊断分层，VMC两完整热身回合

VMC原trainer到3500步/0更新（5000热身），两完整55秒回合Task/Strict0/2、physical_valid2/2，
return−25.24207/−25.23735；第三在途。导纳cp11000末窗口残差拆分为最新25条3.84085、
旧175条.07309，避免把仅有一次更新机会的新终端窗口当成整体拟合失败；仍无成功/收敛证据。
只读诊断exit0、原统计不变、checkpoint/RNG未改；VMC前两回合和cp1375/2750、诊断收据归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-credit-vmc-20261016T0900/evidence.tar.gz`，
SHA256 `45e732d9d9780e1504d679fb4141bf1272b9657c57e64e6113b903e86ae2b9d4`。Goal active，后续GPU验证/奖励对照不变。

## 2026-10-16 16:50 CST 导纳11k有限段结束，VMC真实接续

导纳11000步/6001更新、8完整55秒回合，physical_valid8/8、Task/Strict0/8，reward均值
−25.37961、std.06605，未收敛。cp11000核验通过，原协调器自动启动VMC PID2375301，
已750步/0更新、仍热身，无重复训练。末回合/最终checkpoint/完整日志与八回合诊断归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-close-20261016T0850/`，
包SHA256 `ad63cc832e472ea8aaca5f05023710262d5afecb9ee8a958ec0315776e6c8532`。
摘要脚本在归档完成后因旧记录缺resource_snapshot报错，独立服务逐成员复核归档完整；
错误sidecar保留、缺失最终导纳内存值不补造。VMC交接实测OOM0/swap0。Goal active。
16:56 CST复查VMC1500步/0更新，首完整回合return−25.242069151、Task/Strict0/1、
physical_valid1/1；第二回合在途，新数据仍在本机，热身期不判收敛。

## 2026-10-16 16:40 CST Goal磁盘保留线修复，导纳第7回合归档

导纳9701步/4702更新，7完整55秒physical_valid7/7、Task/Strict0/7；第8在途。修复trainer
每回合只查旧20GiB、遗漏Goal50GiB的问题：后续取所有登记最大值，回合边界保存后停止新派发。
49项Goal＋6项恢复测试通过，真实登记计算50GiB；当前约79.6GiB，活动冻结source保持不变。
GPU新配对准备会引入该修复；额外tracking权重说明改为真实4/36，奖励计算保持。
第7轨迹/cp9625、修复与存储盘点已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-disk-guard-20261016T0840/`，
SHA256 `0d1e3c4bcc31c7c5f191b0c83fa21053a357e222c43e620e6ddc31dc02626eaf`。未删原始文件；
四百万交互轨迹空间外推407–472GB，后续仍需归档/离线保留。Goal active，未收敛。

## 2026-10-16 16:30 CST 导纳6回合奖励/实际参数复核，训练继续

导纳快照8326步/3327更新，cp8250与第6完整55秒回合正常保存，physical_valid6/6、
Task/Strict0/6。reward均值−25.34683、标准差.03004是失败平台。六回合奖励重算一致；
末回合末10秒仍carry17/18，误差12.36–18.30mm，参数变化且energy_scale1，尚无动作不应用证据。
不同condition与25Hz样本限制保留，不将该诊断当因果改善或最终物理审计。OOM0/swap0，
max1311回收事件未造成观察到的更新停滞；原服务继续，无重复进程，VMC排队。
第6轨迹/cp8250与六回合诊断归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-learning-20261016T0830/`，
SHA256 `a83b4c807756c4c4812b7ccd227e471070324f3c38ce7c88dc777adcd0a48ea5`。Goal active。

## 2026-10-16 16:20 CST GPU配对训练准备入口已补齐，导纳第5回合保全

导纳快照7364步/2365更新，5完整55秒回合physical_valid5/5、Task/Strict0/5；第5return−25.29435。
新增从未启动CPU对照创建独立fresh GPU对照的显式入口，要求四族真实GPU全循环通过和冻结
物理/runtime匹配，原CPU目录保持，必须新的CUDA预检。49项Goal测试通过；实际调用因前序
仍在运行按预期拒绝，未建GPU目录或新模拟器。memory.events.max503、OOM0/swap0，继续更新。
第5导纳原始轨迹/cp6875与实现/测试/拒绝收据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-pair-entry-20261016T0820/`，
SHA256 `68548ebda3ad34e1c641c3fd6c9e7f9b1a84e98572dd055058910fc352d4fa56`。
Goal active，准备入口不是GPU训练验证或收敛；实际GPU全循环和奖励对照尚未派发。

## 2026-10-16 16:10 CST 末端邻近诊断与导纳梯度更新

导纳6576步/1577更新，4完整55秒回合physical_valid4/4、Task/Strict0/4；VMC排队。
只读阻抗11000/导纳5500 replay：同回合末端与早期邻居的n25奖励约−22.5对−.05，
但bootstrap mask不同、输入非精确相同，不能将奖励差当作完整目标矛盾或已证实bug。
3项测试/真实诊断通过，checkpoint未变，未改冻结输入/gate；OOM0/swap0，无重复训练。
原始第4导纳回合/cp5500和诊断已保全至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-terminal-neighbours-20261016T0810/`，
包SHA256 `19116474cc1bb4db182f5fcd829131fb68f1484d793c299194d1aa9cd5024d13`。
Goal继续；GPU完整循环预检/奖励对照尚未派发，未声称收敛或最终通过。

## 2026-10-16 16:00 CST 导纳开始梯度更新，重复传输缓存已核验清理

导纳5250步/251更新、3完整热身回合Task/Strict0/3；部分carry窗口仍跨多个路径点，不能
直接照搬阻抗固定点停滞的原因。cp2750/4125与对应原始回合已核验归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-storage-20261016T0800/`。
重新核验9个/tmp传输包与服务器最终SHA256后清理4.73GiB冗余，保留全部原始数据/checkpoint；
恢复命令与逐文件收据已归档，本地约82GiB可用。未改变训练协议或保护线，Goal继续。

## 2026-10-16 15:50 CST 阻抗新鲜配对奖励干预已准备，尚未在线训练

根据8个失败回合的弱跟踪奖励证据，实现并登记权重4→40、其余一致的阻抗fresh两臂对照，
各11k/同seed/n25/UTD1/CPU1/3GiB/swap0；43项Goal＋5项恢复测试和真实2次丢弃更新预检通过。
初始网络相等、checkpoint不变、无OOM；stage01尚未完成，实际就绪检查拒绝新派发。
导纳原训练已2750步/0更新、2完整回合Task/Strict0/2；冻结源码未改。新pilot与导纳首回合
已核验归档至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-weight-pilot-20261016T0750/`。
尚无干预效果/收敛结论，详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 15:40 CST 阻抗阶段结束但未收敛，导纳按原队列启动

阻抗11000步/6001更新、8个完整55秒回合，Task/Strict0/8、physical_valid8/8，仍停carry。
回报−25.5873±.4733的波动主要来自峰矩，不能当作成功平台。cp11000/最终轨迹与训练诊断
已核验归档至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-close-20261016T0738/`。
原协调器自动接续导纳PID2360933，已750步/0更新（热身），无OOM/swap；VMC排队。
四族训练与最终验收未完成，GPU完整循环验证尚未派发。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 15:26 CST 显式GPU接续实现并通过资源guard预检

新增四族GPU完整循环验证阶段入口：前序正常闭合后，各最多1375新交互，完成四个完整回合
且实际设备/亲和性/内存检查通过才允许常规续训。当前提前prepare被正确拒绝，没有GPU训练。
40项Goal＋5项恢复测试通过；真实CUDA guard102次丢弃更新有限、峰值1.293GB、OOM0、
checkpoint不变。原CPU阻抗9750步/4751更新、7完整回合Task/Strict0/7；第8在途。
第6/7轨迹及cp8250/9625和实现证据已核验归档至服务器独立目录
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-backend-implementation-20261016T0724/`，
534,028,451字节，SHA256 `84534fda395ebba80b0b97ec9dbfaea450f2799f2c81313974e64e03d6b60f0e`。
详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 15:10 CST 发现可用GPU更新加速，阻抗仍未过carry

同一阻抗训练已8000步/3001更新、5完整回合Task/Strict0/5；第五回合/cp6875已核验归档。
奖励分解与5500 cp只读诊断显示回报变化主要来自峰矩、末端价值拟合尚不足，不是收敛。
有限CPU/CUDA丢弃更新探针通过：修正绑核并验证实际亲和性[6]后，同batch更新CPU3.89/s、
CUDA191.41/s；优化器部分49.26倍，完整循环尚未测。初次未核验绑核的结果保留但排除比较。
无仿真/模型保存/活动环境修改；下一步登记GPU后端并验证完整循环，不修改冻结活动stage。
源码、所有探针与失败训练证据已归档核验，详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:53 CST 阻抗梯度更新启动，carry阻塞定位

阻抗5500步/501更新checkpoint已核验，继续推进至5769/770，4个完整回合Task/Strict0/4、
physical_valid4/4。闭合训练诊断显示四回合末10秒均卡carry第21/28点：位置误差未进12mm，
也未越过横向重入平面；姿态/速度满足。原生未知凸边接触持续到结束，不能把低刚度定为
唯一原因或放宽门槛。新增3项诊断测试通过，四回合/四checkpoint已完成远端大小/hash核验；详细证据、
hash与局限见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。Goal active，尚无收敛或最终验收。

## 2026-10-16 14:35 CST Direct失败证据归档齐全，阻抗继续推进

Direct阶段8回合均停approach，Task/Strict0/8；最后4回合/4 checkpoint与完整日志已归档核验，
本阶段8回合现分三包共享。最终checkpoint只读诊断显示最新回合TD残差仍大，未证明收敛。
阻抗真实3000步/0更新（热身），2完整回合physical_valid2/2但Task/Strict0/2，第三回合在途；
2750 checkpoint hash通过。新tracking对照已准备，仍等待四族阶段闭合。详见
[Goal进度](RL_GOAL_PROGRESS_20261016.md)中的服务器路径/hash与诊断局限。

## 2026-10-16 14:21 CST Direct阶段结束，阻抗已自动接续

Direct61,531步/95,189更新，本阶段8完整回合Task/Strict0/8、physical_valid3/8，最终hash通过。
原协调器自动切至impedance，真实250步/0更新（5000步热身），后两族排队；无重复训练。
密集tracking的fresh同seed两组对照已登记，各11k、总22k；前序四族全部闭合后才允许派发。
30项测试和两组真实丢弃更新预检通过（相同初始网络hash、峰值1.36GB/OOM0），源码/登记/
预检已归档。未启动新对照，未收敛/未最终验收；详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:10 CST 密集跟踪奖励组件与隔离检查完成

Direct60,090步/93,748更新，第七回合继续，已完成六回合Task/Strict0/6；其他三类排队。
新增可选有界tracking奖励（权重4）和提前失败剩余成本，旧新奖励resume及统计拼接均拒绝。
27项相关测试与trainer编译通过；五条真实历史轨迹奖励复算确认更好的跟踪获得更高候选回报。
仅验证奖励算术，未部署新训练、不声称策略改善；活动源码/物理保持，Goal继续。
源码/测试/完整输入与复算证据已核验归档，详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:01 CST 训练奖励诊断与第六回合闭合

Direct58,781步/92,439更新，6个完整回合Task/Strict0/6，58,781 checkpoint hash通过；
第7回合继续，其余三方法排队。新增奖励分解工具/3项测试，五回合完整快照通过公式/日志核验。
Task信号每1375步仅末步−20；无安全罚分的两条失败轨迹跟踪cost差异很大但折扣总回报相同。
支持下一阶段检验密集跟踪奖励，未证明唯一根因，未改变当前训练或重标最终gate。
诊断源码/完整证据已归档核验，路径/hash见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:55 CST 五个完整回合与失败产物归档

Goal active；Stage01 Direct57,750步/91,408更新，新增7219/7219，5完整回合Task/Strict0/5、
physical_valid2/5；第5回合return−35.653907、仍停approach，第6回合在途，其余三方法排队。
57,406 checkpoint hash通过，OOM0/swap0，但内存已触及硬限回收，继续观察。
episode38–40原始轨迹及三个checkpoint已核验归档，835,219,332字节；episode41之后待同步。
未收敛、未最终验收，详细hash/服务器位置见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:39 CST 收敛统计可复核，第四回合继续

Stage01 Direct optimizer已到55,804步/89,462更新，54,656 checkpoint hash通过；3完整回合
return均值−31.810846、标准差7.480807，Task/Strict0/3、physical_valid1/3，第四回合在途。
新增按精确阶段lineage统计的收敛筛选，落实原登记96回合/两个32回合窗口及联合成功要求，
保留失败/未完成，拒绝重复计数或跨reward拼接；8项测试通过，真实结果不满足收敛。
worker OOM0/swap0，其他三类未启动。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:31 CST 精确接续入口完成，第三回合继续

Stage01 Direct已到54,500步/88,158更新，保持UTD1；2个结束回合Task/Strict0/2，第三回合在途。
补齐四方法各自checkpoint的prepare-next及逐方法预检封存，避免后续阶段误从零重训。
15项测试通过；真实53,281步n25 checkpoint/replay/RNG恢复与一次丢弃更新通过（峰值1.13GB/OOM0）。
当前running阶段被正确拒绝提前接续，未建立stage02，活动冻结源码不变。其他三类排队，
其真实接续预检待checkpoint生成后执行；未收敛/未验收。入口见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:22 CST Goal训练继续，完成只读Bellman/动作诊断

同一Stage01 Direct worker已完成2个完整回合，到53,281步/86,939更新，新增2750/2750；
return−21.667945/−34.277519，Task/Strict0/2、physical_valid1/2，第三回合运行中。
固定51,906 checkpoint的训练replay诊断通过：target裁剪概率质量极小，但terminal附近
当前动作Q明显高于历史动作，新回合TD残差较大；记录为动作外推/样本学习候选线索，未断言bug。
2项数学测试通过；真实只读诊断无梯度/仿真，峰值924MB、OOM0，模型hash/RNG不变。
活动训练和冻结快照保持，其他三类排队，未收敛、未验收。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:02 CST 持续Goal接续，Stage01已启动

用户明确开启持续Goal，旧15小时截止不再作为后续工作的终止授权；旧run保持原始收据。
旧恢复结束于50,531步，本段5个完整回合Task/Strict0/5，最终checkpoint hash通过。
新`outputs/rl_goal_20261016_stage01/`已登记四方法串行、各新增最多11k、25步回报、UTD1，
Direct保留旧checkpoint及原始replay，仅作明确的信用窗口迁移。13项测试与真实checkpoint
预检通过；协调器与Direct worker已启动，其余三方法排队，未收敛、未验收。
后续优先检查该阶段execution/service；详情与完成判据见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 12:04 CST 已授权修复落地，恢复训练完成首个回合

用户明确授权后，旧v2保存卡死进程已退出，partial checkpoint保留；旧v3b两路收完在途回合，
阻抗112,750步、Direct73,365步checkpoint均校验通过，末尾历史源码变更导致的失败收据保留。
确认子进程退出才结束旧协调器。新独立service已从v4的43,656步checkpoint恢复：新增1375步/
1375更新，45,031步checkpoint hash通过，真实UTD1、3GiB硬限、swap0、OOM0，源码hash一致。
首个55秒回合return−22.1773，Task/Strict均false，尚未收敛；下一回合已运行。其余三方法
未启动，未做统一acceptance。原派发截止12:33:19 CST仍有效，结束在途回合后保存退出。

**后续监视入口改为**父目录`RECOVERY_CURRENT.json`与
`outputs/rl_tuned_20261015_v4/recovery_20261016_1140b/direct_task_safety/execution.json`，
service为`sii-rl-v4-recovery-recovery-20261016-1140b.service`；旧execution保留为历史，不得
重复启动旧协调器。详细故障、reward分项与只读critic诊断见[修复报告](RL_V4_REPAIR_20261016.md)。

## 2026-10-16 11:32 CST 修复进展

已实查v2保存卡死、v3b遗留并发和UTD失配；完善独立硬限恢复入口与每回合checkpoint，
5项回归测试通过。真实checkpoint恢复/梯度更新诊断通过（峰值约1.45GiB、OOM0），
排除该checkpoint不加载或完全不更新，但尚未证明闭环收敛。恢复登记已就绪，旧进程处理被
自动审批拒绝、未执行，仍需明确授权才能释放资源并启动恢复。
详见 [修复与验证报告](RL_V4_REPAIR_20261016.md)。

## 2026-10-16 11:06 CST 复查

v4无进程、无新增交互，日志仍47,448步/84,898更新；34已结束回合Task/Strict各0/34，
其他三方法未启动，43,656步checkpoint hash复核通过。MemAvailable约3072MiB仅等于worker
上限且无余量，旧v3b两路仍运行，本轮未恢复或验收，原截止12:33:19 CST不变。
本轮收据及资源细节见 [v4监视报告](RL_V4_MONITOR_20261016.md)。

## 2026-10-16 10:46 CST 复查

v4进程为空、无新增步数；原running收据为中断前状态。仍为47,448步持久化日志、34已结束
回合，Task/Strict各0/34，其余三方法未启动；43,656步checkpoint hash复核通过。
MemAvailable=3035MiB不足3072MiB worker预算（未加余量），本轮未派发恢复或验收。
原截止12:33:19 CST不变，旧v3b进程未干预；详见下方交接报告的本轮补充。

## 2026-10-16 10:33 CST 最新 v4 状态

Direct 至少 47,448 步，34 个已结束回合 Task/Strict 均 0/34，其余三方法未启动；没有收敛或
acceptance 结果。宿主机检查发现实际 UTD=2 与登记1不符，且没有独立3GiB/禁swap硬限。
本轮请求安全停止后整个v4进程树消失，未写出新checkpoint；保留在途失败收据，不冒充正常
回合末退出。已准备独立恢复trainer并验证UTD循环，但可用内存不足，尚未恢复。
详见 [本轮证据、修复和交接](RL_V4_MONITOR_20261016.md)。下文为历史结果，不代表当前进程状态。

最新结果以 [本周三维对比周报](BASELINE_WEEKLY_REPORT_20260923.md) 为准：已完成当前 48D 五方法配对、阻抗积分参考 K300/K900 对照及导纳参考 r2 完整回合。以下 primitive 与 RL pilot 记录保留作前期工程诊断，不与当前配对主表混合。全套检查现为 105 项通过；本轮实验已结束，无后台训练或仿真遗留。

本周先完成 impedance/admittance 的开发矩阵，再建立两类 RL baseline 的文献与本机复现入口：

1. RL 调 VMC/阻抗/导纳参数；
2. RL 直接输出柔顺 action。

当前 GitHub 主线为 `0e9142e9b6c03c22995914e9ef66226cfca27a18`。本记录只引用有 source hash、命令和结果文件的实验。

后续新增公平比较审计：[FAIR_METHOD_COMPARISON_20260923.md](FAIR_METHOD_COMPARISON_20260923.md)。历史 120 条 isolated push 不能冒充 current proposed 的正式对照：完整 provenance 缺失、旧 source/controller 标签不可靠、全部超过当前 0.2 mm 门槛。当前冻结 48D 模型来源见 [CANONICAL_MODEL_PROVENANCE_20260923.md](CANONICAL_MODEL_PROVENANCE_20260923.md)；新配对 panel 矩阵和接口限制见 [PANEL_CLASSICAL_INTEGRATION_20260923.md](PANEL_CLASSICAL_INTEGRATION_20260923.md)。

## 1. 服务器经典 baseline

服务器完成了 24 条隔离运行：

```text
controller × fixture × variant
2 × (ball, push, corner, table_corner) × 3 = 24
```

完整结果：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume/FINAL_RESULT.json
```

本机只读保存了同一汇总：

```text
outputs/server_baseline_20260923/FINAL_RESULT.json
```

固定参数开发矩阵的通过情况如下：

| 控制器 | ball | push | corner | table_corner | 总计 |
|---|---:|---:|---:|---:|---:|
| Cartesian impedance | 3/3 | 3/3 | 0/3 | 0/3 | 6/12 |
| Cartesian admittance | 2/3 | 0/3 | 0/3 | 0/3 | 2/12 |

这里的通过数已经同时满足严格的 `penetration <= 0.2 mm`、有效接触、无上游误碰和任务完成条件。完整的逐回合 penetration、端点误差、峰值外力、峰值力矩和失败原因见 [CLASSICAL_BASELINES_20260923.md](CLASSICAL_BASELINES_20260923.md)。

实现边界需要保留：impedance 使用 `J.T @ (K e + D e_dot)`，并经现有 torque feasibility/slew 栈；admittance 使用本体 joint-load 估计 wrench，积分 `M x_dd + D x_d + K x = wrench`，再输出 bounded Cartesian velocity residual。admittance 当前把虚拟 offset 用于内部弹簧反馈，但没有把 offset 变成独立的 WBC reference，因此 nominal WBC 会和虚拟位移产生竞争；这解释了 push/corner/table_corner 的失败，也是下一轮应修正的控制接口问题。

这组数据是 source primitive 的固定参数开发诊断，不是 office blind-test，也不是参数搜索后的论文最终 baseline。当前结果支持的结论是：传统 impedance 在球/棍推 primitive 上有可用工况，但在两个桌角 fixture 上没有通过完整任务 gate；admittance 的固定配置还没有通过持续推压和桌角任务。

复现命令（服务器隔离 source snapshot）：

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/source_resume
/home/arm1/vmc_mujoco_runtime/.venv/bin/python scripts/run_classical_matrix_20260923.py \
  --output /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie --workers 8
```

## 2. 2024 年以后“RL 调参数”文献

详细核验见 [RL_PARAMETER_LITERATURE_20260923.md](RL_PARAMETER_LITERATURE_20260923.md)。三篇核心文献是：

| 文献 | venue | 适合本项目的 baseline 解释 |
|---|---|---|
| Da-VIL: Adaptive Dual-Arm Manipulation with Reinforcement Learning and Variable Impedance Control | ICRA 2025，DOI `10.1109/ICRA55743.2025.11127487` | PPO 输出 6 个笛卡尔对角刚度，再由 CVXPY QP 和动力学计算关节力矩；适合映射为 RL 输出 6D VMC stiffness |
| Impedance Primitive-Augmented Hierarchical Reinforcement Learning for Sequential Tasks | ICRA 2025，DOI `10.1109/ICRA55743.2025.11128462` | 高层选择 primitive，参数策略输出阶段相关刚度/任务参数，primitive 内使用自适应刚度；适合做 phase-conditioned parameter baseline |
| Variable Impedance Control Combining Reinforcement Learning and Gaussian Process Regression | IEEE-RAS Humanoids 2024，DOI `10.1109/Humanoids58906.2024.10769856` | RL/FCEM 学 stiffness-damping，GP 建模物体重量变化，momentum observer 提供外力矩估计；公开资料不足以编造完整 obs/action，应先按 paper-spec 补齐 |

这类 baseline 的 action 不是项目的 7D action。公平实现应为：RL 使用允许的本体观测输出 `K/D` 或低维 schedule，解析 VMC/阻抗控制器将参数转换为项目统一的 7D action，再通过同一安全栈。物体姿态、质量、接触 truth、未来事件和障碍物几何必须从 blind student observation 中剔除。

## 3. 2024 年以后“RL 直接输出动作”文献

详细核验见 [RL_ACTION_LITERATURE_20260923.md](RL_ACTION_LITERATURE_20260923.md)。三篇核心文献是：

| 文献 | venue | 动作和迁移限制 |
|---|---|---|
| SERL: A Software Suite for Sample-Efficient Robotic Reinforcement Learning | ICRA 2024，DOI `10.1109/ICRA57147.2024.10610040` | RLPD/SAC 风格，7D 常见形式是 6D pose delta + gripper；可作为 SAC/RLPD-action7 的算法来源 |
| HIL-SERL: Precise and Dexterous Robotic Manipulation via Human-in-the-Loop Reinforcement Learning | Science Robotics 2025，DOI `10.1126/scirobotics.ads5033` | RLPD + demonstration/human intervention；动作为 Cartesian 6D twist/target，夹爪另有离散策略；没有真实 FR3 和纠正数据不能声称忠实复现 |
| AutoMate: Specialist and Generalist Assembly Policies over Diverse Geometries | RSS 2024，[官方论文页](https://roboticsproceedings.org/rss20/p064.html) | PPO 直接输出 6D incremental pose，底层 task-space impedance；actor 使用目标位姿，critic 使用 privileged state，必须改成 48D proprio-only 才能公平比较 |

三篇的动作语义都不同于当前 ESN 的 `[slowdown, yield_6d]`。本项目应实现 interface-matched `PPO-action7` 和 `SAC/RLPD-action7`，把原论文作为算法来源，而不是把原论文 action 维度直接塞进当前环境。

## 4. 本机 RL 工程预实验

本机使用 RTX 5080（CUDA 12.8 PyTorch，`torch 2.11.0+cu128`），运行环境为 `.venv-rl`。仓库 89 个测试仍然通过：

```bash
PYTHONPATH=code/mujoco_6d_vmc_benchmark/scripts \
  .venv-rl/bin/python -m pytest -q code/mujoco_6d_vmc_benchmark/tests
# 89 passed
```

由于本机主内存约 16 GB，训练脚本使用单进程 `DummyVecEnv`、单环境、1--3 个 CPU 核和 6 GB 内存上限。首轮并发 16 worker 曾触发系统 OOM；该故障已定位并停止并发方案。

入口脚本：[run_rl_local_pilot_20260923.py](../tools/run_rl_local_pilot_20260923.py)。它会写入 command、Git/source hash、依赖版本、normalization、checkpoint 和冻结评估；默认只用两条旧 rod development fixture 训练，另两条 fixture 做验证，不使用 office 数据。

### 4.1 PPO 调六维刚度

输出目录：

```text
outputs/rl_pilot_r2_stiffness_ppo/
```

配置：`51D proprioception -> PPO -> 6D stiffness action`，8,192 steps，单进程，约 42 s。零动作和学习策略在 4 个 legacy fixture 上均通过旧版“有效碰撞 + 抓起保持 + 配对 no-rod + 无 hard torque limit”判据：

```json
{"zero_paired_gate": [true, true, true, true],
 "learned_paired_gate": [true, true, true, true],
 "publication_ready": false}
```

这个结果只证明 RL 调参链能运行；零动作也全部通过，不能据此宣称 PPO 改善了 VMC 或优于 ESN。它还没有使用当前 canonical 48D observation、四类正式 teacher split 或 office blind test。

### 4.2 SAC 直接输出动作

输出目录：

```text
outputs/rl_pilot_r2_direct_sac/
```

配置：`32D legacy WBC state -> SAC -> 7D direct residual action`，8,192 steps，单进程，约 69 s。零动作四个 fixture 全通过，而学习策略四个 fixture 全未通过：

```json
{"zero_paired_gate": [true, true, true, true],
 "learned_paired_gate": [false, false, false, false],
 "publication_ready": false}
```

冻结评估显示 learned SAC 在这些短预算、旧 32D 环境中没有建立有效接触和任务完成行为。这是失败的工程预实验，不能解释为“RL 直接动作方法不适合本项目”；它提示后续必须改为当前 48D contract、统一 reward/gate、先用 teacher replay warm-start，再做 SAC/RLPD sweep。

## 5. 当前状态与后续执行顺序

导纳 offset 已接入 WBC 参考，且修复运动学快照时序问题；r2 在三个当前 panel 条件下完成 24 s 全程实验。阻抗已改为积分 WBC twist 的移动平衡点，K300/K900 候选均保留。两者仍未成为可靠通过完整 gate 的最终 baseline，四类 primitive 的修正版全矩阵也尚未重跑。

1. 先为所有方法补齐统一的物理子步速度/实际 actuator torque 记录，并明确状态机参考下的全程与阶段误差口径。
2. 在训练/验证条件上给 impedance/admittance 固定调参预算、验收规则和模型选择规则；冻结后评估新的共同条件，不用这三条开发结果冒充独立测试。
3. 在当前 canonical 48D observation 和 7D action contract 上实现 `PPO-action7` 与 `RL-tune-VMC`；调参方法按单独控制器家族解释。
4. 用 VMC teacher bank 初始化 prior replay，实现 `SAC/RLPD-action7`；训练和 ESN 使用同一 fixture-level split、action hold、normalization 和 gates。
5. 扩大共同物理条件和独立训练 seed，最后执行冻结配置下的 office blind test。全部失败回合保留 failure reason、penetration、contact pair、force/torque 和 trace。

当前已完成的是可复现的 baseline 起点与 RL 工程链路，不是论文最终比较矩阵。
