# 完整恢复77审查与78实际续训

2026-10-29T08:10:01.001643+00:00，Goal active。第77轮科学正常完成，完整审查和两项基础设施故障修复已核验；第78轮三路已实际启动，启动审查通过，当前steps {'impedance': 3198395, 'admittance': 3199837, 'vmc': 3201243}。本报告取代[原77等待/78准备状态](RL_RECOVERY77_WAIT78_DEPLOY_20261029.md)作为当前状态入口，历史失败均保留。

执行主机 `rltest-1025--a6ed2ff39b3c-nvfdwjhzzw`，共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。科学配置仍30条件×55秒、每路每轮41250新增、4m追加回放、历史markers23/47、terminal128、batch65536、UTD1、原学习率/reward/masks/物理/gates。没有Direct34、没有自动79。

## 完整77

|方法|steps|平均reward|Task/Strict（30）|critic首→末1000|critic最大|
|---|---:|---:|---|---|---:|
|阻抗|3194648|-2.342727843|18/17|3.194033→2.548128|33.366371|
|导纳|3196250|-6.820801913|15/15|1.200749→1.180500|67.836517|
|VMC|3197250|-4.622457555|17/16|0.915801→0.848468|44.592030|

三路均30完整55秒、41250新增、无abort；全部旧replay/history保持，新reward全量重算最大误差0，网络/optimizer有限。不能据此判健康loss或收敛：尖峰和actor漂移仍在，完整loss、health及V/A两张终端图均已实际查看并保存收据。导纳总成功数不变但long0200恢复、long0500退化；全部180标签/90reward对独立复核，I/V既有物理/Strict失败保留。I long0000 reward下降2.596544而标签未变。

V/A全部2274旧终端SSE分别3883.440215→1997.718105、2815.605065→2352.728519；并非每条改善，VMC两原focus退化保留。新30贡献分别.08326542724914057/.0036010946824885973，原两分母、完整总体和原focus均保留，无因果归因。health中超过当前冻结alpha上界的sampleQ份额I/A/V为0/.000732421875/.0010742187732830644，诊断不新增收敛门槛。

## 修复与准确恢复

原归档监视器在完整77 checkpoint/reward/replay审查成功后，因缺`diagnose_published_value_bound_20261025`退出。按原76版本逐字补齐helper（SHA2a5b04c7），仅继续缺失health，未重跑科学或完整review。原`ARCHIVE_REVIEW_FAILURE.json`、monitor.log和依赖等待器失败均保留，`runtime/recovery77_health_dependency_fix_20261029_v1/HEALTH_RECOVERY_REVIEW.json`串联修复后完成收据；未来78依赖也已补齐。

后续恢复检查首次失败，原因是补跑环境设置空`CUDA_VISIBLE_DEVICES`，导致`state_dict`看不到已存CUDA RNG。CPU learner的设备可见/隐藏对照只发现`cuda_rng`差异；修正环境后，三路原driver未改，全learner/optimizer/RNG/replay及next65536准确检查和每路9拒绝均通过。原失败log/JSON、初次非零exitcodes均保留于`runtime/recovery78_state_check_diagnosis_20261029_v1`证据链；无训练重启，无绕过状态相等校验。

## 当前78与后续

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/recovery78_completion_preparation_20261029_v1/DECISION78.json`绑定完整77全部审查/实际图、准确恢复、历史证据、两次故障修复收据及有限理由。原75缺完整终态、不补造数据，旧74–76窗口unassessable；原前瞻76–78 PLAN SHA57b3d6be84b8b384922a35879ddfd5cd1c6e7a6b71b35ca5652c2ddfc8cd4e85及5%/nearzero1/seed2026102855/5000bootstrap/anchor55保持。近零保护不是把reward推离零的目标。

实际训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_partial75_recovery_cycle78_20261029_v1`，三learner身份与30sampler、完整state初始核验及startup首批映射/原replay/optimizer/新reward核验通过，见startup/REVIEW.json及本证据SAVE_SNAPSHOT。完整78归档/health、全loss、标签和V/A终端等待器已部署，原76–78窗口保持原PID。新的终端锚点从完整77已审Q与准确checkpoint提取全2304条，无新forward，原focus及两分母保留；78预计全2334条，不冒充旧2274。标签入口对真实未完成78拒绝通过。

Direct33已接受的训练条件数值结论保持，Task/Strict0/0，未启动Direct34；旧冻结29不能认证最新33，最终冻结策略和指定ESN比较仍待，不缩小原Goal。第78轮尚在进行，不能预告reward稳定或loss健康。

## GPU与保存

从上次保存起guard 376个5秒间隔样本，四卡最低[75, 67, 67, 66]%，低于50次数[0, 0, 0, 0]；最后利用率[80, 95, 93, 94]%。保活原supervisor78710/四worker身份保持，科研全部完成后仍继续。合成负载不计科学吞吐；不能用本窗口掩盖此前容器停机及v6最初两个预热0样本，也不是系统重启自启服务。

实际fetch/read远端main b1deda6593c6b4bc76a76b89e30b5a6fc4998178、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，另一主机非RL99/108新增保留，没有操作其进程，无子agent。源基线 `e5fa7dab5c5b49e204051287531f04c2b29ba952`；发布以最终push收据为准，既有HTTPS认证缺失。

本轮共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY77_COMPLETE78_RUNNING_20261029/SMALL_EVIDENCE.tar.gz`，383成员/3205500字节，SHA `e03336255cce8a9c6658707fe49c0971cd8bcb334e64d1a80fd535c157b58702`，逐成员原字节和Python AST核验；[归档收据](RL_RECOVERY77_COMPLETE78_RUNNING_20261029_SAVE.json)。完整checkpoint/replay/轨迹仍共享SSD，非HDD或arm1全量备份；HDD现有LATEST入口指向主恢复文档。

下一步持续观察原78及GPU，完成78全审并实际查看图，读取原76–78统计，按原reward稳定与loss健康要求判定。观察器超时或审计失败不重启科学；如需修复保留失败链。不要重复运行本轮launcher，不启动自动79。
