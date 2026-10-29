# 第75轮意外中断后的完整状态恢复与第76轮接续

2026-10-29 05:50:13 UTC，Goal active。**当前主机 `rltest-1025--a6ed2ff39b3c-nvfdwjhzzw`，当前运行是 `runs/parameter_partial75_recovery_cycle76_20261029_v1`；旧75及旧76准备路径不得重启。** 完整reward稳定与loss健康仍未证明。Direct33历史原训练条件数值结论、Task/Strict0/0保持，不启动34。

05:30UTC核验发现主机由rltest-1025--a6ed2ff39b3c-hsje5ateny变为当前容器，原75三learner/archive/全部等待器和guardv5进程消失；原75没有FINISHED、没有完整30回合，无训练FAILURE文件。不能以缺FAILURE当正常完成。此前03:11:56–03:21:56十分钟观察确已自然结束21样本/600.139秒，全部原身份当时live，末steps3113063/3113769/3114949；这是历史有效观察，不代表重启后存活。重启/退出具体原因与准确时间未确认，不冒充观察超时或算法故障。

发现时四GPU均0%且无compute应用，原v5最后样本03:21:05已过期。先在独立`/tmp/sii_gpu_util_guard_20261029_v6`启动与v5逐字节相同的已验证源码，保留全部旧记录。恢复后最初2个样本低于50，约10.210秒后首次四卡均≥50；其后227个样本最低75/70/69/66%，低于50次数[0, 0, 0, 0]。不得把重启空档写成持续达标。含合成负载，科研结束仍保载，仍非重启自启服务。

