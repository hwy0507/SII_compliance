# 2026-10-26 恢复 RL 与 SERL 实现记录

本会话用户明确恢复 Goal。目标仍是 Direct 和三类参数 RL 的有效学习、稳定 reward、健康
优化以及冻结策略验证；当前没有完成收敛，GPU50%要求尚未满足。

## 仓库与执行位置

已 fetch/read main `bd6193872ea68683244be513869c892f6f60273b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，工作区快进 main。新 main 更新为另一主机的
非RL新30条选模与验证重放；不改变本集群物理合同，也不是用户指定的最终ESN checkpoint。
本集群 SSD 根目录为
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`（以下 B）。
HDD 剩约688MiB，SSD剩约5.8TiB；大产物仅在本集群SSD，未声明已传到另一主机。

## 参数 CHEQ 恢复

B/runs/recovery_cheq_resume_20261026_v1 下三方法的 train 目录，分别GPU1/2/3，
CPU13–25/26–38/39–51，各12物理sampler。当前冻结source_train17_clock，batch256/UTD1，
原actor/critic/target/optimizer/replay/RNG完整保留，没有导入辅助权重。
启动时误用单GPU可见环境，四卡RNG恢复报IndexError，尚未派发物理；改为四卡可见并使用
cuda:1/2/3后恢复。初次失败stderr被重试覆盖，此缺陷在RECOVERY_CORRECTIONS.json如实记录。
正式learner曾被调为nice10，尝试恢复0被系统权限拒绝；新sampler会继承当前nice。

独立检查三个真正的部分checkpoint：网络和优化器全状态digest一致，CPU/四CUDA/Python/
NumPy/local RNG后续抽样一致，各三批replay抽样精确，Adam counters保留。
父cycles0/1/2完整，cycle3部分保留但不计完整，恢复重新开始完整cycle4。未保存MuJoCo
中途状态，不能说逐子步无缝。新run首完整cycle4后按STOP_REQUESTED收尾、科学审查再延长。
八SSD/HDD快照hash、30fixture、30预编译MJB和参考plan全通过；未改原快照。

## Direct 错误身份纠正

B/runs/direct_serl_state_sac_from_scratch_20261026_v1 的首次注册和启动不符合SERL约定：
调用的是旧CHEQ作者代码中的双critic SAC，而非十critic、随机双target、无熵backup的SERL。
这不是可以用“适配”一词掩盖的差异。已写ALGORITHM_IDENTITY_CORRECTION.json和STOP_REQUESTED，
首完整周期30条件结束：34192transitions、58386updates、Strict0/30、reward−35.5701；有早停。
该run的目录名和历史registration保留，但所有结果明确排除为SERL结果；不得载入新SERL的
权重或replay。初始空目录导致的FileExistsError也发生在训练前。该问题及错误启动由本会话造成。

## 真正 SERL 的适配合同

固定官方仓库 B/runtime/serl_upstream_1fa2af7，commit
`1fa2af7496be042e43d36120a7c8d1b71f1bfb59`，Python源码逐SHA。
独立 B/serl_env 安装JAX/Flax；原MuJoCo环境不修改，物理worker继续用B/env/bin/python。
新工具serl_state_adapter_20261026.py直接调用官方SACAgent.create_states/update_high_utd，
只复用make_sac_agent的构造参数，避免导入不需要的实验服务器与数据服务。

- 官方保留：actor/critic 256×256、tanh、LayerNorm，十critic，随机选二target（上游有放回）、
  backup_entropy=False、temperature初值.01、target entropy=−action_dim/2、tau=.005，
  官方优化器和2000步learning-rate warmup。
- 本任务适配：canonical48静态SI缩放、零示范空replay和随机初始化、无人工纠正，
  discount=.9995与原SPT shaping一致。critic没有旧CHEQ context或clock，actor仍48维。
- 动作：官方归一化action7的第一维由[-1,1]仿射映射到[0,1]，其余保持[-1,1]，接公共
  slowdown/Cartesian yield接口。replay存归一化raw action。没有CHEQ名义策略混合。
- 下层是原公共WBC/filter/执行器/dt，不等同论文原生阻抗reference limiting；不宣称原机器人
  系统逐项复现。成功gate、MJB、physics和接触指标不改。
- 冻结sampler没有有效terminal canonical48，终端next state沿用最后有效状态且bootstrap=0；
  这也影响官方temperature在next state上的估计，须披露，不能当保存了真实terminal状态。
- 使用官方高UTD入口，每外层批次2048拆成8×256 critic更新，随后一次actor/temperature
  更新；这是显式登记的critic/actor比，不能与旧trainer的UTD2混称。

软件验证、启动和当前结果以本文件后续记录及实际收据为准。准备完成不等于开始训练或收敛。

## 已完成历史产物汇总

