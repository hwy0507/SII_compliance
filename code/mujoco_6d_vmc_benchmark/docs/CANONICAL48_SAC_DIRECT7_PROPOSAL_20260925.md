# canonical48/direct7 SAC：实施前具体方案

状态：具体方案已审查，独立入口及离线验收已实现，等待最终代码review和只读source冻结。未开始SAC物理仿真、正式训练或新物理评估；测试使用合成数据做了真实SB3梯度更新，不能当作机器人学习结果。本方案是标准SAC及其示范预填对照，不称RLPD或任何2024年后论文的完整复现。

## 问题、对照与冻结条件

以已有`PairedControlEnv(mode='direct7')`原接口，比较标准SAC online-only与标准SAC加固定train-only示范预填；两者均使用seed20260923、8192真实在线transition，并固定最终模型。仅在原canonical首个train fixture `push_00000`学习，物理seed800、rod高度0.65m、原WBC/安全链、action7含义和潜势奖励`push4_gate_potential_v1`均不变。训练和评估的完整fixture、资产、原执行源与reward协议hash须匹配原配对PPO证据；不能因SAC失败变更gate或挑选中间checkpoint。

actor/critic仍为canonical48，无stage、privileged state或reward terms输入；critic在标准SAC中另外接收七维动作。动作第一维slowdown在[0,1]，其余六维yield在[-1,1]。此分支不加入VMC解析动作后端。潜势的gamma和SAC的gamma共同固定为.995；这改变了SB3默认gamma=.99，须显式传入。

| 项目 | online-only | demo-prefill |
|---|---|---|
| 新在线transition | 8192 | 8192 |
| 额外既有示范 | 0 | 固定r2全部600条 |
| 可用transition总数 | 8192 | 8792 |
| offline预训练 | 0 | 0 |
| warmup | 前100在线步均匀动作采样 | 相同 |
| 更新开始 | 完成第101在线步之后 | 相同，不因预填提前 |
| replay | 标准均匀有放回采样 | 相同，不用50/50或优先采样 |
| obs_rms | 仅本run在线训练reset/step | 相同，不用demo初始化 |

示范只接受`outputs/train_only_action7_demo_20260924_r2/manifest.json`的SHA256 `9f9092c03abcbf80cbf3e036552fbd9d6a214cdd21af8dded5eed1c402eb0a56`，并核其两个NPZ和来源audit。600条为事先固定的train nominal-VMC zero6 proof的全部动作，使用实际`execution_action7`，不以成功筛选、不掺validation/test。online-only也核来源协议，但不读取示范到训练buffer。

## 已核本机SB3 2.9.0的明确设置

直接只读核对本机`stable_baselines3/sac/sac.py`、`sac/policies.py`、`common/off_policy_algorithm.py`；运行前须再核目标环境版本和实现hash，不能仅凭版本字符串宣称字节相同。

| 设置 | 固定值 |
|---|---|
| policy | MlpPolicy，actor与每个Q均[256,256] ReLU |
| critic | 2个Q，target twin Q；独立actor/critic features |
| optimizer | Adam，固定learning_rate=3e-4，默认optimizer kwargs |
| buffer_size / n_envs | 1,000,000 / 1 |
| learning_starts / batch_size | 100 / 256 |
| gamma / tau | .995 / .005 |
| train_freq / gradient_steps | 每在线步一次 / 1 |
| n_steps | 1，不用多步回报buffer |
| ent_coef | auto，初始alpha=1.0 |
| target_entropy | auto，对7维得到-7 |
| target_update_interval | 1 |
| action_noise / use_sde | None / False |
| optimize_memory_usage | False |
| handle_timeout_termination | True；本任务全部timeout=0 |
| VecNormalize | norm_obs=True、norm_reward=False、clip_obs=12，其他默认值显式记入manifest |

`log_std_init=-3`是policy构造默认项，但`use_sde=False`时不能把它解释为PPO式的全局固定初始log标准差：SAC实际使用观测相关的log_std线性头，后续按实现clip。不复用PPO `log_std_init=-2`或PPO归一化状态，不额外改actor偏置。SAC归一化动作坐标0对应slowdown=.5；PPO的环境动作坐标0对应slowdown=0，两算法动作分布/初始化先验并不相同。

完整8192在线步时，SB3条件`num_timesteps > learning_starts`产生8092次train迭代。每次分别更新alpha、twin-Q共同critic optimizer和actor，再更新target；记录实际`_n_updates`与各optimizer step计数，不能只按公式填表。每支预期采样2,071,552个replay条目（包含重复），而原PPO为384个epoch更新、每次64条且有独立on-policy机制。两者相同在线互动预算，但网络大小、离线数据和梯度预算不同，不称等计算预算算法消融。

预填后无覆盖，在线第t步的示范采样期望比例为600/(600+t)，实际比例须记录；第一更新约600/701，最终约600/8792。采样的实现保持标准均匀采样，不承诺每batch恰有该比例。

## 最小实施及可审计边界

新增独立SAC入口、audit replay辅助模块与纯离线测试；不改旧snapshot、PPO入口、PairedControlEnv或底层物理。新运行snapshot包含冻结原执行源、明确新增模块及hash、协议、proof、fixture/资产、r2示范及其hash。优先同DGX既有runtime/device，以免将本机/服务器差异混入算法对照；最终主机和资源槽位由统一队列在启动前写死，不与现有25项部署争抢超出原并发上限。

