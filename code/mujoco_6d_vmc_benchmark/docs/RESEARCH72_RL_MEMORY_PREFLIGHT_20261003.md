# RL learner组合内存预检

## 2026-10-04 02:51UTC 真实续训起点独立动作重放

parameter_vmc301、parameter_admittance301均真实继承5500步/4回合/1002更新，并执行第5回合train028。
各首续训回合完整保存至6875累计步，学习计数持续增长；不是把旧checkpoint文件存在当作已续训。
新的独立进程重载原父checkpoint、核对源码/配置/先验/条件顺序/累计计数，使用实际新轨迹首observation，
以training=True及pending=None重放第一个随机动作。两者与实际记录逐值相等，max_abs=0。
重放只在内存将interaction/observation计数5500→5501，reward计数和1002更新保持；磁盘父权重及所有不可变证据hash未变。

本次每个审计仅一次actor调用、零梯度/物理/封存读取。它验证接续首动作的权重/随机状态/观测归一化路径，
**未独立重构此后每次优化器更新，也未验证续训后replay完整前缀或最终冻结策略**。
六项合成回归检查拒绝错误seed/源、重复条件、计数重置、不完整父阶段和错误首动作/RNG；合成检查不当真实训练结果。
两审计使用原生Spark NumPy2.2.6/JAX0.7.2 GPU，单线程/3GiB/无swap，墙钟分别7.563/7.391s；没有增加仿真并发。

以下为共享本轮根（主机/完整地址见后文）的新`rl_resume_action_audit_v1/`：

- `VMC301_FIRST_ACTION.json` SHA `ab492d2cae78ea7721a0b39913de9ad99da4752470a05af17ed8235d06aa9ef7`。
- `ADMITTANCE301_FIRST_ACTION.json` SHA `4add155e9f0c35426a247e17499bbe5c692608a3371ed2a099b0cbb188387bda`。
- 两原件与Git证据RL_RESUME_*同字节，保存审计时child execution完整快照及其hash；正在增长的原文件不被改写。
- 三源/测试文件归档核验，审计源码SHA `dd38ffa8df4f6c6cc9b63edd5f8a0ea0251f277e5cd27eb3979ae175f94b0e96`，
  原始源tar SHA `ff9a4cdc27de1b18d2e225e320d21690977421aecd5dd42a20b9e43167154039`。

十个模型已完成首段。新增VMC303为5500步/1002更新，直接任务奖励303为5168步/338更新、4回合，
其中train031在carry因最大外部/全局穿透2.560352mm触发原2mm中止；未补齐为虚构5500步或删除失败。
新增两个存档核验通过，`rl_saved_state_audit_v3/AUDIT.json` SHA `a094a55f2627298175f4f0609ecd41aafb23e1595992273c443874427e0d5828`，Git同字节。
两原manifest SHA分别1e2e0bbee02db2a4a6bf1cbbaeb6477ad230da9cbdbbcdb0d2a2bd2b613ccfdc、
91ecd9fdabdd7c0dbae2ec24b2ec1a7a7daed9fc090233b27191d0671a486cc9；零JAX/物理审计441ms。
第三队列仍等租约，十模型首段不等于十五模型训练完成。首次续训启动包含冷编译，不以其单回合时间冒充稳态吞吐。

## 2026-10-04 02:22UTC 首个任务奖励直接RL存档

增量复核direct_office_task/2026100302及parameter_impedance/2026100303两个首段，
分别75/74文件、action7/action5；均5500步、4回合、1002更新，全部hash、回放、计数/边界/RNG/源检查通过。
沿用v1已归档的独立审计源码，无JAX加载、动作调用、梯度更新、物理积分或封存读取；不重复审计原六份。
两个原manifest SHA分别为e4966da4931b08328c83d24687c66f2a473f10a3ee7b2183f9f11f7bbc49ecd8、
9f06bd0be697134687832b8fae7796b2f8f11fb2e00780571d2bfab291b46934。
新增结果在下述同根`rl_saved_state_audit_v2/AUDIT.json`，SHA256
`a23428d103a1f393f98c269f837bffa786a99355185d11b28f7f9406a9b6f53f`，Git同字节RL_SAVED_STATE_AUDIT_V2.json。
服务器单线程/3GiB/无swap执行434ms、CPU423ms；这是存档有效性，不是实际续训、收敛或最终任务效果。

