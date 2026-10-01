# 更新日志

## 2026-10-01 — temporal evidence integrity, runtime drift and synchronization repair

- 实时核对 main `ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、baseline
  `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`；授权外部网络下 GitHub/Spark 均可达，
  先前失败至少部分为沙箱限制，不能继续称服务器不可达。未合并或操作 baseline 作业。
- 最新六条回合补强审计通过：checkpoint/模型元数据绑定、actor/状态/物理数值有限、
  550000 子步与三指标复算、精确 action/reservoir replay。ESN task 0/3、MLP 3/3，
  strict 各0/3；这些是不同开发配置，不是独立泛化成功率。没有新仿真或正式评估。
- 定位运行时偏移：旧冻结 MJB 仅被现有 MuJoCo 3.11.0 加载，近期 MJB 仅被3.14.0加载。
  最新六条模型hash一致；同版本两模型618个公开字段一致。禁止把跨版本结果作仅算法
  变化排名。后续冻结评估恢复 .venv-canonical-rl/3.11.0，先记录真实执行元数据和限制。
- seed42配置恢复到62f8c65原字节；seed52另存
  `configs/esn_mlp_temporal_consistency_narrow_rep_seed52_20261001.json`，历史命令不改。
  更正窄屏/seed52的“预提交注册”、独立execution.json及历史MemoryMax过强描述。
  本轮只读审计确实使用systemd MemoryMax=3G/单线程；不能反推历史已遵守。
- 原始temporal七组成对回合、训练记录、checkpoint、MJB/XML与新旧审计已核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_integrity_20261001T1450Z/evidence.tar.gz`：
  652346695 bytes，SHA256 `0d30662ae0479b5594f8240eb4f019f7e2f9ee7b76ad974b80b8fdd6216bd460`。
  运行源码快照：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/434e46fbedfc88df11d7ff8c44f2b3d064ebd217/repository.tar`，
  SHA256 `d23b4c74298ff87b5079002f4e3bb246582f4db6447a97613eab7da1e88479b2`。
- 报告 `code/mujoco_6d_vmc_benchmark/docs/ESN_MLP_TEMPORAL_INTEGRITY_20261001.md`；
  同步联合进度、周报和小型JSON证据。已完成配置/审计/归档修复，当前无新实验运行；
  未完成同checkpoint冻结运行时复核、ESN任务/strict稳健成功及formal步长验证。

## 2026-10-01 — temporal-consistency delta=0.25 replication completed locally

- 开工再次核对缓存 `origin/main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、
  `origin/baseline=4dad929b6550b167943becd271836f0c74a21a38`；`git ls-remote` 仍因网络不可达
  失败，未把缓存当作最新远端，未修改 baseline；本机无运行中的 evaluator/training 进程。
- 预注册配置 `configs/esn_mlp_temporal_consistency_replication_20261001.json`，锁定 manifest
  SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、7/2 split、
  canonical48D/action7、宽度128、combined-v4、原 gate、禁止输入和执行器限制；只复现
  `delta_weight=0.25`，ESN seed=`2026100152`、MLP seed=`2026100153`。
- ESN task/strict=`0/1`,`0/1`，停在 lift，指标 `72.223 mm / 44.403 Nm / 0.125044 m/s /
  0.131457 mm`；MLP task/strict=`1/1`,`0/1`，完成 retreat，指标
  `46.980 mm / 45.918 Nm / 0.070165 m/s / 0.151728 mm`。两条均为开发 `dt=1e-4`、55 s、
  550000 子步，失败回合完整保留。
- 独立审计 action replay 最大误差为0、ESN reservoir replay 最大误差为0，三项物理指标
  重算一致。新增报告 `docs/ESN_MLP_TEMPORAL_CONSISTENCY_REPLICATION_20261001.md`；
  结果否定首轮 `delta=0.25` ESN 的稳健改善，formal `dt=5e-5` 继续锁定。大产物仅本地，
  arm1/GitHub 网络仍不可达。

## 2026-10-01 — temporal-consistency narrow follow-up completed locally

- 开工核对缓存 `origin/main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、
  `origin/baseline=4dad929b6550b167943becd271836f0c74a21a38`；本轮
  `git ls-remote` 因网络不可达失败，未把缓存 SHA 当作最新远端，也未修改 baseline。
- 预注册配置 `code/mujoco_6d_vmc_benchmark/configs/esn_mlp_temporal_consistency_narrow_20261001.json`
  （SHA256 `4e6fd694756b73fd964f9f1fe1ab6e71eee98f4da165c06f5f79d48851eac886`），
  固定 manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、
  7/2 split、canonical48D/action7、宽度128、combined-v4、原 gate、禁止输入和执行器限制；
  只测试 temporal delta loss `0.25/0.75`。
- 四条开发闭环均 55 s/550000 子步。ESN task/strict=`0/2`,`0/2`，MLP
  task/strict=`2/2`,`0/2`。`delta=0.25` ESN 到 retreat、RMSE `52.502 mm`、峰矩
  `45.556 Nm`、峰速 `0.117007 m/s`、穿透 `0.146245 mm`、推杆最长接触 `0.7673 s`，
  但未完成 placement；`delta=0.75` ESN 停 carry。MLP 两条均 placement 完成，一条缺
  required contact coverage，另一条球反弹失败，均 strict=false。
- 新增独立审计脚本 `tools/audit_temporal_narrow_screen_20261001.py`（SHA256
  `c9639aecdcb26cce9bcfa394e471a1e2c953224456b77ab44dfec5c582e82c3f`），四条 action replay
  最大误差为0，ESN reservoir replay 最大误差为0，物理子步指标独立重算通过。新增专题报告
  `docs/ESN_MLP_TEMPORAL_CONSISTENCY_NARROW_20261001.md`；大产物和 raw rollout 仅本地，
  arm1/GitHub 网络仍不可达，待恢复后同步。formal `dt=5e-5` 继续锁定。

## 2026-10-01 — temporal-consistency candidate seed replication completed locally

- 对首轮 `delta_weight=1.0` ESN 候选预注册第二 seed `2026100142`（MLP `2026100143`），manifest、7/2 split、canonical48D/action7、combined-v4、gate、禁止输入和执行器限制均未变。
- 复现 ESN 在 carry 停止，task/strict=false，RMSE/峰矩/峰速/穿透=`257.986 mm/44.770 Nm/0.1423 m/s/0.1774 mm`；MLP task=true、strict=false，指标=`58.208/45.395/0.1178/0.1317`。两条均完成550000子步，独立 action/储备池/物理审计通过。
- 复现否定首轮 `delta_weight=1.0` ESN 的稳健泛化结论；formal `dt=5e-5` 仍锁定。复现原始证据保留在 `outputs/esn_mlp_temporal_consistency_20261001_rep_seed42/`，大产物仅本地待同步。

## 2026-10-01 — temporal-consistency ESN/MLP screen completed locally

- 注册并完成纯 ESN/MLP action-delta loss 屏幕，候选 `delta_weight=0/0.5/1.0`。锁定 manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、7/2 identity split、canonical48D/action7、128 宽度、combined-v4、原 gate、禁止输入和执行器限制；只改变训练目标中的相邻 action 增量损失。
- 六条均为开发 `dt=1e-4`、55 s、550000 子步。ESN task/strict=`0/3`,`0/3`，最终阶段 carry/carry/load_transfer；`delta_weight=1.0` ESN 最接近完成但仍未放置。MLP 的 `0.5/1.0` 完成 task，strict=`0/3`，required contact coverage 仍失败。六条指标和 checkpoint hash 见 `docs/ESN_MLP_TEMPORAL_CONSISTENCY_SCREEN_20261001.md`。
- 六条独立 action/储备池/物理子步审计通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP 无 reservoir，均为550000物理子步。没有 strict 候选，formal `dt=5e-5` 继续锁定；结果不支持 ESN 优势。
- 新增配置、训练器和专题报告。原始 rollout、checkpoint、MJB 和失败回合仅保留本地待同步；本轮 GitHub 与 arm1 网络仍不可达。

## 2026-10-01 — low-scale ESN/MLP weight-decay screen completed locally

- 完成预注册 `weight_decay=1e-5/1e-4/1e-3` 屏幕。锁定 teacher manifest SHA256=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`，固定 7/2 identity split、canonical48D/action7、ESN/MLP 宽度128、`input_scale=0.25`、combined-v4、原 gate、纯本体输入和执行器限制；仅改变 AdamW weight decay。
- 三组均为开发 `dt=1e-4`、55 s、550000 物理子步。ESN 三组 task/strict 均为 false，全部在 lift 停滞；MLP 三组 task=true、strict=false，均因 combined contact coverage（含柱子等要求）不足而失败。ESN 的 RMSE/峰矩/峰速/外部穿透分别为 `77.173/42.170/0.1106/0.1635`、`75.485/42.723/0.1078/0.0997`、`73.093/41.235/0.1134/0.0919`；MLP 分别为 `48.442/44.781/0.0662/0.1106`、`60.176/45.249/0.1172/0.1323`、`47.831/44.426/0.0702/0.1666`。
- 六条独立审计通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP 无 reservoir，物理子步与55 s时长一致。两次仿真前 setup failure（hash变量错误、teacher root错误）保留并不计实验回合。结果不支持 ESN 优势，formal `dt=5e-5` 仍锁定。
- 新增报告 `docs/ESN_MLP_LOW_SCALE_WEIGHT_DECAY_20261001.md`、配置和训练器；修复审计器以支持无 reservoir 的 MLP。专题输出和 checkpoint 目前仅本地、待 arm1/GitHub 网络恢复，未声称远端归档；详见专题报告与联合进度。

