# v8公平拟合全部完成，九模型审计通过，真实场景18回合诊断已启动

最新已完成18并启动108，见[完整诊断与回归失败定位](NONRL_V8_COMPLETE18_REGRESSION_DIAGNOSIS_20261029.md)。
18开发资格ESN6/6、RNN6/6、MLP4/6；原108首ESN/RNN失败，主矩阵尚未修复。
下文“18在途”等为保留的历史快照，不能据此重启。

22:38:07UTC覆盖：原1160099继续，已3/18结束，正在rod08 ESN。rod00 MLP任务true、
让位/蹭过/持续回位均满足，但穿透0.244815881mm超过原0.2mm，因此资格failed_preserved。
40万保存子步独立取max、原输入hash及actor/filter重放0已复核；scene_contact_valid=false
来自行为资格包含穿透检查，**不是没有棍—手接触**。不改门或换模型。
[失败资格原件](evidence/NONRL_INTENT_RECOVERY_20261029/V8_STUDENT_ROD00_MLP_QUALIFICATION.json)。

科学78b29b1d及安全合并5c96fde0已push/核远端，双方日志逐字保留；同科学commit源码/
小证据1218文件7820185bytes/SHAe800ac31与当时准确报告5502bytes/SHAd038543e已核共享
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_complete_fits_source_20261029_v1/`。
[源码共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COMPLETED_FITS_SOURCE_SHARED_RECEIPT.json)。
该源码小包不含此后MLP失败收据或后补文本；在途18原物理仍本机，完整后独立归档。

22:36:26UTC：原1160099活跃，已完成2/18，rod00 ESN与RNN均qualified，
原队列继续rod00 MLP；内存656297984bytes/3GiB/swap0/OOM0。完整18仍待。

完整拟合包已核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_complete_fits_20261029_v1/COMPLETE_FITS.tar.gz`。
141956439bytes，SHA256 `a670e2cd30c68ca47fff7eb9ccc0466a17f487360fb19e15d8e9ac6bd882e9db`，
900个载荷文件及1个manifest。包括全部未选中候选，不包含在途学生18或尚未执行的108物理轨迹。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COMPLETE_FITS_SHARED_RECEIPT.json)。

## 已完成的训练与审计

原训练2026-10-28 22:31:14UTC自然结束，75/75作业全部complete；原handoff
1089228退出，service inactive/success/MainPID0，状态fitting_complete_pending_test_review。
22:04:50–22:31:20实际54次观察，前53次同PID/start31715901活跃、53→74完成，
最后一次确认自然终态75；不是观察超时后重启。
[完成观察](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FIT_COMPLETION_OBSERVATION.json)。

共同数据仅来自v8三真实场景新30：24train/6validation，共15750帧（12600/3150）。
训练数据SHA `527bb7341e19b2345f16c04bb48d9b6b9dd643e9d1beeda0b8bb8228cb520805`。
每家每seed12候选，三seed2026102801/02/03；3个ESN搜索各12候选，加72个神经拟合，
共75作业/108候选。神经每候选32000更新、同seed共同曝光序列；ESN解析ridge。
这是相同候选数和验证规则，不是相同FLOPs，也不是神经训练收敛认证。

完整审计核验全部30数据重建、75收据/候选hash、预算/源、每seed神经曝光序列一致、
六validation最小requested-action MSE选模。九个选择模型各在全部15750帧上使用冻结
测试runtime重放，导出与实际actor最大误差均为0。
[完整审计](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COMPLETE_FIT_AUDIT.json)，SHA
`53345419bc68b0075d02675d324bc0f3169484266a8070d32ae91753b62b3d5c`。
[九模型锁定](evidence/NONRL_INTENT_RECOVERY_20261029/V8_MODEL_LOCK.json)，SHA
`0bf736fd0aa14455975752851dd22f6c902e116b1f0ca1940977970c769ee61c`。

| seed | ESN验证MSE | RNN验证MSE / 候选 | MLP验证MSE / 候选 |
|---|---:|---:|---:|
| 2026102801 | 3.082290e−5 | 1.120709e−5 / 05 | 8.923892e−5 / 07 |
| 2026102802 | 2.613990e−5 | 1.095225e−5 / 07 | 8.189934e−5 / 06 |
| 2026102803 | 2.585598e−5 | 1.060905e−5 / 03 | 8.873214e−5 / 08 |

RNN模仿误差最低，ESN其次，MLP最高。这是归一化requested-action误差，
不是Task/Strict、SPT、力矩或闭环排名；此前ESN关键恢复段残差不能因此忽略。
不得根据接下来18/108结果重新选择本批checkpoint。

## 真实场景18诊断的实际执行

原预登记PREPARATION SHA `77fedd0ea523c5d26c773d672a5828fd6420a5d6a93720fb9fb19f4dff3c285b`，
196源码hash启动前一致。原拟合完整并inactive后启动唯一
`sii-special-student-closure-v8-20261029.service`，MainPID1160099/start32477328。
运行目录`code/mujoco_6d_vmc_benchmark/outputs/special_scene_student_closure_20261029_v8`。
22:31:59UTC实际开始；先完整fit audit通过，再写登记并进入学生物理闭环。
[登记](evidence/NONRL_INTENT_RECOVERY_20261029/V8_STUDENT18_REGISTRATION.json)，SHA
`5d42f67a50c59669cfcc4c4e9df6f9ea00988a058c96a0d01fa5600d07f0b4b1`。

固定seed2026102801三家模型 × 三真实场景 × train00/validation08，共18；
所有三seed仍用于后续108。单模拟器/数值线程1/CPU100%/MemoryMax3GiB/swap0，
22:33:05宿主systemd/ps均确认同PID活跃，内存713699328bytes。沙箱PID不可见后
实际宿主复核，未把隔离误判为退出。归档单独半核/1GiB，无额外模拟器。

首个rod00 ESN已完整20秒500动作步结束，原资格qualified，actor/filter回放0，
原棍行为检查全部通过：接触4.734、让位4.840、蹭过7.360、持续回位确认7.760秒，
撤棍12.800秒，提前5.040秒。原件输入hash及事件顺序复核通过。
[资格](evidence/NONRL_INTENT_RECOVERY_20261029/V8_STUDENT_ROD00_ESN_QUALIFICATION.json)、
[行为](evidence/NONRL_INTENT_RECOVERY_20261029/V8_STUDENT_ROD00_ESN_BEHAVIOR.json)。
这只证明训练身份rod00的开发场景表现；不是全18、新条件泛化或冻结主矩阵通过。
随后原协调器接续rod00 RNN，余下结果尚待，不启动重复作业或据此提前108。

## 未完成与后续

完成原18后，复核全部失败及teacher历史模仿、学生真实actor回放、学生轨迹上的teacher
反事实差异，再决定有限修复或推进108。反事实不是实际teacher物理轨迹或新训练标签。
此前ESN球撞恢复低估/过量并存的证据仍有效，不以首个棍推通过掩盖其他场景问题。

最终仍需当前12×九模型108回归，报告Task、Strict、双成功条件SPT、全部回合平均峰矩、
接触时长加权舒适代理、机器合规率及完整审计。当前12曾被查看，不能称未见确认；
舒适代理不是人体安全标定。原失败和旧综合结果保留，不作主结果。

开工实际fetch/read main97c4dd8895a89d506fb8e346971ae04c2c2e01bf、
baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d。实际计算airpig，无RL、子agent或
服务器计算。完整拟合已共享；在途18原始物理仅本机，完成后独立归档。Goal active。
