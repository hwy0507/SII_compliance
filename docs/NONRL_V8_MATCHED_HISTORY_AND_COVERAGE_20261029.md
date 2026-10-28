# 同一成功教师历史上的学习误差与真实场景覆盖修复准备

本轮有两项进展：九个冻结学生在同一成功教师历史上完成诊断；新的八回合真实球场景覆盖
入口已实现、登记并通过静态检查。**没有新物理采集或重新训练，原108继续，主矩阵尚未修复。**
承接[完整18及回归失败](NONRL_V8_COMPLETE18_REGRESSION_DIAGNOSIS_20261029.md)。

## 九模型同历史比较

使用已经保存的v8 teacher `vertical_damping_office000` 成功轨迹，共1375帧。
教师配置hash与v8采集配置完全一致；该原控制Task/Strict同时通过，几何、物理dt、
条件000扰动覆盖、protocol、constructor均与已完成学生回归逐字段一致。
原teacher所有source文件及轨迹/动作链/MJB/子步hash核验，教师动作精确重放。

九模型使用**实际冻结推理源码**和原锁定checkpoint，所有模型均从reset开始读取这同一观测历史。
完成的五个学生回合（seed1三家及ESN/RNN seed2）另核验实际actor全轨迹精确重放，
其首帧观测与教师首帧逐元素完全相同，首动作也精确对应本次离线预测。
每个模型全部1375×7误差用独立标量求和核验；全部预测NPZ回读逐数组一致。

| 方法 | 成功教师历史上的全段动作MSE（三seed） | 首4帧MSE（三seed） |
|---|---|---|
| ESN ridge | 0.250070 / 0.075675 / 0.184260 | 0 / 0 / 0 |
| RNN | 0.003927 / 0.002888 / 0.003585 | 0.005757 / 0.000991 / 0.001099 |
| MLP | 0.008488 / 0.006905 / 0.006757 | 0.015948 / 0.005649 / 0.003581 |

这里是归一化requested-action的同状态误差，**不是闭环排名**。反事实模型动作没有施加到
该教师物理轨迹。三seed ESN在教师抬升段MSE为0.129961/0.099125/0.108492，搬运段为
0.311811/0.080761/0.227324；因此不能将全部ESN误差解释为它先碰撞以后才偏离数据。
但该结果仍不单独区分容量、输入覆盖和读出外推，也不证明唯一失败原因。

## 零载荷但非零上下文的检查缺口

教师首4帧动作严格为零。RNN seed1首动作六残差通道为
`[.115177,.068143,.129449,.012726,-.056396,-.010639]`，MLP seed1为
`[-.108869,.014325,.171687,.012181,-.264459,-.003690]`。
对应实际首帧观测完全相同，说明这些偏差发生在轨迹分叉之前。

进一步做六个**合成网络探针**：模型reset，canonical48除路径方向为±X/±Y/±Z外均为零。
教师全部输出严格零；ESN三seed最大绝对输出均为0，RNN为0.130110/0.110023/0.084461，
MLP为0.273377/0.195345/0.235294。这些探针不是物理轨迹、示范或新增拟合标签。

原因在模型约束上的区别是明确的：ESN由估计载荷及载荷×运动上下文驱动，禁止直接上下文
读出；普通RNN/MLP输入含直接运动上下文。训练器已有的`act(zeros(48))==zeros(7)`
并不覆盖真实“无受力但参考方向非零”的状态。它能通过全零测试，同时产生上述残差。
这不是导出数值错误，也不等于普通RNN实现错误；是目前数据/验证不足以约束的行为。
本轮不向当前模型硬加gate、不改变普通RNN定义、不用测试结果重新选checkpoint。