## 2026-10-01 — low-input-scale pure ESN output-gain screen completed locally

- 在已登记的 `input_scale=0.25` ESN checkpoint 上只改变 `output_gain=0.80/0.90/0.95`；
  base SHA256=`99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`，配置
  `configs/esn_low_scale_gain_screen_20261001.json` SHA256=
  `3e7a79e32cf17ebbd7fc6a81ae9703d27f5c09ed8a69746ce82a5c5fb34fde67`。
- 固定 teacher manifest、7/2 split、canonical48D/action7、combined-v4、原 gate、禁止
  输入与执行器限制；三条均为开发 `dt=1e-4`、55 s/550000 子步，task/strict=`0/3`、`0/3`。
  `.80/.90/.95` 最终 lift/carry/lift，指标分别为
  `60.590/37.618/.1031/.1257`、`144.782/37.867/.1395/.1705`、
  `73.919/37.051/.1019/.1150`（RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm）；柱子
  覆盖全部失败。
- 三条独立审计均通过：action/reservoir replay 最大误差为0，物理子步均550000；失败 raw
  rollout、MJB、checkpoint 和审计保留在 `outputs/esn_low_scale_gain_screen_20261001_v1/`。
  结果只说明增益单因素没有恢复严格任务，不支持 ESN 泛化或相对 MLP 优势。
- formal `dt=5e-5` 继续锁定；arm1 与 GitHub 网络不可达，产物仍仅本地待同步。

## 2026-10-01 — low-input-scale pure ESN alpha screen completed locally

- 开工读取了缓存 main `ba84ed8a39ed743f603aa5d60e901bdf87090e1d` 与 baseline
  `4dad929b6550b167943becd271836f0c74a21a38` 的更新日志；本轮 fetch/SSH 在当前网络下
  失败，未把缓存冒充最新远端，也未修改 baseline。
- 在先前唯一一次 `input_scale=0.25` task-success 的 ESN checkpoint 上预注册并物化
  action-readout `alpha=0.25/0.50/0.75`。base checkpoint SHA256=
  `99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`，配置
  `configs/esn_low_scale_alpha_screen_20261001.json` SHA256=
  `2f286923b0f1a701f42e463553b2f0399fc2b3eba797321536e247a408604f79`。
- 固定 teacher manifest、7/2 identity split、canonical48D/action7、128 ESN、combined-v4
  环境、原 gate、禁止输入和执行器限制；三条均为本地 `.venv-rl`、单线程、开发
  `dt=1e-4`、55 s/550000 子步。结果 task/strict 均 `0/3`：alpha .25 停 lift，
  `.50` 停 carry，`.75` 停 lift；柱子接触覆盖均失败。三项指标分别为
  `68.485/35.127/.1010/.1423`、`138.424/39.585/.1275/.1373`、
  `59.341/37.282/.1041/.1101`（RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm）。
  `.50` 推杆最长连续接触 `.6642 s`，但没有转化为任务成功；`.75` 球反弹失败。
- 三个独立审计均通过：action replay 与 reservoir replay 最大误差均为 `0`，物理子步为
  `550000`，最长单回合 RSS 约 `667 MiB`。所有失败 raw rollout、MJB、checkpoint 和审计
  保留于 `code/mujoco_6d_vmc_benchmark/outputs/esn_low_scale_alpha_screen_20261001_v1/`。
  详细结果见 `docs/ESN_LOW_SCALE_ALPHA_SCREEN_20261001.md` 和联合进度文档。
- 本轮无 strict 候选，formal `dt=5e-5` 继续锁定。arm1 归档尝试因 SSH 不可达未完成，
  产物明确标记为本地待同步；GitHub push 待网络恢复。

## 2026-10-01 — fixed-reservoir ESN readout-seed decomposition completed locally

- 固定 input-scale=`0.25` 和 reservoir seed=`2026100101`，仅改变 readout seeds `2026100121/22/23`，预注册配置 SHA=`c5f31edb3263fa16702229bfd14d74f7f6b584d0f9a8136f5c51d521385e4828`，训练脚本 SHA=`9e30fd12ed056bedcdafe80a32deb67786aa20e6f22b4612b8ebfecdccea5d2f`。
- ESN task/strict=`0/3`、`0/3`，停在 lift/carry/carry；MLP task/strict=`3/3`、`0/3`。所有回合 550000 子步，动作和 ESN 储备池 replay 最大误差为 0，物理审计通过。
- 独立 audit SHA=`d82652a366c6f2d5cd6b3562c9b483ae298563f5a130955cf41aad3a8f6a2cb3`，73 文件收据 SHA=`eda963478fa3362d7ed4078bb6d6e9eb1bd500126310670eed8b83bfcbe54af6`。固定 reservoir 仍未消除 ESN 对 readout seed 的敏感性，也没有 strict 候选。
- 未完成：formal `dt=5e-5`、arm1 归档和 GitHub push；网络仍不可达，产物标记为本地待同步。

## 2026-10-01 — pure ESN input-scale screen and replication completed locally

- 在冻结 teacher manifest、office-v5 combined-v4、gate、canonical48D/action7、禁止输入和执行器限制下，预注册输入权重尺度 `0.25/0.45/0.80` 屏幕；配置 SHA=`1197d1739ae0e2f1af9671cf4dbabbd1350bb4ab589ef7b951708fd5bd87deff`，训练器 SHA=`881d670a56f1723576534020ef4baebddd0ed29e5e0f7bb2f7a4ffc9e0db77c6`。
- `input_scale=0.25` 的单个 ESN seed 完成 task、strict=false，RMSE/峰矩/峰速/穿透=`68.471 mm / 48.004 Nm / 0.1164 m/s / 0.1499 mm`；0.45/0.80 ESN 分别在 carry/load_transfer 停止。MLP 对照全部 task=true、strict=false。
- 对唯一 task=true 候选预注册复现 seeds `2026100118/19/20`，ESN task/strict=`0/3`、`0/3`；复现 audit 与 73 文件收据 SHA=`688ae6b3556023d64eb1c68ba2d84cde0b6ca461892240cbe9f8a83666b484f2`。屏幕收据 SHA=`0fe9e346533fb27ba4ba306b49d9bc128dbe2bf584b1a168d1ae8dba934e42a2`。因此单 seed 成功不能称 ESN 泛化或优势。
- 所有回合均为开发 `dt=1e-4`/550000 子步，严格 gate 无一通过，未解锁 formal `dt=5e-5`。GitHub/arm1 仍不可达，产物仅本地待同步。

## 2026-10-01 — pure ESN spectral-radius screen completed locally

- 在同一 teacher manifest、场景、gate、actor 输入和执行器限制上完成预注册 spectral-radius 屏幕；只改变 128 单元 ESN reservoir 谱半径 `0.60/0.90/1.10`，每组配同宽度 MLP。配置 SHA=`e96a9880d607d77390b062542e25dab677880587a2483aeb3dcfc4e9b48f0c17`，训练脚本 SHA=`9381becd58ce6c750672e6184f4a452004990bec5e98dd989ba8eab97fab5e5c`。
- 三组 ESN task/strict 均失败：0.60 在 lift，0.90 在 lift 且外部穿透 `1.5602 mm`，1.10 在 carry。MLP 对照仅 0.90 完成 task、strict=false；所有行都是 55 s、`dt=1e-4`、550000 子步开发结果。
- 独立审计 `outputs/esn_mlp_spectral_screen_20261001/INDEPENDENT_AUDIT.json` 通过，六条动作 replay 最大误差为 0，ESN 储备池 replay 最大误差为 0。73 文件收据 SHA=`6505943bf8a8711fb03a2e48a86545cc1937e77b8f1e64c5e9459179a182ae0`。完整结果和失败原因见 `docs/ESN_SPECTRAL_SCREEN_20261001.md`。
- 未完成：ESN strict 泛化、formal `dt=5e-5`、arm1 归档与 GitHub push。网络仍不可达，产物明确标记为本地待同步。

