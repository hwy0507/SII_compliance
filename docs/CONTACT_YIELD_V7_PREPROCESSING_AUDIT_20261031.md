# v7公平重训与MLP推理契约核验

## 结果

本轮获批的75候选训练方案已经由v7完整执行，故没有对同一数据、随机种子、搜索网格和32,000更新预算再启动第二份重复训练。核验对象为：

- 数据40条/21,500帧，SHA256 `d771433db06103edb3e33264b8040d059c4df6fb19faa66043f458c61457f42a`。
- 数据登记包含30条纯teacher轨迹及10条通过资格审查的恢复轨迹；其中含两条seed01真实teacher后缀。v6 seed03接管失败数据不在训练集合中。
- 三个seed、每个方法/seed 12候选、ESN/RNN/MLP共75候选均完成；RNN/MLP各32,000更新。`FIT_AUDIT.json`为`passed`，模型锁含9个模型，九路动作重放的最大误差均为0。
- 固定27闭环结果为Task 27/27、Strict 25/27；ESN与RNN各9/9，MLP 7/9。重新拟合不会改变资格事实，失败轨迹继续保留。

## 契约审计

已检查checkpoint、神经训练脚本、拟合审计器、固定27诊断器和部署端：

1. MLP checkpoint的契约是`proprio48_office_mlp_rnn_v1`。运行时`current_student_policy_20260921.load_current()`按契约选择`OfficeMLPRNN`，不会送入旧的45维`CurrentMLP`。
2. MLP/RNN训练使用18个canonical48字段，字段顺序为`14–16, 20–22, 26–28, 39–47`；训练集标准差作scale并设下限0.005，输入除scale后裁剪到`[-12,12]`，再追加绝对值特征。`OfficeMLPRNN.act()`执行同一组变换。
3. v7神经候选的target为`requested`。部署actor先输出requested action，然后由公共`VelocityResidualActionFilter`生成滤波动作；固定27记录与独立replay核对这条链，均精确匹配。
4. FIT_AUDIT通过冻结`OfficeMLPRNN`从训练快照加载checkpoint并逐样本复放导出的动作；固定27及共同观测诊断又通过`load_current()`复放实际轨迹。没有发现checkpoint格式、输入变换、输出动作或公共filter错位。

因此，之前提出的“预处理或加载器不一致”疑点已被证据否定。FIT_AUDIT验证的是训练导出与运行契约一致，不代表策略闭环成功，也不证明所有根因已经找到。

## 仍待查问题

MLP三个seed在共同六条teacher validation上的requested-action MSE约为`1.64e-4–1.72e-4`，RNN约`3.28e-5–3.58e-5`，ESN约`3.40e-5–3.98e-5`。这与fixed27中两条棍推MLP Strict失败同时出现，但不能单凭误差证明因果。MLP是无显式状态的单帧映射；教师控制器使用接触进度记忆，RNN/ESN可能利用历史，而canonical48输入不含该隐藏记忆。该差异是需要以训练数据和同状态动作诊断检验的表征假设。

后续应继续使用固定27开发身份，优先检查棍推失败发生前的观测近邻是否对应明显分散的teacher requested-action标签，以及失败状态是否在训练支持域内；保持物理、gate、输入定义、公共filter、执行器限制和dt不变。只有修复后的模型通过完整Task与Strict开发审核，才另行申请开启封存的final108评测。

## 核验边界

本轮是只读代码、checkpoint metadata、数据登记和已有审计收据核验；没有启动重复拟合、物理仿真或final108评测。GitHub暂时不可达；本地main HEAD及缓存`origin/main`为`9df3bf3df9221a254b40ba5b04b00adee1b2cd45`，baseline缓存为`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，不能据此声称已检查实时远端。
