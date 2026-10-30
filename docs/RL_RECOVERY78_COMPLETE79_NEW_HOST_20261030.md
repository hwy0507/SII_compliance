# 完整78结果、新主机79续训与Direct33中断恢复

2026-10-30T04:00:08.216108+00:00，**Goal active，尚未证明reward稳定且loss健康。第79轮三路已在当前主机实际续训；GPU保活科研结束后仍继续。** 原79准备文档中的“未启动”是历史状态，此文为最新入口。没有自动80/81，也不启动Direct34。

执行主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；参数训练/审查解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`，SERL解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/serl_env/bin/python`。源码基线 `f6252c9652062c22abbba9a539c462cc0727b409`。本轮实际远端fetch/read main `a798f53e6c30ed69bd2dc3ff81d6038726bdf496`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；main非RL新工作已安全合并，双方AGENTS/UPDATE_LOG原行保留（合并f6252c96）。非RL球撞诊断与另机待批准探针属于另一个任务，未改动/派发。无子agent。

## 完整78与原76–78窗口

78三路各30×55s、41250新增、无abort；旧回放全部字段与历史精确保持，新reward逐区间重算最大误差0，网络/optimizer有限。全loss/health、180保存标签和90配对reward、终端后续、五张实际图均已完成；本次复用这些已完成证据，没有重跑78训练或全审。

|方法|78总步数|reward均值|Task/Strict（分母30）|critic首→末1000均值|critic最大值|
|---|---:|---:|---|---|---:|
|阻抗|3235898|−0.5735477017123704|18/18|2.931915→2.540270|24.186956|
|导纳|3237500|−5.041427601121655|16/16|1.192993→1.208637|14.666273|
|VMC|3238500|−4.605158151062658|17/16|1.448537→1.290981|185.416763|

阻抗short0600 Strict/physical false→true，穿透.2169776→.1835818mm；导纳long0500 Task/Strict false→true，long0200仍成功；VMC标签不变，short0600 Strict失败保留。完整78阻抗actor仍有25.24→24.68漂移，VMC actor下降后反弹、末段critic块升高，不称健康收敛。

VMC全部旧77终端2304条SSE3813.2408028→1355.79952335，新30条加权贡献.304517187、旧条.061368976、合计.365886164；focus2423133误差4.672934→4.689178恶化。导纳旧条SSE2431.2679217→1395.60530138，新30贡献.002430701、旧条.063166281、合计.065596981；focus2752093误差25.833394→36.476726恶化。原focus/两分母保留，不把全回放终端SSE归因为实际训练minibatch尖峰。health终端数I2335/A2334/V2334，inbag MAE .276515/.204376/.235745；frozen-alpha Q界超出比例0/.000390625/.002490234仅描述诊断。

原76–78 PLAN SHA `57b3d6be84b8b384922a35879ddfd5cd1c6e7a6b71b35ca5652c2ddfc8cd4e85`、完整结果和独立已保存算术均保持：

- 阻抗reward −2.27565、−2.34273、−.57355，触发近零1保护，相对5%标准不可判定；端点delta1.702102，paired bootstrap95% CI[−.222112,5.393641]，11改善/19恶化。近零保护只是解释限制，不是调整reward远离零的理由。
- 导纳−6.83676、−6.82080、−5.04143，未通过5%；端点相对26.2600%，delta1.795336，CI[.009759,5.193364]。
- VMC−4.57333、−4.62246、−4.60516，通过reward5%标准；端点.6961%、相邻1.0743%/.3742%，端点delta CI[−.090094,.029347]。**loss健康仍未通过，因此不能称训练收敛。**

原partial75始终不完整，原74–76窗口不可评估；没有抹除或替换任何旧窗口结论。

## 第79轮实际续训

本次03:34UTC发现容器更换，旧科学与guard进程均消失，GPU四卡0%。旧`/tmp`仍在不代表进程存活。旧主机已经完成78和79仅恢复检查，本机重新执行三路仅恢复：完整learner/optimizer/RNG/replay及下一65536采样精确，9拒绝项每路通过，结果除时间外与原检查一致。退出码未直接观察，记录按进程退出与完整收据核验，不虚构exit0。

`runtime/recovery79_completion_preparation_20261029_v1/DECISION79.json`绑定完整78、原76–78、五图及新明确CONTINUATION_REASON。只登记额外一轮79，以检查持续loss问题与新终端适应，不承诺收敛。随后真实启动三路trainer、startup、archive/health及全loss等待器。实际startup逐旧replay/history/优化器参数/30模型/30sampler/动作reward映射通过，reward误差0：阻抗新增1000、导纳1000、VMC2000。