## 2026-10-01 — pure ESN reservoir leak-time screen completed locally

- 开工核对 main 缓存 `ba84ed8a39ed743f603aa5d60e901bdf87090e1d` 与 baseline 缓存 `4dad929b6550b167943becd271836f0c74a21a38`；再次 fetch 和 GitHub/arm1 SSH 均因网络限制失败，未把缓存当作最新远端，未修改 baseline。
- 预注册 `configs/esn_tau_screen_20261001.json`（SHA256=`cd21c44d4b0aa494f464d9aa450c9ff70b6d002361f924e19ae5c7a378d9a9d4`）并新增 `tools/train_esn_mlp_tau_screen_20261001.py`（SHA256=`510fd962ebcf96051f064e5a51bab6fa14a16af5afa9650babd52dd71be4fa09`）。只改变 128 单元 ESN 的 reservoir leak 时间尺度，保持 teacher manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、canonical48D/action7、7/2 identity split、估计负载训练权重、环境/gate/actor 输入/执行器限制不变；每个 profile 都训练同宽度 MLP 对照。
- fast/baseline/slow 三组均已完成 55 s、`dt=1e-4`、550000 子步闭环。ESN 依次在 lift/carry/lift 停止，task/strict 均为 false；MLP fast/baseline 为 task=true、strict=false，slow 为 task/strict=false。ESN 最佳 baseline 行的 RMSE/峰矩/峰速/穿透为 `86.080 mm / 40.585 Nm / 0.0862 m/s / 0.1540 mm`，但未完成 placement。
- 独立审计 `outputs/esn_mlp_tau_screen_20261001/INDEPENDENT_AUDIT.json` 通过；六条物理子步均为 550000，动作回放最大误差为 0，ESN 储备池回放最大误差为 0。汇总 70 文件收据 SHA=`361116939aee2ef4b6bedbcba828b215a516de3158434c00161e7e9c4694eea0`。完整结果和失败原因见 `docs/ESN_TAU_SCREEN_20261001.md` 与 `docs/ESN_VMC_JOINT_PROGRESS_20260927.md`。
- 未完成：strict 泛化成功、formal `dt=5e-5`、arm1 归档与远端 push。由于服务器不可达，本轮大产物仍标记为“本地、待同步”，没有声称服务器已核验。

## 2026-10-01 — paired ESN/MLP seed screen completed

- 完成预注册配置 `configs/esn_mlp_seed_screen_20261001.json` 的 seed
  `2026100106/07/08` 成对训练。三组均使用 manifest SHA256
  `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、固定 7/2
  identity split、估计负载训练权重、canonical48D/action7 和 128 宽度；环境、gate、
  actor 输入与执行器限制保持不变。
- 冻结 combined-v4 开发闭环均为 55 s、550000 子步、`dt=1e-4`。MLP 三组 task=true、
  strict=false；ESN 三组 task=false，seed106/107/108 分别停在 lift/load_transfer/lift。
  ESN/MLP 的 `RMSE mm / 峰矩 Nm / 峰速 m/s / 穿透 mm` 为：
  `874.772/55.664/0.1639/0.1089` vs `52.402/44.708/0.0730/0.1772`；
  `187.222/47.666/0.1601/0.1612` vs `33.860/44.542/0.0707/0.1530`；
  `37.743/38.843/0.0721/0.1714` vs `43.083/45.083/0.0724/0.1843`。
- 六条学生回合独立 action/状态/物理子步审计通过，ESN action/储备池 replay 与 MLP action
  replay 最大误差均为0；没有 strict 通过，未解锁 formal `dt=5e-5`。seed108 的 ESN
  数值指标接近成功但 placement gate 未完成，不能写成 task success或ESN优势。
- 训练峰值 RSS 约 832 MiB；初次错误的 `ulimit -v` 导致 PyTorch 库映射失败，相关失败日志
  保留并不计为实验回合。完整 output、checkpoint、raw rollout 和 audit 已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_mlp_seed_screen_20261001_v1/`；
  evidence tar SHA256=`12ebe6d9529df5dd0bc967a45ed7a5ac77d1d0e4774d8fe10203ac5f158e5aa8`。
- 提交 `9888f6cc361004a70a24851e7915062ca5962a5f` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9888f6cc361004a70a24851e7915062ca5962a5f/repository.tar`，
  SHA256=`36563d9b960253ba1ec4a71ac3a4a1fea3966aa9afbdfe4727ad271e5ee9c589`。

## 2026-10-01 — pre-registered paired ESN/MLP seed screen

- 增加 `configs/esn_mlp_seed_screen_20261001.json`，预注册在锁定的 9 条 teacher manifest
  上使用 seed `2026100106/07/08` 成对训练 weighted ESN 与 MLP；仍为 canonical48D/action7、
  128 宽度、固定 7/2 身份留出和训练期估计负载权重。环境、gate、actor 输入和执行器限制不变。
- 先固定配置并提交，再按同一 combined-v4 冻结命令运行闭环；所有 seed、checkpoint、trace
  hash、失败原因和独立物理子步审计均保留。未运行前不解读结果。

## 2026-10-01 — pure ESN output-gain screen completed

- 完成预注册的纯 ESN `output_gain=0.80/0.90/0.95` 屏幕；只改变 v4 checkpoint 输出增益，
  不改 office-v5、gate、canonical48D actor 输入、执行器限制或 MLP。三条回合均为
  seed `2026091751`、55 s、550000 子步、开发 `dt=1e-4`。
- 结果：0.80 停在 carry，task/strict=false，RMSE/峰矩/峰速 `520.286 mm/41.950 Nm/
  0.1879 m/s`，穿透 `0.1688 mm`；0.90 停在 lift，`407.785/46.242/0.2134`，
  `0.1350 mm`；0.95 停在 lift，`454.745/44.605/0.2160`，`0.1243 mm`。三条均未完成放置，
  失败回合全部保留，没有候选解锁 formal `dt=5e-5`。
- 独立 audit `outputs/esn_gain_screen_20261001_v1/gain_{080,090,095}_audit.json` 全部通过：
  action replay 与储备池状态 replay 最大误差为 0，物理子步为 550000。配置 SHA256 为
  `1d0e8cb73db0a8effa142a3fcdbc2dd026edf70eaa4517231b72815895ce5c90`，基准 checkpoint
  SHA256 为 `bb0bd4df0f9467932c15999853f67fe662aaf5f34c06b79855d4d1ab9a4cf1b0`。
- 结果和审计保留在本地 `outputs/esn_gain_screen_20261001_v1/`，并已逐项核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_gain_screen_20261001_v1/`；
  文件收据 SHA256=`6ed5e73204de983d481200bcf5082a50e1259fbd55a281934aa33e7460dcff74`。
  预注册源码提交为 `9e9580a`，结果记录为 `0a611d4`，最终同步提交为 `7fa6a6e`。