1. 普通`SAC`使用只加记录/断言的`ReplayBuffer`子类，保留标准`add`和`_get_samples`逻辑。`add`先记入参，再调用`super().add`，之后读刚写入槽位的实际obs/next/action/reward/done/timeout；写durable journal并逐项验证。不能用callback日志代替实际replay验证：SB3的callback发生在`_store_transition`之前。
2. 训练callback另存真实`buffer_actions`、已发送的环境`actions`、Gym float64 reward与SB3 float32 reward及done。核实际buffer action精确等于该步`buffer_actions`；核`policy.unscale_action(buffer_actions)`精确等于传给env的动作。不能要求将已执行float32动作重新scale一定逐位回到原buffer action，浮点往返可能改变位。PairedControlEnv原contract中“Gaussian sample”是PPO文案，新SAC manifest明确上述真实动作边界，原源保持不变。
3. r2示范直接将raw float32 obs/next、实际`actions_sac`和reward/done写入同一个真实buffer。保存数据来源标签和索引0..599；后续在线插入从600开始。`_get_samples(batch_inds)`只记录既有索引及demo数量，再调用原实现，不增加随机抽样或改变RNG状态。replay最终保存全部已占用槽位及来源掩码、实际size/pos、源hash；不把大容量未填充零槽当作训练数据。
4. 训练统计只由本run VecNormalize的online reset/step更新，包括自动reset观测；示范预填/采样不能改obs_rms。保存初始、checkpoint、最终统计和count。replay存raw，sample时只归一化一次，reward不归一化。每次采样记录obs_rms快照标识；validation时`training=False`，不引入PPO统计或任何验证统计。
5. 真实终态next本来不存在。Gym已保存`next_observation_valid=False`且terminated=True；SB3会normalize再unnormalize其terminal占位，可能有float32/clip差异。审计须记录实际buffer terminal next，明确为无效占位，严格done=1、timeout=0及TD bootstrap mask=0，不假装它精确是真实末态。所有非终态next必须与Gym原raw转float32精确相同；预算最后partial必须保留真实next、done=0，不当作终态。不得用下一episode reset obs冒充有效前一episode next。
6. 保留原全量transition/actor trace/reward terms/MJB；phase仅供奖励和阶段审计。manifest包括source、SB3源、fixture/asset、reward、proof/demo、网络/optimizer/runtime、初始model/normalizer hash和全部预算。捕获失败后写FAILED并保留日志，不吞异常、自动换seed或重试。记录环境步与训练耗时，沿用资源保护和有界退出。
7. 中间2048/4096/6144/8192留存用于诊断，必须标明是在该step更新前或更新后；最终save必须发生于第8192步的SAC更新完成之后，重新加载核seed=20260923、num_timesteps=8192、_n_updates=8092。固定最终model与normalizer，不按验证选择。

## 实施验收与之后的评估

先以禁止物理的合成backend/真实SB3完成：8192预算循环边界的静态或合成小预算验算、实际post-add槽位、真实buffer_actions/环境unscale链、demo600终态、非恒等归一化只做一次、reset与terminal占位、partial有效next、采样来源计数不改变随机序列、日志异常使运行失败，以及最终更新后保存。既有`verify_train_demo_replay_20260924.py`证明r2与真实ReplayBuffer预填接口可用，不替代新的在线`_store_transition`验收。

审查实现后才冻结和安排物理任务。每支训练结束固定在train/validation × zero7/deterministic-SAC各一次24s，保留安全早停和全部失败。zero7应与原同模式fixture/MJB逐值一致；SAC部署输入只读重放核动作，不能把离线重放称新闭环仿真。原奖励审计器复核每条实际reward和Gym日志；新增审计另核全部实际replay槽与source映射。若未记录真实TD target、loss或optimizer梯度，不声称已逐项审计其数值。

这只是单训练seed、单训练fixture、8192在线步的标准SAC可行性对照，不能保证收敛，也不能证明SAC或示范优于ESN。后续六fixture的50µs子步部署为另一个预声明阶段；低频训练torque/speed不进入该主表。

## 实施与零物理验收记录

新增`tools/run_canonical48_sac_20260925.py`、`scripts/canonical48_sac_audit_20260925.py`和`tests/test_sac_audit_20260925.py`。入口继续调用原PairedControlEnv和原评估器；只增加outer info副本以保留自动reset前的已完成transition。logging replay的构造无文件写副作用，只有显式`start_audit()`开启新的训练日志，因此SAC.load不会重开或改写原日志。manifest在prefill/首次reset之前绑定初始模型、normalizer SHA及实际Adam defaults，结束前再次核验proof、协议、demo和初始产物。

12个测试通过（本机SB3 2.9.0、单CPU线程，1.28s），所有物理仿真步数为0。两次各7步的合成SB3训练分别执行5次train迭代；逐项对照标准SAC和加日志SAC的全部policy state_dict、alpha及obs_rms，均精确相同。另以12个固定seed比较标准/logged replay的抽样索引、全部返回张量及NumPy后续RNG状态，均精确相同。其他覆盖真实r2全部600条及终态、其后第1在线条目的来源计数、自动reset前journal归属、故意clip导致的终态next舍入/裁剪变化且mask=0、partial真next/done=0、真实Adam state.step与posthook一致、step6 checkpoint已完成4次更新、最终save/load不触碰audit，以及timeout/动作错位/mask/缺失绑定/I/O失败和proof失败标记/原源漂移的拒绝。

这些是可执行的接口与机制验收，未使用验证数据选参数。实际8192/8092预算、机器人任务成功率、loss/TD target数值与物理部署还没有SAC运行结果；正式运行必须由只读snapshot和运行manifest给出证据。入口每run只有一个环境；有界进程总超时与全服并发槽位仍由启动队列负责，不能直接无队列大量并行启动。
