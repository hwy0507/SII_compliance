# 完整92全部终端审查；同52协议有限93实际训练（2026-10-31）

全部8263终端普查完成，阻抗90/92两条安全中止贡献76.3184%的终端masked SSE。依据完整92、原生冻结batch和全终端证据，单独登记并实际启动一轮相同协议93，每方法最多41250新增。Goal active，未达到全部方法reward平稳且loss健康；无自动94/Direct34。原冻结90继续。

## 来源与恢复

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮按仓库sii-research-sync实际query/fetch/read main `624c7cf22a5eb34473118b66d951bce2c1d2ad12`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无子agent。诊断源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation92_terminal_census_20261031_v1`，结果 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation92_terminal_census_20261031_v1`；续训源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_continuation_20261031_v1`，消费者 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_review_20261031_v1`，实际训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle93_20261031_v1`。版本、seed20261025、源/MJB hash和完整命令沿REGISTRATION/EXECUTION。

完整父92在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle92_archive_20261030_v1/<method>/cycle_00092.pt`，精确SHA与原steps在各93 REGISTRATION。I/A/V父steps为3811512/3815000/3816000，I真实新增40562含安全中止，不能误作41250；新93首步3811513/3815001/3816001、最大末步3852762/3856250/3857250，均未越4m容量。原92和本次终端诊断已完成，不重启。

## 全部终端结果

原52观测、动作、reward、全部五critic和原masks，I2755/A2754/V2754终端全部保留。完整learner/Adam/replay/RNG不变，零optimizer update/physics。原固定87队列的观测/动作/reward/masks精确，全部旧预测与本次结果最大差均0。三份values NPZ保留所有输入和预测，独立保存算术重算分组/SSE/排名、三个安全中止原journal+rollout/TERMINAL绑定及实际图核验通过。

| 方法 | 终端数 | masked SSE总和 | top1占比 | top2占比 | top100占比 |
|---|---:|---:|---:|---:|---:|
| impedance | 2755 | 4897.873438 | 59.8990% | 76.3184% | 88.8918% |
| admittance | 2754 | 2019.291136 | 4.8243% | 7.4163% | 61.0342% |
| vmc | 2754 | 851.069120 | 7.3628% | 14.0422% | 72.3197% |

阻抗cycle90 replay index3726050为第1名，SSE2933.777778，占59.8990%；cycle92 index3804982为第2名，SSE804.201953，占16.4194%；cycle79 index3264118为第16名，SSE10.589127，占.2162%。三者external bit均0，原全局目标物体/台面安全失败保持。90 mask=[1,0,1,1,1]；92 mask=[0,0,0,0,1]，唯一参与该行损失的critic4预测−9.531266，对应target−37.889721。保留其余未参与该行loss的预测，不能把masked拟合改善称为所有critic准确。

全五critic散点图显示未被mask选中时仍可能有大误差，A/V也保留该现象。旧79当前拟合好于90/92是不同记录在同一模型下的观察，不构成纵向学习改善、不可约表示错误或纯训练不足的证明。全回放加权终端贡献按真实全回放mask分母+127倍terminal mask计算，分别.188288177/.077552319/.032673478；这是全回放加权损失的终端部分，不是随机batch loss的数学期望。先前64批抽样结果、全部192原NPZ及所有历史尖峰均保留。

## 科学决定与正式93

完整92 I/A原90–92 reward条件失败，V只通过reward条件；全loss尖峰和actor漂移仍未解决。现在有直接证据表明I终端误差高度集中于新近安全失败，但不能证明已有表示无法拟合。选择一个有限93继续原生学习，跟踪固定92全部8263终端、三条中止、各critic退化及完整loss/30条件结果；如误差不降或加剧，复审学习干扰/表示问题，不盲目自动连续训练。

