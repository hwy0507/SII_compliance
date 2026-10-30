# 完整79、安全中止审查与有限80续训

2026-10-30T04:56:18.482540+00:00。**Goal active，三路参数RL第80轮已真实续训；当前steps {'impedance': 3280700, 'admittance': 3282971, 'vmc': 3284195}，准确恢复/实际startup通过。未证明reward平稳且loss健康；无自动81，无Direct34。GPU科研结束后仍合成保载。**

执行主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。按sii-research-sync流程开工真实fetch/read main `cd8bbf33c44dfb497f1fb7551451c89312b3ae28`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；保存前main前进至`03365fd2e91f02ff8a2b4a9087fa9955e930c646`，只改共享日志、非RL进度27→55/75，已安全快进并读其日志，非RL源码保持。无子agent，未代替另一主机派发teacher/学生工作。

## 完整79结果与限制

|方法|累计steps|实际新增|平均reward|Task/Strict|完整55s|critic首→尾1000|critic最大|
|---|---:|---:|---:|---:|---:|---:|---:|
|impedance|3276448|40550|-2.511716602|17/17|29/30|2.576078 → 2.723751|29.908985|
|admittance|3278750|41250|-10.141244912|14/13|30/30|1.196336 → 1.409760|31.223160|
|vmc|3279750|41250|-2.874607014|17/17|30/30|1.151667 → 0.907557|27.185583|

三路完整30条件已结束，旧回放全部字段/history保持，所有新增reward重建误差0、done与回放精确匹配，网络/optimizer有限；完整loss独立算术、全部180标签/90reward配对、health、两路终端全锚点审查完成。四张原完整图及一张新几何图已实际查看，收据逐图hash绑定。有限数值不等于loss健康。

I反复critic尖峰且actor24.673951→24.081640持续漂移；A后段critic尖峰簇且actor−9.031459→−8.871949，Task/Strict16/16→14/13；V critic均值下降但仍尖峰/actor漂移，Task/Strict17/16→17/17。A的short0600 Strict退化、short0900及long0500任务退化，I long0000安全中止，V short0600 Strict恢复均保留。A/V采样Q超过当前alpha软上界比例分别0.00078125/0.00190430，不能据此声称校准完成。

完整旧2334终端固定观测/action/reward/mask精确：V SSE8084.666548→3396.003020改善但仍有大残差，各focus有升有降；A SSE1449.305195→2084.328691退化，原focus36.476726→5.730751改善不能替代总体。旧新两个回放分母保留，A新30终端贡献0.152839883，全部贡献0.245985272；V全部贡献0.152400481。独立saved-values审查通过，0新物理/更新。

原76–78 I近零1保护不可判、A不满足5%、V reward满足但loss健康未证保持；原75仍不完整，原74–76不可判。79–81前瞻PLAN SHA `5cf5efb87a63b432091276c3b96a3b16126c2ab891a2e195b6c857e93cf110a0`不变，5%/nearzero1/bootstrap5000/seed2026102855/anchor55保持；不能以近零保护为改变reward方向的理由，不能抹去短回合。

## 阻抗79真实安全失败

`runs/impedance_recovery79_abort_review_20261030_v1/FINAL_REVIEW.json`。long0000在27.0000000003s/675动作/540000物理子步终止，原reason `global_penetration_exceeded_2mm`，Task/Strict/physical_valid均false，阶段retreat。记录全子步global峰值97.689118mm，最深对为corner_top与target_object；机器人外部穿透峰值0.072362mm。78同MJB/执行evaluator该条件55s成功。79物块最后保存位置与广义速度出现跳变。

原安全检查在actor间隔结束读取累计global峰值，已按原2mm终止；未提高安全阈值。25Hz保存帧各675个，78/79几何重建共1350次mj_forward、0次mj_step：最大保存帧穿透0.053973/0.066135mm。训练没有保存全部子步状态，**该几何检查不能重建或否定97.689mm记录峰值，根因未确定，不能称为无害尖峰/全局被动性通过**。实际evaluator.log非JSON行无匹配warning记录，但这也不能证明积分全程无警告。

675行shield递推全部误差0、6750伺服记录检查通过，能量最小0.762900626；仅核记录指令，不替代物理速度/力矩审计。终端done恰一次，step3264119，终端transition reward−38.100159404；整条reward−40.529577442，terminal−25及failure_tail−9.940790457保持。全cycle新增40550=29×1375+675，不虚构41250或55s，不重跑该失败，不删除其回放。

