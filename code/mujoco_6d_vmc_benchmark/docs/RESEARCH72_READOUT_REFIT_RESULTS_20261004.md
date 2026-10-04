# 固定本体交互读出：实际重训与开发登记

状态快照：2026-10-04 04:36 UTC。18模型拟合、独立实现审计和服务器归档已完成；
144条开发闭环已派发单队列，当时0/144完成。不是最终留出结果，不宣称ESN优势。

## 前瞻登记与数据

teacher09再采集于04:06:46UTC自然完成：40/40放置、25/40原strict。
训练32为32任务/20strict，验证8为8任务/5strict；旧对应40为36任务/24strict。
真实请求、过滤后action和实际执行量分别保留，公共过滤重放通过；拒绝的15条不进入正示范，仍保留并计成本。
新数据20训练＋5整身份验证，共34,375帧，所有六模仿学习家族共享，未使用开发/封存轨迹作标签。
验证strict从6/8降到5/8，合格验证示范柱接触0/5，不能称新数据全面更优；详见TEACHER_DATA_QUALITY。

04:20:58UTC在拟合前登记修订02，数据收据、工程parity、原三条RL队列实际持有租约均核验。
登记容量依据P90余量3.459小时，保留完整38×24最终矩阵与2小时报告预算；不是按学生结果追加搜索。
新ESN保持128固定储备池，增加128维固定特征 `h * tanh(G c)`，G不学习，当前本体字段不增加。
仅训练3,780个线性读出系数，无运行时teacher或神经混合。相同结构的无记忆、matched MLP/RNN均保留。
ESN/无记忆每seed12候选，四神经家族各一次4000更新，沿用先前整身份验证选择的学习率；3seed共18模型。
只有一个point-loss版本，不再新增gate/学习率/时序损失搜索。累计ESN60候选/seed、无记忆36，
ordinary+matched合并MLP/RNN各16，实际计算不相等，报告分别记账。
数据与结构同时改变，因此与旧队列的差值不是隔离的机制因果证据。

## 实际拟合与独立检查

本机airpig单线程/CPUQuota100%/MemoryMax3GiB/Swap0服务04:22:04→04:26:18自然完成，18/18 returncode0。
原execution保留本机路径；没有重训或重启稳定Spark作业。

- 3 ESN＋3无记忆的全部72个候选按seed重建输入、递归、时间尺度和固定交互投影，逐值一致；
  只读出可学习。每模型额外递归篡改/隐藏层内存负对照均被拒绝；不是稳定性或echo-state性质证明。
- 全18模型在公开训练首身份1375帧重放，24,750次原输入与扰动其他30字段的请求/状态精确一致，
  与exported replay最大误差0；输入只读和动作有界检查通过。仅覆盖该已知序列，不声称所有输入形式验证。
- 首固定矩阵审计的systemd命令漏了工作目录，未加载模型便退出；补全工作目录后通过，未发生拟合/物理。
- 服务器登记首次遇到JSON路径字符串传给Path-only哈希函数，未写出spec；修复路径规范化，保留原训练源码，
  六项既有数据/登记测试通过，真实18模型/source/metadata/lineage校验后成功登记。

全部18模型×相同8开发条件进入原50μs/55s公共环境；原候选仍参与原跨全部seed的选择规则，不筛掉离线误差差的模型。
服务`sii-r72-readout-refit-development-v1` PID2490149，子队列用全局四槽租约。输出路径直接是
`context_readout_refit_development_v1/`，最终选择器要求全部144条完成，不能静默省略。

## RL接续与成本

导纳301/VMC301实际保存的16,500步checkpoint各自保留父5,500条回放前缀逐值一致，
新增11,000条/8回合的观测、原始动作、终止和非末帧下一观测与真实执行记录相符，23,002更新计数与继承一致。
这是存档/数据继承审计，没有逐梯度重算，也没有独立重算奖励或终止帧下一观测，更不是最终策略成功。
两份审计0新动作/训练/物理，SHA与源/快照引用均保留。
q1在04:13一次性让槽工具运行之前已经自然拿到租约；真实工具events为空，未向研究进程发SIGSTOP/SIGCONT。
不把它描述为工具干预的成功；三个RL队列继续运行，原共同最终边界监护保留。