没有重跑既有物理或辅助学习。合并cycle0的12个learned固定回合与12个已复核nominal，
并核对三seed×四方法×两arm共24辅助曲线、1944记录点、48万已完成更新及跨seed标签hash。
这是已有独立审查的汇总和曲线一致性检查，不是本轮重新独立计算原始physics或return标签。

三seed parent/fresh跨周期MAE均值：Direct .5602/.7220；Impedance6.3666/7.7698；
Admittance7.5764/7.5587；VMC5.8782/5.5367。这些是固定无熵行为return预测，不是SAC softQ、
新策略成功或在线收敛证据。汇总见B/runs/shutdown_completed_results_summary_20261026_v1。

## GPU实测与未完成项

B/runs/recovery_monitor_20261026_v1/GPU_60S.json：60样本、66.08秒，均值
20.27/6.37/5.42/5.73%，含错误Direct SAC排空，参数三卡正式CHEQ；无辅助学习。
不能声称达到50%，不能以重复已完实验或无界负载制造占用。
以上是早期窗口；后续实测和已完成检查见下文。有效reward稳定和优化健康证据、
冻结策略最终矩阵、指定ESN及共同SPT仍未完成。Goal保持active。

## 本轮已完成恢复周期及正式续训

三参数恢复cycle4均完整收完30条件、各新增41250条transition。原周期3部分replay全部保留，
cycle3不计完整。`runs/recovery_cheq_resume_20261026_v1/CYCLE04_REVIEW.json`核验全部新reward/
done、父replay全部字段前缀、terminal标签与30个实际MJB、有限网络；不是原始子步重新独立审计。

| 方法 | 累计steps / updates | Task / Strict（各30） | 平均reward | terminal Q绝对误差均值 |
|---|---:|---:|---:|---:|
| Impedance | 203250 / 198251 | 18 / 17 | −2.27254 | 12.4237 |
| Admittance | 202250 / 197251 | 14 / 13 | −10.38703 | 9.5381 |
| VMC | 203250 / 198251 | 17 / 17 | −2.81078 | 44.5040 |

完整健康诊断位于B/runs/recovery_cycle04_health_20261026_v1，图已目视检查。终端Q误差混合
各critic的in/out-of-bag样本，JSON另列两者；不是必须归零的收敛门槛。VMC的next Q从约132
持续升至约188，不能称健康收敛；其他两路亦未完成最终冻结策略验证。

有限吞吐probe在B/runs/recovery_batch_throughput_probe_20261026_v1已经结束：三方法各四个
batch（256/2048/8192/32768）×128更新，共1536辅助更新，0physics，无权重保存或推广。
batch256约75–82updates/s，32768约49updates/s，但采样行吞吐显著增加；短窗loss有限不证明
长期学习更好。第一次launcher缺os导入、尚未派发即失败，LAUNCH_FAILURE保留；第二次正常完成。

基于该测量独立登记一次batch-only在线试验：
B/runs/cheq_batch32768_online_20261026_v1/{impedance,admittance,vmc}/train。
PID1809422/1809423/1809425；GPU1/2/3、CPU13–25/26–38/39–51，各12sampler。
从上述准确完整边界全状态继续，仅batch256→32768，UTD1和其余学习合同保留；预算仅完整cycle5。
该变化改变梯度统计，是显式学习设置试验，不是数值等价提速。不能仅因GPU占用增加而自动延长。
冻结driver校验父checkpoint/注册/源码/审查hash；实际三路各新增12000更新时，再次确认父replay
全部字段前缀精确、更新增量=transition增量、全部learner状态有限。新进程nice0。

## 官方SERL验证与实际启动审查

B/runs/serl_state_validation_20261026_v4/REVIEW.json通过：独立Bellman公式与官方loss一致、
十critic shape、终端mask为0、动作映射端点与可逆性、真实更新改变参数、完整状态恢复后下一
随机动作及更新精确相同。32个合成critic更新，0physics，验证权重丢弃；不是策略学习成功。
此前v1/v2/v3仅因缺依赖失败，日志保留。Flax vmap提示忽略train关键字，无dropout；官方核心未改。

实际Direct：B/runs/serl_official_state_online_20261026_v1/direct，PID1809418，GPU0，CPU0–12，
12sampler，seed20261026，2完整30条件周期，不自动延长。LAUNCH.json保存准确命令；learner
使用B/serl_env/bin/python，sampler显式使用原B/env/bin/python。空replay、随机初始化、无示范、
无旧CHEQ数据或错误SAC run权重。越过5000条随机预热后确实开始更新。

