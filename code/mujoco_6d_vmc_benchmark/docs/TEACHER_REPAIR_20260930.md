# Teacher 修正与先验验证（2026-09-30）

用户要求先修正 teacher、确认特化场景，再做纯 ESN。当前尚未证明修正成功；不启动新的 ESN 蒸馏。

## 原因证据与纠正

旧综合 v1 teacher-v8 的 1375 步动作由保存的 canonical48D 中 `observation[39:45]`
精确重放，最大误差 0。原 teacher 已使用 20 个虚拟动力学积分子步，不能把振荡简单归因于
40 ms 显式积分。原负载观察器也是每个物理子步更新，只有 teacher 请求保持在 25 Hz。
此前对“延迟导致极限环”的解释属于尚待闭环对照确认的机制假设。

最后 5 s 的原动作一阶差分 RMS 为 0.223577（只统计六个残差通道）。虚拟速度的波动
明显高于虚拟位移；在常量 wrench 测试下原方程自身能收敛，不能声称积分器会自行发散。
固定历史上的三种 teacher 修正把差分 RMS 分别降到 0.058852、0.117670、0.126734；
这只是离线证据，不能替代物理闭环。

还发现 `vmc_corner_nominal_success_20260928`、`vmc_corner_nominal_final_teacher_20260928`
的 JSON 实际均为 task/strict=false、load_transfer，不能根据文件名认定早期 teacher 已成功。
旧 v1 同名 flag 曾发生几何变化，不能直接拿当前生成场景重现历史 v1。

## 固定预算及隔离

有效的归档版本计划与源码快照：`outputs/teacher_repair_canonical_20260930/plan.json`、`source/`。
首轮四配置：原版、虚拟速度输出权重 0.25、两点因果 wrench 平均、阻尼乘 2。
不修改公共 teacher 文件；新类在独立包装器内注入，不影响 baseline 或旧模型。
三候选分别检验高频速度读出、相邻周期交替及虚拟动态阻尼，常量负载的静态柔顺性不变。

先运行现有 corner-placement/settle 特化回归，每条完整 55 s、dt=1e-4。
只有该回归 task 与 strict 都通过的修正候选才进入 combined-thick-corner-pillar-v4；
原版额外运行综合对照。最多 8 条回合，失败全部保留，无搜索追加或 held-out 解封。
这里的 corner 回归是现有办公室厚桌角放置开发场景，不等同于早期独立 table_corner 协议
全部条件通过；后者和跨条件验证仍是后续必需工作。

综合模型必须匹配归档 MJB SHA256
`5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`。
各修正与原版的 MJB 必须逐字节一致；不改变环境、任务 gate、actor 字段或执行器限制。
actor 仅接收估计 wrench 与固定 dt，额外状态仅为自身的上一拍 wrench。

每条保存 execution/完整命令、源码快照与 hash、seed/参数、MJB/XML、rollout、teacher
内部状态、原公式输出/修正请求/公共过滤后动作，以及物理子步实际力矩、速度和误差。
独立重放请求并重算三项指标。RMSE 是 waypoint 误差，不是连续参考轨迹跟踪误差。
平滑、完成任务、安全、有效接触必须分开报告，不能以动作平滑替代成功。

运行服务：`teacher-repair-canonical-20260930.service`；本机一个仿真、单线程、MemoryMax=3G、
MemorySwapMax=0，子进程另有 3 GiB 地址空间上限。Spark 已有多项 baseline 工作，未新增
远端作业，也未停止其他任务。当前 service 状态与 execution.json 是恢复依据，禁止重复启动。

## 状态

首批 `outputs/teacher_repair_20260930/` 误用了旧自动化指定的 `.venv-rl`（MuJoCo
3.14.0）。4 条 corner 结果保留为版本诊断，不能与冻结物理结果混用：原版 task/strict
通过但放置阶段动作差分 RMS=0.25124；velocity025/pair-average 均在松爪瞬间
`release_supported=false`，damping2 停在 load_transfer。不能把到达 retreat 当成功。
综合原版在第一个物理步之前被 MJB hash 检查拦截，未继续生成不配对结果。

已查明归档 execution.json 指定 `.venv-canonical-rl`，MuJoCo=3.11.0。新队列新增
版本强校验、启动前综合模型预编译校验，已匹配完整归档 MJB hash；重新运行相同候选
预算。旧失败目录没有删除、覆盖或归入成功示范。解释器版本是物理实验合约的一部分，
恢复时必须读每个实验自己的 execution.json，不能沿用历史自动化的默认解释器。

已完成：固定历史精确重放、常量输入收敛、零输入平衡、reset 可重现性检查；
正确归档版本首轮八条完整回合及独立动作/内部状态/filter/子步审计。
运行中：无；两轮共 12 条归档版本回合均已完成，源和原始结果全部保留。
未完成：特化场景跨条件验证、综合 strict、正式 dt=5e-5、稳定数据上的纯 ESN。

### 归档 MuJoCo 3.11 的首批有效结果

| corner-placement，55 s，dt=1e-4 | 原版 | velocity025 |
|---|---:|---:|
| task / strict | false / false | true / true |
| 松爪前支撑 | 未松爪 | true |
| 最终阶段 | load_transfer | retreat |
| waypoint RMSE (mm) | 47.4093 | 35.7211 |
| 峰值实际力矩 (Nm) | 46.6698 | 49.3032 |
| 峰值末端速度 (m/s) | 0.0616024 | 0.0616024 |
| 最大外部穿透 (mm) | 0.00471858 | 0.00143052 |

