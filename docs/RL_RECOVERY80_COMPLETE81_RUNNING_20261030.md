# 完整第80轮审查与第81轮实际续训

2026-10-30T06:03:24.183226+00:00。Goal active。第80轮完整审查和第81轮精确恢复通过，已明确登记并实际启动一个有限81；当前steps `{'impedance': 3321695, 'admittance': 3323993, 'vmc': 3325157}`。没有自动82或Direct34。科学运行及GPU合成保载继续。

执行主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`；全部大checkpoint/replay/raw位于共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。HDD仓库为该SSD checkout的入口；不是HDD或arm1完整备份。开工延续main b5460e16，实时fetch/read main450dcce3、baselinef6e8f8c，安全快进保留另一主机非RL fixed27的9/27结果（MLP棍推1/3 Strict），不将其替代本RL/指定ESN比较。

## 完整80结果及诊断

|方法|steps|新增|平均reward|Task/Strict（30）|完整55s|
|---|---:|---:|---:|---|---:|
|阻抗|3317698|41250|−2.3904375104|18/17|30|
|导纳|3320000|41250|−8.4918512704|14/14|30|
|VMC|3321000|41250|−4.5887559705|17/16|30|

三路无安全中止，全部旧回放字段精确保留，41250新reward由冻结实现/interval日志重算误差0，网络和optimizer有限；健康度forward前后网络不变。不是独立全物理子步重建，也不是冻结策略评测。180条保存rollout标签及90对reward独立复算通过。

完整loss及实际六栏图：阻抗critic首/末1000均值2.714394→2.674734、max26.822237，反复尖峰和actor下降；导纳1.330159→1.125426、max10.130503，尖峰减弱但actor漂移；VMC0.978321→1.277092、max74.120689，末段尖峰和actor漂移。不能称健康收敛。阻抗max在step3312236、short0600完成3312159之后77步；VMCmax3320045、short0600完成3318759之后1286步。未记录minibatch身份，时序接近不能证明失败terminal造成尖峰。只读检查一次误用episode的step字段，已改用真实total_steps并保留错误说明。

I/V short0600仍Task成功而Strict退化，穿透分别0.232516/0.221289mm，原0.2mm判据和失败惩罚不变。导纳long0900改善至Task/Strict成功，但short0600 Task由真变假、physical由假变真，Strict仍假，不能只报改善。已知79阻抗long0000安全中止保持：27s/675动作/global97.689118mm/失败惩罚；80同条件55s/1375动作、完成52.2s、Task/Strict/physical真，global0.170378mm。模型/evaluator相同，训练策略变化；此事后已知案例对照不证明根因修复、泛化或79峰值独立重建。

健康度图已实际查看。I/A/V sampled Q global上界36.116820/31.888751/33.035671；超界比例0/0.0292969%/0.1953125%。终端mask内MAE0.299866/0.209845/0.231896，mask外3.483180/2.295938/1.872446。mask外未参与对应critic训练，应分栏解释，不能加零误差门槛。

V/A终端跟踪完整保留2364旧行+30新行、原focus及新旧两分母，forward和RNG不变，保存标量独立复算、两散点图实际查看。V旧SSE3410.810922→2329.821680，旧贡献0.152400→0.102793（沿旧分母0.104084），新30贡献0.142613、全0.245407；部分focus恶化，旧总体改善不等于健康。A旧SSE5503.511132→1505.663480，旧贡献0.245985→0.066430（旧分母0.067269），新30贡献0.001459、全0.067888；原focus5.730751→2.912095。

保存的全部30新terminal与episode逐索引核对：VMC short0600失败行的masked SSE3054.377630、贡献0.134723，占新增30贡献约94.47%；其后short0100/short0300贡献0.004332/0.001505。此为完整80末checkpoint上的误差分解，不是训练minibatch归因，也不能据此证明74.12 loss尖峰原因。A新30最大贡献为long0500的0.000335。完整30行保存在NEW80_TERMINAL_CASE_REVIEW.json。

## 第81轮实际续接

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/recovery81_completion_preparation_20261030_v1/DECISION81.json`及`CONTINUATION_REASON.txt`绑定完整80/四实际图/精确恢复、原76–78窗口和版本2 DECISION80失败历史。三路full learner/replay/next65536精确恢复和每路9负例拒绝通过；actual startup独立核验通过。原4m append-only、23/47历史marker、terminal128/batch65536/UTD1、LR/reward/masks/physics/filter/gates和30条件×最多55s/41250新增全部保持。原partial75保留，不补造完整75。

运行 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_partial75_recovery_cycle81_20261029_v1`；每路30 sampler，full archive/replay/health/loss/labels/两终端后续已部署。完整80的2394终端锚点核验后等待81预计2424行。79–81前瞻窗口保持原PLAN及seed/bootstrap5000/nearzero1/relative5%；等待身份收据见本包，不自动训练82。原76–78 I近零不可判、A5%失败、V仅reward通过而loss未证；原74–76不完整不可判，不能换窗口或奖励掩盖失败。

Direct33数值阶段已有接受、冻结全30 Task/Strict0/0，旧28最终内存不变证明缺失继续披露，不启动Direct34。指定ESN及最终完整冻结比较仍待。

## 持续运行与保存

80 completion watcher自然结束、55样本/1620.682s，所有原训练和审查终态核验；81实际启动与连续观察收据在本包。GPU上次保存后430个样本，最低[76, 60, 65, 68]%，低于50次数[0, 0, 0, 0]，最后[78, 69, 69, 95]%。包含合成保载，不能当科学吞吐；按用户要求科研完成后仍运行。历史v6低谷及v7预热0保留，guardv7不是重启自启服务。

SSD小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY80_COMPLETE81_RUNNING_20261030/SMALL_EVIDENCE.tar.gz`，303成员/4359072字节，SHA256 `34a808baf2ab6600d19da4b536425a3cc639ac044a8216188d169b99ec0b3dd4`，逐成员字节/hash/源码AST核验。保存收据 `RL_RECOVERY80_COMPLETE81_RUNNING_20261030_SAVE.json`。依赖既有79完整包及80/81准备包；大产物继续共享SSD。HDD既有254字节LATEST原位更新回读。实际commit/push结果另记同归档目录PUBLICATION.json，不能将保存时快照冒充发布后状态。

接续先检查原81及后续PID/start/FINISHED/FAILURE和guard采样年龄，不重复派发；完成81后审查完整窗口、loss、健康度、终端和冻结验证需求，再登记下一有限步骤。Goal保持active。
