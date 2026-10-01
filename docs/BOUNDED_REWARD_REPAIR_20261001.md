# 有界指标奖励修复协议（2026-10-01）

这是根据已观察失败进行的开发修复，不是盲测或主实验替换。

## 已实现修改

在原有RewardConfig增加显式error_transform选项，默认quadratic保留旧算法。
bounded模式在每个物理子步按 e²/(0.12²+e²) 积分，除以55s，再乘原error_weight=4。
该训练跟踪成本在完整55s内不超过4；原未经变换的误差积分仍完整记录。
正常误差成本和提前失败的剩余成本上界使用同一个变换，后者的误差部分从
4*(3/.12)^2=2500的全时域支持界降到4。
力矩峰值增量权重8、时间权重1、动作变化权重.0002及任务±20均不改。

在55s/40ms配置下，未折扣的全部负成本上界为
4+8+1+.0002*4*7*1375=20.7（不含任务失败-20与势函数项）。
不是把已经发生的物理失败删掉，也不是只裁掉终末大数而留下可逃避成本。
跟踪目标的训练效用已变化，因此不再声称训练积分与最终RMSE严格单调等价。
正式三指标仍从原始子步不裁剪重算；峰速仍是报告项，不冒称显式速度目标。

## 验证

test_rewards与test_bounded_rewards共21项通过：共享任务项与可加性、原始误差保留、
有界误差单调性、所有提前失败位置的合法随机未来成本、55s极端失败数值上界、
missing/NaN越界拒绝、terminal和timeout。训练源码/测试/监督器/报告语法与diff检查通过。
启动真实训练前，test_hooks_invariance.py将以6.4s/dt5e-5真实MuJoCo对照验证
qpos/qvel/ctrl/物块/阶段/模型/三指标逐项完全一致；失败则禁止继续训练。
该物理验证未运行前不写成通过。

## 独立训练与公平对照

- 目录 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/reward_scale_repair_03。
- 新冻结源 frozen_reward_repair_03 从frozen_main_01复制，仅覆盖rewards.py、office_env.py、
  train.py及新测试，记录提交及overlay hash；物理环境、gate、actor48/action7、WBC/filter不变。
- 2个新metric种子61001/61002，从零训练目标30k，学习率总计划保持100k，UTD2，
  gamma=.9995、entropy=-2、initial_temperature=.01、warmup_std=.02。
- 原任务组与原指标组复用entropy_diagnostic_02相同seed/共同周期step checkpoint。
  这两组也使用entropy=-2，因此新旧metric之间只变有界误差与相应失败补偿。
- 两新策略+四控制策略，共六策略×六冻结开发条件=36条55s/dt5e-5评测。
  两seed均值/SD；缺样本/提前结束单列。按共同完成step≤30k，不按测试选模型。
- 新reward不续用旧replay或normalizer。episode阶段不是物块夹持成功；实际行为验收仍需
  轨迹/视频中的夹起、搬运、释放，以及接触后的响应。

## 预算及现有任务

已对核验过命令的四个低熵训练worker发送SIGUSR1：均保存final checkpoint并rc0退出，
实际48462/49059/49042/49992步；它们已有共同40k周期checkpoint，原supervisor继续48条评测。
这是用户要求优先reward修复后的预算调整，不伪称完成原60k目标；旧证据保留。

新监督器等待旧48条评测完成再启动，不超过四个仿真并发。新训练13:12UTC安全截止，
给13:41UTC总交付留评测时间；若共同预算降低，报告实际共同step。缺少共同checkpoint
或源/物理验证失败则保存证据并停止，不能生成伪成功结论。
report_reward_repair.py显式核对36矩阵、同seed/step/entropy/LR/reward版本、
dt/MJB/模型权重/normalizer及raw三指标，不能使用主54或熵诊断48门槛。

代码修复和数值测试已完成；启动、真实物理不扰动验证、训练效果和正式评测状态必须读取
STATE.json、INVARIANCE_STATUS.json、TRAINING_STATUS.json、EVALUATION_STATUS.json及report。
当前协议不声明已经学会抓取或取得更优指标。
