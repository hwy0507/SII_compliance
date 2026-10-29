# v9共同闭环资格修复（2026-10-29）

## 已完成诊断

18条配对开发回合已完整审查：每方法六条（三分离特化场景各train00/validation08），teacher对应身份均qualified。ESN5/6、RNN5/6、MLP6/6开发qualified。ESN失败为rod00，RNN失败为ball00；全部失败保存。此为开发资格，非正式Strict、未见测试成功率或最终主矩阵。

同身份rod00的初始canonical48与MJB一致；teacher动作精确回放、学生actor/filter回放通过。ESN在teacher历史动作MSE为2.56526e-6，RNN为3.77224e-6，但ESN闭环5.12s起饱和、整回合占57.2%，未完成撤棍前持续回位；RNN/MLP通过。离线动作误差不足以保证闭环稳定。teacher在失稳学生历史的反事实动作不是实际物理纠偏证明，也没有用作训练标签。当前证据不支持把失败简单归因于新版teacher蹭棍。

原组合office108保持51完整、57待补，Task5/Strict0。组合测试与三分离特化的范围不同，只是迁移压力结果，不能宣称主矩阵修复完成。

## 前瞻共同规则

保持原30条数据、24train/6validation划分和各方法各seed12候选拟合预算不变。108候选checkpoint、75拟合元数据、数据hash和旧选模排名均已逐一核验。ESN/RNN/MLP三个seed共九组使用相同规则：按原六条validation teacher-history MSE排名，最多检查前三候选；每候选按rod00/08/09、ball00/08/09、corner00/08/09顺序做九条闭环资格检查。首个完整失败即淘汰，全部九条合格则选择；因此选择合格集合中验证MSE最低者。只有完全相同checkpoint与场景身份的既有审查回合可复用。三候选全失败则null，禁止回退到不合格模型或启动最终测试。

这是开发阶段的资格筛选修复，不是增加ESN专属预算、降低成功门槛或使用office测试调参。九组全部锁定仍须独立审计，另冻结未见特化条件、正式Task/Strict与持续成功时刻后测评六指标。若预算耗尽仍有失败，继续仅train/val修复，不声称成功。

## 实际运行与入口失败

`nonrl_v9_common_eligibility_20261029_v1`已保留：AllowedCPUs在本机user service未落实为sched affinity，严格资源检查拒绝；零新仿真。v2加显式taskset后，发现user cgroup未委派CPU controller，没有cpu.max，检查器再次拒绝；零新仿真。两次均在execution创建前失败，登记与HANDOFF保留，不重启旧目录。

v3新脚本保留旧脚本，显式taskset CPU6，资源检查在cpu.max存在时核quota；不存在时仍强制sched affinity恰{6}，物理worker及后代只能用一核。MemoryMax3GiB、MemorySwapMax0、数值线程1不变。七项资源guard正反检查与五核心函数AST等价核验通过。未更改物理、MJB、gate、canonical48、公共filter、执行器或dt。

当前唯一仿真服务`sii-v9-common-eligibility-v3-20261029.service`，PID1684974，Invocation eab97f0b83e545e9956cd2cc230a6d44；宿主已核active，MemoryCurrent745828352/MemoryMax3221225472，swap上限0。实际worker PID1684987在CPU6执行ESN seed01 rank2 rod00；rank1复用原失败，没有重复仿真。该记录是启动快照，不是完成选模。

## 证据与共享

小证据目录`docs/evidence/nonrl_v9_candidate_catalogue_20261029/`：完整18条REVIEW、catalogue、mock合同检查、资源guard、两失败HANDOFF与明确LIVE_V3快照。V2合同检查绑定原runner；新增RESOURCE_GUARD_V3_CHECKS绑定v3 runner，不能混淆。当前v3登记绑定全部运行源，后续不得修改。

服务器仅共享存储：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v9_common_eligibility_20261029_v3/EVIDENCE.tar.gz`，14成员，129123bytes，SHA256 `1e2007e3759aa0914bdd1837850609b6394bcb7180d4a7bcda61a0108b990934`。本地逐成员和远端暂存/最终hash核验一致。此小包不含完整18条raw轨迹，完整raw仍本地待独立归档，不假称已全备份。

开工远端main d51f149cd9424c4cb31208d9517f8d07410ac0d6、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，已fetch/read两日志。Goal active；ESN实际改善及最终主矩阵均未完成。


本轮真实后续：ESN seed01 rank2（rho0.8/gain0.08/ridge0.001）在原失败的同身份rod00已完整qualified，400000子步。相同MJB/任务/安全门：峰矩34.3391Nm，最大外穿透0.067847mm，7.72s确认持续回位，撤回开始12.80s，领先5.08s。该改善只是一条开发回合，不代表其余场景/种子或正式Strict通过；rank2已继续rod08。三份审计小收据2569bytes/SHAce169d545f8961683f501d9fdbb8d3246a77c2c8dee0ca66246126b61a655ae4已逐成员与服务器hash核共享于上述目录`RANK2_ROD00.tar.gz`。完整raw尚未归档。首科学提交ba0c4c282e45604cdb212a03eb1937a6f8b0bafa已push并核远端。
