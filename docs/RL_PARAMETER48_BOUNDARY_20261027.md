# 参数48真实跨越200万回放边界验证完成

2026-10-27，Goal active。执行主机 `rltest-1025--a6ed2ff39b3c-z3ntpmmalx`，共享SSD根B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，源码B/repository/SII_compliance。原四正式48/29继续，没有改变训练算法或物理。上一轮冻结41全90/32→41对照完成属于实质进展；本轮是真实4m容量跨界验证，不重复原静态/合成边界测试。

再次实际查询/fetch/read远端main `e9f8dfddb6beb461bd3a0d43cab646ac4780c765`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未变；遵循sii-research-sync，无子agent。

## 实际跨界审计

原审计401313按预登记≥2001000阈值取得各路真实原子checkpoint，已完成退出。目录 `B/runs/parameter48_boundary_preparation_20261027_v1`。三份完整快照存其evidence目录，未写回正式训练或replay；审计全程CPU52/nice15、0新物理/优化。原REVIEW SHA `762b05db4d0bdf342b27203bc525c694cd2e18bb3d7167a0c27a5085e1bfd982`，独立保存算术及hash复核SAVED_REVIEW SHA `f837dd71d8baf453ba038c9b33590083e67dc97fba3e46ba41eb513cdc82a528`，均通过。

|方法|快照实际步数/行数|完整47保留行数|本轮新增行数|超过200万的行数|65536抽样中旧47行数|65536抽样中≥200万位置行数|
|---|---:|---:|---:|---:|---:|---:|
|impedance|2001180|1976180|25000|1180|64784|28|
|admittance|2002000|1976000|26000|2000|64697|66|
|vmc|2004000|1977000|27000|4000|64620|111|

最后两列不是全部抽样分类之和，其余为本轮新增但位置尚低于200万的行。抽样来自快照RNG的只读克隆，使用原CHEQ mask拒绝规则，不是实时learner的batch日志；未改变正式RNG。三路均覆盖旧47行和超旧容量的新行。

每份快照的完整47所有replay数组prefix逐元素相同；历史cycles保留，新增steps与梯度更新增量一致，优化器超参数保留、网络/优化器数值有限。原terminal128、projection、目标I-min/A-V-mean、actor-min、batch65536、UTD1和全部依赖hash保持。当前capacity4m，原1m→2m marker/entry23以及2m→4m followup/entry47两组历史元数据保留，不将历史入口重标成本轮。

三路分别全部25000/26000/27000新增记录的reward/action/observation/critic-clock映射核验，奖励重建最大误差0；30个原MJB、原sampler/CPU配置核验。审计范围是物理interval journal与回放映射、原生参数动作输入，非另行重跑物理或独立重建导纳/VMC内部动力学。

**这三份跨界快照都尚无本轮终端样本（terminal_coverage_count=0）。** 不能用本审计声称已覆盖本轮终端奖励/完成bonus；完整48原fullreview仍须审查后来产生的全部终端。当前在线训练已开始完成条件，不改变既有快照来追求额外覆盖。

独立保存复核核对快照/父47 SHA、完整47审查绑定、扩容两层元数据、行数/更新数/抽样计数、源hash及当时三原PID身份。未重复加载全部数组来冒充新的独立物理或抽样实验。三快照hash：

- I `3679ca5655b199f81dbfddd4b638b730f0fd3de176ac7b26af956a955827998e`
- A `577e610bef7fe794d3a5bb1886c2f8176a3bace82e36c3e773c02f312eb3637d`
- V `e98ce1e92c569089ac36a8303b61656c2282b4eb55c68c5ab03b49778ff3f188`

## 结束审查和换轮准备

原四正式：参数48 I359275/A359279/V359281、Direct29 241542继续；最新真实进度见LIVE_STATUS。原startup已完成，不重跑。原参数49准备401495/Direct30准备464829仍只等完整父后check-only；Direct29冻结准备3802347继续，冻结41原三评测及root已完整完成，无重复评估。

新增有限7200秒观察1132161：`B/runs/parameter48_serl29_transition_20261027_v1`，每2秒观察48→49/29→30，仅在本组原父退出后将原只读fullreview及其子进程移到释放的CPU13/0；不改正在训练的进程、无自动训练。退出→spawn界仍待实际退出和新轮启动，不能提前报GPU空闲时长。

新增完整结果保存复核：参数48为1132166，Direct29为1132169；各7200秒等待原fullreview/health/FINISHED，核对episode/optimizer算术及hash，Direct29固定870累计终端和930隔离。固定窗口原1908379（46–48）与336744（27–29）继续；新保存统计复核1219180/1219181等待各原结果，按原5%/nearzero1/相同seed/5000已存结果核对，不重跑bootstrap、不自动停止或训练。

手动49科学审查脚本 `/tmp/review_and_launch49.py` 已准备并保存至小证据operations，尚未执行。它要求完整48结果/health/saved、准确48恢复、真实跨界通过及固定46–48统计独立复核；只有窗口尚未全方法通过原描述稳定判据才允许本入口继续一个有限49，保留4m和entry23/47。执行前必须实际查看完整48及稳定性图；如果所有方法通过，需要重新判断健康/冻结要求，不盲目启动。Direct30尚只准备，待27–29统计与健康/冻结结果后决定，不为占用造假负载。

本轮没有重采GPU窗口；前轮冻结41退出后的纯正式60样本均值59.2167/70.7/57.5833/57.5833%保留，不能当成每瞬时或本轮重新测量。4m跨界通过不等于reward平稳或loss健康，整体Goal尚未完成。

小证据 `docs/evidence/RL_PARAMETER48_BOUNDARY_20261027` 共23文件逐大小/hash和Python AST核验。三份约1.3GB快照与正式raw/checkpoint/runtime均留共享SSD；本轮小证据包/push收据另记。HDD已满，只更新既有LATEST入口，不称HDD/arm1全量备份。