[完整诊断](evidence/NONRL_INTENT_RECOVERY_20261029/V8_MATCHED_TEACHER_HISTORY_REVIEW.json)
SHA `5c0bbeb7d287ba4bde87acc2bc1b37250d4a2001dd57283e5458622fab8184dd`。
全数组`outputs/nonrl_v8_matched_teacher_history_20261029_v2/PREDICTIONS.npz`，
SHA `31b0b8b1542d88e5ffdfddee2c48b63b4369484fbc0daa4aa22c4e626aac5819`。
v1诊断输出保留。最初两次诊断因helper修改sys.path而加载当前ESN扩展文件，源码绑定在
任何输出前拒绝；改为按绝对文件路径加载冻结actor后通过。冻结模型和物理作业未受影响，
不将这两次诊断工具导入失败误报为现有训练/推理实现bug。

## 已实现的下一步：八回合物理覆盖探针

有限探针仍在用户指定的**真实自由球场景**，不回旧综合环境采标签：

- 四个接近方向：初始手相对原位置在±X/±Y偏移50mm，z偏移−60mm，原IK解算并检查碰撞。
  目标物体及原几何不移动；接近方向由真实目标—初始位置计算，不能伪造actor输入。
- 抓取后搬运85mm，方向与本次接近方向一致，再回原抬升目标；原任务阶段/gate不变。
- 每个方向配两种球撞角度±0.8rad，其余取原train ball00、同seed和v8教师配置。
  角度保留在原弹道公式正cos区间；原物理dt、公共filter及执行器限制不变。
- 全部八条是development controls，30秒/条；没有validation身份、测试标签或自动训练。
  仍须真实手接触、原末态稳定及0.2mm等资格检查，失败完整保留。

代码为独立`run_primitive_coverage_20261029.py`、`run_video_reference_coverage_20261029.py`，
原场景runner与原108冻结源码完全不变。原资格脚本硬编码旧wrapper名，因此另存
`qualify_ball_coverage_demo_20261029.py`，逐字逆替换证明**仅wrapper路径字符串不同**，
没有更改任何数值、任务或接触判据。早期准备v1保留并标记superseded，无物理。

唯一有效准备：`outputs/nonrl_ball_coverage_probe_20261029_v3`。
[登记](evidence/NONRL_INTENT_RECOVERY_20261029/V8_BALL_COVERAGE_V3_REGISTRATION.json)
SHA `2f008162e1ddf774ae578e8f6e4e5e6961f6a5d6aadb510a5742b4bab03457a1`。
[检查](evidence/NONRL_INTENT_RECOVERY_20261029/V8_BALL_COVERAGE_V3_PREPARATION_CHECK.json)实际通过：
零配置时原task所有状态/goals及layout逐元素一致；原update/sample/gripper函数对象不变；
八个方向/搬运向量、四种非法配置拒绝、全部源hash、原108绑定保持；实际`--run`在
原108未完成时拒绝，未创建execution或物理输出。静态通过不证明IK可达、碰撞合格或有效修复。

启动条件：先完成原108，按原审计入口将完整审计写到其根目录`FROZEN108_AUDIT.json`，
确认原用户服务inactive，再以原单模拟器/单线程/CPU100%/3GiB/swap0运行
`tools/prepare_ball_coverage_probe_20261029.py --root outputs/nonrl_ball_coverage_probe_20261029_v3 --run`。
入口检查完整108、审计hash、服务、cgroup、线程和所有登记源码；使用独占probe锁及原全局仿真锁。
它目前**未启动**。v2也仅准备，提交前移除wrapper末尾多余空行导致hash改变，因此保留v2、
重新登记v3并实际重跑相同检查，不改旧登记。八项结束需完整审查再决定正式采集方案；棍推/桌角仍是必需场景，
不得用八个球回合替代三场景公平训练及最终主矩阵，也不承诺其修复有效。

23:24UTC原1172675 active、603176960bytes/3GiB，7/108完成；RNN seed3在途。
已完成七条Task/Strict均false，其中ESN seed3在34.48秒提前终止；这些新回合尚待独立全审。
完整108持续，Goal active。开工main7c05fd8e/baselinef6e8f8c实际fetch/read；
本轮无RL、子agent、服务器计算或删除。新源码/数组共享状态随后由收据记录。
