# 参数23接续、Direct15/16与温度后继状态有限对照（2026-10-26）

原Goal active，尚未健康收敛。无子agent。本轮完成参数22完整审查与23全state接续，完成Direct15审查并从完整边界续上16；温度状态候选实现、隔离gate和有限同父同draw对照见下文。物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward/canonical48/action7冻结；无示范、nominal mixing、回退、优化器重置或辅助权重推广。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库B/repository/SII_compliance，用户HDD仓库路径为链接。大checkpoint/replay/raw与完整小证据在SSD；HDD仅小交接/收据，非arm1或HDD全量备份。

## 参数22完整结果、末段波动与23

| 方法 | steps / updates | Task / Strict（每路30） | reward均值 | 末1000 q_loss | terminal MAE | sampled Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| impedance | 945750 / 940751 | 18 / 18 | -0.422626 | 1.212221 | 0.677942 | -4.271797 |
| admittance | 944750 / 939751 | 15 / 14 | -8.585905 | 3.149863 | 1.035030 | 11.471194 |
| vmc | 945750 / 940751 | 17 / 17 | -2.772431 | 0.464774 | 0.531523 | 19.478973 |

三路各新增41250交互，全30完整55秒、无abort；全部旧replay字段prefix/history/优化器超参/markers保持，全部新reward从物理interval journal重建误差0，网络/优化器finite。完整review/health/FINISHED和图均核验；不重做物理仿真。准确父位于B/runs/parameter_pool30_cycle22_archive_20261026_v1/{method}/cycle_00022.pt：

- impedance：2235f64d07b86e37aa0325dad207e2d9eac9da0cd72db21022ffa55bd76d4911。
- admittance：bff59e6978b8b792970ea65af6f35ca2d72e2ece4b477bf63c8cac9d54c9495e。
- vmc：6235e587408e91af6fa9a9f0c85ed238886ca86559bd6c75092b554d8d81c2ad。

导纳末段loss并不平稳。B/runs/parameter_pool30_cycle22_tail_audit_20261026_v1只读核对完整22末5000和23首5000连续更新，每1000平均q_loss为22：1.105/1.069/1.894/2.729/3.150；23：2.633/2.270/2.344/2.347/1.958。22训练内terminal MAE从21的.259升至.635，留出从2.452升至2.728，整体.676→1.035；alpha .000332→.000673、动作近边界比例.1006→.1430。终端混合误差含CHEQ mask0留出，不能全部当训练误差。23早期有所回落但仍高于先前；不同物理阶段/新数据，不作因果结论或健康收敛声明。未因短窗口改变正式超参。

正式23三learner I1064168/A1064173/V1064175，B/runs/parameter_pool30_cycle23_20261026_v1/{method}/train；GPU1/2/3、learnerCPU13/26/39、30sampler共享各原12CPU。准确完整22全state接续一个周期，原batch65536/UTD1/terminal128/upper projection/I target min+A-Vmean/actor min/LR I,V3e-4,A3e-5保持。三check-only完整恢复与实际首各1000新增prefix/history/marker/MJB/action/clock/reward0误差检查通过；归档1064231、完整review1064233，startup1064229已完成。旧22进程3849186/3849188/3849190及归档/审查已退出勿重启。参数必须pair_class恢复。没有自动24。

## Direct15完整结果与16全state接续

Direct15完整648282steps/5146264critic，全部30完整55秒、无abort，Task/Strict0/30、reward−31.004831。全部新41250单步reward/32步派生目标精确；旧607032 raw/derived/history/ready保持、pending0。terminal MAE .055173/max1.294567，32步TD .053895、Qmean−20.635448、alpha .000726096。REVIEW/DIAGNOSIS/FINISHED与图通过，完整网络/优化器/RNG只读诊断不变；低loss尚未转成任务成功。准确父B/runs/serl_multistep_batch65536_cycle15_archive_20261026_v1/direct/cycle_00015.pt，SHA70c9068b34a7d014f8b093d1c89fb0ed0420af35d07f8ff687e529636a503998。旧2870244/2870381/2870384已退出勿重启。

正式16 learner1387783，B/runs/serl_multistep_batch65536_cycle16_20261026_v1/direct，GPU0/CPU0，30sampler共享CPU1–12。完整恢复check-only及真实首1000新增检查通过（全部旧648282 raw/derived/history保留，124新mature+876pending、action/clock/reward0误差/30MJB），从最新正式15全state续一个原设置周期：batch65536/32步/gather+transfer/官方10critic/random2-min bootstrap/noentropy backup/8critic:1actor保持；actor目标为全部10critic均值。归档1387835、完整review1387837、启动检查1387833。温度候选未部署，无自动17。bootstrap存gamma^(k−1)mask由learner再乘gamma正确；public0=0 nominal、越大越慢，不改解释或公式。

## 温度状态候选及两版实现gate

新增serl_temperature_state_candidate_20261026.py，仅继承官方SACAgent并覆盖temperature_loss_fn，将单独显式temperature_next_observations传给原官方温度损失；critic/actor/update/高UTD/优化器/RNG保持继承。批次附加规范化49维后继（48状态+clock），actor仍canonical48；不是正式checkpoint迁移器，尚无正式持久marker/strict loader/stage driver。

冻结准确完整Direct14，SHA d47def4626a3cdb8e783403d2a0152c916593e36ef30675e353e699ff35bf410。v1 B/runs/serl_cycle14_temperature_successor_gate_20261026_v1原589004失败已保留：实际下一个65536批/完整恢复与7项负守卫通过，但官方原实现与别名温度输入的完整8:1更新不逐位相同。两次辅助8:1更新（16critic/2actor/2temperature）丢弃，无正式state变化，不能把v1称通过。