velocity025 在 28.16 s 松爪、28.96 s 进入撤退，最终末端误差 3.15 mm。
放置阶段动作差分 RMS 0.049672，撤退阶段 0.006189；不能只用最后 5 s 的近零
动作证明全过程没有抖动。独立工具 `tools/audit_teacher_repair_20260930.py`
对完整 teacher 状态、原始请求和公共 filter 状态逐步重放，所有字段最大误差为 0，
并重算了 550,000 个物理子步的三项指标。最终判定来自真实 JSON，绝不按阶段名字推断。

该变化保留原虚拟动态，只把输出 `v + 1.6*x` 改为 `0.25*v + 1.6*x`。
常量负载的静态顺应性不变，快速虚拟速度扰动的输出权重降低。它没有增加感知、场景
状态或阶段判定，仍然只是 teacher 训练来源的候选修正，不是部署中的 VMC/ESN 混合。
当前仅证明一个开发回合，不足以声称厚桌角全条件已解决。

### 首轮完整结果（八条回合均已完成并独立审计）

| 场景 | teacher | task / strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 外部穿透 mm |
|---|---|---|---:|---:|---:|---:|
| corner | original | 0 / 0 | 47.409 | 46.670 | 0.06160 | 0.00472 |
| corner | velocity025 | 1 / 1 | 35.721 | 49.303 | 0.06160 | 0.00143 |
| corner | pair_average | 1 / 1 | 33.747 | 52.092 | 0.07430 | 0.00143 |
| corner | damping2 | 1 / 1 | 35.101 | 51.279 | 0.06636 | 0.03273 |
| combined-v4 | original | 1 / 0 | 43.438 | 50.324 | 0.10081 | 0.15251 |
| combined-v4 | velocity025 | 0 / 0 | 58.923 | 49.511 | 0.10399 | 0.17897 |
| combined-v4 | pair_average | 1 / 0 | 35.059 | 54.122 | 0.08598 | 0.18793 |
| combined-v4 | damping2 | 0 / 0 | 39.440 | 50.938 | 0.08225 | 0.16522 |

四条综合回合均满足穿透安全，但不满足全部接触曝光。原版和 pair_average 完成了任务，
却没有所需柱接触；velocity025 在 54.84 s 才进入 release，55 s 固定时限内未完成撤退；
damping2 停在 load_transfer。全部原始失败保留。不能延长时限、放宽曝光或解封 formal。

pair_average 的综合放置阶段动作差分 RMS 从原版 0.30619 降至 0.12127（约降低 60%），
但不是完全无振荡，且峰矩从 50.32 增至 54.12 Nm。不能用单项改善宣称全面占优。
综合 MJB 与旧 v4 逐字节相同，11 个共有运行源码 SHA 也与旧 v4 相同；模型、公共 WBC、
gate 或观察器没有修改。

### 第二轮（预先固定，最多四条新回合）

入口 `tools/teacher_repair_followup_20260930.py`，服务
`teacher-repair-followup-20260930.service`，产物 `outputs/teacher_repair_followup_20260930/`。
首轮 complete 后才启动；复用 SHA 固定的首轮 runner 和原版模型作为只读参照。

- velocity025_stiff2：速度权重 0.25，K×2、B×sqrt(2)，保持虚拟阻尼比，检验降低持续
  负载下静态偏移能否减少放置对齐耗时。
- pair_average_pitch035：在两点因果平均基础上只把固定虚拟主轴绕 y 旋转 0.35 rad，
  用正定各向异性弹簧把受力转换为切向让位。固定旋转是 teacher 参数，不从场景读取表面
  法向、障碍几何、接触、阶段或事件，也不修改世界模型。

仍先 corner task/strict，通过者才进入同一 combined-v4；不运行保留条件，不开始 ESN。
这两项为首轮机制结论后的独立登记，并非修改首轮候选或隐藏失败。

### 第二轮完整结果

| 场景 | teacher | task / strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 外部穿透 mm |
|---|---|---|---:|---:|---:|---:|
| corner | velocity025_stiff2 | 1 / 1 | 34.600 | 48.358 | 0.06160 | 0.00143 |
| corner | pair_average_pitch035 | 1 / 1 | 33.807 | 54.032 | 0.08570 | 0.04644 |
| combined-v4 | velocity025_stiff2 | 1 / 0 | 37.406 | 48.127 | 0.07057 | 0.14492 |
| combined-v4 | pair_average_pitch035 | 1 / 0 | 35.438 | 51.892 | 0.08029 | 0.13091 |

四条均独立重放 teacher 全状态、原公式输出、修正请求和公共动作过滤链，最大误差 0；
每条 550,000 个子步的三项物理指标复算通过。两条综合回合均完成了真实支撑下松爪和
撤退，但均无所需柱接触，因此 strict=false，不是整个综合任务通过。

当前优先保留 `velocity025_stiff2` 作为进一步 teacher 回归候选。相对同版本、同模型的
综合原版，waypoint RMSE 43.438→37.406 mm，峰矩 50.324→48.127 Nm，峰速
0.100806→0.070574 m/s，穿透 0.152511→0.144922 mm；放置阶段动作差分 RMS
0.306187→0.042031（下降约 86.3%），撤退阶段为 0.001041。该候选在综合回合
35.56 s 松爪、36.08 s 进入撤退。额外增大刚度确实缓解了首轮 velocity025 的超时，
但没有创造缺失的柱接触数据，不能声称已解决所有接触交互或泛化。

下一步必须先补齐 teacher 的特化条件覆盖和固定场景中柱接触缺失的因果诊断。当前只验证了
corner-placement 开发回合与综合 v4；未完成早期独立 table_corner 全协议回归或多条件
稳健性。不得因为这 12 条完成便自动启动 ESN 蒸馏、正式综合 dt=5e-5 或保留场景。
本轮没有训练或替换 ESN、MLP、RL，未改环境、gate、公共控制器或提交代码。
