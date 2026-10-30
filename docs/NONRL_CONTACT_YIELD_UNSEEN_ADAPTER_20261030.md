# 新teacher学生闭环接续与最终评估来源适配（2026-10-30）

本轮继续修复teacher、学习与场景配对问题；不把teacher通过当作ESN通过。

## 实际状态

宿主核验三项既有用户服务均active，注册源全部一致。采集PID1827286、Invocation ec3b6f480c184966bf86c5def563210d；完整16/30均qualified，ball_06在途。10条棍推已有独立10/10证据，球完成6条，桌角待。唯一训练等待器PID1829248仍waiting_for_collection、未派发。新增固定27闭环等待器PID1838688、Invocation 6e4b70f18e2646e1b3dced9c0b0f5f9b，实际waiting_for_audited_fits、未派发。三服务MemoryMax3GiB、swap0，cgroup oom/oom_kill均0。

精确服务身份、源清单核验、资源与execution快照见[evidence](evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_DIAGNOSIS_HANDOFF_LAUNCH_20261030.json)。此快照不替代后续实时查询。

## 已启动的顺序接续

1. 30条示范全部合格且采集自然结束后，既有训练等待器独立复核、建24train/6validation数据、执行公平75fit、锁九个validation-MSE模型并审计。
2. 新等待器仅在父训练完整完成且inactive后，prepare/run/review固定27闭环：九模型×三个train00身份。不重选模型，不读取最终条件；科学失败全部保留，基础设施异常保留完整前缀和当前身份后停止。
3. 若有失败，按配对teacher轨迹、实际动作/filter回放、特征覆盖及闭环行为继续开发修复，不能隐藏失败或依据unseen调参。

固定27通过只证明三个训练身份的开发闭环。teacher曾使用开发validation rod09，六validation仅作开发选模，不称独立泛化。

## 最终108入口：已准备，未登记或启动

新增experiments/evaluate_contact_yield_unseen108_20261030.py适配新数据与九模型来源。保持原冻结12条件SHA、原make_cases、物理worker、完整回合审计、action/filter replay、聚合T_ref/SPT和独立review。原reviewer字段仍指向复用的原审计源码，adapter自身另在注册源清单绑定；这是来源适配，不是另造评价算法。

仅当九模型完整审计、固定27全部Task/Strict/机器合规及精确replay通过，才允许显式register；前置失败时不打开最终条件。当前没有最终注册目录，没有新学生或unseen成绩。执行仍须单模拟器、CPU6/单线程、3GiB/swap0，并保留失败及未完成格。

零物理控制覆盖缺行、重复行、Task/Strict/机器不合格、actor/filter replay误差、重选模/测试访问标志和隐藏失败；拒绝提前注册且零次读取sealed条件；run/review异常后恢复原checker。保存控制收据并重跑通过，三个新增入口AST检查通过。这些是入口控制，不是27或108物理成功。

最终六指标仍为Task成功率、Strict成功率、双成功条件SPT、平均峰矩、人舒适度和机器合规率。实际人体舒适通道缺失标NA，力矩代理单列。旧综合结果为历史迁移压力测试，不冒充三个新隔离场景主矩阵。

## 协作与存储

本轮宿主fetch/read main ffd928cd26d582268347ef26c61a58a3182d5a2e、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。所有新raw目前仅本地；此前raw导出被自动审查拒绝，本轮未重试或绕过，未宣称服务器新归档。无RL、服务器计算、删除或重复模拟器。Goal active，完整30/训练/闭环/最终108/六指标与媒体尚待。

## 后续：最终108有限接续已实际登记启动

新增experiments/handoff_contact_yield_final108_20261030.py，等待固定27后继的完整独立review且服务inactive。科学失败、基础设施失败、超时或STOP均不派发最终评估；全部通过才显式register/run/review新来源adapter。最多等待24h、单次执行，异常保留不重试，不按最终结果替换模型或调参。最终108中的科学失败也完整保留；完成仅标final108_verified_pending_delivery，完整图表、媒体与交付仍由Goal继续，不能自动宣称研究完成。

真实用户服务sii-contact-yield-final108-handoff-20261030.service PID1843469，waiting_for_fixed27_review/dispatch_attempted=false。完整Invocation、registration/source hash、资源及四既有服务状态见CONTACT_YIELD_FINAL_HANDOFF_LAUNCH_20261030.json。本机仍仅一个物理采集，其余三项等待。此时采集23/30（rod10、ball10、corner3），全部qualified；这是执行资格快照，前18之外仍待全量独立review。源清单均一致、OOM0/swap0、3GiB。训练仍零派发，最终条件未读。

新七种零物理生命周期控制覆盖顺序register→run→review、开发失败不派发、STOP、超时、三个阶段分别异常保留，且所有场景重复run被拒绝不改原execution。active/activating/deactivating/reloading保持等待，父failed拒绝；见CONTACT_YIELD_FINAL_HANDOFF_CONTROLS_20261030.json。无真实测试/训练成功声称。

## 全量采集与训练已实际接续

30条采集全部完成并独立review为verified_all30_qualified：rod/ball/corner各10条，没有失败。采集服务自然inactive/PID0，原训练等待器同PID1829248进入fair_training。纯teacher数据15,750帧，24train/6development-validation，每场景8/2，排除旧综合数据；SHA256 67c01021964857020a039a644a9ff6a5b67735c034d45bb7cc5c84b53cf0691b。每条原始obs/action及划分与dataset逐数组精确核验通过。

三个ESN seed的登记12候选搜索均已完成；以当前物理actor独立重放全15,750帧，和各自exported_replay完全一致，最大误差0，validation requested-action MSE独立重算约3.84549e-5、3.86894e-5、3.45983e-5；这是标准化动作离线拟合误差，不是任务/安全指标或闭环修复证明。ESN为解析ridge，不编造梯度loss曲线或reward收敛。完整数据/三ESN证据CONTACT_YIELD_ALL30_DATASET_ESN_REPLAY_20261030.json。

75fit作业中三个ESN作业完成，神经第一个rnn_scratch_s2026102801_candidate00真实训练进行中；一次快照update12072/32000，末batch loss7.72e-7、development-validation MSE5.56e-5，单个未完成候选不能代表最终比较或训练收敛。真实后续快照及服务见CONTACT_YIELD_TRAINING_STARTED_20261030.json。训练MemoryCurrent约2.17GB/3GiB，OOM0/swap0，两个闭环后继仍等待，零最终派发。不要改已绑定源码或重复运行。

Goal仍active：全部神经候选/九模型锁定与审计、固定27闭环、失败时开发修复、冻结108/六指标表与媒体尚待。新raw仅本地，前述归档权限限制未绕过。
