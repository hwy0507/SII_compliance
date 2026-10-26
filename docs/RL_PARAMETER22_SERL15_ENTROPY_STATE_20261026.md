# 参数22接续与Direct初始探索／温度状态诊断（2026-10-26）

原Goal active，未健康收敛。上轮完成参数20/Direct14审查、21/15全state接续、128对起始探索和纯正式GPU窗口，为实质进展。本轮继续原Direct15，完成参数21审查并启动22，新增只读梯度与温度状态来源诊断。无子agent。冻结物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward、canonical48/action7保持；无示范、nominal mixing、回退、优化器重置或辅助权重推广。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库B/repository/SII_compliance，用户HDD仓库路径为链接。checkpoint/replay/raw和完整小证据在SSD，HDD仅小交接/收据；非arm1或HDD全量备份。

## 参数21完整结果与22

| 方法 | steps / updates | Task / Strict（每路30） | reward均值 | 末1000 q_loss | terminal MAE | sampled Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| impedance | 904500 / 899501 | 18 / 17 | -2.288688 | 1.293199 | 0.792389 | -5.260641 |
| admittance | 903500 / 898501 | 13 / 13 | -10.308804 | 1.048399 | 0.676210 | 11.437226 |
| vmc | 904500 / 899501 | 17 / 17 | -2.803177 | 0.610902 | 0.577882 | 21.792520 |

三路各新增41250交互，全30完整55秒、无abort；完整旧replay全字段prefix/history/优化器超参/markers保持，全部新reward从物理interval journal重建误差0，网络/优化器finite通过。health网络不变、图已目视检查。CHEQ mask0为留出，混合terminal MAE不是纯训练误差；health fixed-pair未投影TD不等于当前A/V mean投影目标。导纳Strict12→13、VMC16→17，阻抗仍17；只是一轮改善，未健康收敛。

准确父位于B/runs/parameter_pool30_cycle21_archive_20261026_v1/{method}/cycle_00021.pt，完整review/health/FINISHED在parameter_pool30_cycle21_review_20261026_v1：

- impedance：a3d91047d0f145dcb84b2f2ebee07ec9789d93b11800e63bf1021f6dbb958615。
- admittance：84b5861e10abba20b2a1b541001b0e628b77452be833bb15319814f8d4604817。
- vmc：4798e05775d6e406e0baac82ec068840ecc4ed36521853c45a4a4cbd3fba1b61。

正式22 I3849186/A3849188/V3849190，B/runs/parameter_pool30_cycle22_20261026_v1/{method}/train；GPU1/2/3、learnerCPU13/26/39，30sampler共享14–25/27–38/40–51，原batch65536/UTD1/terminal128/upper projection/I target min+A-V mean/actor min/LR I,V3e-4,A3e-5不变。准确21全state接续一个22，历史pool来源保持18→19，参数必须pair_class恢复。三check-only完整state/重复恢复/负守卫通过；真实首各1000新增全prefix/history/markers/MJB/action/clock/reward0误差与30sampler集合通过。

归档3849245到parameter_pool30_cycle22_archive_20261026_v1；完整审查3849248到parameter_pool30_cycle22_review_20261026_v1。旧21 learner2558774/2558776/2558777及归档2558780/审查2558781已完，勿重启。没有自动23。

## Direct15原进程继续

learner2870244，B/runs/serl_multistep_batch65536_cycle15_20261026_v1/direct；GPU0/CPU0、30sampler共享CPU1–12。原归档2870381、完整审查2870384仍待15完成。batch65536/32步/gather+transfer/官方10critic/random2/noentropy backup/8critic:1actor保持。最新完整父仍14（607032steps/4816264critic、Task/Strict0/30、reward−31.033155）。准确父SHA d47def4626a3cdb8e783403d2a0152c916593e36ef30675e353e699ff35bf410。

上轮15 check-only及1000真实交互审查已通过，继续原进程，无自动16。不能把运行中的15当完整父。Direct actor目标是官方全部10critic均值；random2/min只用于critic bootstrap，不要误用CHEQ参数路的actor min。public0=(raw0+1)/2，0为nominal、更大减慢WBC。32步bootstrap保存gamma^(k−1)mask、learner再乘gamma是正确实现，不能因下述温度问题改它。

## 起始策略梯度：完整只读诊断

成功run：B/runs/serl_cycle14_initial_actor_gradient_20261026_v3；原3704320/审查3704321均已结束勿重跑。冻结准确完整14全learner/optimizer/RNG/replay，固定seed2026102617，每组8192行：初始组从450个clock1行有放回抽样，early32从14400行无放回抽样，uniform从607032成熟行无放回抽样；三组不新增物理/优化/回放写入，不保存推广权重。

| 固定状态组 | 采样熵 | Q项梯度L2 | 温度×熵项梯度L2 | 官方actor梯度L2 |
|---|---:|---:|---:|---:|
| initial | −23.341679 | 5.891768 | .073189 | 5.881260 |
| early32 | −15.316179 | 1.176424 | .034504 | 1.181061 |
| uniform | −3.665251 | .082897 | .019022 | .082713 |

初始组pre-tanh高斯std七通道均值约.0175–.0656，uniform约.3423–.3966；初始mode public0均值.963595。这里只描述完整14条件分布，不能与上一轮冻结13的128个实际首动作直接作因果趋势比较。初始Q项梯度范数约为熵项80.5004倍。initial与uniform官方actor梯度cos=.048914、initial与early32=.164027、early32与uniform=.851610；是近乎正交而非负向冲突，不支持“相互反向”假说。有限8192样本/固定噪声的欧氏梯度不能当实际Adam步、总体梯度或任务收益。

