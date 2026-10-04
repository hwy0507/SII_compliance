# RL learner组合内存预检

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
