# 下一阶段具体工作（尚未实现/执行）

正式父仍完整93。先读 terminal_census_ablation 的 PLAN/SAVED_REVIEW，原抽样loss和unmasked退化不可遗漏。下一阶段独立登记 full-native 有限副本验证，不能推广1542步辅助权重，也没有94授权登记文件。

接入点已读：
- runtime/violation93_continuation_20261031_v1/published_finite_target_projection_20261026.py 的 install：从原SACEnsemble.train AST重建数值修复、terminal128、投影，动态compile文件名 <registered_finite_target_projection>。
- published_target_pair_mean_20261026.py 又将 target minimum 改为 _reduce_pair(...,_mean_pair)，actor minimum不改。
- history/rawbit wrapper保留原 code object，仅改 globals 中 _project_q。可从原冻结源码重建最终 train 源，先用相同co_filename编译，比较marshal/code对象及已有receipt，确认完全等于实际native函数，再只替换q_losses表达式。
- published_exact_pipeline_20261026.py ExactCache.sample：原replay.rng.integers与accepted、torch.index_select；必须原样保留。DeviceReplayCache具备GPU arrays，终端缓存应随append-only refresh扫描新追加dones、维护索引与完整mask32分组，而非每update扫描4m。
- conditional.py数学实现在runtime/violation93_terminal_census_ablation_20261031_v1；实际调用应基于当前缓存总体及当前batch模式，不使用固定93的终端列表继续新数据。
- target末端就是reward；nonterminal原next_q_value不改。额外终端forward无随机调用，actor/target原更新路径保留；仍需实际完整native多步验证RNG调用量与序列。
- state标记必须版本化并精确回读验证。不要假定不可修改的旧restore函数一定主动拒绝未知键；严格state digest/registered driver必须能发现旧loader丢标记，不得宣称未测试的兼容性。
- 有限验证至少覆盖原全state恢复、保存/重载、旧state迁入（原权重/moments/RNG不变）、真实新终端增量、无新终端append、非法mask/回放截断、完整native一步重复及多步actor/target路径。只能在通过后另登记在线94。

新主机cn2p6rygmr的冷恢复已证明全部8353终端及三路首个65536批次q与旧主机逐元素相等。环境Python3.11.17、Torch2.8.0+cu128、MuJoCo3.11.0，GPU UUID见COLD_RESTORE_REVIEW。
当前guard目录/tmp/sii_gpu_util_guard_20261031_recovery_v1，supervisor96425，workers96426–96429；必须核对start身份，旧97370等已消失，不能按旧PID动作。源码SSD本目录gpu_guard.py.txt。首次启动有2次0%样本，之后77次最低73/81/77/83%，完整记录保留。
