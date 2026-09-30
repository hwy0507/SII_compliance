# parameter6/direct7双模式训练链独立审查

状态：新wrapper/入口静态审查、10项独立合成测试和两份真实DGX proof离线审计均完成，详见末节。后续训练结果另行审计。本审查不启动仿真、不修改训练实现。

比较范围是共同potential reward、同DGX平台、各8192步、seed20260923的参数6维和直接7维策略。参数策略输出VMC调参请求，实际执行仍是action7。两者控制先验、隐状态及网络输出维度不同，配对预算不代表方法结构完全相同。名义K/D和其他VMC options只能取训练fixture并冻结到validation。

## 原基类与继承组合

- `Canonical48Env.reset()`先动态调用`self.close()`，之后才创建新队列与worker。新类的`close()`必须幂等、可处理尚无日志/adapter的首次reset；旧episode应先关闭并封存，再初始化新episode日志。`PotentialRewardEnv.reset()`从reset后的原始`self.obs`初始化potential前态。
- `PotentialRewardEnv.step()`调用父类执行实际action7，再覆盖旧reward。新双模式类应在该调用外层进行action6→action7转换和最终reward记录，不能绕过potential层，也不能把参数6维交给原基类的7维校验。
- 原基类`step()`非终端返回下一actor边界真实raw48；终端返回旧`self.obs`占位，`terminated=True,truncated=False`。新日志必须显式标记终端`next_observation_valid=false`，不得从审计专用状态拼出新的actor输入。终端potential=0，不使用该占位观测bootstrap。
- `QueuePolicy`收到动作后才把obs/action写进actor_trace。预算结束时最后一个Gym step已有真实next_obs，但worker在该边界等待下一动作，close发None使该next_obs未进入旧actor_trace。因此每个成功step应立即追加独立transition记录，不能依赖旧actor_trace重建partial最后reward。
- 原worker终端事件先入队，再执行finally写trace/清理；基类终端分支join后才返回。close超时必须作为失败，不得继续新worker或把部分运行记为完成。进程环境和loader由worker临时替换，仍只允许单进程单环境；训练双模式应隔离进程，不可同进程并发。
- 原基类会clip有限越界action7；新接口必须明确同样执行clip还是拒绝，并记录网络请求、实际执行请求以及最终action7，不能让日志动作与执行动作不一致。NaN/Inf/shape错误应在VMC状态变化及队列投递之前拒绝。
- 为新MJB验收改变旧worker强制SKIP_MODEL_ARCHIVE的行为时，应限于新独立运行函数，并固定来源hash及替换标记唯一性；不能修改既有冻结源或偷偷改变物理配置。

## 必要验收（未标记为已通过）

| 项目 | 必须提供的证据 |
|---|---|
| 新Gym零参数闭环 | 同训练fixture、完整600步；新Gym action6全零与原名义VMC的实际action7、raw48、所有physics/contact数组及MJB完全一致；记录并解释teacher分支元数据差异；不能只用旧ZeroParameterPolicy证明新队列链 |
| 两模式公共底座 | 相同fixture/spec、模型资产、执行器/WBC/安全/时序源hash、24s任务、25Hz动作、reward/gamma、PPO预算/优化参数；direct7的zero7不可冒称参数策略zero6 |
| reset | 首次reset、未开始step就close、partial后reset、terminal后reset、重复close；VMC滤波/offset/velocity/log_scale全部回初态；新日志无前episode行，potential前态对应本次raw初态 |
| 输入契约 | 两模式各自错误shape、NaN/Inf；超界请求处理明示；错误不能修改VMC/previous_action/potential前态或投递worker动作；raw48用于VMC且norm48仅用于网络 |
| 同源训练与验证 | 只从train选择名义options；验证不读取验证专属K/D来构造参数adapter；归一化只在训练更新、eval冻结；两模式分别保存其训练normalizer；不使用validation选checkpoint |
| 完整transition | step索引、raw prev/next48、next有效性、阶段仅reward元数据、requested及applied参数6/direct7、实际action7、K/D/logscale、实际返回reward与terms、terminated/truncated；不把reward专用阶段或审计量送入actor/critic |
| 终端 | 600步有限任务终止；terminalphi0，SB3done mask无terminalbootstrap；以真实最终gate/invalid/upstream重算基础奖励；占位next不伪装真实状态；终端步日志实际执行action与worker一致 |
| partial8192 | 若episode均600步，则13完整+392partial；新日志应有8192个实际reward、8192个transition，partial末真实next可验证；无终端基础奖励、保留非终端bootstrap语义；若不记录critic value/rollout buffer，不声称已验证实际SB3bootstrap |
| 最终产物 | 固定最后8192 checkpoint、model.zip元信息8192、normalizer与manifest SHA、COMPLETE无FAILED、冻结源码及资产未变；保留失败episode，不按结果重选 |

实际Gym返回reward可与独立公式逐transition核对；完整episode检查telescoping，partial检查包含最后真实next的prefix identity。Float64环境reward与VecEnv float32训练reward的差别应单列。记录实际Gymreward不等于证明SB3的advantages/critic values完全正确。

## 新wrapper第一轮只读审查

已完整检查`scripts/canonical48_paired_rl_env_20260924.py`的初版147行：