初始行占原成熟回放450/607032；正式actor65536批期望含48.5826个初始行、1554.6436个early32行。不是完全未采样。官方actor目标Q项为10critic均值，精确数学分解及梯度和校验通过，保存NPZ梯度可独立复算；原完整learner/optimizer/RNG和replay digest不变、父SHA不变。

**诊断失败保留与数值范围**：v1原3409186在eager分解与JIT官方目标比较时相差.00050926；v2原3563038统一动态JIT输入后仍相差.00155067，均在原容差失败，原审查3621297按失败停止。没有把失败作为科学结果。v3仅在诊断进程启用highest float32矩阵计算精度，三组loss差0/0/1.90735e-6，梯度和按原rtol2e-4/atol2e-6通过，未放宽容差。没有改变正式精度；只证明该诊断精度下数学目标一致，不声称正式默认精度下数值梯度完全相同，也不把差异唯一归因到某项编译优化。

REVIEW/INDEPENDENT_REVIEW/FINISHED/FINAL_SCIENTIFIC_REVIEW与图均完成，图已目视检查。独立审查复算保存的梯度和/norm/cos、选择行及全父/源hash，不重新计算神经梯度或动力学；初始与失败两版选择行逐项相同。失败源码/登记/收据保留，原log在SSD。actor_gradients.npz和selected_rows.npz保留SSD及hash，非推广权重。

## 温度学习的状态分布差异

新增完整607032行索引审计TEMPERATURE_STATE_COVERAGE.json：current观测含450初始行、14400个first32行，而派生32步next观测中两者均为0；最早next在32动作后。已核对官方temperature_loss_fn→_compute_next_actions使用batch next_observations，multistep适配器把这个字段换成32步端点，因此温度与actor所见状态分布不同。这不是折扣bootstrap错误，也不独立证明任务失败原因。

随后完成B/runs/serl_cycle14_temperature_states_20261026_v1，协调4020314已结束。等待下面纯正式GPU窗口结束后才启动，复用已登记uniform8192行、固定外部噪声seed2026102618，在准确完整14比较current、原始raw next1、derived next32；温度.000798200257、目标entropy−3.5。均使用同一官方温度目标、同一噪声，仅诊断输入状态来源不同，highest FP32限诊断进程；0优化/新物理、完整state/RNG/父SHA不变。

| 温度状态来源 | entropy | entropy−目标 | softplus原参数梯度 | 负梯度方向 | first32行 |
|---|---:|---:|---:|---|---:|
| current | −3.639658 | −.139658 | −.000111431 | 增加温度 | 193 |
| raw next1 | −3.655493 | −.155493 | −.000124065 | 增加温度 | 191 |
| derived next32 | −3.476145 | +.023855 | +.000019033 | 减小温度 | 0 |

温度参数化是softplus，不是exp/log-alpha；独立复核L=alpha×(H−target)、dL/dtheta=sigmoid(theta)×(H−target)，以及三组输入观测hash/覆盖计数、原父/源hash通过。这里的梯度符号不是带历史动量的实际Adam步。一个固定样本/噪声的结果不证明总体期望或任务成功改善。REVIEW/FINISHED/INDEPENDENT_REVIEW/FINAL_SCIENTIFIC_REVIEW及图完成，图已看。

**下一步科学动作**：依据上述差异，准备单独有限受控候选：仅让温度学习读取原始一步后继，critic继续32步reward/bootstrap/端点，actor继续current观测；保持uniform回放、全部正式state和其他超参。应先验证原始/派生后继相同时与官方更新等价、完整state恢复/计数/RNG/负守卫，再做同父同draw有限优化对照，不能混入辅助权重或直接部署。该候选代码、优化对照和正式部署目前均未完成；候选可使用已完整审查的14作固定起点；正式采用时必须从最新完整15或更晚父恢复，不能回退到候选父或推广辅助权重，当前正式15不变。原128对noise、warm1step、early replay探针不重复。

## 利用率、发布与下一次接手

B/runs/batch15_parameter22_gpu_profile_20261026_v1，观察3752747已结束，180样本208.239987秒，GPU均值59.0333/74.1167/74.2389/74.4167%，D/I/A/V吞吐10.7664/24.4910/25.1008/25.1633steps/s；逐样本GPU PID集合恰为原Direct15和新三路22，四learner全样本live。此窗口无辅助GPU，温度状态诊断严格等待窗口及observer退出。均值全≥50%，非每瞬时/永久保证；尾部和周期检查等待低占用不隐去，不挑窗口重采。

开工fetch/read实际main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，起点e5591ff。GitHub凭据此前已请求恢复，不重复问、不索要token、不用无关环境凭据。小证据docs/evidence/rl_parameter22_serl15_entropy_20261026/SOURCES.json记录原路径与hash，LIVE_STATUS区分当前运行和完整结果；最终提交/推送/归档状态见收尾。

后续先核对原22/15和完整review，及时在完整边界接续；Goal保持active，任务成功、稳定reward和数值健康尚未同时成立。

收尾科学提交a5a8aae86e2ced8dd5a233755edc44be994aaf04仅本地，push仍HTTPS用户名认证失败；远端main dbb1d76/baseline f6e8f8c重新fetch无变。完整114成员小证据SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER22_ENTROPY_STATE_20261026_183920/FULL_SMALL_EVIDENCE.tar.gz，逐成员hash已核验，1487888字节，SHA256 2774dd726304b4e7829c837847bf182c27f09a70399bd68f8d0671978a5f2e46。HDD小交接/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_PARAMETER22_ENTROPY_STATE_STATUS_20261026_183920/HANDOFF.md及收据/LATEST入口已核验，大checkpoint/replay/raw与诊断梯度NPZ仍SSD，非HDD/arm1全备份。FINAL_LIVE_STATUS核验四原15/22持续推进、归档/审查live、全部有限诊断/观察进程已退出。