## 明确登记的80决定及启动

原`runtime/recovery80_completion_preparation_20261030_v1/decision80.py`因40550/29full/abort正确拒绝，`COMPLETE79_ABORT_REJECTION.json`保留，原源码不改。另建`runtime/recovery80_abort_aware_decision_20261030_v2`，在完整79及诊断之后登记PLAN和理由，仅针对**精确已审79 checkpoint及该唯一失败**允许一轮有限80，不允许任意失败通过。12个负例拒绝及三路真实正例、缺决定拒绝通过，绑定全部原证据、五图、准确80恢复与原窗口。版本2不等于原no-abort guard通过；不声称失败已修好。

续训依据是网络/optimizer有限、原reward/done和回放/精确恢复正确、记录shield/servo未见执行偏差，允许继续模拟学习以观察失败是否持续；根因仍待更细证据。原30条件、55s上限、最多41250新transition、4m append-only、markers23/47、terminal128、batch65536/UTD1、LR/masks/reward/物理/MJB/安全门槛均不改。

准备入口另发现旧`launch80.py`残留parent78和`resume_recovery78.py`引用。原错误源和拒绝保留，v2只修为parent79及真实`resume_recovery79.py`；以真实driver导入、三路注册/命令/hash/CPU可用性预检通过后启动。v2构建脚本一次括号SyntaxError在执行前失败，原件/失败收据保留后修复，没有科学重启。实际LAUNCH及INITIAL_STATE在`runs/parameter_partial75_recovery_cycle80_20261029_v1`，三路原数据完整，actual startup全部30sampler/模型/源/奖励映射通过。

完整80 archive/review/health/loss/79→80标签等待均已部署，两路新终端anchor各保留完整79全部2364，V/A SSE3410.810921813/5503.511132148，hash及独立标量复算通过；预计完整80各2394行。旧focus与两个分母保留。所有进程PID/start在LAUNCH收据，先核身份再接续；不得重复派发80。81须完整80证据后另决定。

## 连续观察、GPU与恢复入口

原79完成观察38样本/1110.270秒，三训练/归档/loss/labels/终端/仅恢复80全部完成。80启动后7样本/180.023秒、15个原身份保持live或核完整终态，保存行独立核验；steps {'impedance': 3277877, 'admittance': 3280191, 'vmc': 3281241}→{'impedance': 3280172, 'admittance': 3282465, 'vmc': 3283643}，观察器自然结束、科学不重启。

上次准备保存以来GPU465个5秒样本，最低[70, 62, 64, 64]%，低于50次数[0, 0, 0, 0]；最后[81, 96, 94, 93]%。负载包含合成保活，不能当科研吞吐。guardv7 supervisor97370/start570509460，四worker97399–97402/start570509475，CPU4–6，target70%、floor50%；科学全部完成仍运行。历史停机、v7预热0和v6的31/33/44低谷保留，不能保证每个瞬时无低谷；尚非重启自启服务。

Direct33数值阶段接受状态保持，冻结全30 Task/Strict0/0；旧28最终内存不变证明仍缺失，原中断877额外动作单列。不启动Direct34；指定ESN和最终冻结比较范围仍待，非RL另一主机进度不替代本任务。

SSD小证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY79_ABORT80_RUNNING_20261030/SMALL_EVIDENCE.tar.gz`，381成员/16250492字节，SHA `2991b5d54925dc05bfd4ffbd59ea0baf7b598d6e6f50906b7dab04ad6a912692`，全部成员字节/hash及Python AST核验。收据[RL_RECOVERY79_ABORT80_RUNNING_20261030_SAVE.json](RL_RECOVERY79_ABORT80_RUNNING_20261030_SAVE.json)。大checkpoint/回放/轨迹留原共享SSD，活动日志为快照，**非HDD/arm1全量备份**。HDD原254字节LATEST指针原位更新回读。GitHub发布以实际发布收据为准。

下一步继续原80科学进程，检查完整loss/health/labels/terminal与79–81等待器，按实际物理失败和loss趋势决定有限81；继续GPU保载。勿把本轮有限续训或保存成功写成收敛完成。