启动只读核验B/runs/serl_and_batch_startup_review_20261026_v1/REVIEW.json：16,000条真实replay
逐条对应journal，raw action→公共执行action的仿射映射、canonical48缩放、next state/reward/
done精确；12个已启动模型、30fixture和参考plan hash通过，真实critic全部十ensemble形状。
88008个critic optimizer steps=11001个outer updates×8；所有网络/优化器与日志有限。
该快照尚无terminal行，不能把软件终端测试冒称本次真实terminal物理审查。较早错误SAC run
34192步的结果严格另列，不并入SERL学习曲线。

环境完整freeze位于B/runtime/serl_state_adapter_20261026_v1/ENVIRONMENT_FREEZE.txt：JAX0.4.35、
jaxlib0.4.34、Flax0.10.2、Optax0.2.4、NumPy2.0.2等，旧MuJoCo环境未改。新四工具与实际冻结
runtime逐字节一致并通过语法检查；官方源码manifest逐文件hash与真实启动收据保留。

## 后续资源测量与交接

新的启动窗口66.26秒GPU均值0/39.18/41.92/40.33%；Direct尚在warmup/JIT。
更新阶段66.03秒均值14.88/45.33/41.95/44.57%，四路均正式训练，没有辅助学习；50%仍未满足。
测量分别位于B/runs/serl_and_batch_trial_monitor_20261026_v1和
B/runs/serl_and_batch_trial_steady_monitor_20261026_v1。

30秒外部Python栈采样B/runs/serl_and_batch_live_profile_20261026_v1：Direct新增1606transition，
selector等待约23%；三参数分别新增681/690/667，已经使用device replay cache，非缺少该缓存。
参数每路7495线程样本中5996为空、1499非空，空栈不能当80%GPU空闲；类别包含率以非空样本
重新解释才有意义。该采样不是CUDA kernel耗时或某优化已证实有效，也不改运行中batch/UTD。

现有准确边界归档器在B/runs/serl_and_batch_cycle_archive_20261026_v1运行，PID2135157，CPU52。
使用视图B/runs/serl_and_batch_archive_view_20261026_v1和原归档工具，跟踪四learner进程身份，
仅保存真正完整cycle checkpoint并随原进程结束；错过的边界明确记录。参数父cycle4已在原run
完整保存，不能将当前partial5重标成cycle4。请先查实际PROGRESS/FINISHED，勿重复启动。

已fetch/read并快进main新增6ed6a318dbfc63d8f88f943c4fbcf641d960c716，baseline仍f6e8f8c；
新内容仅是另一主机非RL训练包归档与评测进度，与本集群active RL分别处理。原关机交接保留
历史上下文，当前状态以本文及AGENTS顶部为准。小证据见docs/evidence/rl_recovery_20261026，
大型checkpoint、源码快照和轨迹仅在本集群SSD，未声称归档到arm1或全量更新HDD关机备份。

下一步收取SERL完整周期与参数batch试验完整cycle5，复核真实terminal、reward/optimizer变化，
审查VMC Q漂移及batch是否有效，再登记下一有限训练阶段。当前不宣称收敛、GPU达标或最终比较完成。

## 收尾新增：官方SERL首个完整周期已复核

B/runs/serl_cycle00_review_20261026_v1/REVIEW.json与DIAGNOSIS.json均完成，图已目视检查。
完整cycle0共41250transition、290008critic updates（36251outer updates），30个55秒完整回合；
Task/Strict均0/30、平均reward−34.2232824、全部approach失败。准确边界checkpoint已保存于
B/runs/serl_and_batch_cycle_archive_20261026_v1/direct/cycle_00000.pt，
SHA256 `d8d3765b9ef770dad7cd28996c34fef9119e0b1879918f0e951ec2b1e217a76b`。

全部41250条canonical观测/nextstate、动作仿射映射、reward/done逐条对journal与transition日志
精确核验；全部30实际模型、终端标签、回合奖励和完整条件集合通过。30terminal nextstate确为
最后有效obs占位且mask0；仍非原始子步的独立物理重建。所有网络/优化器有限。

末1000外层更新平均critic loss .0135582、predicted Q23.1456；随机4096样本固定diagnostic
target pair的TD绝对误差均值.05630，但300个终端critic预测的绝对误差均值9.9500、p95为48.5457。
终端reward均值−25.5550，Q均值−15.6761、中位数−25.3737；不能用稀释后的平均TD loss代替终端
校准或任务学习。只读诊断前后完整网络/optimizer/RNG digest未变，新增更新/physics均0。
原SERL已进入登记内cycle1，未增加阶段预算。

参数cycle5仅剩末批条件时，已启动有限只读收尾协调器PID2515639，CPU54，
B/runs/cheq_batch_cycle05_review_20261026_v1。最多观察1小时，等三个FINISHED后检查父完整cycle4
全部replay前缀、新reward/done/30标签/MJB与cycle记账，再用原诊断工具在CPU做健康检查。
它不延长训练、不派发新物理、不宣称审查已通过；结果须读取实际CYCLE05_REVIEW/health/FINISHED。
