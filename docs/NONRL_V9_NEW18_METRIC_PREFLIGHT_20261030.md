# 新增两组模型18条开发回合最终指标路径预检

ESN seed2026102801的rank4在完整12共同资格选择中九条全部合格，MLP seed2026102801的rank1此前也已合格。这两组未包含在先前45条预检中，本轮只对这18条新回合执行最终v2指标路径与独立actor/filter replay，没有重复计算旧45条、不积分、不拟合、不读最终测试或用时间再次选模。

18/18审查通过：Task、三特化Strict、完整20/30/13s时长与5e-5子步时钟、机器安全、13采样任务终态保持确认、checkpoint动作与公共filter精确回放均通过。七组已选开发模型因此均有对应预检证据，但这不是九组模型全锁定或未见泛化证明。

| 新审查模型 | 回合数 | 终态确认时刻范围(s) | 九回合最大峰矩(Nm) | 九回合最大外穿透(mm) |
| --- | ---: | ---: | ---: | ---: |
| ESN seed01 rank4 | 9 | 9.36–18.04 | 54.032208 | 0.072482 |
| MLP seed01 rank1 | 9 | 9.44–16.92 | 51.676148 | 0.139156 |

表是混合三场景开发范围/最大值，不是正式平均峰矩、SPT或方法胜负。未计算局部T_ref/SPT。人体实际接触舒适度仍NA；棍/球扰动接触力矩代理和实际人体指标分列，不用代理冒充人体舒适。

独立入口`docs/evidence/nonrl_v9_candidate_catalogue_20261029/audit_new_selected_metrics_20261030.py`冻结精确execution/registration快照，并核完整12协议、选中candidate及九case、checkpoint/qualification全部输入hash。逐格错误保留failed_preserved，任一失败总体不得passed。结果与快照见同目录`NEW18_METRIC_REVIEW.json`等；源码放docs目录，不修改正在运行的1132绑定tools/scripts。旧45条证据见`NONRL_V9_SELECTED_METRIC_PREFLIGHT_20261030.md`，两份证据范围各自独立，不宣称本轮重新审查63条。

剩余MLP seed02前五验证排名候选在完整rod00均Task=true，但撤回前持续回位失败；rank2安全通过，其他四另有外穿透超0.2mm。rank6仍在途，seed03完整候选后续待。保留全部失败，继续原完整12规则，不降低gate。最终108等待器尚未派发，Goal active。
