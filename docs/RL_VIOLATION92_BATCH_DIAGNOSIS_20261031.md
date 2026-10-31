# 第92轮冻结原生batch尖峰诊断（2026-10-31）

完整92模型冻结、每方法64个原生65536 batch、零梯度/优化器更新，阻抗两次尖峰追溯到第90轮同一安全中止终端。最大批中该行贡献85.5224%的loss。这是罕见失败终端拟合/采样集中的直接证据，不是全部历史在线尖峰的因果复现，也不是已解决或不可约表示误差的证明。Goal active，原冻结90继续，无自动93/Direct34。

## 来源与执行

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。按仓库同步skill实际query/fetch/read main `03c9f084e0c32db805feac7b00dc9655b17bc527`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，恢复后再次核验未变。源 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_batch_diagnosis_20261031_v1`，结果 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation92_frozen_batch_diagnosis_20261031_v1`。原完整92 checkpoint/hash、登记、版本、完整恢复源843项依赖绑定在PLAN；源与首次抽样起始RNG均保存。原92训练完成勿重启。

按PLAN，GPU1/2/3、CPU11/12/13、每方法1800秒上限，原生replay类/device cache/接受mask抽样/target pair及策略抽样/原投影。每批所有实际字段均与独立索引见证精确匹配，原生loss在q_optimizer.zero_grad之前捕获并停止，禁止step/target写入。每路首批重放逐位精确，完整learner/Adam/replay/RNG最终恢复、原checkpoint hash不变。保留全部192批，各65536行；零backward、optimizer update及新物理步。

后续冻结抽样没有消费原训练中actor/update使用的随机数，因此不是历史在线尖峰或下一轮训练序列重放。原FINISHED与SAVED_REVIEW中的查看待办是写入时状态；后续实际查看证据在PLOT_INSPECTION，不改旧收据。

## 全部结果

| 方法 | mean loss | min–max loss | 平均终端贡献 | 平均非终端贡献 |
|---|---:|---:|---:|---:|
| impedance | 1.446160316 | 1.040861130–7.687781334 | 0.245944478 | 1.200215829 |
| admittance | 1.120387740 | 0.899194539–1.390118361 | 0.077049916 | 1.043337833 |
| vmc | 0.753101267 | 0.511821628–1.061775208 | 0.029767811 | 0.723333456 |

独立review重新读取全部192 NPZ，核对大小/SHA、原生float32 loss与float64算术（rtol3e−6/atol1e−6）、各critic真实加权分母、terminal/nonterminal、old/new92、bit0/1分组和top20。全部10种无序target pair均出现，次数不等。实际六栏图已查看且SHA绑定。

阻抗回放index3726050（全局transition step3726051）准确绑定到原cycle90/active_long_train_0000最后一步：877动作/35.08秒，全局穿透97.912589mm、external .046985938mm、bit0、done=true。stored reward与terminal target均为−37.7925643921，原journal float64为−37.7925657369。当前五critic预测约[−3.953916,.960974,−16.629107,−7.943429,−16.582642]，mask=[1,0,1,1,1]。

全部64批只有batch21/41包含此行。两批loss7.6586174965/7.6877813339，该行按不变全批分母贡献6.5068629483/6.5747751471；其他贡献1.1517541255/1.1130059555。其余62批loss范围1.0408611298–1.4884867668。全64原批均保留，没有移除样本、改变分母或另跑排除失败的训练。两尖峰恰与pair0/1同时出现，但该terminal target等于reward、不依赖target pair，因此不能把pair相关当原因。

导纳/VMC这64批没有复现原在线大尖峰，有限未复现不等于已消失；其最大批top行未追溯到原始回合，不作来源断言。

## 科学决定与未完成

这次证据优先指向罕见失败终端的拟合和抽样集中。下一有限诊断应审完整92全部终端（包含79/90/92安全中止），量化误差集中程度并核对现有因果信息是否足够，再单独登记下一在线轮的科学决定。当前不改LR、reward、masks、terminal128、batch65536、UTD1、4m append-only历史23/47标记或网络；不导入离线拟合权重。

critic/replay52、actor49、clock49/history50/raw violation51和已学权重/Adam/RNG/双架构标记保持；canonical48、冻结physics/MJB/Task与Strict gate/filter/执行器/dt5e−5保持。原90–92阻抗/导纳reward条件失败、VMC仅reward条件通过，全三路联合loss健康收敛仍未成立。原固定87 masked SSE的VMC退化及全部critic退化保留。

Direct33原数值验收保持；冻结33全30 Task/Strict0/0、旧28缺最终内存证明和恢复2完整不变均保留，不把Task成功追加为数值收敛门槛。指定ESN仍缺，不替换他机模型。partial75、不可评74–76、安全中止79/90/92、halfstd拒绝及全部旧失败窗口/软件失败均保留。本诊断无软件失败。

## 在途运行与恢复

保存时原冻结90完成 `{'impedance': 27, 'admittance': 25, 'vmc': 25}`（各30）；原三evaluator283421/283428/283430、collector283433、postprocessor292743存活且start identity核验，最终全90/raw/88→90配对/内存不变仍待。沿原截止，不重启/延长。

原guard supervisor97370、workers97399–97402身份核验，`/tmp/sii_gpu_util_guard_20261030_v7` threshold50/target70/min duty.7继续，科研结束也保活，不是重启服务。本次104样本/523.747秒，最小[76, 67, 68, 68]%、低于50次数[0, 0, 0, 0]、末样本[80, 70, 71, 71]%。包含synthetic guard，不等于科研吞吐或每瞬时保证；历史warmup0/v6低样本保留。

共享SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_BATCH_DIAGNOSIS_20261031/SMALL_EVIDENCE.tar.gz`，148成员/1030014字节，SHA256 `e1a6d29600215a62a3cdbeaa7f711525a68affad735e14ec3bdb1e1af19617f9`，逐tar成员大小/字节和Python AST核验。192原NPZ共363248942字节位于 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation92_frozen_batch_diagnosis_20261031_v1/<method>/raw`，逐大小/hash重新核验，三份RAW_MANIFEST入Git，但raw目录不入Git或tar。大checkpoint/replay原始记录仍共享SSD。

本轮清单 `docs/evidence/RL_VIOLATION92_BATCH_DIAGNOSIS_20261031/MANIFEST.json`，index/commit核验与实际远端发布收据在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION92_BATCH_DIAGNOSIS_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原地更新现有254字节LATEST指针并回读，非HDD/arm1全备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
