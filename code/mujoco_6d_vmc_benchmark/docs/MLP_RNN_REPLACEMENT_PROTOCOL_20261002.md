# 固定teacher数据：MLP/RNN替换ESN

2026-10-02 13:15:35UTC开始，依据用户“改成MLP和RNN（替换ESN）看看效果”的新授权。
上一四小时任务已经结束；本轮是新限定8回合对照，不延长旧deadline、不建定时任务。
开工main14820fac7141fa8779aa56b5ae0ba595ee2ee0a5，baseline133a0b4306f70dd703629bf1227961899d6abcfd。
两分支日志与本机/服务器作业已核对，无本轮重复任务；baseline未合并、独立WBC未接入。

固定office-tool-contact-v5/55s/dt1e-4/seed2026091751，原MJB b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1。
冻结世界、名义规划/WBC、观察语义、执行器幅值与变化率、task/strict及外穿透≤.2mm。
两组旧数据直接复制并核对metadata中的training_data hash：四小时产物中
esn_original_system_id_v2与esn_integral41。前者是原VMC诊断，后者是推进较远学生的恢复teacher；
两组均含失败的实际teacher轨迹、明确的反事实重标注、独立合成身份留出，不是成功数据。

每组MLP/RNN×seed2026100201/2026100202，共8模型和8完整开发回合。
均128隐藏单元、无bias、输入只选与对应ESN相同的canonical现有字段，按train数据std缩放；
原VMC只用39:45，恢复teacher用14:17、20:23、26:29、39:48。无物体/接触真值、阶段、事件时间、视觉。
内部不复制ESN手工交叉特征或context门控，普通MLP为tanh(Wx)，普通Elman RNN为
tanh(Wx+Uh)，循环矩阵U通过梯度学习。输出为7维公共动作；部署无teacher、混合controller。
只有全部所用输入为零且零状态时严格零输出；不声称维持旧ESN的任意context/零负载约束。
公开实际可训练参数；128宽度不等于参数/FLOP相同，旧ESN还另有128非线性读出单元。

两模型同数据、身份切分、重要性权重、seed、序列batch顺序、2400更新；AdamW lr=.001、
weight_decay=1e-5、梯度范数≤1。按完整episode打乱组batch8，连续64步块（2.56s）训练；
RNN跨块保留detach状态，episode边界清零，padding不计loss；MLP看相同块。
loss=动作MSE+.25相邻动作增量MSE，标签为实际公共filter之后的teacher动作。
每完整epoch及最后一次更新按完整合成留出序列MSE选checkpoint，不用物理闭环选训练权重。
RNN推理时不每64步清空。保存数据/源码/命令/seed/hash/训练曲线/导出重放和状态审计。
旧ESN只作历史同数据参考；其训练机制、更新数（2400/4000）和参数预算不同，不能作严格单因素优越性结论。

8条闭环串行、本机单模拟器/1线程/MemoryMax3GiB/Swap0，不另开服务器仿真。
先验固定模型、不据单回合追加调参；所有失败保留。task=实际松手稳定放置，strict加原安全；
三指标按完整物理子步复算，低RMSE/低峰速不代替放置，峰速不做正向奖励。
本轮是已见场景开发，不解封保留集、不自动解锁正式或泛化结论。最后更新文档、核验服务器
独立归档并commit/push main。

文字勘误：运行内冻结protocol.md曾将AdamW简称为Adam；实际启动前trainer一直使用AdamW。
本文件补齐准确名称，不改变已预登记或实际执行的优化器/超参数，原运行协议hash保留。
