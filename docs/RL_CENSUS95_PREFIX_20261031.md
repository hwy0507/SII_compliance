# 第95轮前缀审查与全部94终端比较准备

第95轮原三路训练、90sampler和归档器继续运行；本轮零新增科学训练派发、零物理或optimizer诊断更新，Goal active，尚未收敛。实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际query/fetch/read main `9b5ae09c5ab827fff2e83a003e895016dad46aef`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，沿sii-research-sync保存，不改并行非RL任务。

## 固定first5000原始loss

在读取95 loss数值前锁定各方法前5000；原日志前缀逐字复制并回读一致、step连续/update_index0、所有metrics有限。保存NPZ所有字段精确，独立math.fsum首末1000/均值/极值与NumPy复算通过。原抽样、条件估计、actor三列实际九栏图已查看，收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_prefix_20261031_v1/PLOT_INSPECTION.json`。

| 方法 | 原loss首1000 | 原loss末1000 | 原loss最大 | 条件估计最大 | actor首→末1000 |
|---|---:|---:|---:|---:|---:|
| impedance | 1.068074935 | 1.055917105 | 3.434057951 | 1.683230758 | 27.089055→27.251509 |
| admittance | 1.037007323 | 1.043608578 | 1.521494985 | 1.520868421 | -7.620020→-7.598819 |
| vmc | 0.714291142 | 0.717926500 | 1.132568121 | 1.128324509 | -10.184065→-10.160839 |


I原loss均值约1.061、曲线均值较平，但反复2–2.5尖峰及3.434最大值仍在；条件最大1.683不替代原loss健康。I actor持续上移27.089→27.252；A/V此前缀原loss较平、actor小幅上移。没有完整95 episode reward或整轮健康证据。原q_loss等于conditional_terminal_q_loss；健康仍使用original_sampled_q_loss。first5000 terminal_population固定2815/2814/2814，未见新terminal，不当作实际新增cache验证。完整94原loss/actor及所有历史失败保持。

## 完整94全部终端参考

先登记 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census95_fixed94_terminal_20261031_v1/REFERENCE_PLAN.json`，固定完整94的全部8443条terminal（I2815/A2814/V2814），CPU11、1200秒有限预算、零optimizer/physics、全部五critic/原masks。从准确完整94 checkpoint严格census-aware恢复，完整learner/Adam/replay/RNG前后digest不变、无梯度，checkpoint前后hash一致。

旧8353条输入/动作/reward/masks与先前固定93终端数据精确，重新forward的full94预测与先前保存的complete94逐元素相等；新90条从94 replay全部剩余done索引取出，与原94 terminal transition的step/condition/reward和全30 episode标签/长度对应，未删行或选低误差样本。旧历史cycle/condition来源保留；新94标签由真实完整94记录绑定。新reference_npz包含全部indices/obs52/actions/rewards/masks/cycles/conditions/initial_prediction，回读逐值及独立标量SSE核验通过。

CPU计算按每方法旧93块与新94块分别forward，后续95消费者使用同样块大小。原known79/90/92安全中止与93放置失败spike3851694都保留；这是已见训练终端参考，不是独立泛化或新的95误差结果。未生成、保存或推广任何辅助拟合权重。参考 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census95_fixed94_terminal_20261031_v1/reference94`。

## 完整95比较准备与拒绝保护

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census95_fixed94_terminal_20261031_v1/PLAN.json` 绑定参考全部hash、95协议、完整94审查和29份95运行源码；消费者 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_prefix_20261031_v1/terminal95.py`、`wait_terminal95.py`。未来只接受完整95及原全review/health/loss FINISHED，严格加载全state并检验全部保留94 terminal索引/字段；输出全部五critic masked/all-row SSE、≤93旧组/新94组、已知失败、所有逐行预测及退化计数/最大20行。保存结果再独立标量复算；最终图必须实际查看。

完整baseline算术预检通过，缺完整95拒绝；三实际startup95快照通过版本校验、complete=True分别拒绝，未把partial当完成。沿用原111损坏协议/父状态拒绝及三CPU消费者证据，本轮未重复隔离更新。唯一等待器PID1270332/start197302459，截止沿原archive启动+14400秒，完成后分析预算1200秒，无自动96或Direct34。**完整95终端比较尚未运行，不能把准备通过当作95改善。**

## 继续与恢复

原99身份连续180.137s/19样本保持，steps增长{'impedance': 1581, 'admittance': 1610, 'vmc': 1426}；保存总steps{'impedance': 3903994, 'admittance': 3907483, 'vmc': 3908327}。完整95、全部新terminal缓存/回放对应、全loss实际图/独立算术及94→95全90条件比较待完成。固定94–96/5%/nearzero1/5000bootstrap/seed2026102861保持；意向原登记于94启动后首完整回合返回前，95/96需独立有限决定，不自动队列。原90–92失败、94尖峰/actor漂移、A short0200回归与unmasked退化均保持，不因前缀较平改写结论。

原physics/MJB/Task/Strict/canonical48/filter/actuator/dt5e−5、actor49/critic52、clock/history/rawbit、原LR/reward/masks/terminal128/batch65536/UTD1、census源码/marker与4m append-only/23和47标记未改。中断保全最新95 partial权重/Adam/RNG/replay/journals，另登记census-aware恢复，不回退94或重跑整轮95；MuJoCo物理state未保存。Direct33原数值验收/冻结全30 TaskStrict0/0、旧28memory invariance限制/恢复2证明、指定ESN缺失保持，最终独立对比未完成。

## GPU与保存

独立guard `/tmp/sii_gpu_util_guard_20261031_recovery_v1` 保持，科学全部结束仍运行，不创建STOP，非系统重启服务。窗口68样本/339.990s，最低[70, 70, 71, 71]%、低于50[0, 0, 0, 0]、末值[78, 71, 71, 96]%；含synthetic guard，不等于科学吞吐或每瞬时保证，旧主机切换0%记录保留。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_PREFIX_20261031/SMALL_EVIDENCE.tar.gz`，44成员/3786294字节，SHA256 `6ae2cf450658f84da24e033b13c243477cd9f7573d8325913e9089e470914904`，全部tar成员/源码AST/JSON核验。含完整first5000原始指标/保存数组/图和全部8443参考数组，全部原checkpoint/raw仅共享SSD；HDD配额满，仅254字节LATEST原地更新，非HDD/arm1全备份。Git字节与实际远端发布收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_PREFIX_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。
