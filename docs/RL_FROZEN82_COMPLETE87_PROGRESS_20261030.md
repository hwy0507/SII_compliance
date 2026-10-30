# 冻结82完整90回合已审；原87与冻结86多seed继续

2026-10-30T13:51:33.606090+00:00，Goal active。冻结82三方法全30/共90回合已完成，全部55秒、123750动作/9900万子步；完整learner/replay最终不变、原动作native重放/physical/filter/torque、全保存raw独立复核、55→82全部90配对和两张实际图均已核。该完成不等于训练收敛或最终泛化；原87继续，steps `{'impedance': 3597197, 'admittance': 3599489, 'vmc': 3601331}`，冻结86固定16回合继续，无自动88/Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮实际ls-remote、fetch/read main `80e94020d78a3df407541a8c547ff1e9ca56994a` /baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按仓库sii-research-sync发布，保留他主机非RL，无子agent。源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/frozen82_completion_review_20261030_v1`，原评测 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter82_frozen_full30_20261030_v1`。

## 完整冻结82与相同seed55→82比较

原PRE_REGISTRATION SHA `baf37d1715635e1d5352deea7434b33e36e666c4c0d3036f43f404b685935b76`，evaluation PLAN SHA `12359f695a69fa03579ab0515ce8c2cbfb8ecf47b5dc0200240bda3046b97783`，动作seed2026102638、全部30原开发训练条件保持。三路每路41250动作/3300万子步，0优化器更新、0replay追加，全部有限完整55s、无abort。所有原evaluator自然完成，旧PROGRESS是末次周期进度、最终以FINISHED为准，不重启。

|方法|mean reward55→82|Task55→82/30|Strict55→82/30|机器判据违规55→82|
|---|---|---|---|---|
|impedance|-0.566896182→-2.380834508|18→18|18→17|0→1|
|admittance|-13.654079407→-8.484269994|13→14|11→14|2→0|
|vmc|-2.862454262→-2.806293129|17→17|17→17|0→0|

- impedance: Task增加[]、减少[]；Strict增加[]、减少['active_short_train_0100']。均值差-1.813938326，标签改变条件贡献-1.812742119，标签未变贡献-0.001196208；原reward标量重建最大误差1.07e-14。
- admittance: Task增加['active_long_train_0200', 'active_long_train_0300']、减少['active_long_train_0500']；Strict增加['active_short_train_0100', 'active_short_train_0600', 'active_long_train_0200', 'active_long_train_0300']、减少['active_long_train_0500']。均值差5.169809414，标签改变条件贡献5.147656837，标签未变贡献0.022152577；原reward标量重建最大误差1.07e-14。
- vmc: Task增加[]、减少[]；Strict增加[]、减少[]。均值差0.056161133，标签改变条件贡献0.000000000，标签未变贡献0.056161133；原reward标量重建最大误差1.07e-14。

阻抗short0100外穿透0.154178→0.202805mm，越过原0.2mm线，Task仍真但Strict失败；导纳long0500由成功变为lift阶段失败，外穿透0.040687→0.045634mm，该任务退化不是跨越0.2mm门。

全90条件均保留，全部条件的回报差之和/30与两个端点均值差独立一致；标签分组贡献只是算术，不分解随机性与学习变化的历史因果。55与82动作seed/condition fixture/模型/物理dt/actor period/horizon/reference/torque阈值/reward均一致，但训练暴露量不同、包含partial75历史，不能当相等预算或独立training-seed试验。

完整独立保存审计 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter82_frozen_full_saved_audit_20261030_v1` 逐原始文件hash、9900万子步dt5e-5/有限值、实际接触时长/舒适分母/关节峰矩/穿透量、全部123750动作journal重算reward/Task/Strict/安全标签，与原review一致。该审计没有新physics/forward/update，复用原evaluator完整内存不变和原native-action重放收据；不声称在退出后重算其已不存在的内存。

- impedance: 55接触130.551100s、82接触131.227650s；contact-only比例55=0.16279027905548102、82=0.22327459190193547（None即NA）。
- admittance: 55接触77.699900s、82接触74.221450s；contact-only比例55=0.7288741684352231、82=0.7669817822206384（None即NA）。
- vmc: 55接触97.901700s、82接触97.418300s；contact-only比例55=0.6901688121861007、82=0.7398245504181451（None即NA）。

无接触为NA，不以低力矩空闲替代舒适，也不平均每回合舒适比例。两张实际图：原 `frozen_full30_results.png` 与新 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/frozen82_completion_review_20261030_v1/frozen55_82_all90_pairs.png`，全部90返回差和55/82外穿透、原0.2mm线已目视核对，证据见各PLOT_INSPECTION。

