# 第97轮前缀、完整比较与实际容量边界准备

**Goal active，参数RL尚未收敛。** 上一轮是真实进展：准确全96续训97及6m实际接入。本轮不重启这些作业；完成固定前5000健康检查，登记完整97后的全90比较、实际跨4m保留检查，并连续核验现有进程。

## 固定前5000

|方法|原loss首1000均值|末1000均值|前5000均值|最大|
|---|---:|---:|---:|---:|
|impedance|0.949179241|0.955691569|0.951526244|1.477962255|
|admittance|1.037516265|1.042288142|1.040172147|1.512733459|
|vmc|0.723623871|0.725730984|0.725519554|1.197426081|

固定范围在读取loss值之前确定，原5000行字节前后精确，全部metrics与NPZ逐值一致，首/末/全均值和极值用math.fsum独立复算。实际查看九栏图；三原loss和条件估计的250-update均线大体平缓，actor有小幅上移。原health口径是original_sampled_q_loss，不以conditional loss替代。完整96的V尖峰8.7554、actor漂移和全部失败保持，前缀不证明它们已解决。

前5000所有更新terminal_population与原2875/2874/2874加inclusive done计数精确；实际没有新terminal，不能证明真实增长。15个损坏日志/计数例拒绝。已锁census/trainer源顺序为add/cache同步→step→transition日志→update→optimizer日志，线上逐分层tensor未保存，不宣称观察。

## 完整比较与容量边界

已读真实全96三路×30条件的模型身份、Task/Strict/abort/阶段与reward分项/总值，全部通过。新97比较只允许显式新增第三容量阶段，其他科学字段与96相同；真实协议接受，18个物理/条件/容量/父checkpoint/估计器损坏输入拒绝。消费者等待原97 archive完整review/health/loss后比较全部90条件、保留全部标签退化，再核验每条在线terminal计数与完整6m checkpoint中的done/mask/32分层。缺完整97检查已拒绝；无未来结果、无自动98。

实际跨4m观察在每方法仍<4m时登记；每路仅一份实际>4m checkpoint快照，逐块比较完整96的所有回放数组字段，核验新增日志reward/done与原mask，边界两侧5行与原actor journal的current/next52、raw到mixed动作逐值绑定。8个覆盖旧行/新reward/done/NaN/mask/schema/shape/step损坏例拒绝。当前只是在等待真实跨界，不能用先前合成边界或full96兼容测试当作实际跨界证据。原checkpoint/source/训练不修改，零physics/optimizer。路径`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census97_capacity_boundary_20261031_v1`，沿原97预算截止；失败保留并检查原因，不重启训练。

原固定8623终端比较等待器继续，没有重复创建。原三正式、90sampler、archive、三个只读等待器和五guard共102身份连续300.281s/ 31样本保持，steps增加{'impedance': 2808, 'admittance': 2737, 'vmc': 2771}，保存总steps{'impedance': 3989731, 'admittance': 3993289, 'vmc': 3994050}。完整97、真实跨界、真实终端增长、完整loss/实际图及前瞻97–99全九组仍待；原94–96 A/V失败保留。

## Direct范围与恢复

再次读取并逐hash核验原DIRECT_STAGE_DECISION及其7项证据，Direct33已经满足原训练数值标准，保留33，不因冻结任务失败或GPU占用追加34。最新冻结33组合审查全30 Task/Strict0/0；原28最终内存不变性无法证明、全部28保存动作重放精确、新2完整state不变性已证。没有把这些局限抹去，也不把成功率事后新增为原数值收敛门槛。整体Goal仍需参数reward平稳/loss健康，以及指定ESN与最终独立公平比较。

主机`rltest-1025--a6ed2ff39b3c-cn2p6rygmr`；共享SSD根`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，Python`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。正式run`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle97_20261031_v1`，当前检查/等待源码`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census97_prefix_comparison_20261031_v1`；精确97启动和6m恢复见上一交接RL_CENSUS97_CAPACITY6M_ONLINE_20261031。中断须保全最新97 partial，不回退96；旧96已完成勿重启。MuJoCo物理状态未保存。进程按LAUNCH/PROCESS的PID与start_ticks重验，不依据旧进度重启。

## 保存

实际query/fetch/read main fd272610、baseline f6e8f8c2；无子agent。GPU保存窗口137样本最低[58, 70, 69, 71]%、低于50次数[0, 0, 0, 0]、末[90, 93, 94, 93]。含synthetic guard，非科学吞吐或每瞬时保证；科学全部结束后仍guard，非重启自启服务。

小证据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS97_PREFIX_COMPARISON_20261031/SMALL_EVIDENCE.tar.gz`，62成员/2060050字节，SHA256`9db09503b00dcdb05b31aa6c4786a3346f6dc582b3c32551e16a273ece89aba4`，逐成员字节/JSON/AST核验。大型checkpoint/replay/raw仍共享SSD，HDD仅既有254字节LATEST指针，不是HDD/arm1全备份。实际发布收据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS97_PREFIX_COMPARISON_20261031/PUBLICATION.json`。
