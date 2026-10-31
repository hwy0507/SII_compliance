# 第100轮固定前缀与旧失败拟合诊断 — 2026-10-31

Goal active，未收敛。原第100轮三训练/90sampler/归档/固定8893终端消费者继续；本轮新增唯一全90条件与终端计数只读消费者，等待原100完整归档。无101派发。

|方法|前5000原loss均值 / 最大|快照新增步|固定旧终端SSE变化|改善 / 退化行|
|---|---:|---:|---:|---:|
|impedance|1.450083 / 21.345860|7000|-8.8514%|1448 / 1516|
|admittance|1.027932 / 1.516276|8000|-28.5559%|1991 / 972|
|vmc|0.769687 / 1.247959|8000|-0.6819%|1399 / 1565|

固定前5000原日志/全部11种metrics保存数组/独立标量复核通过，九栏实际图已看。I原loss反复约19–21尖峰，原loss首1000均值1.449878、末1000为1.348768，actor向下漂移；conditional更平滑不能替代原健康指标。A/V本段较平缓但actor变化保留，有限值不是loss健康或收敛。此处沿用历史同一first5000规则，但先前513/507/495预览已知，且登记时数据已产生，不声称生成前预登记。首次独立保存审查因尚缺实际看图收据拒绝，失败记录保留；看图写入收据后原程序通过。

当前partial100只读probe每方法取一次当时最新原子checkpoint，三个实际步数不同，明确为观察前5000尖峰后的探索性诊断。全部8893旧99终端/原mask/五critic/原预测块边界与实际replay绑定；保存数组/独立scalar SSE以及完整learner/Adam/replay/RNG不变通过，零优化器更新/物理交互，不推广权重。所有退化行保留，不能作为完整100或未见泛化结果。

I第99轮long0000穿透失败原reward-36.681350708，五critic从[5.947050094604492, 5.520218849182129, 5.1479268074035645, 5.643117427825928, 5.395536422729492]变为[4.509212017059326, 3.8357913494110107, 2.527393102645874, 4.276799201965332, 2.4343373775482178]；该原mask全1样本SSE由8909.666519降至8083.233948，仍很大。原全局穿透与外部穿透不同、原violation bit0保持；无训练抽样索引，不将其与原loss尖峰作因果绑定。其余方法/样本改善和退化均见probe原报告，不能只报总均值。

独立逐行标量审查全部8893行并保留各方法20个最大退化。I旧92 long0000原mask仅critic4为1，masked SSE9.467058→32.429589；新99失败改善同时旧失败退化。V旧11 short0600 masked SSE.224989→6.377385，原critic3 mask0保持，其预测−17.8339→−5.6605、target−28.4238只列未mask误差，不混入masked健康损失。A最大退化为旧16 short0000，.136660→.968864。不能据同条件或时间关联声称因果。

完整99→100全90条件/Task/Strict/奖励项/失败与实际终端计数对照已登记。实际完整99全部90原模型/rollout标签/奖励分解通过；18科学契约损坏与15终端计数损坏拒绝，真实partial/缺完整100不被当作完整。前5000每步终端计数核验I2965/A2964/V2964、均无新增terminal；线上逐分层tensor未日志记录，不声称观察到。本轮consumer沿原archive截止，仅等待，不重启或复制训练。

原97–99三路5%稳定失败、新100–102非重叠前瞻意向、原统计阈值及loss口径保持。Direct33原数值验收/冻结30 Task与Strict0/0、原28memory缺口/恢复2已证保持，不追加34；指定ESN、最终公平冻结比较及共同集合Tref/SPT仍待。

运行首尾101身份一致，间隔228.629s、steps增长{'impedance': 1962, 'admittance': 1974, 'vmc': 1979}，保存步数{'impedance': 4110084, 'admittance': 4113903, 'vmc': 4114901}；不是连续逐样本身份观察。GPU82样本/415.791s，最低[74, 70, 69, 71]%、低于50[0, 0, 0, 0]、末[78, 90, 90, 89]%；含保活负载，非科研吞吐或瞬时保证。科学结束仍保留`/tmp/sii_gpu_util_guard_20261031_recovery_v1`，勿创建STOP，非开机自启。

主机`rltest-1025--a6ed2ff39b3c-cn2p6rygmr`；解释器`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`，正式`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle100_20261031_v1`，本轮全90/前缀证据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census100_prefix_comparison_20261031_v1`，独立probe`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census100_prefix_terminal_probe_20261031_v1`。其三大snapshot.pt仍共享SSD，hash/实际步数见各方法REVIEW，不是完整cycle checkpoint。后续优先收完整100/new90终端与全loss/context/实际图，原终端与全90等待器勿重复派发。

小证据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS100_PREFIX_DIAGNOSIS_20261031/SMALL_EVIDENCE.tar.gz`，70成员/4317822bytes，SHA256`1dcb45caf5cd4ba644b5e26065f3b327c22f4b2ddec509cc28802946a51a5139`，逐成员回读通过。HDD配额满，仅254-byte LATEST指针；非完整HDD/arm1备份。开工main9de58411/baselinef6e8f8c2已实际query/fetch/read，发布见`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS100_PREFIX_DIAGNOSIS_20261031/PUBLICATION.json`。