- 对应 `7fa6a6e39459cf846f21400c7f5fa5d4301da1ca` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7fa6a6e39459cf846f21400c7f5fa5d4301da1ca/repository.tar`，
  SHA256=`1a79dd2583859e38ce785d2cd96bfb5efd1b0a2af436c4565224123c92277015`。
- GitHub `main` 已成功推送至 `7fa6a6e`；服务器归档与源码快照逐项核验通过。
- 已完成：三组闭环、三项物理指标重算、动作/状态重放审计和文档更新。未完成：服务器归档、
  formal `dt=5e-5`（门槛未满足）及 ESN 跨条件成功。

## 2026-10-01 — pre-registered ESN output-gain screen

- 注册第二个纯 ESN 算法屏幕，只改变 v4 checkpoint 的 `output_gain=0.80/0.90/0.95`；不
  组合 alpha、不改环境、gate、actor 输入、执行器限制或 MLP。计划见
  `configs/esn_gain_screen_20261001.json`，物化工具为
  `tools/materialize_esn_gain_screen_20261001.py`。
- 先提交预注册和固定 hash，再逐一运行 55 s/550000 子步开发闭环；未运行前不解读结果。

## 2026-10-01 — pre-registered ESN output-smoothing screen

- 在不修改 office-v5、gate、actor 输入、执行器限制或 MLP 的前提下，注册纯 ESN action
  readout `alpha` 屏幕，候选固定为 `0.25/0.50/0.75`；基准 checkpoint 为 v4 无权重
  ESN，完整命令和选择规则见 `configs/esn_alpha_screen_20261001.json`。
- 新增 `tools/materialize_esn_alpha_screen_20261001.py`，生成变体前固定 base/config
  hash；尚未运行闭环，结果不得提前解读。该预注册先提交，随后按单 MuJoCo/1线程/3GiB
  约束逐一运行，所有失败回合保留。

## 2026-10-01 — pure ESN alpha screen completed

- 按已推送的预注册计划，只改变 v4 ESN checkpoint 的 action-readout smoothing
  `alpha=0.25/0.50/0.75`；场景、gate、canonical48D 输入、执行器限制、MLP 和评测命令均不变。
- 三条开发回合均为 55 s/550000 子步、`dt=1e-4`，task/strict 全部 false：alpha 0.25
  停在 lift，RMSE/峰矩/峰速 `367.725 mm/50.319 Nm/0.2420 m/s`，穿透 `0.6467 mm`；
  alpha 0.50 为 `411.708/36.347/0.2306`，穿透 `0.1787 mm`；alpha 0.75 停在 carry，
  `95.040/41.629/0.0848`，穿透 `0.1276 mm`。alpha 0.25 推杆接触最长2.2952s，0.50为
  0.5018s，0.75为0.0038s；不能把接触时长换写成任务成功。
- 三条动作与储备池状态重放均为0，独立物理子步审计通过；未有候选解锁 formal `dt=5e-5`。
  原始回合、失败和审计保留在 `outputs/esn_alpha_screen_20261001_v1/`，并已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_alpha_screen_20261001_v1/`；
  38 文件收据 `FILE_SHA256_REL.txt` SHA256=`45dcf2d710a8ea12cd0f6ba0277669da76deb6af889347e6ec1f9e01575fbffa`，
  远端逐项校验通过。
- 最终提交 `afba210d2eb554b2e3fd7ca5c91363549cbacf2b` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/afba210d2eb554b2e3fd7ca5c91363549cbacf2b/repository.tar`；
  本地/远端 SHA256=`61b0284f613a13677b5c969be7c5dfca965b491c591efd34806cfb055dc9cb54`。

## 2026-10-01 — v3 teacher-label correction and frozen ESN/MLP rerun

- 开工按 `sii-research-sync` 核对本地 `origin/main` 缓存起点
  `3336864707c1e59a1015568a0aea1891e18b8980`；本轮网络受限，无法重新连接 GitHub 或
  `arm1@192.168.31.70`，因此未把缓存 SHA 冒充最新远端状态。远端没有可读的 `baseline`
  分支／更新日志；baseline 工作区未修改。
- 修正 `tools/train_vmc_teacher_esn_mlp_20261001.py` 和 weighted trainer：训练目标绑定
  `execution_chain.npz/filtered_action`，保留 raw `rollout.npz/applied_action`，逐条校验两者
  shape 与 rollout/chain hash；metadata 增加 execution-chain、ESN/MLP 推理源码 hash，并
  更正 trainable 参数量为 ESN 23,559、MLP 23,687。新增
  `tests/test_student_distillation_20261001.py` 的标签出口回归测试。
- 在冻结 manifest、combined-v4、canonical48D/action7、gate、actor 输入与执行器限制下，
  使用本地 `.venv-canonical-rl`、单线程完成 v3 训练（seed `2026100104`）与无初始细步的
  55 s/550000 子步开发闭环。结果：VMC teacher task/strict=true/false，ESN=false/false
  （carry，RMSE 406.806 mm，43.246 Nm，0.2404 m/s，穿透 0.1929 mm），MLP=true/false
  （retreat，43.333 mm，44.405 Nm，0.0753 m/s，穿透 0.1012 mm）。动作重放均为 0，ESN
  储备池重放为 0，独立物理子步审计通过；strict 未通过，不解锁 formal `dt=5e-5`。
- v3 输出、首轮带细步诊断及失败回合保留在
  `code/mujoco_6d_vmc_benchmark/outputs/vmc_teacher_esn_mlp_weighted_20261001_v3/`；详见
  `docs/VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md`、联合进度与周报。checkpoint：ESN
  `a5560ca073c3afed6d553c1ee7a37ac32d537f1245aa6369feabeb022dff40b4`，MLP
  `e27c4ed63cd5f604c5338c90aa87b09e61a90f401a2d92f674c1e69a501e45f0`。v3/v4 随后同步到
  新的 arm1 归档目录（见末项），已有 v1 归档未覆盖。
- 验证：`pytest -q tests/test_student_distillation_20261001.py tests/test_esn_compliance.py
  tests/test_direct_esn_env_contract.py tests/test_office_memory_esn_20260927.py` → 14 passed；
  `git diff --check` 与两训练脚本 `py_compile` 通过。已完成：标签修复、v3 训练、闭环和
  独立审计。运行中：无本机仿真。未完成：arm1 归档、正式 `dt=5e-5`（门槛未满足）及
  strict 泛化成功。
- 追加预注册无负载权重控制 v4（seed `2026100105`, emphasis=0）：ESN task/strict=false/false、
  lift、RMSE 526.818 mm、峰矩44.416 Nm、峰速0.2204 m/s、穿透0.1323 mm；MLP=true/false、
  retreat、RMSE38.832 mm、峰矩44.286 Nm、峰速0.0807 m/s、穿透0.1527 mm。仍为
  55 s/550000 子步开发回合；动作/储备池重放及独立审计通过。v3/v4 均未过 strict，
  不解锁 formal dt=5e-5；v4 也已进入同一新的 arm1 归档目录。
- 随后将 v3/v4 完整输出（68个文件，含 checkpoint、55 s 原始 rollout、MJB、日志和两份
  独立审计）归档到已核验的新目录
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v3_v4/`。
  相对路径收据 `FILE_SHA256_REL.txt` SHA256=`ce2046f058475edcada19bf264a5f0e3406197b8f34a448f1485d3820e34aff5`，
  远端逐项 `sha256sum -c` 全部通过；未覆盖已有 v1 归档。
- 已将本轮提交 `a2a926b5b4deee3dea9476e1eaefd5dcf211f09a` 的源码快照归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a2a926b5b4deee3dea9476e1eaefd5dcf211f09a/repository.tar`，
  本地/远端 SHA256 均为 `4e6fd79dbf6281217fa7dc718d5b9719be6a667be6fcf13930d35e26d9c7dd70`。

本文件记录每次对话交付的文件修改、验证和结果边界；最新记录在前。对应提交号由 Git 历史
查询：`git log --oneline -- UPDATE_LOG.md`。持续提交约定见 [AGENTS.md](AGENTS.md)。

## 2026-10-01 — VMC teacher 标签上的 ESN/MLP 加权读出续实验

- 开工核对 origin：`main=3336864707c1e59a1015568a0aea1891e18b8980`，随后复核远端
  `baseline=4dad929b6550b167943becd271836f0c74a21a38`；baseline 正在独立运行奖励主批次，
  本轮未合并、停止或改写其冻结源/作业。
- 新增 `tools/train_vmc_teacher_esn_mlp_weighted_20261001.py`，在冻结
  canonical48D/action7、相同 128 单元预算下，只对估计力/负载本体通道采用训练期平滑
  权重；actor、环境、gate、执行器限制均未变。新增报告
  `docs/VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md`，并同步联合进度、周报和 README。
- 新 weighted ESN/MLP checkpoint SHA 分别为
  `2723e218b474e4414bbbf199eeda0099eae5dfae6af9fbd3e40cbe6b389483c9`、
  `992a6dcd99685f278687fcf4cf25e1e6d61171dc4dde650489c679f082497cdc`。
  同一 combined-v4 开发场景：ESN task=false、lift停滞，RMSE 688.378 mm、峰矩
  62.020 Nm、峰速 0.1800 m/s；MLP task=true、placement complete、strict=false，
  RMSE 50.381 mm、峰矩 46.634 Nm、峰速 0.0823 m/s、柱最长接触 0.6056 s。
- `tools/audit_vmc_teacher_esn_mlp_20261001.py` 独立审计通过：三行均 55 s/550000
  子步，动作/储备池重放和 RMSE/力矩/速度复算通过。两学生 strict 均 false，未解锁
  formal `dt=5e-5`；失败回合保留。运行中仿真 0，服务器归档待 SSH 恢复。
- 验证：加权模型训练与闭环均在本地 `.venv-canonical-rl` 单线程运行；10项 ESN/环境
  合约测试通过，`git diff --check` 通过。完整 campaign 已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v1/`；
  远端 file-list receipt SHA=`5dc78c054067e88e3b34922023d3bbe476e251008e01941bfa0bd43525a34d96`，
  checkpoint hash 与本地一致。大型 rollout/checkpoint 未提交 Git。
