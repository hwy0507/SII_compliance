# 固定综合场景：用纯 MLP / RNN 替换 ESN

状态：8 模型训练、8 条完整物理回合、独立审计、两条视频和服务器 hash 核验完成。新授权来自用户
“改成 MLP 和 RNN（替换 ESN）看看效果”，不是延长上一轮已结束的四小时任务。
方案见 [预登记协议](MLP_RNN_REPLACEMENT_PROTOCOL_20261002.md)。

## 环境与模型

沿用 office-tool-contact-v5、55 秒、物理 seed 2026091751、开发 dt=1e-4。
冻结 MJB `b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1`。
几何/碰撞时序、名义规划、公共 WBC、task/strict、外穿透≤0.2mm、执行器幅值与变化率未改。
task 仍要求实际松手后的稳定放置；接近目标或三指标较小都不替代任务成功。
MLP/RNN 只替换公共 action7 柔顺 actor，保留所有方法共有的规划/WBC/限幅滤波链；
部署时没有 VMC teacher、ESN、额外恢复控制器或方法混合。

- MLP：128 个 tanh 隐藏单元，无偏置。
- RNN：128 个 Elman/tanh 单元，输入与循环权重均参与学习，无偏置；不是 GRU/LSTM。
- 原 VMC 数据只用现有 canonical48 中 39:45 的 6 个估计负载输入。
  恢复 teacher41 数据用 14:17、20:23、26:29、39:48 共 18 个既有本体/参考相对字段。
  保留 48D 接口，未使用其他字段；无接触真值、球/障碍状态、时间、阶段、视觉或距离。
- 不复制旧 ESN 的负载×context 手工特征或专用抵消结构。全部选中输入和状态为零时
  输出为零；不声称任意非零运动 context 下仍满足旧 ESN 的零负载平衡。
- 128 宽度相同不等于参数量相同：6 输入 MLP/RNN 分别 1,664 / 18,048 个可训练参数；
  18 输入分别 3,200 / 19,584。旧 ESN 还有额外 128 个非线性读出单元，不是严格参数匹配比较。

## 数据、学习与证据边界