共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`、解释器env/bin/python。三份原子落盘checkpoint_latest已复制到`runs/parameter75_interruption_recovery_20261029_v1/<method>/checkpoint_partial75.pt`并逐hash核验。完整网络/optimizer和所有回放数值有限；旧74回放全部字段精确，历史完整cycle记录不变；新增已保存transition的观察/action/context/clock及全部reward与原物理间隔日志重建一致。无新物理或优化更新用于此审查。

|方法|partial75 checkpoint steps|保留的75新增更新|最后PROGRESS超出checkpoint|checkpoint SHA256|
|---|---:|---:|---:|---|
|impedance|3112148|23000|966|918a0a0671e35194d45de374c96d53a9ff2273866302656b5ffaea9db65d5c89|
|admittance|3113750|24000|67|4a8eb302871e459500d87a27f29ff71e716b3663601524a935332242b0f860f3|
|vmc|3114750|24000|249|085bb05679e31a317841f901e8b358e1cc032a3f79154fc4b6005f901d84a7a1|

这些partial checkpoint没有MuJoCo中途状态。恢复保留全部已落盘learner/optimizer/RNG/replay/masks/history，启动30个新的物理回合作为独立完整76；不是补齐75、不是逐物理子步无缝续接。旧轨迹、未落盘进度和失败/中断记录不删除，不伪造terminal，不回退到完整74。

三路CHECK_ONLY完整learner/replay及下一65536采样精确，原科学参数与恢复边界共9项错误配置/方法协议拒绝每路通过。恢复driver绑定准确partial checkpoint/原75登记/全部依赖hash；原训练器只增加3处恢复元数据与初始状态审查调用，逆变换逐字等于原注册训练源码。原完整边界验证被独立、显式、严格的partial75边界验证替代，未伪称原完整边界验证通过。实际GPU启动INITIAL_STATE_REVIEW三路全state精确，首批新增checkpoint及真实物理映射也已审查：

- impedance 实际新增1000，旧回放/完整历史保留，reward重建最大误差0.0，30模型/30sampler/CPU affinity核验。
- admittance 实际新增1000，旧回放/完整历史保留，reward重建最大误差0.0，30模型/30sampler/CPU affinity核验。
- vmc 实际新增2000，旧回放/完整历史保留，reward重建最大误差0.0，30模型/30sampler/CPU affinity核验。

DECISION_RECOVERY76绑定12项证据，SHA `4e87b3eeda51fb4588e3e484327bd825ac0cd37acdc3d2c90f9042e258f99409`。仅一轮76、无自动77。原30条件×55秒/最多41250新增、4m append/markers23与47、terminal128、batch65536、UTD1、LR/masks/reward/物理/gates和历史目标配对归约全部保持。当前steps 3118043/3119533/3120901，各30sampler，无FAILURE。

|任务|PID / start ticks|
|---|---|
|76 impedance|360532 / 44757345|
|76 admittance|360533 / 44757345|
|76 vmc|360534 / 44757346|
|loss76|436146 / 44768306|
|window76_78|436148 / 44768306|
|archive/health|360535 / 44757346|

76归档/完整回放reward审查/health自动监控已部署；完整loss及独立保存值算术自动审查已部署。完整49–74历史继续保留，75明确缺完整reward，新增76；74→76配对明确跨越partial75额外训练曝光，非原连续周期替代。全标签/终端后续与实际全轮图仍需审查。

原74–76 PLAN d8c243d9原件不变，因75中断明确无法评定，不重启原541941等待器或把部分结果塞入窗口。新的`runs/parameter_recovery76_78_reward_stability_20261029_v1/PLAN.json` SHA `57b3d6be84b8b384922a35879ddfd5cd1c6e7a6b71b35ca5652c2ddfc8cd4e85`，在76启动前登记76/77/78三个新的完整周期，保留5%/近零1/seed2026102855/5000bootstrap/anchor55和全部历史窗口/失败结论；只是中断后前瞻窗口，不按76结果选端点。新等待器已启动，无自动训练/停止。近零保护不是推离零的新目标。

旧canonical76 prepare/原76loss静态工具、原75完成观察/决定工具及旧75标签/终端/74–76等待全部不再适用，路径清单见`runtime/parameter75_interruption_recovery_20261029_v1/SUPERSEDED_PREPARATIONS.json`。保留旧源和hash，仅新建恢复登记；不要运行旧DECISION76助手或另启动canonical76造成重复训练。03时段准备记录保留，未执行的旧保存脚本也不能现在强行执行。

开工及恢复时实际fetch/read远端main08437d86（查询瞬间ba81b92c随后前进）、baselinef6e8f8c，阅读非RL原108进度77/108及最新衔接记录；本地6bc2e423与并行非RL安全合并，两处日志冲突双方新增逐字保留，记录REMOTE_MERGE_REVIEW。未操作另一主机进程。当前保存源码基线be76bb15b004da016821f33c6becd0f7b9e5419f，遵循sii-research-sync，无子agent。

此前push诊断为GitHub HTTP401转入VSCode askpass等待；禁交互返回128无法读取HTTPS用户名，不能继续称纯网络故障。前轮本地提交及本次恢复保存须按实际push结果区分，不能假定已远端发布；不索取私钥/token。源码和小证据已保存本地Git/共享SSD，大数据未同步arm1。

共享SSD证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY75_PARTIAL_TO76_20261029_055014/SMALL_EVIDENCE.tar.gz`，102成员/141890字节，SHA `855ec9c5df886d49e673c49c4600979d0d8b0309a37307050df857d7f206de9a`，逐成员与Python AST核验。[收据](RL_RECOVERY75_PARTIAL_TO76_20261029_SAVE.json)。大partialcheckpoint/startup checkpoint/replay/raw均仍共享SSD，非HDD/arm1全备份；HDD最新入口已重写回读。

下一步保持当前76和guardv6，补齐76全标签/基于partial75的全2244终端诊断；待完整76全审/真实图后再决定有限77。新76–78窗口保持原门槛，原75中断始终保留。Goal active。

发布补充：恢复证据提交 a48d16cc、安全合并提交 359c6cebdfff466c103c21c907e560f86f22fd36 已保存在本地。重新 fetch/read main 9defd6a4（非RL77→79）与 baseline f6e8f8c，双方新增日志逐字保留。禁交互 push 返回128，缺GitHub HTTPS用户名认证；远端发布尚未完成。101项manifest均已与提交Git blob逐大小/SHA核验，SSD归档保持。