04:36:18成本快照：累计120拟合完成，RL106,418交互/102,858更新，旧context23/168、增强网络14/168，
新refit0/144。成本工具已将144条作为已登记工作计入，即使归档或派发尚未发生也不遗漏；未来预测optional=0避免再当假设新增。
余下开发理想24.328–25.475小时，最终912物理22.824–23.942小时，2小时报告后余量3.478–5.742小时。
仍不含额外等待/冷加载保证，最终P90最晚起点10月5日09:33UTC；需持续跟进，不能把正余量当完成。

## 服务器原件

主机`arm1@192.168.31.70`，根`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。

| 原件 | SHA256 / 核验 |
|---|---|
| `teacher_refinement_v1/demonstrations/training_data.npz` | `7bb2f7bad7555cc97ca9cc32d43040e91775ce05cdfd32d109a7afbeb1d7e0a0` |
| `REFIT_DATA_RECEIPT_20261004.json` | `1aea31681b1a4a2fb76b1c2a013bb6b26326b1ee4ee708028182602fb0297d02` |
| `AMENDMENT_02_CONTEXT_READOUT_REFIT.json` | `42c9a4cf59715cfec47b73a706d688b182da89e505cf10033a56da09a2e84493` |
| `local_context_readout_refit_archive_v1/` | 763文件完整内容/大小/模式核验；tar `07d887b4c98426a3a97441e0d1568a8020b2581b494e9b9268e2c2a9b987034b` |
| 上述目录`REFIT_FIXED_RESERVOIR_AUDIT.json` | `edd16bb1c22507304e12680841fa784788bd192e39957382bcb2a5f9c9bb6bc5` |
| 上述目录`REFIT_ACTOR_FIELDS_AUDIT.json` | `8b65c2e1842db3c6d964eebc4ff79728c24c7690f5cc3faf29d068b51a5ac34c` |
| `CONTEXT_READOUT_REFIT_DEVELOPMENT_SPECIFICATION.json` | `9240384b45cfcc7e18ead55d5cf58871ea4139d4b76893afccbd1a15c98b6e3d` |
| `refit_registration_source_v1/` | tar `3548cafc71d089215aac29a17caa13106b429eddf4770ee3d6576fe2035d91fc` |
| `refit_dispatch_source_v1/` | 三源核验；tar `ccbf38b89d0f15ba9410adeb8fff760e122fa7dcfd563e1b1153bbc1701f91f0` |
| `rl_replay_prefix_source_v1/` | 两源核验；tar `fd4cf8c6e74e65015a6a28884e1cd7554b464a3ae8b8478ac12a54261763f988` |
| `rl_replay_prefix_audit_v1/ADMITTANCE301.json` | `41822bdd3afb234903400c5a066db72baaf24d90dc4f73857eac80b4a510967e` |
| `rl_replay_prefix_audit_v1/VMC301.json` | `ea3255ce9b0da424898c6dc4a43079ec2137cee74d12c242c5d99e8d6a008f25` |
| `EXPOSURE_SNAPSHOT_20261004_0443.json` | `b0e228277200daa4ffbba6e691d70626459ab05269eb30184274b6b97db88b11` |
| `BUDGET_FORECAST_20261004_0443.json` | `4aa9989da5d734eb3fafe18d604bb6c0dea8833f601b6ae281a90d909b174ec8` |

文件名0443只是唯一标识，快照真实时间以JSON中的04:36:18UTC为准。
拟合源在上述归档`context_readout_refit_v1/source/`，实际物理公共执行源为
`/home/arm1/sii_shared/SII_compliance/source/8c1633e5b643b68c26008047c1fb5f4a1cf25010/code/mujoco_6d_vmc_benchmark/`，
没有改运行中runtime。关键JSON已按原字节放Git `docs/evidence/research72_20261003/`。
24最终条件仍封存；模型冻结、全部baseline闭环、最终物理/动作/状态审计、统计与媒体尚未完成。
