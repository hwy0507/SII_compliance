# 有限97与600万容量接续

**Goal active，未收敛。** 三路第97轮已从准确完整96 checkpoint启动，每路仅一轮、最多41250新增动作，30条件×55秒；不自动98/Direct34。原94–96窗口A/V失败保留。科学任务结束后GPU guard仍运行。

## 已完成诊断

完整96回放包含I2875/A2874/V2874共8623个终止样本。严格消费者建立全96参考，旧8533预测逐值复现，90个新96终端逐行绑定原transition/episode/reward/rollout；完整learner/Adam/replay/RNG及原checkpoint不变。保存数组算术独立复核并实际查看六栏图。所有五critic和原mask保留，新增终端masked SSE分别10.704156、31.639694、2.884097；全部历史失败仍在参考中。这是已见训练数据，不是独立泛化。

导纳short0600从第95轮成功变为完整55秒仍carry：carry进入时间约8.0→26.6秒，没有release，physical_valid仍true。终端step3979999，为本轮倒数第二条transition；该条在完整96下masked SSE22.091993，占新终端69.8237%。VMC同例Task仍成功，完成约29.76秒，但外穿透.207453711mm超过原.2mm，Strict失败；原terminal奖励由+25变−25。它的terminal step3975451，原loss尖峰3975483在后32更新。未保存抽样索引，时间先后不是具体抽样因果证据。

V该terminal的critic1预测−1.862406而reward−28.414473，但原mask为0；该分支的大残差保留在all5报告中，不能替代真实masked训练loss。V新增30终端all5 SSE714.804882而masked SSE2.884097；未改mask或据此声称健康。A/V行为退化、原loss尖峰和actor漂移继续保留。

## 容量与正式续训

真实完整96的旧4m/新6m/重复6m，在GPU0共9次隔离65536批次更新。全部retained设备镜像、8623终端与32分层、采样及RNG、metrics、更新后完整learner/Adam/RNG逐值相同；随后恢复全部状态，无权重保存。旧2m/4m容量标记不变，新增`replay_capacity_third`；准确去除架构标记后的完整96 replay digest绑定首次迁移。此前跨4m及满6m拒绝测试保留。

正式97协议、checkpoint、execution、startup及fullreview贯穿第三容量阶段，旧23/47历史保持，6m显式构造，禁止覆盖旧行。驱动120错误协议/父状态拒绝、3CPU完整消费者、6次隔离重复GPU更新及全state恢复通过。实际trainer仅改变预算报错轮次和两处容量元数据；原physics/MJB/gates/canonical48/actor49/critic52/filter/执行器限制/dt5e-5、reward/LR/terminal128/原mask/census/65536/UTD1不变。原96只读消费者gamma .9996错误原件保留，新97消费者核对真实.9995。

实际startup新增{'impedance': 1000, 'admittance': 1000, 'vmc': 2000}，全旧回放精确保留，新current/next52、raw/mixed action与reward重建误差0，30模型和30sampler/方法均核验。99身份连续120.204秒，steps增加{'impedance': 1067, 'admittance': 1090, 'vmc': 1063}，保存时总steps{'impedance': 3980710, 'admittance': 3984209, 'vmc': 3985143}。全8623固定96终端的97只读比较已预检、实际partial97拒绝完整检查，沿原archive截止等待；没有新增训练。完整97、真实跨4m旧行保留、终端增长、全loss和实际图仍待，不把startup当完成。

前瞻97–99窗口意向在首97派发之前登记，5%/nearzero1/5000bootstrap/seed2026102861保持，原94–96失败不替换。新窗口binder已准备，统计kernel逆向身份/文字替换后逐字节相同、错误容量及缺九组拒绝；全部九组结果仍待，97只派一轮，不自动授权98/99。Direct33原数值验收/冻结30 Task/Strict0/0、旧Direct28 memory证明缺口与恢复2已证不变；指定ESN和最终独立公平评测仍缺。

## 恢复和保存

主机`rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD根`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，Python`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。正式run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle97_20261031_v1`，源码`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census97_continuation_20261031_v1`；新终端`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census96_new_terminal_diagnosis_20261031_v1`，实际96容量GPU证据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census_capacity6m_full96_20261031_v1`。原96训练及消费者已完成，勿重启；97中断须保全最新partial，不回退96。MuJoCo物理状态未保存。

启动PID以`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle97_20261031_v1/LAUNCH.json`为准并重验/proc start ticks；archive/startup/observer有独立收据。原guard五身份保留、未创建STOP，非系统重启服务。保存窗口256个样本min[72, 67, 66, 68]%、低于50次数[0, 0, 0, 0]，末[79, 95, 89, 92]；包含synthetic guard，非科学吞吐或每瞬时保证。

本轮准备脚本输出路径断言失败一次（写源/计划前），系统Python缺numpy导致独立复核首次导入失败一次，随后使用冻结env通过；97终端消费者预检后发现旧分组截止仍94，在实际推理/等待器启动前修为≤95，原源/计划/预检保留并重做全部分组覆盖检查；原件记录，未更新正式state。开工实际查询/fetch/read main a0962d67与baseline f6e8f8c2，无子agent。

小证据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS97_CAPACITY6M_ONLINE_20261031/SMALL_EVIDENCE.tar.gz`，158成员/2192246字节，SHA256 `14b5aaa31f75db1c21f1da7874b065ba19c9211c8ea9b163386b8dfa7b8e5a3e`，所有成员逐字节验证。大型checkpoint/replay/raw仍共享SSD；HDD仅既有254字节LATEST指针，不是HDD/arm1完整备份。实际Git发布见`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS97_CAPACITY6M_ONLINE_20261031/PUBLICATION.json`。
