# 完整96与原94–96固定窗口审查

原第96轮三路训练、归档与两个比较消费者全部正常结束。**尚未收敛，Goal active**。上一轮实质完成6m GPU兼容性；本轮完成完整96、真实终端增长、原固定窗口统计及实际图审查，没有重复训练或改动原科学设置。

## 完整训练与loss

|方法|完整96步数|Task/Strict（各30）|reward均值|原loss均值|原loss最大|
|---|---:|---:|---:|---:|---:|
|impedance|3976512|18/17|-2.403063414|0.945497|1.873031|
|admittance|3980000|16/16|-5.182521772|1.060712|1.600789|
|vmc|3981000|17/16|-4.605873895|0.735567|8.755404|

每方法30个完整55秒回合/41250新transition，无中止。旧回放所有字段、历史/违规特征保留，新current/next52、raw/mixed action和原reward journal重建精确，reward最大误差0。原网络/Adam有限，完整checkpoint严格恢复；physics/MJB/Task/Strict/canonical48/actor49/critic52/filter/执行器限制/dt5e-5、reward/LR/masks/terminal128/batch65536/UTD1和4m历史23/47容量保持。该reward核验是原journal算术，不是全部原始物理子步重演。

全部123750 optimizer行与保存NPZ所有字段逐值核对，首末1000/均值/极值用math.fsum独立复算，最大20原loss记录保留。实际查看九栏loss和六栏health。I原loss均值约.945，actor上升后趋缓；A中段loss上升后回落、actor仍变；V均值约.736但末段原loss出现8.7554尖峰。具体step3975483对应条件loss.961916、terminal_population2863、sampled_terminal_rows44；原loss3.235736还出现在3975532。不能以条件估计更平滑代替原健康口径，也不能从日志推断某一被抽样transition造成峰值（未保存抽样索引）。V actor上移且末段alpha下降，entropy近目标但有波动。health4096 TD为未投影fixed-min-pair诊断，不等于真实投影/I-min/A-V-mean目标。

## 真实终端与全部条件比较

活跃前缀逐步绑定真实done累计及完成55秒回合，首次检查新增I20/A21/V20终端，真实增长少记一条会被拒。前缀字节hash再与最终日志核对；完整三路每次更新population、全部回放done、新30终端/方法、原8533 indices/masks及存档32分层均通过。最终各2875/2874/2874，总8623。在线逐分层tensor没有日志，不声称已逐值观察。

95→96全90条件模型/reward分项/Task/Strict/abort与变化rollout核验。I标签不变且平均reward+0.003167；A平均+1.686877，long0500和long0900获Task/Strict但short0600失去两者；V平均−1.742864，short0600保持Task但失去Strict。成功总数不能掩盖这些变化，完整原失败都保留。

固定全部8533旧95终端，在准确96 checkpoint下零更新/零physics，完整learner/Adam/replay/RNG不变，保存SSE标量与实际九栏图通过。原mask总SSE相对变化I−29.6328%、A−.4278%、V+3.8651%；逐样本退化1300/1563/1225。I部分critic退化，A masked critic2/3及all-row critic2/4退化，V masked critic1/3退化，虽然V每个critic的all-row SSE下降。原历史79/90/92中止及93放置失败残差仍包含；这是已见历史拟合，不是新96终端评估、独立泛化或全方法改进。

## 原94–96窗口

|方法|94/95/96 reward均值|相邻相对变化|94→96相对变化|原5%描述性检查|
|---|---|---|---:|---|
|impedance|-2.339122/-2.406230/-2.403063|2.8690%/0.1316%|2.7336%|True|
|admittance|-8.562014/-6.869399/-5.182522|19.7689%/24.5564%|39.4708%|False|
|vmc|-2.849536/-2.863010/-4.605874|0.4729%/60.8752%|61.6359%|False|

原窗口/5%/nearzero1/5000 bootstrap/seed2026102861保持；意向登记在94启动后首个完整回合之前，不改写为启动前。完整九组输入含原协议/全部30episode/全部更新/原loss/真实两图/checkpoint，实际读取九份checkpoint并核验连续父链。原绑定器、audit.py和review_saved.py未改，所有源锁保持。原始270回合标量及bootstrap区间用独立math.fsum与排序线性分位数再次核验；区间衡量条件组成敏感性，不是独立训练seed。实际查看reward_stability.png。I仅通过描述性reward稳定检查；A/V失败，有限loss及5%均不能独自建立健康收敛。原90–92和所有后续失败继续保留。

本轮两个操作错误有原件：输入map哈希检查尚未退出时过早调用binder，缺文件退出；等待map成功后原binder通过。统计第一次以相对--root启动，原binding_source绝对路径一致性检查拒绝；随后使用绝对--root运行同一源码成功，原FAILURE.json及WINDOW_RELATIVE_ROOT_FAILURE.json保留。没有改变数据、阈值或统计kernel。

## 下一步及恢复

下一步先核查新96终端残差和short0600退化，再依据准确全96父状态登记有限97：6m容量候选已完成真实全95 CPU/GPU兼容性及边界测试，尚未正式接入；仍需全96 learner/Adam/RNG/replay恢复、三容量marker贯穿协议/checkpoint/startup/fullreview，原生更新及实际跨4m保留检查。4m已不足完整97，禁止覆盖旧数据。97尚未派发，不自动98/Direct34；后续统计须单独前瞻登记，不能替换本次失败窗口。

Direct33原数值验收/冻结30条件Task/Strict0/0、旧28完整memory不变性缺口及恢复2已证保持。指定ESN仍缺，最终独立评测/公平对照和联合收敛未完成。恢复以已核验完整96为父，不能回退95；MuJoCo物理state未保存。原96完成进程勿重启，guard在科学结束后仍继续。

## 来源与保存

主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，Python `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。按sii-research-sync实际query/fetch/read main f529b4ff/baseline f6e8f8c2，无子agent。训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle96_20261031_v1`；完整归档 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle96_archive_20261031_v1`；科学汇总 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census96_completion_20261031_v1`；原固定窗口 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census94_96_reward_stability_20261031_v1`。各checkpoint SHA：

- impedance: `08b8e8d48996a8ddf80a3f7c69a8b2d496c0c078a8203944a8ff019772f98191`
- admittance: `436ba7675d4aaeb50731be5f781a4720e69383dc47da64102a70ec71c3e2dbbd`
- vmc: `1088bb9142efbdfe45ccb8389fbf0e16b79d2618b19530799c8e7df5c673575a`

GPU保存窗口348样本最低[72, 68, 67, 64]%、低于50次数[0, 0, 0, 0]，末值[78, 71, 72, 71]；含synthetic guard，不等于正式吞吐或每瞬时保证。5个guard身份仍在，非系统重启服务。

小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_COMPLETE96_WINDOW94_96_20261031/SMALL_EVIDENCE.tar.gz`，223成员/7256807字节，SHA256 `0f51fb57c0ba396a0a7bf236a271aecb424c339639daf06d5ab9470b8ad7bd71`，逐成员字节/JSON/AST核验。包含原loss数组、终端数组、五张实际图、全90摘要、原固定统计及失败原件。大型checkpoint/replay/raw仍仅共享SSD，HDD仅254字节LATEST指针，非HDD/arm1完整备份。实际发布收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_COMPLETE96_WINDOW94_96_20261031/PUBLICATION.json`。
