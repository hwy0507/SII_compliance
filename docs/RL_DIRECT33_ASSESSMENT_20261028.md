# Direct33完整审查与数值收敛阶段完成（2026-10-28）

**Direct已满足当前训练条件下原“reward平稳、loss未见异常”的经验数值标准；保留完整33，不启动额外34。整体Goal仍active：阻抗/导纳/VMC参数54继续，原53–55窗口尚未完成。GPU守护v4继续，包括已退出Direct所在GPU0。** 这不是任务成功、全局数学收敛、多seed泛化或最终ESN比较的声明。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮实际查询/fetch main `924ff3fb1e9b1a109259cd2177c065a47a93852a`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，已读取相同分支日志，无新科学约束变化；保留并行非RL成果。上一交接[参数54早期检查与55准备](RL_PARAMETER54_EARLY55_PREP_20261028.md)仍有效，但其中Direct33/34准备仍live是历史快照。

## Direct33完整结果

原learner259795正常到达1369290steps、10914328critic updates并退出，30/30条件完整55秒/noabort。独立archive已存在且与最终checkpoint逐SHA一致：

`B/runs/serl_take_cycle33_archive_20261027_v1/direct/cycle_00033.pt`

SHA256 `783eaa7f7b03226915539e41cce313a5faeb4d49a15ae25626bb9762a9f47849`。

完整review在`B/runs/serl_take_cycle33_review_20261027_v1`，REVIEW/DIAGNOSIS/FINISHED/SAVED_REVIEW均通过。旧1328040条raw/derived replay全部字段、history/optimizer配置/2m/entry23保持；新41250全部成熟、32步行为目标精确、原930隔离pending保持且不可采样；完整新奖励按冻结journal重算误差0。没有独立重跑全部原始物理，也没有伪造完整25。

| 指标 | 完整33结果 |
|---|---:|
| 平均回报 | −30.902455898 |
| Task / Strict | 0 / 0（各30条件） |
| critic loss首1000均值 | 0.008725863 |
| critic loss末1000均值 | 0.008436733 |
| critic loss全41250均值 / 最大 | 0.008569069 / 0.016270868 |
| actor loss首 / 末1000均值 | 20.387918949 / 20.384912453 |
| 终端Q绝对误差均值（990终端×10critic） | 0.027468827 |
| 注册32步TD绝对误差均值 / 最大 | 0.025459949 / 1.425813675 |

critic/actor全记录有限；loss和health两图已实际查看，critic平缓下降、actor有浅幅变化但未见发散。单步TD MAE .034230880另列，不冒充训练使用的32步目标误差。temperature .000256707仍缓慢变化；没有把全部参数严格静止作为额外门槛。健康诊断前后network/optimizer/RNG不变。

## 接受Direct数值阶段的依据与边界

本轮重新读取并核对原27–29稳定REVIEW、独立保存复核、完整29/32及health/loss；冻结29全部30份FROZEN_PHYSICAL_REVIEW hash与checkpoint身份再次核验，无新物理/bootstrap。

- 原预登记27–29的5%检查通过，首尾相对变化0.0000462118546（0.004621185%），near-zero保护未触发。原窗口、30条件分母、seed和公式不变。
- 29首/末1000critic .010189882/.009746882，32为.008966154/.008772255；33完整结果支持平台继续维持。没有把回顾性的32/33改名为新的前瞻窗口。
- 原选定的冻结29全30、33000000物理子步已经完成，Task/Strict0/0、机器违规0、正式状态未改变。它只证明29在这些训练条件及一个外部动作seed上的冻结结果，**不认证更新后的33 checkpoint，不等于任务成功或held-out泛化**。
- 历史cycle0 mean−34.223282408到29−30.909745861已有描述性改善，跨历史算法阶段不能作单因素因果。Task0单独披露，不追加为新的收敛失败条件。

决定文件`B/runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json`：direct_numerical_criterion_satisfied=true、launch34=false、overall_goal_complete=false。原固定窗口的冻结证据仍选29，最新恢复状态为33，二者用途明确。保留33全state，不为了占用GPU再追加Direct轮次；GPU占用由独立守护维持。未解决的三参数方法继续训练和评测，指定ESN/最终比较缺失不以历史ESN替代。

## 审查失败与修复全部保留

原归档monitor259815已经正确复制并核验checkpoint，随后full review导入run/audit_source里的旧helper，残留`row['cycle']==32`导致AssertionError。原run/ARCHIVE_REVIEW_FAILURE.json、archive_review.log、完整review_initial_failed.py保留。修复仅把review.py的helper搜索路径改为自身OUT，使用已生成且逐字节等于33 startup_retry3通过版本的helper，没有删除断言、修改训练或checkpoint。

恢复coordinator3237350已完整结束；完整review/health/两图和独立保存算术通过后写入run/ARCHIVE_REVIEW_FINISHED.json，显式引用保留的原失败与恢复review/health hash。原34仅恢复waiter1059038因该失败已退出，direct_FAILURE仍保留；**没有实际34 check-only，不要重启等待或启动34**。这不是整体Goal暂停，也不影响参数54。

## 本轮准备与后续进程

`B/runtime/direct34_dispatch_preparation_20261028_v1`保留可选34的startup/helper/archive/手动launcher及源码freeze/diff。缺少DECISION34时试运行按预期在任何修改或子进程前拒绝，FINAL_LAUNCH_REJECTION记录最终源码hash。34候选只是准备，未执行；本次阶段决定不使用它。

完整33 loss waiter2822749已完成（`B/runs/direct33_complete_loss_20261028_v1`），全41250连续步、Python statistics独立均值/极值与源hash通过，图已查看。不要重跑已完成审查。

04:51 UTC，参数54原I/A/V PID2116858/2116859/2116860及起始ticks核验live，steps2250119/2250155/2251430，每路仍30sampler。归档monitor2116861、55仅恢复2450050、原53–55窗口514418均live。55恢复仍待完整54退出与审查，尚未执行check-only或正式55。继续保留完整optimizer/replay/RNG/history/4m/entry23/47及原学习率/reward/gate/物理。

GPU守护supervisor1629438、worker1629439–1629442继续。Direct退出后独立保存一次GPU进程集合：GPU0只有guard1629439，利用率69%；最终即时四卡70/96/92/92%。这是含合成负载的当前快照，不是新固定窗口或永久50%保证。守护在训练完成后持续至STOP/系统关机，不是重启服务。

## 持久保存

小证据`docs/evidence/RL_DIRECT33_ASSESSMENT_20261028`。共享SSD两包均逐来源成员大小/hash验证：

- 准备包：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_DIRECT33_ASSESSMENT_20261028_043918/PREPARATION_EVIDENCE.tar.gz`，12229字节、13来源成员，SHA256 `e02b943e9b54422aade466c4208061475b7ff4148a5ea1c1b946dba72fd4cdbd`。
- 完整33补充包：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_DIRECT33_ASSESSMENT_20261028_043918/COMPLETE33_EVIDENCE.tar.gz`，424498字节、26来源成员，SHA256 `6c2c6411b6756a2f1485b12c5afd8d1a2af5531fd8e23195cbfba13b4fc4fed6`。

补充包含完整审查源码/修复diff/原失败/两图/episode及决定；大checkpoint与全部optimizer/raw仍共享SSD，不是HDD/arm1全备份。HDD原LATEST只更新入口。下一步聚焦完整参数54、准确55续训及原53–55稳定审计，不重复Direct29冻结或无条件续训34。
