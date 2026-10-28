# v8真实场景18完成；原108回归仍暴露学习迁移失败

当前结论：**主矩阵尚未修复**。三真实场景的开发诊断已完成，ESN与RNN各6/6合格，
MLP为4/6；但原108回归首条件中，ESN seed1提前碰柱终止，RNN seed1未进入抓取。
小验证误差、真实场景诊断通过、动作重放正确，均不能替代最终任务成功。

## 已完成的18回合

原学生服务PID1160099在2026-10-28 22:53:25UTC自然结束，未重启。
完整review状态`complete18_diagnostics_not_success_certification`，18条配对的
teacher/student场景、配置、seed、源码与actor重放通过；50帧互斥分窗完整覆盖，
窗口误差加权重建与全段MSE一致。完整源hash已复核。

| 方法 | 开发资格通过 | 棍推00持续回位/开始撤棍 s | 棍推08持续回位/开始撤棍 s |
|---|---:|---:|---:|
| ESN seed2026102801 | 6/6 | 7.76 / 12.80 | 7.48 / 12.85 |
| RNN seed2026102801 | 6/6 | 8.64 / 12.76 | 7.88 / 12.81 |
| MLP seed2026102801 | 4/6 | 10.56 / 12.76 | 10.80 / 12.81 |

MLP两条棍推失败：00最大外穿透0.244815881mm，08为0.236987226mm，均超过原0.2mm。
00确实发生手部接触且行为顺序满足；08还缺少要求的手部物理接触。后者数值上的
回位时刻不补足接触资格。所有球/角诊断合格，失败未删除、未放宽判据。
这些身份是train00/validation08，不是未见测试；此表也不是最终Task/Strict矩阵。

[完整review](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COMPLETE18_REVIEW.json)
SHA256 `3cde0be3dc7ca12838394ffb480a6093df7a3656885c4a23e28ab1bfc64f42f4`；
[完整execution](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COMPLETE18_EXECUTION.json)
SHA256 `1ef8766def959507d80761adf4cf709089c0da860671381f662757ac19aaac1e`。
[下一阶段决定](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FROZEN108_DECISION.json)
SHA256 `3e9523eaed7d24813e29c8f685e3a9d393de30008e4c358f4fbd86e40b5a6cdb`。
九模型不按这18条或后续108重选，三seed仍全部进入原108。

## 原108真实启动及首两条独立诊断

唯一`sii-special-frozen108-v8-20261029.service`是**用户级服务**，MainPID1172675、
start32623702，22:56:19UTC启动。22:56:24开始物理评测，前置完整fit audit通过，
SHA `a57ab9ead1dcb999cc3d26ab0f015685846872d80df1d5958477517051713104`。
资源3GiB/swap0/CPU100%/数值线程1/单模拟器，宿主已核active、OOM0、实际swap0。
查询系统级同名单元会显示inactive，不能据此重复启动。
[登记](evidence/NONRL_INTENT_RECOVERY_20261029/V8_FROZEN108_REGISTRATION.json)
SHA `173e2abfa083e71bbfedd642d2e20a4e16e9d84d23c70a356507d8ec77d14b06`。

目录`code/mujoco_6d_vmc_benchmark/outputs/special_scene_frozen108_20261029_v8`，
原12条件、九锁定模型、MJB/dt/gate均保持。旧12已被检查过，只称回归。

本轮独立复核最先完成的两条：源清单、checkpoint/config/原物理文件hash、actor/filter收据、
保存子步RMSE/峰速/峰矩/穿透及舒适分母全部一致。无新物理积分或模型更新。

| 条件000，seed2026102801 | Task/Strict | 运行时长 s | 终态 | 最大外/边角穿透 mm |
|---|---|---:|---|---:|
| ESN | false / false | 4.84 | lift；全局穿透中止 | 2.781482 |
| RNN | false / false | 55.00 | approach；未抓起 | 0.087015 |

ESN最严重接触对是`office_v5_pillar`与几何70，actor/filter重放误差0。
RNN重放误差同为0。因此没有证据把这两条的失败解释为导出文件不一致或公共滤波执行错误。
仍需区分学习近似与闭环状态覆盖，不能由此推断系统没有其他bug。

仅用12600训练帧统计18个实际使用观测字段范围，逐元素标量复算与数组计数完全一致：

- 路径方向Y训练范围约[-0.380750,0.380750]；测试初始为-0.990283。ESN只前4帧超该范围，
  不能说它整条失败由该方向造成；RNN1375帧均为此方向且停在approach。
- ESN抬升71帧中约90.14%至少一个选用字段超训练范围，2.32秒起估计Fz首次超界；
  后续估计Fx达219.345N、Fz达72.087N，对应训练最大3.955N/2.871N，随后碰柱中止。
- RNN早期速度误差超范围、后续位置误差超范围；这也可能是动作偏差积累的结果。

逐维区间不能检验联合分布，后期超范围不能单独证明因果。原五接触通道还不含
unexpected_edge，不能把五通道为零解读为无接触。
[完整前缀诊断](evidence/NONRL_INTENT_RECOVERY_20261029/V8_REGRESSION_PREFIX2_DIAGNOSTIC.json)。
复现工具`code/mujoco_6d_vmc_benchmark/tools/diagnose_v8_regression_prefix_20261029.py`，
`--preparation outputs/special_scene_frozen108_preparation_20261029_v8 --count 2 --output <新文件>`。

## 后续修复的证据边界

此前同v8 teacher配置在office000的独立控制已Task/Strict同时通过，见
[原teacher审计](evidence/NONRL_INTENT_RECOVERY_20261029/VERTICAL_DAMPING_OFFICE_AUDIT.json)。
结合新三场景teacher30/30、ESN开发6/6与原回归失败，优先检查学生对跨方向、
任务阶段及扰动后恢复状态的近似与覆盖；不再只盲目调整teacher阻尼或把问题归咎ESN步数。
这仍是单个综合控制条件的证据，不能扩展为teacher全12通过。

当前108继续收全。后继修复若需增加采样，只在三真实特化场景内登记方向/阶段/
恢复状态变化，保持真实棍推接触—让位—蹭过—撤前持续回位资格；不能拿综合测试轨迹
作为新训练标签。三个学习方法继续共享数据、划分、候选预算及验证选模规则。
任何新模型须独立run，原失败与当前模型保留；不改在途绑定源、不据测试选checkpoint。

最终六指标仍待完整108及审计：Task、Strict、双成功条件SPT、所有回合平均峰矩、
实际接触dt加权舒适代理、机器合规率。SPT参考取完整108的最短双成功时间；
无人接触为NA而非100%，舒适代理不是人体标定。Goal active，不宣称主矩阵已修复。

开工及续接实际fetch/read main d36a7990、72d92390，baseline f6e8f8c。
另一agent的RL日志保持；本轮无RL操作、子agent、服务器计算或数据删除。
完整18归档已逐405载荷文件核验，并在服务器暂存/最终目录复核大小及SHA，完整共享于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_complete18_20261029_v1/FULL_PROBE.tar`。
1683322880bytes，SHA `3b25449b58253e5af874d31a0e933a9f60ba3d1f50766c1702845cf20520c374`。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_COMPLETE18_SHARED_RECEIPT.json)。
不含在途108或后补前缀诊断；这些当前仍本地与Git小证据保存。

23:05UTC原108已完成3/108，MLP seed1也完整55秒停在approach、Task/Strict=false；
ESN seed2在途。此第三条尚未运行本轮前两条的独立子步复算，不能冒称三条均已独立审查。