02:21:59UTC实际快照：八模型首段完成；q0的VMC303为1375步、q2的任务奖励303为1500步，均未到梯度warm-up；
累计46875交互/8016更新，q1仍等公共仿真租约。q0/q2 memory.max回收事件1240/1263，三queue的OOM/oom_kill均0。
原作业继续，没有提高限制或重复重启；首个真实续训段和三learner稳态仍待核对。

## 2026-10-04 六个真实首段存档独立复核

截至01:49UTC六个模型已完成5500步/4完整回合/1002梯度更新，包含首个真实5维阻抗模型。
新的零JAX/零动作/零梯度/零物理检查对全部六个不可变manifest执行完整文件集合/hash、经验回放、
runner/agent计数、整回合边界、两种RNG可加载、seed条件顺序、44源文件与prior身份核对，全部通过。
各模型的24条训练回合AUDIT与trace hash也逐项关联；这是文件/状态一致性，不替代原始子步审计或实际续训。

| family/seed尾号 | action维度 | checkpoint文件数 |
|---|---:|---:|
| parameter_admittance/301 | 7 | 75 |
| direct_metric/301 | 7 | 75 |
| parameter_impedance/302 | 5 | 74 |
| parameter_vmc/301 | 7 | 75 |
| parameter_admittance/302 | 7 | 72 |
| direct_metric/302 | 7 | 74 |

所有replay为float32且有限，observation/next_observation为5500×48、action为5500×相应维度，
恰4个terminal且末条终止，truncated全0；pending=null。文件数量差异不凭经验判失败，实际集合须与本模型manifest完全一致。
本次未加载官方优化器或做真实恢复更新，不将这些检查称作续训/收敛/最终actor回放成功。
六个首段端到端1560.208–1667.848秒（含首5000步warm-up、启动/保存），仍不是三个learner稳态吞吐保证。

