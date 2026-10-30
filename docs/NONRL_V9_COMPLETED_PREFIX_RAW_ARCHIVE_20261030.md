# 已完成闭环前缀的完整原始数据归档

本轮补齐大文件证据保存，不把开发闭环资格当正式测试成功。原采集30条与75拟合/108候选的完整归档、原18配对归档继续保留；这里新增共同开发筛选已落盘48条的独立快照。

## 快照范围与一致性

新增工具`code/mujoco_6d_vmc_benchmark/tools/archive_v9_eligibility_prefix_20261030.py`只读取协调器execution的一次字节快照，核登记hash及共同候选顺序/预算，然后仅收集该快照已经登记完成的回合。每回合核qualification全部输入hash、checkpoint/metadata、原执行complete及科学资格标志，完整包含raw子步、保存状态、动作/filter、MJB、执行记录、配置、源码tar、失败收据和审查日志。原18复用回合也实际纳入本包，不只是外部链接。

包内`execution.snapshot.json`与`REGISTRATION.json`是精确快照，`MANIFEST.json`记录每一成员大小/SHA及原绝对来源到archive_prefix映射。逐成员独立解包流式SHA复核后，再核所有源文件前后hash和登记不变。协调器可继续写新的顶层execution，归档不读取或声称包含其后新增的回合；正在写入且尚无完成收据的回合不会进入本包。源和失败不删除。

快照execution SHA256 `09dc37d29c406d004bfc1d6b048e8bc4f9667f88372e76c865d13db677f40a4f`，登记SHA256 `bc2994e299dec10fba75a50c53f3bf4e5064a4c5d253fb91472b6b3ba1add933`。

| 方法/seed | 本包完整回合数 | 科学失败数 |
| --- | ---: | ---: |
| ESN 2026102801 | 8 | 3 |
| ESN 2026102802 | 9 | 0 |
| ESN 2026102803 | 9 | 0 |
| RNN 2026102801 | 13 | 1 |
| RNN 2026102802 | 9 | 0 |

四条科学失败完整保留：ESN seed01 rank1 rod00、rank2 ball09、rank3 rod00；RNN seed01 rank1 ball00。不能把48当作48个独立未见条件或最终108已完成数。

另外对索引中的全部48条再次运行v2独立时长检查：各自达到登记rod20s/ball30s/corner13s，完整时钟/800子步/物理dt及manifest一致，48/48通过。证据`COMPLETED_PREFIX48_HORIZON_AUDIT.json`绑定同一索引与execution快照；这里的“完整”不只依据wrapper complete标记。四条科学失败即使跑满仍然失败，不因归档改变资格。

## 实际产物与资源

1088 payload文件另加三个快照/manifest成员，2815777483 bytes。归档SHA256 `f383e8d24c80b2d21e5ce9dfc116be1397e00d0c3bdffe24077adc1f7ccb22f8`，manifest SHA256 `9602c958ca95377f97cabff0941ff43933bf3f3b076108ca74f52900e139f827`。

本机服务`sii-v9-completed-prefix-archive-20261030.service`显式CPU6、Nice19、idle I/O、512MiB、swap0；00:52:29–00:55:09本地时间运行并自然exit0，CPU75.010s。在途核OOM全0；memory.max回收事件不当成OOM或仿真失败。无新积分、拟合、渲染或服务器计算，原单仿真服务不变。

服务器独立目录：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v9_completed_prefix48_20261030_v1/COMPLETED_PREFIX.tar.gz`。最终是否共享以`COMPLETED_PREFIX48_SHARED_RECEIPT.json`的实际暂存/最终大小与hash核验为准，不能拿启动传输冒充共享完成。恢复时按MANIFEST的source_folder/archive_prefix映射定位，成员保留原scene子目录。

小型索引/本地核验收据位于`docs/evidence/nonrl_v9_candidate_catalogue_20261029/COMPLETED_PREFIX48_CASE_INDEX.json`与`COMPLETED_PREFIX48_LOCAL_RECEIPT.json`。完整训练数据/候选拟合另见既有`nonrl_v9_complete_fits_20261029_v1/COMPLETE_FITS.tar.gz`，本包不冒称再次包含整个训练集。

## 当前研究仍未完成

归档后独立开发prefix审查已核49完整case（4失败/4复用/4 selected组）：ESN seed02/03、RNN seed01/02各九条全qualified。RNN seed03继续，MLP与完整12候选接续仍待；ESN seed01不能以其他seed替代。此49与归档48是不同时间点快照，不能混写。

最终九模型锁定、冻结三特化未见108、统一六指标和最终媒体/完整raw共享仍待；原组合office108的57未完成格不覆盖。Goal active。
