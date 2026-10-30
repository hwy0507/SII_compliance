# 半标准差评测继续；训练熵目标持久化基础已核验

2026-10-30，Goal active。上一轮完成87/冻结86原16审查并启动唯一半标准差配对，属于实质进展。本轮实际查询、fetch/read main `7bff39ecbb3eda9b3ddb0b991f8893b4cb97aafb` 和 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新增远端变化；按仓库sii-research-sync发布，无子agent。完整87未收敛，完整结论与边界仍见 [上一交接](RL_COMPLETE87_HALF_STD86_RUNNING_20261030.md)。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。新源码/证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/half_std86_completion_entropy_preparation_20261030_v1`，科学评测 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter86_half_std_paired_20261030_v3`，冻结runtime未修改。

## 在途原16与全量独立审计

原PLAN0d857019、四固定86组合×同四动作seed、pre-tanh std×0.5、最多16×55s/22000动作/1760万子步/0更新不变。没有重启或新增科学回合。四evaluator PID1280069/72/75/76的start身份和reviewer1280079均已重新核验，允许已完成有FINISHED的任务自然退出，不依据旧PROGRESS重启。

保存进度(完整回合数,seed,在途动作) `{'impedance_short0600': (3, 2026102636, 1300), 'admittance_short0900': (2, 2026102635, 1300), 'admittance_long0200': (2, 2026102635, 1200), 'vmc_short0000': (3, 2026102636, 700)}`。只记录运行进度，不从部分seed选方案；最终全16/最终state不变/paired图和独立raw审计仍待。

新唯一等待审计器PID1888816/start574492188，继承原LAUNCH+原wall deadline，不延长科学预算、不启动physics。每30秒检查原四evaluator和reviewer的实际/proc身份或明确完成收据、失败文件与GPU新鲜样本；原完整review完成才调用 `audit_half_std_raw.py`。该审计在前轮原16独立入口上明确允许并保留有安全原因的短回合，检查全部实际子步/动作、dt5e-5、有限值、峰矩、外穿透、接触分母与reward重建；不强制所有候选必须跑满才被统计，不删除失败，不新增forward/physics/update。入口与原版本diff保留。

恢复时先读原root FINISHED/REVIEW/PAIRED_REVIEW/PAIRED_SAVED_REVIEW，以及新目录WAIT_FINISHED/HALF_STD_RAW_REVIEW/HALF_STD_RAW_SAVED_REVIEW；仍在运行就核验PID/start继续等待。完整后实际查看两张结果图并保留PLOT_INSPECTION，然后审全16增益和退化。半标准差是推理采样干预，不证明训练熵目标等价或一定有效，不自动88/Direct34。

## 解决训练熵目标在恢复时丢失的基础接口

原PublishedLearner不持久化SAC target_entropy。新增独立 `persisted_entropy_target.py`，marker版本1绑定明确target、5/7动作维和准确父learner digest。只允许显式启用迁移且digest完全匹配的旧父进入；后续恢复必须marker准确，拒绝缺失/错误版本/目标/维度/父摘要。state保存和update都检查当前目标未漂移，不能从未恢复的fresh learner开始训练；不覆盖actor forward。

此处只准备恢复基础，未选定新的科学目标、未创建88训练checkpoint。真实完整87全部三方法测试保持原目标I−5/A,V−7；除新marker外，完整权重/actor、q与alpha优化器、RNG、更新计数和所有旧目标marker逐digest精确一致，内存序列化/反序列化再恢复精确，原checkpoint前后SHA不变。只读过原replay digest，未重建Replay对象，不冒称本次重新验证全replay恢复。三份原87checkpoint和准确父digest见ENTROPY_ACTUAL87_REVIEW。

随机初始化的真实native CHEQ接口测试覆盖5维minimum和7维mean：保持原目标时一次真实native update与原实现的完整后状态/全部metrics精确一致；测试用替代目标分别−6/−8时，alpha梯度差约1.0、原native target metric与新增applied metric准确，完整序列化恢复精确。17项拒绝测试通过。**这些−6/−8仅是软件测试值，不是科学选定超参数。** 成功测试6次native update调用；先前三次失败尝试各2次，共另6次，总12次随机fixture调用，每调用内部含原optimizer步骤，不把调用数冒充每个优化器step数。实际checkpoint更新0、physics0。

初版逐字比对失败保留：所有数值/权重/优化器/RNG完全相同，只有step_metrics中原target为整数−5、适配器为浮点−5.0；已改成原目标时保留原整数类型。原失败源码、记录与诊断保留；不是原科学模型损坏。当前adapter SHA `843bb623f2a743d402262b021ffc63f1d2875d6633de7a848a431cf666f086e3`。

这尚不足以直接部署训练。若全16证据支持另登记训练熵修订，必须明确有限预算和目标，统一trainer/resume/frozen-eval/health的loader与diagnostics、拒绝旧loader静默忽略marker，并验证完整实际启动。新的训练父必须完整87，不能从诊断86回退。当前仍无88决定/启动和Direct34。

## GPU与恢复材料

原v7守护保持，科学结束仍合成保载。此次122采样，最低 `[74, 76, 73, 76]`%、低于50次数 `[0, 0, 0, 0]`，末值 `[89, 78, 81, 80]`%。合成占用不等同科研吞吐，历史warmup0/v6低谷保留，不保证采样间每个瞬时；不是重启自启服务。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HALF_STD86_ENTROPY_STATE_READY_20261030/SMALL_EVIDENCE.tar.gz`，99成员/57034字节，SHA256 `98789c127b65fd10577c59b21637213f2791e8b8e8e00793026b4794b108e190`；tar逐成员字节/源码AST已核，Git index/commit另核。依赖前包521成员/SHAabd952ef的完整87与原16/半std源码证据；大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份。HDD LATEST原位254字节指向本文。成功正常push并观察实际远端后才在包外写PUBLICATION。

Direct33数值阶段接受但冻结全30 Task/Strict0/0，旧28缺最终内存证明；指定ESN不可用，不替换/重复追问。原partial75、不可判74—76、79安全中止和历史所有窗口失败保持。Goal active，完成要求仍是四方法收敛、冻结测试与指定比较，不能以本次软件预检通过替代。
