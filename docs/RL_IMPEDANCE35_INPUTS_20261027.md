# 阻抗35保存终端输入与critic误差转移

2026-10-27 UTC。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。Goal active，无子agent；四正式36/Direct22及原冻结32、37/23恢复准备和两稳定性等待继续。此次不新增训练或仿真，问题来自上一轮固定1045结果：总体终端SSE增加，但原focus大幅改善。

原保存值分析3501505已结束。只读完整34/35先前保存的终端输入、Q、奖励、mask及原11/31/34终端transition元数据，0神经推理/优化/物理/replay写入。源和8个输入hash前后核验，AST/--help通过；独立scalar math.fsum与math.dist穷尽候选复核和图核对通过。选择发生在完整35结果及初步保存数组检查之后，是探索性分析，不冒充预登记预测。

|critic索引|34固定终端in-bag SSE|35相同终端in-bag SSE|差值|
|---|---:|---:|---:|
|0|482.207007|642.795658|+160.588650|
|1|1550.342719|1270.092689|−280.250029|
|2|176.432723|26.811104|−149.621619|
|3|110.166897|394.255033|+284.088136|
|4|2327.252532|3326.831322|+999.578790|

五项净增合计1014.383927，与原固定1045跟踪一致。不是所有critic同时恶化，也不是仅mask0预测误差；以上只统计mask1训练行。终端项仍不是全部在线TD loss，不把critic4净增占比称作训练loss的因果份额。

1045个完整55维critic输入（已登记归一化observation50+raw action5）全部不同，没有完全重复输入组，也没有此有限样本集上的“完全相同输入、不同reward”直接证据。这不排除部分可观测性或函数近似限制，不构成全replay无冲突证明。

三组探索性比较固定为已保存最大/第二大行SSE增加及原先登记focus。对于各指定critic，只在它的mask1终端中穷尽搜索相反reward符号的最近输入，不改任何缩放：

|focus / critic|原条件及结果|最近相反标签训练行|完整输入L2|observation50 L2|raw action5 L2|
|---|---|---|---:|---:|---:|
|484123 / 4|第11轮short0600，Task真/Strict假|484077：同轮short0400，Task真/Strict真|.069882465|.001379643|.069868845|
|1306248 / 1|第31轮short0300，Task/Strict真|1306210：同轮short0600，Task真/Strict假|.053989106|.001550410|.053966840|
|1432256 / 4|第34轮short0600，Task真/Strict假|1430170：同轮short0671，Task/Strict真|.063071838|.001320577|.063058012|

第11轮旧行484123的reward−28.270920，critic4预测从−27.452715变成+23.999083；其它四critic在35都仍约−28。它的近邻484077为reward+25.500774、critic4在35约+25.539165。原预选1432256则相反，critic4从+16.969294修正到−27.760746，reward−28.351505。两条旧失败终端上的误差转移与原固定样本观察一致，未证明两者间的训练因果关系。

元数据核验这些正/负终端都Task成功，Strict标签不同；terminal项为+25/−25，正例另有completion_efficiency约3.77–3.85。不能由此推断具体物理门失败原因，也不能把不同条件/动作/历史结果当作相同状态。输入观测是最后动作区间之前的replay观测，不是55秒最终物理状态。欧氏距离不是网络学到的距离，没有据此设“不可区分”阈值或声称误差不可约。

本轮结论只定位了保存终端误差在critic和旧样本间的转移，并排除了该有限集合中可直接观察的完全重复输入冲突。尚不足以凭此改变reward、canonical输入、学习率或物理gate，未改变正式设置。继续等待原完整36健康和固定36–38稳定性，以及原冻结32全30结果；不重复该保存值分析，也不自动追加候选训练。

源码code/mujoco_6d_vmc_benchmark/tools/audit_impedance35_saved_terminal_inputs_20261027.py；实际runtime快照B/runtime/impedance35_saved_terminal_inputs_20261027_v1，结果B/runs/impedance35_saved_terminal_inputs_20261027_v1；小证据docs/evidence/RL_IMPEDANCE35_INPUTS_20261027。原18进程身份/步数见FINAL_LIVE_STATUS.json。新图per_critic_terminal_transfer.png已查看。

本轮重新查询/fetch/read远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，均未变。GitHub认证问题和指定ESN缺失不重复索取。HDD配额已满，新交接/证据仅SSD，更新现有LATEST入口，不称HDD/arm1全量备份。
