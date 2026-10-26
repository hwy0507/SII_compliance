# 参数回放容量扩展与正式第24轮（2026-10-26）

原Goal active，未健康收敛。本轮接续前核对原Direct16及三参数23 learner、归档和完整review均live，四GPU即时59/82/86/86%。上一轮完成16/23接续及有限温度候选对照，属于实质进展；温度候选未支持部署，所有辅助已退出勿重跑。无子agent。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库B/repository/SII_compliance（HDD原路径为链接）。冻结物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward/canonical48/action7保持；不回退、不重置优化器、不导入辅助权重。大产物与完整小证据SSD，HDD仅小交接/收据，非arm1/HDD全备份。

## 容量问题和明确的协议变化

最新已完整核验22父capacity1000000，I/V size945750、A944750，均cursor=size且未覆盖。23完整预期I/V987000、A986000；24将跨100万，如果继续原环形回放会覆盖最老数据，且旧的“全prefix保留”审查会不再成立。

新parameter_replay_capacity_20261026.py定义独立回放子类：capacity2000000，保持所有已存字段、行顺序、NumPy RNG，未使用空间不参与采样。marker包含version/original_capacity/capacity/append_without_overwrite/uniform_all_retained_rows/raise_before_overwrite。仅允许准确已登记legacy回放digest且未覆盖的完整父迁移；新checkpoint必须有准确marker，拒绝标记缺失/容量变化/环形cursor/超限。新容量也在写入和消耗随机数之前拒绝覆盖，不无限增长。

**容量扩大后，超过原100万阈值的采样分布与原环形覆盖不同**：旧数据继续可采，不再被新数据淘汰。这是保留完整回放要求下明确登记的训练协议变化，不能宣称整个后续学习与原1m环形算法等价。到原边界前同state/RNG/采样可精确一致；当前有限24不改batch65536/UTD1/terminal128/upper projection/I target min+A-Vmean/actor min/LR。

## 准备验证与失败保留

v1 B/runs/parameter_capacity_preparation_20261026_v1原1890114失败，FAILURE/源/登记保留。验证构造器把参数回放错按Direct49维构造，strict loader以Invalid replay field: observations拒绝，没有优化、新物理或正式state变化。参数回放实际50维（canonical48+混合系数+critic剩余时间）；修正验证与新driver读取父checkpoint实际维度，不改输入语义或放宽shape检查。

v2 B/runs/parameter_capacity_preparation_20261026_v2原1919323已完成，REVIEW passed。完整22三路父回放所有旧array/RNG和原learner digest不变，扩容/重复恢复精确；CPU device cache的1/32/256/65536批与原采样及RNG精确。每路六个负守卫：missing marker、changed marker、wrapped cursor、different legacy RNG、expanded marker old capacity、oversize；拒绝时原状态不变。准备只读原模型，0optimizer/physics/不保存权重。

合成回放从999998条添加4行到1000002，原prefix保留、CPU cache逐项相同、保存marker后恢复/65536批和RNG精确。达到新200万上限时，add在写入和消耗RNG之前拒绝。合成数据不进正式replay。准备未验证新的实际GPU cache更新或任务改善；正式采用必须最新完整23及实际启动/跨界检查。

新resume_cheq_capacity_pool30_20261026.py继承原30pool continuation契约与历史batch/pool证据链，仅增加容量stage：首次严格从最新完整23进入，持久记录准确父checkpoint/replay digest、准备证据/helper SHA/marker；后续只能保持相同历史stage。完整learner恢复/重复恢复不变，扩容后全旧replay与下一65536批/RNG精确，并拒绝未登记的batch/UTD/clock/weight/projection/worker/容量修改。训练用相同DeviceReplayCache/既有exact采样，额外内存仅新增未使用存储。

## 参数23完整结果

三路各41250新增，全部30完整55秒、无abort，新reward从interval journal重建误差0；全部旧prefix/history/优化器超参/terminal128/projection/pair markers和finite通过。完整review/health/FINISHED与图已核验；health网络保持不变，不是新仿真。结果仍有波动，未健康收敛。

| 方法 | steps / updates | Task / Strict | reward均值 | 末1000 q_loss | terminal MAE | in-bag terminal MAE | Q均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| impedance | 987000 / 982001 | 18 / 17 | -2.189907 | 1.433691 | .869074 | .329739 | -4.313361 |
| admittance | 986000 / 981001 | 12 / 12 | -11.953313 | 1.395008 | .729539 | .311489 | 11.401338 |
| vmc | 987000 / 982001 | 17 / 17 | -2.852282 | .476056 | .438888 | .162799 | 17.363041 |

