# v8 ESN训练残差定位：导出与ridge求解通过，闭环尚待

## 22:00 UTC：原拟合连续核验，41→49/75

21:50:02.519–22:00:02.673UTC共21次实际采样，原1089228/start31715901均live、
service active、training；完成41→49/75，同一候选更新数严格增长。
末次seed03 RNN candidate07到27340更新，内存663339008bytes。
观察器68681正常exit0，未停止训练；22:00:30再次systemd/ps确认原协调器1110985继续，
内存653361152bytes/3GiB/swap0/OOM0。
[完整观察摘要](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FITTING_VERIFIED_WAIT_2150.json)。

本轮为verified wait，上一轮诊断分窗修复为progress。完整75/九模型锁定与审计、
18真实场景学生失败定位、108六指标均未完成，Goal active。预先复核这些入口和分母，
没有修改绑定源/模型/数据或提前测试。开工main4839ac49/baselinef6e8f8c实际fetch/read；
收尾读取并fast-forward至另一任务新增0be97cc8，只有RL文档/证据更新，未操作其运行。
本轮观察摘要2638bytes/SHA256 `1055acd9e1e4f43afcbf5cf97497d138ba3b10c7232a07304a7aa2246d8df7b2`
已在暂存与最终路径逐大小/hash核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_fit_observation_2150_20261029_v1/V8_FITTING_VERIFIED_WAIT_2150.json`。
仅本轮观察摘要，非源码/报告/在途模型全集；此前源码/数据归档保持。

## 21:46 UTC：闭环诊断分窗修正，原公平训练继续

21:47:44UTC覆盖：原队列40/75完成、seed01 MLP candidate06已接续，训练未结束。
科学f5b4b647已正常push并核远端；同commit源码/小证据1209文件7795179bytes/SHA8bf275f2，
准确报告12488bytes/SHA3bb1aadc均已暂存和最终双重核验共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_closure_window_source_20261029_v1/`。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CLOSURE_WINDOW_SHARED_RECEIPT.json)。
覆盖本节“待共享”，不含在途模型/本段后补收据，Goal仍active。

原训练1089228保持active，完成39/75，seed01 RNN candidate06已1040更新；
21:45:34内存534114304bytes/3GiB、swap0、OOM及oom_kill0。仍无完整九模型锁定，
不提前运行18或108，不用当前候选验证损失宣布最终效果。

待用的18回合诊断reviewer也存在浮点时间边界重复/虚假单帧尾窗问题。已修为核验
首帧.04秒、间隔.04秒后的50帧互斥分组，部分尾窗按实际帧数标注终点。
500/750/325帧分别10/15/7窗，角场景最后25帧、12–13秒。原reviewer逐字节另存，
原24训练历史诊断的历史hash保持；error_stats/history/teacher_replay/qualification
四个共享函数AST逐一不变。修正只影响描述统计，不能解释此前学生失败。

9组正负浮点漂移合成输入、全部24train真实时间轴、每窗独立标量MSE核验通过；
空数组/错误起点/错误采样间隔/非有限时间均拒绝。真实尚未启动18的入口也拒绝且
不产生结果。**完整18正向审查仍待**，合成误差不是真实学生动作。首试检查已过但
收据目录缺失导致写出失败，补建目录后重跑成功，失败说明保留。
[核验收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CLOSURE_WINDOW_CHECKS.json)，
[旧reviewer](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CLOSURE_REVIEWER_BEFORE_WINDOW_FIX.py)。

已确认修改文件不在handoff/18/108预登记绑定清单中；18准备的196个源码hash全部保持。
冻结训练/teacher/模型/gate均未改。开工实际fetch/read main74eaff8970f276c934b97e1f83e5a1e87e6f837d、
baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d；独立RL新记录只读，不进行RL操作。
新代码及本节收据当前仅本机、待共享，后续追加共享核验。Goal active，主矩阵未完成。

21:38:20UTC最新：原1089228 active，33/75完成，seed01 RNN candidate05更新2616，
内存1031184384bytes/3GiB/swap0/OOM0。恢复记忆补充和21次观察已随科学a6150123、
合并efe3c46e正常push，双方日志/共同历史逐字保留；未改原训练或独立RL运行。
本轮1205文件7788848bytes/SHAe620bcee源码/小证据及9907bytes/SHA1626795d准确报告，
已核共享到`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_memory_diagnostic_source_20261029_v1/`。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_MEMORY_DIAGNOSTIC_SHARED_RECEIPT.json)。
覆盖下文补充“待共享”状态，不含在途学生或此后收据；Goal active。

