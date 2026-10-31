# 第94轮固定前缀与完整93终端跟踪准备

第94轮原三路正式训练和归档进程继续，没有重启或改写训练。尚未收敛。实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际查询、fetch并读取main `93de46c6b408e4e0c1f4d4dea7cf7844db44055b` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；远端无新RL变更，非RLfinal108仍0/108，不启动非RL作业。

## 固定前5000更新

沿上轮NEXT_REVIEW_NOTES规定恰取前5000，不选最优片段；三路原日志前缀逐字回读，步号连续/update_index0，所有指标有限，保存NPZ逐字段精确及math.fsum/NumPy均值一致。实际查看九栏图见 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census94_prefix_20261031_v1/PLOT_INSPECTION.json`。

| 方法 | 原抽样首1000均值 | 原抽样末1000均值 | 原抽样最大 | 条件估计最大 | actor首→末1000 |
|---|---:|---:|---:|---:|---:|
| impedance | 1.307954869 | 1.163549952 | 16.365428925 | 1.918824673 | 25.318340→25.508113 |
| admittance | 1.073907509 | 1.067582416 | 1.537096262 | 1.536394119 | -7.730148→-7.754692 |
| vmc | 0.743588471 | 0.733234469 | 1.152145267 | 1.152983785 | -10.636989→-10.603952 |


I原抽样尖峰密集但幅度逐渐缩小，16.365尖峰保留；条件估计更平滑不证明原异常解决，actor上移仍在。A/V仅此前缀较平，没有完整周期reward或稳定证据。agent_train/q_loss=conditional_terminal_q_loss；原健康比较始终使用original_sampled_q_loss。此前缀terminal_population仍2785/2784/2784，不能证明实际新terminal缓存增长。

## 固定完整93终端的94跟踪

登记 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census94_fixed93_terminal_20261031_v1/PLAN.json`，源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census94_prefix_20261031_v1/terminal94.py`、`wait_terminal94.py`，来源/28运行源码hash、父完整93checkpoint identity和原注册锁定。固定8353条（2785/2784/2784），使用 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation93_potential_ablation_20261031_v1/*_values.npz` 的 **initial_prediction**。全部五critic/原masks/all-row、old≤92/new93、原79/90/92中止与93放置失败大误差行保留；保存全部逐行预测并报告退化和最大20行。无辅助权重推广、不增加物理或optimizer更新。

实际baseline来源/全8353算术预检通过；三实际startup94 checkpoint可通过架构校验且拒绝complete=True，沿用已通过99负例和CPU严格恢复。唯一等待器PID1895688/start196656130等待原archive完整94/全部review FINISHED，再用原driver.restore_consumer严格CPU恢复完整learner/Adam/RNG；前后digest不变，所有保存预测独立标量复算。已启动等待，但**尚无完整94终端结果**，未来输出图仍需实际查看，准备检查不冒充完成科学结果。

## 当前运行与继续事项

原99身份连续180.123s/19样本稳定，保存总steps `{'impedance': 3863759, 'admittance': 3867242, 'vmc': 3868244}`，完成条件 `{'impedance': 0, 'admittance': 0, 'vmc': 0}`；三训练/90sampler/archive继续。完整94、真实新增terminal缓存与全部回放对应、全loss实际图与独立算术、93→94全90条件reward/Task/Strict/abort/标签比较仍待。首次census窗口94–96沿已登记意向，明确为94启动后完整回合返回前登记，统计绑定仍待；95/96需分别审查登记，无自动队列。

中断先保全最新94 partial权重/Adam/RNG/replay/journal，另登记census-aware恢复；不回退完整93、不重跑整轮94；MuJoCo物理state未保存。全部历史失败、Direct33原数值验收与冻结0/0、旧28不完整不变性证据及指定ESN缺失保持；最终冻结独立评估仍待，Goal active。

## GPU与保存

按用户新要求，科研全部结束后也保留独立guard；保活root `/tmp/sii_gpu_util_guard_20261031_recovery_v1`，身份见CURRENT_GUARD，不创建STOP，不是系统重启服务。窗口51样本/255.348s，最低[76, 70, 71, 71]%、低于50[0, 0, 0, 0]、末值[78, 92, 89, 71]%；含synthetic guard，不等于科学吞吐或每瞬时保证，原主机切换0%记录保留。

小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS94_PREFIX_20261031/SMALL_EVIDENCE.tar.gz`，35成员/2000452字节，SHA256 `c4e3f3cf34694414cf648cc6aa53a87df501858ae3e81721dca674d3b6471395`，逐成员和AST/JSON已核验；提交字节与发布收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS94_PREFIX_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，只原地更新254字节LATEST指针；大checkpoint/replay/raw仅共享SSD，非HDD/arm1完整备份。
