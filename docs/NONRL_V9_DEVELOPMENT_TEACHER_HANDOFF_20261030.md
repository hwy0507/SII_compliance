# 教师接管纠偏采集算子的实现与零物理验证

MLP seed02原12候选预算现已全部耗尽；这组不能锁定。完整12 campaign仍在检查MLP seed03，不抢占/重启现有仿真；最终108等待器不会在null时派发。ESN/RNN各三个seed及MLP seed01七组合格保持，不能以它们代替缺失的两组。

新增`tools/development_teacher_handoff_20261030.py`仅用于后续开发数据采集：同一canonical48历史每步同时推进学生和最新版VMC教师，前N个动作执行学生，此后执行教师；教师接管时保留从真实前缀观测形成的教师内部状态，不把教师状态错误重置为零。切换计数是采集操作协议，不能作为最终学生输入或测试时手工恢复逻辑。

`last_teacher_action`明确区分来源：前缀教师输出为未执行反事实，不能冒称成功VMC示范；后缀教师动作确实被选为行为动作，但仍须真实物理执行和完整资格审查才能进入训练数据。算子不改公共filter/动作幅度、物理/gate，不能凭切到teacher就假设能恢复。后续公平增强数据应由三方法共享，包含前缀上下文以重建循环状态，同时只对审核过的实际教师后缀计示范损失；训练数据接口/权重须另登记，当前未改数据或重训。

仅saved-history控制已通过：原合格teacher rod00和失败MLP02 rank1 rod00两条历史 × N=[0,1,125,175,500]五边界，共10条；分别独立重放纯student和纯teacher，逐值核拼接行为、teacher标签、角色数量、reset后首动作与0.04s时钟。N=125/175分别是候选开发采集5/7s学生前缀，**不是已执行探针**。8类错误输入/调用顺序拒绝通过（负/布尔/非整数计数、无observe先act、错误shape、重复observe、错误dt、wrench不匹配）。原轨迹qualification全部input hashes和checkpoint前后hash核验。

证据入口`docs/evidence/nonrl_v9_candidate_catalogue_20261029/check_development_handoff_20261030.py`，结果`DEVELOPMENT_HANDOFF_CONTROLS_20261030.json`。这验证采集算子切换/数据来源，不验证纠偏动态、Task/Strict、示范安全或任何新模型训练成功。当前**尚无完整采集wrapper/新registration/物理派发/新示范或拟合**。下一步须完成独立集成审查：等原full12结束且服务inactive、完整review确认null，并核最终等待器退出且无测试派发后，另登记有限的真实纠偏探针；每条完整保留动作/子步/filter/源码/失败收据并审查teacher后缀是否真实回位，不能把本10条回放当物理结果。

新工具是新增文件，不改原1132绑定源及最终等待七文件。旧office108历史不覆盖，最终三特化108/六指标/媒体仍待，Goal active。

补充具体失败：MLP02 rank12已在撤回前持续回位，但外穿透0.21860435758863944mm超过冻结0.2mm安全门，所以仍失败；不能把“12候选均失败”改写成“12候选都无法回位”。该对照有助于区分回位控制与安全裕度问题，安全门不放宽。