- 首次代码/文档提交为 `48358e8af6c2563209d52e8f8eeeb852d9be9dae`；对应完整 source tar
  已归档到服务器 `source/48358e8af6c2563209d52e8f8eeeb852d9be9dae/repository.tar`，
  SHA256=`951556d584689f520f13d64d3ad0a9130641c067aa02185602835e31e4c9411e`。

## 2026-09-30 — 十小时窗口收尾：215条记录、9个唯一teacher条件与公平经典对照

- 13:29 UTC读取实际远端日志，13:55/13:57复核fetch：main=
  `cd38ad943b1cf16442ca181e44eae64579720986`、baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，未合并baseline、未干扰其旧暂停作业。
- 10小时派发截止13:48:16；最后派发13:46:18.620425、动态结束13:48:22.954650、
  归档结束13:48:50，continuation v2 rc0退出，截止后派发0。终态162搜索＋27验证记账
  （24动态/3初态拒绝）＋26collection，共212完整动态/3初态失败；缺失最后long0002
  阻抗配对明确保留，未补跑。定义3300不等于已执行/合法示范。
- 验证有效8fixture：VMC/导纳/阻抗task7/8、0/8、7/8；strict4/8、0/8、6/8；
  全要求录取3/8、0/8、4/8。每方法另1个预注册初态无效条件。类别分别锁参，不称统一策略
  或VMC全面优势。追加采集共同8训练fixture录取5/8、0/8、5/8，失败参与指标汇总。
- 新collection独立审计26/26通过，全55s/550000子步，动作重放最大5.55e-17；9重复对
  57NPZ/612数组完全相同、不增样本。严格train-only锁参VMC清单9唯一（厚角4/短撞4/持续1），
  205排除/1隔离：隔离因部分配对缺模型绑定且原本接触失败，不是证明模型矛盾；不回写追认。
  validation全排除，无新ESN。每类1000合格、持续推碰可靠teacher和正式综合泛化未完成。
- 新collection审计入口/测试、shared validation helper显式phase/split绑定、完整验证及
  十小时报告；README、联合进度、周报、三类记录同步。65相关测试通过、diff check通过。
  原冻结v10源207项hash保持一致，环境/gate/actor/执行器限制未改，全部为开发dt=1e-4。
- 2120文件最终证据已逐项核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_final/evidence/`，
  含`tools/`审计代码、`outputs/teacher_bank_v10_terminal_review_20260930_1349/`完整metadata、
  `outputs/teacher_bank_v10_final_comparison_20260930_1350/`及raw/duplicate/strict manifest。
  终态review SHA=`6414365111679e1712ed169bc83c3022c7b8b6cf68b56fd7f27a4517b7b0deea`；
  manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`。
  逐条raw及动态源码仍在相邻`teacher_bank_three_domains_20260930_v10/`，215份凭据完整。
  归档后的文档地址补充以本提交为准，不冒称已在较早快照中。运行中仿真0，teacher-10已暂停。
- 汇报入口：[十小时结果](code/mujoco_6d_vmc_benchmark/docs/TEACHER_BANK_TEN_HOUR_REPORT_20260930.md)。
  限时工作已完成，数据数量和研究目标未完成；不能以少量合格轨迹宣称泛化或真实部署安全。

## 2026-09-30 — 严格训练标签出口、初态拒绝诊断与不改场景接续

- 12:21及12:49 UTC核对并读取main=`d39aed3f4800223e1aa1584f1dbcc9d45c13e13f`、baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，无上游新变化，未合并baseline。
- 新训练标签出口绑定原train manifest、锁参、源、实际MJB/NPZ/hash和服务器凭据；
  历史validation标签即使true也拒绝。1144快照仅6个唯一训练fixture（厚角2/短撞3/持续1），
  158排除、0隔离。重复不增样本，矛盾结果/模型隔离；未来runner标签增加train条件，
  冻结v10保留。旧collector/status已另筛train，没有证据表明实际训练数据混用。
- 12:27原作业在21完整validation后因棍推0001初态交叉最大60.09884mm退出；
  独立源码/堆栈/空曝光核查表明动态前拒绝，不能说控制器运动失败。三方法该场景均原样
  保留，无替换。新独立continuation复用全部已完成数据、原冻结attempt与截止，未知异常停机。
  v1资源检查未派发即失败（cpu.max未委派）；v2记录quota_enforced=false并强制单sim/1线程/
  MemoryMax3GiB/Swap0，12:46:27启动，最后验证运行中。此前CPUQuota配置请求不等于实际生效。
- 新增去重原始数组对比、严格标签出口、验证图、接续工具与初态诊断；独立验证审计支持
  无效初态单列null指标。五组相关70测试通过；未修改gate/环境/参数、未做新ESN或正式dt验证。
- 已逐文件核验共享至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_1209/evidence/`厚角raw审计与source发布凭据；
  `_1237/evidence/`1791文件（完整名称前缀同上teacher_bank_review_checkpoint_20260930）；
  `_1242/evidence/`45文件初态核查/v1协议；`_1245/evidence/`41文件v2协议/源和首次启动失败。
  v2 driver SHA=`9215b66fefbd7a91082ddbf7c205c777122a59777f5827502d0042a06ed93077`。
  运行中state及本次补充文档未冒称已在此前快照中。原截止13:48:16 UTC不延长，继续验证/采集。

## 2026-09-30 — 162搜索锁参、首个人推独立通过与完整决策审计

- 11:52 UTC重新fetch并读main=`0a1e7972750114d2e0e1f5c1626004e1ed449d7a`及baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，上游无新增变化，未合并baseline。
- 11:42搜索162/162完成，27录取/135未录取；九组候选/排名、源与配对模型独立核对通过。
  bank SHA=`1cafd43556f754df0595027c6aa1a358520038bbd5a3f742b9ef3b2a2f287945`。
  锁定参数训练录取厚角VMC/导纳/阻抗2/3、0/3、2/3；短撞3/3、1/3、2/3；持续1/3、0/3、0/3。
  task/strict与曝光/录取分开，持续阻抗task/strict仍2/3；不称VMC三指标全面优势。
  27预注册验证运行，collection/新ESN未开始，仍只有2/3/1个唯一合格VMC训练fixture。
- 新增定义覆盖工具，3300定义在剔除未消费字段后仍全部唯一、train/val精确重合0，未宣称
  全量动态有效。全部27BO决策用当时训练前缀同实现精确重放，误差0，不当作收敛证明。
  短撞c05退化诊断区分两类任务失败，不调原score。首个人推c05原始550000子步/动作与
  独立连续段重算通过：1.2643s同段14.3532mm；但RMSE/峰力增加且仍碎接触，不称真实安全。
- 新增validation离线审计、human分段与图工具、相关专属报告，10项针对性测试通过。
  全162点图显示所有失败并修正长期图标签含paddle，已视觉核验。README/主记录/进度/周报同步。
- 均已逐项核验到服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_1124/evidence/`56文件定义覆盖、短撞诊断及工具；
  `teacher_bank_review_checkpoint_20260930_1138/evidence/`49文件独立人推/图与全部BO审计；
  `teacher_bank_review_checkpoint_20260930_1150/evidence/`1609文件锁定元数据、公平表和162点图。
  锁定review SHA=`a2708301bdf41874c01dca8a31611c6a5fc1a09081fb50e6c41ea6c8afd32169`；
  人推review SHA=`dab55a4eba144668891332ff6c9a4dbd4415ae8a2c21e7cce7e3acb5725ba2a7`。
  归档后文档地址补充以本Git提交为准，不冒称已在旧快照中。稳定v10未重启，10小时任务继续。

## 2026-09-30 — 135回合检查点、完整资产复现更正与公平展示

