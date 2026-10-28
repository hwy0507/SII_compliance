# 参数59完整、冻结55独立复核与准确续训60

2026-10-28 UTC。Goal **active**，尚未达到三路 reward 稳定且 loss 无异常的整体目标。用户要求即使科学任务完成也继续 GPU 保活；守护负载不能作为训练吞吐或收敛证据。无子 agent。

实际计算主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；共享 SSD 根目录
`B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
仓库 `B/repository/SII_compliance`。Torch `B/env/bin/python`，Direct JAX `B/serl_env/bin/python`。
本轮开工实际查询/fetch/read main `f9c757c28ae7f69e04fb1ff0f24d75f77966ce68` 与 baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。main 非RL拟合/测试接续/接触诊断改动已读并 fast-forward 保留，未改其运行。

## 完整59

原 `B/runs/parameter_capacity_pool30_cycle59_20261026_v1` 三 learner 自然退出；归档及完整审查通过。每路30条件×55秒、41250新增、无abort；全58 replay/history、4m容量和历史23/47 marker保留，新reward重算误差0、网络/优化器有限。

|方法|steps / updates|mean reward|Task / Strict|critic首→末1000|critic mean / max|
|---|---|---:|---|---|---|
|阻抗|2470398 / 2465399|−0.596952576|18 / 18|2.567929280 → 2.073373972|2.294326621 / 31.611806870|
|导纳|2471000 / 2466001|−13.606294811|12 / 11|1.429877706 → 1.613900730|1.429315008 / 25.786527634|
|VMC|2472000 / 2467001|−4.517594098|17 / 16|1.167645328 → 1.331206823|1.140594475 / 36.549129486|

归档 `B/runs/parameter_capacity_pool30_cycle59_archive_20261026_v1/{method}/cycle_00059.pt`：

- impedance SHA256 `391fb04ff614e3ec94cbb4d1da1d22d7aae6979ecafc1c1df47261ad6c54fbad`。
- admittance SHA256 `8039ec5b5acc8de9bb414803e9b1f31497110e684f33dafb0d785b9d02cc7c2f`。
- vmc SHA256 `e5acf40dac600683c6839d670818641ec9ed73176902222fb93a0623b1af9a87`。

`B/runs/parameter59_loss_20261028_v1` 全41250更新逐字段有限/连续、实际长度及49–59完整历史和源hash审查通过；独立保存算术与实际loss图均完成。阻抗actor30.929136→29.972500仍漂移；导纳约37000更新、VMC约34000更新有后段burst，尾critic上升。有限数值不能等同收敛。

原58→59配对：阻抗short0600外穿透.217917→.188218mm恢复Strict，long0000恢复Task/Strict；导纳short0600/short0900/long0900失Task+Strict，short0000 Task保持但穿透.135968→.217124mm失Strict；VMC标签全部保持。原MJB/evaluator/hash及.2mm门不变，无独立子步重仿真。

health路径 `B/runs/parameter_capacity_pool30_cycle59_review_20261026_v1/health`，JSON及实际图已读。I/A/V全终端MAE .864863248/.720910685/.663977199，inbag .240082521/.318956615/.347268919，固定min-pair未投影TD .251009461/.251608648/.166932148，Qmean −29.597247482/9.962840521/14.227318151。A/V训练target为mean，诊断为固定min；网络不变。health图标题边缘裁切，精确定义以JSON为准。

原56–58阻抗reward5%通过事实保留；59均值从−4.044914变至−.596953，平台未延续。原VMC53–55通过也保留。启动59之前登记的连续59–61窗口仍等待60/61，原5%/seed2026102855/5000 bootstrap/anchor55不改。I59绝对均值<1触发原near-zero保护，不能修改公式或宣称相对稳定通过。原56–58 bootstrap未独立重跑，保存标量与图已独立复核。

## VMC全部旧终端对照

`B/runs/vmc59_terminal_anchor_followup_20261028_v1` 完整FINISHED、保存值独立复算和实际图审通过。登记在59训练期间，不冒称训练前登记。固定58全1764×57输入逐项相等；权重/RNG不变、health59复现，0优化/物理。

旧1764 masked SSE 8649.382573630→7126.144292315，下降17.61095%；按最终分母旧贡献.521313854→.422160890，新30贡献.159778508，全部.581939398。旧58分母下末值.429339460。
第58轮short0600失败索引2423133 SSE5275.945304→1175.688107改善，但short0200成功索引2423122从530.595778→1637.752307退化。三个历史focus2050526/2299142/2046571均改善。全部旧样本保留，不作梯度/随机minibatch因果解释，不增加零误差停止门。

anchor58 SHA `55d2476e60f106cf1c08701140c8dc03e88047a2043cb40fbbc0ea81b42be383`；values SHA `aec16c2ec6ce49beac679eb6b57ffa64aade976df26ef5e9e4bd006f51d6f07f`；follow59.png SHA `a6d527e5ab7c2ad7c3d818654784038d18eb4f56a9996c2ef1a5d5afbc4b8e64`。图标题完整，近原点标注有重叠。

## 冻结55完成与41→55比较

`B/runs/parameter55_frozen_full30_20261028_v1` 原三评估器及root审查自然结束，完整90回合/123750动作/99000000子步，全部55秒，0新优化，全learner/replay状态不变；原30训练条件与外部action seed2026102638。

|方法|冻结41 reward|冻结55 reward|41 Task/Strict|55 Task/Strict|55外穿透范围mm|
|---|---:|---:|---|---|---|
|阻抗|−.528457769|−.566896182|18/18|18/18|.009163–.186254|
|导纳|−10.422220086|−13.654079407|14/13|13/11|.018243–.208611|
|VMC|−2.909769682|−2.862454262|17/17|17/17|.005275–.181918|

完整独立复核 `B/runs/parameter41_55_frozen_comparison_20261028_v2/REVIEW.json` 已通过全部180回合保存标量/门/源及全30配对。导纳Strict恢复short0200、long0500；失去short0100、short0900、long0300、long0900，净−2。阻抗/VMC无Strict标签变化。实际 `frozen_full30_results.png` 已目视：三方法全部10 passive_corner仍负回报；导纳2点超原.2mm门，失败保留。

原v1报错 `AssertionError: runtime` 及日志保留。原因是把第41与55轮各自runtime目录字符串误设为应相同。v2仅修复此审查逻辑：绑定两个准确路径、每个登记源码hash及全部共有源码内容相等，并继续要求全条件/seed/MJB/实际执行evaluator相等；原评测程序和结果未改、未重跑物理。v2在结果完成后修正，不冒称预登记。源码diff、原失败和v2PLAN均归档。

冻结41 replay2m、冻结55 replay4m且训练曝光不同；此为同训练条件单action-seed的描述性比较，不能解释为容量独立因果、泛化、多seed稳健性、最终ESN比较或训练已收敛。原raw子步/filter/torque审计保留，本次独立复核未重做全部raw物理。

## 当前60及接续入口

`B/runtime/prepare_parameter60_20261028_v1/DECISION60.json` 绑定完整59/health/loss/配对/独立保存算术/图/VMC终端/原56–58和未来59–61计划。准确59 fulllearner/replay/下一65536恢复三路exit0后，10:39:24启动一个有限60，原reward/gate/物理/LR/mask/批量65536/UTD1/终端权重128/target规则保持，无auto61。

- 60 run：`B/runs/parameter_capacity_pool30_cycle60_20261026_v1`。
- learner I2048394/A2048396/V2048399，start ticks均37968090；GPU1/2/3、CPU13–25/26–38/39–51，每路30sampler。
- archive身份以该run `MONITOR_LAUNCH.json` 为准；实际startup已通过新增1000/1000/2000、旧2470398/2471000/2472000全部replay/history保留、新reward0误差。证据 `startup/REVIEW.json`；不是只有check-only通过。
- 完整60 loss等待 `B/runs/parameter60_loss_20261028_v1`，2054688/start37969923、CPU54/7200秒；实际jobs/source/PLAN已绑定，完成后须执行review_saved并实际看图。
- 61仅恢复等待 `B/runtime/prepare_parameter61_20261028_v1`，2162225/start37988230、CPU53/14400秒。绑定原60三learner/archive，完整60审查并退出后才check-only；没有DECISION61、没有61训练。父/新cycle含补零映射逆变换/AST通过，无DECISION61真实调用拒绝。初次补零映射漏掉00060被逆变换检查拒绝，保留INITIAL_ADAPTATION_REJECTION，未启动错误脚本。
- 原59–61统计waiter4067967/start37570184继续，不自动派发训练或改变判据。若观察预算到期，先查真实进程及FINISHED，不因timeout重启科学任务。

Direct完整33已按原27–29 reward和29/32/33 loss接受经验数值收敛，Task/Strict仍0/0；`B/runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json` 的launch34=false保持，不能当任务成功。

## GPU守护及恢复注意

实际执行 `/tmp/sii_gpu_util_guard_20261028_v5`，共享源/证据 `B/runtime/gpu_util_guard_20261028_v5`。supervisor3256866/start37410686；GPU0/1 workers3256867/3256868 start37410690；GPU2 worker3256869/start37410691；GPU3 worker3256870/start37410693。新STOP不存在，旧v4 STOP刻意保留，禁止恢复v4。20ms周期、duty70–90%、控制目标70%。10:44即时79/71/71/75%，包含合成保活，不能保证每瞬时均≥50；历史09:03–09:04共同0%/D等待异常见GPUv5文档，不抹去。科学完成仍保持guard。

守护脱离当前对话运行，但不是重启服务，/tmp不跨系统重启。重新开机须先核对PID+start ticks和实际GPU状态再恢复，不能仅凭旧PID启动重复任务。

## 归档与下一步

本轮完整小证据包与逐成员校验收据见 [保存收据](RL_PARAMETER59_FROZEN55_COMPLETE_SAVE_20261028.json)，仓库证据 `docs/evidence/RL_PARAMETER59_FROZEN55_COMPLETE_20261028/MANIFEST.json`。大checkpoint/replay/raw仍在原共享SSD；HDD配额已满，只更新既有 `sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md` 入口，不声称HDD或arm1完整备份。

继续原60，不重启已经完成的59/冻结55。下一步审完整60、实际loss/配对/health及61恢复检查；必要时按原配置明确审定一个有限61，完成原59–61窗口并保留near-zero保护。原全部窗口和失败保留，不因某次局部改善宣称整体收敛。
