# 纯 ESN 方法定位与当前证据缺口

2026-10-03。这是研究定位记录，不是新颖性确证、最终实验结论或新增拟合预算。
本轮目标仍是固定office-v6中的公平比较，不预设ESN必须获胜。

## 已核对的基础文献

| 文献 | 本次核对范围 | 对本项目表述的约束 |
|---|---|---|
| Jaeger, Lukoševičius, Popovici, Siewert (2007), [Optimization and applications of echo state networks with leaky-integrator neurons](https://doi.org/10.1016/j.neunet.2007.04.016) | Crossref原始元数据；未读全文 | leaky ESN本身不是新结构，不能将采用泄漏时间尺度称作首创 |
| Waegeman, Wyffels, Schrauwen (2012), [Feedback Control by Online Learning an Inverse Model](https://doi.org/10.1109/TNNLS.2012.2208655) | Crossref原始元数据；未读全文 | 反馈控制/逆模型学习已有相关研究；方法细节和机器人条件需要进一步全文核查，不能仅凭标题声称已复现 |
| Yildiz, Jaeger, Kiebel (2012), [Re-visiting the echo state property](https://doi.org/10.1016/j.neunet.2012.07.005) | Crossref原始元数据；未读全文 | echo-state性质应单独论证，不用谱半径或状态有界替代机器人闭环安全证明 |
| Gauthier, Bollt, Griffith, Barbosa (2021), [Next generation reservoir computing](https://doi.org/10.1038/s41467-021-25801-2) | 已读出版商HTML正文Introduction至Methods，未读补充材料 | 固定非线性特征加线性正则化读出已有明确先例；这类特征扩展本身不足以构成本文贡献 |

NG-RC正文式(2)–(6)明确区分对固定特征线性与对输入/状态非线性，并用延迟观测的多项式特征做
正则化回归。其主要实验是Lorenz与double-scroll动力系统预测/推断，不是本项目接触机器人任务。
不能将其预测结果搬来声称机器人闭环安全，也不将本项目tanh循环储备池说成与该NVAR实现逐式等价。
文献所示低维预测成本优势也不能替代本轮实测延迟；本轮旧102模型中ESN actor-only耗时高于普通MLP/RNN。

这里只是基础文献初查，不是覆盖最新机器人储备池/柔顺控制工作的系统综述。一次Crossref查询遇到429；
之后通过已核验DOI逐条取得元数据。Nature首次请求只返回303页面，跟随重定向后取得正文；没有将重定向页当论文。

## 23:10UTC后续机器人文献核对

| 文献 | 实际阅读范围 | 对本项目的约束 |
|---|---|---|
| Shen, Miyazaki, Kawashima, [Control Pneumatic Soft Bending Actuator With Feedforward Hysteresis Compensation by Pneumatic Physical Reservoir Computing](https://doi.org/10.1109/LRA.2024.3523229)，RAL卷期2025 | [arXiv:2409.06961v2](https://arxiv.org/html/2409.06961v2)，2024-12-27作者稿HTML正文、公式/表及参考文献；图未独立渲染，非逐页核对出版社终稿 | RC/ESN已用于机器人控制；固定记忆＋线性正则化读出本身不是本文新贡献 |
| Giannetto et al., [Reservoir Computing Encodes Physical Adaptations for Reinforcement Learning](https://doi.org/10.1109/ICRA55743.2025.11127876)，ICRA2025 | Crossref元数据＋Semantic Scholar完整摘要，未获得全文 | 摘要已有RC+FORCE特征预训练/RL身体配置适应；不能泛称首次用储备池实现机器人适应或泛化 |
| Thanee, Uttayopas, [Computationally Efficient Sensorless Force Estimation for Robotic Haptic Exploration Using Echo State Networks](https://doi.org/10.2139/ssrn.6832482)，2026预印本 | Crossref元数据和完整摘要；posted-content，DOI创建2026-05-26，未读全文/未确认期刊审稿状态 | 已有末端位置/速度驱动ESN估计接触力的工作；估计准确不等于完成闭环操作任务，也不把预印本当正式期刊实验定论 |

Shen作者稿III-A式(3)–(5)明确采用固定随机ESN/泄漏状态、历史参考输入和ridge读出；III-B式(7)–(12)
把物理储备池输出与输入历史送入T-S分组线性读出。其模型参数包含800节点ESN、100步washout，硬件信号200Hz。
这些设置不等于本轮128节点/25Hz策略，论文报告的相对速度不能移用到我们的部署成本。
正文同时解释物理储备池增加装置空间、可调性有限等代价，不能只摘录其速度优势。

IV节确有真实气动执行器跟踪及FPRC+PD实验；Fig.17的人工干扰施加在用于计算的物理储备池，
不是本项目机械臂受到球/手/杆碰撞后完成pick-and-place。不能把该抗扰实验当我们的硬件安全/柔顺行为背书。
结论仍将系统稳定性分析列为困难和未来工作；不把“物理系统遵守守恒”或“储备池状态有界”直接等同闭环无源证明。

因此本文若要形成方法贡献，需要在本轮已冻结任务中证明纯本体记忆机制对接触后的恢复与安全放置有实际贡献，
并与调好参数的经典/RL以及充分优化的MLP/RNN比较。初始ESN点版较积分版更好的开发计数只是候选结果；
当前不能声称特征交互或多时间尺度首次提出，更不能因目标RAL就预定ESN胜者。
这次不引入新baseline/预算或修改环境，现有完整开发、冻结与留出计划继续。

另外读取Baldini2022机器人RC综述的元数据/摘要，未读其全文。两次OpenAlex请求429后没有把失败页面当证据，
Semantic Scholar提供两篇论文摘要。此次是定向补查，不是系统性/穷尽性综述。

## 当前结构究竟研究什么

当前实验包含固定多时间尺度储备池、请求动作的点损失/时序积分代理、同输入的本体context调制记忆漏率。
新增但尚未拟合的读出是固定交互r*tanh(G*c)：同一记忆可以随当前本体误差/相对速度改变作用。
G固定，最终ESN只训练线性系数；同特征MLP/RNN使用相同固定变换。它仍增加特征与计算，
不能只用“128神经元相同”宣称容量或成本完全相同。

需要支持的假设是：在接触负载已变化而任务尚未恢复时，当前本体信息能帮助记忆决定继续让位还是恢复推进。
第一公开条件观察到当前负载项与记忆项的动作方向冲突；第二条件存在接近目标却太晚进入release的失败。
这些是候选机制的动机，不是新结构有效的证据。代数分解不等于独立因果干预，反事实teacher请求没有被执行。

只有完整闭环对比、相同训练数据/seed的结构消融和保留条件评估才能支持机制主张。
若不同族分别选中不同数据、loss或gate，须称作选定方法比较，不称严格隔离的记忆实验。
当前新增读出没有拟合结果；ESN48候选/seed cap已满，任何新增拟合都必须先登记共享预算和截止。

## 理论陈述的边界

对当前leaky tanh更新，零初态、每个有效leak在(0,1]内可直接得到储备池分量位于[-1,1]，
最终action经过共同限幅。这个局部性质可由实现本身检查，不依赖机器人接触真值。

它不证明echo-state收缩，更不证明闭环无源。即便对同一外生输入序列，状态差的充分收缩条件还涉及
矩阵范数与有效漏率；谱半径小于1不等于所有相关范数都小于1。在机器人闭环中，后续本体输入又随
动作改变，因此网络状态有界不能推出接触力、全身速度或穿透安全。稿件应分别报告网络属性、公共执行器
限幅/变化率验证，以及物理子步实测安全，不混成一个“稳定性证明”。

本场景球接触的kN量级尖峰来自当前刚性接触模型，不能解释为已验证的人体安全力。较低P95或RMSE也不能
单独证明更好柔顺性：必须同时看任务成功、实际暴露、累计负载、恢复/推进，以及未恢复的右删失。

## 投稿前仍缺少的证据

- 三seed、全部公共开发与真正24留出条件尚未完成；RL office适配及增强神经baseline结果尚未齐备。
- 新读出仍只是工程实现；尚无完整同数据消融支持它改善恢复，不能在摘要中写成已验证贡献。
- 当前条件变化只覆盖固定几何的窄扰动范围，不等于跨办公布局、物体种类或真实硬件泛化。
- 只有补齐最终矩阵、实际成本、全部失败、三机位完整视频和局限之后，才能决定哪些主张值得写入RAL稿件。
  若ESN不占优，报告失败与改进方向，不能改变gate、解封后继续选权重或仅展示成功片段。

## 审阅归档

主机arm1@192.168.31.70：
/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/related_work_review_v1/
包含4份Crossref元数据和已读NG-RC出版商HTML，5文件内容/大小/模式核验通过。
tar SHA256：3c7b08994ab1e09d1daf0efed5f845843482a63d7f59ff0e98f9586fbfad961c。
HTML SHA256：b03455ff17545082d796162b922d3741a79df55b438e6c62160c20d84fcc8231。
元数据单独初始归档related_work_metadata_archive_v1保持不变，不包含全文阅读证据。

23:10UTC新增同根`related_work_review_v2/`，8文件逐内容/大小/模式核验（6份元数据/摘要响应、1份作者HTML、1阅读记录）。
tar SHA256 `2e68435b5e3ea6ca8f79efb0e698b8782d7c05cb500506b1e2477cd1f9cb3406`；
HTML SHA256 `61f4a5baada4835aabbddaf505d83c19c16e3e648e212e5ae8fa25790dbf9a46`；
REVIEW_RECEIPT.md SHA256 `84f7682a953d784ee260e6c846f815b25f9747904846ce4404b3d82db165b77b`。
原v1不覆盖；本次未使用封存数据，0新仿真/拟合。