- `PairedControlEnv`是独立`gym.Wrapper`，包裹`PotentialArchiveEnv`。外层close不会被内层reset动态调度，避开新增journal与旧继承初始化次序冲突；旧worker仍先结束，再reset控制器和新建journal。
- action6从`self.env.obs`原始float64取wrench，调用固定训练options的VMC后将action7交给共同potential层；direct7走同一个底层。外层Box clip后记录边界request与applied，并注明SB3先前可能已clip原始Gaussian样本。
- 原基类源码不变，私有run_episode仅替换一次MJB archive开关；模型仍由相同create_environment产生。原panel runner以字符串等于`'1'`跳过存档，故设`'0'`可实际恢复MJB，不是环境变量“非空即真”的错误。
- 每个完成step记录原始prev/next、实际reward/terms、参数与执行动作；terminal明确valid=false，partial保留实际next。完整episode的journal在返回之前关闭，partial由close关闭。JSONL行缓冲使正常退出/进程中断时可恢复已提交行，但没有fsync，不宜宣称系统断电耐久性。

第一轮未发现阻断性实现缺陷；这只是静态结论。测试尚未检查，真实闭环proof尚未核验。建议训练入口把日志`execution_action`与原actor_trace逐项核对，既验证因果对齐也检测未来底层clip行为变化。错误worker事件或journal写入失败必须令运行FAILED，不可据已存在checkpoint将运行标COMPLETE。

## 入口审查与独立审计工具

已只读检查`tools/run_canonical48_paired_ppo_20260924.py`：proof直接执行新Gym类600步，与既有名义VMC（parameter6）或同源直接zero7（direct7）比较全部物理/接触/rollout数组及MJB；训练前要求两个proof齐全且source/options匹配。初次审查提出还需验证proof目录mode和fixture/assets/runtime同源；实现者已增加COMPLETE/PARITY/manifest mode一致、fixture_specs/asset_hashes/runtime/device/protocol hash逐项一致。固定8192最终模型、训练归一化冻结、网络参数量披露及源/资产结束复核均在入口中。未发现剩余阻断性静态缺陷；真实DGX proof仍待核验。

新wrapper的合成测试已只读检查，覆盖raw float64而非网络float32、训练options固定、两模式partial next与action日志、terminal占位、首次/partial/terminal reset、零步close/重复close、非法shape/NaN/Inf、越界clip。实现者报告其相关测试32项通过；本审查未把这些合成结果当作物理闭环证据。

本审查另外实现独立工具`tools/audit_paired_transitions_20260924.py`及`tests/test_paired_transition_audit_20260924.py`，本机纯离线测试10项通过。工具用manifest校验指定snapshot每一项源hash，核episode contract base bridge hash与训练options；从冻结源码AST仅取potential、VMC数值类及pure evaluator，不导入MuJoCo、不使用可变当前实现冒充冻结实现。随后检查：

- JSONL和NPZ全字段逐值相同且finite；原actor_trace的raw obs/action/phase逐值一致；step索引与25Hz周期、next前后相接、terminal/partial标记正确。
- 用固定训练options从reset开始重播参数VMC，核每步请求、logscale、K/D及action7；direct7核clip和inactive参数元数据。数值重播容差rtol=atol=1e−12，并报告最大误差，原日志对齐要求精确。
- 每个实际Gymreward和terms由冻结potential函数重新计算，完整及partial的折扣恒等式包含最后一条实际奖励与真实partial next；terminal next仅作已标记占位。
- 若存在训练callback，则核每步收到的VecEnvfloat32奖励与对应Gymfloat64转换精确一致及done/order/terms。未记录critic/advantages，不声称验证实际bootstrap值。

10项测试包含两mode×终端/partial、同步篡改JSONL/NPZ中的reward/KD/partial末next/validity、单独篡改actor_trace、冻结源hash不匹配、改用非训练nominal options。损坏例均被拒绝。真实proof归档仍须实际运行此工具；其CLI为`--run RUN --snapshot FROZEN_SOURCE --output FRESH_AUDIT.json`。

## 真实DGX proof归档审计结果

两模式完整proof归档到`outputs/paired_parameter_action_20260924_r1_archive`后，已直接使用其中只读`source/tools/audit_paired_transitions_20260924.py`对各自proof运行，未修改snapshot：

| proof | 实际transition | 核验源文件 | reward/terms最大误差 | 控制器重播最大误差 | telescoping残差 | 证据 |
|---|---:|---:|---:|---:|---:|---|
| parameter6 zero6 | 600 | 163 | 2.22e−16 | 2.22e−16 | 7.22e−16 | docs/evidence/paired_gym_20260924/parameter6_transition_audit.json |
| direct7 zero7 | 600 | 163 | 3.33e−16 | 0 | 6.94e−17 | docs/evidence/paired_gym_20260924/direct7_transition_audit.json |

两份JSONL/NPZ/原actor_trace的obs/action/phase均精确对齐，终端占位valid=false正确。parameter6解析名义VMC本次task/gate通过，direct7零执行动作本次失败；这两者控制含义不同，proof只用于接口验收，不能视为学到的策略对比。proof未训练，没有SB3 callback日志，因此此处未声称已验证实际训练buffer奖励；后续训练归档再由同一审计器核对float32 callback。两proof完成且独立审计通过的消息已发送主agent及训练实现agent。