直接复制上一轮 `esn_original_system_id_v2` 和 `esn_integral41` 的 training_data.npz，
分别 20,925 / 72,700 帧，并与原 TRAINING_COMPLETE 中的数据 hash 一致性核验。
前者含 48×350 合成步和 3×1375 真实历史步，后者含 48×1400 和 4×1375 步。
合成轨迹按 40 个训练身份 / 8 个留出身份划分；真实历史为已见开发训练历史。
这些真实 teacher 回合没有完成放置，包含显式反事实重标注，不能称“成功 teacher 数据”。
原始来源已核验保存在：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_esn_four_hour_20261002_090155/evidence/`。

两组数据各训练 MLP/RNN × seed 2026100201/2026100202，共 8 模型。
相同数据、训练身份、重要性权重、训练顺序、输入缩放与 2400 次更新；保存 schedule hash。
AdamW lr=.001、weight_decay=1e-5、梯度范数上限 1；batch 为 8 条完整 episode，按连续
64 步（2.56 秒）分块，RNN 跨块保留 detach 隐藏状态，仅 episode 边界重置。
padding 不计损失；loss=动作 MSE+.25×相邻动作增量 MSE，标签为公共 filter 后动作。
完整合成留出序列决定 checkpoint，不据物理结果挑训练权重。
所有模型依预定顺序各跑一条完整物理回合，不按结果追加搜索或删掉失败。

离线精度衡量拟合，闭环才衡量任务。两训练 seed 在一个已见场景上的结果不是跨条件泛化率。
旧 ESN 仅作历史同数据参考，其特征、结构、训练机制和更新数（2400 / 4000）不同。
RNN 隐藏状态沿用旧日志字段名 reservoir_state/reservoir_delta，但语义是可训练 RNN 状态。

## 完整结果

全部 task=false、strict=false，全部完成 55 秒，未中止或筛除物理回合。
seed1/seed2 分别为 2026100201/2026100202；末端阶段和最终物块 XY 误差一并报告，
防止把停住不动导致的较低指标当作恢复成功。

| 数据 / 模型 / seed | RMSE mm | 峰矩 Nm | 峰速 m/s | 外穿透 mm | 最终 XY 误差 mm | 最终阶段 |
|---|---:|---:|---:|---:|---:|---|
| 原 VMC / MLP / 1 | 32.457 | 38.616 | .389320 | .142642 | 132.713 | carry |
| 原 VMC / RNN / 1 | 29.388 | 39.557 | .367909 | .124445 | 134.688 | carry |
| 原 VMC / MLP / 2 | 45.663 | 38.325 | .418969 | **.205319** | 134.303 | carry |
| 原 VMC / RNN / 2 | 29.227 | 38.309 | .404788 | .196682 | 134.068 | carry |
| 恢复41 / MLP / 1 | 58.750 | 37.299 | .419984 | .188705 | 149.338 | carry |
| 恢复41 / RNN / 1 | 74.640 | 36.846 | .382280 | .118647 | 101.545 | carry |
| 恢复41 / MLP / 2 | 70.667 | 41.862 | .380940 | .123101 | 59.899 | carry |
| 恢复41 / RNN / 2 | 52.751 | 35.514 | .449740 | .189982 | 192.149 | **approach** |

原 VMC 组两 seed 的平均三指标：MLP 39.060mm / 38.470Nm / .404145m/s，
RNN 29.307mm / 38.933Nm / .386349m/s。RNN 的平均 RMSE 低约 25%，两个 seed 都约 29mm，
但都在未知凸边附近停滞，最终 XY 误差没有改善。第一 seed 的未知凸边累计接触分别
29.8166 秒（MLP）、17.8588 秒（RNN）；接触时间较短不等于已越过障碍完成放置。

恢复41 组没有一致优势：seed1 的 RNN 比 MLP 更接近目标，但 RMSE 更高；seed2 的 RNN
全程停在 approach，最大抬升仅 .0308mm，未完成抓取。此行的低峰矩/较低 RMSE 是失败轨迹
的一部分，不能当作性能提升。恢复 MLP seed2 最终 XY 误差最小（59.899mm），仍超过原目标
区域，未松手稳定放置。只有原 VMC MLP seed2 的外穿透超 .2mm，其余穿透未超限也不等于任务成功。

历史同数据 ESN 参考（不是本轮预算/结构严格匹配的重新评估）：

| 历史 ESN | RMSE mm | 峰矩 Nm | 峰速 m/s | 最终 XY 误差 mm | task/strict |
|---|---:|---:|---:|---:|---|
| 原 VMC 蒸馏 | 30.058 | 39.210 | .370185 | 136.271 | false/false |
| 恢复41 integral ESN | 76.718 | 38.129 | .398990 | 76.918 | false/false |

普通 RNN 在原 VMC 数据上的轨迹精度接近历史 ESN，并未解决 ESN 原有的越障/放置失败。
恢复数据上 MLP 与 RNN 都有明显 seed 敏感性，不能宣称替换结构已解决瓶颈，或证明任何一种
结构天然不适合。更合适的下一步是先获得通过同一固定任务的 teacher 恢复轨迹，再做共同
数据下的闭环学习；仅继续比较对失败历史的拟合损失，不能确立成功控制器。

## 离线学习与审计结果

| 数据 / seed | MLP 合成留出 MSE | RNN 合成留出 MSE | MLP 已见真实历史 MSE | RNN 已见真实历史 MSE |
|---|---:|---:|---:|---:|
| 原 VMC / 1 | .01272640 | .01024524 | .00506759 | .00179129 |
| 原 VMC / 2 | .01285691 | .01002155 | .00344971 | .00188678 |
| 恢复41 / 1 | .00588067 | .00540339 | .00154772 | .00080557 |
| 恢复41 / 2 | .00566869 | .00502494 | .00163759 | .00149069 |

RNN 四个配对的离线误差都更小，但没有产生任何任务成功，这是本轮最直接的学习/闭环差异。
全部 8 模型导出 NumPy 与训练 Torch 的最大动作差≤3.76e-7；独立公式对保存导出重放
误差为零。四个 RNN 的循环矩阵相对初始化 Frobenius 变化为 5.317、5.559、5.710、6.143，
确认训练的确更新了循环权重。四组数据、身份切分、缩放、batch 顺序和 2400 更新核验一致。
每个模型的未用字段扰动不改变输出、全零输入/零状态输出零；这不证明非零 context 或历史下稳定。

8 条动作与公共 filter 重放误差均零，4 条 RNN 隐藏状态重放误差均零。
全部 8×550,000 个物理子步三指标、8 份独立接触 sidecar、执行器幅值与 4ms 指令变化率、
源/配置/checkpoint/原始轨迹 hash 核验通过。原始 teacher trace hash 及失败标签另行复核。
最终审计 8 completed、0 pending。初次通用目录扫描把保留的预启动协调记录计作 pending，
其诊断保留在 SETUP_DISCOVERY_AUDIT.json；最终显式扫描全部 evaluations 回合，模型审计
强制匹配 8 个预登记模型，没有排除物理失败。

两条恢复41/seed1 完整三机位视频均为 1375 帧、25fps、55 秒，整段解码/hash/六帧视觉复核完成。
选择同一预先指定 seed 展示，不代表最佳模型；字幕保留 task=false/strict=false。
本机缓存为 outputs/mlp_rnn_replacement_20261002_v2；服务器核验地址见后文。

## 工程与复现

计算在 airpig，Python 3.11 / MuJoCo 3.11.0，本地单模拟器、1 线程、MemoryMax=3GiB、
MemorySwapMax=0、CPUQuota=100%。第一条 MLP 已训练后，初次独立 runtime 因没有指定
MuJoCo Menagerie 路径在物理初始化前报错，没有产生模型或物理 rollout；该记录保留于
`setup_failures/attempt1/`。随后显式传入原资产路径，复用 SHA 核验后的同一 MLP checkpoint，
未重训、未改变环境或计入额外物理样本。

每条训练保存源码 overlay、数据/配置/seed/hash、更新曲线、选中步数和逐步导出重放；
物理保存原始请求、公共 filter 输出、实际执行量、550,000 个子步指标和独立接触 sidecar。
需分别核验动作/状态重放、完整误差积分、真实 qfrc_actuator 峰值、实际末端峰速、外穿透。
指令力矩变化率按冻结 4ms servo 更新计算，不能除以 100µs 的零阶保持物理采样间隔。

源码入口：scripts/office_mlp_rnn_20261002.py、tools/train_office_mlp_rnn_20261002.py、
tools/run_office_mlp_rnn_20261002.py、tools/audit_office_mlp_rnn_20261002.py。
现有 loader 增加新 contract；评估器仅增加 rnn 类型接收，不修改场景或 gate。
运行器固定新输出目录、独占锁、显式机器人资产路径；不会覆盖或重启稳定作业。
跨机器需将公开的完整机器人资产下载到本地缓存，路径及三机位设置见
[环境交接](OFFICE_TOOL_CONTACT_HANDOFF_20261002.md)。

## 已核验共享位置与完成状态

全部 680 项、747,693,072 字节已在 2026-10-02 13:59:53 UTC 逐项大小/SHA256 核验并发布到：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/mlp_rnn_replacement_20261002_131535/evidence/`。
archive_manifest.json SHA256：
`8a5209a9432138459175202d7a6452125bfc1c1bd7082aca0943256e5743931d`。

