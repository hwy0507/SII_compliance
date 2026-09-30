# parameter6/direct7新Gym完整闭环验收结果

两模式完整24s/600步Gym验收均通过，独立transition审计也通过。原名义VMC、直接zero7参考以及两份新Gym记录的MJB共同SHA256为`9f220b70f721aba1cec9c86d53fc2e2ec748736034a47a8a9c44951684492288`。未改物理、安全、gate或原source。

| 验收 | 参考 | 原始比较 | task / accepted_panel_demo |
|---|---|---|---|
| parameter6持续zero6 | 原DGX已归档nominal VMC | 24项原始数组检查按预声明逐值完全一致，teacher_action核对A.teacher=B.action且B.teacher=0 | 两者true / true |
| direct7持续zero7 | 同源直接zero7注入的完整24s参考 | 27项数组，包括actor_trace、rollout、physics、contact全部逐值完全一致 | 两者false / false |

所有数组先检查有限值，不接受共同NaN。JSON仅允许预声明的controller/teacher分支标签及输出路径差异，contact四个源码明确set字段排序后比较全部数值；没有事后排除动态字段。parameter6与direct7本身不是同一控制律，上表只证明各自Gym桥接正确，不是训练策略比较。

两模式manifest逐项核对163份执行源hash、134个模型资产hash、训练/验证fixture规格、nominal options、软件runtime/device及协议hash全相同。验收使用CPU0/1，只有亲和核和mode/action维度等预声明字段不同。完整本地归档`outputs/paired_parameter_action_20260924_r1_archive`已与服务器checksum dry-run核对无内容差异。

独立agent使用归档snapshot内的审计器，在本机纯离线重放600步控制器及reward，未导入仿真。JSONL/NPZ/actor及阶段逐值精确一致，terminal next placeholder的valid=false正确。参数模式controller与reward最大重放差各2.22e−16、势差恒等式残差7.22e−16；直接模式action误差0、reward最大差3.33e−16、势差残差6.94e−17。报告：`docs/evidence/paired_gym_20260924/parameter6_transition_audit.json`及`direct7_transition_audit.json`。

42项必要纯合成测试通过；主agent整套172项通过。另两模式真实DummyVecEnv/VecNormalize/PairedProgress合成4步smoke验证自动reset、终端done、partial末next及实际SB3 float32 reward转换，无MuJoCo、无神经网络训练。完整proof没有预算partial，partial实际8192末尾审计仍须在训练完成后执行，不能把合成测试冒称真实partial结果。

冻结关键SHA256：新Gym`df37f7fb5aae99e2d430fb4fd3fbad218bf0716513bf961a8f3ca03af3e5482b`；训练入口`64b7c0dc315e25094c4e658d5e5193e82c8f7acd59f9de05db161663500b76cf`；独立审计器`18864571f15baef61e3faf989ce2ba86961694631ce78730b4362609db27dff6`；总协议`d14cf2545489475f41ea407235cf0e21be6b109120d8506c2c10ace38f6174d3`。已冻结VMC adapter与potential reward未改变。

验收通过后，主agent已有条件授权生效，两分支8192训练已按`PAIRED_TRAINING_LAUNCH_20260924.md`独立启动：CPU5/6、同CUDA、各单环境单线程、7200s上限。训练成功/失败尚待最终产物，不从名义zero6任务成功推导学习收益。