v2同名_v2原841719完成，REVIEW与FINAL_SCIENTIFIC_REVIEW已核验：默认精度最大state绝对差2.9802322387695312e-08，只涉及actor Dense_1/kernel及其Adam mu/nu（后两者最大2.2737e-10/4.4409e-16）；metrics逐位相同，所有非浮点/counter/RNG精确。全部浮点满足显式rtol1e-6/atol1e-7，highest精度公式检查也通过，但**不声称默认更新逐位等价**，原false标记保留。highest只用于诊断对照，未改正式精度。

在正式默认精度下，仅改变温度状态，独立critic-only和actor-only更新的全部state与metrics精确相同；temperature-only仅温度参数/优化器不同，其他完整state精确。真实第一65536行与原采样/RNG精确；width48、wrongcount、NaN、clockhigh/low、doubleconversion、missingtemperature共7负守卫通过。原learner/replay/RNG/父SHA不变，v2共34critic/6actor/6temperature辅助更新丢弃，0physics/不保存权重。审查决定只许可有限离线probe，未许可正式部署。

## 有限温度后继对照协议

B/runs/serl_cycle14_temperature_successor_probe_20261026_v1；原probe1094552、独立保存结果审查1162204。两个顺序臂derived_next32/raw_next1都使用相同候选wrapper、正式默认精度、准确完整14全learner/optimizer/replay/RNG，各2000outer/16000critic/2000actor/2000temperature、batch65536；同一全部row draws和RNG流。critic继续32步reward/bootstrap/endpoint，actor继续current；只改变temperature输入来源。每200记录，固定seed2026102619的4096诊断行及全450initial/terminal，0新physics、不保存或推广权重。

probe显式验证v2 gate及独立gate_decision的hash、数值界、精确critic/actor隔离与仅温度变化，保留native_alias_complete8to1_update_exact=false。两臂开始完整state/诊断相同、真实部署下批和采样RNG相同，最终采样摘要/agent RNG一致、计数严格增加。独立结果审查检查保存预算/摘要/源与父hash/finite数值并绘图；不重新计算神经梯度/推理、采样或动力学，范围如实标注。即便有限对照改善，也不能直接导入辅助权重；正式采用必须最新完整正式父及独立迁移/恢复/持久marker验证。

## 有限对照结果与审查决定

两臂均完成全部预算，累计32000critic/4000actor/4000temperature，实际采样摘要均e0fc1cbb626c7e3574c04cfc006059011ad53dc0ca463590e481894c47384ca0。两臂全初始state/replay/诊断、末sample RNG和agent RNG相同；原父hash/replay保持。REVIEW/INDEPENDENT_REVIEW/FINISHED/FINAL_SCIENTIFIC_REVIEW均完成，图已目视，原1094552/1162204退出勿重跑。

| 固定诊断 | 初始 | derived32对照末 | rawnext1候选末 |
|---|---:|---:|---:|
| alpha | .000798200 | .000792780 | .000839037 |
| initial entropy | −23.402439 | −23.741861 | −23.744192 |
| rawnext1 entropy | −3.657357 | −3.607643 | −3.304644 |
| terminal MAE | .059095 | .056703 | .058605 |
| 32步TD MAE | .060768 | .076244 | .077213 |
| initial mode public0 | .963522 | .961014 | .966044 |
| initial residual mode abs | .378834 | .404125 | .430945 |

候选alpha比对照高约5.8%、rawnext1熵更高，但initial熵未改善，terminal/32步TD略差，public0和残差幅度也更高；初始pre-tanh std仍约.017–.067。两臂在outer1200都有terminal/TD尖峰，保留全轨迹，不挑有利中间点。**不部署、不导入权重、不重复或扩展本probe**。单父/单共同采样序列/固定有限预算，无新物理/任务成功评估，不据此证明总体劣于；它不支持把全局温度后继来源调整当作初始探索问题的解决方案。正式16原设置保持。

## 下一步容量边界

参数回放容量新只读审计：准确22阻抗父capacity1000000/size945750/cursor945750，base默认同为100万。23完整预期I/V987000、A986000，当前不会覆盖；24会跨100万，禁止盲目复用全prefix审查/旧driver。下一步优先验证独立登记容量扩展/持久marker/strict loader及合成跨界守卫，保留全部旧row/state/RNG/下批；超过原容量后相对环形丢弃的采样分布改变须明确披露。尚未实施或部署扩容，须核三路最新23父。 证据B/runs/parameter_pool30_cycle22_tail_audit_20261026_v1/REPLAY_CAPACITY_AUDIT.json；0优化/physics。

## 纯正式GPU利用率

纯正式GPU观测已完成：180样本/209.097716秒，GPU均值58.5778/74.1556/71.5111/73.8944%，D/I/A/V吞吐10.7270/24.4049/24.5722/24.9214steps/s；逐样本GPU PID集合恰四正式、原learner全部live，无辅助GPU。原1275249完成勿重采；均值≥50%仅此固定窗口，非每瞬时/永久保证，周期检查和尾部空闲不隐去。

完整PROFILE位于B/runs/batch16_parameter23_gpu_profile_20261026_v1/PROFILE.json；采样严格等待16启动检查和温度probe完整审查及GPU退出后开始。

## 发布与后续

本轮再次查询、fetch/read实际远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变。起点b20eba43dd1992298aa598d8c500550e47c1e59d。遵循仓库sii-research-sync；GitHub凭据此前已请求恢复，不重复问、不索要token、不使用无关环境凭据。最终提交/推送/归档结果另见收尾收据。
