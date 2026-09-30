# train-only VMC示范用于canonical48/direct7 SAC/RLPD：离线可行性

可以工程化复用这条新transition轨迹，且已完成数据导出；当前仅为数据准备，没有训练SAC/RLPD，也没有复现论文。来源是实验前按manifest顺序固定的训练fixture `push_00000`，由解析名义VMC执行全零parameter6请求产生的全部600步。它本次task/gate均通过，但导出不以成功为筛选条件，未读取validation/test轨迹，不使用旧imitation NPZ补造reward或终止标记。

源目录：`outputs/paired_parameter_action_20260924_r1_archive/proof/parameter6/gym/episode_00000`。独立证据：`docs/evidence/paired_gym_20260924/parameter6_transition_audit.json`，163项冻结源hash、600条journal/actor精确对齐；VMC动作重播最大误差2.22e−16，实际reward重算最大误差2.22e−16，完整折扣恒等式残差7.22e−16。对应direct7接口proof也已独立通过，证据为同目录`direct7_transition_audit.json`。

## 已生成数据与契约

当前应使用`outputs/train_only_action7_demo_20260924_r2/`：`demonstration.npz`、`reward_audit_only.npz`和完整`manifest.json`。导出工具`tools/export_train_demo_20260924.py`固定接受上述预选proof的manifest SHA，再复核独立audit并重新运行原冻结审计器，核验后导出全部600条，无结果筛选。原snapshot与r1数据/manifest未改动。

| 字段 | 含义与入buffer规则 |
|---|---|
| observations / next_observations | 原始SI单位canonical48，float64→float32，形状600×48；没有预归一化 |
| actions_execution | 实际执行的action7，600×7；绝不是全零的policy_action6 |
| actions_sac | 与真实SB3 `policy.scale_action`逐值一致：所有轴统一用float32表达式`2*((action-low)/(high-low))-1`；slowdown数学上映射为`2*a0−1`，yield数学上是恒等映射，但保留统一表达式的实际舍入 |
| rewards | 已审计的实际Gymreward转float32，600×1；保持potential gamma=.995，未来不可换目标后仍当作同一reward |
| dones / timeouts | 最后一条done=1，其余0；timeouts全部0；对应`terminated=True,truncated=False` |
| next_observation_valid | 前599条true，最后一条false；末next是原末obs占位，非末态物理观测 |
| reward_audit_only.npz | stage/next_stage与potential terms仅作奖励来源审计，禁止拼入actor/critic输入 |

第600条可以保留在SAC buffer，因为done=1且timeout=0使TD target停止bootstrap，其最终reward仍有效。必须保持此语义；若将其误标为TimeLimit.truncated、把done清零或对该占位next bootstrap，数据就不合法。占位值有限，可供普通批计算，但不能用于动力学预测或宣称具有真实终端next。

float32转换最大绝对误差：obs/next约2.274e−7，execution action约2.706e−8，reward约1.925e−7；r2使用真实SB3表达式的SAC动作scale/unscale float32往返误差约5.96e−8。原始float64证据保留在proof，导出manifest记录这些误差、全部来源hash和输出hash。

r1直接保留yield数值，数学上等价，却未逐位复现SB3的float32加减/除法。对本机真实SB3 2.9.0 `BasePolicy.scale_action`核验600×7个动作后，r1有3349个yield元素与其结果不同，最大差5.960464477539063e−8，slowdown没有差异。r2已修正为全部轴统一表达式，并与真实SB3逐值一致；其余obs/next、实际执行动作、reward、done/timeout/validmask与r1完全相同。这是数据导入接口舍入修正，不改变原执行行为或reward。证据：`docs/evidence/paired_gym_20260924/demo_r2_sb3_scale_action_verification.json`。r1及原manifest完整保留，SHA仍为`a71f780c632ffde22271501adbd4151d7adec58eab08a1f2fceb9fd4f7afd509`。

## 归一化与下一步工程边界

已只读核本机SB3的`common/off_policy_algorithm.py`与`common/buffers.py`：off-policy buffer存raw observation/reward与scaled action，sample时才使用VecNormalize的统计量归一化。示范应以本文件raw float32写入buffer，再与online raw样本走同一采样归一化流程，禁止先离线normalize后再normalize一次。`norm_reward=False`保留既定reward量纲。未来要事先确定obs_rms仅由在线train数据拟合，还是允许以这600条train demo初始化；两种都不能从validation/test更新，本导出器未拟合任何统计量。不能无说明地复用PPO已训练normalizer作为新SAC的数据先验。

下一步只需在独立的新SAC/direct7训练入口接入这份数据，验证replay action缩放、末done/timeout和raw→normalized采样，再预注册online预算、demo采样比例、更新次数、随机种子及固定最终checkpoint规则。标准SB3 SAC不等同RLPD；要声称RLPD还需落实并说明其offline/online采样、critic集成与更新设计，不能把SAC简单预填buffer改名为论文复现。单条示范的覆盖有限，当前数据准备不保证学习成功或泛化。

额外数据预算必须披露：若未来仍训练8192步online，示范方案具有8192+600=8792条独特可用transition，online-only方案只有8192条。600条示范虽复用既有proof、不增加本次仿真，也仍是额外训练数据；重复replay采样次数和梯度更新预算须另列，不能称同总数据量比较。

验证：9个纯离线导出测试通过，覆盖真实SB3的小数值yield/所有轴float32逐值缩放、完整reward保留，以及错误使用零6动作、timeout、缺失终止、错误next mask、非有限值、越界action和非零参数请求的拒绝。r2真实导出成功后manifest SHA256为`9f9092c03abcbf80cbf3e036552fbd9d6a214cdd21af8dded5eed1c402eb0a56`。

## 真实SB3 replay接口验收（2026-09-24追加）

`tools/verify_train_demo_replay_20260924.py`已在本机SB3 2.9.0上把上述固定r2全部600条写入真实`ReplayBuffer`，再通过真实`_get_samples`指定全索引取出，避免随机抽样漏掉最后终态。raw obs/next、scaled action、reward、done和timeout入库逐值相同；sample obs/next仅归一化一次，reward保持原值。最后done=1、timeout=0，`1-done`恰与原next-valid掩码相同，明确禁用终态占位的bootstrap。

校验采用人为固定的非恒等均值/方差，未用示范或validation/test拟合统计；取样前后统计完全不变。占位环境的reset/step均设置为报错，实际仿真步数和梯度更新数均为0。本项仅证明标准SB3 replay预填与归一化接口可行，未实现RLPD的50/50采样，也未运行SAC训练或核验其实际TD梯度。证据为`docs/evidence/paired_gym_20260924/demo_r2_real_replay_verification.json`；工具SHA256 `a32465871d053f3bd0ce00df8011ace7d490a0fc379a3c13b976b27205fd8f66`。
