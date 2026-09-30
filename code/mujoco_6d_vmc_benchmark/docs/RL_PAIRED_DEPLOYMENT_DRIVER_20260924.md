# 18条配对部署driver：准备完成，未执行

`tools/run_paired_six_fixture_deployment_20260924.py`只消费已经通过最终模型、transition audit及动作回放审计的冻结plan。它不训练、不选模型、不生成新的评估参数；没有恢复或覆盖已有目录的选项。本文件补充执行说明，不改变`RL_PAIRED_SIX_FIXTURE_DEPLOYMENT_PROTOCOL_20260924.md`的协议hash。

启动前必须由主任务核实DGX全服物理worker：总上限4；默认本队列2，显式`--available-worker-slots`为已核可用槽位。本机driver不能据一个命令行数值自行证明全服空闲，所以心跳只可在主任务完成资源核查后启动。当前没有启动任何本队列进程。

示例命令仅展示接口，PLAN_JSON与PLAN_SHA256必须替换为实际已经审计冻结的文件和hash：

```bash
python tools/run_paired_six_fixture_deployment_20260924.py \
  --plan PLAN_JSON \
  --expected-plan-sha256 PLAN_SHA256 \
  --max-workers 2 \
  --available-worker-slots 2
```

输出根从plan的18个job路径唯一恢复，必须完全不存在。plan文件必须位于输出根之外。启动时再次检查全部输入、两份真实transition audit原日志/8192次SB3转换、动作回放全部输入hash、最终模型与normalizer、协议和源文件；将plan原文件与源文件副本写入新输出目录。每条job开始和结束再核模型/source/plan，整批结束再做深度核查。

prepare必须先把两分支训练manifest的全部163项source_hashes与部署ROOT逐项核对，再合并新增部署源码和driver，不能只冻结入口及metrics几个文件。该集合包含primitive scene、contact memory、workstation及src物理依赖；driver每job前后全量核验并归档。rollout自报六个核心源码集合/hash还必须与原fixture reference完全相同，不接受仅与当前本地文件自洽。

准备时只读核查发现当前本机ROOT有一个已存在的同名文件差异：`scripts/run_panel_classical_matrix_20260923.py`不等于训练proof的冻结hash，其余162项一致。本任务没有覆盖该文件或豁免检查。后续应在独立部署ROOT复制原训练只读快照，再只加入新部署文件；不得把当前混合源码直接当作完整训练快照。

唯一差异的冻结SHA256为`862965a719be0ffd71587dc5e08f8454d7ac450b3ba4a986167328d0f73b1532`，当前本机文件SHA256为`3d37b19e5e39f6428c5c5f6cf70f79a0d7a4abaf342dc8cdd725fd5622fc4b5a`。独立构建工具`tools/prepare_paired_deployment_snapshot_20260924.py`先逐项验证原训练source对已通过proof的163项hash，复制整个原source，再只加入明确列出的全新部署文件，拒绝覆盖任何原有同名文件。构建记录`BUILD.json`保留原文件/新增文件/全副本hash，并静态编译和导入部署入口（mj_step被禁止调用），最后将副本设为只读；不包含最终模型，不运行仿真。

先用同一并发限制执行seed9400的parameter6、direct7和nominal_train_vmc三条。三条都通过执行与对齐检查，才提交其余15条。task=False、strict=False和有完整证据的安全早停都是正常实验结果，保留后继续。只有程序执行错误、缺日志/非有限值、物理/初始观测/动作或hash对齐失败才停止提交新job；已经运行的同批job正常结束和归档，不删除失败，不选择性重试。收到SIGTERM/SIGINT亦停止新提交并归档已启动任务。

每条记录父PID/子PID、原命令、开始/退出时间、只含相关字段的有效运行环境、stdout日志、raw rollout、physics_states、contact_samples、action/参数日志、50µs子步指标及全部产物hash。清理继承的PUSH_/PANEL_/CORE_VMC_/UNIFIED_/VMC_MODEL_CACHE_变量，再应用原fixture环境；显式设置SKIP_MODEL_ARCHIVE=0与OMP/OpenBLAS/MKL各1线程。原CLI dt参数不改，检查实际物理dt=50µs。

验收读取真实MJB和原fixture初始raw48，要求完全一致；policy日志的原始观测/action7与rollout逐元素一致。物理raw全字段要求有限，按实际时长核样本数、50µs时间间隔/起止、分stage计数，并用既有报告的定义复算RMSE、峰矩、峰速。float32原始保存与float64累积的比较沿用此前rtol=1e−6/atol=1e−7，未根据新结果放宽。短安全回合使用真实观测窗口，不能混称完整24秒。

`status.json`显示phase、已完成数、活动子PID和目录；`results.json`逐条更新。三条预检通过后写`PREFLIGHT_PASSED.json`；全部18条有效执行后写`COMPLETE.json`。执行错误写`FAILED.json`与未启动job列表；`FINAL_RESULT.json`保留全部已经开始的结果。默认每job超时1800秒；仅超时或worker记录异常时终止driver自己创建的子进程，不触碰其他任务。

本次针对driver的7项纯离线测试覆盖task/gate失败继续、对齐错误阻断新任务且排空已启动任务、并发上限、已有job目录不覆盖、50µs安全短窗口，以及错误time/非有限值/count拒绝。连同加载器13项共20项通过；没有用测试启动模拟或训练。

主任务还独立用已归档VMC9400的真实480000子步数据运行本driver的physical_raw_audit，通过有限值/时间/指标检查：RMSE=0.10909175132217334m，峰速=0.11217567825923538m/s，实际actuator峰矩=35.578983306884766Nm。这是既有真实日志的只读兼容性验证，没有重跑该回合。