- impedance: checkpoint `e5ecda2add46cef31c43d1fc1c4eaf127c25927ada73da16de3cf40c06726c76`，initial=final learner digest `19c27c3792cd06067f042fd455d92306b82634f42c2fd6c6f8255a8c8ffffd1d`。
- admittance: checkpoint `cfde4b502b22e85eb08f2187bc868763ff4ddf0724bea981e88d759974d6c02b`，initial=final learner digest `29b86408725e96d7bbdc5c6c6f1bdf30020a0fec9afb9794a25692dfa1657bc6`。
- vmc: checkpoint `4d21592f534f9f1ee475561d8fbfb914d86a488027691be28022939119a10ae8`，initial=final learner digest `a049d24541cceee28057411707bc23d647e1bdcc5e635ce4d4104b79fdf9ae85`。

## 原87与固定2514后续

原87每方法最多41250新增、30条件×最多55秒、4m append-only、历史23/47、terminal128/batch65536/UTD1及原LR/reward/masks/physics/filter/gates保持。PID2291679/80/81 start573936642；原archive/loss/labels/两终端后续继续，完整87仍待。85—87原PLAN SHA6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e、seed2026102858、5000bootstrap/nearzero1/5%/anchor55/原4h截止不改；A/V 85→86相邻已超5%，87不能追认该窗口通过。

在完整87之前登记同一2514旧终端/all5critic的84/85/86/87跟踪 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery84_87_fixed_terminal_critic_followup_20261030_v1`，PLAN SHA `7cb97319d8b3cb10e862ebb1ada6dbfe79d97b87cc04035facd3be04d348346d`，等待PID `1474` /start `574170896`。已验证旧2514 inputs/actions/rewards/masks与当前86anchor前缀精确一致，当前anchor2574、预测87共2604，全部5critic旧86值逐位一致；真实缺完整87执行被正确拒绝。

此跟踪只汇总既有两终端审计的保存预测，0新forward/physics/update，保留全部旧样本与30新84cohort，检查VMC86改善及Acritic4回归是否持续。沿用原87monitor+14400截止，不延长原85—87统计窗口、不新增健康门槛、无自动88。完整87后需结合全loss/health/标签/固定群体和完整窗口决定是否独立登记训练修订。

## 冻结86动作seed诊断与其他范围

上一轮登记的完整86四组合×四动作seed固定16回合继续，PLAN SHA42dc5ea17bbcde872335568ca6c02da16f42620500b8a6d31b9021bc43fd8234，不改预算/源/seed。当前保存(已完成回合,seed,在途动作) `{'impedance_short0600': (3, 2026102636, 700), 'admittance_short0900': (2, 2026102635, 1100), 'admittance_long0200': (2, 2026102635, 800), 'vmc_short0000': (3, 2026102636, 300)}`。完整16/最终全state证明/独立saved图仍待；不能只用部分seed判断当前策略稳定。既有冻结29敏感性证据/原12回合结束状态保持，不宣称首次发现随机性。

Direct33数值阶段已接受，冻结30 Task/Strict0/0，无Direct34；中断28缺最终内存不变证明保留。指定ESN仍缺，不替换他主机模型、不重复追问。partial75与原74—76不可判、原76—78/79—81/82—84结论及79真实安全中止均保留；完整85历史重建只是数据可行性，无actor输入修订。

本轮完成观察19样本/540.195秒，原34进程身份保持live或合法完成；最后另核新fixed87等待，共35身份。观察器自然结束不重启科学。GPU原v7守护保持，科学结束仍合成保载，180样本min `[64, 66, 63, 68]`%、低于50次数 `[0, 0, 0, 0]`，末值 `[80, 70, 73, 96]`%。合成利用率不是科学吞吐；历史预热0及GPU0=31/GPU2=33/44低谷保留，不保证采样间每瞬时，非重启自启服务。

小证据SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_FROZEN82_COMPLETE87_PROGRESS_20261030/SMALL_EVIDENCE.tar.gz`，317成员/845408字节，SHA256 `dc7bb2407474d92c7a72aa50478cfd6ca28a63cda128640ff90825ff415e70c0`；逐tar成员字节/源码AST已核，Git index/commit字节另核。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份，HDD LATEST保持254字节原位更新。运行日志为快照，成功push及后续实际远端核验见SSD本包PUBLICATION.json。
