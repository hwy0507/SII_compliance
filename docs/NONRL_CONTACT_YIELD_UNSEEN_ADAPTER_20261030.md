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
