# 三分离特化108格最终测试执行入口

> 版本说明（2026-10-31）：本文的“27条开发回合全部通过才可登记”属于原 v1 模型选择流程。对已冻结的 v7 ESN/RNN 与 validation 选出的 MLP384 九模型组合，用户要求进行一次正式未见组比较；专用入口为 `experiments/evaluate_contact_yield_unseen108_locked_v2_20261031.py`，当前登记见 `outputs/contact_yield_locked_unseen108_20261031_v3/REGISTRATION.json`。v2 只允许将既有开发失败带入正式对比，不做回退选模或测试调参；下文冻结条件、Task/Strict/机器 gate、失败分母、SPT及独立复核规定继续有效。v1旧登记与其历史结果不覆盖。

本入口补齐从开发资格选择到最终测试的执行路径，尚未登记或派发正式测试。冻结条件JSON仍为SHA256 `c99f0f962ab44821693f9928c9f68dc4a3ff907617bcc9e55cce3ccdbfbcc24d`。不得用当前开发改善宣称正式结果。

## 前置要求与执行

源码：`code/mujoco_6d_vmc_benchmark/tools/run_v9_unseen_matrix_20261030.py`。

`register`必须在原top3及完整12候选两个服务都inactive、完整12候选九组全部选择成功、完整独立review绑定execution/registration/source之后执行。任何null仍需开发修复，不替换成次优失败模型。模型来自该独立选择的准确九项，同一teacher配置、原条件及其冻结源码全部校验。登记绑定当前全部scripts/tools源码hash、原数据/训练/候选审查祖先、九checkpoint/metadata、解释器、资源和108格的预期时长。登记不执行物理。

从benchmark目录、冻结解释器及`PYTHONPATH=scripts:tools`运行：

```bash
python tools/run_v9_unseen_matrix_20261030.py register --root outputs/nonrl_v9_isolated_unseen_108_20261030_v1
python tools/run_v9_unseen_matrix_20261030.py run --root outputs/nonrl_v9_isolated_unseen_108_20261030_v1
python tools/run_v9_unseen_matrix_20261030.py review --root outputs/nonrl_v9_isolated_unseen_108_20261030_v1 --output outputs/nonrl_v9_isolated_unseen_108_20261030_v1/FINAL_REVIEW.json
```

上例`python`必须替换为登记的绝对解释器。`run`须置于user systemd：`MemoryMax=3G`、`MemorySwapMax=0`、数值线程三变量均1、显式`taskset -c 6`；资源guard会核实际cgroup和affinity。本机唯一仿真，不使用服务器计算。未满足前提不运行命令；本轮实际只验证了在途拒绝。

独立协调锁与wrapper物理锁分开，启动前尝试物理锁并立即释放，由唯一worker重新独占；竞态由worker拒绝。每格调用原wrapper，再执行原actor/filter、棍推行为、qualification和v2全时长审查。科学失败保留并继续下一格；基础设施异常停止，execution=failed_preserved并保留current/已完成行与raw。无自动重试、覆盖、缺格补零或测试选模。若需恢复，另行审查并登记不相交补跑，不能再次运行同root。

12条件各九模型，逐条件核MJB hash、第一帧canonical48逐值和filter配置相同。每格核seed/全部场景参数、teacher/checkpoint、worker保存的源码hash。预期预算来自登记：rod20s、ball30s、corner13s，不从实际结束时间反推。

## 最终审查与指标

`review`必须完整108格且严格按登记顺序一一对应。重新核来源/配对、逐格子步及终态任务，独立从checkpoint回放actor和公共filter，而非只相信先前passed标记；重新计算的完整指标行必须与运行收据完全一致，所有相关hash及execution前后保持。缺格、重复或在途状态拒绝输出最终报告。

输出完整九seed模型汇总、三family和family×scene汇总。所有组共用全部108格双成功最短完成时刻T_ref，组内不能重设参考。Task/Strict各自成功率、双成功条件SPT、全回合平均峰矩、机器合规率均保留失败分母；人体舒适NA，棍球扰动接触代理单列。保留逐关节峰矩/峰速/外穿透。0双成功SPT为NA。原13样本0.48s采样保持语义不改，不宣称物理子步终态连续证明。

最终报告仍须完整raw共享、hash核验、研究解释和媒体核对，不能仅以运行器exit0当Goal完成。原组合office108为独立迁移压力，51完成/57待补不覆盖。

## 本轮实际验证

`check_v9_unseen_controls_20261030.py`以合成case和mock worker检查108格一次派发、拒绝隐式重启、第四格基础设施异常停止且保留前三格、模型初始配对不符失败、缺模型/重复seed/重复方法名/缺条件/重复条件拒绝、107/109/在途矩阵拒绝、family共享全局T_ref。真实两个选择服务仍active时`register`拒绝且零目录/零登记/零物理。控制测试明确mock锁和worker，不获取或中断活跃物理锁。

新独立replay路径实际检查原18开发中的ESN rod00、RNN ball00、MLP corner00，分别500/750/325帧，actor/filter误差全0。包括科学失败轨迹，不挑成功回合。证据`UNSEEN_REPLAY_THREE_20261030.json`；不积分、不拟合、不读取新条件结果。

最新独立prefix另存`UNSEEN_PREPARATION_PREFIX_20261030.json`；RNN seed01第二排名候选也已九条开发全部qualified，仍不足以启动最终矩阵。ESN seed01及其余组仍待，完整12共同接续保留。Goal active。