主机arm1@192.168.31.70，本轮根`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：

- `rl_saved_state_audit_v1/AUDIT.json` SHA256 `bb3120147ee90a4c2e90447b373ad44818a39dcc84015380e4d495514a3b4d35`，Git同字节证据RL_SAVED_STATE_AUDIT_V1.json。
- 同目录tools下实际核验源码SHA256 `79c260018f624edbdf684ca7896baabcd986e33b73a17d7335344d082564e46a`、
  checkpoint辅助源码SHA256 `09819072752e8c440b4074bda225829a3351bdfd2ada21c0e512b015ffa9fb3f`，原生NumPy2.2.6，1线程/3GiB/无swap；1.572s墙钟、1.124s CPU。
- 源包incoming/research72-rl-saved-state-audit-v1.tar.gz SHA256 `717b32450b5902a52426740d1871ccb6302277aee4c1bbef422eecbbdd227261`，源与结果均核验。
- 首5D manifest：`rl_office_adaptation_v2/queue_0/parameter_impedance_2026100302/initial_CHECKPOINT.json`，
  SHA256 `b8dfd88edc65ff28e64f9fbc0d26a852f6ad86ccb653d67669c4e5872ec9cf4b`；Git同字节RL_IMPEDANCE_302_INITIAL_CHECKPOINT.json。

其余模型/真实续训仍在进行。第三RL队列仍待租约，历史内存事件与局限继续适用。

## 2026-10-04 00:56UTC真实首段检查

调导纳seed2026100301和调VMC同seed各完成5500步、4个完整训练回合、1002次梯度更新，
已保存真实checkpoint并轮转到下一模型。训练还远未收敛，不能把本节资源/存档检查当作最终任务效果。
对应两个真实queue子服务累计峰值2,867,982,336/2,851,860,480字节（约2.67/2.66GiB），
memory.events max/oom/oom_kill均0，限制仍3GiB/无swap/1线程。父调度服务的低内存不能代表这些子服务。
第三RL队列此时仍等租约；本次不是三个learner同时训练的完整压力保证。

零积分/零更新的独立只读检查：每个checkpoint全部75文件hash与不可变manifest相同；
episode_boundary=true、pending_transition=null；runner/agent/replay累计步和reward_samples均5500；
agent更新数与execution同为1002。回放各数组float32/有限、观测5500×48、动作5500×7，
terminal恰4个且最后一条终止、truncated全0；探索和回放RNG状态可加载，所有登记源文件与prior hash仍一致。
这验证真实保存完整性，**不是实际续训已完成或最终冻结actor回放**；其余模型/首个resume段仍待核对。

主机arm1@192.168.31.70，以下相对目录位于本轮共享根
`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_office_adaptation_v2/`：

| 模型 | 原始manifest路径 | SHA256 |
|---|---|---|
| 导纳301 | `queue_0/parameter_admittance_2026100301/initial_CHECKPOINT.json` | `e7b87d5eeeab012d264488fe4bea6069a502357bd3430251ab8f21980d4ec09f` |
| VMC301 | `queue_2/parameter_vmc_2026100301/initial_CHECKPOINT.json` | `8a40de50910f9366bf129c6665857dc970db3ecf2b03a06b41d73dfe44ea7696` |

Git evidence中的RL_ADMITTANCE_301_INITIAL_CHECKPOINT.json和RL_VMC_301_INITIAL_CHECKPOINT.json为同字节副本；
完整权重、优化器、回放、命令及逐回合失败保留服务器各initial目录。只读核验用原生NumPy2.2.6及
main759ba7b的research72_checkpoint辅助函数，无新候选，无修改原始存档。

补充运行观察：10月4日约01:19UTC，第二模型越过warm-up后，两queue累计峰触及3GiB；
memory.events max分别169/148，OOM/oom_kill仍0，训练计数继续增加。
当时anon约1.83/1.87GB、file约1.25/1.26GB；符合限额下文件页缓存回收，不能再将后续累计max写成0。
这也不是未来不会OOM的保证；保持原限制/稳定作业并继续检查checkpoint保存，未据此增加资源。

## 历史：启动前静态压力检查

2026-10-03 22:53:57–22:55:16UTC在Spark完成，0物理积分、0候选权重、8次工程梯度更新后全部丢弃。
这是资源工程检查，不是RL实际训练、完整仿真并行检查或闭环表现。

实际参数确认队列的cgroup峰值为1,086,394,368字节（含物理进程与父队列），独立learner此前测得约2.22GB。
为避免直到长跑才发现组合OOM，本次在单3GiB/无swap/CPUQuota100%的cgroup内：
导入真实`research72_train_rl`依赖；实际触写1,086,394,368字节的uint8常驻数组作为物理队列压力；
分配并触写完整80k Replay；装载已有零物理工程7D checkpoint；执行4次动作＋UTD2周期。
JAX使用CUDA、预分配false、mem_fraction .02，与待启动RL环境一致；三个BLAS/OpenMP线程变量为1。

峰值**2,844,037,120字节（2.649GiB）**，距3GiB上限359.715MiB；memory.events的max/oom/oom_kill均0。
首周期71.831s，之后.491/.0194/.0163s；不把这一小样本当稳态吞吐排名。
工程7D检查点完整73文件集合/hash在运行前后精确不变，未保存新模型，未用这些更新计入RL真实交互。

不因预检通过就保证真实训练不会OOM：物理分配模式是模拟压力，仍未测三个GPU learner竞争、
实际IPC全55s轨迹、短失败重启或checkpoint保存峰值。当前无需修改训练/环境/资源限制；
首个真实5500步阶段仍须逐回合核验内存、实际步数、状态/优化器/回放恢复。

主机arm1@192.168.31.70，本轮共享根
`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：

- `rl_memory_probe_v1/execution.json`原进程记录，SHA256
  `26885a47d096fd3bcce484544bbb86ca7812b746524d540538d7dc7b83193297`，Git同字节证据`RL_MEMORY_PROBE_V1.json`。
- `rl_memory_probe_source_v1/research72_rl_memory_probe_20261003.py`实际源SHA
  `9be4dc23c1ae0e0fc8a880d08ea241eb249e570509abd9cc67aa77aef36b2593`，两端核验。
- 导入相邻`research72_20261003_1149_rl_runtime_v4/tools/research72_train_rl_20261003.py`，SHA
  `82bad7f324bef9220700a3f5ad300b5fa3c7e46c483b8812e0e4e12abdeca0c7`；该runtime不改。
- agent在`/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/frozen_train02/`，源SHA
  `cef423295711966e963ac5f23492350d1f3bda0c3177822fa221312ab65f8d89`。
- 实际解释器`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python`，NumPy2.2.6/JAX0.7.2；
  unit`sii-r72-rl-memory-probe-v1` invocation`0932f40a6080400a9e193dc89f295760`，退出0。
  完整命令、来源工程checkpoint逐文件hash和各周期内存保留在execution。

当前teacher/经典参数确认继续运行；真实RL仍等前序。封存条件未读，预算修订02未登记。