## 05:55UTC后续：partial75终端基准和完整76标签等待已部署

原76三learner、归档/health、完整loss及76–78等待身份持续保持；本次快照steps 3122627/3123989/3125869、每路30sampler，无训练失败。原75中断结论不变。新两个终端等待器与一个全标签等待器见 `docs/evidence/RL_RECOVERY76_TERMINAL_LABELS_20261029/runtime/parameter75_interruption_recovery_20261029_v1/FOLLOWUP_FINAL_SNAPSHOT.json`，均仅只读诊断，无新训练。

partial75仍只有2244个terminal，与完整74的indices/57维feature/reward/masks全部精确相同，但权重和全replay分母已发生变化。以实际恢复的partial75 checkpoint重新CPU前向五critic，权重/前向RNG保持；独立scalar SSE VMC=475.481157404010，admittance=2078.809356364851。保留原VMC五focus和A2752093；76完整后检查2244旧+30新增=2274、原两分母贡献及独立保存算术，完整图仍待实际生成与查看。不是完整75结果或收敛证明。

全标签工具明确比较完整74→恢复76，包含中途已保留partial75额外曝光，非连续完整周期。原180标签/90配对reward/模型/evaluator/物理0.2mm判据和Task-only变化检查保持，实际不完整76拒绝测试通过。等待完整归档与loss保存复核后自动运行交叉检查。

诊断准备期间首次VMC anchor读方法级`passed`键产生KeyError；方法收据本无该键。已保留首次源码/PLAN/日志，改成要求总审计passed且方法收据逐值完全相同，之后两路通过；无科学重启。全标签等待器初版使用了错误的loss失败文件名，身份核验后仅停止该诊断等待器并重启修正版，原LAUNCH/PLAN/source保留；三learner/guard未动。

GPU guardv6持续，排除最初2预热样本后301个样本各卡最低[75, 68, 66, 66]%，低于50次数[0, 0, 0, 0]；包含合成负载，科学完成后继续。当前系统重启仍会终止进程，未宣称重启自启。

后续证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY76_TERMINAL_LABELS_20261029/FOLLOWUP_EVIDENCE.tar.gz`，65成员/938013字节，SHA `5938fe7ca3e47c4063dc65d26a4030ddbe8ba11f72181ec8f86577987ff9f730`，逐成员与源码AST检查通过。大型产物仍SSD，非HDD/arm1全备份。GitHub缺HTTPS认证，恢复提交a48d16cc与合并359c6ceb已在本地，远端发布仍待；不影响训练。Goal active，尚无77训练，Direct34false。


后续最新：[恢复76早期loss、77仅恢复准备及连续观察](RL_RECOVERY76_PREFIX77_PREPARATION_20261029.md)。原76保持，77仅恢复等待，实际77训练未启动，GPU保载继续。


后续最新：[76连续观察与77完整loss/派发准备](RL_RECOVERY76_WAIT77_DEPLOY_20261029.md)。77训练未启动，原目标与GPU保载继续。


当前最新：[完整76审查与77实际接续](RL_RECOVERY76_COMPLETE77_RUNNING_20261029.md)。77启动审查通过，原76–78与GPU保载继续，Goal active。


更新：[77全标签与2274终端后续](RL_RECOVERY77_FOLLOWUPS_20261029.md)。各后续实际部署，原科学和GPU保底继续。


更新：[77前缀审查与78仅恢复准备](RL_RECOVERY77_PREFIX78_PREPARATION_20261029.md)。原77继续，78仅恢复等待已部署；无78训练。


更新：[77等待与78完整审查/派发准备](RL_RECOVERY77_WAIT78_DEPLOY_20261029.md)。原任务继续，后续入口已准备，无78训练。


更新：[完整77审查与78实际续训](RL_RECOVERY77_COMPLETE78_RUNNING_20261029.md)。两项基础设施失败已保留并修复，原78训练和GPU保活继续。