- 11:10 UTC重新fetch并读取main=`2581451cc9c471b19c67286457bea8d3b8a4b2b7`及baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`日志。baseline奖励主实验和独立40k诊断均已收尾，
  仍存在无grasp的探索瓶颈；不合并、不混同其综合场景和本次训练域，也不声称算法本质失败。
- v10完整c00–c04共135回合23录取/112失败，c05继续，未重启。短撞VMC c04单参数3/3、
  c05为0/3；不改规则或丢失败。参数未锁定，validation/collection/新ESN未开始。
- 纠正资产清单遗漏FR3：完整133文件而非85；未来prepare校验两树与引用资源。原冻结
  plan/source/execution保留。本机真实冻结初始化零积分9/9逐字节复现；XML-only0/9因质量
  默认和运行时mask等差异失败。ARM首个source模型22数组有差异，动态补充采集阻断。
  新资产审计/静态复现工具与报告解释范围，不声称跨架构物理等价。
- 新公平展示器分列task/strict/曝光/录取与失败，锁定前不输出策略成绩；三方法指标采用
  同fixture共同完整证据集合，缺失或不匹配一项则共同排除指标聚合但保留任务统计与明细。
  最终11测试通过；资产6/选择6/Spark driver8通过。Spark采集driver仅准备，未启动态作业。
- 已逐文件核验服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_runtime_inputs_complete_20260930/menagerie/`完整133资产，manifest SHA
  `56b0e9d07c2b0e5636f38fb228dbd077980d2ea14c2ea26bc8987be11a304523`；
  `teacher_bank_review_checkpoint_20260930_1104/evidence/`含112文件，本机静态成功和XML失败
  证据、135状态及归档时工具版本；`teacher_bank_spark_static_source_20260930_v1/`为ARM阻断证据。
  归档后的展示器修正及本段文档以本次Git提交为准，未虚称已在1104快照中。
  10小时窗口继续至13:48:16 UTC；3300定义不等于示范，未达到每类1000条。

## 2026-09-30 — 短撞VMC同参数3/3与108回合公平检查点

- 09:42 UTC核对main=`e1d815c390d1221ee0bf80293e2b8179d2e1d3f8`，baseline已前进至
  `e47da59ebb665fb20764131bd56c7b639805f326`，已读新日志。其100k RL主实验已完成但任务失败，
  发现训练覆盖问题后正做独立补充诊断；不把该局限解释为算法本质，不混入本轮特化训练比较，
  未合并baseline或操作其Spark服务。
- 09:40 v10完整c00–c03共108条，17录取/91失败，全部逐条有核验归档凭据；c04运行。
  VMC短撞c03同一参数3/3，初始c00为2/3。六条配对550000子步的三指标独立重算、冻结
  VMC/filter/状态重放与source/参数/model/hash通过；球形RMSE64.667→37.662mm、峰矩
  47.935→45.004Nm，但峰力1793→2221N、穿透0.11744→0.18863mm。穿透仅元数据核验，
  不冒称独立物理重算、全面安全提升或泛化。新增短撞审计工具和报告，更新专题/进度/周报。
- 新终态收尾工具保存原始JSON快照、独立重建选参和锁定、核对后续参数一致性并指出截止
  汇总归档缺口；11项针对性测试通过，live验收正常。它不重新核验所有原始轨迹/远端receipt。
  原稳定仿真未重启，仍固定六候选；持续推碰三方法0/12，validation/collection/新ESN未开始。
- 以下均已逐文件核验至服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_0913/evidence/`含964文件（短撞审计/六份重放、终态
  工具与live验收/JSON快照）；review SHA=`d135e2f4336583528e66be27e03b0e47b66201355fbc5d03b21212c7a1659c50`。
  `teacher_bank_review_checkpoint_20260930_0943/evidence/`含42文件（108回合status/公平图/报告），
  PNG已视觉核验，SHA=`fb7df489d653adfad53c1a2245d5eca8ef7b2aba7019c3c035ec92148d3f9f13`。
  10小时任务继续至原截止，不改gate、环境或执行器，不把3300定义当作已采满示范。

## 2026-09-30 — 初始81回合完成与首个BO决策复核

- 08:57 UTC再次核对main=`b1e14de2dade36eed6cc8d9ce448cd8b4a1565ad`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及日志，无新上游变化；未合并baseline。
- 08:40检查点的初始81回合10录取/71失败，VMC唯一合格fixture厚角2/短撞3/持续推碰0。
  不能把跨参数样本拼成单控制器成功率。实际BO已开始，首个VMC厚角c03录取1/3，低于c01
  的2/3；不称BO已改善。参数未锁定，validation/collection/新ESN未开始，固定预算继续。
- 新增首次BO只读审计及报告：前三候选训练证据独立汇总与history一致；读取九份真实MJB
  哈希，并核对peer audit记录的同模型hash，未冒称重读peer全部模型。冻结源与plan绑定；
  相同优化器实现、seed20260933重放差0。首次是可行性LCB，离散代理不是连续物理超限。
- 初始81条公平三指标图含所有失败，排除另计尚不完整BO尝试，PNG视觉核验通过。
  审计/图/status等44文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0848/evidence/`。
  review SHA=`979ea114c384ba23ced024f37601a35221ed3c27da9f9832ba97d6f14a6dc197`；
  PNG SHA=`31f933a44a09a1fea4eb0189130cc8bfd1ee29191219af9195efc6de8e0a8536`。
  更新三类记录/联合进度/周报。v10未重启，冻结测试、gate和执行器未改；十小时任务继续。

## 2026-09-30 — 54回合检查点与可复算的公平三指标图

- 07:18 UTC核对main=`24c5bac6f26bae935d2367b952ebe0f97bb6fc5b`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，未出现上游变化。稳定v10服务未重启。
- 07:35 UTC前两个初始候选54回合完成：8录取/46失败，全部已核验归档；第三组c02运行。
  VMC合格唯一fixture为厚角2/短撞3/持续推碰0，但短撞3条来自不同候选，不能拼成单策略3/3。
  银行未锁定，BO/独立验证/collection/新ESN尚未完成，截止与预算不变。
- 新增`plot_teacher_bank_search_20260930.py`和测试：只画共同完整候选前缀，核对每条audit SHA、
  fixture/MJB、方法/录取与anchor集合，保留所有失败，partial另计。stage-waypoint RMSE与
  峰矩/峰速分列展示，不当平滑全局路径误差，不挑最佳点，不冒称重新复算物理轨迹。
  5项证据/搬移/不覆盖校验通过；首轮27点PNG视觉检查通过。可选campaign-root映射服务器
  读取根，原执行路径保留，v3旧图不重写。联合进度/周报/主报告同步更新。
- 以下均已逐文件核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_0717/evidence/`含42文件（首轮PNG/PDF/点JSON/来源status/绘图源）；
  `teacher_bank_review_checkpoint_20260930_0722/evidence/`含36文件（支持服务器映射的新版源码/测试）；
  `teacher_bank_review_checkpoint_20260930_0736/evidence/`含36文件（54回合配对状态）。
  PNG SHA=`bf088ec34ac28340a6c19535654dc1d4f4d80885c63926e22643f2e1c9072824`，完整点JSON的
  SHA=`507cae91f03b65b2335c0c4fde6b08d09295dd46e1b1a1a1816f4f919b514c8e`。未改冻结源码或gate。

## 2026-09-30 — 完整首轮27回合及人手子步独立重建

- 06:26 UTC核对main=`f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，均无新上游变更。v10相同服务稳定运行，未重启。
- 06:32 UTC第一轮c00三类×三方法×三anchor共27条全部完成，5录取/22失败并逐条归档；
  持续推碰三方法均0/3。status确认三个类别共同完整候选前缀[0]、模型hash与历史一致。
  进入c01；固定6候选搜索未完成、参数未锁定，collection=0、新ESN未启动。
- 新增`teacher_bank_person_anchor_review_20260930.py`及专题报告，原hash全匹配；每条550000
  物理子步独立重建schema2连续段，差≤1.22e-13。VMC1.2516s/9.09595mm，尚差0.90405mm；
  导纳宏观约27mm不能替代连续段要求；阻抗连宏观也不足1cm。力阈值间断不能当几何脱离。
  保留所有失败，不改gate/冻结环境或源。同步联合进度、周报和三类主报告。
