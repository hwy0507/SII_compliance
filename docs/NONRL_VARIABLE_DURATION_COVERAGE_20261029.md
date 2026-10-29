# 补采后的实际训练覆盖检查

原108尚未结束，主矩阵修复仍未完成。本轮新增独立工具，修正后续覆盖诊断不能处理
变时长示范的入口问题；不修改在途或八球v5绑定源码，也没有新采集、拟合或物理审计。

原`audit_v8_train_direction_coverage_20261029.py`写死24条train合计12,600帧。
它适用于原v8，但后续球轨迹延长至30秒后不能直接复用该帧数断言。
新`tools/audit_special_coverage_dataset_20261029.py`根据真实lineage逐episode核对帧数，
保留每场景8train+2validation、canonical48、7维requested action及40ms采样时钟。
在计算描述统计前拒绝重复身份/目录、未归属行、错误计数、split泄漏和非物理数据标记。

仅对24条train提取原始trajectory的观察和action，并逐元素核对数据集及文件hash。
复用原方向分箱(component≥0.8)和估计载荷分箱；输出逐示范及场景聚合，
没有把方向阈值变成资格gate，没有统计validation动作/观察。
这是方向×估计载荷的实际覆盖描述，**不包含完整阶段×历史状态联合支持度证明**，
也不能替代teacher资格、接触审计、棍推顺序审计或闭环六指标。

验证工具`tools/check_special_coverage_dataset_audit_20261029.py`完成：

- 内存中的30个变长度身份，共465行，正确划分通过；不是物理数据或训练标签。
- 九项拒绝检查通过：validation标为train、未归属身份、重复目录、错帧数、空回合、
  非物理行、错误命名划分、非布尔split、错误action形状。
- 对实际v8的24train/12,600帧重新读取，所有逐示范及场景统计与原准确报告逐值相同；
  原±Y方向覆盖缺口仍然存在，未因更换检查工具被隐藏。
- 八球v5全部198绑定源码hash保持，REG仍`be0056d3…`，未启动。

检查服务`sii-special-coverage-dataset-check-20261029.service`自然exit0，261ms/CPU190ms。
启动请求CPU affinity6、数值线程1、MemoryMax512MiB/禁swap；瞬态服务已回收，
事后not-found返回的默认资源属性不能当作真实运行资源读数。本次未保存内存峰值。
这不是仍待原用户问题回复的可选004轨迹审计，未重新派发该动作。

准确检查[CHECK](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VARIABLE_DURATION_COVERAGE_CHECK.json)
SHA256 `a5f099056130302ce81213d54e646184a195602e6d00a4b30679c6a2eda01b39`；
[实际覆盖](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VARIABLE_DURATION_ACTUAL_COVERAGE.json)
SHA256 `b45b812ca966efc5b7723d56634fd3846417377af85957b858a47a8a6bd79849`。
四成员源码/检查包已逐成员及暂存/最终大小hash核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_variable_duration_coverage_20261029_v1/SOURCE_AND_CHECKS.tar.gz`，
11516bytes，SHA256 `ceb3511e4abc4797ad9c2bb0194692c1f5772042da265e82dee25549c4c47f7b`。

后续按原顺序：原108完整后处理/审查归档→八球v5全八审查→正式三场景30条计划与采集资格
→原v3 builder构建共同数据集→使用新覆盖工具检查实际train分布→公平重训/冻结108回归。
新工具使用`--training <新训练根> --output <不存在的报告路径>`，仍须在有界只读进程中执行。
不要只看计划参数范围便认为覆盖已补齐；新数据/新效果尚未产生。

开工实际fetch/read main `dd2fe5c1f48bedd385accbd1af901dc0a74c2878`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。03:55原1172675/后处理1201537仍active，
原57条；04:00已58/108，原后处理等待完整矩阵。上一轮verified wait，本轮完成新检查入口，
Goal active，无RL/子agent/服务器计算/删除，不宣称研究修复完成。

04:03:14 UTC收尾再核原两服务loaded/active，startticks仍32623702/32942337；
原矩阵59/108，seed2 MLP在途，原科学继续。
