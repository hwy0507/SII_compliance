# 2026-10-26 参数cycle6与官方SERL cycle2审查、冻结验证及后续训练

原Goal继续active，尚未收敛。本文接续RL_CYCLE05_REVIEW_AND_CONTINUATION_20261026.md，
优先于历史关机paused及旧PID记录。执行产物都在本集群SSD
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`（下称B）。
本轮fetch/read main=d8dd13e44e567e2aa9b160cf83ba40c0c88a8cbc，baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。
已快进main；另一主机非RL第二条件9回合审查是独立工作，未干预其运行。

## 新完整周期

| 方法 | 周期编号 | 累计transition / critic更新 | Task / Strict，各30 | 平均reward | 终端Q MAE |
|---|---:|---:|---:|---:|---:|
| 官方SERL Direct | 2 | 123196 / 945576 | 0 / 0 | −33.52447 | 2.34804 |
| CHEQ Impedance | 6 | 285750 / 280751 | 18 / 17 | −2.29317 | 2.94187 |
| CHEQ Admittance | 6 | 284750 / 279751 | 15 / 14 | −8.59121 | 2.41212 |
| VMC all5 target试验 | 6 | 285750 / 280751 | 17 / 16 | −4.53645 | 29.31883 |

三参数均新增41250条、30个完整55秒回合，无提前终止。Direct新增40872条，29完整回合；
active_short_train_0500于997动作因global_penetration_exceeded_2mm提前结束，失败保留在30分母。
全部父replay字段前缀精确保留；每条新reward按冻结SPTReward及interval journal重建，最大误差0；
新reward/done、30terminal标签、条件fixture、MJB、参考计划、完整learner/optimizer有限性核验通过。
Direct另核验canonical48、归一化动作映射和nextstate。此审查不是原始物理子步独立重算。

Direct周期reward −34.2233→−35.1020→−33.5245，三个周期仍全失败；终端Q MAE9.95→4.09→2.35。
90条历史终端×10critic的误差中位数.0702，但p95仍37.19，不能只报平均误差掩盖尾部。
固定4096条诊断replay Q均值12.462、TD MAE.02184、alpha.0003663；固定随机双target仅是诊断，
不等于重放全部训练target。cycle2图显示Q先升到约19再降至12.5，loss大部分.001–.005且有尖峰；
完整网络/优化器/RNG诊断前后digest相同，0训练更新。图已目视检查，不构成健康收敛结论。

参数cycle6 I的Strict18→17、reward反弹；A的Strict12→14、reward改善，但尚不稳定。
VMC all5使平均Q从约249降至175，却使terminal MAE16.01→29.32，loss约50升到150–250；
replay Q范围−267.85至855.83，p95约589.01。不能把Q均值下降当作问题解决。
in-bag终端MAE I/A/V=2.247/1.959/25.268，out-of-bag=5.654/4.171/44.485。
已有登记cycle7继续，不在周期中修改设置。完整cycle7审查后才决定下一参数阶段，不自动延长。

审查产物：B/runs/reviewed_cycle06_audit_20261026_v1（REVIEW、health/DIAGNOSIS及图），
B/runs/serl_cycle02_review_20261026_v1（REVIEW、DIAGNOSIS及图）；精确checkpoint在
B/runs/reviewed_continuation_cycle_archive_20261026_v1。代码、小证据SHA映射见文末SOURCES。

## Direct冻结策略三代表诊断

新通用入口code/mujoco_6d_vmc_benchmark/tools/evaluate_serl_state_20261026.py实际加载官方
SERL及冻结完整checkpoint，仅支持确定性动作；拒绝未实现的随机策略选项。核对source_adapter
全部hash、注册、模型与checkpoint；物理采样使用B/env/bin/python，JAX使用B/serl_env/bin/python。
原canonical48、动作映射、WBC/filter、MJB、gate、dt5e-5和55秒保持不变，0optimizer更新。
完成时要求full learner state digest与初始完全相同。

预先登记passive_corner_train_0000、active_short_train_0000、active_long_train_0000三例，
不是完整30条件比较，更不是最终收敛验证。输出B/runs/serl_cycle02_fixed_representatives_20261026_v1。
checkpoint cycle2 SHA为6b4c64daa94ab1c73096a15d34131d1ae2538db104a55071161ec71bebb0896e。
启动后独立核验已落盘被动1375动作、短期975动作，共2350个，直接调用官方deterministic
sample_actions再手算首维仿射映射，与物理journal误差全部0；MJB、canonical48、800子步/40ms通过。
这是当时进度快照，不冒称剩余动作已核验；ACTION_REPLAY_REVIEW.json保持不可变供下一阶段登记引用。

原协调器144052计划的后处理命令遗漏必要CLI参数，发现后仅终止父协调器；原评估器144056及
物理子进程完整保留，没有重启回合或重复采样。替代只读后处理215406记录原PID/start ticks，
等原三例完成后运行物理汇总、filter与torque独立审查。原代码/日志/移交收据保留，修正记录在
POSTPROCESS_HANDOFF.json、POSTPROCESS_LAUNCH.json。FINISHED只表示脚本完成，还须科学审查。

收尾三例已完成，FINAL_SCIENTIFIC_REVIEW.json独立核对全部4125个确定性动作，最大误差0；
330万物理子步的接触/力矩/穿透/时间聚合与原记录一致，公共filter与力矩投影重放均通过。
最终learner完整digest不变，0optimizer更新。三例Task/Strict均0/3、全55秒、全approach，
没有机器安全违规；三例人体接触均0，舒适比率必须NA，不能声称柔顺改善。
被动/短期/长期各回合最大关节力矩50.21/49.56/66.89Nm，第一动作通道平均slowdown
.515/.384/.462。动作统计是行为描述，不是因果诊断。完整30条件或最终ESN/SPT仍未完成。
原评估及后处理已结束，不重新启动；保留失败结果，不因无接触或低loss宣告成功。

## 新正式SERL续训及参数收尾

SERL原cycle2进程3339709已经正常结束，勿重启。根据完整周期reward/Q诊断与实际动作重放，
独立登记保持全部设置的两周期cycle3/4，B/runs/serl_reviewed_cycle03_04_20261026_v1/direct，
PID521120、GPU0、CPU0–12、12sampler。未引入辅助权重，完整网络、Adam、replay、RNG及旧周期history
保留，batch32768、官方十critic/随机双target/无熵backup、8critic:1actor、零示范来源均不变。
这是继续检验不足的在线学习证据，不是宣告batch有效或机械重复已完成辅助实验。

新入口resume_serl_reviewed_stage_20261026.py只允许有限阶段元数据变化，不允许batch/学习配置变化；
精确父checkpoint、父registration、源码、cycle/health/action审查hash及其checkpoint对应关系均验证。
check-only正向通过，改变UTD、critic_clock、batch、阶段预算的负向检查均拒绝。
实际新阶段新增1000transition/8000critic更新时，父123196条replay各字段前缀精确、旧history和
官方config/source不变、12实际MJB及完整state有限性通过；证据B/runs/serl_reviewed_cycle03_startup_20261026_v1。
新的只读精确归档器533451在B/runs/serl_reviewed_cycle03_04_archive_view_20261026_v1，
输出B/runs/serl_reviewed_cycle03_04_archive_20261026_v1；按原learner身份跟踪，结束即退出。

原参数I3070037/A3070069已完整cycle7结束，勿重启；V3419078仍按已登记cycle6/7预算，GPU3/CPU39–51。
新的只读cycle7协调441621在B/runs/reviewed_cycle07_audit_20261026_v1等待准确归档：
以cycle6为逐字段prefix和新transition审查父，另核验原prepared cycle5的stage恢复hash；
随后诊断完整cycle7，0新物理/optimizer更新。原归档3494331继续，勿重复派发。

## 收尾I/A完整cycle7与独立续训

I327000transition/322001更新，Task/Strict18/17，reward−2.34905；A326000/321001，15/15，
reward−6.90047。均30完整55秒、各新增41250条、父cycle6 replay全字段精确、新reward重建误差0。
各自cycle7的REVIEW已落盘，统一REVIEW仍待VMC，不把部分结果当四路完整收敛。

为在VMC收尾期间及时作出I/A决策，单独只读诊断B/runs/reviewed_cycle07_ready_ia_health_20261026_v1。
I/A终端MAE3.6488/1.9511，in-bag2.8501/1.3422，out-of-bag6.7443/4.3229；
Q均值27.90/28.23，末1000 Qloss3.505/5.866。图已目视检查：I/A loss都有上升趋势，
虽然A的Q偏高减轻和终端误差改善，仍不能判定优化健康。I两周期reward近似稳定但未恢复cycle5最佳值。

据此只登记再两个完整周期8/9，保持I原LR和A已降低的actorLR3e-5，完整checkpoint直接恢复，
本次不修改learner/replay/RNG，也不清空history或导入辅助权重。实际使用原冻结trainer的
completed_stage_continuation校验：parent_cycle7、new_cycles2、factor=None、准确父LR。
准备脚本首次误用不含torch的系统python，在导入阶段失败，未创建产物/派发任务；已用冻结解释器
重试并通过，PREPARATION_RETRY.json保留原因，不是训练失败。

新run B/runs/clock_parameter_reviewed_cycle08_09_20261026_v1/{impedance,admittance}/train，
I806847/GPU1、A806849/GPU2，原CPU13–25/26–38，各12sampler；独立归档806853在
B/runs/clock_parameter_cycle08_09_archive_view_20261026_v1，输出clock_parameter_cycle08_09_archive_20261026_v1。
实际I/A新增3000/4000transition及同数optimizer更新后，父327000/326000条replay全部字段前缀精确，
旧history、原actor LR、target2、完整state有限性及各12MJB核验通过，证据clock_parameter_cycle08_startup_20261026_v1。
科学决策/精确父checkpoint/协议验证在SCIENTIFIC_DECISION、PREPARED和LAUNCH.json，需再次完整边界审查，
不自动延长。VMC未纳入此新阶段；其all5风险必须等完整cycle7审查处理。

## 当前GPU实测

新60样本窗口实际66.43秒，GPU0/1/2/3均值为62.53/23.48/27.33/48.10%。
GPU0含真实SERL续训和冻结推理，其他卡是参数cycle7尾部，未运行辅助训练。尾部仅剩少数物理
采样器使I/A占用下降，四卡50%要求仍未满足。证据B/runs/reviewed_cycle07_gpu_monitor_20261026_v1；
这是实测占用，不把短窗口、混合评估或训练性能当作收敛。

## 发布与剩余事项

小型证据见docs/evidence/rl_cycle06_serl02_20261026/SOURCES.json，逐文件列真实SSD来源与SHA。
源码副本仅供审阅，实际冻结runtime及大checkpoint/原始轨迹留SSD，没有宣称已同步另一主机或
HDD旧关机快照。HDD剩余约544MiB，因此备份只放更新文档和小型manifest。

仍待：参数完整cycle7及优化健康决策、Direct完整cycle3/4、三代表最终独立审查、足够稳定的reward
与loss、最终完整冻结策略矩阵/指定ESN/统一SPT。GPU每卡50%也不能宣称达成；不使用重复辅助计算填占用。