当前快照steps `{'impedance': 3251451, 'admittance': 3253055, 'vmc': 3254465}`。运行入口 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_partial75_recovery_cycle79_20261029_v1`，真实PID/start在LAUNCH.json；不得重复启动。4m append、历史markers23/47、30×55s/最多41250新增、terminal128、batch65536/UTD1及原LR/reward/masks/physics/gates保持。

全79 loss/health、标签和两路终端后续均已派发并核验source/输入hash及真实进程身份。V/A锚定完整78全部2334终端，SSE8084.666547839108/1449.305194656441，复用完整78已审Q和精确features、没有新增forward；预期79后2364终端。完整78原focus与两分母保持。

79–81新窗口在79启动前登记（`runs/parameter_recovery79_81_reward_stability_20261030_v1`），仍5%/近零1/bootstrap5000/seed2026102855/anchor55；数值常量对照确认只改周期。原76–78结果保留。80/81须后续完整科学证据决定，窗口等待器14400s不派发训练，到期不重启科学。

79前5000日志原字节/步号连续/全数值有限/独立算术及六栏图实际查看通过。I/A/V critic首→末1000为2.576078→2.464755、1.196336→1.217126、1.151667→1.017293，最大18.152563/4.153562/18.067972。I/V重复尖峰保留，短前缀不能替代完整loss/终端和reward稳定结论。连续5样本/120.016秒观察8个原身份live或有完整终态收据，三路步数单调增加，无科学重启；观察器已自然结束。

## Direct33冻结评测恢复

原两个分片各完整14/15，共28完整。最后两个active_long_train_0671/0900中断在约17.04s，原raw/journal/结果hash和额外877条动作曝光保留（不计入30完整回合分母）。旧进程最终内存状态无法取回，不能补造POLICY_UNCHANGED。固定33 checkpoint SHA `783eaa7f7b03226915539e41cce313a5faeb4d49a15ae25626bb9762a9f47849`、原动作seed2026102626/独立噪声/每回合reset、原703依赖和物理/evaluator保持。

初次新host尝试`serl_take33_frozen_remaining2_20261030_v1`在加载前失败：漏设CUDA_VISIBLE_DEVICES=0导致SERL四卡可见；独立动作复核命令误改taskset参数。均0新物理，原日志/收据保留。修正环境与命令索引后，`...remaining2_20261030_v2`只补两缺失条件，未重跑28。两新回合已完成，最终完整learner/replay/history不变，0优化/0replay写；原930隔离pending保持。

原28回合全部38500保存动作由冻结33和原case RNG精确复现，np.array_equal误差0，复核自身learner/replay不变。它验证保存动作来源，**不能恢复旧进程丢失的最终内存不变证明**。组合审查首版又因read helper对str路径未转换Path失败，发生在逐回合审查前；只读v3修正接受Path/str并测试，原失败保留，未重启物理。最终审查目录 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_take33_frozen_combined_review_20261030_v3`，物理补跑目录 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_take33_frozen_remaining2_20261030_v2`。

全30合并审查和29→33描述性比较已完成，保存JSON/CSV与独立算术核验。新33 Task **0/30**、Strict **0/30**、full horizon 30/30、机器违规0/30，物理审查33000000子步。原28逐动作精确复现，新2全状态不变；`formal_state_unchanged=False`与`original_final_inmemory_state_unavailable=True`明确保留。

|冻结checkpoint|Task/Strict|平均回合峰矩Nm|最大关节力矩Nm|接触时长s|接触内舒适比例|
|---|---|---:|---:|---:|---:|
|29|0/0|40.320816|43.542727|0.000000|NA|
|33|0/0|39.599679|40.344833|0.000000|NA|

全部30失败与接触分母保留；这是单训练seed、单动作seed、训练条件的描述性比较。没有选择最终SPT参考、没有完成指定ESN比较，也不构成独立动力学重积分或泛化证明。

## GPU与持久交接

本机guardv7位于`/tmp/sii_gpu_util_guard_20261030_v7`，supervisor97370与四worker身份/CPU4–6已核。采用原v6控制逻辑，只将亲和52–54调整为4–6，target70%、自适应duty.7–.9；合成矩阵负载不是科研吞吐，所有科学任务完成后仍保持运行。

v7至快照共298个5秒样本，首次全卡≥50出现在第3个样本、约10.205s；全程最低[0, 0, 0, 0]%，初始预热低谷如实保留。首次达标后最低[75, 68, 67, 69]%，低于50次数[0, 0, 0, 0]；最后[80, 94, 92, 96]%。这不是重启自启服务，停机期间不可能继续GPU负载。

旧v6全部2788样本保留；预热后仍出现GPU0一次31%、GPU2两次33/44%，不是持续达标。此前将guard线程迁至CPU4–6的PLAN/APPLIED_REVIEW保留；CPU争用只是原因假说。容器停机与恢复空档不隐去。

小证据归档 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY78_COMPLETE79_NEW_HOST_20261030/SMALL_EVIDENCE.tar.gz`，1079成员/16592505字节，SHA `9ea3de2663969257f63a17e196a97249cc8d5a780d7d5e172f72a5908f56a161`；逐成员字节/hash与Python AST核验。仓库证据`docs/evidence/RL_RECOVERY78_COMPLETE79_NEW_HOST_20261030/MANIFEST.json`含源路径和snapshot hash，日志是快照，大checkpoint/replay/raw仍共享SSD，**不是HDD或arm1完整备份**。收据[RL_RECOVERY78_COMPLETE79_NEW_HOST_20261030_SAVE.json](RL_RECOVERY78_COMPLETE79_NEW_HOST_20261030_SAVE.json)。HDD既有LATEST指针原位等长更新，避免已满配额新增分配。GitHub发布依最终push收据，已有HTTPS认证缺失；本地commit不冒充已发布。

接续顺序：核当前进程与新终态，再收齐79全loss/health/标签/2364终端及实际图，审查79科学结果后决定有限80；保留79–81前瞻窗口和所有历史失败。Direct33结果/状态缺失限制和指定ESN/完整最终比较仍须随报告保留，不能将GPU占用或单窗口平稳当Goal完成。

保存补充：首次写HDD指针前等长检查发现新文案过长而拒绝（未写HDD），随后只缩短指针摘要，原位等长写入并回读通过；没有重跑文档生成器或科学。