- 新脚本/JSON/完整配对汇总38文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/`。
  review SHA=`2f94c7999c3732582e38b69e005c75e257dda84f510b1f190842ac8e145c7835`。
- f3b42f5完整源码2623文件已核验发布到同一服务器
  `/home/arm1/sii_shared/SII_compliance/source/f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985/`；
  tar SHA=`274e159481c6f9545ce705b0bcfee90455f0c8caf7433aa7b8357d4a0f931b11`。10小时任务仍继续。

## 2026-09-30 — 首两条VMC合格搜索轨迹复核，完整保留接触峰力

- 06:16 UTC核对main=`5ded01a21ed07f57c28786c616507ade46974289`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及两分支日志，未合并baseline；Spark四个新worker运行，
  旧四个进程为T暂停态。本机v10稳定，未重启或新增仿真。
- 06:18 UTC v10完成21条搜索/5条录取/16条失败，另1条运行。共同c00配对：厚角VMC/导纳/阻抗
  0/3、0/3、2/3；短撞2/3、0/3、1/3。VMC持续推碰0/3，其余方法仍在运行；不提前作配对结论。
- 新增`teacher_bank_search_success_audit_20260930.py`及专题报告：VMC短撞337/671原hash与独立
  子步指标重算通过，冻结runner动作/状态重放通过。它们是初始参数搜索样本，不是BO改善，
  不代表独立验证。正式collection=0、参数银行未锁定，各类1000有效示范/新ESN未完成。
- VMC两条合格短撞接触峰力约1368/1350 N，阻抗合格短撞约2077 N；保留冲击风险局限，
  不用电机峰矩合规冒充低碰撞力/真实部署安全。未改变gate、模型或评分。
- status工具新增已完成rollout元数据哈希核验、接触载荷及原失败字段，不冒充独立物理复算。
  19项status测试通过；联合进度、周报及三类记录同步更新。
- 冻结源码输入审计：反馈控制器无直接外部真值字段，但共享task executive使用真实支撑/物块速度
  辅助松爪，并间接改变名义参考。专题文档明确该边界，不将当前系统称为端到端纯本体真实部署；
  本轮不修改共同协议或停止稳定作业。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`下：
  `teacher_bank_review_checkpoint_20260930_0603/evidence/`（40文件，首次VMC复核源码/JSON/报告）；
  `teacher_bank_review_checkpoint_20260930_0621/evidence/`（38文件，06:18状态及status源码/测试）。
  原始轨迹继续逐条归档到`teacher_bank_three_domains_20260930_v10/`。10小时任务继续，截止不变。

## 2026-09-30 — 首个公平配对与pilot失败归因，v10继续运行

- 05:36 UTC核对main=`7423d5ef94df05470ba14188a983f92fc51846b1`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`，已读日志，未合并baseline。
- 05:49 UTC，v10厚桌角c00完成三个方法各3个anchor、同模型hash配对，录取VMC0/3、导纳0/3、
  阻抗2/3。统计含失败，不称泛化；参数银行仍暂定，作业继续短撞类别，本机单环境/1线程/3GiB。
  VMC合格新教师仍0，全部搜索、独立验证、各类1000有效轨迹及ESN未完成。
- 新增`tools/teacher_bank_pilot_failure_causes_20260930.py`及同名专题报告（研究目录内）：
  九条v8原始文件hash全部匹配，子步三指标独立重算差≤6.94e-18m，力矩/速度差0。
  球撞VMC主要晚期释放后滑落；导纳放置漂移、阻抗收敛超时。145mm误差跳变主要来自
  waypoint切换，不能当作碰撞末端位移。人推VMC/导纳约27mm宏观位移横跨微接触间断，
  不能说完全不会让位，也不能追认连续接触/schema2成功。原gate/源/失败记录未改。
- 归因JSON SHA=`c6d3469bea9113edf7416697d31950921b7d2fbf44da3f5016c2c74d6d020986`。
  41个新证据文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`；
  内含归因脚本/报告/JSON、当前status源码和v10_0549预算汇总。新增review归档的显式include选项。
- 已提交源码7423d5e的2618文件经SHA/大小/权限及完整文件集合核对，共享到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7423d5ef94df05470ba14188a983f92fc51846b1/`。
  tar SHA=`47399ebcc9e6463d81f001a3112642ff362e45e9ee46f046efff37229b8cf13e`；初次tar compare
  仅因uid/gid不同而退出，之后独立核验内容通过才发布。新增源码归档核验工具，不改源内容。
- 更新联合进度、周报和三类专题。未重启稳定作业、未新增仿真槽位，10小时原截止不变。

## 2026-09-30 — 三类pilot审计完成，v10公平搜索启动（10小时任务继续）

- 05:19 UTC接续核对main=`8dec129deecf2b769e765c5d91a54a64140a22a7`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`并读日志。baseline的SimbaV2
  campaign_03在Spark四路训练，本任务本机单环境/1线程/3GiB，不修改其分支或作业。
- 已完成v6六条主动pilot、v8九条三类别pilot及服务器归档；v8仅阻抗厚桌角fixture0通过，
  RMSE47.988mm/峰矩45.612Nm/峰速0.15314m/s。接触18840段、其中一个5ms段以0.231mm上抬
  通过已注册曝光，不称平顺明显蹭过。VMC同场任务成功但上抬0.0866mm不足0.1mm，保留拒绝。
  当前合格新VMC轨迹为0，不把3300配置定义当成功示范。未启动新ESN。
- 新训练厚边缘移至掌翼上方，避开下降手掌；18项跨类初态预检通过。只改新增训练域，
  冻结综合测试/gate/actor/执行器不变。几何失败、旧corner曝光不足与v5失败全部保留。
- 修复人手曝光方向与施推时窗，schema2保存每个物理子步；旧schema1不追认为新筛选通过。
  修复搜索anchor的物体形状覆盖（0/337/671），独立验证固定0/1/11。候选成功anchor数量
  优先，之后比较失败标签代理及原评分；不把该离散代理称作连续物理超限。
- 每次dispatch核验实际Panda资产85文件，模型hash跨方法/候选/阶段一致；新增曝光-物理
  时间绑定、观察q/dq-前后状态绑定。九条旧pilot关联只读复核全通过，原audit未改写。
  搜索开始前73项测试通过。数值异常停机待分类，不吞异常或伪造BO指标。
- v8于05:23:21 UTC按预定阶段锁在pilot后停止，末尾BlockingIOError是计划内边界停止，
  不算物理失败。v9只准备未运行。v10于05:29:05 UTC实际启动固定6候选×3anchor搜索，
  首回合完成并归档，未通过接触筛选。服务`teacher-bank-search-v10-20260930.service`。
  计算窗口仍截止13:48:16 UTC；heartbeat保留到14:28只做最后归档审计，不扩展计算授权。
- 已核验服务器根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`。
  其下`teacher_bank_three_domains_20260930_v10/`含源码210文件、metadata2文件、输入3文件，
  运行记录逐条发布。`teacher_bank_runtime_inputs_20260930/menagerie/`含实际Panda资产85文件；
  `teacher_bank_reaudit_v5_20260930/impedance/`为旧raw复审及源码；
  `teacher_bank_review_checkpoint_20260930_0527/evidence/`为34份新几何/pilot报告/计划停止证据。
  所有路径均已SHA256核验，未覆盖历史产物。
- 已更新README、联合进度、周报、三类专题及schema2/手掌阻塞诊断；新增独立审计测试和
  review归档工具。未完成：搜索、锁定参数验证、各类1000条合格teacher、ESN与正式泛化。
  `teacher_bank.json`搜索中只是暂定选择；截止partial block须单列，公平比较用共同完整预算。
- 搜索启动后另扩展只读status，独立核验decision/anchors/执行记录和模型hash、reuse/recovery、
  共同完整候选前缀、截止partial，以及完整搜索后才locked。该工具13项测试通过；没有改
  v10冻结源码或运行过程。实时PID核验需宿主上下文，沙箱生成报告可能看不到systemd进程。

## 2026-09-30 — 启动三类 teacher 数据与经典 baseline 的 10 小时任务

- 开工核对 main=`38caf3152282df4963435bb65c11c93a1e4fffa5`、
  baseline=`59342005b11b5892b18301fd9b52c6b07ad87f45`；开工时其日志仅有初始化，
  其工作区 `/home/arm1/SII_compliance_baseline` 不由本任务修改。
  04:15 UTC再次核对baseline已到`5bc21d8d19eaf60691f561f0ad9dd4409749e667`，已读新日志：
  SimbaV2奖励配对训练/GPU验证与布局合法性修正；不合并其分支，不占用Spark仿真槽位。
- 用户新增授权：三类各至少1000训练环境，VMC同时作teacher/model-based baseline，导纳/阻抗
  同场景同预算调参，多agent协作，持续10小时。窗口至2026-09-30 13:48:16 UTC。
- 新增 `tools/teacher_bank_{design,rollout,campaign,classical,exposure}_20260930.py`、相关测试和
  `docs/TEACHER_BANK_THREE_DOMAINS_20260930.md`、独立场景审查报告（路径相对研究目录）。
  生成3000训练+300验证配置，支持冻结源码、约束BO、原始/过滤动作、物理子步与接触曝光审计。
- 已完成34项新测试；动态pilot发现新训练桌角连接件初态与机器人相交，正确拒绝并归档，
  修正为绕手爪连接后42个初态预检通过。v4九条动态pilot已于04:16 UTC启动。
  v4完成一个有效物理回合但没有真实上抬碰face，不可入库；导纳adapter在仿真前失败已修。
  v5于04:30 UTC启动，VMC/导纳前两条均在align被训练face挡住，负结果保留，继续其他配对。
  尚无合格新teacher轨迹；未启动ESN、不改冻结综合测试或保留集。
- 已核验服务器源码/失败路径：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v2/`。
  v4源码206文件/metadata2文件也已核验归档到同一父目录下
  `teacher_bank_three_domains_20260930_v4/`，动态轨迹完成后逐条归档。
  不覆盖失败记录。详细实时状态和限制见上述专题文档。
