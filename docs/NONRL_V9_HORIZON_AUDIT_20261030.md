# 三特化闭环修复与完整回合审查

## 当前实测进展

共同开发筛选的独立prefix审查已核32条完整case，含4条失败、4条精确复用及2组完整选择。ESN seed2026102802和2026102803均通过同一九条train/validation闭环；seed01前三候选耗尽，不能回退为合格。当前RNN seed01的第二排名候选继续，其前三棍推中的rod00/08已经通过。三方法同一数据、预算和九开发条件，不读取未见测试选模。

这证明部分ESN闭环问题可以在原有训练方案及冻结门槛下修复，但不证明九组全部修复或正式泛化成功。此前已核teacher动作精确重放、初始canonical48/MJB及学生actor/filter；离线MSE小仍可能闭环失稳，球撞物块不稳也可以没有动作饱和。不能单凭一次蹭棍改动解释全部失败。

原共同筛选服务保持PID1684974/Invocation eab97f0b83e545e9956cd2cc230a6d44；1115源hash全匹配，真实子步推进。完整12候选后继PID1697598仍仅等待，未启动第二仿真。CPU6、线程1、3GiB、swap上限0、两服务OOM计数全0。详见`HORIZON_LIVE_20261030.json`，这是时间点快照。

## 评估实现补齐

冻结指标合同原已要求“完成全回合”，但v1机器合规实现只核wrapper的`status=complete`和力矩/穿透。底层legacy脚本物理中止可能仍正常返回，因此该状态不能独立证明跑满时长。

新增`code/mujoco_6d_vmc_benchmark/tools/audit_special_scene_metrics_v2_20261030.py`，保留原冻结文件不动，以独立登记的预期时长核25Hz步数、每步800子步、5e-5s物理dt、两层完整时钟、manifest时间、轨迹/子步hash与legacy invalid_physics。可读短回合仍保留指标行，但机器合规与Strict为false；数据损坏则拒绝审计，必须保留基础设施失败收据，不能删除格子。Task仍继承原谓词，门槛不改。

预期时长必须由最终派发登记传入，不能从观察到的末帧反推。当前开发预算为rod20s/500步/400000子步、ball30s/750步/600000子步、corner13s/325步/260000子步。未来最终runner须绑定此新增审计源hash及预算，再接入完整矩阵；本轮没有创建或派发最终测试。

## 实际验证与限制

`check_special_horizon_contract_20261030.py`验证完整回合、短回合即使complete仍失败、invalid_physics失败、failed状态失败；拒绝超预算、非有限、缺子步、时钟断裂、dt错误、manifest时间不符、非25Hz格点预算共七类损坏。原18配对轨迹全部时长审查通过，故这个缺口不是原18性能差异的原因。

实际RNN seed01 rod00的400000子步v2完整指标预览通过：任务13采样确认9.52s、峰矩34.526338Nm、外穿透0.0740395mm、机器合规。只读mj_forward与replay，不做积分；是开发预览，不据此发布SPT。没有human force通道，人体舒适仍NA，棍/球代理单列。

首次预览因缺少`PYTHONPATH=scripts:tools`导入失败，日志完整保留；补齐启动环境后独立重试exit0，不改冻结源码、不重复物理。旧预览不覆盖。

证据位于`docs/evidence/nonrl_v9_candidate_catalogue_20261029/`：`HORIZON_AUDIT_20261030.json`、`METRIC_V2_PREVIEW_ROD00_20261030.json`、`SELECTED_TWO_PREFIX_REVIEW_20261030.json`及失败日志。独立服务器共享收据另存`HORIZON_SHARED_RECEIPT_20261030.json`。

Goal保持active：九组完整共同资格与独立审查、最终模型锁定/执行入口、未见三分离108、完整六指标和归档尚未完成；原组合108的57未完成格继续保留，不冒充新主矩阵。
