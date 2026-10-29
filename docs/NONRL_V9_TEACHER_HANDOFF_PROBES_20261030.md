# 两条真实教师接管纠偏探针：已准备并等待安全接续

唯一接续服务`sii-v9-teacher-handoff-probes-20261030.service`已启动（原PID1755735），快照为`waiting_for_full_grid_null_boundary`，dispatch_attempted=false、零物理。单CPU6、数值线程1、MemoryMax3GiB、swap0。原唯一仿真仍为full12 PID1697598；不启动并发模拟器。源快照绑定1136文件，不能运行中编辑。

必须同时满足：原full12完整null终态且inactive、最终108等待器inactive且明确null/dispatch_attempted=false、最终108目录不存在。随后独立完整review，绑定终态/审核hash才正式登记两条探针，取得公共计算锁；等待最长6h，失败停止并保留，不重试/覆盖。未见测试保持未曝光，不涉及RL。

探针固定为已有训练身份rod00和失败MLP02原验证rank1，分别先执行学生175/275步（7/11秒），随后执行最新版VMC教师至原20秒完整回合。11秒探针覆盖更晚的学生偏离；此时刻并非固定接触/越棍门或额外actor输入。教师与学生观察同一canonical48，teacher前缀状态持续推进不重置；原物理worker/场景参数/MJB/filter/动作尺度/执行器/dt及gate不变。

执行器直接复用原物理worker，不编辑其源码。原execution.json保留student-diagnostic来源记录，新增HANDOFF_EXECUTION.json明确实际mixed behavior；handoff_actions.npz分别保存teacher/student、role、物理步完成标记和后缀候选loss mask。物理异常前最后一个已请求但未完成动作不算执行示范。source.tar.gz保留原来源，另handoff_source.tar.gz及全源hash绑定新适配器。尚无纯教师新示范，不能直接把旧collector标签当新数据。

独立审查用两个独立纯controller按保存观测重建teacher/student序列，再逐值拼接行为及检查label/mask；不复用采集切换实现生成预期值。再接入原公共filter逐步独立审计、原rod顺序/保持检查与原Task/安全资格审查，比较相同MJB、初始canonical48/filter。完整失败仍保留。qualified仅使**实际执行teacher后缀**成为后续增强候选，前缀teacher仍反事实；尚不自动进入训练或改变数据划分。后续循环模型需要前缀warmup/后缀loss mask的共享新协议，三方法公平重训，不能给ESN部署手工纠偏。

零物理验证通过：两种前缀的真实保存历史独立纯controller回放；完整/注入物理异常两条worker集成路径；真实prepare/hash检查和重复prepare拒绝；五种等待边界控制。错误路径保存3个完成动作、第四个未完成，不产生teacher示范标签。源码编译通过。首次只检查mock未覆盖prepare的mkdir，已补真实prepare/check控制并修正后通过；无物理失败/重启。以上控制不是动态恢复成功证据。

当前七组开发合格：ESN/RNN各三seed、MLP01。MLP02完整12失败保留，其中rank12撤回前回位成功但穿透0.218604mm>0.2mm，不能混写为完全不回位。MLP03后续筛选仍运行。最终九模型锁定、未见108/六指标/媒体仍待，旧office108的57待补保留，Goal active。新探针尚无结果，结论须待真实执行审查。