- 新增进程身份恢复：仅确认旧PID已退出才另开retry目录，旧文件逐字节保留，基础设施失败
  不进入BO；新增只读状态汇总器。53项测试通过。公共评分移除对力矩阻抗不公平的action7
  平滑罚，补配对MJB一致性和阻抗命令→实际物理力矩审计。
- v5源码209文件、metadata2文件已核验归档到同父目录`teacher_bank_three_domains_20260930_v5/`；
  几何诊断/初态成功及失败的7份JSON已核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_archive_20260930/evidence/`。
- 重要纠正：旧corner task/strict成功不是“上抬碰face成功”证据。新曝光审计把桌面支撑与
  真实上抬碰边分开。十小时按98.3s首回合吞吐无法跑满9000次配对采集；搜索前预注册
  6候选×3anchors/方法/类、每类3个独立验证、之后剩余时间配对采集，3000有效数据目标未完成。
- v5阻抗完整仿真后审计触发3GiB限制，原因是NPZ逐行索引重复解压且保留整列view；已修为
  一次读列＋生成器，54项测试通过。旧raw独立复审4.39s成功，13750servo/550000子步实际力矩
  映射误差0；原failed execution不改写。该复审仅本地、待归档。
  v5现已停止；v6冻结源码的主动短撞/持续推碰六条pilot已启动，仍单环境/1线程/3GiB。

## 2026-09-30 — 协作 skill：双分支开工检查、本地计算与服务器归档

- 新增 `skills/sii-research-sync/SKILL.md` 与 `agents/openai.yaml`，安装至
  `/home/airpig/.codex/skills/sii-research-sync/`，允许自动选择。开工先 fetch/读取远端
  main、baseline 的 `UPDATE_LOG.md`；收工重新读取 `AGENTS.md`，记录并发布本轮进展。
  同步更新根目录 AGENTS 与 README，让未自动加载 skill 的后续 agent 也有入口。
- 本轮远端检查（2026-09-30，Asia/Shanghai）：main=`f098678ad1532f1b87c7e2ac803faa301c4c65ca`；截至本轮查询，
  远端没有 baseline 分支，因此无 baseline 更新日志可读。没有擅自创建分支或合并代码。
- 新默认偏好：尽量本地计算，服务器共享持久文件。共享目录为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`，源码按 commit 隔离，
  实验按 branch/run-id 隔离；先同步并校验，再把服务器绝对路径写入更新文档。
  本地缓存和实际执行来源保留，不改历史 execution.json，不覆盖别的 agent 或 runtime。
- 本轮归档的是已发布研究源码，服务器代码位置：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f098678ad1532f1b87c7e2ac803faa301c4c65ca/code/mujoco_6d_vmc_benchmark/`。
  此路径对应本轮开始时的研究代码；本轮 skill/文档更改以 GitHub 新提交为准。
  未全量迁移历史 outputs、原始大轨迹或 checkpoint，不声称它们已在新共享目录。
- 验证：仓库版与安装版 skill 均通过 skill-creator 的 quick_validate，目录内容一致；
  使用现有 `.venv-canonical-rl` 中的 PyYAML 完成校验，未安装新依赖。文档差异检查通过。
  本轮没有修改算法、环境或启动仿真。
- 已完成：skill 编写安装、双分支状态检查、共享目录创建与研究源码归档。2026-09-30
  03:10:53 UTC 逐文件校验服务器快照：2,592 个文件 SHA256 全部一致，无缺失或额外文件。
  本轮没有运行中的新实验；历史大文件仍在原位置，后续按实际任务逐批归档。

## 2026-09-30 — 积累成果同步与每轮自动提交约定

### 文件更新

- 新增根目录 `AGENTS.md`，落实用户“每次对话结束前 commit、push main、记录更新”的授权。
  新增本日志，README 增加当前状态与入口。此次同步的起点为 `2e37ddc`。
- 纳入 9 月 23 日至今未提交的研究代码、配置、测试、报告与小型证据：统一物理子步指标、
  经典控制器预算实验、canonical48D/action7 及参数动作 RL 对照、ESN 记忆消融、
  VMC＋ESN 联合优化、延迟球撞、综合环境的版本化开发、纯 ESN 与 MLP 比较和动作重放审计。
  各历史实验的冻结配置、失败原因与结论以各自报告为准，不合并为一个“全部成功”的结论。
- 纳入独立 teacher 修正实现 `scripts/vmc_teacher_stable_readout_20260930.py`、
  `tools/teacher_repair_campaign_20260930.py`、`tools/teacher_repair_followup_20260930.py`、
  `tools/audit_teacher_repair_20260930.py`，以及 `docs/TEACHER_REPAIR_20260930.md` 和进度、周报。
  上述路径均相对 `code/mujoco_6d_vmc_benchmark/`。
- 新增 `tools/export_publication_evidence_20260930.py`，导出 teacher 的小型审计 JSON、运行配置、
  源码快照及哈希索引到 `docs/evidence/publication_20260930/`。原始大文件不进入普通 Git：
  `results/` 下 NPZ/MJB、证据目录编译模型，以及原本已忽略的 outputs、视频等仍在原处。
  本次清单覆盖 results 大文件、证据 MJB 和三轮 teacher 输出，不覆盖所有历史 outputs 或服务器。
  小型 docs/evidence NPZ 仍纳入版本管理。没有删除原始数据；需要完整重放时还须取得清单中的本地产物。

### 已有实验结果（与本次发布检查分开）

- teacher 两轮完成 12 条有效 55 s、dt=1e-4 开发回合；动作、内部状态及过滤链独立重放误差为 0，
  每条 550,000 个物理子步复算指标。此前误用 MuJoCo 3.14 的四条诊断保留，不混入有效结果；
  有效实验固定 MuJoCo 3.11，并核对综合模型 SHA256。
- 当前候选 `velocity025_stiff2`：corner-placement 的 task/strict 均通过；综合单柱 v4
  task=true、strict=false（缺少要求的柱接触）。综合 waypoint RMSE 37.406 mm，峰值实际力矩
  48.127 Nm，峰值末端速度 0.070574 m/s，外部穿透 0.144922 mm。
  相对同模型原版，放置阶段动作差分 RMS 0.306187→0.042031，降低约 86.3%。
- 尚未完成：特化场景全协议与跨条件验证、综合 strict、正式 dt=5e-5，以及稳定 teacher 数据上的
  新纯 ESN 蒸馏。此次发布没有新训练，没有改冻结环境或 gate。
- README 中 9/29 的 delayed-ball 正式通过结果和早期 cup/pillar 综合失败属于不同版本；
  不可与当前单柱 teacher 开发回合互相替代，也不能据此声称 ESN 已全面优于 baseline。

### 发布验证

发布内容扫描：814 个 Python 文件（包含归档源码副本）语法通过，1,216 个 JSON 可解析；
已检查的私钥、GitHub token、AWS key 和含密码 URL 模式无命中。相关既有测试
`test_esn_load_gated_20260929`、`test_esn_impact_response_20260929`、
`test_office_canonical_audit_20260927`、`test_physics_substep_metrics_20260923`
共 9 项通过。发布集合约 60 MB，最大单文件约 7.6 MB，无超大单文件。
产物索引含 1,642 项、17,382,062,868 字节（含保留在本地的原始数据和已复制的小型证据）。
本次不重复运行已经完成的长仿真实验。
发布整理同时移除了八份历史 Markdown 的行尾空白或多余末尾空行，不修改实验内容。
`git diff --cached --check` 通过；推送前 fetch 确认远端 main 与此次同步起点一致。
