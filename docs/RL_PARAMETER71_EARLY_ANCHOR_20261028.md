# 参数71早期检查、全2124终端基准与72仅恢复准备

2026-10-28 22:40 UTC。Goal active。承接[完整70审查与准确71启动](RL_PARAMETER70_COMPLETE_20261028.md)。原71继续，尚无完整71或整体收敛结论；Direct33原训练条件已有经验数值收敛判断，Task/Strict仍0/0，不启动Direct34。

## 当前运行

计算主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `env/bin/python`。22:40:40快照：impedance/admittance/vmc steps2935125/2935765/2936796，每路30sampler，原身份均live，无完整/失败。固定30×55秒、41250新交互、4m append replay、原23/47标记、terminal128、batch65536、UTD1及原LR/mask/reward/物理/gate不变。

|任务|PID / start ticks|状态|
|---|---|---|
|71 impedance|2902207 / 42203070|运行|
|71 admittance|2902208 / 42203070|运行|
|71 VMC|2902211 / 42203070|运行|
|71 archive|2902216 / 42203071|等待完整科学输入|
|71全loss|2909138 / 42204909|PLAN000ce694，原等待器|
|原71–73窗口|2909145 / 42204920|PLANc160b5d6，原等待器|
|71全标签|3168755 / 42251130|PLAN21e7dbe4，已部署|
|71 VMC终端|3247685 / 42265260|PLAN9a5d6cc1，已部署|
|71导纳终端|3247693 / 42265262|PLAN03249f57，已部署|
|72仅恢复|3191936 / 42255080|REG3e3d2ecc，无72训练|

行动前核PID/start ticks/源hash/输出，不凭旧PID重复启动。全部精确hash与命令见[证据manifest](evidence/RL_PARAMETER71_EARLY_ANCHOR_20261028/MANIFEST.json)。

## 71前5000更新

三路原日志前缀逐字节保持、步号连续、全数值有限、独立标量复算通过，实际loss.png已查看。登记发生在前缀可用之后，非前瞻注册。

|路|critic首1000→末1000|critic最大值|actor首1000→末1000|
|---|---|---|---|
|I|1.762973287→1.710394800|15.837354660|26.388200737→26.423793169|
|A|1.420316279→1.428642462|19.473249435|−8.770751721→−8.779608354|
|V|1.327330528→1.174746798|24.339267731|−12.943229807→−12.956655347|

I critic中段上升后回落、actor略升；A近似平但末段稍升；V起始较高后下降，三路有限尖峰保留。仅早期前缀，不代替完整loss、temperature、reward稳定性或收敛。SAVED_REVIEW的plot_inspected=false是算术审查当时状态，后续实际图审以PLOT_INSPECTION.json为准，不改历史收据。

## 全2124终端基准与审查部署

从已核完整70保存值提取V/A全2124×57 features及Q/reward/mask/indices，独立数组和标量复算全部精确；0新前向/物理/优化更新。V全2124 SSE10788.124347762961，anchor SHA1d2770433e8053e8b7d76f6ce15b46b9156308df8bff0a65c17ad7f4e5a9b7c1；A8555.136404615867，SHA0f56139d66de3f9bc066adb01eac3a3c562920097673004c547a1de2a21c2c67。包含70新增30，不能与70审查的旧2094 SSE混用。

71完成后比较全部2124旧终端与新增30（总2154），保留两个分母。原V五focus[2050526,2299142,2046571,2423133,2423122]、A原66short0600/index2752093及历史58/66背景保持。capture绑定完整70 checkpoint V b3090ced/A e27f42cb；五源同时周期与行数映射，保护完整hash、逆变换/AST/diff/输入hash核验。两个终端waiter CPU53/7200秒，等待完整71与原learner退出，无自动训练。

标签通用audit_labels.py SHA77e985c2逐字节保持，wait71/review_labels71映射核验通过。实际不完整71调用拒绝Incomplete cycle 71，非零且无COMPLETE70_71输出。完整后须独立审查180标签与90reward对，review_labels71依赖完整loss SAVED_REVIEW，当前不提前pass。

## 72仅恢复与原收敛约定

runtime/prepare_parameter72_20261028_v1四脚本周期映射，保留原68–70完整审查路径；通用wait_prepare SHA c4617a04逐字节一致。完整71审查和原learner退出后才运行全state/replay/下一65536 check-only。真实缺DECISION72启动拒绝，未创建72训练；没有自动72。launcher额外绑定准确current_window71_73_plan及cycles[71,72,73]，不要求尚未来到的73结果才能启动72，也不新增科学阈值。

已重读原RL_SPT_TRAINING_HANDOFF_20261025.md收敛段：先历史改善，再末3轮均值变化≤5%、斜率/不确定性和数值/temperature健康；近零均值不能用CV下结论。近零1保护限制百分比证据的解释，不是要求将reward推离零的新训练目标。原68–70 I/A未过结论及全部历史保持；该窗确有大幅均值变化，不追溯改判。原71–73仍按已登记5%/近零1/seed2026102855/5000/anchor55计算，若近零保护触发需如实报告并结合完整历史解释，不能静默修改窗口/阈值或提前宣称收敛。任务成功率与数值稳定分开报告。

## GPU与保存

用户要求全部科研完成后仍保留GPU负载。v5 supervisor3256866/start37410686及四worker3256867–3256870身份保持，STOP/FAILURE不存在；约5秒采样，低于65%增加保载。22:30:13–22:40:38共123样本，四卡最低76/59/65/62%，均值85.7398/88.4878/89.2114/88.7967%，低于50计数全0，最大间隔5.279656秒。含合成占用，不等于科学吞吐或每瞬时保证。科学结束不停止，当前保载不是跨重启服务。

共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER71_EARLY_ANCHOR_20261028_224142/SMALL_EVIDENCE.tar.gz`，96成员/1912551字节，SHA256 `084fec7883cc7b1718d32293a5f34980f08629761b7e9dee5bd84756115d126e`，逐成员字节/Python AST核验。[收据](RL_PARAMETER71_EARLY_ANCHOR_20261028_SAVE.json)。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；HDD配额满，只缩短重写现有入口。

本轮起始main6951a569/baselinef6e8f8c已fetch/read；保存前再次fetch/read main d36a7990594c31d7536f4e3aa9bfb0066b504b29、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，安全fast-forward保留非RL75拟合/18闭环工作，不操作其进程。遵循sii-research-sync，无子agent。

下一步保持原71及guard；完整71后审archive/health/full loss、独立算术/实际图、全部标签、两终端数组/图，再根据完整证据决定有限72。原71–73不变，所有有界观察超时都不是科学重启授权。72 full-loss准备尚未部署。