导纳末loss由22的3.150回落至1.395、in-bag terminal MAE .635→.311，但Strict14→12，reward下降，不能把loss回落写成任务改善或收敛。阻抗Strict18→17，VMC17保持。混合terminal MAE含mask0留出；固定pair未投影TD诊断也不是正式目标误差。

准确父B/runs/parameter_pool30_cycle23_archive_20261026_v1/{method}/cycle_00023.pt：I39afc495f95dfcab8ae1a634e26950d3e20797158d697fe4a398f6cfac7a70fe；Ae9fdacad1f14b62c2777412d1f242549d34d4fb1aa5b449ac50c910a425ec7ca；Vb5252c80a6b70afb7b7b6bd2040b387be79cab19f0fc5244d5e92f89d2196d4c。旧23 I1064168/A1064173/V1064175及归档1064231/review1064233已退出，勿重启。

## 正式接续和检查

准备入口B/runtime/prepare_parameter_capacity24_20261026.py只等待原23完整FINISHED/REVIEW/health并核准确父后登记独立parameter_capacity_pool30_cycle24_20261026_v1，三路check-only均已通过（原完整learner精确、回放只增加capacity/marker、下一65536行及RNG精确、继承与新增容量负守卫通过），已launch。CPU/worker/GPU原配置保持：GPU1/2/3，learnerCPU13/26/39，30sampler共享原各12CPU。

正式24 I2362748/A2362749/V2362750，B/runs/parameter_capacity_pool30_cycle24_20261026_v1/{method}/train，从准确最新23全state启动一个周期。启动检查2362753、跨界检查2362754、归档2362755、完整review2362756。

新setup_parameter_capacity24_monitors_20261026.py已启动四种监视：实际启动首1000新增、实际跨1001000步检查、完整边界归档、完整24 review/health。每项验证capacity/marker/size/cursor，并继续检查完整旧prefix/历史/优化器超参及新动作/clock/reward/MJB。跨界审查在原运行首次达到门槛后只读快照，不新增训练，不把合成跨界冒称实际完成。没有自动25。三路真实首各1000新增已审查通过：I/V旧987000、A旧986000全部prefix保留，capacity2000000/marker/cursor=size准确，history/优化器参数/30MJB/action/clock/reward0误差。实际跨1001000审查尚待原进度，不能称已完成。

Direct16原learner1387783、归档1387835、review1387837保持；batch65536/32步/gather+transfer/官方10critic、bootstrap random2-min、actor all10mean、noentropy backup、8:1与全部state保持。最新完整父15：648282/5146264，Task/Strict0/30、reward−31.004831、terminalMAE.055173；未健康收敛。没有自动17。

新纯正式profile2085988，B/runs/batch16_parameter24_gpu_profile_20261026_v1，预登记180样本，等新24 startup通过、GPU PID集合恰四正式后开始，不重复选窗。

## 纯正式GPU观测

纯正式GPU窗口完成：180样本/208.235546s，GPU均值58.6278/73.5111/71.7167/73.2222%，D/I/A/V吞吐10.7619/24.1169/24.7748/24.8084steps/s。逐样本GPU PID集合恰四正式且原learner全live，无辅助GPU。原2085988结束勿重采；仅此固定窗口均值≥50%，不保证每瞬时或隐去轮次尾部/恢复检查的空闲。

完整PROFILE：B/runs/batch16_parameter24_gpu_profile_20261026_v1/PROFILE.json。

## 同步

本轮实际查询/fetch/read main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变；起点6d3b448532d697b41f19779a24acc4ebade0409c。按sii-research-sync与AGENTS更新；GitHub认证仍待恢复，用户已被问，不重复索要、不使用无关凭据。

收尾科学提交16b56236e98cd1a6da77b7ce8ac5d29e70fa41cd仅本地，push仍HTTPS用户名认证失败；重新fetch远端main dbb1d76/baseline f6e8f8c未变。完整82成员小证据SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER24_REPLAY_CAPACITY_20261026_194123/FULL_SMALL_EVIDENCE.tar.gz逐成员hash核验，1243364字节，SHA256 402af5ef2f73a996e73fcf77bea92c7d40c7df01e7d4ded80413dc1b46303a2d。HDD小交接/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_PARAMETER24_REPLAY_CAPACITY_STATUS_20261026_194123/HANDOFF.md与收据/LATEST入口已验证；大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。FINAL_LIVE_STATUS确认四原16/24、归档/完整review及跨界检查仍live；准备/observer已退出。实际跨1001000审查完成状态=False，下一轮先核原2362754及capacity_boundary/REVIEW.json，不能重复启动。Goal active。
