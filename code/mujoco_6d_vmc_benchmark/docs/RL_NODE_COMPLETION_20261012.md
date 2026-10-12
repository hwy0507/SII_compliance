# 10月12日 RL 未完成节点接续与兼容性试跑记录

## 研究边界

用户在核查过夜结果后授权“继续推进”。本轮目标先将唯一未完成的
`parameter_impedance_historical_entropy` 从已保存的 97,625 步接到原 165,000 步节点，
随后同八个 development 条件重评。其余六组已完成节点按原 checkpoint/hash 引用，不重跑。
仅本机计算，不动 Spark 算力或显示设置；不解封 final、不改环境、Task/Strict、actor、
执行器限制、奖励、网络或训练超参数。训练继续原 500k 优化器日程；165k 是本次补齐上限，
不是收敛证明。后续更大节点须先复核学习曲线与失败原因，不自动无限追加步数。

本轮远端 main `8de2df9d5c5b23a7803d0b7f375f3d1427de4abc`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 已在宿主机 fetch 并读取更新日志。
未跟踪的根目录 `docs/MEETING_FLOWCHART_IMAGE_PROMPTS.md` 未动。

## 上轮真实收口

2026-10-12 12:01:50 CST 到达派发安全截止，最后一组完成当前回合、保存到 97,625 步，
12:02:14 结束，`stop_reason=deadline`。上层把有限停止记录成 `failed_preserved`，
不代表该 checkpoint 损坏或整夜没有训练；原收据保留。

| 配置 | 实际步数 | Task | Strict | RMSE mm | 每回合峰矩均值 Nm | 每回合峰速均值 m/s |
|---|---:|---:|---:|---:|---:|---:|
| direct_office_task | 163927 | 0/8 | 0/8 | 20.088 | 40.531 | .3447 |
| parameter_impedance | 165000 | 0/8 | 0/8 | 21.352 | 50.136 | .3752 |
| parameter_admittance | 165000 | 0/8 | 0/8 | 27.241 | 40.055 | .3799 |
| parameter_vmc | 165000 | 0/8 | 0/8 | 28.956 | 37.755 | .3722 |
| direct_metric | 163928 | 0/8 | 0/8 | 225.327 | 53.887 | .3570 |
| direct_office_task_historical_entropy | 163972 | 0/8 | 0/8 | 66.697 | 51.004 | .1849 |
| parameter_impedance_historical_entropy | 97625 | 未完成 CUDA 开发评估 | 未完成 | — | — | — |

前五组均完整 55 秒；直接 RL 历史熵配置八条均为物理早停，保留在成功率分母，
其较低峰速不能与完整时长回合混作优势。该表为 development、正式步长 `dt=5e-5`，
不是 final 测试。经典90次有限搜索已完成不等于90个测试条件，也不在此表冒充新结果。

