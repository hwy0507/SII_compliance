# 官方RL实现的有限吞吐测量

2026-10-03 20:47:22–20:49:03UTC，Spark `cuda:0`，单CPU线程/3GiB。
为核算轮转续训的剩余预算，加载已有工程探针checkpoint，对5D/7D分别进行41次
“动作计算＋两次更新”：1次冷启动、8次预热、32次计时。共164次**工程更新**，
更新后的权重全部丢弃，0新物理、0新候选，不能给真实office baseline计入这些训练步。

| 策略动作维度 | 构建 s | 载入 s | 首次动作＋两更新 s | 稳态动作 ms | 稳态两更新 ms | 整周期P95 ms |
|---|---:|---:|---:|---:|---:|---:|
| 5（调阻抗接口） | 5.159 | 0.319 | 71.160 | 0.773 | 17.449 | 20.744 |
| 7（其余接口） | 4.884 | 0.353 | 16.000 | 0.839 | 18.568 | 21.719 |

每次计时均等待JAX参数树计算结束，不能把异步派发时间冒充完成时间。
峰值cgroup内存2,220,003,328B，约2.07GiB；NumPy2.2.6、JAX0.7.2。
两维度在同一个进程中顺序测量，缓存可复用，不能把7D较小冷启动解释成算法更快。
同一官方actor128/critic512、batch256、UTD2，优化器仍为80000总步计划。

这不是三训练进程竞争GPU时的吞吐，也不包含物理子进程、额外IPC、checkpoint写盘和独立审计。
尤其3GiB限制下的完整“learner＋物理”峰值仍待正式初段验证，不能只凭该探针宣称组合训练已通过。
稳态额外开销约18–19ms/策略步可作孤立参考；80000步训练中约75000步进入更新，
相当于每模型约23–24分钟的孤立学习计算，不能替代实测端到端完成时间。

已有完整55s开发回合约需5–6分钟；最终38×24=912回合仍需保留最后一天。
当前teacher两条件筛选中排前的teacher_09/teacher_07都与原teacher不同，应为40条实际再采集
留预算，但仍须正式八条件确认才能选teacher。可选ESN交互读出再拟合尚未登记；若新teacher数据改变，
六学习族共同再拟合并需144开发回合，不能因为GPU空闲就贸然追加或挤掉baseline。

## 证据

原工程checkpoint5D/7D分别74/73个文件，完成后用独立递归hash工具核对完整文件集合及字节精确不变。
探针只读它们的512条工程回放数据；不读取封存条件，也不根据任何任务结果调时长。
源脚本语法检查和实际有限运行通过；实际164次更新数有执行断言及逐周期原始耗时。

主机`arm1@192.168.31.70`：

- 实际收据：`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_throughput_probe_v1/execution.json`，
  SHA256 `687fdaf8d61f842bdd3c7572891e2064ab11e364d1895cc8cc3b9a38153a9861`。
  Git evidence保留同字节小型副本，含命令、环境、逐周期耗时及原checkpoint所有hash。
- 实际脚本：`/home/arm1/sii_shared/SII_compliance/incoming/research72_rl_throughput_20261003_v1.py`，
  SHA256 `0ed30caf396db249c1b304767344a84ae546979a9bfe39f576bade140a9293c9`，base main788d681加该新脚本。
- 官方adapter：`/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/frozen_train02/official_parameter_agent.py`，
  具体源hash和上游固定commit见实际收据。

20:56UTC初始开发198/264，第六身份仍32/33，不按不齐的seed汇总其胜负。
四仿真继续；RL v2、teacher确认和后续ESN/增强baseline仍等待前序。真正24条件封存。