21:23:11UTC更新：原1089228同PID active，21/75完成，RNN seed2026102801 candidate03
更新1076；内存960634880bytes/3GiB/swap0。原训练继续，无最终学生闭环矩阵。
科学提交5037e93a已push并核远端；源码/小证据1200文件、7770548bytes/SHAf679ad46，
以及该commit准确报告5439bytes/SHAe3dd130c，已逐大小/SHA核验共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_esn_diagnostic_source_20261029_v1/`。
[完整收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_ESN_DIAGNOSTIC_SHARED_RECEIPT.json)。
覆盖下文“待共享”快照；不含在途学生/后补收据，不是模型或原物理全集。

本轮检查三组已完成ESN的全部24条训练历史，共12,600帧；不等待神经网络全部结束才做
这些只读数学核验，但没有提前启动学生仿真、重新选模型或改在途训练。
主矩阵尚未修复完成，教师全30合格不能代替学生闭环成功。

## 后续定位：低估与残留并存，不能仅延长记忆

原训练有界观察已正常结束：21:25:45–21:35:45UTC共21次均确认
1089228/start31715901同身份live、service active、真实更新增长，完成作业23→31。
最后seed2026102803 RNN candidate04更新1184，内存1147834368bytes；观察器退出不代表
训练终止，没有重启/重复任务。[完整观察摘要](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FITTING_VERIFIED_WAIT_2125.json)。
新九模型锁定、18诊断和108主矩阵仍待。

进一步审查全部24train的最后50帧（每条最后2秒），三seed全部保留。
用actor原尺度[8N,8N,8N,1Nm,1Nm,1Nm]归一化估计wrench，取六维绝对值最大值；
1e−4、1e−6、1e−8三个描述阈值下，整个末2秒都接近零的数量均为rod8/8、ball7/8、corner0/8。
这是估计外力输入的分类，不是实际接触检测或新任务门。

下表为完整8条训练球撞，数值都是归一化requested-action的z通道；偏差为ESN减teacher，
不是滤后速度或实际位移。RNN/MLP尚在训练，不作三家最终排名。

| 训练身份 | 教师末2秒平均z动作 | 教师恢复激活均值 | ESN平均偏差（三seed范围） |
|---|---:|---:|---:|
| ball00 | .0599565 | .21662 | −.0031088 ～ +.0023255 |
| ball01 | .0014700 | .00499 | +.0024925 ～ +.0072401 |
| ball02 | .0702652 | .24930 | −.0364037 ～ −.0312581 |
| ball03 | .0159613 | .05472 | +.0120792 ～ +.0265146 |
| ball04 | .0343852 | .11911 | +.0003247 ～ +.0029171 |
| ball05 | .0276748 | .09530 | −.0019743 ～ +.0103419 |
| ball06 | .0014180 | .00481 | +.0171451 ～ +.0275664 |
| ball07 | .0782612 | .27913 | −.0399713 ～ −.0244210 |

ball02、07在1e−6描述阈值下末段已分别连续12.32、11.04秒近零估计负载，
教师却仍保持恢复动作；ESN持续低估。反过来，ball03、06被高估；棍推末段教师恢复激活0、
z动作近零，ESN仍有−.0006255至+.0081972的均值偏差。不能把这些现象统一归结为“动作太小”，
也不能据两个低估样本就盲目增大输出或统一拉长记忆。

实现核对：当前ESN的独立context读出权重为0，context只通过估计负载或储备池状态交叉项
影响动作；三seed没有context-dependent leak。神经元名义时间尺度为.04/.12/.5/2秒，
但**不等于**整个递归网络有效记忆最长2秒，实际保存轨迹的末段状态仍非零。
教师恢复记忆按正向进展与意图衰减，和当前ESN固定leak并非同一状态更新机制。
这支持“恢复状态表征/拟合仍有不足”的排查方向，尚不证明单一原因或任何改法有效。
需在原18实际闭环中对比误差方向、保持/衰减和回位结果，之后再决定有限修复。

全24 teacher及72个model/history actor回放精确通过；另用独立math.fsum循环复算
全部72条尾段bias/RMSE及24条teacher均值和scaled-wrench最大值通过。
[完整数据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_RECOVERY_MEMORY_REVIEW.json)、
[核验及首次拒绝收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_RECOVERY_MEMORY_DIAGNOSTIC_CHECKS.json)。
新诊断首次假定旧冻结actor有新版字段而在写输出前拒绝，改为核checkpoint真实schema；
冻结actor、checkpoint、训练队列均未改。复核服务3.696秒自然success，单线程/3GiB/swap0。
无新物理积分、合成延长轨迹、验证/测试诊断或refit。

原训练21:33:15UTC同1089228/start31715901保持active，29/75结束，
RNN seed2026102802 candidate04已1428更新。原十分钟有界observer仍在途，只读同一进程，
不是新训练/等待超时重启；完整观察结果以后续记录为准。本补充新证据仅本机，待共享核验。

## 本轮定位结果

- 三组ESN用原108冻结runtime逐帧重放全部24train，与拟合导出动作完全相同；
  24条原teacher动作也精确重放，原始数据/示范/config/source/checkpoint hash均核验。
  在这些训练输入上没有发现导出、输入排列或储备池reset不一致。
- 独立重建12,600×540训练设计矩阵、训练归一化、原ridge正规方程，直接检查保存权重，
  **没有重新求解或更新模型**。三seed相对方程残差分别1.3692e−14、7.3183e−15、
  2.8201e−14；重建输出与导出最大差≤8.33e−15。没有发现解析ridge求解/归一化错误。
- 仍有明确的拟合残差，且集中在关键阶段。不能因为全局MSE小就认为已经学好。

以下是所有8条训练身份合并后的归一化requested-action误差，未经过公共filter；
不是力矩、实际末端速度或Task/Strict指标。RMS教师幅值是相同样本的参考量，
不把该比值作为新成功门槛。

| 场景 | 垂向动作教师RMS | ESN垂向动作RMSE（三seed范围） | 全7通道MSE（三seed范围） |
|---|---:|---:|---:|
| 棍推 | .00558630 | .00331486–.00334958 | 3.65214e−6–3.98500e−6 |
| 球撞 | .06471633 | .00787122–.00910465 | 1.20375e−5–1.51230e−5 |
| 厚桌角 | .07772992 | .00474382–.00626966 | 7.25914e−6–9.79388e−6 |

棍推垂向误差约为教师该通道RMS的59.34%–59.96%，绝对值小不等于相对动作误差小。
全训练2秒窗口中，三seed棍推最大整体误差均在rod01的8–10秒；球撞最大误差分别在
ball02、ball02、ball07的28–30秒，垂向RMSE分别.03466389/.03650927/.04000848。
这些均来自训练示范，未读测试轨迹选窗口；不是新的验证选模规则。

棍推独立事件窗口的全7通道MSE：接触到蹭过为1.21329e−5–1.37442e−5，
蹭过到确认回位为3.06614e−6–6.97414e−6，确认回位到撤棍为1.97638e−6–2.68197e−6。
事件端点可能属于相邻描述窗口，不能将三个窗口帧数相加当不重叠总数。
2秒时间窗则按50个40ms采样点互斥分组，全部训练样本恰好覆盖一次。

三个模型6个运动通道均未触发输出裁剪；slowdown有17.60%/19.10%/18.18%的原始值
被其合法[0,1]范围裁剪。这里仅说明实现，不据此认定slowdown裁剪导致闭环失败。

证据：[完整训练历史诊断](evidence/NONRL_INTENT_RECOVERY_20261029/V8_ESN_TRAIN_HISTORY_REVIEW.json)、
[独立ridge方程](evidence/NONRL_INTENT_RECOVERY_20261029/V8_ESN_RIDGE_EQUATION_REVIEW.json)。
全75作业/9模型的正式审计仍未完成；本轮仅排查已完成ESN的训练历史和数学实现。

## 诊断分窗修正及局限

首版诊断按浮点物理时间的上界循环，个别30秒末时间略大于30，产生一个伪30–32秒
单帧窗口，也可能重复边界采样。已改为通过40ms检查后的样本下标分组，500/750/325帧
及浮点扰动覆盖检查通过，实际全部24历史重新审查。初版原件压缩保留在
`evidence/NONRL_INTENT_RECOVERY_20261029/V8_ESN_TRAIN_HISTORY_INITIAL_WINDOW_ISSUE.json.gz`，
不用它做窗口排名；全场景汇总不受影响。此问题只在本轮新增诊断中，未改训练、物理、gate
或原评测代码，也不能解释旧ESN闭环退化。

两项审计服务均自然success，实际运行分别约3.9秒和2.0秒；CPU100%/线程1/3GiB/swap0。
无新物理积分、优化或模型改写。本轮工具不在原拟合/18/108绑定源清单中；绑定源保持。

## 原训练继续与下一步

2026-10-28 21:19:25 UTC，原接续MainPID1089228仍active，同一训练协调器继续，
已17/75作业完成；RNN seed2026102802 candidate02到23160更新。
MemoryCurrent808775680bytes/MemoryMax3221225472，swap0、OOM及oom_kill均0；
没有最终MODEL_LOCK。进度从本轮早先13/75增加，不是只凭service active判断推进。
该候选在途validationMSE不是最终选择，也不构成三家效果结论。

接下来完成原75作业和9模型锁定/审计，再运行已准备的v8真实场景18回合诊断。
优先核对棍推接触—蹭过与球撞末段的实际学生误差积累：若教师历史拟合尚可、
学生自身轨迹却偏离，则进一步检查状态覆盖和闭环误差，而不是继续改teacher掩盖学习问题。
依证据决定有限修复，不预设ESN必胜，不改共同数据/预算/验证选择规则。
之后才进行原12×9回归108六指标与独立物理/动作/filter审计；当前12不是未见集。

原全30数据及教师修复已共享，见[完整采集报告](NONRL_V8_FULL_COLLECTION_AND_FITS_20261029.md)。
本轮新诊断当前仅本机/Git待发布，归档核验后追加准确共享收据。实际计算主机airpig；
无RL、子agent、服务器计算或删除。开工实际fetch/read main4b413840ae3ac41c3c7cda8d2942700cefdd386b，
baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d；前轮实质progress，本轮新增学习定位属progress。
Goal active，尚不能宣称ESN或主矩阵修复。
