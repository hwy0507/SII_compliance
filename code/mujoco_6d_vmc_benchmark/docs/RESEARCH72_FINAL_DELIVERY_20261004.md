# 最终评测到独立回放、统计与媒体的连续衔接

2026-10-04 09:04:53 UTC 实际核验：一次性服务 `sii-r72-final-delivery-v1` active，
PID 2550310，状态 `waiting_for_final`，steps 为空；MemoryMax 3 GiB、Swap0、CPUQuota100%、单线程。
现有训练、开发队列和最终衔接服务不变，没有新的仿真、学习、选模或定时任务。

## 为什么增加这一步

已有 `final_transition_v1` 只保证正式物理批次和独立阶段审计，未接上独立 RL actor 回放、
最终统计或视频。新增程序等待其终止及最终批次终止，调用原冻结 a3b8c97 runtime 的现有工具。
不读取封存环境内容，不改变选择规则、原环境、gate、模型或执行器限制。

1. 原报告加载器核验模型锁、开封收据、队列和独立子步审计，从已审计回合建立全部15个RL模型的回放清单。
2. 按模型顺序重新加载冻结checkpoint、回放所有已审计回合，包括任务失败和物理短回合。
3. 原比较报告生成器输出38模型×24条件的统一矩阵和既有配对统计，缺失保留计划分母和缺失界限。
4. 原绘图工具生成SVG/PNG，原媒体工具按字典序第一个共同条件生成所有模型/seed的三角度视频；不挑成功。

无回合的RL模型保留为缺失。单模型回放失败不阻止其他模型，已产生的终止失败收据仍交给报告核验；
缺回放不删除物理结果。报告核验失败则停止后续绘图/视频。图形生成失败仍可生成视频，失败不自动重试。
前置PID消失、父进程结束但物理批次未确认终止、源码/协议变化，都保留失败并停止，不自行续训或补测。
程序不延长原物理派发期限。后处理没有新的物理积分，使用实际训练解释器以保持RL逐值推理兼容；
顺序执行共享同一个3GiB进程组限制，媒体是保存状态重放，未重启任何稳定计算。

`complete` 仅表示该后处理链完成；`complete_with_gaps` 明确包含缺失/失败。
两者都不自动代表ESN胜出、硬件安全、论文解释已完成或RAL投稿就绪。仍需研究者检查图像、视频、
统计子集、预算差异及论文表述。912真实最终回合及独立RL回放目前都尚未产生。

## 验证与共享

本机 `.venv-canonical-rl` 与Spark实际 `reward_study_20260930/venv_gpu` 解释器分别通过9项合成编排测试：
活跃前置等待、死亡前置拒绝、终止批次守卫、短失败/缺模型保留、37模型及重复记录拒绝、
固定调用顺序、回放/绘图失败保留其他输出、坏报告阻止媒体、完整覆盖状态。
测试mock加载器/实际计算，只证明编排规则，不是新实际RL回放或正式成功证据。
实际服务器NumPy2.2.6、MuJoCo3.11.0、Matplotlib3.11.2、Pillow10.2.0可导入，
imageio内置ffmpeg7.0.2可执行；磁盘剩余2.7TiB。尚未重复渲染物理样本。

服务器 `arm1@192.168.31.70`：

- 根：`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
- 新监督源码：根下 `final_delivery_source_v1/tools/`，两文件内容/大小/权限/完整集合已核验；
  tar SHA256 `ff113e8896f4b1f6dd0fdb4df8c34cc6fd2fd55078bb735f8c1203f029a25174`。
- 原冻结子工具：`/home/arm1/sii_shared/SII_compliance/source/a3b8c97fa027f4bf9bb55149e45cac4f664be562/code/mujoco_6d_vmc_benchmark/`。
- 实际登记：根下 `final_delivery_v1/SPECIFICATION.json`，SHA256
  `348925fe49141896477d3f7433e032949991c71f0f343716137f5d03075d2134`，Git副本同字节。
- 实时进程状态：根下 `final_delivery_v1/execution.json`。
- **待生成**：该目录的 `REPLAY_PLAN.json`、逐RL回放收据、`comparison/`、`figures/`、`media/`。

开工实际查询/fetch main de89c451ca33f56aee9e66ca06dac398417b5f04、
baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，未合并baseline或修改其产物。
de89c45完整3299文件源码此前已核验共享，新监督单独登记，未冒充包含在原a3 runtime内。