不改变采样、masks、terminal128、batch65536、UTD1、原LR/reward、critic/replay52、actor49/canonical48、clock49/history50/bit51、已学history/violation权重、Adam/RNG和两个架构标记。append-only4m与历史23/47标记不变。冻结physics/MJB、Task/Strict gate、filter/执行器/dt5e−5不变，无离线权重推广、无失败样本删除。原90–92方案与失败结论保留，不以移动窗口抹去原失败。

driver和审查消费者仅适配完整92→93边界；实际trainer与92逐字相同，health算法逐字相同，学习数值依赖逐字相同。三路共108个负例拒绝通过，涵盖错误周期/partial/预算/自动后续/marker/51维/回放cursor/capacity/优化器计数/LR；各2次原生batch65536 clone更新重复后全state恢复，共6次，0正式更新/physics。

实际startup新增步数 `{'impedance': 1000, 'admittance': 1000, 'vmc': 2000}`，全部旧replay字段逐位相同，新52 current/next、raw bit/history/clock、raw→mixed action及所有新增reward重建误差 `{'impedance': 0.0, 'admittance': 0.0, 'vmc': 0.0}`。30MJB/30sampler及原CPU配置通过；这是保存journal审查，不是独立动力学重跑。

启动后实际观察120.045秒、99身份/13样本保持、三路steps增长；保存时steps `{'impedance': 3816234, 'admittance': 3819659, 'vmc': 3820553}`。原archive完整消费者按14400秒上限等待，完整checkpoint复制/hash后执行全回放/new reward/health/loss审查，实际完整图仍须查看。命令/PID/start在LAUNCH和MONITOR/STARTUP/OBSERVER_LAUNCH；先核验现有进程，禁止重复派发。

## 冻结评测、GPU与未完成

原冻结90 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1`、原三evaluator283421/283428/283430及collector283433、postprocessor292743按原PID/start核验；已正常结束的方法 `['impedance']` 以30回合FINISHED和全learner/replay不变收据核验，其余保持原进程。完成 `{'impedance': 30, 'admittance': 28, 'vmc': 28}`/各30，最终全90/raw/88→90配对及其余方法完整内存不变仍待。沿原seed2026102638与launch+21600秒截止，零updates，不延长重启。完整93与后续固定92比较仍待，本轮不新增冻结93。

原冻结90的阻抗现已正常结束：Task17/30、Strict16/30，29完整回合加long0000在614动作/24.56秒全局穿透安全中止，共40489动作。失败和完整learner/replay不变收据、原rollout/TERMINAL来源均保存于FROZEN_I_COMPLETION；完成是指评测结束，不代表所有回合成功。该记录属于原90冻结评测，不是93训练新增失败。

Direct33原数值验收保持；冻结33全30 Task/Strict0/0，旧28缺最终内存证明、恢复2完整不变保持；不把Task成功追加为数值收敛要求。指定ESN仍缺，不替换其他主机模型。partial75、不可评74–76、79/90/92安全中止、halfstd拒绝及所有失败窗口/软件失败保持。

原guard supervisor97370/workers97399–97402继续，threshold50/target70/min duty.7，科研完成仍保活，不是重启服务。本轮199样本/1005.973秒，最低[68, 66, 68, 68]%、低于50次数[0, 0, 0, 0]、末值[73, 91, 92, 94]%。包含synthetic guard，不等于科研吞吐或每瞬时保证；旧warmup0/v6低值保留。

## 保存

共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_TERMINAL92_ONLINE93_20261031/SMALL_EVIDENCE.tar.gz`：164成员/2418930字节，SHA256 `5979f5751df4e207693393fd2083bfda06905c75c35a34d11712b49dde07101b`，逐tar成员字节和Python AST核验。清单 `docs/evidence/RL_TERMINAL92_ONLINE93_20261031/MANIFEST.json`；index/commit逐字和实际远端正常push收据在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_TERMINAL92_ONLINE93_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。原大checkpoint/replay/raw保留SSD；HDD配额满，仅原地更新254字节LATEST指针并回读，非HDD/arm1全备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