该 evidence 根目录下：

- `evaluations/source/` 为训练/物理使用的冻结运行源码；`postprocess_source/` 为精确审计/渲染源码。
- `train_<dataset>_<kind>_<seed>/` 为 8 模型的 checkpoint、数据来源、曲线与导出重放。
- `evaluations/<dataset>_<kind>_<seed>/` 为 8 条完整原始轨迹、模型、物理子步和失败审计。
- `data/{original,recovery41}/` 为本轮未改动的两套 teacher 数据和原始 lineage。
- `FINAL_PHYSICS_AUDIT.json`、`PAIRED_MODEL_AUDIT.json`、`POSTPROCESS_RECORD.md` 为独立核验。
- `media/recovery41_mlp_seed1/replay_threeview.mp4` 与
  `media/recovery41_rnn_seed1/replay_threeview.mp4` 为完整配对视频，旁边保存 GIF/帧图/hash/解码审计。
- `setup_failures/attempt1/` 保留初次资产路径错误和原始执行记录。

小型收据和模型结果同步在本仓库 `docs/evidence/mlp_rnn_replacement_20261002/`。
Git 发布源码另外按本次完整 commit SHA 归档服务器 `/home/arm1/sii_shared/SII_compliance/source/`；
实验执行源以本轮 overlay hash 为准，不把 base commit 冒充干净工作区。
开工 main 为 `14820fac7141fa8779aa56b5ae0ba595ee2ee0a5`，baseline 为
`133a0b4306f70dd703629bf1227961899d6abcfd`。收工 main 未前进，baseline 已更新到
`d00b995711c68a2e42a2ffd4ec2813758849aff3`，新增历史 ESN/RL 三指标复算报告，已读；
没有合并 baseline 或接入其独立 WBC/场景。

已完成本轮 8 模型比较及证据共享，无运行中训练/仿真。未完成稳定放置/strict、成功 teacher
数据、正式 dt=5e-5 与跨条件泛化；不据本轮开发失败声称某一网络结构已被穷尽。
