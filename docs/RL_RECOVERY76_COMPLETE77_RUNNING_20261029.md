# 完整恢复76审查与有限77实际接续

2026-10-29T06:59:54.796169+00:00，Goal active。恢复76三路完整结束并全审，准确恢复77已实际运行且startup通过。当前77 steps 3160279/3161595/3163135，各30sampler，无训练失败。整体reward稳定和loss健康仍未证明；Direct33原训练条件数值结论及Task/Strict0/0保持，不启动34。

共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，主机`rltest-1025--a6ed2ff39b3c-nvfdwjhzzw`，Python env/bin/python。全部partial75已保存学习/replay状态保留，完整cycle历史仍缺75；76是重置物理环境后的新完整周期，77从完整76精确接续。原30条件×55秒/最多41250新增、4m append/markers23与47、terminal128、batch65536、UTD1、LR/masks/reward/物理/gates均不变。

|方法|76累计steps|reward均值|Task/Strict|critic首→末1000|max critic|actor首→末1000|
|---|---:|---:|---|---|---:|---|
|impedance|3153398|-2.275649963|18/17|2.827437724→2.932798522|43.798500061|25.765414024→25.713243219|
|admittance|3155000|-6.836763353|15/15|1.177549279→1.209828281|7.459600925|-9.214740112→-9.181080909|
|vmc|3156000|-4.573325316|17/16|0.707768058→0.831653571|22.249963760|-13.034758131→-12.797851939|

三路各30完整55秒、41250新增、无abort；旧回放所有字段/history保持，全部新增reward由冻结物理间隔日志重建最大误差0，network/optimizer有限，marker和原学习参数保持。完整loss所有日志及保存算术、90reward配对和全180标签核验通过。有限数值不等于健康loss。

全轮loss与health图已实际查看：I critic持续尖峰并有尾段burst，actor先升后降；A critic约1.2且稀疏尖峰，actor尾段略升；V critic局部/尾段burst、actor明显上移。health混合mask终端MAE和in-bag/out-of-bag分栏保留，不能把heldout误差当所有拟合失败或新增零误差门槛。

74→76标签比较跨越保留的partial75额外曝光：I无标签变化；A long0200真→假，long0500/short0900假→真，short0600恢复Strict（穿透.204262→.189901mm），总体14/13→15/15；V short0600失去Strict（.178927→.213513mm），17/17→17/16。全部改善和退化保留，非随机性/梯度因果证明。

终端基准取真实partial75权重，固定2244旧样本+76新增30；不是拿完整74权重替代。两路所有保存数组/独立scalar算术与实际散点图已审：

- vmc 旧2244 SSE 475.481157404→1774.984034503，原分母贡献0.022372861→新分母0.082449473，after仍用旧分母0.083543482；新30贡献0.097963515，全终端0.180412988。
- admittance 旧2244 SSE 2078.809356365→2778.879842723，原分母贡献0.097828215→新分母0.129015203，after仍用旧分母0.130713569；新30贡献0.001705373，全终端0.130720576。

V原2050526 SSE1.4808→48.8337、2423133 2.8373→15.1305退化，2423122 8.3721→2.3999改善；A原2752093 43.6609→31.9523改善但全群体退化。不只挑好focus；原focus/两分母不变。V新30贡献较大，仍不能断言历史minibatch或梯度因果。

DECISION77绑定96项准确证据，SHA `529d56148ab333eb5208710858f7d248622f1187bb9c072a3d72d2704bba9aad`；理由原件`runtime/recovery77_completion_preparation_20261029_v1/CONTINUATION_REASON.txt`。未证明收敛，因此接续一轮同科学配置77并采集原前瞻76–78窗口，不保证更多训练必然改善。旧53–55及后续全部失败窗口保留，原74–76因75中断无法评定；新76–78 PLAN SHA57b3d6be原件不变、原5%/近零1/seed2026102855/5000/anchor55保持。近零保护不用于推离零。

准确77 CHECK_ONLY三路全learner/optimizer/RNG/replay和next65536一致、各9拒绝通过；77协议新增显式post_interruption_continuation绑定完整76，保留原initial恢复历史与旧stage字段，明确不伪造完整75。三路实际GPU INITIAL_STATE精确；首批实际checkpoint旧回放/历史、原优化器/物理映射/奖励/30模型/30sampler/CPU affinity审查通过：

- impedance 新增1000，旧3153398行全部字段保持，reward最大误差0.0。
- admittance 新增1000，旧3155000行全部字段保持，reward最大误差0.0。
- vmc 新增2000，旧3156000行全部字段保持，reward最大误差0.0。

|当前任务|PID / start ticks|
|---|---|
|77 impedance|3187668 / 45169092|
|77 admittance|3187669 / 45169092|
|77 vmc|3187670 / 45169092|
|77 archive/health|3187671 / 45169092|
|parameter_recovery77_loss_20261029_v1|3187674 / 45169097|
|parameter_recovery76_78_reward_stability_20261029_v1|436148 / 44768306|

77完整loss/独立保存算术自动等待已部署，保留49–74/76历史、显式拒绝75，配对76→77；77归档/replay/reward/health和startup均绑定源码。77完整标签、基于完整76的全2274终端锚点后续仍需准备，实际77完整结果未有；无自动78。

从前次保存起280个guard样本最低[75, 67, 62, 63]%，低于50次数[0, 0, 0, 0]。76结束到77启动之间是CPU审查/恢复准备，GPU当时由合成保底占用，不能称科学吞吐持续；原v6进程保持，科学全部完成后仍保载。早前容器空档与预热样本保留，非重启自启服务。

开工实际fetch/read main6492ab17、baselinef6e8f8c，发布前又读mainc1e2bf02（另一主机非RL86→89）及交接，双方新增日志安全合并原字节保留；未操作非RL进程，无子agent。源码基线22c87e3b6776eea87892023fd28cae49058c0d50。本轮此前push128缺HTTPS认证，不能称远端已发布；待最终实际结果记录。

共享SSD证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY76_COMPLETE77_RUNNING_20261029/SMALL_EVIDENCE.tar.gz`，317成员/2677677字节，SHA `9fe6df28b429340ca077817df797d3de6ad8f545284dcd1a73e508fab042eed0`，逐成员/AST核验。[收据](RL_RECOVERY76_COMPLETE77_RUNNING_20261029_SAVE.json)。大checkpoint/replay/raw仍SSD，非HDD/arm1全备份；现有HDD最新入口仍指已补本报告链接的主恢复文档。

下一步保持原77/76–78/guard，补77全标签与全2274终端后续；等完整77全审/实际图后再决定78，按原reward/loss目标判断，Goal active。