上轮终局小包已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_longrun_report_20261011_v1_006/evidence/`，
12文件264418字节，manifest `79990c02ccba8711308f6de4b374553e93b6512b0c2934de6952375dfa4de51c`。
仅含小型报告/审计，未声称完整大型轨迹或权重已归档。

## 本轮操作偏差及纠正

1. 沙箱内无法连接用户 systemd bus，且看不到 `/dev/nvidia*`。此前将此误报为宿主机驱动故障，
   这是 agent 的诊断错误。13:43 CST 宿主机直接检查 RTX 5080 Laptop GPU 正常（16,303 MiB），
   没有驱动故障证据。网络也在宿主机正常；不把沙箱的网络错误当作 GitHub 不可用。
2. 首次直接 CPU load 因 CUDA Orbax sharding 失败；用当前网络/归一化结构作为恢复 target 后能加载。
   首次直接进程没有3GiB cgroup，被 worker 主动拒绝；之后恢复受约束用户服务。
   第一次 manifest 含相对训练协议路径，切换工作目录后失败，另存绝对路径 manifest 后才成功。
   这些均发生在物理仿真前，不能计为算法失败。
3. 该 CPU 兼容性试跑实际只评估 97,625 步 checkpoint，目录名仍带历史 `step165000`；
   必须以权重内部步数为准。恢复改动只涉及 upstream 的 network/normalization 读取 target，
   未训练或改权重。原生 CPU actor replay=0 仅证明 CPU 内部重放，不能证明 CUDA 数值等价。
4. 兼容改动曾直接施加到共享本机 runtime，破坏原冻结 hash；本轮将两份实际源码另存证据，
   八条 CPU 试跑结束后按原 hash 恢复，再允许 CUDA 续训。CPU 试跑单列为开发兼容性探针，
   不纳入注册的七配置 CUDA 节点矩阵，不拿失败筛选权重。
5. 临时 shell 队列的部分外层收据缺少完整命令和 hash 映射；不事后改写旧收据伪装完整。
   `audit_rl_cpu_probe_20261012.py` 独立核对内部实际执行、条件/模型/权重、动作/参数重放及
   物理子步，并明示这个出处限制。后续接续统一用受检 Python 协调器写入完整命令、源码及收据。

## 接续实现与验收

`tools/complete_rl_node_20261012.py` 使用独立目录和全局计算锁，只有一个模拟器，
1数值线程、每worker MemoryMax3GiB/禁swap，启动可用内存≥4GiB、磁盘保留40GiB。
这是单路接续，不满足7GiB两路准入时不再派发第二路。原 checkpoint 包含 replay、optimizer、
RNG、归一化及 episode-boundary 状态，续接前逐文件 hash 核验。

准备时核验六个既有 CUDA 开发节点与权重，复制被冻结 source；派发时再次核对全部 runtime、
参数源码、模型/条件协议。训练只补到165k，在完整回合边界停止；每条新训练轨迹和开发轨迹
进行参数审计，八条开发完成后独立复算物理子步。输出 `SEVEN_METHOD_DEVELOPMENT.json`。
单独登记本次授权及12小时安全派发截止，不延长旧登记，也不因到点强杀在途回合。

子失败必须传播非零退出码，不覆盖失败目录。独立连续监视与汇总沿用现有工具，
缺失节点为pending，监视失效请求回合边界保存停止。没有定时任务，也没有新服务器实验。

## 已核验结果和运行状态

14:09:42 CST：首条新CUDA训练回合完成55秒，已99,000步/188,002次更新，新增2,750条
优化器记录全部有限，进入episode72。该训练回合Task/Strict失败、停carry，
三指标22.845277mm/36.008171Nm/.378133m/s；独立重算1,100,000子步、核对模型/轨迹/动作链通过。
审计工具新增可指定注册方法的`--names`，原默认两路行为保留，不修改训练。
首回合证据已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_completion_first_episode_20261012/evidence/`，
3文件15,390字节，manifest `3d2cee03550fa967471b0a856319db6c86245d72936fd0afd93fcdf30c7c7e59`。
这证明真实训练恢复，不是冻结策略评估或收敛；165k新checkpoint和其8条开发评估仍运行/待完成。

14:01 CST：CPU八条均完整55秒，Task/Strict `0/8`，全部停在carry；三指标均值为
`22.819469 mm / 36.279807 Nm / 0.378260 m/s`。`audit_rl_cpu_probe_20261012.py` 独立复算
8,800,000物理子步、核对条件/权重/动作/参数链，审计通过。原runtime已恢复并通过完整
`RUNTIME_HASHES.json` 核验；SimbaV2工作区清洁。原CUDA对11,000个保存观测重放，
动作最大绝对差 `7.103197276592255e-6`，归一化hash一致、权重hash未变、梯度更新0。
这不是逐位相同或闭环轨迹等价证明，因此CPU结果仍不并入CUDA主表。

14:02:50 CST：单路CUDA训练启动，独立run为本机
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/completion_20261012_v1/`。
登记SHA `4216b0325331bb9c55dc6b77f8c8454e8182c2bc82c14861abbf11735cf6f164`，安全截止
2026-10-13 02:01:42 CST（本轮12小时有限上限）。14:05监视快照显示98,000步、186,002次更新，
高于继承97,625步/185,252次更新，首完整新回合尚在执行；不能仅凭service active声称训练完成。

运行服务为 `sii-rl-completion-20261012-v1`、`sii-rl-completion-monitor-20261012-v1`、
`sii-rl-completion-report-20261012-v1`。后两者不增加仿真。监视每30秒核对真实步数及故障，
汇总每60秒更新当前节点并在完成时归档小包。训练、八条件评估、最终七配置汇总仍待完成。

源码/设置/CPU探针审计小包已逐文件核验发布至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_completion_setup_20261012/evidence/`。
609文件，5,340,373字节，manifest
`160425ee4230959cd901d21500cec61cbbdf0db42bb93a3bf5f39639e23fecd5`。
实际冻结源码在该目录的 `source/`；CPU恢复源码快照、实际临时派发脚本、审计及CUDA重放证据
在 `cpu_probe/`。文件是本轮运行专属未提交源码快照，不冒充干净Git源码。

启动汇总小包也已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_completion_report_20261012_v1_001/evidence/`，
4文件33,062字节，manifest `88fbb4fbf03859118d3e2e7df7bf9f8f2b41503d0a640e9a4750ee34cc2f5e78`。
这个启动包没有新的完整CUDA开发成绩。CPU原始大轨迹和所有训练权重实体仍在上述本机outputs中。

验证：新协调器3项失败传播/防覆盖/父节点验证，监视与汇总8项检查，以及既有收敛停止规则6项
检查通过；冻结副本的独立import通过。未改科学判据，未将合法卡住当实现故障，也未宣称RL收敛。
